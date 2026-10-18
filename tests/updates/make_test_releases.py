#!/usr/bin/env python3
"""DRBR update tests: from a real payload, newer releases served by range_server.py - each one DRBR.zip, as published:
  good/DRBR.zip     +1 (1.0.1 from a 1.0.0 payload), correctly signed, one file changed (the update must read only that
                    file's bytes)
  rezip/DRBR.zip    +2, the same kind of release compressed again by hand (deflated): read by downloading it whole
  norange/DRBR.zip  +3, served by a server that ignores HTTP ranges (range_server.py: the norange/ folder)
  badsig/DRBR.zip   +4, its manifest signed by another key (must be refused)
  corrupt/DRBR.zip  +4, correctly signed, but the changed file inside it is damaged (must be refused)
  inuse/DRBR.zip    +5, a new DRBR Launcher.exe too: the running launcher cannot be replaced (Windows), so it waits for
                    DRBR Updater
  wrongtag/DRBR.zip +6, its signed manifest names another address (a release put up under another tag than its version):
                    the update reads the DRBR.zip the check read
  json/             +1 in DRBR 1.0.0's layout (update-manifest.json + .sig + every file): still understood
(+n: the payload's own version with n added to its last number - DRBR 1.0.1: they were fixed 1.0.1-1.0.5, so a 1.0.1
payload's "updates" were not newer than it; drbr-tests.dll counts the same way, TestVer)
The DRBR-Setup.exe inside each is a stand-in program with the real package appended (the launcher reads only the package).
Usage: make_test_releases.py <payload dir> <out dir> <private key> <base url>"""
import io, json, os, shutil, struct, subprocess, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'packaging'))
import release_tools as rt

payload, out, key, base = sys.argv[1:5]
if os.path.isdir(out):
    shutil.rmtree(out)
os.makedirs(out)
other = os.path.join(out, 'other-key.pem')
subprocess.run(['openssl', 'genpkey', '-algorithm', 'RSA', '-pkeyopt', 'rsa_keygen_bits:3072', '-out', other], check=True, capture_output=True)
work = os.path.join(out, '_work')
os.makedirs(work)


def release_files(kind, ver, doc_text, damage, launcher=False):
    """the release's payload folder: the real one, the docs changed (damage: the changed doc on disk differs from the manifest;
    launcher: DRBR Launcher.exe changed too - bytes after its end, as in a new build, and it still runs)"""
    d = os.path.join(work, kind)
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
        if launcher and f['kind'] == 'app' and f.get('dest') == 'DRBR Launcher.exe':
            open(dst, 'wb').write(open(src, 'rb').read() + ('DRBR-TEST-LAUNCHER-' + ver).encode())
            f['sha256'] = rt.sha256(dst)
            f['size'] = os.path.getsize(dst)
            continue
        try:
            os.link(src, dst)
        except OSError:
            shutil.copyfile(src, dst)
    open(os.path.join(d, 'payload.json'), 'w').write(json.dumps(m, indent=2))
    return d, m


def setup_with(d):
    """a stand-in DRBR-Setup.exe with the folder appended as its package (as release_tools.py setup does)"""
    z = rt.zip_dir(d)
    p = os.path.join(work, 'setup-%s.exe' % os.path.basename(d))
    with open(p, 'wb') as o:
        o.write(b'MZ' + b'\0' * 4094)
        o.write(z)
        o.write(struct.pack('<q', len(z)))
        o.write(rt.MAGIC)
    return p


def make(kind, ver, doc_text, sign_key, damage=False, rezip=False, folder=None, launcher=False, tag_folder=None):
    d, m = release_files(kind, ver, doc_text, damage, launcher)
    setup = setup_with(d)
    od = os.path.join(out, folder or kind)
    os.makedirs(od, exist_ok=True)
    zp = os.path.join(od, 'DRBR.zip')
    # (tag_folder: the release's own address as its signed manifest names it - another folder than where it is served: a release
    # put up under the wrong tag)
    m['base_url'] = base.rstrip('/') + '/' + (tag_folder or folder or kind) + '/'
    m['package'] = 'DRBR.zip'
    mb = json.dumps(m, indent=2).encode()
    sig = rt.sign_bytes(mb, sign_key).encode()
    comp = zipfile.ZIP_DEFLATED if rezip else zipfile.ZIP_STORED
    with zipfile.ZipFile(zp, 'w', comp, allowZip64=True) as z:
        # (a hand re-zip: a top folder, everything compressed)
        pre = 'DRBR/' if rezip else ''
        z.write(setup, pre + 'DRBR-Setup.exe')
        z.writestr(pre + 'README.txt', 'test')
        z.writestr(pre + 'update/update-manifest.json', mb)
        z.writestr(pre + 'update/update-manifest.json.sig', sig)
    print(kind, ver, os.path.getsize(zp), 'bytes')


def make_json(kind, ver, doc_text, sign_key):
    """DRBR 1.0.0's layout: every file a release asset of its own"""
    d, m = release_files(kind, ver, doc_text, False)
    od = os.path.join(out, kind)
    os.makedirs(od)
    for f in m['files']:
        shutil.copyfile(os.path.join(d, f['file']), os.path.join(od, f['file']))
    m['base_url'] = base.rstrip('/') + '/' + kind + '/'
    b = json.dumps(m, indent=2).encode()
    open(os.path.join(od, 'update-manifest.json'), 'wb').write(b)
    open(os.path.join(od, 'update-manifest.json.sig'), 'w').write(rt.sign_bytes(b, sign_key))


BASE = json.load(open(os.path.join(payload, 'payload.json')))['version']


def V(n):
    p = [int(x) for x in BASE.split('.')]
    p[-1] += n
    return '.'.join(str(x) for x in p)


make('good', V(1), ('# DRBR %s\n\nThis README changed in the test release.\n' % V(1)) * 60, key)
make('rezip', V(2), ('# DRBR %s (compressed again by hand)\n' % V(2)) * 60, key, rezip=True)
make('norange', V(3), ('# DRBR %s (no HTTP ranges on this server)\n' % V(3)) * 60, key)
make('badsig', V(4), ('# DRBR %s (bad signature)\n' % V(4)) * 60, other)
make('corrupt', V(4), ('# DRBR %s (damaged on the server)\n' % V(4)) * 60, key, damage=True)
make('inuse', V(5), ('# DRBR %s (a new launcher)\n' % V(5)) * 60, key, launcher=True)
# DRBR 1.0.2: put up under another tag than its version - its signed address (v-not-its-tag/) is not there
make('wrongtag', V(6), ('# DRBR %s (under the wrong tag)\n' % V(6)) * 60, key, tag_folder='v-not-its-tag')
make_json('json', V(1), ('# DRBR %s\n\nThis README changed in the test release.\n' % V(1)) * 60, key)
shutil.rmtree(work)
print('test releases in', out)
