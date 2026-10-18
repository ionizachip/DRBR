"""Runtime support used by compiled closures: frames, field access, calls."""
from .errors import GMError, GMThrow
from time import perf_counter as _pc
from .values import (GMArray, GMStruct, GMInstance, GMFunc, GMMethod, BuiltinRef, GMEnum, GlobalRef,
                     MISS, FIRST_INSTANCE_ID, NOONE, typeof, gml_str, GLOBAL_REF)

BRK = 1
CNT = 2
RET = 3


class Frame:
    __slots__ = ("sim", "self", "other", "loc", "args", "ret", "statics", "ev", "fn")

    def __init__(self, sim, self_obj, other, args, ev=None, fn=None):
        self.sim = sim
        self.self = self_obj
        self.other = other
        self.loc = {}
        self.args = args
        self.ret = None
        self.statics = None
        self.ev = ev
        self.fn = fn


def share(v):
    if v.__class__ is GMArray:
        v.cow = True
    return v


# ------------------------------------------------------------------ errors

def err_no_instance(n):
    return GMError("Unable to find instance for object index %s" % (n,), "no_instance")


def global_name_index(sim, name):
    idx = sim.global_name_ids.get(name)
    if idx is None:
        idx = 100000 + len(sim.global_name_ids)
        sim.global_name_ids[name] = idx
    return idx


def err_global_is_function(name):
    # GameMaker binds every script function to the global variable of the same name, so global.<function name> reads
    # (or overwrites) the function itself. gmlsim keeps them apart, so it refuses the collision instead of hiding it.
    return GMError("global.%s collides with the script function %s(): in GameMaker that global IS the function "
                   "(functions are bound to globals), so this read/write does not do what it looks like" % (name, name),
                   "global_is_function")


def err_global_unset(sim, name):
    if name in getattr(sim, "scripts", ()):
        return err_global_is_function(name)
    return GMError("global variable name '%s' index (%d) not set before reading it" % (name, global_name_index(sim, name)),
                   "global_not_set")


def err_unset(owner, name):
    return GMError("Variable %s.%s not set before reading it" % (owner, name), "var_not_set")


def err_local_unset(sim, name):
    return GMError("local variable '%s' not set before reading it" % name, "local_not_set")


# ------------------------------------------------------------------ instances / fields

def resolve_instance(f, n):
    sim = f.sim
    if n.__class__ is not int:
        if n.__class__ is float and n == int(n):
            n = int(n)
        else:
            raise GMError("Unable to use %r as an instance reference" % (n,), "type")
    if n >= FIRST_INSTANCE_ID:
        inst = sim.instances.get(n)
        if inst is None:
            # GameMaker: a deactivated instance's variables can still be read / written through its id
            inst = sim.deact.get(n)
            if inst is None:
                # ... and a destroyed one's until the event that destroyed it is over (sim.grave)
                inst = sim.grave.get(n)
                if inst is None:
                    raise err_no_instance(n)
        return inst
    if n >= 0:
        inst = sim.first_of(n)
        if inst is None:
            raise err_no_instance(n)
        return inst
    if n == -1:
        return f.self
    if n == -2:
        if f.other is None:
            raise err_no_instance(n)
        return f.other
    if n == -5:
        return GLOBAL_REF
    raise err_no_instance(n)


def vars_of(f, o):
    t = o.__class__
    if t is GMInstance or t is GMStruct:
        return o.vars
    if t is GlobalRef:
        return f.sim.globals
    if t is int or t is bool or t is float or t.__name__ == "GMInt64":
        r = resolve_instance(f, int(o))
        if r.__class__ is GlobalRef:
            return f.sim.globals
        return r.vars
    if o is None:
        raise GMError("Unable to access a variable of undefined", "type")
    raise GMError("Unable to access a variable of %s" % typeof(o), "type")


def field_missing(f, o, name):
    """Called when a field is absent from o.vars (o is Instance/Struct/GlobalRef/number)."""
    sim = f.sim
    t = o.__class__
    if t is GlobalRef:
        raise err_global_unset(sim, name)
    if t is int or t is float or t is bool or t.__name__ == "GMInt64":
        o = resolve_instance(f, int(o))
        if o.__class__ is GlobalRef:
            raise err_global_unset(sim, name)
        if name in o.vars:
            return o.vars[name]
    if o.__class__ is GMStruct:
        c = o.ctor
        while c is not None:
            st = sim.statics.get(c)
            if st is not None and name in st:
                return st[name]
            c = sim.ctor_parent(c)
        raise err_unset(o.name, name)
    raise err_unset(o.name, name)


def get_field(f, o, name):
    t = o.__class__
    if t is GMInstance or t is GMStruct:
        try:
            return o.vars[name]
        except KeyError:
            return field_missing(f, o, name)
    if t is GlobalRef:
        try:
            return f.sim.globals[name]
        except KeyError:
            raise err_global_unset(f.sim, name)
    if t is GMEnum:
        try:
            return o.members[name]
        except KeyError:
            raise GMError("enum %s has no member '%s'" % (o.name, name), "enum")
    if t is int or t is float or t is bool or t.__name__ == "GMInt64":
        r = resolve_instance(f, int(o))
        if r.__class__ is GlobalRef:
            return get_field(f, r, name)
        try:
            return r.vars[name]
        except KeyError:
            return field_missing(f, r, name)
    if o is None:
        raise GMError("Unable to read field '%s' of undefined" % name, "type")
    raise GMError("Unable to read field '%s' of %s" % (name, typeof(o)), "type")


def set_field(f, o, name, v):
    t = o.__class__
    if t is GMInstance or t is GMStruct:
        o.vars[name] = v
        return
    if t is GlobalRef and name in f.sim.scripts:
        raise err_global_is_function(name)
    vars_of(f, o)[name] = v


# ------------------------------------------------------------------ arrays

def to_index(i, what="array index"):
    t = i.__class__
    if t is int:
        return i
    if t.__name__ == "GMInt64":
        return int(i)
    if t is float:
        return int(i)
    if t is bool:
        return int(i)
    if t is GMInstance:
        return i.id
    raise GMError("%s must be a number, got %s" % (what, typeof(i) if i is not None else "undefined"), "type")


def err_oor(i, n):
    return GMError("Array index out of range: index [%d] not in [0..%d) (array length %d)" % (i, n, n), "array_oob")


def not_array(a):
    return GMError("Variable is not an array (it is %s)" % (typeof(a) if a is not None else "undefined"), "type")


def array_get(a, i):
    if a.__class__ is not GMArray:
        raise not_array(a)
    if i.__class__ is not int:
        i = to_index(i)
    d = a.data
    if 0 <= i < len(d):
        return d[i]
    raise err_oor(i, len(d))


def array_set(a, i, v):
    if i.__class__ is not int:
        i = to_index(i)
    d = a.data
    if i < 0:
        raise GMError("Array index out of range: cannot write negative index [%d]" % i, "array_oob")
    n = len(d)
    if i < n:
        d[i] = v
    else:
        if i > 32000000:
            raise GMError("Array index %d is too large" % i, "array_oob")
        if i > n:
            d.extend([0] * (i - n))
        d.append(v)


def elem_for_write(arr, i):
    """Return the (uncow'd, possibly auto-created) nested array stored at arr[i]."""
    if i.__class__ is not int:
        i = to_index(i)
    d = arr.data
    if i < 0:
        raise GMError("Array index out of range: cannot write negative index [%d]" % i, "array_oob")
    cur = d[i] if i < len(d) else MISS
    if cur.__class__ is GMArray:
        if cur.cow:
            cur = cur.copy()
            d[i] = cur
        return cur
    if cur is MISS or cur is None or cur.__class__ in (int, float, bool, str):
        new = GMArray()
        array_set(arr, i, new)
        return new
    raise not_array(cur)


# ------------------------------------------------------------------ ds accessors

def ds_get(f, kind, c, idx):
    sim = f.sim
    if kind == "|":
        lst = sim.ds_list(c)
        i = to_index(idx[0])
        if 0 <= i < len(lst):
            return lst[i]
        raise GMError("ds_list index %d out of range (size %d)" % (i, len(lst)), "ds_oob")
    if kind == "?":
        m = sim.ds_map(c)
        return m.get(idx[0])
    if kind == "#":
        g = sim.ds_grid(c)
        x, y = to_index(idx[0]), to_index(idx[1])
        if 0 <= x < g["w"] and 0 <= y < g["h"]:
            return g["d"][x][y]
        raise GMError("ds_grid index (%d,%d) out of range" % (x, y), "ds_oob")
    if kind == "$":
        o = c
        key = idx[0]
        if key.__class__ is not str:
            key = gml_str(key)
        if o.__class__ is GMStruct or o.__class__ is GMInstance:
            return o.vars.get(key)
        return vars_of(f, o).get(key)
    raise GMError("bad accessor %s" % kind)


def ds_set(f, kind, c, idx, v):
    sim = f.sim
    if kind == "|":
        lst = sim.ds_list(c)
        i = to_index(idx[0])
        if 0 <= i < len(lst):
            lst[i] = v
            return
        # (a write past the end: GameMaker's ds_list_set - padded with 0s)
        if i >= 0:
            while len(lst) < i:
                lst.append(0)
            lst.append(v)
            return
        raise GMError("ds_list index %d out of range (size %d)" % (i, len(lst)), "ds_oob")
    if kind == "?":
        sim.ds_map(c)[idx[0]] = v
        return
    if kind == "#":
        g = sim.ds_grid(c)
        x, y = to_index(idx[0]), to_index(idx[1])
        if 0 <= x < g["w"] and 0 <= y < g["h"]:
            g["d"][x][y] = v
            return
        raise GMError("ds_grid index (%d,%d) out of range" % (x, y), "ds_oob")
    if kind == "$":
        key = idx[0]
        if key.__class__ is not str:
            key = gml_str(key)
        vars_of(f, c)[key] = v
        return
    raise GMError("bad accessor %s" % kind)


# ------------------------------------------------------------------ calls

# profiling (off unless a test sets rt.PROF = {}): {name: [calls, inclusive seconds, exclusive seconds]}; builtins as "B:name"
PROF = None
_PSTACK = []


def prof_enter():
    _PSTACK.append(0.0)
    return _pc()


def prof_leave(name, t0):
    dt = _pc() - t0
    child = _PSTACK.pop() if _PSTACK else 0.0
    e = PROF.get(name)
    if e is None:
        e = PROF[name] = [0, 0.0, 0.0]
    e[0] += 1
    e[1] += dt
    e[2] += dt - child
    if _PSTACK:
        _PSTACK[-1] += dt


def call_func(sim, fn, args, so, other, ev=None):
    if PROF is not None:
        t0 = prof_enter()
        try:
            return _call_func(sim, fn, args, so, other, ev)
        finally:
            if PROF is not None:
                prof_leave(fn.name, t0)
    return _call_func(sim, fn, args, so, other, ev)


def _call_func(sim, fn, args, so, other, ev=None):
    fr = Frame(sim, so, other, args, ev, fn)
    loc = fr.loc
    na = len(args)
    i = 0
    for pn, pd in fn.params:
        if i < na:
            v = args[i]
            if v is None and pd is not None:
                v = pd(fr)
            elif v.__class__ is GMArray:
                v.cow = True
        elif pd is not None:
            v = pd(fr)
        else:
            v = None
        loc[pn] = v
        i += 1
    if fn.static_names:
        st = sim.statics.get(fn)
        if st is None:
            st = sim.statics[fn] = {}
        fr.statics = st
    sim.depth += 1
    try:
        if sim.depth > sim.max_depth:
            raise GMError("Stack overflow: call depth exceeded %d (recursion in %s?)" % (sim.max_depth, fn.name), "stack")
        fn.body(fr)
    except GMError as e:
        e.stack.append(fn.name)
        raise
    finally:
        sim.depth -= 1
    return fr.ret


def call_ctor(sim, fn, args, struct, ev=None):
    fr = Frame(sim, struct, None, args, ev, fn)
    loc = fr.loc
    na = len(args)
    i = 0
    for pn, pd in fn.params:
        if i < na:
            v = args[i]
            if v is None and pd is not None:
                v = pd(fr)
            elif v.__class__ is GMArray:
                v.cow = True
        elif pd is not None:
            v = pd(fr)
        else:
            v = None
        loc[pn] = v
        i += 1
    if fn.static_names:
        st = sim.statics.get(fn)
        if st is None:
            st = sim.statics[fn] = {}
        fr.statics = st
    sim.depth += 1
    try:
        if sim.depth > sim.max_depth:
            raise GMError("Stack overflow in constructor %s" % fn.name, "stack")
        if fn.parent is not None:
            pname, pargs = fn.parent
            pfn = sim.get_callable(pname, fr)
            if pfn.__class__ is GMMethod:
                pfn = pfn.func
            if pfn.__class__ is not GMFunc or not pfn.ctor:
                raise GMError("Parent '%s' of constructor %s is not a constructor" % (pname, fn.name), "type")
            call_ctor(sim, pfn, [a(fr) for a in pargs], struct, ev)
        fn.body(fr)
    except GMError as e:
        e.stack.append(fn.name)
        raise
    finally:
        sim.depth -= 1
    return struct


def call_value(f, fv, args, self_obj=None):
    """Call a GML callable value from frame f. self_obj overrides self for unbound functions."""
    t = fv.__class__
    sim = f.sim
    if t is GMMethod:
        so = fv.self_obj
        if so is None:
            so = self_obj if self_obj is not None else f.self
        fn = fv.func
        return call_func(sim, fn, args, so, f.other if so is f.self else f.self, f.ev)
    if t is GMFunc:
        so = self_obj if self_obj is not None else f.self
        return call_func(sim, fv, args, so, f.other if so is f.self else f.self, f.ev)
    if t is BuiltinRef:
        return sim.call_builtin(fv.name, f, args)
    if t is int or t is float or t.__name__ == "GMInt64":
        fn = sim.script_by_index(int(fv))
        if fn is not None:
            return call_value(f, fn, args, self_obj)
    if t is str:
        fn = sim.get_callable(fv, f, quiet=True)
        if fn is not None:
            return call_value(f, fn, args, self_obj)
    raise GMError("Unable to call %s: it is not a function/method" % (gml_str(fv) if fv is not None else "undefined"), "not_callable")
