"""AST -> Python closure compiler.  Statement closures return None or BRK/CNT/RET."""
import re

from . import ops
from . import rt as _rt
from .errors import GMError, GMThrow
from .parser import parse, parse_expression, FuncDef
from .rt import (Frame, BRK, CNT, RET, share, get_field, set_field, vars_of, array_get, array_set, elem_for_write,
                 ds_get, ds_set, to_index, not_array, err_oor, err_local_unset, err_unset,
                 err_global_unset, err_global_is_function, call_func, call_ctor, call_value, resolve_instance)
from .values import (GMArray, GMStruct, GMInstance, GMFunc, GMMethod, BuiltinRef, MISS, GLOBAL_REF, gml_str,
                     GlobalRef, typeof)

# GameMaker: an indexed write into a variable that holds a number makes it a new array (the number is dropped); only
# reading a number with an index is an error
# a value an indexed WRITE replaces with a new array (GameMaker does: Chapter 3's scr_gamestart sets global.msg = " " and
# then writes global.msg[i] - every new game and every load runs it)
_NUMW = (int, float, bool, str)

truth = ops.truth
LOOP_LIMIT = 2_000_000
_ARG_RE = re.compile(r"^argument(\d+)$")
_CALL_ERRORS = (TypeError, ValueError, IndexError, KeyError, AttributeError, OverflowError, ZeroDivisionError)


class Code:
    __slots__ = ("entry", "body", "funcs", "enums", "macros", "has_stmts", "src_lines")

    def __init__(self, entry, body, funcs, enums, macros, has_stmts):
        self.entry = entry
        self.body = body
        self.funcs = funcs          # [(name, GMFunc)] hoisted global-script functions
        self.enums = enums          # [(name, [(member, closure|None)])]
        self.macros = macros        # [(name, text)]
        self.has_stmts = has_stmts

    def __deepcopy__(self, memo):
        return self


class Ctx:
    __slots__ = ("decl", "statics")

    def __init__(self):
        self.decl = set()
        self.statics = set()


def _noop(f):
    return None


class Compiler:
    def __init__(self, entry, is_script=False):
        self.entry = entry
        self.is_script = is_script
        self.ctx = Ctx()
        self.funcs = []
        self.enums = []
        self.macros = []
        self.depth = 0

    # ------------------------------------------------------------ entry points
    def compile_program(self, ast):
        stmts = ast[2]
        pairs = []
        has = False
        for s in stmts:
            if self.is_script and s[0] == "fdecl":
                fd = s[2]
                self.funcs.append((fd.name, self.compile_function(fd, fd.name)))
                continue
            c = self.stmt(s)
            if s[0] not in ("enum", "macro"):
                has = True
            pairs.append((c, s[1]))
        body = self.mk_block(pairs)
        return Code(self.entry, body, self.funcs, self.enums, self.macros, has)

    def compile_function(self, fd, name):
        saved = self.ctx
        self.ctx = Ctx()
        try:
            self.ctx.decl.update(p[0] for p in fd.params)
            params = []
            for pn, pd in fd.params:
                params.append((pn, self.expr(pd) if pd is not None else None))
            parent = None
            if fd.parent is not None:
                parent = (fd.parent[0], [self.expr(a) for a in fd.parent[1]])
            body = self.stmt(fd.body)
            gf = GMFunc(name or "anonymous", params, body, fd.ctor, parent, frozenset(self.ctx.decl),
                        frozenset(self.ctx.statics), self.entry, fd.line)
        finally:
            self.ctx = saved
        return gf

    # ------------------------------------------------------------ blocks
    def mk_block(self, pairs):
        entry = self.entry
        pairs = [p for p in pairs if p[0] is not _noop]
        if not pairs:
            return _noop
        fns = tuple(p[0] for p in pairs)
        lns = tuple(p[1] for p in pairs)
        if len(fns) == 1:
            s0 = fns[0]
            l0 = lns[0]

            def run1(f):
                try:
                    return s0(f)
                except GMError as e:
                    if e.line is None:
                        e.line = l0
                        e.entry = entry
                    raise
            return run1

        def run(f):
            i = 0
            try:
                for s in fns:
                    c = s(f)
                    if c:
                        return c
                    i += 1
            except GMError as e:
                if e.line is None:
                    e.line = lns[i]
                    e.entry = entry
                raise
        return run

    # ------------------------------------------------------------ statements
    def stmt(self, n):
        return getattr(self, "s_" + n[0])(n)

    def s_block(self, n):
        return self.mk_block([(self.stmt(s), s[1]) for s in n[2]])

    def s_expr(self, n):
        e = self.expr(n[2])

        def run(f):
            e(f)
        return run

    def s_macro(self, n):
        self.macros.append((n[2], n[3]))
        return _noop

    def s_enum(self, n):
        mem = [(m, self.expr(v) if v is not None else None) for m, v in n[3]]
        self.enums.append((n[2], mem))
        return _noop

    def s_fdecl(self, n):
        fd = n[2]
        fn = self.compile_function(fd, fd.name)
        name = fd.name
        # name becomes visible as a local-ish callable in this scope: bind as method on self
        def run(f):
            f.self.vars[name] = GMMethod(fn, f.self)
        return run

    def s_var(self, n):
        items = []
        for name, init in n[2]:
            c = self.expr(init) if init is not None else None
            self.ctx.decl.add(name)
            items.append((name, c))
        if len(items) == 1 and items[0][1] is not None:
            name, c = items[0]

            def run1(f):
                v = c(f)
                if v.__class__ is GMArray:
                    v.cow = True
                f.loc[name] = v
            return run1

        def run(f):
            loc = f.loc
            for name, c in items:
                if c is not None:
                    v = c(f)
                    if v.__class__ is GMArray:
                        v.cow = True
                    loc[name] = v
        return run

    def s_gvar(self, n):
        names = n[2]

        def run(f):
            f.sim.globalvars.update(names)
        return run

    def s_static(self, n):
        name = n[2]
        c = self.expr(n[3]) if n[3] is not None else None
        self.ctx.statics.add(name)
        entry = self.entry

        def run(f):
            st = f.statics
            if st is None:
                st = f.statics = f.sim.statics.setdefault(("code", entry), {})
            if name not in st:
                st[name] = share(c(f)) if c is not None else None
        return run

    def s_empty(self, n):
        return _noop

    def s_if(self, n):
        cond = self.expr(n[2])
        then = self.stmt(n[3])
        els = self.stmt(n[4]) if n[4] is not None else None
        if els is None:
            def run(f):
                c = cond(f)
                if c is True or (c is not False and truth(c)):
                    return then(f)
        else:
            def run(f):
                c = cond(f)
                if c is True or (c is not False and truth(c)):
                    return then(f)
                return els(f)
        return run

    def s_while(self, n):
        cond = self.expr(n[2])
        body = self.stmt(n[3])

        def run(f):
            it = 0
            while True:
                c = cond(f)
                if c is not True and (c is False or not truth(c)):
                    break
                r = body(f)
                if r:
                    if r == BRK:
                        break
                    if r != CNT:
                        return r
                it += 1
                if it > LOOP_LIMIT:
                    raise GMError("Infinite loop suspected (while ran > %d iterations)" % LOOP_LIMIT, "loop_limit")
        return run

    def s_do(self, n):
        body = self.stmt(n[2])
        cond = self.expr(n[3])

        def run(f):
            it = 0
            while True:
                r = body(f)
                if r:
                    if r == BRK:
                        break
                    if r != CNT:
                        return r
                c = cond(f)
                if c is True or (c is not False and truth(c)):
                    break
                it += 1
                if it > LOOP_LIMIT:
                    raise GMError("Infinite loop suspected (do-until ran > %d iterations)" % LOOP_LIMIT, "loop_limit")
        return run

    def s_repeat(self, n):
        cnt = self.expr(n[2])
        body = self.stmt(n[3])

        def run(f):
            k = cnt(f)
            if k.__class__ is not int:
                k = int(ops.num(k, "repeat count"))
            for _ in range(k):
                r = body(f)
                if r:
                    if r == BRK:
                        break
                    if r != CNT:
                        return r
        return run

    def s_for(self, n):
        init = self.stmt(n[2]) if n[2] is not None else None
        cond = self.expr(n[3]) if n[3] is not None else None
        step = self.stmt(n[4]) if n[4] is not None else None
        body = self.stmt(n[5])

        def run(f):
            if init is not None:
                init(f)
            it = 0
            while True:
                if cond is not None:
                    c = cond(f)
                    if c is not True and (c is False or not truth(c)):
                        break
                r = body(f)
                if r:
                    if r == BRK:
                        break
                    if r != CNT:
                        return r
                if step is not None:
                    step(f)
                it += 1
                if it > LOOP_LIMIT:
                    raise GMError("Infinite loop suspected (for ran > %d iterations)" % LOOP_LIMIT, "loop_limit")
        return run

    def s_switch(self, n):
        e = self.expr(n[2])
        cases = n[3]
        exprs = []
        blocks = []
        default_idx = None
        allconst = True
        for i, (ce, stmts) in enumerate(cases):
            if ce is None:
                default_idx = i
                exprs.append(None)
            else:
                if ce[0] != "const":
                    allconst = False
                exprs.append(self.expr(ce))
            blocks.append(self.mk_block([(self.stmt(s), s[1]) for s in stmts]))
        table = None
        if allconst:
            table = {}
            for i, (ce, _) in enumerate(cases):
                if ce is not None and ce[2] not in table:
                    table[ce[2]] = i
        nb = len(blocks)
        eq = ops.eq

        def run(f):
            v = e(f)
            start = None
            if table is not None:
                try:
                    start = table.get(v)
                except TypeError:
                    start = None
                if start is None and v.__class__ is float:
                    for k, i in table.items():
                        if k.__class__ is not str and eq(v, k):
                            start = i
                            break
            else:
                for i in range(nb):
                    ce = exprs[i]
                    if ce is not None and eq(v, ce(f)):
                        start = i
                        break
            if start is None:
                start = default_idx
                if start is None:
                    return None
            for i in range(start, nb):
                r = blocks[i](f)
                if r:
                    if r == BRK:
                        return None
                    return r
        return run

    def s_with(self, n):
        e = self.expr(n[2])
        body = self.stmt(n[3])

        def run(f):
            insts = f.sim.with_targets(f, e(f))
            old_self = f.self
            old_other = f.other
            try:
                for inst in insts:
                    if inst.__class__ is GMInstance and inst.dead:
                        continue
                    f.self = inst
                    f.other = old_self
                    r = body(f)
                    if r:
                        if r == BRK:
                            break
                        if r != CNT:
                            return r
            finally:
                f.self = old_self
                f.other = old_other
        return run

    def s_break(self, n):
        return lambda f: BRK

    def s_continue(self, n):
        return lambda f: CNT

    def s_exit(self, n):
        def run(f):
            f.ret = None
            return RET
        return run

    def s_return(self, n):
        if n[2] is None:
            def run0(f):
                f.ret = None
                return RET
            return run0
        e = self.expr(n[2])

        def run(f):
            v = e(f)
            if v.__class__ is GMArray:
                v.cow = True
            f.ret = v
            return RET
        return run

    def s_throw(self, n):
        e = self.expr(n[2])

        def run(f):
            v = e(f)
            if v.__class__ is GMStruct and "message" in v.vars:
                text = "Unhandled exception: %s" % gml_str(v.vars["message"])
            else:
                text = "Unhandled exception: %s" % gml_str(v)
            raise GMThrow(v, text)
        return run

    def s_delete(self, n):
        e = self.expr(n[2])

        def run(f):
            e(f)
        return run

    def s_try(self, n):
        body = self.stmt(n[2])
        cvar = n[3]
        if cvar:
            self.ctx.decl.add(cvar)
        cbody = self.stmt(n[4]) if n[4] is not None else None
        fbody = self.stmt(n[5]) if n[5] is not None else None

        def run(f):
            ctl = None
            try:
                try:
                    ctl = body(f)
                except GMError as e:
                    if cbody is None:
                        raise
                    if cvar:
                        if e.__class__ is GMThrow:
                            f.loc[cvar] = e.value
                        else:
                            s = GMStruct()
                            s.vars["message"] = e.message
                            s.vars["longMessage"] = str(e)
                            s.vars["script"] = e.entry or ""
                            s.vars["line"] = e.line if e.line is not None else 0
                            s.vars["stacktrace"] = GMArray(list(e.stack))
                            s.vars["kind"] = e.kind
                            f.loc[cvar] = s
                    ctl = cbody(f)
            finally:
                if fbody is not None:
                    c2 = fbody(f)
                    if c2:
                        return c2
            return ctl
        return run

    # ---- assignment
    def s_assign(self, n):
        op, target, rhs_n = n[2], n[3], n[4]
        rhs = self.expr(rhs_n)
        if op is None:
            st = self.make_store(target)

            def run(f):
                st(f, rhs)
            return run
        if target[0] == "id" and target[2] in self.ctx.decl and op in ("+", "-"):
            name = target[2]
            add = op == "+"
            slow = ops.BINOPS[op]

            def runl(f):
                loc = f.loc
                try:
                    old = loc[name]
                except KeyError:
                    raise err_local_unset(f.sim, name)
                r = rhs(f)
                oc = old.__class__
                rc = r.__class__
                if (oc is int or oc is float) and (rc is int or rc is float):
                    loc[name] = old + r if add else old - r
                else:
                    loc[name] = slow(old, r)
            return runl
        upd = self.make_update(target)
        if op == "??":
            def comp(f, old):
                return old if old is not None else rhs(f)
        else:
            fn = ops.BINOPS[op]

            def comp(f, old):
                return fn(old, rhs(f))

        def run(f):
            upd(f, comp)
        return run

    # ------------------------------------------------------------ store / update machinery
    def ident_setter(self, name):
        if name in self.ctx.decl:
            def set_local(f, v):
                f.loc[name] = v
            return set_local
        if name in self.ctx.statics:
            def set_static(f, v):
                f.statics[name] = v
            return set_static

        def set_self(f, v):
            gv = f.sim.globalvars
            if gv and name in gv:
                f.sim.globals[name] = v
            else:
                f.self.vars[name] = v
        return set_self

    def ident_reader(self, name):
        return self.x_id(("id", 0, name))

    def make_container_w(self, node):
        """Return closure f -> writable GMArray stored at `node` (auto-creating)."""
        k = node[0]
        if k == "paren":
            return self.make_container_w(node[2])
        if k == "id":
            name = node[2]
            if name == "argument":
                return lambda f: GMArray(f.args)
            if name in self.ctx.decl:
                def w_local(f):
                    loc = f.loc
                    cur = loc.get(name, MISS)
                    if cur.__class__ is GMArray:
                        if cur.cow:
                            cur = cur.copy()
                            loc[name] = cur
                        return cur
                    if cur is MISS or cur is None or cur.__class__ in _NUMW:
                        cur = loc[name] = GMArray()
                        return cur
                    raise not_array(cur)
                return w_local
            if name in self.ctx.statics:
                def w_static(f):
                    d = f.statics
                    cur = d.get(name, MISS)
                    if cur.__class__ is GMArray:
                        if cur.cow:
                            cur = cur.copy()
                            d[name] = cur
                        return cur
                    if cur is MISS or cur is None or cur.__class__ in _NUMW:
                        cur = d[name] = GMArray()
                        return cur
                    raise not_array(cur)
                return w_static

            def w_self(f):
                d = f.self.vars
                gv = f.sim.globalvars
                if gv and name in gv:
                    d = f.sim.globals
                cur = d.get(name, MISS)
                if cur.__class__ is GMArray:
                    if cur.cow:
                        cur = cur.copy()
                        d[name] = cur
                    return cur
                if cur is MISS or cur is None or cur.__class__ in _NUMW:
                    cur = d[name] = GMArray()
                    return cur
                raise not_array(cur)
            return w_self
        if k == "mem":
            name = node[3]
            oc = self.expr(node[2])

            def w_mem(f):
                d = vars_of(f, oc(f))
                cur = d.get(name, MISS)
                if cur.__class__ is GMArray:
                    if cur.cow:
                        cur = cur.copy()
                        d[name] = cur
                    return cur
                if cur is MISS or cur is None or cur.__class__ in _NUMW:
                    cur = d[name] = GMArray()
                    return cur
                raise not_array(cur)
            return w_mem
        if k == "idx":
            kind = node[4]
            idxs = node[3]
            if kind in ("", "@"):
                inner = self.container_chain(node[2], idxs)
                return inner
        ec = self.expr(node)

        def w_expr(f):
            v = ec(f)
            if v.__class__ is GMArray:
                return v
            raise not_array(v)
        return w_expr

    def container_chain(self, base, idxs):
        """Writable array for base[i0][i1]..., all but the last write step."""
        cw = self.make_container_w(base)
        ics = [self.expr(i) for i in idxs]
        if len(ics) == 1:
            ic = ics[0]

            def w1(f):
                return elem_for_write(cw(f), ic(f))
            return w1

        def wn(f):
            a = cw(f)
            for ic in ics:
                a = elem_for_write(a, ic(f))
            return a
        return wn

    def split_idx(self, node):
        """For idx target with plain accessor: (container_w closure, last index closure)."""
        base, idxs = node[2], node[3]
        ics = [self.expr(i) for i in idxs]
        last = ics[-1]
        if len(idxs) == 1:
            cw = self.make_container_w(base)
        else:
            cw = self.container_chain(base, idxs[:-1])
        return cw, last

    def make_store(self, target):
        k = target[0]
        if k == "id":
            name = target[2]
            if name in self.ctx.decl:
                def st_local(f, rhs):
                    v = rhs(f)
                    if v.__class__ is GMArray:
                        v.cow = True
                    f.loc[name] = v
                return st_local
            setter = self.ident_setter(name)

            def st_id(f, rhs):
                v = rhs(f)
                if v.__class__ is GMArray:
                    v.cow = True
                setter(f, v)
            return st_id
        if k == "mem":
            name = target[3]
            on = target[2]
            if on[0] == "id" and on[2] == "global":
                def st_global(f, rhs):
                    v = rhs(f)
                    if v.__class__ is GMArray:
                        v.cow = True
                    if name in f.sim.scripts:
                        raise err_global_is_function(name)
                    f.sim.globals[name] = v
                return st_global
            if on[0] == "id" and on[2] == "self":
                def st_self(f, rhs):
                    v = rhs(f)
                    if v.__class__ is GMArray:
                        v.cow = True
                    f.self.vars[name] = v
                return st_self
            oc = self.expr(on)

            def st_mem(f, rhs):
                o = oc(f)
                v = rhs(f)
                if v.__class__ is GMArray:
                    v.cow = True
                set_field(f, o, name, v)
            return st_mem
        if k == "idx":
            kind = target[4]
            if kind in ("", "@"):
                cw, ic = self.split_idx(target)

                def st_idx(f, rhs):
                    arr = cw(f)
                    i = ic(f)
                    v = rhs(f)
                    if v.__class__ is GMArray:
                        v.cow = True
                    if i.__class__ is not int:
                        i = to_index(i)
                    d = arr.data
                    if 0 <= i < len(d):
                        d[i] = v
                    else:
                        array_set(arr, i, v)
                return st_idx
            cc = self.expr(target[2])
            ics = [self.expr(i) for i in target[3]]

            def st_ds(f, rhs):
                c = cc(f)
                idx = [ic(f) for ic in ics]
                v = rhs(f)
                if v.__class__ is GMArray:
                    v.cow = True
                ds_set(f, kind, c, idx, v)
            return st_ds
        raise GMError("invalid assignment target", "parse")

    def make_update(self, target):
        """Return upd(f, comp) -> (old, new); comp(f, old) -> new."""
        k = target[0]
        if k == "id":
            rd = self.ident_reader(target[2])
            setter = self.ident_setter(target[2])

            def up_id(f, comp):
                old = rd(f)
                new = comp(f, old)
                setter(f, new)
                return old, new
            return up_id
        if k == "mem":
            name = target[3]
            on = target[2]
            if on[0] == "id" and on[2] == "global":
                def up_global(f, comp):
                    g = f.sim.globals
                    if name in f.sim.scripts:
                        raise err_global_is_function(name)
                    try:
                        old = g[name]
                    except KeyError:
                        raise err_global_unset(f.sim, name)
                    new = comp(f, old)
                    g[name] = new
                    return old, new
                return up_global
            oc = self.expr(on)

            def up_mem(f, comp):
                o = oc(f)
                old = get_field(f, o, name)
                new = comp(f, old)
                set_field(f, o, name, new)
                return old, new
            return up_mem
        if k == "idx":
            kind = target[4]
            if kind in ("", "@"):
                cw, ic = self.split_idx(target)

                def up_idx(f, comp):
                    arr = cw(f)
                    i = ic(f)
                    old = array_get(arr, i)
                    new = comp(f, old)
                    array_set(arr, i, new)
                    return old, new
                return up_idx
            cc = self.expr(target[2])
            ics = [self.expr(i) for i in target[3]]

            def up_ds(f, comp):
                c = cc(f)
                idx = [ic(f) for ic in ics]
                old = ds_get(f, kind, c, idx)
                new = comp(f, old)
                ds_set(f, kind, c, idx, new)
                return old, new
            return up_ds
        raise GMError("invalid update target", "parse")

    # ------------------------------------------------------------ expressions
    def expr(self, n):
        return getattr(self, "x_" + n[0])(n)

    def x_const(self, n):
        v = n[2]
        return lambda f: v

    def x_paren(self, n):
        return self.expr(n[2])

    def x_tstr(self, n):
        parts = [(p if p.__class__ is str else self.expr(p)) for p in n[2]]

        def run(f):
            out = []
            for p in parts:
                out.append(p if p.__class__ is str else gml_str(p(f)))
            return "".join(out)
        return run

    def x_id(self, n):
        name = n[2]
        if name == "self":
            def rself(f):
                s = f.self
                return s.id if s.__class__ is GMInstance else s
            return rself
        if name == "other":
            def rother(f):
                o = f.other
                if o is None:
                    o = f.self
                    if o is None:
                        return -4
                return o.id if o.__class__ is GMInstance else o
            return rother
        if name == "global":
            return lambda f: GLOBAL_REF
        if name == "noone":
            return lambda f: -4
        if name == "all":
            return lambda f: -3
        if name == "argument_count":
            return lambda f: len(f.args)
        m = _ARG_RE.match(name)
        if m:
            ai = int(m.group(1))
            return lambda f: f.args[ai] if ai < len(f.args) else None
        if name in self.ctx.decl:
            def rlocal(f):
                try:
                    return f.loc[name]
                except KeyError:
                    raise err_local_unset(f.sim, name)
            return rlocal
        if name in self.ctx.statics:
            return lambda f: f.statics[name]

        def rself2(f):
            try:
                v = f.self.vars[name]
            except KeyError:
                return f.sim.lookup_name(name, f)
            # GameMaker 2.3+ compiles a bare name that is a global function to the FUNCTION (push.i [function]) even where the
            # instance has a variable of that name - the game never reads the variable there (sim.fn_shadow_check: say so)
            sim = f.sim
            fs = sim.fn_shadow_check
            if fs and ((fs is not True and name in fs) or name in sim.script_entries or name in sim.scripts):
                raise GMError("variable %s is read here, but %s is also a global function: the compiled game reads the FUNCTION "
                              "(a reference, about 100000 as a number) - rename the variable" % (name, name), "fn_shadow")
            return v
        return rself2

    def x_arr(self, n):
        items = [self.expr(i) for i in n[2]]

        def run(f):
            d = [i(f) for i in items]
            for x in d:
                if x.__class__ is GMArray:
                    x.cow = True
            return GMArray(d)
        return run

    def x_struct(self, n):
        fields = []
        for key, e in n[2]:
            if e[0] == "func":
                fields.append((key, None, self.compile_function(e[2], key)))
            else:
                fields.append((key, self.expr(e), None))

        def run(f):
            s = GMStruct()
            d = s.vars
            for key, c, fn in fields:
                if fn is not None:
                    d[key] = GMMethod(fn, s)
                else:
                    v = c(f)
                    if v.__class__ is GMArray:
                        v.cow = True
                    d[key] = v
            return s
        return run

    def x_func(self, n):
        fn = self.compile_function(n[2], n[2].name)

        def run(f):
            return GMMethod(fn, f.self)
        return run

    def x_un(self, n):
        op = n[2]
        a = self.expr(n[3])
        if op == "-":
            def neg(f):
                v = a(f)
                c = v.__class__
                if c is int or c is float:
                    return -v
                return -ops.num(v, "operand of unary -")
            return neg
        if op == "!":
            def lnot(f):
                v = a(f)
                if v is True:
                    return False
                if v is False:
                    return True
                return not truth(v)
            return lnot
        if op == "~":
            return lambda f: ops.bnot(a(f))
        return lambda f: ops.num(a(f), "operand of unary +")

    def x_log(self, n):
        op = n[2]
        a = self.expr(n[3])
        b = self.expr(n[4])
        if op == "&&":
            def land(f):
                x = a(f)
                if x is not True and (x is False or not truth(x)):
                    return False
                y = b(f)
                return y is True or (y is not False and truth(y))
            return land
        if op == "||":
            def lor(f):
                x = a(f)
                if x is True or (x is not False and truth(x)):
                    return True
                y = b(f)
                return y is True or (y is not False and truth(y))
            return lor
        return lambda f: truth(a(f)) != truth(b(f))

    def x_coal(self, n):
        a = self.expr(n[2])
        b = self.expr(n[3])

        def run(f):
            v = a(f)
            return v if v is not None else b(f)
        return run

    def x_tern(self, n):
        c = self.expr(n[2])
        a = self.expr(n[3])
        b = self.expr(n[4])

        def run(f):
            v = c(f)
            if v is True or (v is not False and truth(v)):
                return a(f)
            return b(f)
        return run

    def x_bin(self, n):
        op = n[2]
        a = self.expr(n[3])
        b = self.expr(n[4])
        slow = ops.BINOPS[op]
        if op == "+":
            def add(f):
                x = a(f)
                y = b(f)
                tx = x.__class__
                ty = y.__class__
                if (tx is int or tx is float) and (ty is int or ty is float):
                    return x + y
                return slow(x, y)
            return add
        if op == "-":
            def sub(f):
                x = a(f)
                y = b(f)
                tx = x.__class__
                ty = y.__class__
                if (tx is int or tx is float) and (ty is int or ty is float):
                    return x - y
                return slow(x, y)
            return sub
        if op == "*":
            def mul(f):
                x = a(f)
                y = b(f)
                tx = x.__class__
                ty = y.__class__
                if (tx is int or tx is float) and (ty is int or ty is float):
                    return x * y
                return slow(x, y)
            return mul
        if op == "==":
            def eq(f):
                x = a(f)
                y = b(f)
                if x == y:
                    return True
                if x.__class__ is float or y.__class__ is float:
                    return slow(x, y)
                if x.__class__ is GMInstance or y.__class__ is GMInstance:
                    return slow(x, y)
                return False
            return eq
        if op == "!=":
            def ne(f):
                x = a(f)
                y = b(f)
                if x == y:
                    return False
                if x.__class__ is float or y.__class__ is float:
                    return not slow_eq(x, y)
                if x.__class__ is GMInstance or y.__class__ is GMInstance:
                    return not slow_eq(x, y)
                return True
            slow_eq = ops.eq
            return ne
        if op in ("<", ">", "<=", ">="):
            import operator
            pyop = {"<": operator.lt, ">": operator.gt, "<=": operator.le, ">=": operator.ge}[op]

            # (two ints: exact; a real on either side: within GameMaker's epsilon - ops.lt and the rest)
            def cmp(f):
                x = a(f)
                y = b(f)
                tx = x.__class__
                ty = y.__class__
                if tx is int and ty is int:
                    return pyop(x, y)
                if (tx is int or tx is float) and (ty is int or ty is float):
                    d = x - y
                    if -1e-5 < d < 1e-5:
                        return eq_res
                    return pyop(x, y)
                return slow(x, y)
            eq_res = op in ("<=", ">=")
            return cmp
        return lambda f: slow(a(f), b(f))

    def x_inc(self, n):
        target, d, prefix = n[2], n[3], n[4]
        if target[0] == "id" and target[2] in self.ctx.decl:
            name = target[2]

            def inc_local(f):
                loc = f.loc
                try:
                    v = loc[name]
                except KeyError:
                    raise err_local_unset(f.sim, name)
                c = v.__class__
                nv = v + d if (c is int or c is float) else ops.num(v, "operand of ++/--") + d
                loc[name] = nv
                return nv if prefix else v
            return inc_local
        upd = self.make_update(target)

        def comp(f, old):
            return ops.num(old, "operand of ++/--") + d

        def run(f):
            old, new = upd(f, comp)
            return new if prefix else old
        return run

    def x_mem(self, n):
        name = n[3]
        on = n[2]
        if on[0] == "id":
            if on[2] == "global":
                def rglobal(f):
                    try:
                        return f.sim.globals[name]
                    except KeyError:
                        if name in f.sim.scripts:
                            raise err_global_is_function(name)
                        raise err_global_unset(f.sim, name)
                return rglobal
            if on[2] == "self":
                def rself(f):
                    s = f.self
                    try:
                        return s.vars[name]
                    except KeyError:
                        return get_field(f, s, name)
                return rself
        oc = self.expr(on)

        def rmem(f):
            o = oc(f)
            if o.__class__ is GMStruct or o.__class__ is GMInstance:
                try:
                    return o.vars[name]
                except KeyError:
                    pass
            return get_field(f, o, name)
        return rmem

    def x_idx(self, n):
        kind = n[4]
        base = n[2]
        idxs = n[3]
        if kind in ("", "@"):
            if len(idxs) > 1:   # legacy a[i,j] == a[i][j]
                inner = ("idx", n[1], base, idxs[:-1], kind)
                return self.x_idx(("idx", n[1], inner, idxs[-1:], kind))
            ic = self.expr(idxs[0])
            if base[0] == "id" and base[2] == "argument":
                def rarg(f):
                    i = to_index(ic(f))
                    if 0 <= i < len(f.args):
                        return f.args[i]
                    return None
                return rarg
            bc = self.expr(base)

            def ridx(f):
                a = bc(f)
                i = ic(f)
                if a.__class__ is GMArray:
                    d = a.data
                    if i.__class__ is not int:
                        i = to_index(i)
                    if 0 <= i < len(d):
                        return d[i]
                    raise err_oor_n(i, len(d))
                raise not_array(a)
            return ridx
        bc = self.expr(base)
        ics = [self.expr(i) for i in idxs]

        def rds(f):
            return ds_get(f, kind, bc(f), [ic(f) for ic in ics])
        return rds

    def x_new(self, n):
        name = n[2]
        args = [self.expr(a) for a in n[3]]

        def run(f):
            av = [a(f) for a in args]
            fn = f.sim.get_callable(name, f)
            if fn.__class__ is GMMethod:
                fn = fn.func
            if fn.__class__ is not GMFunc:
                raise GMError("Unable to construct %s: not a constructor" % name, "not_callable")
            if not fn.ctor:
                raise GMError("Function %s is not a constructor (missing 'constructor' keyword)" % name, "type")
            s = GMStruct(ctor=fn)
            call_ctor(f.sim, fn, av, s, f.ev)
            return s
        return run

    def x_call(self, n):
        callee = n[2]
        argcs = [self.expr(a) for a in n[3]]
        nargs = len(argcs)
        if callee[0] == "id":
            return self.call_ident(callee[2], argcs, nargs)
        if callee[0] == "mem":
            name = callee[3]
            on = callee[2]
            oc = self.expr(on)
            is_global = on[0] == "id" and on[2] == "global"

            def call_mem(f):
                o = oc(f)
                fv = get_field(f, o, name)
                args = [a(f) for a in argcs]
                if is_global:
                    return call_value(f, fv, args)
                t = o.__class__
                if t is not GMStruct and t is not GMInstance:
                    o = resolve_instance(f, int(o)) if t in (int, float, bool) else o
                return call_value(f, fv, args, o)
            return call_mem
        cc = self.expr(callee)

        def call_expr(f):
            fv = cc(f)
            return call_value(f, fv, [a(f) for a in argcs])
        return call_expr

    def call_ident(self, name, argcs, nargs):
        local = name in self.ctx.decl
        entry = self.entry
        if local:
            def call_local(f):
                try:
                    fv = f.loc[name]
                except KeyError:
                    raise err_local_unset(f.sim, name)
                return call_value(f, fv, [a(f) for a in argcs])
            return call_local
        a0 = argcs[0] if nargs > 0 else None
        a1 = argcs[1] if nargs > 1 else None

        def call(f):
            if nargs == 1:
                args = [a0(f)]
            elif nargs == 0:
                args = []
            elif nargs == 2:
                args = [a0(f), a1(f)]
            else:
                args = [a(f) for a in argcs]
            sim = f.sim
            v = f.self.vars.get(name, MISS)
            if v is not MISS and (v.__class__ is GMMethod or v.__class__ is GMFunc):
                return call_value(f, v, args)
            fn = sim.scripts.get(name)
            if fn is not None:
                return call_func(sim, fn, args, f.self, f.other, f.ev)
            ent = sim.builtins.get(name)
            if ent is not None:
                if _rt.PROF is not None:
                    t0 = _rt.prof_enter()
                    try:
                        if ent[1]:
                            return ent[0](sim, f, *args)
                        return ent[0](sim, *args)
                    except _CALL_ERRORS as e:
                        raise GMError("%s(): %s: %s" % (name, e.__class__.__name__, e), "builtin_args") from e
                    finally:
                        if _rt.PROF is not None:
                            _rt.prof_leave("B:" + name, t0)
                try:
                    if ent[1]:
                        return ent[0](sim, f, *args)
                    return ent[0](sim, *args)
                except _CALL_ERRORS as e:
                    raise GMError("%s(): %s: %s" % (name, e.__class__.__name__, e), "builtin_args") from e
            return sim.call_unresolved(name, f, args)
        return call


def err_oor_n(i, n):
    return GMError("Array index out of range: index [%d] not in [0..%d)" % (i, n), "array_oob")


# ----------------------------------------------------------------------------- cache

_CACHE = {}
_EXPR_CACHE = {}


def compile_code(entry, src, is_script=False):
    key = (entry, src, is_script)
    c = _CACHE.get(key)
    if c is None:
        ast = parse(src, entry)
        c = Compiler(entry, is_script).compile_program(ast)
        _CACHE[key] = c
    return c


def compile_expression(src):
    c = _EXPR_CACHE.get(src)
    if c is None:
        c = Compiler("<expr>").expr(parse_expression(src))
        _EXPR_CACHE[src] = c
    return c
