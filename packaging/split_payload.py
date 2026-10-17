#!/usr/bin/env python3
"""DRBR: a payload folder in pieces of at most --max bytes (for copying through channels with a file size limit).
DRBR-Setup.exe joins the pieces (name.part0, name.part1, ...) itself when it finds a "payload" folder next to it.
Usage: split_payload.py <payload dir> <out dir> [--max 24000000]"""
import os, shutil, sys

src, out = sys.argv[1], sys.argv[2]
mx = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else 24000000
if os.path.isdir(out):
    shutil.rmtree(out)
os.makedirs(out)
n = 0
for name in sorted(os.listdir(src)):
    p = os.path.join(src, name)
    if not os.path.isfile(p):
        continue
    size = os.path.getsize(p)
    if size <= mx:
        shutil.copyfile(p, os.path.join(out, name))
        n += 1
        continue
    with open(p, 'rb') as f:
        i = 0
        while True:
            b = f.read(mx)
            if not b:
                break
            open(os.path.join(out, '%s.part%d' % (name, i)), 'wb').write(b)
            i += 1
            n += 1
print('%s -> %s: %d files (largest %d bytes)' % (src, out, n, max(os.path.getsize(os.path.join(out, x)) for x in os.listdir(out))))
