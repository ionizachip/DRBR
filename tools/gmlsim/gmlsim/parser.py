"""Hand-written recursive-descent / precedence-climbing GML parser.

AST nodes are tuples: (kind, line, ...). See the node table in the README.
"""
import re

from .errors import GMParseError
from .lexer import tokenize, line_col, unescape

BINPREC = {
    "??": 1, "||": 2, "&&": 3, "^^": 4, "==": 5, "!=": 5,
    "<": 6, "<=": 6, ">": 6, ">=": 6, "|": 7, "^": 8, "&": 9,
    "<<": 10, ">>": 10, "+": 11, "-": 11, "*": 12, "/": 12, "div": 12, "%": 12,
}
ASSIGN_OPS = {"=": None, "+=": "+", "-=": "-", "*=": "*", "/=": "/", "%=": "%",
              "&=": "&", "|=": "|", "^=": "^", "??=": "??"}
CONST_IDS = {"true": True, "false": False, "undefined": None}


class FuncDef:
    __slots__ = ("name", "params", "body", "ctor", "parent", "line")

    def __init__(self, name, params, body, ctor, parent, line):
        self.name = name
        self.params = params          # [(name, default_expr_or_None)]
        self.body = body              # ('block', ...) node
        self.ctor = ctor
        self.parent = parent          # (name, [args]) or None
        self.line = line


class Parser:
    def __init__(self, src, entry="<src>"):
        self.src = src
        self.entry = entry
        self.k, self.v, self.ln, self.ps = tokenize(src, entry)
        self.i = 0

    # ------------------------------------------------------------ helpers
    def err(self, msg, i=None):
        i = self.i if i is None else i
        line, col = line_col(self.src, self.ps[i])
        got = self.v[i]
        raise GMParseError("%s (got %r)" % (msg, got), self.entry, line, col)

    def is_op(self, s):
        return self.k[self.i] == "op" and self.v[self.i] == s

    def is_kw(self, s):
        return self.k[self.i] == "kw" and self.v[self.i] == s

    def eat_op(self, s):
        if self.k[self.i] == "op" and self.v[self.i] == s:
            self.i += 1
            return True
        return False

    def eat_kw(self, s):
        if self.k[self.i] == "kw" and self.v[self.i] == s:
            self.i += 1
            return True
        return False

    def expect_op(self, s):
        if self.k[self.i] == "op" and self.v[self.i] == s:
            self.i += 1
            return
        self.err("expected %r" % s)

    def expect_kw(self, s):
        if not self.eat_kw(s):
            self.err("expected keyword %r" % s)

    def ident(self):
        if self.k[self.i] == "id":
            self.i += 1
            return self.v[self.i - 1]
        self.err("expected identifier")

    # ------------------------------------------------------------ program
    def parse_program(self):
        stmts = []
        while self.k[self.i] != "eof":
            s = self.statement()
            if s is not None:
                stmts.append(s)
        return ("block", 1, stmts)

    def block_until_close(self):
        stmts = []
        while not self.is_op("}"):
            if self.k[self.i] == "eof":
                self.err("unexpected end of file, missing '}'")
            s = self.statement()
            if s is not None:
                stmts.append(s)
        self.i += 1
        return stmts

    def end_stmt(self):
        while self.eat_op(";"):
            pass

    # ------------------------------------------------------------ statements
    def statement(self):
        k = self.k[self.i]
        v = self.v[self.i]
        ln = self.ln[self.i]
        if k == "op":
            if v == "{":
                self.i += 1
                return ("block", ln, self.block_until_close())
            if v == ";":
                self.i += 1
                return None
        elif k == "kw":
            m = getattr(self, "st_" + v, None)
            if m is not None:
                self.i += 1
                return m(ln)
        elif k == "macro":
            self.i += 1
            return self.macro(v, ln)
        s = self.simple_statement(ln)
        self.end_stmt()
        return s

    def sub_statement(self):
        s = self.statement()
        return s if s is not None else ("block", self.ln[self.i - 1], [])

    def macro(self, text, ln):
        body = text[len("#macro"):].strip()
        body = re.sub(r"\\\r?\n", " ", body)
        m = re.match(r"([A-Za-z_][A-Za-z_0-9]*)\s*(.*)$", body, re.DOTALL)
        if not m:
            self.err("bad #macro")
        txt = re.sub(r"//.*$", "", m.group(2)).strip()
        return ("macro", ln, m.group(1), txt)

    def simple_statement(self, ln):
        e = self.expression_postfix_unary()
        k = self.k[self.i]
        v = self.v[self.i]
        if k == "op" and v in ASSIGN_OPS:
            self.check_lvalue(e)
            self.i += 1
            rhs = self.expression()
            return ("assign", ln, ASSIGN_OPS[v], e, rhs)
        if k == "op" and (v == "++" or v == "--"):
            pass  # handled inside postfix
        # expression continues? (e.g. a call followed by binary op is meaningless but tolerate)
        if k == "op" and v in BINPREC or (k == "op" and v == "?"):
            e = self.continue_expression(e)
        return ("expr", ln, e)

    def check_lvalue(self, e):
        if e[0] not in ("id", "mem", "idx"):
            self.err("invalid assignment target", self.i - 1 if self.i else 0)

    def st_var(self, ln):
        decls = []
        while True:
            name = self.ident()
            init = None
            if self.eat_op("="):
                init = self.expression()
            decls.append((name, init))
            if not self.eat_op(","):
                break
        self.end_stmt()
        return ("var", ln, decls)

    def st_globalvar(self, ln):
        names = [self.ident()]
        while self.eat_op(","):
            names.append(self.ident())
        self.end_stmt()
        return ("gvar", ln, names)

    def st_static(self, ln):
        name = self.ident()
        init = None
        if self.eat_op("="):
            init = self.expression()
        self.end_stmt()
        return ("static", ln, name, init)

    def paren_expr(self):
        if self.is_op("("):
            self.i += 1
            e = self.expression()
            self.expect_op(")")
            return e
        return self.expression()

    def st_if(self, ln):
        cond = self.paren_expr()
        self.eat_kw("then")
        then = self.sub_statement()
        els = None
        if self.eat_kw("else"):
            els = self.sub_statement()
        return ("if", ln, cond, then, els)

    def st_while(self, ln):
        cond = self.paren_expr()
        return ("while", ln, cond, self.sub_statement())

    def st_do(self, ln):
        body = self.sub_statement()
        self.expect_kw("until")
        cond = self.paren_expr()
        self.end_stmt()
        return ("do", ln, body, cond)

    def st_repeat(self, ln):
        n = self.paren_expr()
        return ("repeat", ln, n, self.sub_statement())

    def st_for(self, ln):
        self.expect_op("(")
        init = None
        if not self.is_op(";"):
            init = self.for_clause()
        self.expect_op(";")
        cond = None
        if not self.is_op(";"):
            cond = self.expression()
        self.expect_op(";")
        step = None
        if not self.is_op(")"):
            step = self.for_clause()
        self.expect_op(")")
        return ("for", ln, init, cond, step, self.sub_statement())

    def for_clause(self):
        ln = self.ln[self.i]
        if self.is_kw("var"):
            self.i += 1
            return self.st_var_noterm(ln)
        return self.simple_statement(ln)

    def st_var_noterm(self, ln):
        decls = []
        while True:
            name = self.ident()
            init = None
            if self.eat_op("="):
                init = self.expression()
            decls.append((name, init))
            if not self.eat_op(","):
                break
        return ("var", ln, decls)

    def st_switch(self, ln):
        e = self.paren_expr()
        self.expect_op("{")
        cases = []
        cur = None
        while not self.is_op("}"):
            if self.eat_kw("case"):
                ce = self.expression()
                self.expect_op(":")
                cur = (ce, [])
                cases.append(cur)
            elif self.eat_kw("default"):
                self.expect_op(":")
                cur = (None, [])
                cases.append(cur)
            else:
                if cur is None:
                    self.err("statement before first case in switch")
                if self.k[self.i] == "eof":
                    self.err("unexpected end of file in switch")
                s = self.statement()
                if s is not None:
                    cur[1].append(s)
        self.i += 1
        return ("switch", ln, e, cases)

    def st_with(self, ln):
        e = self.paren_expr()
        return ("with", ln, e, self.sub_statement())

    def st_break(self, ln):
        self.end_stmt()
        return ("break", ln)

    def st_continue(self, ln):
        self.end_stmt()
        return ("continue", ln)

    def st_exit(self, ln):
        self.end_stmt()
        return ("exit", ln)

    def st_return(self, ln):
        e = None
        if not (self.is_op(";") or self.is_op("}") or self.k[self.i] == "eof"
                or (self.k[self.i] == "kw" and self.v[self.i] in ("else", "case", "default"))):
            e = self.expression()
        self.end_stmt()
        return ("return", ln, e)

    def st_throw(self, ln):
        e = self.expression()
        self.end_stmt()
        return ("throw", ln, e)

    def st_delete(self, ln):
        e = self.expression()
        self.end_stmt()
        return ("delete", ln, e)

    def st_try(self, ln):
        self.expect_op("{")
        body = ("block", ln, self.block_until_close())
        cvar = None
        cbody = None
        fbody = None
        if self.eat_kw("catch"):
            if self.eat_op("("):
                cvar = self.ident()
                self.expect_op(")")
            self.expect_op("{")
            cbody = ("block", ln, self.block_until_close())
        if self.eat_kw("finally"):
            self.expect_op("{")
            fbody = ("block", ln, self.block_until_close())
        if cbody is None and fbody is None:
            self.err("try without catch or finally")
        return ("try", ln, body, cvar, cbody, fbody)

    def st_enum(self, ln):
        name = self.ident()
        self.expect_op("{")
        members = []
        while not self.is_op("}"):
            mname = self.ident()
            val = None
            if self.eat_op("="):
                val = self.expression()
            members.append((mname, val))
            if not self.eat_op(","):
                break
        self.expect_op("}")
        self.end_stmt()
        return ("enum", ln, name, members)

    def st_function(self, ln):
        # statement-level: either declaration `function name(...)` or an expression statement
        if self.k[self.i] == "id":
            fd = self.function_rest(ln, named=True)
            return ("fdecl", ln, fd)
        self.i -= 1  # let expression parser handle anonymous function expression
        s = self.simple_statement(ln)
        self.end_stmt()
        return s

    def st_new(self, ln):
        self.i -= 1
        s = self.simple_statement(ln)
        self.end_stmt()
        return s

    # kw statements that cannot start a statement
    def st_else(self, ln):
        self.i -= 1
        self.err("unexpected 'else'")

    # ------------------------------------------------------------ functions
    def function_rest(self, ln, named):
        name = None
        if named and self.k[self.i] == "id":
            name = self.ident()
        self.expect_op("(")
        params = []
        while not self.is_op(")"):
            pname = self.ident()
            d = None
            if self.eat_op("="):
                d = self.expression()
            params.append((pname, d))
            if not self.eat_op(","):
                break
        self.expect_op(")")
        parent = None
        if self.eat_op(":"):
            pname = self.ident()
            self.expect_op("(")
            pargs = self.call_args()
            parent = (pname, pargs)
        ctor = self.eat_kw("constructor")
        self.expect_op("{")
        body = ("block", ln, self.block_until_close())
        return FuncDef(name, params, body, ctor, parent, ln)

    # ------------------------------------------------------------ expressions
    def expression(self):
        c = self.binary(1)
        if self.is_op("?"):
            ln = self.ln[self.i]
            self.i += 1
            a = self.expression()
            self.expect_op(":")
            b = self.expression()
            return ("tern", ln, c, a, b)
        return c

    def continue_expression(self, left):
        """Continue parsing binary/ternary operators after an already-parsed unary operand."""
        e = self.binary(1, left)
        if self.is_op("?"):
            ln = self.ln[self.i]
            self.i += 1
            a = self.expression()
            self.expect_op(":")
            b = self.expression()
            return ("tern", ln, e, a, b)
        return e

    def binary(self, minprec, left=None):
        if left is None:
            left = self.unary()
        k = self.k
        v = self.v
        while True:
            if k[self.i] != "op":
                return left
            op = v[self.i]
            p = BINPREC.get(op)
            if p is None or p < minprec:
                return left
            ln = self.ln[self.i]
            self.i += 1
            right = self.binary(p + 1)
            if op == "&&" or op == "||" or op == "^^":
                left = ("log", ln, op, left, right)
            elif op == "??":
                left = ("coal", ln, left, right)
            else:
                left = ("bin", ln, op, left, right)

    def unary(self):
        k = self.k[self.i]
        if k == "op":
            op = self.v[self.i]
            ln = self.ln[self.i]
            if op in ("!", "-", "+", "~"):
                self.i += 1
                e = self.unary()
                if op == "-" and e[0] == "const" and e[2].__class__ in (int, float):
                    return ("const", ln, -e[2])
                return ("un", ln, op, e)
            if op in ("++", "--"):
                self.i += 1
                e = self.unary()
                return ("inc", ln, e, 1 if op == "++" else -1, True)
        return self.expression_postfix_unary()

    def expression_postfix_unary(self):
        """primary + postfix chain (+ trailing ++/--); also handles prefix unary for statements."""
        k = self.k[self.i]
        if k == "op" and self.v[self.i] in ("++", "--", "!", "-", "+", "~"):
            return self.unary()
        e = self.primary()
        while True:
            if self.k[self.i] != "op":
                break
            op = self.v[self.i]
            ln = self.ln[self.i]
            if op == ".":
                self.i += 1
                name = self.v[self.i]
                if self.k[self.i] not in ("id", "kw"):
                    self.err("expected field name")
                self.i += 1
                e = ("mem", ln, e, name)
            elif op == "(":
                self.i += 1
                args = self.call_args()
                e = ("call", ln, e, args)
            elif op[0] == "[":
                self.i += 1
                kind = op[1:] if len(op) > 1 else ""
                idx = [self.expression()]
                while self.eat_op(","):
                    idx.append(self.expression())
                self.expect_op("]")
                e = ("idx", ln, e, idx, kind)
            elif op == "++" or op == "--":
                self.i += 1
                e = ("inc", ln, e, 1 if op == "++" else -1, False)
            else:
                break
        return e

    def call_args(self):
        args = []
        while not self.is_op(")"):
            args.append(self.expression())
            if not self.eat_op(","):
                break
        self.expect_op(")")
        return args

    def primary(self):
        k = self.k[self.i]
        v = self.v[self.i]
        ln = self.ln[self.i]
        if k == "num" or k == "str":
            self.i += 1
            return ("const", ln, v)
        if k == "id":
            self.i += 1
            if v in CONST_IDS:
                return ("const", ln, CONST_IDS[v])
            return ("id", ln, v)
        if k == "tstr":
            self.i += 1
            return self.template(v, ln)
        if k == "op":
            if v == "(":
                self.i += 1
                e = self.expression()
                self.expect_op(")")
                return ("paren", ln, e)
            if v == "[":
                self.i += 1
                items = []
                while not self.is_op("]"):
                    items.append(self.expression())
                    if not self.eat_op(","):
                        break
                self.expect_op("]")
                return ("arr", ln, items)
            if v == "{":
                self.i += 1
                fields = []
                while not self.is_op("}"):
                    if self.k[self.i] in ("id", "str", "kw"):
                        key = self.v[self.i]
                        self.i += 1
                    else:
                        self.err("expected struct field name")
                    self.expect_op(":")
                    fields.append((key, self.expression()))
                    if not self.eat_op(","):
                        break
                self.expect_op("}")
                return ("struct", ln, fields)
        if k == "kw":
            if v == "function":
                self.i += 1
                fd = self.function_rest(ln, named=False)
                return ("func", ln, fd)
            if v == "new":
                self.i += 1
                name = self.ident()
                self.expect_op("(")
                args = self.call_args()
                return ("new", ln, name, args)
        self.err("expected expression")

    def template(self, body, ln):
        parts = []
        i = 0
        buf = []
        n = len(body)
        while i < n:
            c = body[i]
            if c == "{":
                depth = 1
                j = i + 1
                while j < n and depth:
                    if body[j] == "{":
                        depth += 1
                    elif body[j] == "}":
                        depth -= 1
                    j += 1
                if buf:
                    parts.append(unescape("".join(buf)))
                    buf = []
                sub = Parser(body[i + 1:j - 1], self.entry)
                parts.append(sub.expression())
                i = j
            else:
                buf.append(c)
                i += 1
        if buf:
            parts.append(unescape("".join(buf)))
        return ("tstr", ln, parts)


def parse(src, entry="<src>"):
    return Parser(src, entry).parse_program()


def parse_expression(src, entry="<expr>"):
    p = Parser(src, entry)
    e = p.expression()
    if p.k[p.i] != "eof":
        p.err("unexpected trailing tokens")
    return e
