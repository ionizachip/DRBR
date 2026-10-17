"""Runtime value types and conversion helpers."""
import math

from .errors import GMError


class _Sentinel:
    __slots__ = ("name",)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<%s>" % self.name

    def __deepcopy__(self, memo):
        return self


MISS = _Sentinel("MISS")
NOONE = -4
ALL = -3
SELF = -1
OTHER = -2
GLOBAL = -5
FIRST_INSTANCE_ID = 100000


class GMArray:
    """GML array. Copy-on-write value semantics: `cow` means "possibly shared";
    the first indexed write through any holder copies it first."""
    __slots__ = ("data", "cow")

    def __init__(self, data=None):
        self.data = data if data is not None else []
        self.cow = False

    def copy(self):
        d = self.data[:]
        for x in d:
            if x.__class__ is GMArray:
                x.cow = True
        return GMArray(d)

    def __repr__(self):
        return "GMArray(%r)" % (self.data,)


class GMStruct:
    __slots__ = ("vars", "ctor", "name")

    def __init__(self, vars=None, ctor=None):
        self.vars = vars if vars is not None else {}
        self.ctor = ctor          # GMFunc (constructor) or None
        self.name = "struct"

    def __repr__(self):
        return "GMStruct(%r)" % (self.vars,)


class GMInstance:
    __slots__ = ("id", "obj", "vars", "dead", "name")

    def __init__(self, id, obj):
        self.id = id
        self.obj = obj
        self.name = obj
        self.vars = {}
        self.dead = False

    def __getitem__(self, k):
        return self.vars[k]

    def __setitem__(self, k, v):
        self.vars[k] = v

    def get(self, k, default=None):
        return self.vars.get(k, default)

    def __repr__(self):
        return "<inst %s#%d>" % (self.obj, self.id)


class GMFunc:
    """Compiled function (immutable; shared between sims and snapshots)."""
    __slots__ = ("name", "params", "body", "ctor", "parent", "decl", "static_names", "entry", "line", "nparams")

    def __init__(self, name, params, body, ctor, parent, decl, static_names, entry, line):
        self.name = name
        self.params = params      # list of (name, default_closure|None)
        self.nparams = len(params)
        self.body = body
        self.ctor = ctor
        self.parent = parent      # (name, args_closures) or None
        self.decl = decl
        self.static_names = static_names
        self.entry = entry
        self.line = line

    def __deepcopy__(self, memo):
        return self

    def __repr__(self):
        return "<function %s>" % (self.name,)


class GMInt64(int):
    """an int64 value: what GameMaker's bitwise operators (& | ^ ~ << >>) and int64() return. It is a number like any
    other in arithmetic, but is_real() is false for it and typeof() says "int64" - code that checks is_real() on such a value
    behaves as in the real runtime."""
    __slots__ = ()

    def __repr__(self):
        return "int64(%d)" % int(self)


class GMMethod:
    __slots__ = ("func", "self_obj")

    def __init__(self, func, self_obj):
        self.func = func
        self.self_obj = self_obj

    def __repr__(self):
        return "<method %s>" % (self.func.name,)


class BuiltinRef:
    """A builtin function used as a value (e.g. passed to script_execute)."""
    __slots__ = ("name",)

    def __init__(self, name):
        self.name = name

    def __deepcopy__(self, memo):
        return self


class GMEnum:
    __slots__ = ("name", "members")

    def __init__(self, name, members):
        self.name = name
        self.members = members

    def __deepcopy__(self, memo):
        return self


class GlobalRef:
    __slots__ = ()

    def __deepcopy__(self, memo):
        return self


GLOBAL_REF = GlobalRef()


class GMHandle:
    """A typed runtime handle ("ref buffer 3", "ref socket 0"), as newer GameMaker runtimes return from buffer_create /
    network_create_socket. Only used when a test turns handle mode on (lib_net): is_real/is_numeric are false for it,
    it equals only the same handle, and comparing it with < or > is refused (the real runtime's rules are not known)."""
    __slots__ = ("kind", "index")

    def __init__(self, kind, index):
        self.kind = kind
        self.index = int(index)

    def __eq__(self, o):
        return o.__class__ is GMHandle and o.kind == self.kind and o.index == self.index

    def __ne__(self, o):
        return not self.__eq__(o)

    def __hash__(self):
        return hash((self.kind, self.index))

    def __repr__(self):
        return "ref %s %d" % (self.kind, self.index)

    def __deepcopy__(self, memo):
        return self


class MacroVal:
    __slots__ = ("name", "text")

    def __init__(self, name, text):
        self.name = name
        self.text = text

    def __deepcopy__(self, memo):
        return self


# ---------------------------------------------------------------- formatting

def fmt_real(v):
    if v != v:
        return "NaN" if True else "nan"
    if v == math.inf:
        return "infinity"
    if v == -math.inf:
        return "-infinity"
    if v == int(v):
        return str(int(v))
    s = "%.2f" % v
    s = s.rstrip("0").rstrip(".")
    if s in ("", "-", "-0"):
        return "0"
    return s


def gml_str(v):
    """string(v)"""
    t = v.__class__
    if t is str:
        return v
    if t is int or t is GMInt64:
        return str(int(v))
    if t is float:
        return fmt_real(v)
    if t is bool:
        return "true" if v else "false"
    if v is None:
        return "undefined"
    if t is GMArray:
        return "[ " + ",".join(gml_repr(x) for x in v.data) + " ]"
    if t is GMStruct:
        return "{ " + ", ".join("%s : %s" % (k, gml_repr(x)) for k, x in v.vars.items()) + " }"
    if t is GMInstance:
        return str(v.id)
    if t is GMFunc or t is GMMethod:
        return "function"
    if t is GMHandle:
        return repr(v)
    return str(v)


def gml_repr(v):
    if v.__class__ is str:
        return '"%s"' % v
    return gml_str(v)


def typeof(v):
    t = v.__class__
    if t is str:
        return "string"
    if t is int or t is float:
        return "number"
    if t is GMInt64:
        return "int64"
    if t is bool:
        return "bool"
    if v is None:
        return "undefined"
    if t is GMArray:
        return "array"
    if t is GMStruct:
        return "struct"
    if t is GMMethod or t is GMFunc or t is BuiltinRef:
        return "method"
    if t is GMInstance or t is GMHandle:
        return "ref"
    return "unknown"


def is_num(v):
    t = v.__class__
    return t is int or t is float or t is bool or t is GMInt64


def to_py(v):
    """Recursively convert GML values to plain Python (arrays->list, structs->dict)."""
    t = v.__class__
    if t is GMArray:
        return [to_py(x) for x in v.data]
    if t is GMStruct:
        return {k: to_py(x) for k, x in v.vars.items()}
    if t is GMInstance:
        return v.id
    if t is GMHandle:
        return v.index
    return v


def from_py(v):
    if isinstance(v, (list, tuple)):
        a = GMArray([from_py(x) for x in v])
        return a
    if isinstance(v, dict):
        s = GMStruct()
        for k, x in v.items():
            s.vars[str(k)] = from_py(x)
        return s
    if isinstance(v, GMInstance):
        return v.id
    return v
