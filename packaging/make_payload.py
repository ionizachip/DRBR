#!/usr/bin/env python3
"""DRBR: the release payload - every file a DRBR install is made of, and payload.json listing them with checksums.

Input: a Knight Hub game package made by the mod build (KNIGHT_HUB_MANIFEST.txt, the xdelta parts, the music zips, the Steam
files, xdelta3.exe), the built DRBR programs, the provided starting save (save-profile/starting-save/start_filech3).
The game patch is the binary difference from the player's own vanilla Chapter 3 data.win: no DELTARUNE file is shipped.

Usage: make_payload.py --pkg <game package dir> --apps <dir with DRBR Launcher.exe / DRBR Updater.exe> --out <dir>
                       [--version X.Y.Z] [--notes CHANGELOG.md] [--no-music]
  --notes     release notes: from a changelog, only the "## <version>" section is taken
  --no-music  leave out the mod's fight songs (third-party works: see docs/RELEASING.md). Those fights then play the
              game's own music; the installer and the game handle that.
"""
import argparse, hashlib, json, os, shutil, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def read_kh_manifest(p):
    kv, music, steam, parts = {}, [], [], []
    for line in open(p, encoding='utf8'):
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        if k == 'music':
            rel, h = v.split('|')
            music.append({'rel': rel, 'sha256': h})
        elif k == 'steam':
            n, h = v.split('|')
            steam.append((n, h))
        elif k.startswith('part.'):
            n, size, h = v.split('|')
            parts.append((int(k[5:]), n, int(size), h))
        else:
            kv[k] = v
    parts.sort()
    return kv, music, steam, parts


def release_notes(path, version):
    """the notes for this version: a changelog's "## <version>" section (up to the next "## "), else the whole file"""
    if not path or not os.path.exists(path):
        return ''
    text = open(path, encoding='utf8').read()
    out, on = [], False
    for line in text.splitlines():
        if line.startswith('## '):
            if on:
                break
            on = line[3:].strip().lstrip('[v').split(']')[0].split(' ')[0] == version
            continue
        if on:
            out.append(line)
    return '\n'.join(out).strip() if out else text.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pkg', required=True)
    ap.add_argument('--apps', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--version')
    ap.add_argument('--notes')
    ap.add_argument('--no-music', action='store_true')
    a = ap.parse_args()
    cfg = json.load(open(os.path.join(ROOT, 'drbr.json')))
    version = a.version or cfg['version']
    kv, music, steam, parts = read_kh_manifest(os.path.join(a.pkg, 'KNIGHT_HUB_MANIFEST.txt'))
    if os.path.isdir(a.out):
        shutil.rmtree(a.out)
    os.makedirs(a.out)
    files = []

    def add(src, name, kind, dest='', expect=None, **extra):
        dst = os.path.join(a.out, name)
        if src != dst:
            shutil.copyfile(src, dst)
        h = sha256(dst)
        if expect and h != expect:
            sys.exit('FAILED: %s does not match its expected checksum' % name)
        e = {'file': name, 'kind': kind, 'size': os.path.getsize(dst), 'sha256': h}
        if dest:
            e['dest'] = dest
        e.update(extra)
        files.append(e)
        return e

    # 1. the game patch: the parts joined back into one file and checked against the mod build's own checksum
    patch = os.path.join(a.out, 'drbr-chapter3.xdelta')
    with open(patch, 'wb') as o:
        for _, n, size, h in parts:
            pp = os.path.join(a.pkg, n)
            if os.path.getsize(pp) != size or sha256(pp) != h:
                sys.exit('FAILED: patch part %s is damaged' % n)
            with open(pp, 'rb') as f:
                shutil.copyfileobj(f, o, 1 << 20)
    if sha256(patch) != kv['xdelta_sha256'] or os.path.getsize(patch) != int(kv['xdelta_size']):
        sys.exit('FAILED: the joined patch does not match the mod build manifest')
    add(patch, 'drbr-chapter3.xdelta', 'patch')
    # 2. the mod's Steam files (multiplayer), the patch tool
    for n, h in steam:
        add(os.path.join(a.pkg, n), n, 'copy', 'game/chapter3_windows/' + n, expect=h)
    add(os.path.join(a.pkg, 'xdelta3.exe'), 'xdelta3.exe', 'tool', 'tools/xdelta3.exe', expect=kv.get('xdelta3_exe_sha256'))
    # 3. the music (each song's checksum is in payload.json's "music")
    zips = [('knight_hub_extras.zip', 'drbr-music-0.zip'), ('knight_hub_music.zip', 'drbr-music-1.zip'), ('knight_hub_music2.zip', 'drbr-music-2.zip'),
            ('knight_hub_music3.zip', 'drbr-music-3.zip'), ('knight_hub_music4.zip', 'drbr-music-4.zip')]
    if a.no_music:
        music = []
    for src, name in ([] if a.no_music else zips):
        if os.path.exists(os.path.join(a.pkg, src)):
            add(os.path.join(a.pkg, src), name, 'music_zip')
    if not a.no_music and os.path.exists(os.path.join(a.pkg, 'knight_hub_kfsongs.zip')):
        add(os.path.join(a.pkg, 'knight_hub_kfsongs.zip'), 'drbr-kfsongs.zip', 'kfsongs_zip')
    # 4. the provided starting save, byte for byte
    tpl = os.path.join(ROOT, 'save-profile', 'starting-save', 'start_filech3')
    tdata = open(tpl, 'rb').read()
    sp = cfg['save_profile']
    tentry = add(tpl, 'start_filech3', 'template')
    # 5. the programs
    lv = cfg['launcher_version']
    add(os.path.join(a.apps, 'DRBR Launcher.exe'), 'DRBR-Launcher.exe', 'app', 'DRBR Launcher.exe', version=lv)
    add(os.path.join(a.apps, 'DRBR Updater.exe'), 'DRBR-Updater.exe', 'app', 'DRBR Updater.exe', version=lv)
    # 6. the player-facing docs
    for d in ('README.md', 'docs/INSTALLATION.md', 'docs/SAVE_SYSTEM.md', 'docs/TROUBLESHOOTING.md', 'docs/UPDATING.md'):
        p = os.path.join(ROOT, d)
        if os.path.exists(p):
            add(p, 'doc-' + os.path.basename(d), 'doc', 'docs/' + os.path.basename(d))

    notes = release_notes(a.notes, version)
    payload = {
        'schema': 1,
        'product': 'DRBR',
        'version': version,
        'mod_build': cfg['mod_build'],
        'protocol': cfg['protocol'],
        'launcher_version': lv,
        'min_launcher_version': cfg['min_launcher_version'],
        'released': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'notes': notes,
        'supported_game_builds': cfg['supported_game_builds'],
        'drbr_data_win': {'size': int(kv['patched_size']), 'sha256': kv['patched_sha256']},
        'files': files,
        'music': music,
        'save_profile': {
            'schema_version': sp['schema_version'], 'profile': sp['profile'], 'save_template_version': sp['save_template_version'],
            'migration_version': sp['migration_version'], 'starting_location': sp['starting_location'],
            'starting_room_id': sp['starting_room_id'], 'starting_plot': sp['starting_plot'],
            'template': {'file': 'start_filech3', 'size': len(tdata), 'sha256': tentry['sha256'], 'sha1': hashlib.sha1(tdata).hexdigest()},
        },
    }
    # the vanilla build the patch was made from must be one drbr.json supports
    if not any(b['sha256'] == kv['vanilla_sha256'] and b['size'] == int(kv['vanilla_size']) for b in cfg['supported_game_builds']):
        sys.exit('FAILED: the game package was built from a vanilla data.win that drbr.json does not list')
    json.dump(payload, open(os.path.join(a.out, 'payload.json'), 'w'), indent=2)
    total = sum(f['size'] for f in files)
    print('payload %s: %d files, %.1f MB -> %s' % (version, len(files), total / 1048576, a.out))


if __name__ == '__main__':
    main()
