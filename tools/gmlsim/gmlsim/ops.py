"""GML operator semantics (slow paths; the compiler inlines int/float fast paths)."""
import math

from .errors import GMError
from .values import GMArray, GMStruct, GMInstance, GMInt64, gml_str, typeof


def _tn(v):
    t = v.__class__
    if t is str:
        return 'string "%s"' % v
    return typeof(v) if v is not None else "undefined"


def num(v, what="operand"):
    t = v.__class__
    if t is int or t is float:
        return v
    if t is GMInt64:
        return int(v)
    if t is bool:
        return 1 if v else 0
    if t is GMInstance:
        return v.id
    raise GMError("Unable to convert %s to a number (%s)" % (_tn(v), what), "type")


def truth(v):
    if v is True:
        return True
    if v is False:
        return False
    t = v.__class__
    if t is int or t is float or t is GMInt64:
        return v >= 0.5
    if v is None:
        raise GMError("Unable to convert undefined to a boolean", "type")
    if t is str:
        raise GMError('Unable to convert string "%s" to a boolean' % v, "type")
    if t is GMInstance:
        return True
    if t.__name__ in ('GMMethod', 'GMFunc', 'BuiltinRef'):
        # a script function named without a call (`if (!scr_debug)` in Cyan Knight's arena code) is a script reference in the
        # real runtime, never 0: true
        return True
    raise GMError("Unable to convert %s to a boolean" % typeof(v), "type")


def add(a, b):
    ta, tb = a.__class__, b.__class__
    if ta is str and tb is str:
        return a + b
    if ta is str or tb is str:
        raise GMError("Unable to add %s and %s (cannot mix string and number)" % (_tn(a), _tn(b)), "type")
    return num(a, "left of +") + num(b, "right of +")


def sub(a, b):
    return num(a, "left of -") - num(b, "right of -")


def mul(a, b):
    return num(a, "left of *") * num(b, "right of *")


def div_zero(sim_opts=None):
    raise GMError("Division by zero", "div0")


def truediv(a, b):
    x, y = num(a, "left of /"), num(b, "right of /")
    if y == 0:
        return _div0(x, "/")
    return x / y


def _div0(x, op):
    # "real": the GameMaker 2.3+ runner - a real division by zero is IEEE (inf / -inf / nan, is_infinity() exists for it;
    # DELTARUNE Chapter 4's shipped Gerson fight divides by a 0 spear speed every red-hammer fakeout); div / mod still fail
    if DIV0_MODE[0] == "error" or (DIV0_MODE[0] == "real" and op != "/"):
        raise GMError("Division by zero", "div0")
    DIV0_SEEN[0] += 1
    if op == "mod":
        return math.nan
    if x == 0:
        return math.nan
    return math.inf if x > 0 else -math.inf


DIV0_MODE = ["error"]   # "error" | "inf" | "real"; Sim syncs this
DIV0_SEEN = [0]         # real divisions by zero let through (inf / real modes)


def intdiv(a, b):
    x, y = num(a, "left of div"), num(b, "right of div")
    if y == 0:
        return _div0(x, "div")
    return int(x / y)


def mod(a, b):
    x, y = num(a, "left of mod"), num(b, "right of mod")
    if y == 0:
        return _div0(x, "mod")
    if x.__class__ is int and y.__class__ is int:
        r = abs(x) % abs(y)
        return -r if x < 0 else r
    return math.fmod(x, y)


def _i64(v):
    v = int(num(v))
    v &= 0xFFFFFFFFFFFFFFFF
    return v - (1 << 64) if v >= (1 << 63) else v


def band(a, b):
    return GMInt64(_i64(a) & _i64(b))


def bor(a, b):
    return GMInt64(_i64(a) | _i64(b))


def bxor(a, b):
    return GMInt64(_i64(a) ^ _i64(b))


def shl(a, b):
    return GMInt64(_i64(_i64(a) << (_i64(b) & 63)))


def shr(a, b):
    return GMInt64(_i64(a) >> (_i64(b) & 63))


def bnot(a):
    return GMInt64(~_i64(a))


def eq(a, b):
    if a == b:
        return True
    ta, tb = a.__class__, b.__class__
    if (ta is float or tb is float) and ta is not str and tb is not str and a is not None and b is not None:
        try:
            return abs(a - b) < 1e-5
        except TypeError:
            return False
    if ta is GMInstance and (tb is int or tb is GMInt64):
        return a.id == b
    if tb is GMInstance and (ta is int or ta is GMInt64):
        return b.id == a
    return False


def cmp_check(a, b, op):
    ta, tb = a.__class__, b.__class__
    if ta is str and tb is str:
        return a, b
    if ta is str or tb is str:
        raise GMError("Unable to compare %s %s %s" % (_tn(a), op, _tn(b)), "type")
    return num(a, "left of " + op), num(b, "right of " + op)


# GameMaker compares reals within its epsilon (math_get_epsilon(), 0.00001) for EVERY comparison, not only == / !=: two reals
# that close are equal, so neither is less than the other (-1e-14 < 0 is false - Chapter 5's scr_wrap relies on it: a lane
# direction a hair under 0 would otherwise loop for ever between -1e-14 and 361)
def lt(a, b):
    x, y = cmp_check(a, b, "<")
    if x.__class__ is float or y.__class__ is float:
        return x < y and not abs(x - y) < 1e-5
    return x < y


def le(a, b):
    x, y = cmp_check(a, b, "<=")
    if x.__class__ is float or y.__class__ is float:
        return x <= y or abs(x - y) < 1e-5
    return x <= y


def gt(a, b):
    x, y = cmp_check(a, b, ">")
    if x.__class__ is float or y.__class__ is float:
        return x > y and not abs(x - y) < 1e-5
    return x > y


def ge(a, b):
    x, y = cmp_check(a, b, ">=")
    if x.__class__ is float or y.__class__ is float:
        return x >= y or abs(x - y) < 1e-5
    return x >= y


def coalesce(a, b):
    return b if a is None else a


def ne(a, b):
    return not eq(a, b)


BINOPS = {
    "!=": ne,
    "+": add, "-": sub, "*": mul, "/": truediv, "div": intdiv, "%": mod,
    "&": band, "|": bor, "^": bxor, "<<": shl, ">>": shr, "??": coalesce,
    "==": eq, "<": lt, "<=": le, ">": gt, ">=": ge,
}
