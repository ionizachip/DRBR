"""The Sim class: loader, object/instance model, event dispatch, rooms, stepping, snapshots."""
import atexit
import copy
import itertools
import shutil
import datetime
import difflib
import os
import random
import re
import sys
import tempfile
from collections import namedtuple

from . import ops
from .compiler import compile_code, compile_expression, Code
from .errors import GMError, GMParseError, SimGameEnd
from .registry import DEFAULT_BUILTINS, DEFAULT_CONSTS, DEFAULT_VARS
from .rt import Frame, call_func, call_value, err_unset, err_global_unset, err_no_instance, BRK, CNT, RET
from .values import (GMArray, GMStruct, GMInstance, GMFunc, GMMethod, BuiltinRef, GMEnum, MacroVal, MISS,
                     FIRST_INSTANCE_ID, from_py, to_py, gml_str)

sys.setrecursionlimit(max(sys.getrecursionlimit(), 40000))

from .sim_log import Call  # noqa: E402

EVENT_NAMES = ("Create", "Destroy", "Alarm", "Step", "Draw", "Other", "CleanUp", "PreCreate", "KeyPress",
               "KeyRelease", "Keyboard", "Mouse", "Collision", "Gesture", "Trigger")
_OBJ_FILE_RE = re.compile(r"^gml_Object_(.+?)_(%s)_(.+)$" % "|".join(EVENT_NAMES))
_LOOSE_FILE_RE = re.compile(r"^(.+?)_(create|destroy|alarm|step|draw|other|cleanup|precreate|keypress)_(\d+)$", re.I)
_CANON = {n.lower(): n for n in EVENT_NAMES}
_ROOMCC_RE = re.compile(r"^gml_RoomCC_(.+)_(\d+)_(PreCreate|Create)$")
_ROOM_RE = re.compile(r"^gml_Room_(.+)_Create$")
_FUNC_DECL_RE = re.compile(r"(?m)^function\s+([A-Za-z_]\w*)\s*\(")
_EAGER_RE = re.compile(r"(?m)^\s*(?:enum\s+\w+|#macro\s)")
ASSET_PREFIXES = ("spr_", "snd_", "mus_", "bg_", "fnt_", "room_", "shd_", "path_", "tile_", "tl_", "ts_", "seq_",
                  "anim_", "audio_", "obj_")

INSTANCE_DEFAULTS = dict(
    x=0, y=0, xprevious=0, yprevious=0, xstart=0, ystart=0, image_index=0, image_speed=1, image_alpha=1,
    image_xscale=1, image_yscale=1, image_angle=0, image_blend=16777215, sprite_index=-1, mask_index=-1,
    depth=0, visible=True, solid=False, speed=0, direction=0, hspeed=0, vspeed=0, friction=0, gravity=0,
    gravity_direction=270, sprite_width=64, sprite_height=64, bbox_left=0, bbox_right=0, bbox_top=0,
    bbox_bottom=0, image_number=1, layer=0,
)

DRAW_ORDER = (72, 0, 73, 74, 64, 75)
_SANDBOX_COUNTER = itertools.count()


class ObjDef:
    __slots__ = ("name", "index", "parent", "persistent", "events", "sprite", "visible")

    def __init__(self, name, index):
        self.name = name
        self.index = index
        self.parent = None
        self.persistent = False
        self.events = {}      # (ev, num) -> entry name
        self.sprite = -1
        self.visible = True


class RoomDef:
    __slots__ = ("name", "index", "instances", "width", "height", "creation", "persistent")

    def __init__(self, name, index):
        self.name = name
        self.index = index
        self.instances = []
        self.width = 1280
        self.height = 960
        self.creation = None
        self.persistent = False


class Input:
    """Scripted keyboard input keyed by absolute frame number."""

    def __init__(self):
        self.events = []        # (key, start_frame, hold_frames)
        self.pressed = set()
        self.held = set()
        self.released = set()
        self.cleared = set()
        self.last_key = 0
        self.string = ""

    def begin_frame(self, fno):
        self.pressed = set()
        self.held = set()
        self.released = set()
        self.cleared = set()
        for key, start, hold in self.events:
            if start == fno:
                self.pressed.add(key)
                self.last_key = key
            if start <= fno < start + hold:
                self.held.add(key)
            if start + hold == fno:
                self.released.add(key)
        self.events = [e for e in self.events if e[1] + e[2] >= fno]

    def any_pressed(self):
        return any(k < 32769 for k in self.pressed - self.cleared)


_STATE_ATTRS = ("globals", "globalvars", "instances", "deact", "act_q", "next_id", "frame_no", "rng", "statics", "pending_room",
                "room_index", "input", "log", "assets", "next_asset", "ini", "fhandles", "next_fh", "game_ended",
                "global_name_ids", "ds_lists", "ds_maps", "ds_grids", "next_ds", "global_init_done", "now_base",
                "depth", "noself", "audio_next", "surfaces", "next_surface", "room_started", "timer_extra",
                "persist_flag", "debug_messages", "sys_state")


class Sim:
    def __init__(self, sandbox=None, seed=0, fps=30):
        from . import lib  # noqa: F401  (registers builtins)
        from .fs import FS
        if sandbox is None:
            sandbox = os.path.join(tempfile.gettempdir(), "gmlsim_%d_%d" % (os.getpid(), next(_SANDBOX_COUNTER)))
            atexit.register(shutil.rmtree, sandbox, True)
        self.sandbox = sandbox
        self.fs = FS(self.sandbox)
        self.builtins = dict(DEFAULT_BUILTINS)
        self.builtin_vars = dict(DEFAULT_VARS)
        self.names = dict(DEFAULT_CONSTS)
        self.scripts = {}
        self.script_entries = {}
        self.sources = {}
        self.codes = {}
        self.objects = {}
        self.obj_by_index = {}
        self.rooms = {}
        self.room_by_index = {}
        self.room_cc = {}
        self.mocked = set()
        self.destroying = set()
        # instances destroyed during the running event (GameMaker keeps a destroyed instance's variables readable through
        # `other` / its id until the event that destroyed it is over: Chapter 2's shot is destroyed by its own user event and
        # the collision event that called it reads other.big next)
        self.grave = {}
        self.events_cache = {}
        self.desc_cache = {}
        self.chain_cache = {}
        self.prepared = set()
        self.global_inits = []
        self.auto_assets = True
        self.max_depth = 400
        self.fps = fps
        self.raise_on_game_end = False
        self.div_zero = "error"
        ops.DIV0_MODE[0] = "error"
        self.noself = GMStruct()
        self.noself.name = "self"
        # ---- snapshotted state
        self.globals = {}
        self.globalvars = set()
        self.instances = {}
        # deactivated instances (GameMaker: skipped by events, with() and instance_exists, but their variables can still be read by id).
        # Activation changes requested inside an event take effect at the end of that event (as the GameMaker manual documents).
        self.deact = {}
        self.act_q = []
        self.ev_depth = 0
        self.next_id = FIRST_INSTANCE_ID
        self.frame_no = 0
        self.rng = random.Random(seed)
        self.seed = seed
        self.statics = {}
        self.pending_room = None
        self.room_index = -1
        self.input = Input()
        self.log = []
        self.assets = {}
        self.next_asset = 50000
        self.ini = None
        self.fhandles = {}
        self.next_fh = 1
        self.game_ended = False
        self.global_name_ids = {}
        self.ds_lists = {}
        self.ds_maps = {}
        self.ds_grids = {}
        self.next_ds = 0
        self.global_init_done = set()
        self.now_base = datetime.datetime(2024, 1, 1, 12, 0, 0)
        self.depth = 0
        self.audio_next = 100
        self.surfaces = {}
        self.next_surface = 0
        self.room_started = False
        self.timer_extra = 0
        self.persist_flag = {}
        self.debug_messages = []
        self.sys_state = {}
        self.record_calls = True
        self.restart_requested = False

    # ================================================================== loading
    def load_dir(self, path, kinds=None, match=None, define_objects=True):
        """Load every .gml in a directory (names follow UndertaleModTool conventions). Returns stats dict.

        kinds: optional subset of {'objects_events','scripts','room_cc','rooms'} to load (default all).
        match: optional regex string; only entries whose name matches are loaded.
        define_objects: even when object events are not loaded, still define the object *names* seen in the
        directory (so identifiers like obj_foo resolve and instance_exists(obj_foo) works)."""
        rx = re.compile(match) if match else None
        stats = {"objects_events": 0, "scripts": 0, "room_cc": 0, "rooms": 0, "unclassified": []}
        for fn in sorted(os.listdir(path)):
            if not fn.endswith(".gml"):
                continue
            if rx is not None and not rx.search(fn[:-4]):
                continue
            if kinds is not None and self.classify(fn[:-4]) not in kinds:
                if define_objects and self.classify(fn[:-4]) == "objects_events":
                    m = _OBJ_FILE_RE.match(fn[:-4])
                    if m and m.group(1) not in self.objects:
                        self.define_object(m.group(1))
                continue
            with open(os.path.join(path, fn), encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            kind = self.load_source(fn[:-4], text)
            if kind is None:
                stats["unclassified"].append(fn)
            else:
                stats[kind] = stats.get(kind, 0) + 1
        return stats

    @staticmethod
    def classify(entry):
        """Return 'objects_events' | 'scripts' | 'room_cc' | 'rooms' | None for an entry name."""
        if _OBJ_FILE_RE.match(entry) or _LOOSE_FILE_RE.match(entry):
            return "objects_events"
        if entry.startswith("gml_GlobalScript_"):
            return "scripts"
        if _ROOMCC_RE.match(entry):
            return "room_cc"
        if _ROOM_RE.match(entry):
            return "rooms"
        return None

    def load_file(self, path, entry=None):
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        name = entry or os.path.basename(path)[:-4]
        return self.load_source(name, text)

    def load_source(self, entry, text):
        """Register one code entry by its UTMT-style name. Returns classification string or None."""
        m = _OBJ_FILE_RE.match(entry)
        if m:
            obj, ev, num = m.group(1), m.group(2), m.group(3)
            self._add_event(obj, ev, num, entry, text)
            return "objects_events"
        if entry.startswith("gml_GlobalScript_"):
            self.sources[entry] = text
            # a new text for an entry loaded before: its old compiled code goes (it would be used again otherwise)
            self.codes.pop(entry, None)
            names = _FUNC_DECL_RE.findall(text)
            if not names:
                names = [entry[len("gml_GlobalScript_"):]]
            for n in names:
                if n not in self.mocked:
                    self.script_entries[n] = entry
                    self.scripts.pop(n, None)
                    if n in self.builtins and n not in self.mocked:
                        del self.builtins[n]
            if _EAGER_RE.search(text):
                self.get_code(entry, True)
                self.prepare(self.codes[entry])
            return "scripts"
        m = _ROOMCC_RE.match(entry)
        if m:
            self.sources[entry] = text
            self.room_cc[(m.group(1), int(m.group(2)))] = entry
            return "room_cc"
        m = _ROOM_RE.match(entry)
        if m:
            self.sources[entry] = text
            self.define_room(m.group(1)) if m.group(1) not in self.rooms else None
            self.rooms[m.group(1)].creation = entry
            return "rooms"
        m = _LOOSE_FILE_RE.match(entry)
        if m:
            self._add_event(m.group(1), _CANON[m.group(2).lower()], m.group(3), entry, text)
            return "objects_events"
        return None

    def _add_event(self, obj, ev, num, entry, text):
        self.sources[entry] = text
        self.codes.pop(entry, None)
        if obj not in self.objects:
            self.define_object(obj)
        try:
            key = (ev, int(num))
        except ValueError:
            key = (ev, num)
        self.objects[obj].events[key] = entry
        self.events_cache.clear()

    def define_event(self, obj, ev, num, source):
        """Attach inline GML source as an event: sim.define_event('obj_x', 'Step', 0, 'x += 1;')"""
        entry = "gml_Object_%s_%s_%s" % (obj, ev, num)
        self._add_event(obj, ev, num, entry, source)

    def define_script(self, name, source):
        """Define global script(s) from source text, e.g. 'function foo(a) { return a * 2; }'."""
        entry = "gml_GlobalScript_" + name
        self.sources[entry] = source
        names = _FUNC_DECL_RE.findall(source) or [name]
        for n in names:
            self.script_entries[n] = entry
            self.scripts.pop(n, None)
            self.builtins.pop(n, None) if n not in self.mocked else None
        self.codes.pop(entry, None)
        if _EAGER_RE.search(source):
            self.get_code(entry, True)
            self.prepare(self.codes[entry])

    def get_code(self, entry, is_script=None):
        c = self.codes.get(entry)
        if c is None:
            src = self.sources[entry]
            if is_script is None:
                is_script = entry.startswith("gml_GlobalScript_")
            c = compile_code(entry, src, is_script)
            self.codes[entry] = c
        return c

    def prepare(self, code):
        """Register hoisted enums/macros of a compiled entry (once per sim)."""
        if id(code) in self.prepared:
            return
        self.prepared.add(id(code))
        for name, text in code.macros:
            self.names[name] = MacroVal(name, text)
        for name, members in code.enums:
            vals = {}
            nxt = 0
            scope = GMStruct(vals)
            scope.name = "enum " + name
            fr = Frame(self, scope, None, [])
            for m, c in members:
                if c is not None:
                    nxt = c(fr)
                    if nxt.__class__ is float and nxt == int(nxt):
                        nxt = int(nxt)
                vals[m] = nxt
                nxt = nxt + 1 if isinstance(nxt, (int, float)) else nxt
            self.names[name] = GMEnum(name, vals)

    def ensure_script(self, name):
        entry = self.script_entries.get(name)
        if entry is None:
            return None
        code = self.get_code(entry, True)
        self.prepare(code)
        for fname, fn in code.funcs:
            if fname not in self.mocked:
                self.scripts[fname] = fn
        if code.has_stmts and entry not in self.global_inits:
            self.global_inits.append(entry)
        return self.scripts.get(name)

    def run_global_inits(self):
        """Execute top-level (non-function) statements of loaded global scripts, once each."""
        for entry in list(self.global_inits):
            if entry in self.global_init_done:
                continue
            self.global_init_done.add(entry)
            self.exec_code(self.get_code(entry, True), self.noself)

    # ================================================================== configuration API
    def define_object(self, name, parent=None, persistent=None, sprite=None, index=None, **_):
        od = self.objects.get(name)
        if od is None:
            od = self.objects[name] = ObjDef(name, index if index is not None else max([o.index for o in self.objects.values()] + [-1]) + 1)
            self.obj_by_index[od.index] = name
            self.names[name] = od.index
        if parent is not None:
            od.parent = parent
            if parent not in self.objects:
                self.define_object(parent)
        if persistent is not None:
            od.persistent = bool(persistent)
        if sprite is not None:
            od.sprite = sprite
        self.desc_cache.clear()
        self.chain_cache.clear()
        self.events_cache.clear()
        return od.index

    def object_index(self, name):
        return self.objects[name].index

    def define_room(self, name, instances=(), width=1280, height=960, creation_code=None, persistent=False):
        rd = self.rooms.get(name)
        if rd is None:
            rd = self.rooms[name] = RoomDef(name, len(self.rooms))
            self.room_by_index[rd.index] = name
            self.names[name] = rd.index
        rd.instances = list(instances)
        rd.width, rd.height = width, height
        rd.persistent = persistent
        if creation_code is not None:
            ename = "sim_room_creation_" + name
            self.sources[ename] = creation_code
            rd.creation = ename
        return rd.index

    def define_global(self, name, value):
        self.globals[name] = from_py(value)

    def define_globals(self, **kw):
        for k, v in kw.items():
            self.globals[k] = from_py(v)

    def define_const(self, name, value):
        self.names[name] = value

    def define_asset(self, name):
        idx = self.assets.get(name)
        if idx is None:
            idx = self.assets[name] = self.next_asset
            self.next_asset += 1
        return idx

    asset_index = define_asset

    def mock(self, name, fn, frame=False, record=False):
        """Install a Python mock. fn(sim, *args) (or fn(sim, frame, *args) if frame=True); a non-callable
        is returned as a constant."""
        if not callable(fn):
            val = fn
            fn = lambda sim, *a: val
        if record:
            inner = fn
            if frame:
                def fn(sim, f, *a):
                    sim.log.append(Call(sim.frame_no, name, a))
                    return inner(sim, f, *a)
            else:
                def fn(sim, *a):
                    sim.log.append(Call(sim.frame_no, name, a))
                    return inner(sim, *a)
        self.builtins[name] = (fn, frame)
        self.mocked.add(name)
        self.script_entries.pop(name, None)
        self.scripts.pop(name, None)

    def mock_value(self, name, value):
        self.builtin_vars[name] = value

    def calls(self, name=None):
        return [c for c in self.log if name is None or c.name == name]

    def clear_log(self):
        self.log.clear()

    def inject_write_fault(self, fault, match=None, once=True):
        """Arm a write fault (see gmlsim.Fault) for the next sandbox file write matching `match`."""
        self.fs.inject(fault, match, once)

    def set_div_zero(self, mode):
        assert mode in ("error", "inf", "real")
        self.div_zero = mode
        ops.DIV0_MODE[0] = mode

    # ================================================================== name resolution
    def lookup_name(self, name, f):
        if self.globalvars and name in self.globalvars:
            try:
                return self.globals[name]
            except KeyError:
                raise err_global_unset(self, name)
        v = self.names.get(name, MISS)
        if v is not MISS:
            if v.__class__ is MacroVal:
                return compile_expression(v.text)(f)
            return v
        fn = self.scripts.get(name)
        if fn is not None:
            return fn
        if name in self.script_entries:
            fn = self.ensure_script(name)
            if fn is not None:
                return fn
        v = self.assets.get(name)
        if v is not None:
            return v
        if name in self.builtins:
            return BuiltinRef(name)
        bv = self.builtin_vars.get(name, MISS)
        if bv is not MISS:
            return bv(self) if callable(bv) else bv
        if self.auto_assets and name.startswith(ASSET_PREFIXES) and not name.startswith("obj_"):
            return self.define_asset(name)
        raise err_unset(f.self.name, name)

    def get_callable(self, name, f, quiet=False):
        v = f.loc.get(name, MISS)
        if v is MISS:
            v = f.self.vars.get(name, MISS)
        if v is not MISS and v.__class__ in (GMFunc, GMMethod):
            return v
        fn = self.scripts.get(name)
        if fn is None and name in self.script_entries:
            fn = self.ensure_script(name)
        if fn is not None:
            return fn
        if name in self.builtins:
            return BuiltinRef(name)
        if quiet:
            return None
        raise GMError("undefined function %s%s" % (name, self._suggest(name)), "undefined_function")

    def _suggest(self, name):
        pool = list(self.builtins) + list(self.script_entries) + list(self.scripts)
        m = difflib.get_close_matches(name, pool, 2, 0.8)
        return " (did you mean %s?)" % " / ".join(m) if m else ""

    def call_unresolved(self, name, f, args):
        if name in self.script_entries:
            fn = self.ensure_script(name)
            if fn is not None:
                return call_func(self, fn, args, f.self, f.other, f.ev)
        raise GMError("undefined function %s%s" % (name, self._suggest(name)), "undefined_function")

    def call_builtin(self, name, f, args):
        ent = self.builtins.get(name)
        if ent is None:
            raise GMError("undefined function %s" % name, "undefined_function")
        try:
            return ent[0](self, f, *args) if ent[1] else ent[0](self, *args)
        except (TypeError, ValueError, IndexError, KeyError, AttributeError, OverflowError, ZeroDivisionError) as e:
            raise GMError("%s(): %s: %s" % (name, e.__class__.__name__, e), "builtin_args") from e

    def script_by_index(self, i):
        return None

    def ctor_parent(self, fn):
        """GMFunc of the parent constructor of fn (or None)."""
        if fn.parent is None:
            return None
        pn = fn.parent[0]
        p = self.scripts.get(pn)
        if p is None and pn in self.script_entries:
            p = self.ensure_script(pn)
        return p

    # ================================================================== instances
    def chain(self, obj):
        c = self.chain_cache.get(obj)
        if c is None:
            out = []
            n = obj
            while n is not None:
                if n in out:
                    raise GMError("object parent cycle at %s" % n)
                out.append(n)
                od = self.objects.get(n)
                n = od.parent if od else None
            c = self.chain_cache[obj] = tuple(out)
        return c

    def descendants(self, obj):
        """Set of object names that are obj or inherit from it."""
        s = self.desc_cache.get(obj)
        if s is None:
            s = {n for n in self.objects if obj in self.chain(n)}
            self.desc_cache[obj] = s
        return s

    def is_a(self, obj, ancestor):
        return ancestor in self.chain(obj)

    def first_of(self, objindex):
        name = self.obj_by_index.get(objindex)
        if name is None:
            return None
        d = self.descendants(name)
        for inst in self.instances.values():
            if inst.obj in d:
                return inst
        return None

    def instances_of(self, objindex_or_name):
        if objindex_or_name.__class__ is str:
            name = objindex_or_name
        else:
            name = self.obj_by_index.get(objindex_or_name)
            if name is None:
                return []
        d = self.descendants(name)
        return [i for i in self.instances.values() if i.obj in d]

    def with_targets(self, f, v):
        t = v.__class__
        if t is GMStruct:
            return (v,)
        if t is GMInstance:
            return () if v.dead else (v,)
        if v is None:
            return ()
        if t is int or t is float or t is bool or t.__name__ == "GMInt64":
            n = int(v)
            if n >= FIRST_INSTANCE_ID:
                i = self.instances.get(n)
                return (i,) if i is not None else ()
            if n >= 0:
                return self.instances_of(n)
            if n == -3:
                return list(self.instances.values())
            if n == -1:
                return (f.self,)
            if n == -2:
                return (f.other,) if f.other is not None else ()
            return ()
        raise GMError("with(): cannot iterate over %s" % type(v).__name__, "type")

    def lookup_instance(self, who):
        """Python-side: resolve id / GMInstance / object name / object index to a live instance (or raise)."""
        if who.__class__ is GMInstance:
            return who
        if who.__class__ is str:
            insts = self.instances_of(who) if who in self.objects else []
            if not insts:
                raise err_no_instance(who)
            return insts[0]
        if who >= FIRST_INSTANCE_ID:
            i = self.instances.get(who)
        else:
            i = self.first_of(who)
        if i is None:
            raise err_no_instance(who)
        return i

    def create(self, obj, x=0, y=0, depth=0, vars=None, **kw):
        """Create an instance (runs PreCreate + Create). Returns the instance id."""
        v = dict(vars or {})
        v.update(kw)
        return self.create_instance(obj, x, y, depth, v).id

    def create_instance(self, obj, x=0, y=0, depth=0, vars=None, creator=None):
        if obj.__class__ is not str:
            name = self.obj_by_index.get(int(obj))
            if name is None:
                raise GMError("Unable to find object with index %s" % obj, "no_object")
            obj = name
        hook = getattr(self, 'create_hook', None)
        if hook is not None:
            hook(obj)
        od = self.objects.get(obj)
        if od is None:
            raise GMError("Unable to find object %s (not defined in sim; use define_object)" % obj, "no_object")
        iid = self.next_id
        self.next_id += 1
        inst = GMInstance(iid, obj)
        d = inst.vars
        d.update(INSTANCE_DEFAULTS)
        d["x"] = d["xstart"] = d["xprevious"] = x
        d["y"] = d["ystart"] = d["yprevious"] = y
        d["depth"] = depth
        d["id"] = iid
        d["object_index"] = od.index
        d["persistent"] = self._inherited_flag(obj)
        d["alarm"] = GMArray([-1] * 12)
        d["sprite_index"] = od.sprite
        self.instances[iid] = inst
        if vars:
            for k, val in vars.items():
                d[k] = from_py(val)
        if creator is not None:
            pass
        self.run_event(inst, "PreCreate", 0, creator)
        if not inst.dead:
            self.run_event(inst, "Create", 0, creator)
        return inst

    def _inherited_flag(self, obj):
        for n in self.chain(obj):
            if self.objects[n].persistent:
                return True
        return False

    def destroy_instance(self, inst, run_events=True):
        if inst.dead or inst.id in self.destroying:
            return
        if run_events:
            d = self.destroying
            d.add(inst.id)
            try:
                self.run_event(inst, "Destroy", 0)
                self.run_event(inst, "CleanUp", 0)
            finally:
                d.discard(inst.id)
        inst.dead = True
        self.instances.pop(inst.id, None)
        if self.ev_depth > 0:
            self.grave[inst.id] = inst

    def instance_count_of(self, objindex):
        return len(self.instances_of(objindex))

    # ================================================================== events
    def find_event(self, obj, key):
        ck = (obj, key)
        r = self.events_cache.get(ck, MISS)
        if r is MISS:
            r = None
            for n in self.chain(obj):
                od = self.objects.get(n)
                if od is not None:
                    e = od.events.get(key)
                    if e is not None:
                        r = (n, e)
                        break
            self.events_cache[ck] = r
        return r

    def has_event(self, obj, ev, num=0):
        return self.find_event(obj, (ev, num)) is not None

    def run_event(self, inst, ev, num=0, other=None):
        found = self.find_event(inst.obj, (ev, num))
        if found is None:
            return False
        defobj, entry = found
        self._run_entry(inst, defobj, (ev, num), entry, other)
        return True

    def _run_entry(self, inst, defobj, key, entry, other):
        code = self.codes.get(entry) or self.get_code(entry, False)
        if self.ev_depth == 0 and self.grave:
            self.grave.clear()
        self.ev_depth += 1
        d = self.ev_depth
        try:
            self.exec_code(code, inst, other, (defobj, key))
        except GMError as e:
            if e.event is None:
                e.event = "%s.%s_%s" % (inst.obj, key[0], key[1])
            raise
        finally:
            self.ev_depth -= 1
            if self.act_q:
                self.apply_activation(d)

    # ---- instance (de)activation
    def request_activation(self, op, ids):
        """op: 'on' / 'off'; ids: list of instance ids. Applied at the end of the current event (immediately outside events)."""
        self.act_q.append((self.ev_depth, op, list(ids)))
        if self.ev_depth == 0:
            self.apply_activation(0)

    def apply_activation(self, depth):
        keep = []
        todo = []
        for q in self.act_q:
            (todo if q[0] >= depth else keep).append(q)
        self.act_q = keep
        for _d, op, ids in todo:
            for i in ids:
                if op == 'off':
                    inst = self.instances.pop(i, None)
                    if inst is not None and not inst.dead:
                        self.deact[i] = inst
                else:
                    inst = self.deact.pop(i, None)
                    if inst is not None and not inst.dead:
                        self.instances[i] = inst

    def run_inherited(self, f):
        ev = f.ev
        if ev is None:
            return None
        defobj, key = ev
        ch = self.chain(defobj)
        for n in ch[1:]:
            e = self.objects[n].events.get(key)
            if e is not None:
                code = self.get_code(e, False)
                return self.exec_code(code, f.self, f.other, (n, key))
        return None

    def exec_code(self, code, self_obj, other=None, ev=None, args=()):
        if id(code) not in self.prepared:
            self.prepare(code)
        fr = Frame(self, self_obj, other, list(args), ev, None)
        try:
            code.body(fr)
        except GMError as e:
            if e.entry is None:
                e.entry = code.entry
            raise
        except RecursionError:
            raise GMError("Stack overflow (Python recursion limit hit in %s)" % code.entry, "stack")
        return fr.ret

    # ---- python-side convenience
    def run(self, source, self_obj=None, entry="<run>", other=None):
        """Execute GML statements. self_obj: instance id / object name / GMInstance / None."""
        code = compile_code(entry, source, True)
        self.prepare(code)
        for fname, fn in code.funcs:
            self.scripts[fname] = fn
        so = self._self_for(self_obj)
        if self.ev_depth == 0 and self.grave:
            self.grave.clear()
        return self.exec_code(code, so, other)

    def eval(self, expr, self_obj=None):
        """Evaluate a GML expression and return the raw GML value."""
        c = compile_expression(expr)
        fr = Frame(self, self._self_for(self_obj), None, [])
        try:
            return c(fr)
        except GMError as e:
            if e.entry is None:
                e.entry = "<expr>"
            raise

    def _self_for(self, who):
        if who is None:
            return self.noself
        if who.__class__ is GMStruct:
            return who
        return self.lookup_instance(who)

    def py(self, v):
        return to_py(v)

    def call(self, name, *args, self_obj=None):
        """Call a script function / builtin by name with Python args (converted); returns raw GML value."""
        fr = Frame(self, self._self_for(self_obj), None, [])
        fn = self.get_callable(name, fr)
        return call_value(fr, fn, [from_py(a) for a in args])

    def get(self, who, name):
        if who == "global" or who is None:
            return self.globals[name]
        return self.lookup_instance(who).vars[name]

    def set(self, who, name, value):
        v = from_py(value)
        if who == "global" or who is None:
            self.globals[name] = v
        else:
            self.lookup_instance(who).vars[name] = v

    def inst(self, who):
        return self.lookup_instance(who)

    def instance_list(self, obj=None):
        if obj is None:
            return list(self.instances.values())
        return self.instances_of(obj)

    # ================================================================== ds helpers
    def ds_list(self, i):
        try:
            return self.ds_lists[int(i)]
        except (KeyError, TypeError, ValueError):
            raise GMError("Data structure with index %s does not exist (ds_list)" % (i,), "ds")

    def ds_map(self, i):
        try:
            return self.ds_maps[int(i)]
        except (KeyError, TypeError, ValueError):
            raise GMError("Data structure with index %s does not exist (ds_map)" % (i,), "ds")

    def ds_grid(self, i):
        try:
            return self.ds_grids[int(i)]
        except (KeyError, TypeError, ValueError):
            raise GMError("Data structure with index %s does not exist (ds_grid)" % (i,), "ds")

    # ================================================================== input
    def press(self, key, frame=None, hold=1):
        """Schedule a key press. frame=None means the next frame stepped. hold = number of frames held."""
        from .lib_input import key_code
        self.input.events.append((key_code(key), self.frame_no if frame is None else frame, hold))

    def hold(self, key, frames, start=None):
        self.press(key, start, frames)

    # ================================================================== stepping
    def step(self, n=1, draw=True):
        for _ in range(n):
            if self.game_ended:
                if self.raise_on_game_end:
                    raise SimGameEnd()
                break
            try:
                self._frame(draw)
            except GMError as e:
                if e.frame is None:
                    e.frame = self.frame_no
                raise
            self.frame_no += 1

    def _phase(self, ev, num):
        for inst in list(self.instances.values()):
            # GameMaker: an instance switched off (instance_deactivate_*) by an earlier instance's event of this phase does not run
            # its own (the runner's event loops skip deactivated instances); one destroyed is gone too
            if not inst.dead and inst.id in self.instances:
                found = self.find_event(inst.obj, (ev, num))
                if found is not None:
                    self._run_entry(inst, found[0], (ev, num), found[1], None)

    def _frame(self, draw):
        inp = self.input
        inp.begin_frame(self.frame_no)
        # the runner's first act of a frame: every instance's xprevious / yprevious = where it is now
        for inst in self.instances.values():
            if not inst.dead:
                d = inst.vars
                d["xprevious"] = d.get("x", 0)
                d["yprevious"] = d.get("y", 0)
        self._phase("Step", 1)
        # alarms
        for inst in list(self.instances.values()):
            if inst.dead or inst.id not in self.instances:
                continue
            al = inst.vars.get("alarm")
            if al.__class__ is not GMArray:
                continue
            for i in range(len(al.data)):
                a = al.data[i]
                if a.__class__ in (int, float) and a > 0:
                    a -= 1
                    if a <= 0:
                        a = -1
                        al.data[i] = -1
                        if not inst.dead:
                            found = self.find_event(inst.obj, ("Alarm", i))
                            if found is not None:
                                self._run_entry(inst, found[0], ("Alarm", i), found[1], None)
                    else:
                        al.data[i] = a
        # key events
        if inp.pressed or inp.held or inp.released:
            for kind, keys in (("Keyboard", inp.held), ("KeyPress", inp.pressed), ("KeyRelease", inp.released)):
                for k in sorted(keys):
                    self._phase(kind, k)
        self._phase("Step", 0)
        self._phase("Step", 2)
        # asynchronous events (network): delivered after End Step
        hooks = getattr(self, "async_hooks", None)
        if hooks:
            for h in list(hooks):
                h(self)
        if self.pending_room is not None:
            self._change_room()
        if draw:
            for num in DRAW_ORDER:
                for inst in sorted(self.instances.values(), key=lambda i: -i.vars.get("depth", 0)):
                    if inst.dead or inst.id not in self.instances or not inst.vars.get("visible", True):
                        continue
                    found = self.find_event(inst.obj, ("Draw", num))
                    if found is not None:
                        self._run_entry(inst, found[0], ("Draw", num), found[1], None)

    # ================================================================== rooms
    def room_name(self):
        return self.room_by_index.get(self.room_index)

    def goto_room(self, room):
        """Request a room change at the next step boundary (what room_goto does)."""
        self.pending_room = self._room_idx(room)

    def _room_idx(self, room):
        if room.__class__ is str:
            if room not in self.rooms:
                raise GMError("Room %s is not defined in the sim (define_room)" % room, "no_room")
            return self.rooms[room].index
        if room not in self.room_by_index:
            raise GMError("Room index %s is not defined in the sim (define_room)" % (room,), "no_room")
        return int(room)

    def start(self, room):
        """Enter the first room immediately (no Room End events)."""
        self.pending_room = self._room_idx(room)
        self._change_room()

    def _change_room(self):
        target = self.pending_room
        self.pending_room = None
        if self.room_started:
            for inst in list(self.instances.values()):
                if not inst.dead:
                    self.run_event(inst, "Other", 5)
            for inst in list(self.instances.values()):
                if inst.vars.get("persistent") is not True and not inst.dead:
                    self.run_event(inst, "CleanUp", 0)
                    inst.dead = True
                    self.instances.pop(inst.id, None)
        if self.room_started:
            for i, inst in list(self.deact.items()):
                inst.dead = True
            self.deact = {}
            self.act_q = []
        self.room_started = True
        self.room_index = target
        rd = self.rooms[self.room_by_index[target]]
        created = []
        for i, spec in enumerate(rd.instances):
            obj, x, y, vars_, cc = self._room_spec(spec)
            inst_vars = dict(vars_)
            iid = self._create_room_instance(obj, x, y, inst_vars, rd.name, cc)
            created.append(iid)
        if rd.creation:
            self.exec_code(self.get_code(rd.creation, False), self.noself)
        for inst in list(self.instances.values()):
            if not inst.dead:
                self.run_event(inst, "Other", 4)

    def _room_spec(self, spec):
        if spec.__class__ is str:
            return spec, 0, 0, {}, None
        if isinstance(spec, dict):
            return spec["obj"], spec.get("x", 0), spec.get("y", 0), spec.get("vars", {}), spec.get("cc")
        spec = tuple(spec)
        obj = spec[0]
        x = spec[1] if len(spec) > 1 else 0
        y = spec[2] if len(spec) > 2 else 0
        vars_ = spec[3] if len(spec) > 3 else {}
        cc = spec[4] if len(spec) > 4 else None
        return obj, x, y, vars_, cc

    def _create_room_instance(self, obj, x, y, vars_, room, cc):
        od = self.objects.get(obj)
        if od is None:
            raise GMError("Room %s references undefined object %s" % (room, obj), "no_object")
        iid = self.next_id
        self.next_id += 1
        inst = GMInstance(iid, obj)
        d = inst.vars
        d.update(INSTANCE_DEFAULTS)
        d["x"] = d["xstart"] = d["xprevious"] = x
        d["y"] = d["ystart"] = d["yprevious"] = y
        d["id"] = iid
        d["object_index"] = od.index
        d["persistent"] = self._inherited_flag(obj)
        d["alarm"] = GMArray([-1] * 12)
        d["sprite_index"] = od.sprite
        self.instances[iid] = inst
        for k, val in vars_.items():
            d[k] = from_py(val)
        self.run_event(inst, "PreCreate", 0)
        if cc is not None:
            e = self.room_cc.get((room, cc))
            if e is not None:
                self.exec_code(self.get_code(e, False), inst)
        if not inst.dead:
            self.run_event(inst, "Create", 0)
        return iid

    # ================================================================== snapshot / restore
    def snapshot(self, files=True):
        state = {k: copy.deepcopy(getattr(self, k)) for k in _STATE_ATTRS}
        return {"state": state, "files": self.fs.dump() if files else None}

    def restore(self, snap):
        state = copy.deepcopy(snap["state"])
        for k, v in state.items():
            setattr(self, k, v)
        if snap["files"] is not None:
            self.fs.load(snap["files"])
