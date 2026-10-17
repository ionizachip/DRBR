#!/usr/bin/env python3
"""DRBR release tools.

  sign      <file> --key <private key .pem>            -> <file>.sig (RSA PKCS#1 v1.5 SHA-256, base64)
  verify    <file>                                       checks <file>.sig against drbr.json's public key
  setup     --exe <DRBR-Setup.exe built> --payload <dir> --out <DRBR-Setup.exe with the payload appended>
  release   --payload <dir> --setup <DRBR-Setup.exe> --out <release dir> --key <private key> [--base-url URL] [--full]
            -> every payload file as a release asset, update-manifest.json(.sig), DRBR-Setup.exe, RELEASE_NOTES.md,
               SHA256SUMS.txt; --full adds DRBR-Setup-X.exe and DRBR-FullPatch-X.zip (copies of the same files)
  check     <release dir>                                validates a release dir completely (signature, every checksum,
                                                         the Setup's appended payload)
The private key is never in the repository: pass it with --key or DRBR_SIGNING_KEY_FILE (GitHub Actions: the
DRBR_SIGNING_KEY secret).
"""
import argparse, base64, hashlib, io, json, os, shutil, struct, subprocess, sys, tempfile, zipfile

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


def cmd_check(a):
    d = a.dir
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
    s = sub.add_parser('check'); s.add_argument('dir')
    a = ap.parse_args()
    {'sign': cmd_sign, 'verify': cmd_verify, 'setup': cmd_setup, 'release': cmd_release, 'check': cmd_check}[a.cmd](a)


if __name__ == '__main__':
    main()
