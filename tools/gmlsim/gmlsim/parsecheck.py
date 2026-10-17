"""Parse (and compile) every .gml in the given directories and report failures.

    python3 -m gmlsim.parsecheck DIR [DIR...] [--no-compile]
"""
import collections
import os
import sys
import time

from .compiler import Compiler
from .errors import GMError
from .parser import parse


def check_dir(d, compile_=True, verbose=True):
    n = 0
    lines = 0
    fails = []
    cfails = []
    t_parse = t_comp = 0.0
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".gml"):
            continue
        n += 1
        with open(os.path.join(d, fn), encoding="utf-8", errors="replace") as fh:
            src = fh.read()
        lines += src.count("\n") + 1
        t = time.time()
        try:
            ast = parse(src, fn[:-4])
        except GMError as e:
            fails.append((fn, str(e)))
            t_parse += time.time() - t
            continue
        t_parse += time.time() - t
        if compile_:
            t = time.time()
            try:
                Compiler(fn[:-4], fn.startswith("gml_GlobalScript_")).compile_program(ast)
            except Exception as e:  # noqa
                cfails.append((fn, "%s: %s" % (e.__class__.__name__, e)))
            t_comp += time.time() - t
    if verbose:
        print("%s: %d files, %d lines | parse failures: %d | compile failures: %d | parse %.1fs compile %.1fs"
              % (d, n, lines, len(fails), len(cfails), t_parse, t_comp))
        for fn, msg in (fails + cfails)[:20]:
            print("   FAIL", fn, msg)
    return n, lines, fails, cfails


def main(argv):
    dirs = [a for a in argv if not a.startswith("--")]
    if not dirs:
        print(__doc__)
        return 2
    bad = 0
    tot = [0, 0]
    for d in dirs:
        n, lines, f, c = check_dir(d, "--no-compile" not in argv)
        tot[0] += n
        tot[1] += lines
        bad += len(f) + len(c)
    print("TOTAL: %d files, %d lines, %d failures => %.2f%% parse+compile coverage" %
          (tot[0], tot[1], bad, 100.0 * (tot[0] - bad) / max(1, tot[0])))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
