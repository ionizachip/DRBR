#!/usr/bin/env python3
"""DRBR release tools.

  sign      <file> --key <private key .pem>            -> <file>.sig (RSA PKCS#1 v1.5 SHA-256, base64)
  verify    <file>                                       checks <file>.sig against drbr.json's public key
  setup     --exe <DRBR-Setup.exe built> --payload <dir> --out <DRBR-Setup.exe with the payload appended>
  package   --payload <dir> --setup <DRBR-Setup.exe> --out <DRBR.zip> --key <private key> [--base-url URL]
            -> THE release: one file, DRBR.zip (stored, not compressed): DRBR-Setup.exe (the whole package appended),
               README.txt, update/update-manifest.json and its .sig last. The launcher reads only the zip's end (the
               manifest) and then just the bytes of the files that changed. RELEASE_NOTES.md is written next to it.
  release   --payload <dir> --setup <DRBR-Setup.exe> --out <release dir> --key <private key> [--base-url URL] [--full]
            -> (DRBR 1.0.0's layout) every payload file as a release asset, update-manifest.json(.sig), DRBR-Setup.exe,
               RELEASE_NOTES.md, SHA256SUMS.txt
  check     <release dir | DRBR.zip>                     validates a release completely (signature, every checksum,
                                                         the Setup's appended payload; for DRBR.zip: read the way the
                                                         launcher reads it)
The private key is never in the repository: pass it with --key or DRBR_SIGNING_KEY_FILE (GitHub Actions: the
DRBR_SIGNING_KEY secret).
"""
import argparse, base64, hashlib, io, json, os, shutil, struct, subprocess, sys, tempfile, zipfile, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAGIC = b'DRBRPAY1'


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def key_path(a):
    k = getattr(a, 'key', None) or os.environ.get('DRBR_SIGNING_KEY_FILE')
    if not k and os.environ.get('DRBR_SIGNING_KEY'):
        fd, k = tempfile.mkstemp(suffix='.pem')
        os.write(fd, os.environ['DRBR_SIGNING_KEY'].encode())
        os.close(fd)
    if not k or not os.path.exists(k):
        sys.exit('No signing key: use --key <file>, DRBR_SIGNING_KEY_FILE or DRBR_SIGNING_KEY. (It is never stored in the repository.)')
    return k


def sign_bytes(data, key):
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    pk = serialization.load_pem_private_key(open(key, 'rb').read(), password=None)
    return base64.b64encode(pk.sign(data, padding.PKCS1v15(), hashes.SHA256())).decode()


def public_key():
    from cryptography.hazmat.primitives.asymmetric import rsa
    cfg = json.load(open(os.path.join(ROOT, 'drbr.json')))
    n = int.from_bytes(base64.b64decode(cfg['public_key']['modulus_b64']), 'big')
    e = int.from_bytes(base64.b64decode(cfg['public_key']['exponent_b64']), 'big')
    return rsa.RSAPublicNumbers(e, n).public_key()


def verify_bytes(data, sig_b64):
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    try:
        public_key().verify(base64.b64decode(sig_b64), data, padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception:
        return False


def cmd_sign(a):
    data = open(a.file, 'rb').read()
    open(a.file + '.sig', 'w').write(sign_bytes(data, key_path(a)))
    print('signed', a.file)


def cmd_verify(a):
    ok = verify_bytes(open(a.file, 'rb').read(), open(a.file + '.sig').read().strip())
    print('signature', 'OK' if ok else 'BAD', a.file)
    sys.exit(0 if ok else 1)


def zip_dir(src):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_STORED, allowZip64=True) as z:
        for n in sorted(os.listdir(src)):
            p = os.path.join(src, n)
            if os.path.isfile(p):
                z.write(p, n)
    return buf.getvalue()


def cmd_setup(a):
    exe = open(a.exe, 'rb').read()
    if exe[-8:] == MAGIC:
        sys.exit('That Setup already has a payload appended (use the plain build).')
    z = zip_dir(a.payload)
    with open(a.out, 'wb') as o:
        o.write(exe)
        o.write(z)
        o.write(struct.pack('<q', len(z)))
        o.write(MAGIC)
    print('DRBR-Setup: %s (%.1f MB: program %.0f KB + package %.1f MB)' % (a.out, os.path.getsize(a.out) / 1048576, len(exe) / 1024, len(z) / 1048576))


def appended_payload(setup):
    with open(setup, 'rb') as f:
        f.seek(-16, 2)
        tail = f.read(16)
        if tail[8:] != MAGIC:
            return None
        n = struct.unpack('<q', tail[:8])[0]
        f.seek(-16 - n, 2)
        return zipfile.ZipFile(io.BytesIO(f.read(n)))


def cmd_release(a):
    payload = json.load(open(os.path.join(a.payload, 'payload.json')))
    ver = payload['version']
    cfg = json.load(open(os.path.join(ROOT, 'drbr.json')))
    base = a.base_url or cfg['release_download_base'].replace('{owner}', cfg['github']['owner']).replace('{repo}', cfg['github']['repo']).replace('{version}', ver)
    if os.path.isdir(a.out):
        shutil.rmtree(a.out)
    os.makedirs(a.out)
    for f in payload['files']:
        shutil.copyfile(os.path.join(a.payload, f['file']), os.path.join(a.out, f['file']))
    manifest = dict(payload)
    manifest['base_url'] = base
    mb = json.dumps(manifest, indent=2).encode()
    open(os.path.join(a.out, 'update-manifest.json'), 'wb').write(mb)
    open(os.path.join(a.out, 'update-manifest.json.sig'), 'w').write(sign_bytes(mb, key_path(a)))
    shutil.copyfile(a.setup, os.path.join(a.out, 'DRBR-Setup.exe'))
    if a.full:
        shutil.copyfile(a.setup, os.path.join(a.out, 'DRBR-Setup-%s.exe' % ver))
        # the full package for a manual install (the same files as the Setup carries)
        with zipfile.ZipFile(os.path.join(a.out, 'DRBR-FullPatch-%s.zip' % ver), 'w', zipfile.ZIP_STORED, allowZip64=True) as z:
            for n in sorted(os.listdir(a.payload)):
                z.write(os.path.join(a.payload, n), n)
    notes = payload.get('notes') or ''
    open(os.path.join(a.out, 'RELEASE_NOTES.md'), 'w', encoding='utf8').write('# DRBR %s\n\n%s\n' % (ver, notes))
    with open(os.path.join(a.out, 'SHA256SUMS.txt'), 'w') as s:
        for n in sorted(os.listdir(a.out)):
            if n != 'SHA256SUMS.txt':
                s.write('%s  %s\n' % (sha256(os.path.join(a.out, n)), n))
    print('release %s -> %s (%d assets)' % (ver, a.out, len(os.listdir(a.out))))


PACKAGE = 'DRBR.zip'

README = """DRBR - DELTARUNE BATTLE ROYALE {ver}
=========================================

1. Extract this zip (or open it) and run DRBR-Setup.exe.
   It finds your DELTARUNE (Steam) and installs DRBR in a folder of its own:
   your DELTARUNE, its files and its saves are not changed.
2. Play with "DRBR Launcher" (desktop or Start menu). It keeps DRBR up to date by itself.

You need DELTARUNE (Steam, Chapter 3). DRBR ships no DELTARUNE files: it patches a copy of your own.
The "update" folder is what the launcher reads to update DRBR - nothing to do with it.

DRBR is a fan mod by ionizachip. DELTARUNE (c) Toby Fox. Not affiliated with Toby Fox.
"""


def release_manifest(payload_dir, base_url):
    payload = json.load(open(os.path.join(payload_dir, 'payload.json')))
    ver = payload['version']
    cfg = json.load(open(os.path.join(ROOT, 'drbr.json')))
    base = base_url or cfg['release_download_base'].replace('{owner}', cfg['github']['owner']).replace('{repo}', cfg['github']['repo']).replace('{version}', ver)
    m = dict(payload)
    m['base_url'] = base
    m['package'] = PACKAGE
    return m


def cmd_package(a):
    m = release_manifest(a.payload, a.base_url)
    ver = m['version']
    inner = appended_payload(a.setup)
    if inner is None:
        sys.exit('That DRBR-Setup.exe has no package appended (make it with: release_tools.py setup ...).')
    carried = json.loads(inner.read('payload.json'))
    if carried['version'] != ver or carried['drbr_data_win'] != m['drbr_data_win'] or carried['files'] != m['files']:
        sys.exit('That DRBR-Setup.exe carries another release than the payload (%s).' % carried['version'])
    mb = json.dumps(m, indent=2).encode()
    sig = sign_bytes(mb, key_path(a)).encode()
    out = a.out
    if os.path.exists(out):
        os.remove(out)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    # stored, in this order: the launcher reads the manifest and its signature from the end of the file
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_STORED, allowZip64=True) as z:
        z.write(a.setup, 'DRBR-Setup.exe')
        z.writestr(zipfile.ZipInfo('README.txt', date_time=(2026, 1, 1, 0, 0, 0)), README.format(ver=ver).replace('\n', '\r\n'))
        z.writestr(zipfile.ZipInfo('update/update-manifest.json', date_time=(2026, 1, 1, 0, 0, 0)), mb)
        z.writestr(zipfile.ZipInfo('update/update-manifest.json.sig', date_time=(2026, 1, 1, 0, 0, 0)), sig)
    notes = m.get('notes') or ''
    open(os.path.join(os.path.dirname(os.path.abspath(out)), 'RELEASE_NOTES.md'), 'w', encoding='utf8').write('# DRBR %s\n\n%s\n' % (ver, notes))
    print('release %s -> %s (%.1f MB)' % (ver, out, os.path.getsize(out) / 1048576))


# ---------- reading DRBR.zip the way the launcher does (Package.cs): the zip's end, then byte ranges ----------
def zip_entries(read, length):
    """[(name, method, csize, size, header offset)] of a zip seen through read(offset, n)"""
    tl = min(length, 22 + 65535 + 20)
    tail = read(length - tl, tl)
    e = -1
    for i in range(tl - 22, -1, -1):
        if tail[i:i + 4] == b'PK\x05\x06' and i + 22 + struct.unpack('<H', tail[i + 20:i + 22])[0] == tl:
            e = i
            break
    if e < 0:
        raise ValueError('no end record')
    count, cdsize, cdoff = struct.unpack('<H', tail[e + 10:e + 12])[0], struct.unpack('<I', tail[e + 12:e + 16])[0], struct.unpack('<I', tail[e + 16:e + 20])[0]
    if count == 0xFFFF or cdsize == 0xFFFFFFFF or cdoff == 0xFFFFFFFF:
        assert tail[e - 20:e - 16] == b'PK\x06\x07', 'no ZIP64 locator'
        e64 = struct.unpack('<Q', tail[e - 12:e - 4])[0]
        r = read(e64, 56)
        assert r[:4] == b'PK\x06\x06'
        count, cdsize, cdoff = struct.unpack('<QQQ', r[32:56])
    cd = read(cdoff, cdsize)
    out, p = [], 0
    for _ in range(count):
        assert cd[p:p + 4] == b'PK\x01\x02', 'damaged directory'
        method, = struct.unpack('<H', cd[p + 10:p + 12])
        csize, size = struct.unpack('<II', cd[p + 20:p + 28])
        n, m_, c = struct.unpack('<HHH', cd[p + 28:p + 34])
        off, = struct.unpack('<I', cd[p + 42:p + 46])
        name = cd[p + 46:p + 46 + n].decode('utf8').replace('\\', '/')
        x = p + 46 + n
        while x + 4 <= p + 46 + n + m_:
            xid, xs = struct.unpack('<HH', cd[x:x + 4])
            if xid == 1:
                q = x + 4
                for attr in ('size', 'csize', 'off'):
                    if {'size': size, 'csize': csize, 'off': off}[attr] == 0xFFFFFFFF:
                        v, = struct.unpack('<Q', cd[q:q + 8]); q += 8
                        if attr == 'size': size = v
                        elif attr == 'csize': csize = v
                        else: off = v
            x += 4 + xs
        out.append((name, method, csize, size, off))
        p += 46 + n + m_ + c
    return out


def data_offset(read, off):
    h = read(off, 30)
    assert h[:4] == b'PK\x03\x04', 'damaged local header'
    n, m_ = struct.unpack('<HH', h[26:30])
    return off + 30 + n + m_


def package_view(path):
    """what the launcher sees in DRBR.zip: (manifest bytes, signature, {payload file: (offset, size)} or None)"""
    f = open(path, 'rb')
    length = os.path.getsize(path)
    reads = [0]

    def read(o, n):
        reads[0] += 1
        f.seek(o)
        b = f.read(n)
        assert len(b) == n, 'short read'
        return b
    ents = {e[0].split('/')[-1] if e[0].endswith(('update-manifest.json', 'update-manifest.json.sig', 'DRBR-Setup.exe')) else e[0]: e for e in zip_entries(read, length)}
    def small(e):
        raw = read(data_offset(read, e[4]), e[2])
        return raw if e[1] == 0 else zlib.decompress(raw, -15)
    mb = small(ents['update-manifest.json'])
    sig = small(ents['update-manifest.json.sig']).decode().strip()
    st = ents['DRBR-Setup.exe']
    files = None
    if st[1] == 0:
        exe0 = data_offset(read, st[4])
        exelen = st[2]
        t = read(exe0 + exelen - 16, 16)
        assert t[8:] == MAGIC, 'no payload appended to DRBR-Setup.exe'
        n, = struct.unpack('<q', t[:8])
        inner0 = exe0 + exelen - 16 - n
        iread = lambda o, k: read(inner0 + o, k)
        files = {}
        for name, method, csize, size, off in zip_entries(iread, n):
            assert method == 0, name + ' is compressed inside the package'
            files[name] = (inner0 + data_offset(iread, off), size)
    f.close()
    return mb, sig, files, reads[0]


def check_package(path):
    bad = []
    mb, sig, files, nreads = package_view(path)
    if not verify_bytes(mb, sig):
        bad.append('update-manifest.json: signature does not verify with drbr.json\'s public key')
    m = json.loads(mb)
    if m.get('package') != os.path.basename(path):
        bad.append('the manifest names the package %r, the file is %r' % (m.get('package'), os.path.basename(path)))
    if files is None:
        bad.append('DRBR-Setup.exe is compressed inside the zip (the launcher would have to download it whole)')
    else:
        with open(path, 'rb') as f:
            for e in m['files']:
                if e['file'] not in files:
                    bad.append(e['file'] + ': not in the package')
                    continue
                off, size = files[e['file']]
                f.seek(off)
                h = hashlib.sha256()
                left = size
                while left:
                    b = f.read(min(left, 1 << 20)); h.update(b); left -= len(b)
                if size != e['size'] or h.hexdigest() != e['sha256']:
                    bad.append(e['file'] + ': size / checksum mismatch at its place in the package')
        # the same through Python's zipfile (a normal unzip): the Setup inside, its payload
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            if names[-2:] != ['update/update-manifest.json', 'update/update-manifest.json.sig']:
                bad.append('the manifest and its signature are not the last entries: %r' % names)
            if any(i.compress_type != zipfile.ZIP_STORED for i in z.infolist()):
                bad.append('an entry is compressed (DRBR.zip has to be stored)')
    for b in bad:
        print('FAIL', b)
    print('package check: %s (%s, %d files, the launcher\'s way: %d reads)' % ('OK' if not bad else 'FAILED', m['version'], len(m['files']), nreads))
    sys.exit(1 if bad else 0)


def cmd_check(a):
    d = a.dir
    if os.path.isfile(d) and d.lower().endswith('.zip'):
        return check_package(d)
    bad = []
    mb = open(os.path.join(d, 'update-manifest.json'), 'rb').read()
    if not verify_bytes(mb, open(os.path.join(d, 'update-manifest.json.sig')).read().strip()):
        bad.append('update-manifest.json: signature does not verify with drbr.json\'s public key')
    m = json.loads(mb)
    for f in m['files']:
        p = os.path.join(d, f['file'])
        if not os.path.exists(p):
            bad.append(f['file'] + ': missing')
        elif os.path.getsize(p) != f['size'] or sha256(p) != f['sha256']:
            bad.append(f['file'] + ': size / checksum mismatch')
    for name in ('DRBR-Setup.exe', 'DRBR-Setup-%s.exe' % m['version']):
        p = os.path.join(d, name)
        if name != 'DRBR-Setup.exe' and not os.path.exists(p):
            continue   # the versioned copy is optional (release --full)
        z = appended_payload(p) if os.path.exists(p) else None
        if z is None:
            bad.append(name + ': no payload appended')
            continue
        inner = json.loads(z.read('payload.json'))
        for f in inner['files']:
            if hashlib.sha256(z.read(f['file'])).hexdigest() != f['sha256']:
                bad.append(name + ': ' + f['file'] + ' damaged inside')
        if inner['version'] != m['version'] or inner['drbr_data_win'] != m['drbr_data_win']:
            bad.append(name + ': carries a different release than update-manifest.json')
    if os.path.exists(os.path.join(d, 'SHA256SUMS.txt')):
        for line in open(os.path.join(d, 'SHA256SUMS.txt')):
            h, n = line.strip().split('  ', 1)
            if sha256(os.path.join(d, n)) != h:
                bad.append('SHA256SUMS.txt: ' + n + ' differs')
    for b in bad:
        print('FAIL', b)
    print('release check: %s (%s, %d files)' % ('OK' if not bad else 'FAILED', m['version'], len(m['files'])))
    sys.exit(1 if bad else 0)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('sign'); s.add_argument('file'); s.add_argument('--key')
    s = sub.add_parser('verify'); s.add_argument('file')
    s = sub.add_parser('setup'); s.add_argument('--exe', required=True); s.add_argument('--payload', required=True); s.add_argument('--out', required=True)
    s = sub.add_parser('release'); s.add_argument('--payload', required=True); s.add_argument('--setup', required=True); s.add_argument('--out', required=True)
    s.add_argument('--key'); s.add_argument('--base-url'); s.add_argument('--full', action='store_true')
    s = sub.add_parser('package'); s.add_argument('--payload', required=True); s.add_argument('--setup', required=True); s.add_argument('--out', required=True)
    s.add_argument('--key'); s.add_argument('--base-url')
    s = sub.add_parser('check'); s.add_argument('dir')
    a = ap.parse_args()
    {'sign': cmd_sign, 'verify': cmd_verify, 'setup': cmd_setup, 'release': cmd_release, 'package': cmd_package, 'check': cmd_check}[a.cmd](a)


if __name__ == '__main__':
    main()
