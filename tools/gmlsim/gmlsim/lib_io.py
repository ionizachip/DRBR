"""INI / file / ossafe / date builtins, backed by the sandbox FS (real files)."""
import datetime

from .errors import GMError, SimCrash
from .registry import builtin, gvar, DEFAULT_BUILTINS
from .values import gml_str, typeof

INI_REAL_FMT = "%.6f"


def _str(v, fn, n=1):
    if v.__class__ is not str:
        raise GMError("%s(): argument %d must be a string, got %s" % (fn, n, typeof(v) if v is not None else "undefined"), "type")
    return v


def _ini(sim, fn):
    if sim.ini is None:
        raise GMError("%s(): no ini file is open (call ini_open first)" % fn, "ini")
    return sim.ini["data"]


def parse_ini(text):
    data = {}
    sec = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            sec = line[1:-1]
            data.setdefault(sec, {})
            continue
        if sec is None or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
            data[sec][k] = ("s", v[1:-1])
        else:
            data[sec][k] = ("r", v)
    return data


def serialize_ini(data):
    out = []
    for sec, kv in data.items():
        out.append("[%s]\n" % sec)
        for k, (kind, v) in kv.items():
            out.append('%s="%s"\n' % (k, v) if kind == "s" else "%s=%s\n" % (k, v))
        out.append("\n")
    return "".join(out)


@builtin()
def ini_open(sim, name):
    name = _str(name, "ini_open")
    data = {}
    if sim.fs.exists(name):
        data = parse_ini(sim.fs.read(name).decode("utf-8", errors="replace"))
    sim.ini = {"name": name, "data": data}
    return 0


@builtin()
def ini_close(sim):
    if sim.ini is None:
        raise GMError("ini_close(): no ini file is open", "ini")
    ini = sim.ini
    sim.ini = None
    text = serialize_ini(ini["data"])
    sim.fs.write(ini["name"], text)
    return text


@builtin()
def ini_write_string(sim, sec, key, val):
    d = _ini(sim, "ini_write_string")
    d.setdefault(_str(sec, "ini_write_string"), {})[_str(key, "ini_write_string", 2)] = ("s", gml_str(val))
    return 0


@builtin()
def ini_write_real(sim, sec, key, val):
    d = _ini(sim, "ini_write_real")
    from . import ops
    d.setdefault(_str(sec, "ini_write_real"), {})[_str(key, "ini_write_real", 2)] = ("r", INI_REAL_FMT % ops.num(val))
    return 0


def _read(sim, fn, sec, key):
    d = _ini(sim, fn)
    return d.get(_str(sec, fn), {}).get(_str(key, fn, 2))


@builtin()
def ini_read_string(sim, sec, key, default):
    e = _read(sim, "ini_read_string", sec, key)
    return e[1] if e is not None else default


@builtin()
def ini_read_real(sim, sec, key, default):
    e = _read(sim, "ini_read_real", sec, key)
    if e is None:
        return default
    try:
        t = e[1]
        return int(t) if t.lstrip("-").isdigit() else float(t)
    except ValueError:
        return default


@builtin()
def ini_key_exists(sim, sec, key):
    return _read(sim, "ini_key_exists", sec, key) is not None


@builtin()
def ini_section_exists(sim, sec):
    return _str(sec, "ini_section_exists") in _ini(sim, "ini_section_exists")


@builtin()
def ini_key_delete(sim, sec, key):
    _ini(sim, "ini_key_delete").get(_str(sec, "ini_key_delete"), {}).pop(_str(key, "ini_key_delete", 2), None)
    return 0


@builtin()
def ini_section_delete(sim, sec):
    _ini(sim, "ini_section_delete").pop(_str(sec, "ini_section_delete"), None)
    return 0


# ---------------------------------------------------------------- plain files
@builtin()
def file_exists(sim, name):
    return sim.fs.exists(_str(name, "file_exists"))


@builtin()
def file_delete(sim, name):
    return sim.fs.delete(_str(name, "file_delete"))


@builtin()
def file_copy(sim, a, b):
    sim.fs.copy(_str(a, "file_copy"), _str(b, "file_copy", 2))
    return 0


@builtin()
def file_rename(sim, a, b):
    try:
        sim.fs.rename(_str(a, "file_rename"), _str(b, "file_rename", 2))
        return True
    except OSError:
        return False


@builtin()
def directory_exists(sim, d):
    import os
    return os.path.isdir(sim.fs.path(_str(d, "directory_exists")))


@builtin()
def directory_create(sim, d):
    import os
    os.makedirs(sim.fs.path(_str(d, "directory_create")), exist_ok=True)
    return 0


def _h(sim, h, fn):
    if h.__class__ not in (int, float) or int(h) not in sim.fhandles:
        raise GMError("%s(): invalid file handle %r" % (fn, h), "file")
    return sim.fhandles[int(h)]


def _new_h(sim, rec):
    i = sim.next_fh
    sim.next_fh += 1
    sim.fhandles[i] = rec
    return i


@builtin()
def file_text_open_write(sim, name):
    _str(name, "file_text_open_write")
    return _new_h(sim, {"path": name, "mode": "w", "buf": []})


@builtin()
def file_text_open_append(sim, name):
    _str(name, "file_text_open_append")
    prev = sim.fs.read(name).decode("utf-8", errors="replace") if sim.fs.exists(name) else ""
    return _new_h(sim, {"path": name, "mode": "w", "buf": [prev]})


@builtin()
def file_text_open_read(sim, name):
    _str(name, "file_text_open_read")
    if not sim.fs.exists(name):
        return -1
    text = sim.fs.read(name).decode("utf-8", errors="replace")
    return _new_h(sim, {"path": name, "mode": "r", "text": text, "pos": 0})


@builtin()
def file_text_write_string(sim, h, s):
    _h(sim, h, "file_text_write_string")["buf"].append(_str(s, "file_text_write_string", 2))
    return 0


@builtin()
def file_text_write_real(sim, h, v):
    # GameMaker writes C's "%g" (6 significant digits) and a space: "8896 ", "180.993 ", "1.18131e+06 " - as in a real
    # Chapter 3 save (filech3_N), every number line
    rec = _h(sim, h, "file_text_write_real")
    if v.__class__ is bool:
        v = int(v)
    if v.__class__ not in (int, float) and not isinstance(v, int):
        raise GMError("file_text_write_real(): a number is needed, got %s" % (type(v).__name__,), "type")
    rec["buf"].append(("%g" % v) + " ")
    return 0


@builtin()
def file_text_writeln(sim, h):
    # (Windows: CR LF, as the real saves have)
    _h(sim, h, "file_text_writeln")["buf"].append("\r\n")
    return 0


@builtin()
def file_text_close(sim, h):
    rec = _h(sim, h, "file_text_close")
    del sim.fhandles[int(h)]
    if rec["mode"] == "w":
        sim.fs.write(rec["path"], "".join(rec["buf"]))
    return 0


@builtin()
def file_text_eof(sim, h):
    r = _h(sim, h, "file_text_eof")
    return r["pos"] >= len(r["text"])


@builtin()
def file_text_eoln(sim, h):
    r = _h(sim, h, "file_text_eoln")
    return r["pos"] >= len(r["text"]) or r["text"][r["pos"]] == "\n"


@builtin()
def file_text_read_string(sim, h):
    r = _h(sim, h, "file_text_read_string")
    t = r["text"]
    end = t.find("\n", r["pos"])
    end = len(t) if end < 0 else end
    s = t[r["pos"]:end].rstrip("\r")
    r["pos"] = end
    return s


@builtin()
def file_text_read_real(sim, h):
    r = _h(sim, h, "file_text_read_real")
    t = r["text"]
    p = r["pos"]
    while p < len(t) and t[p] in " \t\r\n":
        p += 1
    q = p
    while q < len(t) and t[q] not in " \t\r\n":
        q += 1
    r["pos"] = q
    try:
        v = float(t[p:q])
    except ValueError:
        raise GMError("file_text_read_real(): cannot parse %r as a number" % t[p:q], "file")
    return int(v) if v == int(v) else v


@builtin()
def file_text_readln(sim, h):
    r = _h(sim, h, "file_text_readln")
    t = r["text"]
    end = t.find("\n", r["pos"])
    r["pos"] = len(t) if end < 0 else end + 1
    return ""


# ---------------------------------------------------------------- ossafe thin wrappers
def _alias(new, old):
    DEFAULT_BUILTINS[new] = DEFAULT_BUILTINS[old]


for _n in ("ini_open", "ini_close", "file_exists", "file_delete", "file_text_open_read", "file_text_open_write",
           "file_text_close", "file_text_eof", "file_text_read_real", "file_text_read_string", "file_text_readln",
           "file_text_write_real", "file_text_write_string", "file_text_writeln"):
    _alias("ossafe_" + _n, _n)
_alias("ossafe_game_end", "game_end") if "game_end" in DEFAULT_BUILTINS else None


@builtin("ossafe_savedata_save", "ossafe_savedata_load")
def _ossafe_save(sim, *a):
    return 0


@builtin("ossafe_init")
def _ossafe_init(sim, *a):
    return 0


# ---------------------------------------------------------------- time / date
_EPOCH = datetime.datetime(1899, 12, 30)


def _now(sim):
    return sim.now_base + datetime.timedelta(seconds=sim.frame_no / sim.fps)


def _to_dt(v):
    return _EPOCH + datetime.timedelta(days=float(v))


def _from_dt(d):
    return (d - _EPOCH).total_seconds() / 86400.0


@builtin()
def get_timer(sim):
    sim.timer_extra += 1
    return int(sim.frame_no * 1000000 / sim.fps) + sim.timer_extra


@builtin("date_current_datetime")
def date_current_datetime(sim):
    return _from_dt(_now(sim))


@builtin()
def date_create_datetime(sim, y, mo, d, h=0, mi=0, s=0):
    return _from_dt(datetime.datetime(int(y), int(mo), int(d), int(h), int(mi), int(s)))


for _nm, _attr in (("year", "year"), ("month", "month"), ("day", "day"), ("hour", "hour"), ("minute", "minute"),
                   ("second", "second")):
    DEFAULT_BUILTINS["date_get_" + _nm] = ((lambda sim, v, _a=_attr: getattr(_to_dt(v), _a)), False)
    gvar("current_" + _nm, (lambda sim, _a=_attr: getattr(_now(sim), _a)))


@builtin()
def date_get_weekday(sim, v):
    return (_to_dt(v).weekday() + 1) % 7


@builtin()
def date_inc_day(sim, v, n):
    return _from_dt(_to_dt(v) + datetime.timedelta(days=int(n)))


@builtin()
def date_inc_hour(sim, v, n):
    return _from_dt(_to_dt(v) + datetime.timedelta(hours=int(n)))


@builtin()
def date_inc_minute(sim, v, n):
    return _from_dt(_to_dt(v) + datetime.timedelta(minutes=int(n)))


@builtin()
def date_inc_second(sim, v, n):
    return _from_dt(_to_dt(v) + datetime.timedelta(seconds=int(n)))


@builtin()
def date_compare_datetime(sim, a, b):
    return (a > b) - (a < b)


@builtin()
def date_datetime_string(sim, v):
    return _to_dt(v).strftime("%m/%d/%y %H:%M:%S")


@builtin()
def date_date_string(sim, v):
    return _to_dt(v).strftime("%m/%d/%y")


@builtin()
def date_time_string(sim, v):
    return _to_dt(v).strftime("%H:%M:%S")


@builtin()
def date_days_in_month(sim, v):
    import calendar
    d = _to_dt(v)
    return calendar.monthrange(d.year, d.month)[1]


@builtin()
def date_set_timezone(sim, tz):
    return 0
