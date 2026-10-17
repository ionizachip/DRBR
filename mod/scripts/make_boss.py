"""DRBR: the shared part of every boss import (make_gerson.py, make_flowery.py, make_spamton.py, make_pink.py) - the Jevil model
(make_jevil.py) made general.

A boss's pieces are copied from the player's own chapter data.win (decompiled by jevil/dumpall.csx into /home/claude/work/src/<src>/)
as NEW objects with the boss's prefix (Chapter 3 may have the same names for other things), their code changed only where
Chapter 3 differs:
  - object names -> the boss's copies; names of source objects that are NOT imported -> obj_drbr_none (an empty object: never
    there, so i_ex / with / instance_exists see nothing; only unreachable code would make one);
  - sprites the Chapter 3 build lacks, or has with another size, -> spr_<prefix>_* copies (the generic ones Chapter 3 has with the
    same size and origin keep their names); sounds the build lacks are imported under their own names;
  - the source chapter's view enum (e__VW) -> Chapter 3's camera calls; scr_84_get_sound("x") -> x;
  - randomness of the attacks -> the attack stream (det_rewrite: kbr_random & co.), except for the files a boss marks local;
  - "obj_x.v = e;" (every instance in GameMaker; the emulator sets only the first) -> a with();
  - every Create of a piece ends with kbr_bvars() (the fields Chapter 3's battle code reads; a bullet is complete - the
    projectile contract);
  - a Step / Draw that reads obj_heart. skips a step without a SOUL.
The manifest (build/assets.json) gets the sprites (packed: only their own pixels are copied, PackPages in build.csx), the
sounds and the object shells (sprite / mask / parent / depth from the source), tagged with the boss's key."""
import os, re, json, glob, sys
sys.path.insert(0, '/home/claude/scripts')
import det_rewrite

SRC = '/home/claude/work/src/'
ASSETS = '/home/claude/work/build/assets.json'
CH3 = '/home/claude/work/src/built/assets.tsv'
NONE = 'obj_drbr_none'


def table(p):
    t = {'obj': {}, 'spr': {}, 'snd': {}, 'shd': {}, 'bg': {}}
    for l in open(p, encoding='utf8'):
        r = l.rstrip('\n').split('\t')
        if r[0] in t:
            t[r[0]][r[1]] = r[2:]
    return t


def block_at(t, i):
    """(start, end) of the {...} block whose '{' is the first at or after i"""
    j = t.index('{', i)
    d = 0
    k = j
    n = len(t)
    while k < n:
        c = t[k]
        if c == '"':
            k += 1
            while k < n and t[k] != '"':
                if t[k] == '\\':
                    k += 1
                k += 1
        elif c == '{':
            d += 1
        elif c == '}':
            d -= 1
            if d == 0:
                return j, k + 1
        k += 1
    raise ValueError('unbalanced')


class Boss:
    def __init__(self, key, src, prefix, objmap, keep_spr=(), import_spr=(), local=(), none_ok=None):
        self.key = key
        self.src = src
        self.prefix = prefix
        self.objmap = dict(objmap)
        self.keep_spr = set(keep_spr)
        self.import_spr = set(import_spr)
        self.local = set(local)
        self.S = table(SRC + src + '/assets.tsv')
        self.B = table(CH3)
        self.files = {}
        self.sprites = set()
        self.sounds = set()
        self.none_ok = none_ok

    # ---- source
    def code(self, name):
        p = SRC + self.src + '/code/' + name + '.gml'
        return open(p, encoding='utf8', errors='replace').read() if os.path.exists(p) else None

    def events(self, o):
        out = {}
        for f in sorted(glob.glob(SRC + self.src + '/code/gml_Object_%s_*.gml' % o)):
            n = os.path.basename(f)[len('gml_Object_%s_' % o):-4]
            if re.match(r'^(Create|Step|Draw|Alarm|Other|Destroy|Collision|CleanUp|KeyPress|PreCreate)_', n) and not n.startswith('KeyPress') and not n.startswith('Mouse'):
                out[n] = open(f, encoding='utf8', errors='replace').read()
        return out

    # ---- names
    def spr_new(self, s):
        if s in self.keep_spr:
            return s
        if s in self.B['spr'] and s not in self.import_spr:
            a = self.B['spr'][s]
            b = self.S['spr'].get(s)
            # same size, origin and frame count as the source's: Chapter 3's own (the generic art)
            if b and a[:4] == b[:4] and (len(a) < 5 or len(b) < 5 or a[4] == b[4]):
                return s
        return 'spr_%s_%s' % (self.prefix, s[4:] if s.startswith('spr_') else s)

    def rename(self, t):
        def obj(m):
            n = m.group(0)
            if n in self.objmap:
                return self.objmap[n]
            if n in self.S['obj'] and n not in self.B['obj']:
                return NONE
            return n
        t = re.sub(r'\bobj_\w+\b', obj, t)

        def spr(m):
            n = m.group(0)
            if n in self.S['spr']:
                nn = self.spr_new(n)
                if nn != n or n not in self.B['spr']:
                    self.sprites.add(n)
                return nn
            return n
        # (mask_* too: Chapter 5's mask_empty - a sprite there, an unknown name (an instance variable) in Chapter 3)
        t = re.sub(r'\b(spr_\w+|bg_\w+|IMAGE_\w+|mask_(?!index\b)\w+)\b', spr, t)
        for m in re.finditer(r'\b(snd_\w+|motor_\w+)\b', t):
            n = m.group(1)
            if n in self.S['snd'] and n not in self.B['snd']:
                self.sounds.add(n)
        return t

    def fix(self, t, det=True):
        t = re.sub(r'\nenum e__VW\s*\{[^}]*\}\s*', '\n', t)
        t = re.sub(r'scr_84_get_sound\("((?:snd|motor)_\w+)"\)', r'\1', t)
        t = self.rename(t)
        # Chapter 4 / 5's scr_oflash leaves its flash in the caller's instance variable _oflash (Chapter 3's returns it only)
        t = re.sub(r'^([ ]*)scr_oflash\(\);', r'\1_oflash = scr_oflash();', t, flags=re.M)
        t = t.replace('__view_get(e__VW.XView, 0)', 'camera_get_view_x(view_camera[0])')
        t = t.replace('__view_get(e__VW.YView, 0)', 'camera_get_view_y(view_camera[0])')
        t = t.replace('__view_get(e__VW.WView, 0)', 'camera_get_view_width(view_camera[0])')
        t = t.replace('__view_get(e__VW.HView, 0)', 'camera_get_view_height(view_camera[0])')
        if det:
            t = det_rewrite.rewrite(t)[0]
        return t

    def take(self, o, skip=()):
        """the events of source object o as the boss's copy (fixed)"""
        new = self.objmap[o]
        ev = self.events(o)
        assert ev, 'no code for ' + o
        self.shell(o)
        for n, t in ev.items():
            if n in skip:
                continue
            det = (o not in self.local) and not n.startswith('Draw')
            self.files['gml_Object_%s_%s.gml' % (new, n)] = self.fix(t, det)
        return ev

    def shell(self, o):
        """the object's own sprite and mask (set in the source's data.win, never named in code): imported like the code's -
        the build gives the copy the mapped names, and a name the build lacks would leave it with no sprite and no mask"""
        row = self.S['obj'].get(o)
        if not row:
            return
        for n in row[1:3]:
            if n and n in self.S['spr']:
                if self.spr_new(n) != n or n not in self.B['spr']:
                    self.sprites.add(n)

    # ---- the common finishing rules
    def finish(self, no_vars=(), no_guard=()):
        P = 'obj_%s_' % self.prefix
        cnt = [0]

        def every(m):
            cnt[0] += 1
            v = '_%sv%d' % (self.prefix, cnt[0])
            return '%svar %s = %s;\n%swith (%s)\n%s    %s = %s;' % (m.group(1), v, m.group(4), m.group(1), m.group(2), m.group(1), m.group(3), v)
        for n in list(self.files):
            self.files[n] = re.sub(r'^([ ]*)(%s\w+)\.(\w+) = (.+);$' % re.escape(P), every, self.files[n], flags=re.M)
        for n in list(self.files):
            m = re.match(r'gml_Object_(%s\w+)_Create_0\.gml$' % re.escape(P), n)
            if m and m.group(1) not in no_vars:
                self.files[n] = self.files[n].rstrip('\n') + '\nkbr_bvars();\n'
        for n in list(self.files):
            m = re.match(r'gml_Object_(%s\w+)_(Step|Draw)_\d+\.gml$' % re.escape(P), n)
            if m and m.group(1) not in no_guard and re.search(r'\bobj_heart\.', self.files[n]):
                self.files[n] = 'if (!instance_exists(obj_heart))\n    exit;\n' + self.files[n]
        e = [n for n, t in self.files.items() if 'e__VW' in t or '__view_get' in t]
        assert not e, ('view enum left', e)

    # ---- pieces a SEND can use (the target's own game makes them around its SOUL while its own boss fights on)
    def sendable(self, keep_soul=(), skip=(), guard=()):
        """every taken piece (not the boss's battle object / background, `skip`): joins the send that made it (kbr_ev_cr, the first
        line of its Create; kbr_ev_in on its other events - what it makes joins too); reads the turn timer as a send does
        (kbr_tt(): a sent piece never ends with the boss's turn - its send's end does); and a sent piece never writes the boss's
        battle object, the box or the SOUL (`if (kbr_mine())` before those writes: 1 for the boss's own pieces, so they are
        unchanged). keep_soul: pieces whose SOUL / box writes ARE the send (a SOUL-mode send: the shield and its spears)."""
        P = 'obj_%s_' % self.prefix
        boss = 'obj_%s_' % self.prefix
        n_cr = n_in = n_tt = n_g = 0
        for n in list(self.files):
            m = re.match(r'gml_Object_(%s\w+?)_(Create|Step|Draw|Alarm|Other|Collision|CleanUp|Destroy|PreCreate)_(\w+)\.gml$' % re.escape(P), n)
            if not m or m.group(1) in skip:
                continue
            t = self.files[n]
            if m.group(2) == 'Create':
                t = 'kbr_ev_cr();\n' + t
                n_cr += 1
            else:
                t = 'kbr_ev_in();\n' + t
                n_in += 1
            t, k = re.subn(r'\bglobal\.turntimer\b(?!\s*(=[^=]|\+=|-=|\*=|/=|\+\+|--))', 'kbr_tt()', t)
            n_tt += k
            if m.group(1) not in keep_soul:
                tg = '|'.join(['obj_growtangle', 'obj_heart', re.escape(boss) + 'gerson', re.escape(boss) + 'boss'] + [re.escape(g) for g in guard])
                t, k1 = re.subn(r'^([ ]*)(with \((?:%s)\))$' % tg, r'\1if (kbr_mine())\n\1\2', t, flags=re.M)
                t, k2 = re.subn(r'^([ ]*)((?:obj_growtangle|obj_heart)\.\w+ (?:=|\+=|-=|\*=|/=) .+;)$', r'\1if (kbr_mine())\n\1    \2', t, flags=re.M)
                n_g += k1 + k2
            self.files[n] = t
        return n_cr, n_in, n_tt, n_g

    def write(self, out):
        os.makedirs(out, exist_ok=True)
        for f in glob.glob(out + '*.gml'):
            os.remove(f)
        for n, t in self.files.items():
            open(out + n, 'w', encoding='utf8').write(t)

    def manifest(self, extra_spr=(), extra_snd=()):
        sprs = set(self.sprites) | set(extra_spr)
        sprs = sorted(s for s in sprs if s in self.S['spr'] and (self.spr_new(s) != s or s not in self.B['spr']))
        missing = [s for s in set(self.sprites) | set(extra_spr) if s not in self.S['spr']]
        assert not missing, ('sprites not in the source', missing)
        snds = sorted(s for s in set(self.sounds) | set(extra_snd) if s in self.S['snd'] and s not in self.B['snd'])
        A = json.load(open(ASSETS))
        M = A['manifest']
        ren = A['rename'].setdefault(self.src, {})
        for kind in ('sprites', 'sounds', 'objects'):
            M[kind] = [m for m in M[kind] if m.get('boss') != self.key]
        for s in sprs:
            ren[s] = self.spr_new(s)
            M['sprites'].append({'name': s, 'new': self.spr_new(s), 'src': self.src, 'users': [self.src], 'keep': False, 'added': True, 'dx': 0, 'dy': 0, 'pack': True, 'boss': self.key})
        for s in snds:
            M['sounds'].append({'name': s, 'new': s, 'src': self.src, 'users': [self.src], 'keep': False, 'added': True, 'boss': self.key})
        for a, b in self.objmap.items():
            if a.startswith('@'):
                continue
            ren[a] = b
            M['objects'].append({'name': a, 'new': b, 'src': self.src, 'users': [self.src], 'keep': False, 'added': True, 'boss': self.key})
        json.dump(A, open(ASSETS, 'w'), indent=1)
        return sprs, snds
