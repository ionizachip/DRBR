#!/usr/bin/env python3
"""DRBR: checks a DELTARUNE Chapter 3 PC save the way DRBR does, and prints what is in it.
Default: the provided starting save (save-profile/starting-save/start_filech3) against drbr.json's save profile.
Usage: scripts/validate-save.py [save file] [--json]"""
import hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ROOMS = {30108: 'room_dw_snow_zone', 30191: 'room_dw_snow_zone_battle'}


def parse(data):
    lines = data.decode('latin-1').split('\r\n')
    if len(lines) != 3055:
        raise ValueError('not a Chapter 3 PC save: %d lines (3055 expected)' % len(lines))
    i = [0]

    def take(n=1):
        v = lines[i[0]:i[0] + n]
        i[0] += n
        return [x.strip() for x in v]
    s = {'truename': take()[0], 'othername': take(6), 'char': [int(x) for x in take(3)]}
    for k in ('gold', 'xp', 'lv', 'inv', 'invc', 'darkzone'):
        s[k] = float(take()[0])
    s['party_stats'] = []
    for c in range(5):
        st = dict(zip(('hp', 'maxhp', 'at', 'df', 'mag', 'guts', 'weapon', 'armor1', 'armor2', 'weaponstyle'), [float(x) for x in take(10)]))
        take(40)
        st['spells'] = [int(float(x)) for x in take(12) if x not in ('0', '')]
        s['party_stats'].append(st)
    take(3); take(26); take(96); take(72)
    s['tension'], s['maxtension'] = [float(x) for x in take(2)]
    take(11); take(16)
    flags = [float(x) for x in take(2500)]
    s['nonzero_flags'] = sum(1 for f in flags if f != 0)
    s['plot'], s['room_id'], s['time'] = int(float(take()[0])), int(float(take()[0])), float(take()[0])
    return s


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    path = args[0] if args else os.path.join(ROOT, 'save-profile', 'starting-save', 'start_filech3')
    cfg = json.load(open(os.path.join(ROOT, 'drbr.json')))
    sp = cfg['save_profile']
    data = open(path, 'rb').read()
    problems = []
    try:
        s = parse(data)
    except Exception as e:
        print('INVALID:', e)
        sys.exit(2)
    if s['room_id'] != sp['starting_room_id']:
        problems.append('room %d is not the starting room %d' % (s['room_id'], sp['starting_room_id']))
    if s['plot'] != sp['starting_plot']:
        problems.append('story point %d is not the starting story point %d' % (s['plot'], sp['starting_plot']))
    if not (310 <= s['plot'] < 330):
        problems.append('story point %d is outside 310-329 (the Roaring Knight scene and the hub sign need it)' % s['plot'])
    if s['char'][:3] != [1, 2, 3]:
        problems.append('the party is not Kris, Susie, Ralsei: %r' % s['char'])
    # the default profile (save-profile/profile-config/profile.json) must say the same as drbr.json (only for the provided save)
    prof = os.path.join(ROOT, 'save-profile', 'profile-config', 'profile.json')
    if not args and os.path.exists(prof):
        pj = json.load(open(prof))
        for k, v in sp.items():
            if k in pj and pj[k] != v:
                problems.append('profile.json %s=%r but drbr.json says %r' % (k, pj[k], v))
        if pj.get('save_template_sha256') != hashlib.sha256(data).hexdigest():
            problems.append('profile.json names another starting save (save_template_sha256)')
        if pj.get('default_settings', {}).get('start_mode') != sp.get('default_start_mode'):
            problems.append('profile.json default start_mode differs from drbr.json default_start_mode')
    info = {
        'file': path, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'sha1': hashlib.sha1(data).hexdigest(),
        'md5': hashlib.md5(data).hexdigest(), 'name': s['truename'], 'party': s['char'], 'gold': s['gold'], 'lv': s['lv'],
        'plot': s['plot'], 'room_id': s['room_id'], 'room': ROOMS.get(s['room_id'], '?'), 'play_time_hours_at_30fps': round(s['time'] / 30 / 3600, 2),
        'nonzero_flags': s['nonzero_flags'], 'hp': [(p['hp'], p['maxhp']) for p in s['party_stats'][1:5]], 'problems': problems,
    }
    if '--json' in sys.argv:
        print(json.dumps(info, indent=2))
    else:
        for k, v in info.items():
            print('%-26s %s' % (k, v))
    print('VALID' if not problems else 'NOT THE DRBR STARTING STATE')
    sys.exit(0 if not problems else 1)


if __name__ == '__main__':
    main()
