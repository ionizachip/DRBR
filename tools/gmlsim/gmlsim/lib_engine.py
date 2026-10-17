"""Engine builtins: instances, events, rooms, alarms."""
from . import ops
from .errors import GMError
from .registry import builtin, gvar
from .rt import resolve_instance
from .values import GMInstance, GMStruct, GMArray, FIRST_INSTANCE_ID, NOONE, from_py


def _int(v, fn="function"):
    t = v.__class__
    if t is int:
        return v
    if t.__name__ == "GMInt64":
        return int(v)
    if t is float or t is bool:
        return int(v)
    if t is GMInstance:
        return v.id
    raise GMError("%s(): expected an object/instance id, got %r" % (fn, v), "type")


@builtin(frame=True)
def instance_exists(sim, f, v):
    n = _int(v, "instance_exists")
    if n >= FIRST_INSTANCE_ID:
        return n in sim.instances
    if n >= 0:
        return sim.first_of(n) is not None
    if n == -3:
        return bool(sim.instances)
    if n == -1:
        return not f.self.dead if f.self.__class__ is GMInstance else False
    if n == -2:
        return f.other is not None and f.other.__class__ is GMInstance and not f.other.dead
    return False


@builtin(frame=True)
def instance_number(sim, f, v):
    n = _int(v, "instance_number")
    if n == -3:
        return len(sim.instances)
    if n >= FIRST_INSTANCE_ID:
        return 1 if n in sim.instances else 0
    return len(sim.instances_of(n))


@builtin()
def instance_find(sim, v, k):
    n = _int(v, "instance_find")
    k = _int(k, "instance_find")
    lst = list(sim.instances.values()) if n == -3 else sim.instances_of(n)
    if 0 <= k < len(lst):
        return lst[k].id
    return NOONE


@builtin(frame=True)
def instance_destroy(sim, f, *args):
    if not args:
        if f.self.__class__ is GMInstance:
            sim.destroy_instance(f.self)
        return 0
    n = _int(args[0], "instance_destroy")
    run_ev = ops.truth(args[1]) if len(args) > 1 else True
    if n >= FIRST_INSTANCE_ID:
        i = sim.instances.get(n)
        if i is not None:
            sim.destroy_instance(i, run_ev)
    elif n == -3:
        for i in list(sim.instances.values()):
            sim.destroy_instance(i, run_ev)
    elif n == -1:
        if f.self.__class__ is GMInstance:
            sim.destroy_instance(f.self, run_ev)
    else:
        for i in sim.instances_of(n):
            sim.destroy_instance(i, run_ev)
    return 0


def _vars_arg(v):
    if v.__class__ is GMStruct:
        return dict(v.vars)
    return None


@builtin(frame=True)
def instance_create_depth(sim, f, x, y, depth, obj, vars=None):
    inst = sim.create_instance(_int(obj, "instance_create_depth"), x, y, depth, _vars_arg(vars), f.self)
    return inst.id


@builtin(frame=True)
def instance_create_layer(sim, f, x, y, layer, obj, vars=None):
    inst = sim.create_instance(_int(obj, "instance_create_layer"), x, y, 0, _vars_arg(vars), f.self)
    return inst.id


@builtin(frame=True)
def instance_create(sim, f, x, y, obj):
    return sim.create_instance(_int(obj, "instance_create"), x, y, 0, None, f.self).id


def _act_ids(sim, v, pool):
    """ids in pool (dict id->inst) matched by an instance id / object index (with children) / all"""
    n = _int(v, "instance_(de)activate_object")
    if n >= FIRST_INSTANCE_ID:
        return [n] if n in pool else []
    if n == -3:
        return list(pool.keys())
    name = sim.obj_by_index.get(n)
    if name is None:
        return []
    d = sim.descendants(name)
    return [i for i, inst in pool.items() if inst.obj in d]


@builtin(frame=True)
def instance_deactivate_object(sim, f, v):
    sim.request_activation('off', _act_ids(sim, v, sim.instances))
    return 0


@builtin(frame=True)
def instance_activate_object(sim, f, v):
    sim.request_activation('on', _act_ids(sim, v, sim.deact))
    return 0


@builtin(frame=True)
def instance_deactivate_all(sim, f, notme=False):
    me = f.self.id if (ops.truth(notme) and f.self.__class__ is GMInstance) else None
    sim.request_activation('off', [i for i in sim.instances if i != me])
    return 0


@builtin(frame=True)
def instance_activate_all(sim, f):
    sim.request_activation('on', list(sim.deact.keys()))
    return 0


@builtin("instance_activate_region", "instance_deactivate_region", "instance_activate_layer", "instance_deactivate_layer")
def _inst_activate(sim, *a):
    return 0


@builtin(frame=True)
def instance_change(sim, f, obj, perf):
    raise GMError("instance_change() is not supported by the sim; mock it", "unsupported")


@builtin()
def object_get_name(sim, i):
    n = sim.obj_by_index.get(_int(i))
    return n if n is not None else "<undefined>"


@builtin()
def object_get_parent(sim, i):
    n = sim.obj_by_index.get(_int(i))
    if n is None:
        return -1
    p = sim.objects[n].parent
    return sim.objects[p].index if p else -100


@builtin()
def object_exists(sim, i):
    return _int(i) in sim.obj_by_index


@builtin()
def object_is_ancestor(sim, obj, anc):
    n = sim.obj_by_index.get(_int(obj))
    a = sim.obj_by_index.get(_int(anc))
    return bool(n and a and n != a and a in sim.chain(n))


@builtin(frame=True)
def event_inherited(sim, f):
    sim.run_inherited(f)
    return 0


@builtin(frame=True)
def event_user(sim, f, n):
    n = _int(n, "event_user")
    if not 0 <= n <= 15:
        raise GMError("event_user(%d): user event number must be 0..15" % n, "builtin_args")
    return event_perform(sim, f, 7, 10 + n)


_EV_NAMES = {0: "Create", 1: "Destroy", 2: "Alarm", 3: "Step", 5: "Keyboard", 7: "Other", 8: "Draw",
             9: "KeyPress", 10: "KeyRelease", 12: "CleanUp", 4: "Collision", 6: "Mouse"}


@builtin(frame=True)
def event_perform(sim, f, t, n):
    t, n = _int(t), _int(n)
    name = _EV_NAMES.get(t)
    if name is None:
        raise GMError("event_perform(): unsupported event type %d" % t, "unsupported")
    inst = f.self
    if inst.__class__ is not GMInstance:
        raise GMError("event_perform(): self is not an instance", "type")
    sim.run_event(inst, name, n, f.other)
    return 0


@builtin(frame=True)
def event_perform_object(sim, f, obj, t, n):
    t, n = _int(t), _int(n)
    name = _EV_NAMES.get(t)
    oname = sim.obj_by_index.get(_int(obj))
    if oname is None:
        raise GMError("event_perform_object(): unknown object %r" % (obj,), "no_object")
    found = sim.find_event(oname, (name, n))
    if found is not None:
        code = sim.get_code(found[1], False)
        sim.exec_code(code, f.self, f.other, (found[0], (name, n)))
    return 0


@builtin(frame=True)
def alarm_set(sim, f, i, v):
    f.self.vars["alarm"].data[_int(i)] = v
    return 0


@builtin(frame=True)
def alarm_get(sim, f, i):
    return f.self.vars["alarm"].data[_int(i)]


# ---- rooms
@builtin()
def room_goto(sim, r):
    sim.pending_room = sim._room_idx(_int(r, "room_goto"))
    return 0


@builtin()
def room_restart(sim):
    sim.pending_room = sim.room_index
    return 0


@builtin()
def room_goto_next(sim):
    nxt = sim.room_index + 1
    if nxt not in sim.room_by_index:
        raise GMError("room_goto_next(): no room after the current one", "no_room")
    sim.pending_room = nxt
    return 0


@builtin()
def room_goto_previous(sim):
    prv = sim.room_index - 1
    if prv not in sim.room_by_index:
        raise GMError("room_goto_previous(): no room before the current one", "no_room")
    sim.pending_room = prv
    return 0


@builtin()
def room_next(sim, r):
    r = _int(r) + 1
    return r if r in sim.room_by_index else -1


@builtin()
def room_previous(sim, r):
    r = _int(r) - 1
    return r if r in sim.room_by_index else -1


@builtin()
def room_exists(sim, r):
    return _int(r) in sim.room_by_index


@builtin()
def room_get_name(sim, r):
    return sim.room_by_index.get(_int(r), "<undefined>")


@builtin("room_set_persistent", "room_set_width", "room_set_height")
def _room_noop(sim, *a):
    return 0


gvar("room", lambda sim: sim.room_index)
gvar("room_speed", lambda sim: sim.fps)
gvar("fps", lambda sim: sim.fps)
gvar("fps_real", lambda sim: sim.fps)
gvar("room_width", lambda sim: (sim.rooms[sim.room_by_index[sim.room_index]].width if sim.room_index in sim.room_by_index else 640))
gvar("room_height", lambda sim: (sim.rooms[sim.room_by_index[sim.room_index]].height if sim.room_index in sim.room_by_index else 480))
gvar("room_first", 0)
gvar("room_last", lambda sim: max(0, len(sim.rooms) - 1))
gvar("instance_count", lambda sim: len(sim.instances))
gvar("delta_time", lambda sim: int(1000000 / sim.fps))
gvar("os_type", 0)
gvar("os_browser", -1)
gvar("debug_mode", False)
gvar("async_load", -1)
gvar("keyboard_key", lambda sim: sim.input.last_key if sim.input.held else 0)
gvar("keyboard_lastkey", lambda sim: sim.input.last_key)
gvar("keyboard_string", lambda sim: sim.input.string)
gvar("mouse_x", 0)
gvar("mouse_y", 0)
gvar("mouse_button", 0)
gvar("mouse_lastbutton", 0)
gvar("view_current", 0)
gvar("application_surface", -1)
gvar("program_directory", lambda sim: sim.fs.root + "/")
gvar("working_directory", lambda sim: sim.fs.root + "/")
gvar("game_save_id", lambda sim: sim.fs.root + "/")
gvar("temp_directory", lambda sim: sim.fs.root + "/")
gvar("cache_directory", lambda sim: sim.fs.root + "/")
gvar("game_display_name", "gmlsim")
gvar("game_project_name", "gmlsim")
gvar("current_time", lambda sim: int(sim.frame_no * 1000 / sim.fps * getattr(sim, "ct_rate", 1.0)) + getattr(sim, "ct_offset", 0))
gvar("health", 100)
gvar("score", 0)
gvar("lives", 3)

# builtin view arrays (read-only snapshots; writes land in instance variables)
for _nm in ("view_camera", "view_xview", "view_yview", "view_wview", "view_hview", "view_xport", "view_yport",
            "view_wport", "view_hport", "view_visible", "view_enabled", "view_surface_id", "view_angle",
            "view_object", "view_hborder", "view_vborder", "view_hspeed", "view_vspeed"):
    gvar(_nm, (lambda sim: GMArray([0] * 8)))
