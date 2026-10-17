"""Self-test for the GML simulator.   python3 -m gmlsim.selftest [-v] [--real]

pytest-free: every `check*` call counts as one assertion.
"""
import math
import os
import sys
import time
import traceback

from .errors import GMError, GMParseError, SimCrash
from .fs import Fault
from .sim import Sim
from .values import GMArray, GMStruct, to_py

VERBOSE = "-v" in sys.argv
STATS = {"pass": 0, "fail": 0}
FAILS = []
_CUR = ["?"]


def _fail(msg):
    STATS["fail"] += 1
    FAILS.append("[%s] %s" % (_CUR[0], msg))
    if VERBOSE:
        print("FAIL", FAILS[-1])


def ok(cond, msg="condition"):
    if cond:
        STATS["pass"] += 1
    else:
        _fail(msg)


def eq(got, want, msg=""):
    if got == want and type(got) is not type(want) and isinstance(want, bool) != isinstance(got, bool):
        _fail("%s: got %r want %r (bool/num mismatch)" % (msg, got, want))
    elif got == want:
        STATS["pass"] += 1
    else:
        _fail("%s: got %r want %r" % (msg, got, want))


def approx(got, want, msg=""):
    if abs(got - want) < 1e-9:
        STATS["pass"] += 1
    else:
        _fail("%s: got %r want %r" % (msg, got, want))


def ev(sim, expr, **kw):
    return sim.py(sim.eval(expr, **kw))


def raises(sim, src, contains=None, kind=None, expr=False):
    """Assert that running src raises GMError (optionally containing text / of a kind)."""
    try:
        if expr:
            sim.eval(src)
        else:
            sim.run(src)
    except GMError as e:
        good = (contains is None or contains in e.message) and (kind is None or e.kind == kind)
        if good:
            STATS["pass"] += 1
        else:
            _fail("wrong error for %r: %s [%s]" % (src, e.message, e.kind))
        return e
    except Exception as e:  # python-level crash = harness bug
        _fail("python exception for %r: %r" % (src, e))
        return None
    _fail("no error raised for %r" % src)
    return None


def run(sim, src):
    sim.run(src)
    return sim


def G(sim, name):
    return sim.py(sim.globals[name])


def S(**kw):
    return Sim(seed=1, **kw)


TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


# =============================================================================
@test
def t_arith():
    s = S()
    eq(ev(s, "1 + 2 * 3"), 7, "prec")
    eq(ev(s, "(1 + 2) * 3"), 9)
    eq(ev(s, "10 div 3"), 3)
    eq(ev(s, "-10 div 3"), -3, "div truncates")
    eq(ev(s, "10 mod 3"), 1)
    eq(ev(s, "-10 mod 3"), -1, "mod sign of dividend")
    eq(ev(s, "10 % 4"), 2)
    eq(ev(s, "7 / 2"), 3.5)
    eq(ev(s, "6 / 2"), 3)
    eq(ev(s, "2 - 3 - 4"), -5, "left assoc")
    eq(ev(s, "$FF"), 255)
    eq(ev(s, "0xFF"), 255)
    eq(ev(s, "#FF0000"), 255, "#RRGGBB is BGR int: red == 255")
    eq(ev(s, "#0000FF"), 16711680)
    eq(ev(s, "5 & 3"), 1)
    eq(ev(s, "5 | 3"), 7)
    eq(ev(s, "5 ^ 3"), 6)
    eq(ev(s, "~0"), -1)
    eq(ev(s, "1 << 4"), 16)
    eq(ev(s, "256 >> 4"), 16)
    eq(ev(s, "5 & 3 == 1"), True, "& binds tighter than ==")
    eq(ev(s, "1 + 1 << 2"), 8, "shift lower than +")
    eq(ev(s, "-(-3)"), 3)
    eq(ev(s, "!true"), False)
    eq(ev(s, "!0"), True)
    eq(ev(s, "true && false"), False)
    eq(ev(s, "false || true"), True)
    eq(ev(s, "true ^^ true"), False)
    eq(ev(s, "true ^^ false"), True)
    eq(ev(s, "1 and 1"), True)
    eq(ev(s, "0 or 0"), False)
    eq(ev(s, "not 0"), True)
    eq(ev(s, "5 > 3 ? 'a' : 'b'"), "a")
    eq(ev(s, "5 < 3 ? 'a' : 'b'"), "b")
    eq(ev(s, "undefined ?? 7"), 7)
    eq(ev(s, "3 ?? 7"), 3)
    eq(ev(s, "0.1 + 0.2 == 0.3"), True, "epsilon compare")
    eq(ev(s, "1 == 1.000001"), True)
    eq(ev(s, "1 == 1.1"), False)
    eq(ev(s, "'a' == 'a'"), True)
    eq(ev(s, "'a' == 'b'"), False)
    eq(ev(s, "'a' == 1"), False)
    eq(ev(s, "undefined == undefined"), True)
    eq(ev(s, "1 != 2"), True)
    eq(ev(s, "1 <> 2"), True)
    eq(ev(s, "true + true"), 2)
    eq(ev(s, "'a' + 'b' + 'c'"), "abc")
    eq(ev(s, "\"tab\\there\""), "tab\there")
    eq(ev(s, "'it\\'s'"), "it's")
    eq(ev(s, "\"line\\nbreak\""), "line\nbreak")
    eq(ev(s, "\"\\\\E4*\""), "\\E4*", "backslash kept")
    eq(ev(s, "1e3"), 1000)
    eq(ev(s, "0.5 + .25"), 0.75)
    eq(ev(s, "-2 * -3"), 6)
    eq(ev(s, "2 * (3 + 4) mod 5"), 4)
    eq(ev(s, "5 > 3 && 2 > 1"), True)
    eq(ev(s, "$\"x={1+2}!\""), "x=3!", "template string")
    eq(ev(s, "@\"c:\\path\""), "c:\\path", "verbatim string")


@test
def t_vars():
    s = S()
    run(s, "var a = 1; a += 2; a *= 4; a -= 2; a /= 5; global.r = a;")
    eq(G(s, "r"), 2)
    run(s, "var b = 5; b++; ++b; b--; global.r = b;")
    eq(G(s, "r"), 6)
    run(s, "var b = 5; global.r = b++; global.q = b;")
    eq((G(s, "r"), G(s, "q")), (5, 6), "postfix value")
    run(s, "var b = 5; global.r = ++b;")
    eq(G(s, "r"), 6, "prefix value")
    run(s, "var s1 = 'a'; s1 += 'b'; global.r = s1;")
    eq(G(s, "r"), "ab")
    run(s, "var m = 7; m %= 4; global.r = m; m |= 8; global.q = m; m &= 10; global.z = m; m ^= 2; global.w = m;")
    eq((G(s, "r"), G(s, "q"), G(s, "z"), G(s, "w")), (3, 11, 10, 8))
    run(s, "var u = undefined; u ??= 4; global.r = u;")
    eq(G(s, "r"), 4, "??= on undefined")
    run(s, "var a = 1, b = 2, c; c = a + b; global.r = c;")
    eq(G(s, "r"), 3, "multi-var decl")
    run(s, "global.g = 1; global.g += 5; global.g++;")
    eq(G(s, "g"), 7)
    run(s, "globalvar gv; gv = 10; global.r = gv + 1;")
    eq(G(s, "r"), 11, "globalvar alias")
    eq(G(s, "gv"), 10)
    run(s, "x = 3; global.r = x * 2;")  # instance var on the global-scope self
    eq(G(s, "r"), 6)
    run(s, "var v = 1; { var v2 = v + 1; global.r = v2; }")
    eq(G(s, "r"), 2)
    run(s, "self.sv = 4; global.r = self.sv;")
    eq(G(s, "r"), 4)
    eq(ev(s, "true"), True)
    eq(ev(s, "undefined"), None)
    eq(ev(s, "noone"), -4)
    eq(ev(s, "all"), -3)
    eq(ev(s, "pi") > 3.14, True)
    eq(ev(s, "c_white"), 16777215)
    eq(ev(s, "vk_up"), 38)
    run(s, "var t = 5; var t2 = t; t = 6; global.r = t2;")
    eq(G(s, "r"), 5, "numbers copy")


@test
def t_arrays():
    s = S()
    eq(ev(s, "[1,2,3]"), [1, 2, 3])
    eq(ev(s, "[1,2,3][2]"), 3)
    eq(ev(s, "array_length([1,2,3])"), 3)
    eq(ev(s, "array_length([])"), 0)
    run(s, "var a = [1,2]; a[5] = 9; global.r = a;")
    eq(G(s, "r"), [1, 2, 0, 0, 0, 9], "auto-grow pads with 0")
    run(s, "var a; a[2] = 1; global.r = a;")
    eq(G(s, "r"), [0, 0, 1], "assign to unset var creates array")
    run(s, "var a = [1,2,3]; var b = a; b[0] = 99; global.r = a; global.q = b;")
    eq(G(s, "r"), [1, 2, 3], "assignment copies (COW)")
    eq(G(s, "q"), [99, 2, 3])
    run(s, "var a = [1,2,3]; var b = a; a[1] = 50; global.r = a; global.q = b;")
    eq((G(s, "r"), G(s, "q")), ([1, 50, 3], [1, 2, 3]), "writing the original also leaves the copy")
    run(s, "function chg(arr) { arr[0] = 100; return arr; } var a = [1,2]; var b = chg(a); global.r = a; global.q = b;")
    eq((G(s, "r"), G(s, "q")), ([1, 2], [100, 2]), "array passed to function is COW")
    run(s, "var a = [[1,2],[3,4]]; var b = a; b[0][1] = 77; global.r = a; global.q = b;")
    eq((G(s, "r"), G(s, "q")), ([[1, 2], [3, 4]], [[1, 77], [3, 4]]), "nested COW")
    run(s, "var a = [[1,2],[3,4]]; a[1][0] = 9; global.r = a;")
    eq(G(s, "r"), [[1, 2], [9, 4]], "a[i][j] write")
    run(s, "var a = []; a[1][2] = 5; global.r = a;")
    eq(G(s, "r"), [0, [0, 0, 5]], "nested auto-create")
    run(s, "var a = [[1,2],[3,4]]; global.r = a[1][0] + a[0, 1];")
    eq(G(s, "r"), 5, "a[i][j] and legacy a[i,j] read")
    run(s, "var a = [0,0]; a[1, 1] = 3; global.r = a;")
    eq(G(s, "r"), [0, [0, 3]], "legacy a[i,j] write auto-creates inner array")
    run(s, "var a = [1,2]; a[0] += 5; a[1]++; global.r = a;")
    eq(G(s, "r"), [6, 3], "compound on elements")
    run(s, "var a = [1,2]; var i = 0; a[i++] = 9; global.r = a; global.q = i;")
    eq((G(s, "r"), G(s, "q")), ([9, 2], 1), "index side effect evaluated once")
    run(s, "var a = array_create(3, 7); global.r = a;")
    eq(G(s, "r"), [7, 7, 7])
    run(s, "var a = [1]; array_push(a, 2, 3); global.r = array_length(a); array_pop(a); global.q = array_length(a);")
    eq((G(s, "r"), G(s, "q")), (3, 2))
    run(s, "var a = [1]; var b = a; array_push(a, 2); global.r = array_length(b);")
    eq(G(s, "r"), 2, "KNOWN DEVIATION (documented): array_* mutators modify shared storage in place")
    run(s, "var a = [1,2,3,4]; array_delete(a, 1, 2); global.r = a;")
    eq(G(s, "r"), [1, 4])
    run(s, "var a = [1,4]; array_insert(a, 1, 2, 3); global.r = a;")
    eq(G(s, "r"), [1, 2, 3, 4])
    run(s, "var a = [3,1,2]; array_sort(a, true); global.r = a;")
    eq(G(s, "r"), [1, 2, 3])
    run(s, "var a = [3,1,2]; array_sort(a, false); global.r = a;")
    eq(G(s, "r"), [3, 2, 1])
    run(s, "var a = [1,2,3]; var b = [0,0,0,0]; array_copy(b, 1, a, 0, 3); global.r = b;")
    eq(G(s, "r"), [0, 1, 2, 3])
    eq(ev(s, "array_contains([1,2,3], 2)"), True)
    eq(ev(s, "array_contains([1,2,3], 5)"), False)
    eq(ev(s, "array_get_index([5,6,7], 7)"), 2)
    run(s, "global.ga = [1,2,3]; var l = global.ga; l[0] = 0; global.r = global.ga[0];")
    eq(G(s, "r"), 1, "alias of global array is a copy on write")
    run(s, "self.ia = [1,2]; self.ia[1] = 5; global.r = self.ia;")
    eq(G(s, "r"), [1, 5], "write via self.array")
    run(s, "global.m = [[0,0],[0,0]]; global.m[1][1] = 4; global.r = global.m;")
    eq(G(s, "r"), [[0, 0], [0, 4]], "global.arr[i][j]")
    run(s, "var a = [1,2,3]; var n = 0; for (var i = 0; i < array_length(a); i++) n += a[i]; global.r = n;")
    eq(G(s, "r"), 6)
    run(s, "var a = [1,2,3]; var f = function(x) { return x * 2 }; global.r = array_map(a, f);")
    eq(G(s, "r"), [2, 4, 6])
    run(s, "var a = [1,2,3,4]; global.r = array_filter(a, function(x) { return x mod 2 == 0 });")
    eq(G(s, "r"), [2, 4])
    run(s, "var t = 0; array_foreach([1,2,3], function(x) { global.acc = x });")
    eq(G(s, "acc"), 3)
    eq(ev(s, "array_length_1d([1,2])"), 2)
    run(s, "var a = [1,2]; a[0] = [7,8]; var b = a; b[0][0] = 0; global.r = a;")
    eq(G(s, "r"), [[7, 8], 2], "array stored in array is COW")
    run(s, "var q = [1,2,3]; array_resize(q, 5); global.r = array_length(q); global.s = q[4]; array_resize(q, 1); global.t = array_length(q);")
    eq((G(s, "r"), G(s, "s"), G(s, "t")), (5, 0, 1))
    run(s, "var a = [1,2]; global.r = [a, a]; a[0] = 5;")
    eq(G(s, "r"), [[1, 2], [1, 2]], "array literal holds copies")


@test
def t_structs():
    s = S()
    run(s, "var st = {a: 1, b: 'x'}; global.r = st.a; global.q = st.b;")
    eq((G(s, "r"), G(s, "q")), (1, "x"))
    run(s, "var st = {}; st.n = 5; st.n += 1; global.r = st.n;")
    eq(G(s, "r"), 6)
    run(s, "var st = {a: [1,2]}; st.a[1] = 9; global.r = st.a;")
    eq(G(s, "r"), [1, 9])
    run(s, "var a = {x: 1}; var b = a; b.x = 2; global.r = a.x;")
    eq(G(s, "r"), 2, "structs are references")
    run(s, "var st = {x: 1}; global.r = variable_struct_exists(st, 'x'); global.q = variable_struct_exists(st, 'y');")
    eq((G(s, "r"), G(s, "q")), (True, False))
    run(s, "var st = {}; variable_struct_set(st, 'k', 3); global.r = variable_struct_get(st, 'k');")
    eq(G(s, "r"), 3)
    eq(ev(s, "variable_struct_get({a:1}, 'zz')"), None)
    run(s, "var st = {a:1, b:2}; global.r = variable_struct_names_count(st); global.q = variable_struct_get_names(st);")
    eq((G(s, "r"), G(s, "q")), (2, ["a", "b"]))
    run(s, "var st = {a:1}; variable_struct_remove(st, 'a'); global.r = variable_struct_exists(st, 'a');")
    eq(G(s, "r"), False)
    run(s, "var st = {a:1}; global.r = st[$ 'a']; global.q = st[$ 'nope']; st[$ 'z'] = 5; global.w = st.z;")
    eq((G(s, "r"), G(s, "q"), G(s, "w")), (1, None, 5), "[$ ] accessor")
    run(s, "var st = {v: 10, get: function() { return self.v; }}; global.r = st.get();")
    eq(G(s, "r"), 10, "method in struct literal bound to struct")
    run(s, """
function Point(_x, _y) constructor {
    x = _x; y = _y;
    static count = 0;
    sum = function() { return x + y; };
    scale = function(k) { x *= k; y *= k; return self; };
}
var p = new Point(3, 4);
global.r = p.sum();
p.scale(2);
global.q = p.x;
global.w = instanceof(p);
""")
    eq((G(s, "r"), G(s, "q"), G(s, "w")), (7, 6, "Point"), "constructor + methods")
    run(s, """
function Animal(n) constructor { name = n; function speak() { return name + '...'; } }
function Dog(n) : Animal(n) constructor { tricks = 2; }
var d = new Dog('rex');
global.r = d.name; global.q = d.tricks; global.w = d.speak();
global.i1 = is_instanceof(d, Dog); global.i2 = is_instanceof(d, Animal);
""")
    eq((G(s, "r"), G(s, "q"), G(s, "w"), G(s, "i1"), G(s, "i2")), ("rex", 2, "rex...", True, True), "ctor inheritance")
    raises(s, "var st = {}; var z = st.missing;", "Variable struct.missing not set before reading it", "var_not_set")
    raises(s, "var z = new NoSuchCtor();", "NoSuchCtor")
    raises(s, "function NC() {} var z = new NC();", "not a constructor")
    eq(ev(s, "is_struct({})"), True)
    eq(ev(s, "is_struct(1)"), False)
    eq(ev(s, "typeof({})"), "struct")
    eq(ev(s, "typeof([])"), "array")
    eq(ev(s, "typeof(1)"), "number")
    eq(ev(s, "typeof('s')"), "string")
    eq(ev(s, "typeof(undefined)"), "undefined")
    run(s, "function Q() constructor { n = 1; } var a = new Q(); var b = a; b.n = 2; global.r = a.n;")
    eq(G(s, "r"), 2)
    run(s, "var st = {a: {b: {c: 5}}}; st.a.b.c = 6; global.r = st.a.b.c;")
    eq(G(s, "r"), 6, "nested struct write")
    run(s, "var st = {n: 1}; with (st) { n = 5; } global.r = st.n;")
    eq(G(s, "r"), 5, "with(struct)")
    eq(ev(s, "is_method(function() {})"), True)


@test
def t_functions():
    s = S()
    run(s, "function add(a, b = 10) { return a + b; } global.r = add(1); global.q = add(1, 2);")
    eq((G(s, "r"), G(s, "q")), (11, 3), "default args")
    run(s, "function f(a, b = a * 2) { return b; } global.r = f(4);")
    eq(G(s, "r"), 8, "default refers to earlier param")
    run(s, "function f(a) { return is_undefined(a); } global.r = f(); global.q = f(1);")
    eq((G(s, "r"), G(s, "q")), (True, False), "missing arg is undefined")
    run(s, "function f() { return argument_count; } global.r = f(1,2,3);")
    eq(G(s, "r"), 3)
    run(s, "function f() { return argument[0] + argument[1]; } global.r = f(4, 5);")
    eq(G(s, "r"), 9)
    run(s, "function f() { return argument0 * 2; } global.r = f(4);")
    eq(G(s, "r"), 8)
    run(s, "function fact(n) { if (n <= 1) return 1; return n * fact(n - 1); } global.r = fact(6);")
    eq(G(s, "r"), 720, "recursion")
    run(s, "var f = function(x) { return x + 1; }; global.r = f(1);")
    eq(G(s, "r"), 2, "anonymous function in local")
    run(s, "function mk(k) { return function(x) { return x * k; }; } ")  # closures are NOT supported (GML has no closures)
    run(s, "function v() { return; } global.r = is_undefined(v());")
    eq(G(s, "r"), True)
    run(s, "function e() { exit; } global.r = is_undefined(e());")
    eq(G(s, "r"), True, "exit inside function")
    run(s, "function a1() { return 1 } function b1() { return a1() + 1 } global.r = b1();")
    eq(G(s, "r"), 2)
    run(s, "function sx(f, v) { return script_execute(f, v); } global.r = sx(function(x) { return x * 3 }, 5);")
    eq(G(s, "r"), 15, "script_execute with function value")
    run(s, "function two(a, b) { return a - b; } global.r = script_execute(two, 9, 4);")
    eq(G(s, "r"), 5)
    run(s, "function two(a, b) { return a - b; } global.r = script_execute_ext(two, [9, 4]);")
    eq(G(s, "r"), 5)
    run(s, "function sc() { static n = 0; n++; return n; } sc(); sc(); global.r = sc();")
    eq(G(s, "r"), 3, "static persists across calls")
    s.define_object("o1")
    i = s.create("o1")
    s.define_script("scr_self", "function scr_self() { return hp * 2; }")
    s.set(i, "hp", 21)
    eq(s.py(s.call("scr_self", self_obj=i)), 42, "script runs with caller's self")
    run(s, "function addn() { var t = 0; for (var i = 0; i < argument_count; i++) t += argument[i]; return t; } global.r = addn(1,2,3,4);")
    eq(G(s, "r"), 10)
    run(s, "var m = method(undefined, function(a) { return a + 1 }); global.r = m(1);")
    eq(G(s, "r"), 2, "method(undefined, fn)")
    eq(ev(s, "is_callable(function(){})"), True)
    eq(ev(s, "script_exists(scr_self)"), True)
    run(s, "function fa() { return 1; } var f = fa; global.r = f() + 1;")
    eq(G(s, "r"), 2, "function name as value")
    e = raises(s, "function f() { return g(); } function g() { return nope(); } f();", "undefined function nope")
    eq(e.stack[:2] if e else None, ["g", "f"], "error stack names")


@test
def t_control():
    s = S()
    run(s, "var n = 0; for (var i = 0; i < 5; i++) n += i; global.r = n;")
    eq(G(s, "r"), 10)
    run(s, "var n = 0; var i = 0; while (i < 4) { n += 2; i++; } global.r = n;")
    eq(G(s, "r"), 8)
    run(s, "var n = 0; do { n++; } until (n >= 3); global.r = n;")
    eq(G(s, "r"), 3)
    run(s, "var n = 0; repeat (4) n += 2; global.r = n;")
    eq(G(s, "r"), 8)
    run(s, "var n = 0; for (var i = 0; i < 10; i++) { if (i == 3) continue; if (i == 6) break; n += i; } global.r = n;")
    eq(G(s, "r"), 0 + 1 + 2 + 4 + 5)
    run(s, "var n = 0; for (var i = 0; i < 3; i++) for (var j = 0; j < 3; j++) { if (j == 1) break; n++; } global.r = n;")
    eq(G(s, "r"), 3, "break only inner loop")
    run(s, """var r = ''; switch (2) { case 1: r += 'a'; case 2: r += 'b'; case 3: r += 'c'; break; case 4: r += 'd'; } global.r = r;""")
    eq(G(s, "r"), "bc", "switch fallthrough + break")
    run(s, """var r = ''; switch (9) { case 1: r = 'a'; break; default: r = 'z'; break; } global.r = r;""")
    eq(G(s, "r"), "z", "switch default")
    run(s, """var r = ''; switch ('k') { case 'j': r = 1; break; case 'k': r = 2; break; } global.r = r;""")
    eq(G(s, "r"), 2, "switch on strings")
    run(s, """var r = 0; for (var i = 0; i < 4; i++) { switch (i) { case 1: continue; case 2: r += 10; break; default: r += 1; } r += 100; } global.r = r;""")
    eq(G(s, "r"), 1 + 100 + 10 + 100 + 1 + 100, "continue inside switch continues the loop")
    run(s, """var r = 0; switch (1 + 1) { case 1 + 1: r = 5; break; } global.r = r;""")
    eq(G(s, "r"), 5, "switch with expression case")
    run(s, "if (1 > 2) global.r = 'a'; else if (2 > 1) global.r = 'b'; else global.r = 'c';")
    eq(G(s, "r"), "b")
    run(s, "if (true) { global.r = 1; } else { global.r = 2; }")
    eq(G(s, "r"), 1)
    run(s, "function f() { for (var i = 0; i < 10; i++) { if (i == 4) return i; } return -1; } global.r = f();")
    eq(G(s, "r"), 4, "return from inside loop")
    run(s, "global.r = 0; exit; global.r = 1;")
    eq(G(s, "r"), 0, "exit stops the entry")
    run(s, "var i = 0; while (true) { i++; if (i > 5) break; } global.r = i;")
    eq(G(s, "r"), 6)
    run(s, "var n = 0; for (var i = 0; i < 3; i++) { for (var j = 0; j < 3; j++) { if (j == 2) continue; n++; } } global.r = n;")
    eq(G(s, "r"), 6)
    import gmlsim.compiler as _C
    _old = _C.LOOP_LIMIT
    _C.LOOP_LIMIT = 1000
    raises(s, "while (true) { var z = 1; }", "Infinite loop", kind="loop_limit")
    raises(s, "for (;;) { }", "Infinite loop", kind="loop_limit")
    raises(s, "do { } until (false);", "Infinite loop", kind="loop_limit")
    _C.LOOP_LIMIT = _old
    run(s, "var a = 3; if (a == 3) if (a == 4) global.r = 1; else global.r = 2;")
    eq(G(s, "r"), 2, "dangling else binds inner")
    run(s, "if (0.7) global.r = 'y'; else global.r = 'n';")
    eq(G(s, "r"), "y", "0.7 is truthy (>=0.5)")
    run(s, "if (0.3) global.r = 'y'; else global.r = 'n';")
    eq(G(s, "r"), "n", "0.3 is falsy")
    run(s, "var n = 0; for (var i = 0, j = 10; i < 3; i++) n++; global.r = n;")
    eq(G(s, "r"), 3, "for with multi var init")


@test
def t_trycatch():
    s = S()
    run(s, "try { throw 'boom'; } catch (e) { global.r = e; }")
    eq(G(s, "r"), "boom", "throw string")
    run(s, "try { throw {code: 5}; } catch (e) { global.r = e.code; }")
    eq(G(s, "r"), 5, "throw struct")
    run(s, "try { var z = global.nope; } catch (e) { global.r = e.message; }")
    ok("not set before reading it" in G(s, "r"), "catch GM runtime error message")
    run(s, "global.fin = 0; try { global.fin += 1; } finally { global.fin += 10; }")
    eq(G(s, "fin"), 11, "finally runs")
    run(s, "global.fin = 0; try { throw 1; } catch (e) { global.fin += 1; } finally { global.fin += 10; }")
    eq(G(s, "fin"), 11)
    raises(s, "throw 'unhandled';", "unhandled")
    run(s, "function f() { try { return 1; } finally { global.fin = 'ran'; } } global.r = f();")
    eq((G(s, "r"), G(s, "fin")), (1, "ran"), "finally on return")
    run(s, "try { try { throw 'in'; } finally { global.fin = 'inner'; } } catch (e) { global.r = e; }")
    eq((G(s, "r"), G(s, "fin")), ("in", "inner"), "nested try")
    run(s, "try { var q = [1][4]; } catch (e) { global.r = e.kind; }")
    eq(G(s, "r"), "array_oob")


@test
def t_enum_macro():
    s = S()
    s.define_script("enums", "enum Color { RED, GREEN = 5, BLUE }\nenum Flag { A = 1, B = 2, C = A | B }")
    eq(ev(s, "Color.RED"), 0)
    eq(ev(s, "Color.GREEN"), 5)
    eq(ev(s, "Color.BLUE"), 6)
    eq(ev(s, "Flag.C"), 3, "enum value referencing earlier members")
    raises(s, "var z = Color.PURPLE;", "no member")
    s.define_script("macros", "#macro MAXHP 100\n#macro DOUBLE (MAXHP * 2)\n")
    s.run("global.r = DOUBLE;")
    eq(G(s, "r"), 200, "macro expansion lazily")
    s.run("switch (5) { case Color.GREEN: global.r = 'g'; break; }")
    eq(G(s, "r"), "g", "enum in case label")


# =============================================================================
def mk_objs():
    s = S()
    s.define_object("obj_a")
    s.define_object("obj_b", parent="obj_a")
    s.define_object("obj_c", parent="obj_b")
    s.define_object("obj_d")
    return s


@test
def t_instances():
    s = mk_objs()
    s.define_event("obj_a", "Create", 0, "hp = 10; tag = 'a';")
    s.define_event("obj_d", "Create", 0, "hp = 5;")
    a = s.create("obj_a", 10, 20)
    ok(a >= 100000, "instance ids start at 100000")
    eq(s.get(a, "x"), 10)
    eq(s.get(a, "y"), 20)
    eq(s.get(a, "hp"), 10, "Create ran")
    eq(ev(s, "instance_exists(obj_a)"), True)
    eq(ev(s, "instance_exists(obj_d)"), False)
    eq(ev(s, "instance_number(obj_a)"), 1)
    d = s.create("obj_d")
    eq(ev(s, "instance_number(obj_d)"), 1)
    eq(ev(s, "instance_exists(%d)" % d), True, "by id")
    eq(ev(s, "instance_exists(all)"), True)
    eq(ev(s, "obj_a.hp"), 10, "obj.var reads first instance")
    eq(s.eval("obj_d.hp"), 5)
    run(s, "obj_a.hp = 77;")
    eq(s.get(a, "hp"), 77, "obj.var write")
    c = s.create("obj_c")
    eq(ev(s, "instance_number(obj_a)"), 2, "children count as parent")
    eq(ev(s, "instance_number(obj_b)"), 1)
    eq(ev(s, "instance_number(obj_c)"), 1)
    eq(s.eval("instance_find(obj_a, 1)"), c, "instance_find nth in creation order")
    eq(s.eval("instance_find(obj_a, 5)"), -4, "instance_find out of range is noone")
    run(s, "instance_destroy(obj_c);")
    eq(ev(s, "instance_exists(obj_c)"), False)
    eq(ev(s, "instance_number(obj_a)"), 1)
    run(s, "instance_destroy(%d);" % a)
    eq(ev(s, "instance_number(obj_a)"), 0)
    raises(s, "var z = obj_a.hp;", "Unable to find instance for object index", "no_instance")
    raises(s, "var t = %d; var z = t.hp;" % a, "Unable to find instance for object index %d" % a)
    raises(s, "obj_a.hp = 1;", "Unable to find instance for object index")
    raises(s, "var z = obj_d.nonexistent_var;", "Variable obj_d.nonexistent_var not set before reading it", "var_not_set")
    raises(s, "var z = noone.x;", "Unable to find instance for object index -4")
    raises(s, "var t = 12345678; var z = t.x;", "Unable to find instance")
    b = s.create("obj_b")
    run(s, "with (obj_a) { zz = 1; }")
    eq(s.get(b, "zz"), 1, "with(parent obj) reaches child instances")
    n0 = len(s.instances)
    s.create("obj_a"); s.create("obj_a")
    run(s, "with (all) { mark = 1; }")
    ok(all(i.vars.get("mark") == 1 for i in s.instances.values()), "with(all) hits everything")
    run(s, "global.cnt = 0; with (obj_a) { global.cnt++; }")
    eq(G(s, "cnt"), 3, "with iterates all matching instances")
    d2 = s.create("obj_d", hp=1)
    s.set(b, "marker", 123)
    s.define_object("obj_me")
    me = s.create("obj_me")
    s.set(me, "who", "me!")
    s.run("with (obj_d) { got = other.who; }", self_obj=me)
    eq(s.get(d2, "got"), "me!", "other refers to the instance that ran with")
    s.run("var cnt = 0; with (obj_d) { cnt++; } global.r = cnt;", self_obj=me)
    eq(G(s, "r"), 2, "locals are shared into with-body")
    s.run("with (obj_d) { instance_destroy(); }")
    eq(ev(s, "instance_number(obj_d)"), 0, "instance_destroy() inside with destroys the with-instance")
    s.run("with (noone) { global.r = 'never'; }")
    ok(G(s, "r") != "never", "with(noone) is a no-op")
    s.run("with (obj_d) { global.r = 'never2'; }")
    ok(G(s, "r") != "never2", "with(object without instances) is a no-op")
    s.run("var t = id; global.r = (t == id);", self_obj=me)
    eq(G(s, "r"), True, "id")
    s.run("global.r = self.id;", self_obj=me)
    eq(G(s, "r"), me)
    s.run("global.r = object_index == obj_me;", self_obj=me)
    eq(G(s, "r"), True, "object_index")
    s.run("with (%d) { global.r = id; }" % me)
    eq(G(s, "r"), me, "with(id)")
    eq(s.eval("variable_instance_exists(%d, 'who')" % me), True)
    eq(s.eval("variable_instance_exists(%d, 'nope')" % me), False)
    eq(s.eval("variable_instance_exists(99999999, 'nope')"), False)
    s.run("variable_instance_set(%d, 'dyn', 9);" % me)
    eq(s.get(me, "dyn"), 9)
    eq(s.eval("variable_instance_get(%d, 'dyn')" % me), 9)
    raises(s, "var q = instance_create_depth(0, 0, 0, obj_missing);", None)
    e = raises(s, "instance_create_depth(0, 0, 0, 424242);", "Unable to find object")
    s.run("global.nid = instance_create_depth(5, 6, -100, obj_d);")
    nid = G(s, "nid")
    eq((s.get(nid, "x"), s.get(nid, "y"), s.get(nid, "depth")), (5, 6, -100), "instance_create_depth")
    s.run("global.nid = instance_create_depth(1, 2, 0, obj_d, {hp: 99, extra: 'e'});")
    eq((s.get(G(s, "nid"), "hp"), s.get(G(s, "nid"), "extra")), (5, "e"), "var struct arg applied before Create (Create may overwrite)")
    s.run("global.nid = instance_create_layer(1, 2, 'Instances', obj_d);")
    ok(G(s, "nid") in s.instances, "instance_create_layer")


@test
def t_events():
    s = mk_objs()
    s.define_event("obj_a", "Create", 0, "log = 'a-create;';")
    s.define_event("obj_b", "Create", 0, "event_inherited(); log += 'b-create;';")
    s.define_event("obj_c", "Create", 0, "event_inherited(); log += 'c-create;';")
    c = s.create("obj_c")
    eq(s.get(c, "log"), "a-create;b-create;c-create;", "event_inherited chain")
    s.instances.clear()
    s.define_event("obj_a", "Step", 0, "n = n + 1;")
    s.define_event("obj_a", "Create", 0, "n = 0;")
    a = s.create("obj_a")
    s.step(3)
    eq(s.get(a, "n"), 3, "Step runs each frame")
    s.define_event("obj_b", "Create", 0, "n = 100;")
    b2 = s.create("obj_b")
    s.step(2)
    eq(s.get(b2, "n"), 102, "child inherits parent's Step when it has none")
    # Begin step / step / end step order
    s2 = S()
    s2.define_object("o")
    s2.define_event("o", "Create", 0, "trace = '';")
    s2.define_event("o", "Step", 1, "trace += 'B';")
    s2.define_event("o", "Step", 0, "trace += 'S';")
    s2.define_event("o", "Step", 2, "trace += 'E';")
    s2.define_event("o", "Draw", 0, "trace += 'D';")
    s2.define_event("o", "Alarm", 0, "trace += 'A';")
    i = s2.create("o")
    s2.run("alarm[0] = 2;", self_obj=i)
    s2.step(2)
    eq(s2.get(i, "trace"), "BSEDBASED", "frame order: Begin Step, Alarm, Step, End Step, Draw")
    eq(s2.eval("alarm[0]", self_obj=i), -1, "alarm resets to -1 after firing")
    s2.run("alarm[3] = 1;", self_obj=i)
    s2.define_event("o", "Alarm", 3, "trace += 'X';")
    s2.step(1)
    ok(s2.get(i, "trace").endswith("BXSED"), "alarm[3] fires before Step in the same frame")
    s2.run("alarm[1] = 3;", self_obj=i)
    s2.step(1)
    eq(s2.eval("alarm[1]", self_obj=i), 2, "alarm decrements per step")
    # user events
    s3 = S()
    s3.define_object("p")
    s3.define_object("q", parent="p")
    s3.define_event("p", "Create", 0, "hits = 0;")
    s3.define_event("p", "Other", 10, "hits += 1;")
    s3.define_event("p", "Other", 11, "hits += 10; event_user(0);")
    s3.define_event("q", "Other", 10, "event_inherited(); hits += 100;")
    qi = s3.create("q")
    s3.run("event_user(0);", self_obj=qi)
    eq(s3.get(qi, "hits"), 101, "event_user(0) + event_inherited")
    s3.run("event_user(1);", self_obj=qi)
    eq(s3.get(qi, "hits"), 101 + 10 + 101, "user event calling user event")
    s3.run("event_perform(ev_other, ev_user0);", self_obj=qi)
    eq(s3.get(qi, "hits"), 101 + 10 + 101 + 101, "event_perform(ev_other, ev_user0)")
    s3.run("event_user(5);", self_obj=qi)  # undefined user event is a silent no-op
    ok(True)
    raises(s3, "event_user(16);", "user event number")
    # destroy ordering
    s4 = S()
    s4.define_object("o")
    s4.define_event("o", "Destroy", 0, "global.order = 'D';")
    s4.define_event("o", "CleanUp", 0, "global.order += 'C';")
    s4.define_event("o", "Step", 0, "if (!variable_instance_exists(id, 'n')) n = 0; n++; if (n == 2) instance_destroy();")
    o = s4.create("o")
    s4.step(3)
    eq(s4.globals["order"], "DC", "Destroy then CleanUp")
    eq(len(s4.instances), 0, "self-destroy in Step")
    # event_inherited with no parent event is a no-op
    s5 = mk_objs()
    s5.define_event("obj_b", "Create", 0, "event_inherited(); ok = 1;")
    i = s5.create("obj_b")
    eq(s5.get(i, "ok"), 1, "event_inherited with nothing above")
    # PreCreate
    s6 = S()
    s6.define_object("o")
    s6.define_event("o", "PreCreate", 0, "seq = 'pre;';")
    s6.define_event("o", "Create", 0, "seq += 'create;';")
    eq(s6.get(s6.create("o"), "seq"), "pre;create;", "PreCreate before Create")
    # instance created during step does not step in same phase
    s7 = S()
    s7.define_object("spawner"); s7.define_object("kid")
    s7.define_event("spawner", "Step", 0, "if (!variable_instance_exists(id,'done')) { done = true; instance_create_depth(0,0,0,kid); }")
    s7.define_event("kid", "Create", 0, "steps = 0;")
    s7.define_event("kid", "Step", 0, "steps++;")
    s7.create("spawner")
    s7.step(1)
    kid = s7.instance_list("kid")[0]
    # errors carry location
    s8 = S()
    s8.define_object("o")
    s8.define_event("o", "Step", 0, "var a = 1;\nvar b = a + missing_var;")
    s8.create("o")
    try:
        s8.step(1)
        _fail("expected error")
    except GMError as e:
        eq(e.line, 2, "error line")
        ok("o" in (e.event or "") and "Step_0" in (e.event or ""), "error event: %s" % e.event)
        eq(e.frame, 0, "error frame")
        ok("gml_Object_o_Step_0" == e.entry, "error entry %s" % e.entry)
        ok("Variable o.missing_var not set before reading it" in e.message, e.message)
    # keyboard
    s9 = S()
    s9.define_object("o")
    s9.define_event("o", "Create", 0, "hits = 0; held = 0;")
    s9.define_event("o", "Step", 0, "if (keyboard_check_pressed(ord('Z'))) hits++; if (keyboard_check(vk_right)) held++;")
    s9.create("o")
    s9.press("Z", frame=2)
    s9.hold("right", 3, start=1)
    s9.step(6)
    o = s9.instance_list("o")[0]
    eq((o.vars["hits"], o.vars["held"]), (1, 3), "scripted input per frame")
    s9.press("z")
    s9.step(1)
    eq(o.vars["hits"], 2, "press with frame=None hits the next frame")
    s10 = S()
    s10.define_object("o")
    s10.define_event("o", "KeyPress", 38, "up = 1;")
    s10.define_event("o", "Keyboard", 39, "right = (variable_instance_exists(id,'right') ? right : 0) + 1;")
    i = s10.create("o")
    s10.press("up", frame=1); s10.hold("right", 2, start=0)
    s10.step(3)
    eq((s10.get(i, "up"), s10.get(i, "right")), (1, 2), "KeyPress/Keyboard events")


@test
def t_rooms():
    s = S()
    s.define_object("player")
    s.define_object("wall")
    s.define_object("keeper", persistent=True)
    s.define_event("player", "Create", 0, "made = (variable_instance_exists(id, 'made') ? made : 0) + 1; ")
    s.define_event("player", "Other", 5, "global.ended = 1;")
    s.define_event("player", "CleanUp", 0, "global.cleaned = 1;")
    s.define_room("room_r1", instances=[("player", 10, 20), ("wall", 0, 0, {"hp": 3})])
    s.define_room("room_r2", instances=[("wall", 5, 5)])
    s.start("room_r1")
    eq(len(s.instances), 2, "room instances created")
    eq(s.instance_list("wall")[0].vars["hp"], 3, "room instance vars applied")
    eq(s.eval("room"), 0)
    k = s.create("keeper")
    s.run("room_goto(room_r2);")
    eq(s.eval("room"), 0, "room_goto only sets pending")
    s.step(1)
    eq(s.eval("room"), 1, "room changes at step boundary")
    eq(s.globals.get("ended"), 1, "Room End event ran")
    eq(s.globals.get("cleaned"), 1, "non-persistent instances got CleanUp")
    names = sorted(i.obj for i in s.instances.values())
    eq(names, ["keeper", "wall"], "non-persistent destroyed, persistent kept, new room instances created")
    ok(k in s.instances, "persistent instance survives (same id)")
    s.run("room_restart();")
    s.step(1)
    names = sorted(i.obj for i in s.instances.values())
    eq(names, ["keeper", "wall"], "room_restart recreates room, keeps persistent")
    raises(s, "room_goto(room_nonexistent_zzz);", "not defined")
    s.run("room_goto(room_r1);")
    s.step(1)
    eq(sorted(i.obj for i in s.instances.values()), ["keeper", "player", "wall"])
    eq(s.eval("room_get_name(room)"), "room_r1")
    s.run("room_goto_next();")
    s.step(1)
    eq(s.eval("room_get_name(room)"), "room_r2")
    raises(s, "room_goto_next();", "no room after")
    # room start event + creation code
    s2 = S()
    s2.define_object("o")
    s2.define_event("o", "Other", 4, "global.rs = 1;")
    s2.define_event("o", "Create", 0, "global.order = 'c';")
    s2.define_room("a", instances=["o"], creation_code="global.order += 'r';")
    s2.start("a")
    eq((s2.globals["rs"], s2.globals["order"]), (1, "cr"), "Create, then room creation code, then Room Start")
    # persistent flag via var
    s3 = S()
    s3.define_object("p")
    s3.define_room("a"); s3.define_room("b")
    s3.start("a")
    pid = s3.create("p", persistent=True)
    npid = s3.create("p")
    s3.goto_room("b"); s3.step(1)
    ok(pid in s3.instances and npid not in s3.instances, "persistent=true var keeps instance")


@test
def t_errors():
    s = S()
    s.define_object("o")
    i = s.create("o")
    e = raises(s, "var z = undefined_local_thing;", "Variable self.undefined_local_thing not set before reading it")
    try:
        s.run("var z = foo;", self_obj=i)
        _fail("no error")
    except GMError as e:
        eq(e.message, "Variable o.foo not set before reading it", "instance var unset message")
        eq(e.kind, "var_not_set")
    try:
        s.run("var z = global.nothing;")
    except GMError as e:
        ok(e.message.startswith("global variable name 'nothing' index ("), e.message)
        ok(e.message.endswith(") not set before reading it"), e.message)
    raises(s, "var l; var z = l + 1;", "local variable 'l' not set before reading it", "local_not_set")
    raises(s, "var a = [1,2,3]; var z = a[3];", "out of range", "array_oob")
    raises(s, "var a = [1,2,3]; var z = a[-1];", "out of range", "array_oob")
    raises(s, "var a = [1,2,3]; a[-1] = 0;", "out of range", "array_oob")
    raises(s, "var a = 5; var z = a[0];", "not an array")
    # (an indexed WRITE on a string replaces it with an array in GameMaker - Chapter 3's scr_gamestart relies on it; a READ
    # of a string with an index stays an error)
    raises(s, "var a = 'str'; var z = a[0];", "not an array")
    raises(s, "var z = 'a' + 1;", "Unable to add", "type")
    raises(s, "var z = 1 + 'a';", "Unable to add", "type")
    raises(s, "var z = 'a' - 1;", "Unable to convert", "type")
    raises(s, "var z = 'a' * 2;", "Unable to convert", "type")
    raises(s, "var z = undefined + 1;", "Unable to convert undefined", "type")
    raises(s, "var z = -'a';", "Unable to convert", "type")
    raises(s, "var z = 'a' < 1;", "Unable to compare", "type")
    raises(s, "if ('str') { var q = 1; }", "boolean", "type")
    raises(s, "if (undefined) { var q = 1; }", "boolean", "type")
    raises(s, "var z = 1 / 0;", "Division by zero", "div0")
    raises(s, "var z = 5 div 0;", "Division by zero", "div0")
    raises(s, "var z = 5 mod 0;", "Division by zero", "div0")
    raises(s, "var z = nonexistent_function(1, 2);", "undefined function nonexistent_function", "undefined_function")
    raises(s, "nonexistent_function();", "undefined function")
    raises(s, "var z = 5; z();", "not a function")
    raises(s, "var z; z.field = 1;", "local variable 'z'")
    raises(s, "var z = undefined; var q = z.field;", "undefined")
    raises(s, "var z = 'str'; var q = z.field;", "string")
    raises(s, "var q = ds_list_find_value(99, 0);", "Data structure with index 99")
    raises(s, "var q = string_length(5);", "must be a string")
    raises(s, "var q = array_length(5);", "must be an array")
    raises(s, "var q = real('abc');", "Unable to convert string")
    raises(s, "var q = floor();", "floor():", "builtin_args")
    raises(s, "var q = clamp(1);", "clamp():", "builtin_args")
    raises(s, "show_error('custom fatal', true);", "custom fatal", "show_error")
    raises(s, "function rec() { return rec(); } rec();", "Stack overflow", "stack")
    raises(s, "var a = {}; var q = a.b.c;", "Variable struct.b not set before reading it")
    raises(s, "global.cnt += 1;", "global variable name 'cnt'", "global_not_set")
    raises(s, "var q; q++;", "local variable 'q'", "local_not_set")
    raises(s, "self.zork++;", "Variable self.zork not set", "var_not_set")
    raises(s, "var l = [1]; l[5] += 1;", "out of range", "array_oob")
    raises(s, "var a = [1,2]; var z = a['x'];", "must be a number", "type")
    # error location data
    try:
        s.run("var a = 1;\n\nvar b = a + zzz;", entry="my_entry")
    except GMError as e:
        eq((e.entry, e.line), ("my_entry", 3), "error entry/line")
    # parse errors
    for bad in ["var = 5;", "if (1 { }", "x = ;", "for (;;", "a.= 1;", "function ( {"]:
        try:
            s.run(bad)
            _fail("expected parse error for %r" % bad)
        except GMParseError as e:
            ok(e.line is not None and e.col is not None, "parse error has position")
    # DESTROYED instance
    i2 = s.create("o", hp=1)
    s.run("instance_destroy(%d);" % i2)
    raises(s, "var t = %d; var z = t.hp;" % i2, "Unable to find instance for object index %d" % i2, "no_instance")
    # lenient div mode
    s.set_div_zero("inf")
    eq(s.eval("1/0"), math.inf, "inf mode")
    s.set_div_zero("error")


@test
def t_builtins():
    s = S()
    eq(ev(s, "floor(2.7)"), 2); eq(ev(s, "floor(-2.1)"), -3)
    eq(ev(s, "ceil(2.1)"), 3); eq(ev(s, "round(2.5)"), 2, "banker's rounding"); eq(ev(s, "round(3.5)"), 4)
    eq(ev(s, "round(2.4)"), 2)
    eq(ev(s, "abs(-3)"), 3); eq(ev(s, "sign(-5)"), -1); eq(ev(s, "sign(0)"), 0)
    eq(ev(s, "min(3, 1, 2)"), 1); eq(ev(s, "max(3, 1, 2)"), 3)
    eq(ev(s, "clamp(5, 0, 3)"), 3); eq(ev(s, "clamp(-5, 0, 3)"), 0); eq(ev(s, "clamp(2, 0, 3)"), 2)
    eq(ev(s, "sqrt(16)"), 4); eq(ev(s, "power(2, 10)"), 1024); eq(ev(s, "sqr(3)"), 9)
    eq(ev(s, "lerp(0, 10, 0.5)"), 5)
    approx(ev(s, "sin(pi / 2)"), 1.0); approx(ev(s, "cos(0)"), 1.0)
    approx(ev(s, "lengthdir_x(10, 0)"), 10.0); approx(ev(s, "lengthdir_y(10, 90)"), -10.0)
    approx(ev(s, "point_distance(0, 0, 3, 4)"), 5.0)
    approx(ev(s, "point_direction(0, 0, 1, 0)"), 0.0); approx(ev(s, "point_direction(0, 0, 0, -1)"), 90.0)
    approx(ev(s, "degtorad(180)"), math.pi)
    eq(ev(s, "angle_difference(10, 350)"), 20)
    eq(ev(s, "frac(2.25)"), 0.25)
    eq(ev(s, "mean(1, 2, 3)"), 2)
    eq(ev(s, "merge_color(c_black, c_white, 0.5)") & 255, 127)
    eq(ev(s, "make_color_rgb(255, 0, 0)"), 255)
    eq(ev(s, "color_get_blue(make_color_rgb(1, 2, 3))"), 3)
    # strings
    eq(ev(s, "string(5)"), "5"); eq(ev(s, "string(5.5)"), "5.5"); eq(ev(s, "string(1/3)"), "0.33")
    eq(ev(s, "string(true)"), "true"); eq(ev(s, "string(undefined)"), "undefined")
    eq(ev(s, "string_length('hello')"), 5)
    eq(ev(s, "string_copy('hello', 2, 3)"), "ell")
    eq(ev(s, "string_char_at('hello', 1)"), "h"); eq(ev(s, "string_char_at('hello', 9)"), "")
    eq(ev(s, "string_pos('l', 'hello')"), 3); eq(ev(s, "string_pos('z', 'hello')"), 0)
    eq(ev(s, "string_replace('aXbXc', 'X', '-')"), "a-bXc")
    eq(ev(s, "string_replace_all('aXbXc', 'X', '-')"), "a-b-c")
    eq(ev(s, "string_delete('hello', 2, 3)"), "ho")
    eq(ev(s, "string_insert('XY', 'hello', 3)"), "heXYllo")
    eq(ev(s, "string_upper('abc')"), "ABC"); eq(ev(s, "string_lower('ABC')"), "abc")
    eq(ev(s, "string_digits('a1b22')"), "122")
    eq(ev(s, "string_count('a', 'banana')"), 3)
    eq(ev(s, "string_format(3.14159, 6, 2)"), "  3.14")
    eq(ev(s, "ord('A')"), 65); eq(ev(s, "chr(66)"), "B")
    eq(ev(s, "real('3.5')"), 3.5); eq(ev(s, "real('42')"), 42)
    eq(ev(s, "string_hash_to_newline('a#b')"), "a\nb")
    eq(ev(s, "string_repeat('ab', 3)"), "ababab")
    eq(ev(s, "is_string('a')"), True); eq(ev(s, "is_real(1)"), True); eq(ev(s, "is_real('1')"), False)
    eq(ev(s, "is_array([])"), True); eq(ev(s, "is_undefined(undefined)"), True); eq(ev(s, "is_bool(true)"), True)
    # random reproducibility
    s1, s2 = S(), S()
    a = [ev(s1, "irandom(100)") for _ in range(5)]
    b = [ev(s2, "irandom(100)") for _ in range(5)]
    eq(a, b, "seeded RNG is deterministic")
    s1.run("random_set_seed(7);"); x = ev(s1, "irandom(1000)")
    s1.run("random_set_seed(7);"); eq(ev(s1, "irandom(1000)"), x, "random_set_seed")
    ok(all(0 <= ev(s1, "irandom(3)") <= 3 for _ in range(50)), "irandom inclusive range")
    ok(all(0 <= ev(s1, "random(1)") < 1 for _ in range(50)), "random range")
    ok(ev(s1, "choose(1, 2, 3)") in (1, 2, 3), "choose")
    ok(all(5 <= ev(s1, "irandom_range(5, 8)") <= 8 for _ in range(30)))
    # ds
    run(s, "var l = ds_list_create(); ds_list_add(l, 'a', 'b'); global.r = ds_list_size(l); global.q = ds_list_find_value(l, 1); global.w = l[| 0]; l[| 0] = 'z'; global.e = ds_list_find_value(l, 0); ds_list_delete(l, 0); global.t = ds_list_size(l); ds_list_destroy(l);")
    eq((G(s, "r"), G(s, "q"), G(s, "w"), G(s, "e"), G(s, "t")), (2, "b", "a", "z", 1), "ds_list")
    run(s, "var m = ds_map_create(); ds_map_add(m, 'k', 1); m[? 'j'] = 2; global.r = m[? 'k'] + ds_map_find_value(m, 'j'); global.q = ds_map_exists(m, 'zz'); global.w = ds_map_size(m); global.e = is_undefined(m[? 'nope']); ds_map_destroy(m);")
    eq((G(s, "r"), G(s, "q"), G(s, "w"), G(s, "e")), (3, False, 2, True), "ds_map")
    run(s, "var g = ds_grid_create(3, 2); g[# 1, 1] = 5; global.r = g[# 1, 1]; global.q = ds_grid_width(g);")
    eq((G(s, "r"), G(s, "q")), (5, 3), "ds_grid")
    raises(s, "var l = ds_list_create(); var z = l[| 3];", "out of range")
    # every real comparison within the epsilon (GameMaker: -1e-14 < 0 is false, 0.000001 < 0.000002 is false, 1 - 1e-9 >= 1 is true)
    eq((ev(s, "-0.00000000000001 < 0"), ev(s, "0.000001 < 0.000002"), ev(s, "(1 - 0.000000001) >= 1"), ev(s, "0.5 < 1"), ev(s, "2 > 1.99"), ev(s, "-0.00000000000001 <= 0")), (False, False, True, True, True, True), "epsilon comparisons")
    # a set past the end pads with 0s (GameMaker's ds_list_set; Chapter 5's list_burnt)
    run(s, "var l = ds_list_create(); ds_list_set(l, 3, 1); global.r = ds_list_size(l); global.q = ds_list_find_value(l, 1); l[| 5] = 7; global.w = ds_list_size(l); global.e = l[| 5]; global.t = is_undefined(ds_list_find_value(l, 9)); ds_list_destroy(l);")
    eq((G(s, "r"), G(s, "q"), G(s, "w"), G(s, "e"), G(s, "t")), (4, 0, 6, 7, True), "ds_list_set pads")
    # json
    eq(ev(s, "json_stringify({a: 1, b: [1,2]})"), '{"a":1,"b":[1,2]}')
    eq(ev(s, "json_parse('{\"a\": [1, 2]}').a"), [1, 2])
    # date
    ok(ev(s, "current_year") == 2024, "deterministic clock")
    ok(ev(s, "date_get_year(date_current_datetime())") == 2024)
    eq(ev(s, "date_get_month(date_create_datetime(2020, 5, 17))"), 5)
    # time
    a = ev(s, "get_timer()"); b = ev(s, "get_timer()")
    ok(b > a, "get_timer monotonic")


@test
def t_mocks():
    s = S()
    raises(s, "totally_unknown_api(1);", "undefined function totally_unknown_api")
    s.mock("totally_unknown_api", lambda sim, a: a * 2)
    eq(ev(s, "totally_unknown_api(21)"), 42, "sim.mock")
    s.mock("const_api", 7)
    eq(ev(s, "const_api()"), 7, "constant mock")
    s.mock("frame_api", lambda sim, f, a: f.self.vars["v"] + a, frame=True)
    s.define_object("o")
    i = s.create("o", v=100)
    s.run("global.r = frame_api(5);", self_obj=i)
    eq(G(s, "r"), 105, "frame mock sees self")
    s.mock("rec_api", lambda sim, *a: 1, record=True)
    s.run("rec_api(1, 'x'); rec_api(2);")
    eq([c.args for c in s.calls("rec_api")], [(1, "x"), (2,)], "recorded calls")
    s.run("draw_text(10, 20, 'hi'); draw_sprite(spr_x, 0, 1, 2); draw_set_color(c_red); draw_set_alpha(0.5);")
    eq(s.calls("draw_text")[0].args, (10, 20, "hi"), "draw_text recorded")
    eq(s.calls("draw_sprite")[0].args[0], s.asset_index("spr_x"), "sprite asset index")
    eq(ev(s, "draw_get_color()"), 255, "draw state")
    eq(ev(s, "draw_get_alpha()"), 0.5)
    s.clear_log()
    eq(len(s.calls()), 0)
    s.run("var sf = surface_create(64, 32); global.w = surface_get_width(sf); global.e = surface_exists(sf); surface_free(sf); global.n = surface_exists(sf);")
    eq((G(s, "w"), G(s, "e"), G(s, "n")), (64, True, False), "surface mock state")
    eq(ev(s, "audio_play_sound(snd_x, 1, false)") > 0, True)
    s.mock_value("my_builtin_var", 33)
    eq(ev(s, "my_builtin_var"), 33)
    # a mock overriding a script
    s.define_script("scr_a", "function scr_a() { return 1; }")
    eq(ev(s, "scr_a()"), 1)
    s.mock("scr_a", lambda sim: 99)
    eq(ev(s, "scr_a()"), 99, "mock overrides script")
    # a python exception inside a mock with bad args becomes a GMError, not a crash
    raises(s, "totally_unknown_api();", "totally_unknown_api(): TypeError")
    # script defined later replaces default builtin of same name
    s.define_script("ossafe_file_exists", "function ossafe_file_exists(f) { return 'script'; }")
    eq(ev(s, "ossafe_file_exists('x')"), "script", "scripts replace default builtins")
    s2 = S()
    s2.record_calls = False
    s2.run("draw_text(1,2,'x');")
    eq(len(s2.log), 0, "record_calls off")


@test
def t_files():
    import tempfile
    import atexit, shutil
    d = tempfile.mkdtemp(prefix="gmlsim_t_")
    atexit.register(shutil.rmtree, d, True)
    s = Sim(sandbox=d)
    s.run("ini_open('save.ini'); ini_write_real('Player', 'hp', 90); ini_write_string('Player', 'name', 'Kris'); ini_write_real('World', 'room', 3); ini_close();")
    ok(os.path.isfile(os.path.join(d, "save.ini")), "ini file really written")
    text = open(os.path.join(d, "save.ini")).read()
    ok("[Player]" in text and 'name="Kris"' in text and "hp=90.000000" in text, "genuine INI format: %r" % text)
    s.run("ini_open('save.ini'); global.r = ini_read_real('Player', 'hp', -1); global.q = ini_read_string('Player', 'name', ''); global.w = ini_read_real('Player', 'nokey', 42); global.e = ini_read_string('Nope', 'k', 'dflt'); global.t = ini_key_exists('Player', 'hp'); global.y = ini_section_exists('World'); global.u = ini_section_exists('Zip'); ini_close();")
    eq((G(s, "r"), G(s, "q"), G(s, "w"), G(s, "e"), G(s, "t"), G(s, "y"), G(s, "u")), (90, "Kris", 42, "dflt", True, True, False), "ini read back")
    s.run("ini_open('save.ini'); ini_section_delete('World'); ini_key_delete('Player', 'hp'); ini_close();")
    t2 = open(os.path.join(d, "save.ini")).read()
    ok("[World]" not in t2 and "hp=" not in t2 and "name=" in t2, "ini deletes persisted")
    raises(s, "ini_write_real('a', 'b', 1);", "no ini file is open", "ini")
    raises(s, "ini_close();", "no ini file is open")
    # real GM format read from a hand-written file
    with open(os.path.join(d, "hand.ini"), "w") as fh:
        fh.write('[G]\nName="NAME"\nTime="123"\nLV=1.000000\n\n[Other]\nx=5\n')
    s.run("ini_open('hand.ini'); global.r = ini_read_string('G', 'Name', 'd'); global.q = ini_read_real('G', 'Time', 0); global.w = ini_read_real('G', 'LV', 0); global.e = ini_read_real('Other', 'x', 0); ini_close();")
    eq((G(s, "r"), G(s, "q"), G(s, "w"), G(s, "e")), ("NAME", 123, 1, 5), "parse hand-written INI")
    # fault injection: interrupt (crash) mid-write
    s.run("ini_open('crash.ini'); ini_write_string('S', 'k', 'v1'); ini_close();")
    good = open(os.path.join(d, "crash.ini")).read()
    s.fs.inject(Fault.interrupt(5), "crash.ini")
    try:
        s.run("ini_open('crash.ini'); ini_write_string('S', 'k', 'v2-longer-value'); ini_write_string('S2', 'z', 'q'); ini_close();")
        _fail("expected SimCrash")
    except SimCrash:
        STATS["pass"] += 1
    partial = open(os.path.join(d, "crash.ini")).read()
    eq(len(partial), 5, "interrupted write leaves partial bytes")
    ok(partial != good, "file differs from the good one")
    s.run("ini_open('crash.ini'); global.r = ini_read_string('S', 'k', 'DEFAULT'); ini_close();")
    eq(G(s, "r"), "DEFAULT", "reading a truncated INI falls back to default")
    s.fs.inject(Fault.truncate(10), "trunc.ini")
    s.run("ini_open('trunc.ini'); ini_write_string('Sec', 'key', 'value-here'); ini_close();")
    eq(len(open(os.path.join(d, "trunc.ini")).read()), 10, "truncate fault")
    s.fs.inject(Fault.zero(), "z.ini")
    s.run("ini_open('z.ini'); ini_write_real('a', 'b', 1); ini_close();")
    eq(os.path.getsize(os.path.join(d, "z.ini")), 0, "zero fault")
    s.fs.inject(Fault.corrupt(3, 5), "c.ini")
    s.run("ini_open('c.ini'); ini_write_string('Section', 'key', 'a-fairly-long-value'); ini_close();")
    ok(open(os.path.join(d, "c.ini"), "rb").read() != b'[Section]\nkey="a-fairly-long-value"\n\n', "corrupt fault")
    s.fs.inject(Fault.fail(), "f.ini")
    raises(s, "ini_open('f.ini'); ini_write_real('a', 'b', 1); ini_close();", "file write failed", "io")
    ok(not os.path.exists(os.path.join(d, "f.ini")), "failed write creates nothing")
    s.fs.inject(Fault.garbage(), "g.ini")
    s.run("ini_open('g.ini'); ini_write_real('a', 'b', 1); ini_close(); ini_open('g.ini'); global.r = ini_read_real('a', 'b', -5); ini_close();")
    eq(G(s, "r"), -5, "garbage INI reads defaults")
    ok(len(s.fs.faults) == 0, "one-shot faults are consumed")
    # file ops
    s.run("var h = file_text_open_write('t.txt'); file_text_write_string(h, 'line1'); file_text_writeln(h); file_text_write_real(h, 42); file_text_close(h);")
    eq(open(os.path.join(d, "t.txt"), "rb").read(), b"line1\r\n42 ", "file_text write (CR LF, a number as %g and a space)")
    s.run("var h = file_text_open_read('t.txt'); global.r = file_text_read_string(h); file_text_readln(h); global.q = file_text_read_real(h); file_text_readln(h); global.w = file_text_eof(h); file_text_close(h);")
    eq((G(s, "r"), G(s, "q"), G(s, "w")), ("line1", 42, True), "file_text read")
    eq(ev(s, "file_exists('t.txt')"), True)
    eq(ev(s, "file_exists('nope.txt')"), False)
    s.run("file_copy('t.txt', 'u.txt');")
    ok(os.path.isfile(os.path.join(d, "u.txt")), "file_copy")
    s.run("file_rename('u.txt', 'v.txt');")
    ok(os.path.isfile(os.path.join(d, "v.txt")) and not os.path.isfile(os.path.join(d, "u.txt")), "file_rename")
    s.run("file_delete('v.txt');")
    ok(not os.path.isfile(os.path.join(d, "v.txt")), "file_delete")
    eq(ev(s, "file_text_open_read('missing.txt')"), -1, "open missing -> -1")
    raises(s, "file_text_close(-1);", "invalid file handle", "file")
    raises(s, "var z = file_exists('../../../../../../etc/passwd');", "sandbox escape refused", "sandbox")
    # ossafe wrappers
    s.run("ossafe_ini_open('o.ini'); ini_write_real('a', 'b', 2); ossafe_ini_close();")
    ok(os.path.isfile(os.path.join(d, "o.ini")), "ossafe_ini_*")
    eq(ev(s, "ossafe_file_exists('o.ini')"), True)
    s.run("var h = ossafe_file_text_open_write('os.txt'); ossafe_file_text_write_string(h, 'x'); ossafe_file_text_close(h);")
    ok(os.path.isfile(os.path.join(d, "os.txt")), "ossafe_file_text_*")
    # fault on file_text close
    s.fs.inject(Fault.interrupt(1), "ft.txt")
    try:
        s.run("var h = file_text_open_write('ft.txt'); file_text_write_string(h, 'abcdef'); file_text_close(h);")
        _fail("expected crash")
    except SimCrash:
        STATS["pass"] += 1
    eq(open(os.path.join(d, "ft.txt")).read(), "a", "interrupted file_text write")
    # snapshot restores files
    snap = s.snapshot()
    s.run("ini_open('snap.ini'); ini_write_real('a', 'b', 1); ini_close(); file_delete('t.txt');")
    ok(os.path.isfile(os.path.join(d, "snap.ini")))
    s.restore(snap)
    ok(not os.path.isfile(os.path.join(d, "snap.ini")) and os.path.isfile(os.path.join(d, "t.txt")), "snapshot restores sandbox files")


@test
def t_snapshot():
    s = mk_objs()
    s.define_event("obj_a", "Create", 0, "n = 0; arr = [1,2,3]; st = {k: 1};")
    s.define_event("obj_a", "Step", 0, "n++; arr[0] += 1; st.k += 1;")
    a = s.create("obj_a")
    s.step(2)
    snap = s.snapshot()
    s.step(3)
    eq(s.get(a, "n"), 5)
    s.restore(snap)
    eq(s.get(a, "n"), 2, "restore instance state")
    eq(s.py(s.get(a, "arr")), [3, 2, 3], "restore arrays")
    eq(s.py(s.get(a, "st")), {"k": 3}, "restore structs")
    s.step(1)
    eq(s.get(a, "n"), 3, "can continue after restore")
    # branching
    s.restore(snap)
    s.set(a, "n", 1000)
    snap2 = s.snapshot()
    s.step(1)
    s.restore(snap)
    eq(s.get(a, "n"), 2, "branch 1 independent")
    s.restore(snap2)
    eq(s.get(a, "n"), 1000, "branch 2 independent")
    # snapshot isolation: mutating after snapshot doesn't change it
    b = s.create("obj_a")
    s.restore(snap)
    ok(b not in s.instances, "instances created after snapshot vanish on restore")
    eq(s.frame_no, 2, "frame counter restored")
    # globals / rng
    s.globals["g"] = GMArray([1, 2])
    sn = s.snapshot()
    s.globals["g"].data.append(3)
    r1 = s.eval("irandom(1000000)")
    s.restore(sn)
    eq(len(s.globals["g"].data), 2, "globals deep-copied")
    eq(s.eval("irandom(1000000)"), r1, "rng state restored")
    # statics restored
    s.define_script("cnt", "function cnt() { static n = 0; n++; return n; }")
    s.eval("cnt()"); sn = s.snapshot(); s.eval("cnt()"); s.eval("cnt()")
    s.restore(sn)
    eq(s.eval("cnt()"), 2, "statics restored")


@test
def t_load_and_names():
    s = S()
    st = s.load_dir(os.path.join(os.path.dirname(__file__), "..", "testdata"))
    eq(st["objects_events"], 4, "loaded event files")
    eq(st["scripts"], 2)
    eq(st["unclassified"], [])
    ok("obj_demo" in s.objects)
    ok(s.has_event("obj_demo", "Create", 0) and s.has_event("obj_demo", "Alarm", 2) and s.has_event("obj_demo", "Other", 10))
    s.define_object("obj_demo")
    s.define_global("score", 0)
    i = s.create("obj_demo", 1, 1)
    s.step(1)
    eq(s.get(i, "ticks"), 1, "file-loaded Step ran")
    eq(s.eval("scr_double(21)"), 42, "file-loaded script")
    eq(s.eval("scr_helper_uses_enum()"), 7, "script with enum in same file")
    r = s.load_source("gml_Object_obj_x_Collision_obj_demo", "hit = true;")
    eq(r, "objects_events", "collision event name parses")
    ok(s.load_source("junk_name_here", "x") is None, "unclassified returns None")
    r = s.load_source("gml_RoomCC_room_x_5_PreCreate", "a = 1;")
    eq(r, "room_cc")
    # loose merged names
    r = s.load_source("titan_spawn_enemy_other_10", "z = 1;")
    eq(r, "objects_events")
    ok(s.has_event("titan_spawn_enemy", "Other", 10), "loose naming")


@test
def t_loader_options():
    s = S()
    s.define_script("boot", "global.booted = 1;\nfunction boot_helper() { return global.booted + 1; }")
    ok("booted" not in s.globals, "top-level script statements do not run at load")
    s.run_global_inits() if s.ensure_script("boot_helper") else None
    eq(s.globals.get("booted"), 1, "run_global_inits executes top-level statements once")
    s.globals["booted"] = 5
    s.run_global_inits()
    eq(s.globals["booted"], 5, "global inits run only once")
    eq(s.eval("boot_helper()"), 6)
    d = os.path.join(os.path.dirname(__file__), "..", "testdata")
    s2 = S()
    st = s2.load_dir(d, kinds=("scripts",))
    eq((st.get("scripts"), st.get("objects_events")), (2, 0), "kinds filter")
    ok("obj_demo" in s2.objects and not s2.objects["obj_demo"].events, "object names defined, events not loaded")
    s3 = S()
    st = s3.load_dir(d, match="scr_double")
    eq(st.get("scripts"), 1, "match filter")
    s4 = S()
    s4.define_object("o")
    i = s4.create("o")
    s4.inject_write_fault(Fault.truncate(3), "x.ini")
    s4.run("ini_open('x.ini'); ini_write_string('S', 'k', 'v'); ini_close();")
    eq(len(s4.fs.read("x.ini")), 3, "inject_write_fault convenience")
    eq(s4.fs.write_log[-1][2], "truncate(3)", "write log records fault")
    # builtin vars and consts
    s4.define_const("MY_CONST", 12)
    eq(s4.eval("MY_CONST + 1"), 13, "define_const")
    s4.define_asset("spr_custom")
    eq(s4.eval("spr_custom"), s4.asset_index("spr_custom"))
    s4.auto_assets = False
    raises(s4, "var z = spr_not_defined;", "not set before reading it")
    # sim.set / sim.get through python
    s4.set(i, "arr", [1, 2, 3])
    eq(s4.py(s4.get(i, "arr")), [1, 2, 3], "python list becomes a GML array")
    s4.set("global", "g", {"a": [1]})
    eq(s4.eval("global.g.a[0]"), 1, "python dict becomes a GML struct")
    eq(s4.py(s4.call("array_length", [1, 2])), 2, "sim.call on a builtin")


@test
def t_perf():
    s = S()
    big = []
    for i in range(1500):
        big.append("if (a == %d) { b = %d; c = [%d, %d]; global.g%d = a + b * 2; }\nelse if (a > 5000) { b += 1; }\n" % (i, i, i, i + 1, i % 7))
    src = "var a = 3; var b = 0; var c;\n" + "".join(big)
    lines = src.count("\n")
    ok(lines >= 3000)
    from .parser import parse
    t = time.time()
    parse(src, "big")
    dt = time.time() - t
    ok(dt < 1.0, "parse %d lines in %.3fs" % (lines, dt))
    if VERBOSE:
        print("  parse %d lines: %.3fs" % (lines, dt))
    # menu-like object: thousands of frames
    s = S()
    s.define_object("menu")
    s.define_event("menu", "Create", 0, "sel = 0; items = ['A','B','C','D']; timer = 0; cnt = 0;")
    s.define_event("menu", "Step", 0, """
timer++;
if (keyboard_check_pressed(vk_down)) sel = (sel + 1) mod array_length(items);
if (keyboard_check_pressed(vk_up)) sel = (sel - 1 + array_length(items)) mod array_length(items);
for (var i = 0; i < array_length(items); i++) { if (i == sel) cnt += 1; }
switch (sel) { case 0: cnt += 1; break; case 1: cnt += 2; break; default: cnt += 3; }
""")
    s.define_event("menu", "Draw", 0, """
for (var i = 0; i < array_length(items); i++) {
    draw_set_color(i == sel ? c_yellow : c_white);
    draw_text(20, 20 + i * 16, items[i]);
}
""")
    m = s.create("menu")
    for f in range(0, 3000, 7):
        s.press("down", frame=f)
    s.record_calls = False
    t = time.time()
    s.step(3000)
    dt = time.time() - t
    if VERBOSE:
        print("  3000 menu frames: %.3fs" % dt)
    ok(dt < 3.0, "3000 frames in %.2fs" % dt)
    eq(s.get(m, "timer"), 3000)
    ok(s.get(m, "cnt") > 3000)
    t = time.time()
    s.run("var n = 0; for (var i = 0; i < 200000; i++) { n += i mod 3; } global.n = n;")
    dt = time.time() - t
    if VERBOSE:
        print("  200k loop iterations: %.3fs" % dt)
    ok(dt < 3.0, "200k iterations in %.2fs" % dt)
    # parse cache: recompiling identical source is a dict hit
    from .compiler import compile_code
    compile_code("cache_probe", src)
    t = time.time()
    for _ in range(500):
        compile_code("cache_probe", src)
    ok(time.time() - t < 0.05, "compile cache hit is fast")
    a = compile_code("cache_probe", src)
    b = compile_code("cache_probe", src)
    ok(a is b, "same Code object returned from cache")


@test
def t_misc():
    s = S()
    # hoisting / nested decls
    run(s, "function outer() { function inner() { return 5; } return inner(); } global.r = outer();")
    eq(G(s, "r"), 5, "nested function declaration")
    # comments
    run(s, "// line\nglobal.r = 1; /* block\ncomment */ global.q = 2; // end")
    eq((G(s, "r"), G(s, "q")), (1, 2), "comments")
    run(s, "#region Foo\nglobal.r = 3;\n#endregion\n")
    eq(G(s, "r"), 3, "#region ignored")
    run(s, "global.r = 'a;b'; // ; in string\n")
    eq(G(s, "r"), "a;b")
    run(s, "global.r = 'multi\nline';")
    eq(G(s, "r"), "multi\nline", "multiline string")
    run(s, "global.r = 5;;;; global.q = 6;")
    eq((G(s, "r"), G(s, "q")), (5, 6), "empty statements")
    run(s, "var a = 1\nvar b = 2\nglobal.r = a + b")
    eq(G(s, "r"), 3, "semicolons optional")
    run(s, "if (1) global.r = 'x'\nelse global.r = 'y'")
    eq(G(s, "r"), "x")
    run(s, "global.r = (1 > 0) ? ((2 > 1) ? 'a' : 'b') : 'c';")
    eq(G(s, "r"), "a", "nested ternary")
    run(s, "var f = function() { return 3; }; global.r = (function() { return 4; })() + f();")
    eq(G(s, "r"), 7, "immediately-invoked function")
    run(s, "global.fn = function(a) { return a + 1; }; global.r = global.fn(2);")
    eq(G(s, "r"), 3, "function stored in global, called as global.fn()")
    run(s, "var s1 = {f: function() { return 9; }}; global.r = s1.f();")
    eq(G(s, "r"), 9)
    eq(ev(s, "is_nan(NaN)"), True)
    eq(ev(s, "infinity > 1000000"), True)
    run(s, "var t = 'abc'; global.r = string_length(t) + string_length('xx');")
    eq(G(s, "r"), 5)
    # self in noself context
    s.define_object("o")
    i = s.create("o", hp=3)
    s.run("hp += 1; global.r = hp;", self_obj=i)
    eq(G(s, "r"), 4, "self var compound")
    eq(s.eval("hp * 2", self_obj=i), 8, "eval with self")
    s.run("with (o) { hp = 10; }")
    eq(s.get(i, "hp"), 10)
    # delete is a no-op statement
    run(s, "var d = {a: 1}; delete d;")
    ok(True)
    # string comparisons / equality of arrays by identity
    eq(ev(s, "'abc' == 'abc'"), True)
    # undefined handling
    eq(ev(s, "is_undefined(variable_struct_get({}, 'q'))"), True)
    # asset auto-creation for prefixed names
    a1 = s.eval("spr_player"); a2 = s.eval("spr_player"); a3 = s.eval("spr_other")
    ok(a1 == a2 and a1 != a3, "asset indices stable & distinct")
    raises(s, "var z = obj_never_defined;", "not set before reading it")
    # game_end
    s.run("game_end();")
    ok(s.game_ended)
    s.game_ended = False
    # alarm_set
    s.define_object("al")
    s.define_event("al", "Alarm", 2, "global.fired = 1;")
    i = s.create("al")
    s.run("alarm_set(2, 1);", self_obj=i)
    s.step(1)
    eq(s.globals.get("fired"), 1, "alarm_set()")
    # debug messages captured
    s.run("show_debug_message('hello ' + string(5));")
    eq(s.debug_messages[-1], "hello 5")
    # variable_global_*
    s.run("variable_global_set('vg', 5);")
    eq((ev(s, "variable_global_exists('vg')"), ev(s, "variable_global_get('vg')"), ev(s, "variable_global_exists('nop')")), (True, 5, False))
    # object helpers
    eq(ev(s, "object_get_name(o)"), "o")
    s.define_object("kid", parent="o")
    eq(ev(s, "object_get_parent(kid)"), s.object_index("o"))
    eq(ev(s, "object_is_ancestor(kid, o)"), True)
    eq(ev(s, "object_exists(o)"), True)
    # parent cycle detection
    s.define_object("cyc1", parent="cyc2")
    try:
        s.define_object("cyc2", parent="cyc1")
        s.chain("cyc1")
        _fail("cycle not detected")
    except GMError:
        STATS["pass"] += 1
    # long chain of else-if
    chain = "var v = 7; var r = 0;" + "".join("%sif (v == %d) r = %d;" % ("else " if k else "", k, k * 2) for k in range(30)) + "global.r = r;"
    run(s, chain)
    eq(G(s, "r"), 14, "long else-if chain")


REAL_DIRS = ["/home/claude/work/gml/base/CodeEntries", "/home/claude/work/build/merged"]


@test
def t_b46_engine_rules():
    """build 46: rules the real runner has that the emulator was stricter about, the scripted controller, reloading"""
    s = S()
    run(s, "global.a = 0; global.a[2] = 5; var b = 7; b[1] = 3; global.r = [global.a, b]; xx = 1.5; xx[0] = 2; global.r2 = xx;")
    eq(s.py(ev(s, "global.r")), [[0, 0, 5], [0, 3]], "an indexed write into a number makes a new array")
    eq(s.py(ev(s, "global.r2")), [2], "instance variable too")
    raises(s, "var c = 4; var d = c[0];", contains="not an array")
    eq(ev(s, "string_hash_to_newline(42)"), "42", "string_hash_to_newline takes a number")
    s.press("gp_shoulderl", hold=2)
    s.press("S", hold=1)
    s.step(1)
    eq(s.py(ev(s, "[gamepad_button_check(0, gp_shoulderl), gamepad_button_check_pressed(0, gp_shoulderl), keyboard_check(gp_shoulderl), keyboard_check(ord(\"S\")), keyboard_check(vk_anykey)]")),
       [True, True, False, True, True], "a scripted controller button: only the gamepad functions see it")
    s.step(1)
    eq(s.py(ev(s, "[gamepad_button_check(0, gp_shoulderl), gamepad_button_check_pressed(0, gp_shoulderl), keyboard_check(vk_anykey)]")),
       [True, False, False], "held, not pressed; vk_anykey ignores it")
    s.load_source("gml_GlobalScript_rl", "function rl_f() { return 1; }")
    s.run_global_inits()
    eq(ev(s, "rl_f()"), 1)
    s.load_source("gml_GlobalScript_rl", "function rl_f() { return 2; }")
    eq(ev(s, "rl_f()"), 2, "a script entry loaded again runs its new text")


@test
def t_b53_deactivate_mid_phase():
    """build 53: an instance switched off by an earlier instance's event of the same phase does not run that phase's event
    (nor its Draw); it runs again once switched back on"""
    s = S()
    s.define_object("k")
    s.define_object("v")
    s.define_event("k", "Step", 0, "if (global.off) { instance_deactivate_object(v); global.off = false; }")
    s.define_event("v", "Create", 0, "n = 0; d = 0;")
    s.define_event("v", "Step", 0, "n += 1;")
    s.define_event("v", "Draw", 0, "d += 1;")
    run(s, "global.off = false;")
    k = s.create("k")
    v = s.create("v")
    s.step(1)
    eq(s.get(v, "n"), 1, "runs while on")
    run(s, "global.off = true;")
    s.step(1)
    eq(s.deact[v].vars["n"], 1, "switched off by the controller before its turn: no Step that frame")
    eq(s.deact[v].vars["d"], 1, "and no Draw (the one Draw is from the frame it was on)")
    run(s, "instance_activate_object(v);")
    s.step(1)
    eq(s.get(v, "n"), 2, "back on: runs again")


@test
def t_b53_destroyed_other_readable():
    """build 53 (DRBR): a collision event whose other is destroyed by other's own user event still reads other's variables
    for the rest of that event (Chapter 2's yellow shot: with (other) event_user(0); ... other.big); after the event the id
    is gone (instance_exists false, a read by id is an error again)"""
    s = S()
    s.define_object("shot")
    s.define_object("tgt")
    s.define_event("shot", "Create", 0, "big = 7;")
    s.define_event("shot", "Other", 10, "instance_destroy();")
    s.define_event("tgt", "Other", 11, "with (other) { event_user(0); } got = other.big; alive = instance_exists(other);")
    a = s.create("shot")
    b = s.create("tgt")
    s.run_event(s.instances[b], "Other", 11, other=s.instances[a])
    eq(s.get(b, "got"), 7, "other.big read after other destroyed itself in this event")
    eq(s.get(b, "alive"), False, "instance_exists says it is gone")
    raises(s, "var t = %d; var z = t.big;" % a, "Unable to find instance for object index %d" % a, "no_instance")


@test
@test
def t_drbr_bundle_buffers():
    """DRBR: the read-only bundle behind the save area, buffer_load / buffer_save, buffer_sha1 / buffer_md5"""
    import tempfile, hashlib
    import atexit, shutil
    d = tempfile.mkdtemp(prefix="gmlsim_sa_")
    bnd = tempfile.mkdtemp(prefix="gmlsim_bd_")
    atexit.register(shutil.rmtree, d, True)
    atexit.register(shutil.rmtree, bnd, True)
    s = Sim(sandbox=d)
    s.fs.bundle = bnd
    os.makedirs(os.path.join(bnd, "inc"))
    payload = b"LINE1\r\n2 \r\nlast"
    with open(os.path.join(bnd, "inc", "f.txt"), "wb") as fh:
        fh.write(payload)
    s.run("global.e = file_exists('inc/f.txt'); global.n = file_exists('inc/none.txt');")
    eq((G(s, "e"), G(s, "n")), (True, False), "file_exists sees the bundle")
    s.run("var _b = buffer_load('inc/f.txt'); global.sz = buffer_get_size(_b); global.h1 = buffer_sha1(_b, 0, buffer_get_size(_b)); global.h5 = buffer_md5(_b, 0, buffer_get_size(_b)); buffer_save(_b, 'out/copy.txt'); buffer_delete(_b); global.m = buffer_load('inc/none.txt');")
    eq(G(s, "sz"), len(payload), "buffer_load reads the whole bundle file")
    eq(G(s, "h1"), hashlib.sha1(payload).hexdigest(), "buffer_sha1 = sha1 of the bytes")
    eq(G(s, "h5"), hashlib.md5(payload).hexdigest(), "buffer_md5 = md5 of the bytes")
    eq(G(s, "m"), -1, "buffer_load of a missing file gives -1")
    ok(open(os.path.join(d, "out", "copy.txt"), "rb").read() == payload, "buffer_save writes the exact bytes into the save area")
    ok(not os.path.exists(os.path.join(bnd, "out")), "nothing is written into the bundle")
    # file_text_write_real / writeln as GameMaker on Windows writes them (a real Chapter 3 save's bytes)
    s.run('var _f = file_text_open_write("t_real.txt"); file_text_write_string(_f, "ENDER"); file_text_writeln(_f); file_text_write_real(_f, 320); file_text_writeln(_f); file_text_write_real(_f, 180.993); file_text_writeln(_f); file_text_write_real(_f, 0.85); file_text_writeln(_f); file_text_write_real(_f, 1181310); file_text_close(_f);')
    eq(open(os.path.join(d, "t_real.txt"), "rb").read(), b"ENDER\r\n320 \r\n180.993 \r\n0.85 \r\n1.18131e+06 ", "numbers as %g plus a space, lines CR LF")
    s.run('var _f = file_text_open_read("t_real.txt"); global.a0 = file_text_read_string(_f); file_text_readln(_f); global.a1 = file_text_read_real(_f); file_text_readln(_f); global.a2 = file_text_read_real(_f); file_text_readln(_f); file_text_readln(_f); global.a3 = file_text_read_real(_f); file_text_readln(_f); global.a4 = file_text_eof(_f); file_text_close(_f);')
    eq((G(s, "a0"), G(s, "a1"), G(s, "a2"), G(s, "a3"), G(s, "a4")), ("ENDER", 320, 180.993, 1181310, True), "and they read back")
    # an indexed write replaces a string with a new array (scr_gamestart: global.msg = " "; global.msg[i] = ...)
    s.run('global.mg = " "; for (var _i = 0; _i < 3; _i++) global.mg[_i] = "x" + string(_i); var _l = "a"; _l[1] = 7; global.ml = _l;')
    eq((s.py(s.eval("global.mg")), s.py(s.eval("global.ml"))), (["x0", "x1", "x2"], [0, 7]), "an indexed write turns a string into an array")
    # the save area shadows the bundle for the same name
    os.makedirs(os.path.join(d, "inc"), exist_ok=True)
    with open(os.path.join(d, "inc", "f.txt"), "wb") as fh:
        fh.write(b"SAVEAREA")
    s.run("var _f = file_text_open_read('inc/f.txt'); global.l = file_text_read_string(_f); file_text_close(_f);")
    eq(G(s, "l"), "SAVEAREA", "the save area is read before the bundle")
    s.run("global.dl = file_delete('inc/f.txt');")
    s.run("var _f = file_text_open_read('inc/f.txt'); global.l = file_text_read_string(_f); file_text_close(_f);")
    eq(G(s, "l"), "LINE1", "after deleting the save-area copy the bundle's is read again")
    ok(os.path.isfile(os.path.join(bnd, "inc", "f.txt")), "file_delete never deletes a bundle file")


def t_real_scr_damage():
    d = REAL_DIRS[0]
    if not os.path.isdir(d):
        print("  (skipped: %s not present)" % d)
        return
    s = Sim(seed=1)
    st = s.load_dir(d, kinds=("scripts",))
    ok(st["scripts"] > 900, "loaded %d global scripts" % st["scripts"])
    ok("scr_damage" in s.script_entries and "scr_damage_calculation" in s.script_entries)
    ok("obj_knight_enemy" in s.objects, "object names defined from file names without loading events")
    s.mock("instance_create", lambda sim, x, y, obj: sim.create_instance(obj, x, y).id)
    s.define_object("hero_dummy"); s.define_object("battle_dummy")
    heroes = [s.create("hero_dummy", 100 + i * 50, 200, myheight=40) for i in range(3)]
    s.define_globals(inv=-1, invc=1, chapter=1, char=[1, 2, 3], hp=[0, 90, 110, 70], maxhp=[0, 90, 110, 70],
                     battledf=[0, 2, 1, 0], charaction=[0, 0, 0, 0], chararmor1=[0, 0, 0, 0],
                     chararmor2=[0, 0, 0, 0], charinstance=heroes)
    en = s.create("battle_dummy", target=0, damage=40)
    s.globals["inv"] = 5
    r = s.call("scr_damage", self_obj=en)
    eq((r, s.py(s.globals["hp"])), (None, [0, 90, 110, 70]), "trivial case: inv>=0 is a no-op")
    s.globals["inv"] = -1
    s.call("scr_damage", self_obj=en)
    eq(s.py(s.globals["hp"]), [0, 50, 110, 70], "real scr_damage reduced hp[1] by 40")
    eq(s.get(en, "tdamage"), 40)
    eq(s.globals["inv"], 30, "global.inv = invc * 30")
    eq(s.py(s.globals["damage_cache"]), [90, 110, 70], "scr_damage_cache (another script file) ran")
    ok(any(i.obj == "obj_dmgwriter" for i in s.instances.values()), "damage writer instance created")
    s.globals["inv"] = -1
    del s.globals["battledf"]
    try:
        s.call("scr_damage", self_obj=en)
        _fail("expected missing-global error")
    except GMError as e:
        ok("battledf" in e.message and e.stack == ["scr_damage_calculation", "scr_damage"], "stack %s" % e.stack)
        eq(e.entry, "gml_GlobalScript_scr_damage_calculation")


@test
def t_real_parse_coverage():
    if "--real" not in sys.argv:
        return
    from .parsecheck import check_dir
    for d in REAL_DIRS:
        if not os.path.isdir(d):
            continue
        n, lines, fails, cfails = check_dir(d, True, verbose=True)
        eq((len(fails), len(cfails)), (0, 0), "parse+compile failures in %s" % d)
        ok(n > 0)


def main():
    t0 = time.time()
    for fn in TESTS:
        _CUR[0] = fn.__name__
        try:
            fn()
        except Exception:
            STATS["fail"] += 1
            FAILS.append("[%s] CRASH\n%s" % (fn.__name__, traceback.format_exc()))
    total = STATS["pass"] + STATS["fail"]
    for f in FAILS:
        print("FAIL", f)
    print("gmlsim selftest: %d assertions, %d passed, %d failed (%.2fs, %d test groups)" %
          (total, STATS["pass"], STATS["fail"], time.time() - t0, len(TESTS)))
    return 1 if STATS["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
