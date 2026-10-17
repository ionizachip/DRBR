"""Regex-driven GML lexer. Produces parallel lists (kinds, values, lines, positions)."""
import re

from .errors import GMParseError

KEYWORDS = frozenset("""var globalvar if else for while do until repeat switch case default break continue
return exit with function constructor new static enum try catch finally throw delete then""".split())

# word operators map to symbolic ones
WORD_OPS = {"and": "&&", "or": "||", "xor": "^^", "not": "!", "mod": "%", "div": "div"}

_TOKEN_RE = re.compile(r"""
 (?P<ws>[ \t\r\f\v﻿]+)
|(?P<nl>\n)
|(?P<lc>//[^\n]*)
|(?P<bc>/\*.*?\*/)
|(?P<macro>\#macro[ \t]+[^\n]*(?:\\\r?\n[^\n]*)*)
|(?P<region>\#(?:end)?region[^\n]*|\#define[^\n]*)
|(?P<color>\#[0-9A-Fa-f]{6}\b)
|(?P<hex>(?:\$|0[xX])[0-9A-Fa-f]+)
|(?P<num>(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?)
|(?P<vstr>@"[^"]*"|@'[^']*')
|(?P<tstr>\$"(?:[^"\\]|\\.)*")
|(?P<str>"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')
|(?P<id>[A-Za-z_][A-Za-z_0-9]*)
|(?P<op>\[(?:\||\?|@|\$(?![0-9A-Fa-f]+\s*\])|\#(?![0-9A-Fa-f]{6}\b))|<<=|>>=|\?\?=|\.\.\.|===|!==|==|!=|<>|<=|>=|&&|\|\||\^\^|\+\+|--|\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<|>>|\?\?|:=|[-+*/%&|^~!<>=?:;,.(){}\[\]])
""", re.VERBOSE | re.DOTALL)

_ESC = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'", "0": "\0",
        "a": "\a", "b": "\b", "f": "\f", "v": "\v"}
_ESC_RE = re.compile(r"\\(x[0-9A-Fa-f]{2}|u[0-9A-Fa-f]{4}|.)", re.DOTALL)


def _unesc(m):
    g = m.group(1)
    if len(g) > 1:
        return chr(int(g[1:], 16))
    return _ESC.get(g, "\\" + g)


def unescape(body):
    if "\\" not in body:
        return body
    return _ESC_RE.sub(_unesc, body)


def line_col(src, pos):
    line = src.count("\n", 0, pos) + 1
    col = pos - (src.rfind("\n", 0, pos) + 1) + 1
    return line, col


def tokenize(src, entry="<src>"):
    """Return (kinds, values, lines, poss). kinds: num str id kw op macro eof."""
    kinds, vals, lines, poss = [], [], [], []
    ka, va, la, pa = kinds.append, vals.append, lines.append, poss.append
    pos = 0
    line = 1
    n = len(src)
    match = _TOKEN_RE.match
    while pos < n:
        m = match(src, pos)
        if m is None:
            ln, col = line_col(src, pos)
            raise GMParseError("unexpected character %r" % src[pos], entry, ln, col)
        g = m.lastgroup
        text = m.group()
        end = m.end()
        if g == "ws" or g == "lc" or g == "region":
            pass
        elif g == "nl":
            line += 1
        elif g == "bc":
            line += text.count("\n")
        elif g == "id":
            if text in KEYWORDS:
                ka("kw"); va(text)
            elif text in WORD_OPS:
                ka("op"); va(WORD_OPS[text])
            else:
                ka("id"); va(text)
            la(line); pa(pos)
        elif g == "op":
            if text == "<>":
                text = "!="
            elif text == ":=":
                text = "="
            elif text == "===":
                text = "=="
            elif text == "!==":
                text = "!="
            ka("op"); va(text); la(line); pa(pos)
        elif g == "num":
            ka("num"); va(float(text) if ("." in text or "e" in text or "E" in text) else int(text))
            la(line); pa(pos)
        elif g == "hex":
            ka("num"); va(int(text.replace("$", "").replace("0x", "").replace("0X", ""), 16)); la(line); pa(pos)
        elif g == "color":
            h = text[1:]
            r, gg, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            ka("num"); va((b << 16) | (gg << 8) | r); la(line); pa(pos)
        elif g == "str":
            ka("str"); va(unescape(text[1:-1])); la(line); pa(pos)
            line += text.count("\n")
        elif g == "vstr":
            ka("str"); va(text[2:-1]); la(line); pa(pos)
            line += text.count("\n")
        elif g == "tstr":
            ka("tstr"); va(text[2:-1]); la(line); pa(pos)
            line += text.count("\n")
        elif g == "macro":
            ka("macro"); va(text); la(line); pa(pos)
            line += text.count("\n")
        pos = end
    ka("eof"); va("<eof>"); la(line); pa(n)
    return kinds, vals, lines, poss
