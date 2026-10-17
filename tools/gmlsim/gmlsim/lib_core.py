"""Core builtins: math, string, array, types, struct/variable, ds_*, random, json."""
import math

from . import ops
from .errors import GMError
from .registry import builtin, const, gvar
from .rt import call_value, resolve_instance, vars_of, share
from .values import (GMArray, GMStruct, GMInstance, GMFunc, GMMethod, BuiltinRef, MISS, gml_str, typeof,
                     from_py, to_py, is_num, GLOBAL_REF, FIRST_INSTANCE_ID)

const(pi=math.pi, infinity=math.inf, NaN=math.nan, true=True, false=False, undefined=None, noone=-4, all=-3,
      c_white=16777215, c_black=0, c_red=255, c_green=32768, c_blue=16711680, c_yellow=65535, c_lime=65280,
      c_aqua=16776960, c_fuchsia=16711935, c_gray=8421504, c_grey=8421504, c_ltgray=12632256,
      c_dkgray=4210752, c_orange=4235519, c_maroon=128, c_navy=8388608, c_olive=32896, c_purple=8388736,
      c_silver=12632256, c_teal=8421376, fa_left=0, fa_center=1, fa_right=2, fa_top=0, fa_middle=1,
      fa_bottom=2, bm_normal=0, bm_add=1, bm_max=2, bm_subtract=3, bm_zero=0, bm_one=1, bm_src_alpha=6,
      bm_inv_src_alpha=7, bm_src_color=2, bm_inv_src_color=3, bm_dest_color=4, bm_inv_dest_color=5,
      bm_dest_alpha=8, bm_inv_dest_alpha=9, bm_src_alpha_sat=10,
      ev_create=0, ev_destroy=1, ev_alarm=2, ev_step=3, ev_collision=4, ev_keyboard=5, ev_mouse=6,
      ev_other=7, ev_draw=8, ev_keypress=9, ev_keyrelease=10, ev_cleanup=12, ev_gesture=13,
      ev_step_normal=0, ev_step_begin=1, ev_step_end=2, ev_draw_normal=0, ev_gui=64, ev_draw_begin=72,
      ev_draw_end=73, ev_gui_begin=74, ev_gui_end=75,
      ev_room_start=4, ev_room_end=5, ev_game_start=2, ev_game_end=3, ev_animation_end=7, ev_user0=10,
      ev_user1=11, ev_user2=12, ev_user3=13, ev_user4=14, ev_user5=15, ev_user6=16, ev_user7=17,
      ev_user8=18, ev_user9=19, ev_user10=20, ev_user11=21, ev_user12=22, ev_user13=23, ev_user14=24,
      ev_user15=25,
      os_windows=0, os_macosx=1, os_psp=2, os_ios=3, os_android=4, os_symbian=5, os_linux=6, os_winphone=7,
      os_tizen=8, os_win8native=9, os_wiiu=10, os_3ds=11, os_psvita=12, os_bb10=13, os_ps4=14,
      os_xboxone=15, os_ps3=16, os_xbox360=17, os_uwp=18, os_tvos=20, os_switch=21, os_ps5=22, os_gdk=23,
      os_unknown=-1, browser_not_a_browser=-1,
      pr_pointlist=1, pr_linelist=2, pr_linestrip=3, pr_trianglelist=4, pr_trianglestrip=5, pr_trianglefan=6,
      cr_default=0, cr_none=-1, cr_arrow=-2, cr_cross=-3, cr_beam=-4, cr_size_all=-22,
      audio_stereo=0, audio_mono=1, audio_3d=2, buffer_fixed=0, buffer_grow=1, buffer_wrap=2, buffer_fast=3,
      buffer_u8=1, buffer_s8=2, buffer_u16=3, buffer_s16=4, buffer_u32=5, buffer_s32=6, buffer_f16=7,
      buffer_f32=8, buffer_f64=9, buffer_bool=10, buffer_string=11, buffer_u64=12, buffer_text=13,
      tf_point=0, tf_linear=1, tf_anisotropic=2, mean_dummy=0, lb_dummy=0,
      ds_type_map=1, ds_type_list=2, ds_type_grid=3,
      layerelementtype_undefined=0, layerelementtype_background=1, layerelementtype_instance=2,
      layerelementtype_oldtilemap=3, layerelementtype_sprite=4, layerelementtype_tilemap=5,
      layerelementtype_particlesystem=6, layerelementtype_tile=7,
      path_action_stop=0, path_action_restart=1, path_action_continue=2, path_action_reverse=3,
      display_landscape=0, display_landscape_flipped=1, display_portrait=2, display_portrait_flipped=3,
      lighttype_dir=0, lighttype_point=1, fa_readonly=1, fa_hidden=2, fa_sysfile=4, fa_volumeid=8,
      fa_directory=16, fa_archive=32, spritespeed_framespersecond=0, spritespeed_framespergameframe=1,
      mb_dummy=0, device_ios_unknown=0, gm_dummy=0)


def _s(v, fn, n=1):
    if v.__class__ is str:
        return v
    raise GMError("%s(): argument %d must be a string, got %s" % (fn, n, typeof(v) if v is not None else "undefined"), "type")


def _n(v):
    return ops.num(v)


def _i(v):
    t = v.__class__
    if t is int:
        return v
    if t.__name__ == "GMInt64":
        return int(v)
    return int(ops.num(v))


# ------------------------------------------------------------------ math
@builtin()
def floor(sim, x):
    return math.floor(_n(x))


@builtin()
def ceil(sim, x):
    return math.ceil(_n(x))


@builtin()
def round(sim, x):
    import builtins
    x = _n(x)
    return builtins.round(x) if x == x and x != math.inf and x != -math.inf else x


@builtin()
def abs(sim, x):
    import builtins
    return builtins.abs(_n(x))


@builtin()
def sign(sim, x):
    x = _n(x)
    return (x > 0) - (x < 0)


@builtin()
def min(sim, *a):
    import builtins
    if not a:
        raise GMError("min() requires at least one argument", "builtin_args")
    return builtins.min(_n(x) for x in a)


@builtin()
def max(sim, *a):
    import builtins
    if not a:
        raise GMError("max() requires at least one argument", "builtin_args")
    return builtins.max(_n(x) for x in a)


@builtin()
def clamp(sim, v, lo, hi):
    v, lo, hi = _n(v), _n(lo), _n(hi)
    return lo if v < lo else hi if v > hi else v


@builtin()
def sqrt(sim, x):
    x = _n(x)
    if x < 0:
        raise GMError("sqrt of negative number", "math")
    return math.sqrt(x)


@builtin()
def sqr(sim, x):
    x = _n(x)
    return x * x


@builtin()
def power(sim, a, b):
    try:
        return math.pow(_n(a), _n(b))
    except (ValueError, OverflowError):
        return math.nan


@builtin()
def exp(sim, x):
    return math.exp(_n(x))


@builtin()
def ln(sim, x):
    return math.log(_n(x))


@builtin()
def log2(sim, x):
    return math.log2(_n(x))


@builtin()
def log10(sim, x):
    return math.log10(_n(x))


@builtin()
def logn(sim, n, x):
    return math.log(_n(x), _n(n))


def _trig(name, fn):
    builtin(name)(lambda sim, x, _f=fn: _f(_n(x)))


for _nm, _fn in (("sin", math.sin), ("cos", math.cos), ("tan", math.tan), ("arcsin", math.asin),
                 ("arccos", math.acos), ("arctan", math.atan)):
    _trig(_nm, _fn)


@builtin()
def arctan2(sim, y, x):
    return math.atan2(_n(y), _n(x))


@builtin()
def dsin(sim, x):
    return math.sin(math.radians(_n(x)))


@builtin()
def dcos(sim, x):
    return math.cos(math.radians(_n(x)))


@builtin()
def dtan(sim, x):
    return math.tan(math.radians(_n(x)))


@builtin()
def darctan2(sim, y, x):
    return math.degrees(math.atan2(_n(y), _n(x)))


@builtin()
def degtorad(sim, x):
    return math.radians(_n(x))


@builtin()
def radtodeg(sim, x):
    return math.degrees(_n(x))


@builtin()
def lengthdir_x(sim, l, d):
    return _n(l) * math.cos(math.radians(_n(d)))


@builtin()
def lengthdir_y(sim, l, d):
    return -_n(l) * math.sin(math.radians(_n(d)))


@builtin()
def point_distance(sim, x1, y1, x2, y2):
    return math.hypot(_n(x2) - _n(x1), _n(y2) - _n(y1))


@builtin()
def point_direction(sim, x1, y1, x2, y2):
    d = math.degrees(math.atan2(-(_n(y2) - _n(y1)), _n(x2) - _n(x1)))
    return d % 360


@builtin()
def angle_difference(sim, a, b):
    return ((_n(a) - _n(b) + 180) % 360) - 180


@builtin()
def lerp(sim, a, b, t):
    a, b, t = _n(a), _n(b), _n(t)
    return a + (b - a) * t


@builtin()
def frac(sim, x):
    x = _n(x)
    return x - math.trunc(x)


@builtin()
def mean(sim, *a):
    return sum(_n(x) for x in a) / len(a)


@builtin()
def median(sim, *a):
    s = sorted(_n(x) for x in a)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


@builtin()
def is_nan(sim, x):
    return is_num(x) and x != x


@builtin()
def is_infinity(sim, x):
    return is_num(x) and x in (math.inf, -math.inf)


@builtin()
def point_in_rectangle(sim, px, py, x1, y1, x2, y2):
    return x1 <= px <= x2 and y1 <= py <= y2


@builtin()
def rectangle_in_rectangle(sim, ax1, ay1, ax2, ay2, bx1, by1, bx2, by2):
    return 1 if (ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1) else 0


@builtin("make_color_rgb", "make_colour_rgb")
def make_color_rgb(sim, r, g, b):
    return (_i(b) << 16) | (_i(g) << 8) | _i(r)


@builtin("make_color_hsv", "make_colour_hsv")
def make_color_hsv(sim, h, s, v):
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(_n(h) / 255, _n(s) / 255, _n(v) / 255)
    return make_color_rgb(sim, int(r * 255), int(g * 255), int(b * 255))


@builtin("color_get_red", "colour_get_red")
def color_get_red(sim, c):
    return _i(c) & 255


@builtin("color_get_green", "colour_get_green")
def color_get_green(sim, c):
    return (_i(c) >> 8) & 255


@builtin("color_get_blue", "colour_get_blue")
def color_get_blue(sim, c):
    return (_i(c) >> 16) & 255


@builtin("merge_color", "merge_colour")
def merge_color(sim, c1, c2, t):
    c1, c2, t = _i(c1), _i(c2), _n(t)
    out = 0
    for sh in (0, 8, 16):
        a, b = (c1 >> sh) & 255, (c2 >> sh) & 255
        out |= (int(a + (b - a) * t) & 255) << sh
    return out


# ------------------------------------------------------------------ random
@builtin()
def random(sim, n, *extra):
    # extra arguments are ignored by the runtime (Chapter 3 calls random(12, 30))
    return sim.rng.random() * _n(n)


@builtin()
def irandom(sim, n):
    n = _i(n)
    if n < 0:
        raise GMError("irandom() argument must be >= 0", "builtin_args")
    return sim.rng.randint(0, n)


@builtin()
def random_range(sim, a, b):
    a, b = _n(a), _n(b)
    return a + sim.rng.random() * (b - a)


@builtin()
def irandom_range(sim, a, b):
    a, b = _i(a), _i(b)
    if a > b:
        a, b = b, a
    return sim.rng.randint(a, b)


@builtin()
def choose(sim, *a):
    if not a:
        raise GMError("choose() requires arguments", "builtin_args")
    return a[sim.rng.randrange(len(a))]


@builtin()
def random_set_seed(sim, s):
    sim.rng.seed(_i(s))
    sim.seed = _i(s)
    return 0


@builtin()
def random_get_seed(sim):
    return sim.seed


@builtin()
def randomize(sim):
    sim.rng.seed(sim.rng.random())
    return 0


# ------------------------------------------------------------------ strings
@builtin()
def string(sim, v, *rest):
    s = gml_str(v)
    if rest:
        for i, r in enumerate(rest):
            s = s.replace("{%d}" % i, gml_str(r))
    return s


@builtin()
def string_length(sim, s):
    return len(_s(s, "string_length"))


@builtin()
def string_copy(sim, s, i, n):
    s = _s(s, "string_copy")
    i, n = _i(i), _i(n)
    if i < 1:
        i = 1
    return s[i - 1:i - 1 + n] if n > 0 else ""


@builtin()
def string_char_at(sim, s, i):
    s = _s(s, "string_char_at")
    i = _i(i)
    return s[i - 1] if 1 <= i <= len(s) else ""


@builtin()
def string_byte_at(sim, s, i):
    c = string_char_at(sim, s, i)
    return ord(c) if c else -1


@builtin()
def string_pos(sim, sub, s):
    return _s(s, "string_pos", 2).find(_s(sub, "string_pos")) + 1


@builtin()
def string_last_pos(sim, sub, s):
    return _s(s, "string_last_pos", 2).rfind(_s(sub, "string_last_pos")) + 1


@builtin()
def string_replace(sim, s, a, b):
    return _s(s, "string_replace").replace(_s(a, "string_replace", 2), _s(b, "string_replace", 3), 1)


@builtin()
def string_replace_all(sim, s, a, b):
    a = _s(a, "string_replace_all", 2)
    if a == "":
        return _s(s, "string_replace_all")
    return _s(s, "string_replace_all").replace(a, _s(b, "string_replace_all", 3))


@builtin()
def string_delete(sim, s, i, n):
    s = _s(s, "string_delete")
    i, n = _i(i), _i(n)
    if i < 1 or n < 1:
        return s
    return s[:i - 1] + s[i - 1 + n:]


@builtin()
def string_insert(sim, sub, s, i):
    s = _s(s, "string_insert", 2)
    i = _i(i)
    i = 1 if i < 1 else len(s) + 1 if i > len(s) else i
    return s[:i - 1] + _s(sub, "string_insert") + s[i - 1:]


@builtin()
def string_upper(sim, s):
    return _s(s, "string_upper").upper()


@builtin()
def string_lower(sim, s):
    return _s(s, "string_lower").lower()


@builtin()
def string_digits(sim, s):
    return "".join(c for c in _s(s, "string_digits") if c.isdigit())


@builtin()
def string_letters(sim, s):
    return "".join(c for c in _s(s, "string_letters") if c.isalpha())


@builtin()
def string_lettersdigits(sim, s):
    return "".join(c for c in _s(s, "string_lettersdigits") if c.isalnum())


@builtin()
def string_count(sim, sub, s):
    sub = _s(sub, "string_count")
    return _s(s, "string_count", 2).count(sub) if sub else 0


@builtin()
def string_repeat(sim, s, n):
    return _s(s, "string_repeat") * __import__("builtins").max(0, _i(n))


@builtin()
def string_trim(sim, s, *chars):
    return _s(s, "string_trim").strip()


@builtin()
def string_hash_to_newline(sim, s):
    # GameMaker takes any value here (Chapter 3's party box passes the HP numbers straight in)
    if s.__class__ is not str and s.__class__ in (int, float, bool):
        s = gml_str(s)
    return _s(s, "string_hash_to_newline").replace("\\#", "\0").replace("#", "\n").replace("\0", "#")


@builtin()
def string_format(sim, v, tot, dec):
    v = _n(v)
    tot, dec = _i(tot), _i(dec)
    s = "%.*f" % (dec, v)
    return s.rjust(tot)


@builtin()
def chr(sim, n):
    return __import__("builtins").chr(_i(n))


@builtin()
def ord(sim, s):
    s = _s(s, "ord")
    return __import__("builtins").ord(s[0]) if s else 0


@builtin()
def real(sim, v):
    if v.__class__ is str:
        t = v.strip()
        try:
            if t.startswith("$"):
                return int(t[1:], 16)
            return float(t) if ("." in t or "e" in t.lower()) else int(t)
        except ValueError:
            try:
                return float(t)
            except ValueError:
                raise GMError('Unable to convert string "%s" to number' % v, "type")
    if v.__class__.__name__ == "GMHandle":
        # handle mode 2 plays a runtime where real() refuses handles
        if getattr(sim, "net_handles", 0) == 2:
            raise GMError("real(): unable to convert %r to a number" % (v,), "type")
        return v.index
    return _n(v)


@builtin()
def int64(sim, v):
    return int(real(sim, v))


@builtin("bool")
def _bool(sim, v):
    return ops.truth(v) if not (v.__class__ is str) else v != ""


@builtin()
def string_width_dummy(sim, *a):
    return 0


# ------------------------------------------------------------------ type checks
@builtin()
def is_string(sim, v):
    return v.__class__ is str


@builtin()
def is_real(sim, v):
    return is_num(v) and v.__class__.__name__ != "GMInt64"


@builtin()
def is_numeric(sim, v):
    return is_num(v)


@builtin("is_int32", "is_int64")
def is_int(sim, v):
    return v.__class__.__name__ == "GMInt64"


@builtin()
def is_bool(sim, v):
    return v.__class__ is bool


@builtin()
def is_array(sim, v):
    return v.__class__ is GMArray


@builtin()
def is_struct(sim, v):
    return v.__class__ is GMStruct


@builtin()
def is_undefined(sim, v):
    return v is None


@builtin()
def is_method(sim, v):
    return v.__class__ is GMMethod


@builtin()
def is_callable(sim, v):
    return v.__class__ in (GMMethod, GMFunc, BuiltinRef)


@builtin("is_ptr", "is_handle")
def is_ptr(sim, v):
    return False


@builtin()
def typeof_(sim, v):
    return typeof(v)


from .registry import DEFAULT_BUILTINS  # noqa: E402
DEFAULT_BUILTINS["typeof"] = (lambda sim, v: typeof(v), False)


# ------------------------------------------------------------------ arrays
def _arr(a, fn):
    if a.__class__ is not GMArray:
        raise GMError("%s(): argument 1 must be an array, got %s" % (fn, typeof(a) if a is not None else "undefined"), "type")
    return a


@builtin()
def array_create(sim, n, val=0):
    n = _i(n)
    if n < 0:
        raise GMError("array_create(): negative size", "builtin_args")
    share(val)
    return GMArray([val] * n)


@builtin("array_length", "array_length_1d")
def array_length(sim, a):
    return len(_arr(a, "array_length").data)


@builtin()
def array_push(sim, a, *vals):
    d = _arr(a, "array_push").data
    for v in vals:
        d.append(share(v))
    return 0


@builtin()
def array_pop(sim, a):
    d = _arr(a, "array_pop").data
    return d.pop() if d else None


@builtin()
def array_delete(sim, a, i, n):
    d = _arr(a, "array_delete").data
    i, n = _i(i), _i(n)
    if i < 0 or i > len(d):
        raise GMError("array_delete(): index %d out of range" % i, "array_oob")
    del d[i:i + n]
    return 0


@builtin()
def array_insert(sim, a, i, *vals):
    d = _arr(a, "array_insert").data
    i = _i(i)
    if i < 0 or i > len(d):
        raise GMError("array_insert(): index %d out of range" % i, "array_oob")
    d[i:i] = [share(v) for v in vals]
    return 0


@builtin()
def array_resize(sim, a, n):
    d = _arr(a, "array_resize").data
    n = _i(n)
    if n < len(d):
        del d[n:]
    else:
        d.extend([0] * (n - len(d)))
    return 0


@builtin()
def array_copy(sim, dst, di, src, si, n):
    d = _arr(dst, "array_copy").data
    s = _arr(src, "array_copy").data
    di, si, n = _i(di), _i(si), _i(n)
    if si < 0 or si + n > len(s) or di < 0:
        raise GMError("array_copy(): range out of bounds", "array_oob")
    chunk = [share(x) for x in s[si:si + n]]
    if di > len(d):
        d.extend([0] * (di - len(d)))
    d[di:di + n] = chunk
    return 0


@builtin()
def array_get(sim, a, i):
    d = _arr(a, "array_get").data
    i = _i(i)
    if 0 <= i < len(d):
        return d[i]
    raise GMError("array_get(): index %d out of range (length %d)" % (i, len(d)), "array_oob")


@builtin()
def array_set(sim, a, i, v):
    from .rt import array_set as aset
    aset(_arr(a, "array_set"), _i(i), share(v))
    return 0


@builtin()
def array_contains(sim, a, v, *rest):
    return any(ops.eq(x, v) for x in _arr(a, "array_contains").data)


@builtin("array_get_index")
def array_get_index(sim, a, v, *rest):
    for i, x in enumerate(_arr(a, "array_get_index").data):
        if ops.eq(x, v):
            return i
    return -1


@builtin()
def array_equals(sim, a, b):
    return to_py(_arr(a, "array_equals")) == to_py(_arr(b, "array_equals"))


@builtin()
def array_reverse(sim, a):
    return GMArray(list(reversed(_arr(a, "array_reverse").data)))


@builtin()
def array_shuffle(sim, a):
    d = _arr(a, "array_shuffle").data[:]
    sim.rng.shuffle(d)
    return GMArray(d)


@builtin(frame=True)
def array_sort(sim, f, a, order=True):
    import functools
    d = _arr(a, "array_sort").data
    if order.__class__ in (GMMethod, GMFunc):
        d.sort(key=functools.cmp_to_key(lambda x, y: int(_n(call_value(f, order, [x, y])))))
    else:
        d.sort(reverse=not ops.truth(order))
    return 0


@builtin(frame=True)
def array_foreach(sim, f, a, fn, start=0, n=None):
    d = _arr(a, "array_foreach").data
    for i, x in enumerate(d[:]):
        call_value(f, fn, [x, i])
    return 0


@builtin(frame=True)
def array_map(sim, f, a, fn, *r):
    d = _arr(a, "array_map").data
    return GMArray([share(call_value(f, fn, [x, i])) for i, x in enumerate(d[:])])


@builtin(frame=True)
def array_filter(sim, f, a, fn, *r):
    d = _arr(a, "array_filter").data
    return GMArray([x for i, x in enumerate(d[:]) if ops.truth(call_value(f, fn, [x, i]))])


@builtin(frame=True)
def array_reduce(sim, f, a, fn, init=None, *r):
    d = _arr(a, "array_reduce").data
    acc = init
    start = 0
    if init is None and d:
        acc, start = d[0], 1
    for i in range(start, len(d)):
        acc = call_value(f, fn, [acc, d[i], i])
    return acc


@builtin(frame=True)
def array_find_index(sim, f, a, fn, *r):
    for i, x in enumerate(_arr(a, "array_find_index").data[:]):
        if ops.truth(call_value(f, fn, [x, i])):
            return i
    return -1


@builtin(frame=True)
def array_any(sim, f, a, fn, *r):
    return any(ops.truth(call_value(f, fn, [x, i])) for i, x in enumerate(_arr(a, "array_any").data[:]))


@builtin(frame=True)
def array_all(sim, f, a, fn, *r):
    return all(ops.truth(call_value(f, fn, [x, i])) for i, x in enumerate(_arr(a, "array_all").data[:]))


# ------------------------------------------------------------------ structs / variables
def _skey(k, fn):
    return _s(k, fn, 2)


@builtin(frame=True)
def variable_struct_get(sim, f, s, k):
    return vars_of(f, s).get(_skey(k, "variable_struct_get"))


@builtin(frame=True)
def variable_struct_set(sim, f, s, k, v):
    vars_of(f, s)[_skey(k, "variable_struct_set")] = share(v)
    return 0


@builtin(frame=True)
def variable_struct_exists(sim, f, s, k):
    if s.__class__ is not GMStruct and s.__class__ is not GMInstance:
        return False
    return _skey(k, "variable_struct_exists") in s.vars


@builtin(frame=True)
def variable_struct_remove(sim, f, s, k):
    vars_of(f, s).pop(_skey(k, "variable_struct_remove"), None)
    return 0


@builtin("variable_struct_get_names", "struct_get_names", frame=True)
def variable_struct_get_names(sim, f, s):
    return GMArray(list(vars_of(f, s).keys()))


@builtin("variable_struct_names_count", frame=True)
def variable_struct_names_count(sim, f, s):
    return len(vars_of(f, s))


@builtin(frame=True)
def variable_instance_exists(sim, f, who, name):
    try:
        return _s(name, "variable_instance_exists", 2) in vars_of(f, who)
    except GMError as e:
        if e.kind == "no_instance":
            return False
        raise


@builtin(frame=True)
def variable_instance_get(sim, f, who, name):
    return vars_of(f, who).get(_s(name, "variable_instance_get", 2))


@builtin(frame=True)
def variable_instance_set(sim, f, who, name, v):
    # the GameMaker runtime takes a variable hash (a number) too: Chapter 3's own code passes a number (the Roaring's
    # scr_lerpvar(r_goal, ...)) and the runner goes on; here a number names a variable of its own
    if isinstance(name, (int, float)) and not isinstance(name, bool):
        name = "__hash_%d" % int(name)
    vars_of(f, who)[_s(name, "variable_instance_set", 2)] = share(v)
    return 0


@builtin(frame=True)
def variable_instance_get_names(sim, f, who):
    return GMArray(list(vars_of(f, who).keys()))


@builtin()
def variable_global_exists(sim, name):
    return _s(name, "variable_global_exists") in sim.globals


@builtin()
def variable_global_get(sim, name):
    return sim.globals.get(_s(name, "variable_global_get"))


@builtin()
def variable_global_set(sim, name, v):
    name = _s(name, "variable_global_set")
    if name in sim.scripts:
        from .rt import err_global_is_function
        raise err_global_is_function(name)
    sim.globals[name] = share(v)
    return 0


@builtin()
def instanceof(sim, s):
    if s.__class__ is GMStruct and s.ctor is not None:
        return s.ctor.name
    return "struct" if s.__class__ is GMStruct else None


@builtin(frame=True)
def is_instanceof(sim, f, s, ctor):
    if s.__class__ is not GMStruct:
        return False
    c = s.ctor
    target = ctor
    while c is not None:
        if c is target or (target.__class__ is GMMethod and target.func is c):
            return True
        c = sim.ctor_parent(c)
    return False


@builtin()
def method(sim, who, fn):
    if fn.__class__ is GMMethod:
        fn = fn.func
    if fn.__class__ is not GMFunc:
        raise GMError("method(): second argument must be a function", "type")
    if who.__class__ in (int, float):
        who = sim.lookup_instance(int(who)) if who >= 0 else None
    return GMMethod(fn, who)


@builtin()
def method_get_self(sim, m):
    s = m.self_obj if m.__class__ is GMMethod else None
    return s.id if s.__class__ is GMInstance else s


@builtin()
def method_get_index(sim, m):
    return m.func if m.__class__ is GMMethod else m


@builtin(frame=True)
def script_execute(sim, f, fn, *args):
    return call_value(f, fn, list(args))


@builtin(frame=True)
def script_execute_ext(sim, f, fn, arr=None, offset=0, num=None):
    items = list(arr.data) if arr is not None else []
    offset = _i(offset)
    items = items[offset:] if num is None else items[offset:offset + _i(num)]
    return call_value(f, fn, items)


@builtin(frame=True)
def script_exists(sim, f, fn):
    if fn.__class__ in (GMFunc, GMMethod):
        return True
    if fn.__class__ is str:
        return sim.get_callable(fn, f, quiet=True) is not None
    return False


@builtin(frame=True)
def asset_get_index(sim, f, name):
    name = _s(name, "asset_get_index")
    if name in sim.objects:
        return sim.objects[name].index
    if name in sim.rooms:
        return sim.rooms[name].index
    fn = sim.get_callable(name, f, quiet=True)
    if fn is not None:
        return fn
    if name in sim.assets:
        return sim.assets[name]
    return -1


@builtin("show_debug_message", "show_debug_message_ext")
def show_debug_message(sim, v, *a):
    msg = gml_str(v)
    sim.debug_messages.append(msg)
    return 0


@builtin()
def show_error(sim, msg, abort=True):
    if ops.truth(abort):
        raise GMError(gml_str(msg), "show_error")
    sim.debug_messages.append("ERROR: " + gml_str(msg))
    return 0


@builtin()
def assert_(sim, cond, msg=""):
    if not ops.truth(cond):
        raise GMError("assertion failed: %s" % gml_str(msg), "assert")
    return 0


@builtin()
def game_end(sim, *a):
    sim.game_ended = True
    return 0


@builtin()
def game_restart(sim, *a):
    sim.game_ended = False
    sim.restart_requested = True
    return 0


# ------------------------------------------------------------------ ds
def _new_ds(sim):
    i = sim.next_ds
    sim.next_ds += 1
    return i


@builtin()
def ds_list_create(sim):
    i = _new_ds(sim)
    sim.ds_lists[i] = []
    return i


@builtin()
def ds_list_destroy(sim, i):
    sim.ds_list(i)
    del sim.ds_lists[int(i)]
    return 0


@builtin()
def ds_list_add(sim, i, *vals):
    lst = sim.ds_list(i)
    for v in vals:
        lst.append(share(v))
    return 0


@builtin()
def ds_list_size(sim, i):
    return len(sim.ds_list(i))


@builtin()
def ds_list_find_value(sim, i, k):
    lst = sim.ds_list(i)
    k = _i(k)
    return lst[k] if 0 <= k < len(lst) else None


@builtin()
def ds_list_find_index(sim, i, v):
    for k, x in enumerate(sim.ds_list(i)):
        if ops.eq(x, v):
            return k
    return -1


@builtin()
def ds_list_delete(sim, i, k):
    lst = sim.ds_list(i)
    k = _i(k)
    if not 0 <= k < len(lst):
        raise GMError("ds_list_delete(): index %d out of range" % k, "ds_oob")
    del lst[k]
    return 0


@builtin()
def ds_list_insert(sim, i, k, v):
    sim.ds_list(i).insert(_i(k), share(v))
    return 0


@builtin("ds_list_set")
def ds_list_set(sim, i, k, v):
    """GameMaker pads a list set past its end with 0s (Chapter 5's obj_pink_battlemovement fills its empty list_burnt so)"""
    lst = sim.ds_list(i)
    k = _i(k)
    if k < 0:
        raise GMError("ds_list_set(): index %d out of range" % k, "ds_oob")
    while len(lst) <= k:
        lst.append(0)
    lst[k] = share(v)
    return 0


@builtin("ds_list_replace")
def ds_list_replace(sim, i, k, v):
    lst = sim.ds_list(i)
    k = _i(k)
    if not 0 <= k < len(lst):
        raise GMError("ds_list_replace(): index %d out of range" % k, "ds_oob")
    lst[k] = share(v)
    return 0


@builtin()
def ds_list_clear(sim, i):
    sim.ds_list(i).clear()
    return 0


@builtin()
def ds_list_shuffle(sim, i):
    sim.rng.shuffle(sim.ds_list(i))
    return 0


@builtin()
def ds_list_sort(sim, i, asc):
    sim.ds_list(i).sort(reverse=not ops.truth(asc))
    return 0


@builtin()
def ds_list_exists(sim, i):
    return i.__class__ in (int, float) and int(i) in sim.ds_lists


@builtin()
def ds_map_create(sim):
    i = _new_ds(sim)
    sim.ds_maps[i] = {}
    return i


@builtin()
def ds_map_destroy(sim, i):
    sim.ds_map(i)
    del sim.ds_maps[int(i)]
    return 0


@builtin()
def ds_map_add(sim, i, k, v):
    m = sim.ds_map(i)
    if k in m:
        return False
    m[k] = share(v)
    return True


@builtin("ds_map_set", "ds_map_replace")
def ds_map_set(sim, i, k, v):
    sim.ds_map(i)[k] = share(v)
    return 0


@builtin()
def ds_map_find_value(sim, i, k):
    return sim.ds_map(i).get(k)


@builtin()
def ds_map_exists(sim, i, k):
    return k in sim.ds_map(i)


@builtin()
def ds_map_delete(sim, i, k):
    sim.ds_map(i).pop(k, None)
    return 0


@builtin()
def ds_map_size(sim, i):
    return len(sim.ds_map(i))


@builtin()
def ds_map_clear(sim, i):
    sim.ds_map(i).clear()
    return 0


@builtin()
def ds_map_find_first(sim, i):
    m = sim.ds_map(i)
    return next(iter(m), None)


@builtin()
def ds_map_find_next(sim, i, k):
    ks = list(sim.ds_map(i))
    try:
        return ks[ks.index(k) + 1]
    except (ValueError, IndexError):
        return None


@builtin()
def ds_map_exists_(sim, i):
    return False


@builtin()
def ds_exists(sim, i, t):
    return int(i) in {1: sim.ds_maps, 2: sim.ds_lists, 3: sim.ds_grids}.get(int(t), {})


@builtin()
def ds_grid_create(sim, w, h):
    i = _new_ds(sim)
    w, h = _i(w), _i(h)
    sim.ds_grids[i] = {"w": w, "h": h, "d": [[0] * h for _ in range(w)]}
    return i


@builtin()
def ds_grid_destroy(sim, i):
    sim.ds_grid(i)
    del sim.ds_grids[int(i)]
    return 0


@builtin()
def ds_grid_width(sim, i):
    return sim.ds_grid(i)["w"]


@builtin()
def ds_grid_height(sim, i):
    return sim.ds_grid(i)["h"]


@builtin()
def ds_grid_set(sim, i, x, y, v):
    g = sim.ds_grid(i)
    x, y = _i(x), _i(y)
    if not (0 <= x < g["w"] and 0 <= y < g["h"]):
        raise GMError("ds_grid_set(): (%d,%d) out of range" % (x, y), "ds_oob")
    g["d"][x][y] = v
    return 0


@builtin()
def ds_grid_get(sim, i, x, y):
    g = sim.ds_grid(i)
    x, y = _i(x), _i(y)
    if not (0 <= x < g["w"] and 0 <= y < g["h"]):
        raise GMError("ds_grid_get(): (%d,%d) out of range" % (x, y), "ds_oob")
    return g["d"][x][y]


# ------------------------------------------------------------------ json
def _to_json_obj(v):
    t = v.__class__
    if t is GMArray:
        return [_to_json_obj(x) for x in v.data]
    if t is GMStruct:
        return {k: _to_json_obj(x) for k, x in v.vars.items()}
    if t is float and v == int(v):
        return int(v)
    return v


@builtin()
def json_stringify(sim, v, *a):
    import json
    return json.dumps(_to_json_obj(v), separators=(",", ":"))


@builtin()
def json_parse(sim, s):
    import json
    try:
        return from_py(json.loads(_s(s, "json_parse")))
    except ValueError as e:
        raise GMError("json_parse(): %s" % e, "json")


# ------------------------------------------------------------------ misc
@builtin()
def is_nan_(sim, v):
    return False


@builtin("array_concat_dummy")
def _unused(sim, *a):
    return 0


@builtin()
def environment_get_variable(sim, name):
    return ""


@builtin()
def os_get_language(sim):
    return "en"


@builtin()
def os_get_region(sim):
    return "US"


@builtin()
def os_is_network_connected(sim, *a):
    return False


@builtin()
def os_get_info(sim):
    return from_py({})


@builtin()
def os_get_config(sim):
    return ""
