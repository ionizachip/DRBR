"""Default builtin function registry. Library modules register with @builtin."""

DEFAULT_BUILTINS = {}      # name -> (fn, needs_frame)
DEFAULT_CONSTS = {}        # name -> value
DEFAULT_VARS = {}          # name -> value | callable(sim)


def builtin(*names, frame=False):
    def deco(fn):
        for n in (names or (fn.__name__,)):
            DEFAULT_BUILTINS[n] = (fn, frame)
        return fn
    return deco


def const(**kw):
    DEFAULT_CONSTS.update(kw)


def gvar(name, value):
    DEFAULT_VARS[name] = value
