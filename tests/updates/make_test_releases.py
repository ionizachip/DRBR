#!/usr/bin/env python3
"""DRBR update tests: from a real payload, newer releases served by range_server.py:
  good/     1.0.1, correctly signed, one file changed (the update must download only that one)
  badsig/   1.0.2, its manifest signed by another key (must be refused)
  corrupt/  1.0.2, correctly signed, but the changed file on the server is damaged (must be refused)
Usage: make_test_releases.py <payload dir> <out dir> <private key> <base url>"""
import json, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'packaging'))
import release_tools as rt

payload, out, key, base = sys.argv[1:5]
if os.path.isdir(out):
    shutil.rmtree(out)
os.makedirs(out)
other = os.path.join(out, 'other-key.pem')
subprocess.run(['openssl', 'genpkey', '-algorithm', 'RSA', '-pkeyopt', 'rsa_keygen_bits:3072', '-out', other], check=True, capture_output=True)


def make(kind, ver, doc_text, sign_key, damage=False):
    d = os.path.join(out, kind)
    os.makedirs(d)
    m = json.load(open(os.path.join(payload, 'payload.json')))
    m['version'] = ver
    m['notes'] = 'DRBR %s (test release): the README changed.' % ver
    for f in m['files']:
        src = os.path.join(payload, f['file'])
        dst = os.path.join(d, f['file'])
        if f['kind'] == 'doc':
            open(dst, 'wb').write(doc_text.encode())
            f['sha256'] = rt.sha256(dst)
            f['size'] = os.path.getsize(dst)
            if damage:
                data = bytearray(open(dst, 'rb').read())
                data[10] ^= 0x55
                os.remove(dst)
                open(dst, 'wb').write(bytes(data))
            continue
        try:
            os.link(src, dst)
        except OSError:
            shutil.copyfile(src, dst)
    m['base_url'] = base.rstrip('/') + '/' + kind + '/'
    b = json.dumps(m, indent=2).encode()
    open(os.path.join(d, 'update-manifest.json'), 'wb').write(b)
    open(os.path.join(d, 'update-manifest.json.sig'), 'w').write(rt.sign_bytes(b, sign_key))


make('good', '1.0.1', '# DRBR 1.0.1\n\nThis README changed in the test release.\n' * 60, key)
make('badsig', '1.0.2', '# DRBR 1.0.2 (bad signature)\n' * 60, other)
make('corrupt', '1.0.2', '# DRBR 1.0.2 (damaged on the server)\n' * 60, key, damage=True)
print('test releases in', out)
