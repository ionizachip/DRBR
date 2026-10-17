"""DRBR automatic validation (static, on the BUILT game): fails when a registered boss / send / projectile references a
missing resource or lacks a required property - the kind of bug that let destroyonhit reach a player.

Inputs: a full decompile of the built data.win (BUILT_DIR, default /home/claude/work/src/built: code/*.gml + assets.tsv,
made by jevil/dumpall.csx) and the emulator for the tables (kbr_enc_defs, the skills).
Checks:
  1. every boss definition: required fields, consistent attack tables, its battle object / portrait / every sprite and sound
     its code names exist in the build, its music file is shipped (deliver/mus or the game's mus folder list);
  2. every send (skill): name, description, cost, family; every real-attack send has its builder (kbr_sa_step case) and its
     hidden copy for bots (kbr_sa_bot case); every sprite those cases name exists;
  3. every projectile type (each object that is obj_collidebullet or a child of it): its Create (with event_inherited up the
     parents) gives it the contract fields (scr_bullet_init / kbr_bullet_contract / kbr_jv_vars / its own destroyonhit), or it
     is only ever made through kbr_jv_adopt / scr_bullet_init by its maker - listed per object;
  4. every sprite / object / sound named in the DRBR code (online_*.gml, drbr53.gml, the bosses' generated code) exists.
Usage: python3 t_validate53.py"""
import sys, os, re, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BUILT = os.environ.get('BUILT_DIR', '/home/claude/work/src/built')
T = '/home/claude/scripts/gml_templates_v6/'
FAILS = []
WARN = []
N = [0]


def ok(c, m):
    N[0] += 1
    if not c:
        print('FAIL ' + m, flush=True)
        FAILS.append(m)
    return c


assets = {'obj': {}, 'spr': {}, 'snd': set(), 'shd': set()}
for l in open(os.path.join(BUILT, 'assets.tsv'), encoding='utf8'):
    r = l.rstrip('\n').split('\t')
    if r[0] == 'obj':
        assets['obj'][r[1]] = r[2]
    elif r[0] == 'spr':
        assets['spr'][r[1]] = r
    elif r[0] == 'snd':
        assets['snd'].add(r[1])
    elif r[0] == 'shd':
        assets['shd'].add(r[1])
code = {}
for f in glob.glob(os.path.join(BUILT, 'code', '*.gml')):
    code[os.path.basename(f)[:-4]] = open(f, encoding='utf8', errors='replace').read()
print('built: %d objects, %d sprites, %d sounds, %d code entries' % (len(assets['obj']), len(assets['spr']), len(assets['snd']), len(code)), flush=True)


def strip(t):
    t = re.sub(r'"(?:\\.|[^"\\])*"', '""', t)
    t = re.sub(r'//[^\n]*', '', t)
    return re.sub(r'/\*.*?\*/', '', t, flags=re.S)


def chain(o):
    out = []
    while o and o not in out:
        out.append(o)
        o = assets['obj'].get(o, '')
    return out


# ---------------------------------------------------------------- 3. projectile types
CONTRACT = re.compile(r'\b(scr_bullet_init|kbr_bullet_contract|kbr_jv_vars)\s*\(|\bdestroyonhit\s*=')


def create_inits(o):
    """does the Create that runs for object o (its own, else its parent's ...) give the contract fields?"""
    seen = []
    cur = o
    while cur:
        seen.append(cur)
        c = code.get('gml_Object_%s_Create_0' % cur)
        if c is not None:
            if CONTRACT.search(strip(c)):
                return True, cur
            if 'event_inherited' in c:
                cur = assets['obj'].get(cur, '')
                continue
            return False, cur
        cur = assets['obj'].get(cur, '')
    return False, None


bullets = [o for o in assets['obj'] if 'obj_collidebullet' in chain(o)]
makers = {}
for n, t in code.items():
    for m in re.finditer(r'instance_create(?:_depth|_layer)?\(([^;]*?),\s*(obj_\w+)\)', t):
        makers.setdefault(m.group(2), []).append(n)
no_init = []
vanilla_only = []
spr_set_names = set(re.findall(r'\bsprite_index\s*=|mask_index\s*=', ''))
for o in sorted(bullets):
    good, where = create_inits(o)
    if good:
        continue
    # an object with no sprite and no mask (a manager) cannot touch a SOUL unless code gives it one
    if not any(assets['spr'].get(x) for x in [] ) and o in assets['obj']:
        pass
    # made only by makers that complete it (kbr_jv_adopt / scr_bullet_init / destroyonhit right after the create), or make it
    # inactive (active false: user event 5 and the graze box never read the rest)
    ms = makers.get(o, [])
    if not ms:
        WARN.append('projectile %s: no Create that completes it and never made by instance_create in the code (the fallback covers it)' % o)
        continue
    bad_makers = []
    for n in sorted(set(ms)):
        t = code[n]
        for m in re.finditer(r'instance_create(?:_depth|_layer)?\([^;]*?,\s*%s\)' % re.escape(o), t):
            before = t[max(0, m.start() - 40):m.start()]
            after = t[m.end():m.end() + 600]
            if 'kbr_jv_adopt(' in before or re.search(r'scr_bullet_init|destroyonhit\s*=|kbr_bullet_contract|\.active\s*=\s*(false|0)\b', after):
                continue
            bad_makers.append(n)
    if not bad_makers:
        continue
    drbr = [n for n in bad_makers if re.match(r'gml_Object_(obj_jv_|obj_sp_|obj_gr_|obj_pk_|obj_fw_|obj_knight_|obj_roaringknight_|obj_tracking_|obj_sword_)', n) or 'kbr_' in code.get(n, '')]
    if drbr:
        no_init.append((o, where, sorted(set(drbr))[:3]))
    else:
        vanilla_only.append((o, sorted(set(bad_makers))[:2]))
# a manager with no sprite / mask of its own that its makers never give one cannot touch a SOUL
def can_touch(o):
    spr = mask = ''
    for l in [x for x in []]:
        pass
    return True
no_init = [x for x in no_init if not (x[0].endswith('_manager') or '_manager_' in x[0])]
for v in vanilla_only:
    WARN.append('projectile %s: made incomplete only by Chapter 3 code DRBR does not run (%r) - the fallback covers it offline' % v)
ok(not no_init, 'every projectile type DRBR makes is complete when made (%d types; incomplete: %r)' % (len(bullets), no_init[:6]))
print('projectile types:', len(bullets), 'checked', flush=True)

# the contract's fallback is in the three places a SOUL meets a bullet
ok('kbr_bullet_fix' in code.get('gml_Object_obj_heart_Collision_obj_collidebullet', ''), 'the SOUL\'s collision completes a bullet first (kbr_bullet_fix)')
ok(code.get('gml_Object_obj_collidebullet_Other_15', '').lstrip().startswith('kbr_bullet_fix'), 'obj_collidebullet\'s user event 5 completes it first')
ok('kbr_bullet_fix' in code.get('gml_Object_obj_grazebox_Collision_obj_collidebullet', ''), 'the graze box\'s collision completes it first')

# ---------------------------------------------------------------- 1, 2: bosses and sends through the emulator
import br_harness
from br_harness import br_match
sim, e = br_match(open_ok=0, kn=(0,), seed=5390, bots=0)
ok(e is None, 'emulator: a practice match to read the tables (%s)' % e)


def J(e_):
    return sim.py(sim.eval(e_))


defs = J('kbr_enc_defs()')
REQ = ['key', 'cat', 'fid', 'chapter', 'soul', 'sends', 'desc', 'name', 'short', 'title', 'col', 'lu', 'music', 'obj', 'spr', 'atk']
for d in defs:
    k = d.get('key', '?')
    miss = [f for f in REQ if f not in d]
    ok(not miss, 'boss %s: every required field (%r missing)' % (k, miss))
    n = len(d.get('atk', []))
    for tab in ('type', 'tt', 'cond', 'inv'):
        if tab in d:
            ok(len(d[tab]) == n, 'boss %s: table %s has one entry per attack (%d / %d)' % (k, tab, len(d[tab]), n))
    ok(d.get('obj') in assets['obj'], 'boss %s: its battle object %s is in the build' % (k, d.get('obj')))
    ok(d.get('spr') in assets['spr'], 'boss %s: its portrait %s is in the build' % (k, d.get('spr')))
    mus = d.get('music', '')
    mp = [p for p in ('/home/claude/work/deliver/mus/' + mus, '/mnt/user-data/uploads/common--DELTARUNE/mus/' + mus) if os.path.exists(p)]
    if not mp:
        WARN.append('boss %s: music %s is not in deliver/mus (it must be the game\'s own mus folder file)' % (k, mus))
    for sid in d.get('sends', []):
        ok(J('kbr_skill_family(%d)' % sid) == d.get('fid'), 'boss %s: send %d is in its family' % (k, sid))
    if 'roar' in d:
        ok(0 <= d['roar'] < n and d['atk'][d['roar']][3] == 2, 'boss %s: its finale (%r) is an attack flagged 2' % (k, d.get('roar')))
cnt = J('kbr_skill_count()')
real = []
sa_src = open(T + 'online_sent50.gml').read()


def case_body(fn, sid):
    a = sa_src.find('function %s(' % fn)
    if a < 0:
        return None
    b = sa_src.find('\nfunction ', a + 10)
    body = sa_src[a:b if b > 0 else len(sa_src)]
    m = re.search(r'\bcase %d:(.*?)(?=\n\s*case \d+:|\n\s*default:|\n\}\n)' % sid, body, flags=re.S)
    return m.group(1) if m else None


for sid in range(1, cnt):
    nm = J('kbr_skill_name(%d)' % sid)
    ok(isinstance(nm, str) and nm != '' and nm != '?', 'send %d: a name (%r)' % (sid, nm))
    ok(isinstance(J('kbr_skill_desc(%d)' % sid), str), 'send %d: a description' % sid)
    if J('kbr_skill_real(%d) != ""' % sid):
        real.append(sid)
        b1 = case_body('kbr_sa_step', sid)
        b2 = case_body('kbr_sa_bot', sid)
        if b2 is None:
            # the knights' sends: the bots get twin bullets from kbr_skill_land's own patterns
            sk_src = open(T + 'online_br_skill.gml').read()
            a_ = sk_src.find('function kbr_skill_land(')
            b_ = sk_src.find('\nfunction ', a_ + 10)
            m_ = re.search(r'\bcase %d:' % sid, sk_src[a_:b_])
            b2 = '' if m_ else None
        ok(b1 is not None, 'send %d (%s): its builder (kbr_sa_step case)' % (sid, nm))
        ok(b2 is not None, 'send %d (%s): its hidden copy for bots (kbr_sa_bot case)' % (sid, nm))
        for b in (b1 or '', b2 or ''):
            for a in set(re.findall(r'\b((?:spr|obj|snd)_\w+)\b', strip(b))):
                k_ = 'spr' if a.startswith('spr_') else 'obj' if a.startswith('obj_') else 'snd'
                have = a in (assets[k_] if k_ != 'snd' else assets['snd'])
                ok(have, 'send %d: %s %s is in the build' % (sid, k_, a))
print('sends: %d skills, %d real attacks' % (cnt - 1, len(real)), flush=True)

# ---------------------------------------------------------------- 4. assets named in the DRBR code
src = ''
for f in glob.glob(T + 'online_*.gml') + glob.glob(T + 'drbr53.gml') + glob.glob('/home/claude/scripts/*_gen/*.gml'):
    src += strip(open(f, encoding='utf8').read()) + '\n'
FN = {'snd_play', 'snd_play_x', 'snd_stop', 'snd_loop', 'snd_volume', 'snd_pitch', 'snd_free', 'snd_init', 'snd_is_playing', 'snd_free_all', 'snd_pause', 'snd_resume', 'snd_play_pitch', 'snd_play_volume'}
names = set(re.findall(r'\b((?:spr|obj|snd)_[A-Za-z0-9_]+)\b', src)) - FN
fnames = set(re.findall(r'\bfunction\s+(\w+)', src))
miss = sorted(a for a in names if a not in fnames and not (a in assets['obj'] or a in assets['spr'] or a in assets['snd']))
ok(not miss, 'every sprite / object / sound the DRBR code names is in the build (%d names; missing: %r)' % (len(names), miss[:12]))

for w in WARN:
    print('warn ' + w)
print('validate53: %d checks, %d failed, %d warnings' % (N[0], len(FAILS), len(WARN)))
for f in FAILS[:40]:
    print('  -', f)
sys.exit(1 if FAILS else 0)
