"""Build 50: Flowery's battle sprites, anchored. Every pose and move sprite is built here from his Chapter 5 frames
(/home/claude/ch5/fl and /home/claude/ch5/om, full sprite size) on one canvas per sprite:
  - Chapter 5 drew his fight facing left (he was the enemy): those frames are mirrored to face the knight;
  - the frames of one Chapter 5 sprite keep their own alignment (their shared origin); different Chapter 5 sprites in one
    animation are lined up by his BODY (the middle of his shirt / hair / skin / vest / pants pixels - the cape, the black
    outline and effects are left out) and his FEET (the lowest pixel under his body);
  - every sprite's origin is set so his body and feet land where Noelle's do on her battle sprite (spr_noelleb_idle, the
    member of his size): standing in a party slot he lines up with the others.
Output: <out>/fl_atlas.png + fl_atlas.json (build.csx: a sprite with w / h / ox / oy gets that size and origin)."""
import json, os, sys
from PIL import Image, ImageOps
FL = '/home/claude/ch5/fl/'
OM = '/home/claude/ch5/om/'
PU = '/home/claude/ch5/pu/'
REF = '/home/claude/work/heroref/'
OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/work/out'


def origins():
    o = {}
    for p in (FL + 'list.txt', OM + 'list.txt', PU + 'list.txt'):
        for ln in open(p, errors='replace'):
            ln = ln.strip()
            if ln.startswith('SPR '):
                ln = ln[4:]
            parts = ln.split()
            if len(parts) >= 4 and parts[0].startswith('spr_') and 'origin' in parts:
                w, h = parts[1].split('x')
                ox, oy = parts[parts.index('origin') + 1].split(',')
                o[parts[0]] = (int(w), int(h), int(ox), int(oy))
    return o


ORG = origins()
BODY = {(113, 88, 68), (255, 255, 255), (254, 229, 2), (255, 240, 111), (223, 115, 50), (111, 166, 38)}


def frames(src):
    d = FL if os.path.exists(FL + src + '_0.png') else (PU if os.path.exists(PU + src + '_0.png') else OM)
    out = []
    i = 0
    while os.path.exists(d + '%s_%d.png' % (src, i)):
        out.append(Image.open(d + '%s_%d.png' % (src, i)).convert('RGBA'))
        i += 1
    assert out, src
    return out


def body_anchor(im, white=False):
    """(x, y) of his body's middle and his feet in this frame"""
    px = im.load()
    xs = []
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            if p[3] == 0:
                continue
            if white or (p[0], p[1], p[2]) in BODY or (abs(p[0] - p[1]) < 60 and p[0] > 90 and p[2] > 60 and not (p[0] > 100 and p[1] > 95 and p[2] < 70)):
                xs.append(x)
    if not xs:
        bb = im.getbbox()
        return ((bb[0] + bb[2]) / 2.0, bb[3])
    xs.sort()
    lo, hi, mid = xs[len(xs) // 10], xs[(len(xs) * 9) // 10], xs[len(xs) // 2]
    bottom = 0
    for y in range(im.height):
        for x in range(max(0, lo), min(im.width, hi + 1)):
            if px[x, y][3] > 0:
                bottom = max(bottom, y + 1)
    return (float(mid), float(bottom))


# Noelle's body / feet relative to her origin (spr_noelleb_idle: 26x46, origin 3,0)
_n = Image.open(REF + 'spr_noelleb_idle_0.png').convert('RGBA')
_bb = _n.getbbox()
_xs = sorted(x for y in range(_n.height) for x in range(_n.width) if _n.getpixel((x, y))[3] > 0)
NOE = (_xs[len(_xs) // 2] - 3, _bb[3] - 0)          # her body's middle / feet, from her origin
FLOOR_UP = 0                                         # (his feet on her line)

# name: [(chapter 5 sprite, frame indices or None for all, mirror, white silhouette)]
ANIMS = {
    # the hero's own poses (obj_knight_herocc: obj_heroparent draws these)
    'idle': [('spr_flowery_idle3', None, True, False)],
    'walk': [('spr_flowery_walk_right', None, False, False)],
    'attackready': [('spr_flowery_punch_windup', [0], True, False)],
    # FIGHT: wind-up, the punch, and back to his stance (the last frame is what he holds until the attacks are over)
    'attack': [('spr_flowery_punch_windup', [1, 2, 3, 4], True, False), ('spr_flowery_puuunch', [0, 0], False, False), ('spr_flowery_idle3', [0], True, False)],
    'act': [('spr_flowery_pose_point_cooler_right', None, False, False)],
    'spellready': [('spr_flowery_poweringup', [0], True, False)],
    'spell': [('spr_flowery_poweringup', None, True, False)],
    'item': [('spr_flowery_gestureup_right', None, False, False)],
    'defend': [('spr_flowery_crouch', None, False, False)],
    'hurt': [('spr_flowery_hurt', None, True, False)],
    'defeat': [('spr_flowery_kneel_hurt_right', None, True, False)],
    'victory': [('spr_flowery_pose_r', None, True, False)],
    # his moves (markers in his hero's place)
    'kiss': [('spr_flowery_kiss', None, True, False)],
    'dance': [('spr_flowery_pirouette', None, True, False), ('spr_flowery_spin_to_idle', None, True, False)],
    # SANFRANDISCO: his flash kick (run, crouch, crescent kick) - Chapter 5's faces left: mirrored
    'flashkick': [('spr_omegaflowery_flashkick', None, True, False)],
    # MY JARONA: the runner (faces right in Chapter 5: it runs at Kris from the left): run x4, crouch, crescent kick, kick
    'runner': [('spr_flowery_walk_right', None, False, False), ('spr_flowery_crouch', None, False, False),
               ('spr_flowery_kick_crescent', None, False, False), ('spr_flowery_kick', None, False, False)],
    'pose': [('spr_flowery_pose', None, True, False)],
    # MY JARONA (Chapter 5's Jarona rush, obj_orangeheart_floweryjarona): wind-up (0-4, charging), the punch lunge (5),
    # knocked back (6)
    'jarona': [('spr_flowery_punch_windup', None, True, False), ('spr_flowery_puuunch', [0], False, False),
               ('spr_flowery_deflected', [0], True, False)],
    # PRISM RUSH's power-up (Chapter 5's): kneeling, powering up (0-1), then the finish, pointing up (2-6) - facing front
    'powerup': [('spr_flowery_powering_up_kneel', None, False, False), ('spr_flowery_powering_up_finish', None, False, False)],
    # his permanent OMEGA FLOWERY form (the last stand): the battle hero's own poses, white (obj_knight_omega adds the outline
    # and the rainbow) - mirrored to face the knight
    'om_idle': [('spr_omegaflowery_idle', None, True, True)],
    'om_ready': [('spr_omegaflowery_windup', [0], True, True)],
    'om_attack': [('spr_omegaflowery_windup', [0, 1, 2, 3], True, True), ('spr_omegaflowery_punch', [0, 1], True, True), ('spr_omegaflowery_idle', [0], True, True)],
    'om_hurt': [('spr_omegaflowery_hurt', None, True, True)],
    'om_defend': [('spr_omegaflowery_deflect', None, True, True)],
    'om_spellready': [('spr_omegaflowery_powerup', [0], True, True)],
    'om_spell': [('spr_omegaflowery_powerup', None, True, True)],
    'om_pose': [('spr_omegaflowery_pose', None, True, True)],
    # PRISM RUSH: OMEGA FLOWERY (white silhouettes, tinted by the move) - mirrored to face the knight
    'omega': [('spr_omegaflowery_pose', None, True, True), ('spr_omegaflowery_powerup', None, True, True), ('spr_omegaflowery_jarona', None, True, True),
              ('spr_omegaflowery_clash', None, True, True), ('spr_omegaflowery_windup', None, True, True), ('spr_omegaflowery_punch', None, True, True),
              ('spr_omegaflowery_idle', None, True, True), ('spr_omegaflowery_hurt', None, True, True), ('spr_omegaflowery_deflect', None, True, True)],
}

sprites = {}
for name, parts in ANIMS.items():
    placed = []          # (image, dx, dy) relative to the body anchor
    index = {}
    for src, idx, mir, white in parts:
        fr = frames(src)
        if idx is None:
            idx = list(range(len(fr)))
        w, h, ox, oy = ORG[src]
        if mir:
            ox = w - ox
        imgs = [ImageOps.mirror(f) if mir else f for f in fr]
        # this Chapter 5 sprite's body anchor (frame 0) relative to its own origin: every frame of it moves together
        ax, ay = body_anchor(imgs[0], white)
        rel = (ax - ox, ay - oy)
        index[src] = len(placed)
        for i in idx:
            im = imgs[i]
            # top-left of this frame relative to the body anchor
            placed.append((im, -ox - rel[0], -oy - rel[1]))
    minx = min(dx for im, dx, dy in placed)
    miny = min(dy for im, dx, dy in placed)
    maxx = max(dx + im.width for im, dx, dy in placed)
    maxy = max(dy + im.height for im, dx, dy in placed)
    W, H = int(round(maxx - minx)) + 1, int(round(maxy - miny)) + 1
    ax, ay = -minx, -miny          # the body anchor on the canvas
    canv = []
    for im, dx, dy in placed:
        c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        c.paste(im, (int(round(dx - minx)), int(round(dy - miny))))
        canv.append(c)
    # origin: his body / feet land where Noelle's are from her origin
    sprites['spr_knfl_' + name] = {'frames': canv, 'ox': int(round(ax - NOE[0])), 'oy': int(round(ay - NOE[1])), 'w': W, 'h': H, 'start': index}

# the FIGHT bar panel's head (spr_pressfront's frame for him: his head in his gold, like Noelle's in her yellow)
hd = Image.open(FL + 'spr_headflowery_0.png').convert('RGBA')
pf = Image.new('RGBA', (75, 38), (0, 0, 0, 0))
gold = (254, 229, 2, 255)
hb = hd.getbbox()
hc = hd.crop(hb)
if hc.height > 34:
    hc = hc.resize((int(hc.width * 34 / hc.height), 34), Image.NEAREST)
tint = Image.new('RGBA', hc.size, (0, 0, 0, 0))
for y in range(hc.height):
    for x in range(hc.width):
        p = hc.getpixel((x, y))
        if p[3] > 0 and (p[0] + p[1] + p[2]) > 120:
            tint.putpixel((x, y), gold)
pf.paste(tint, (9 + (28 - tint.width) // 2, 2 + (34 - tint.height) // 2), tint)
sprites['spr_knfl_pressfront'] = {'frames': [pf], 'ox': 0, 'oy': 0, 'w': 75, 'h': 38, 'start': {}}

# his hit effect (the FIGHT hit on the foe): his crescent, growing and fading in his gold
cr = Image.open(FL + 'spr_flowery_crescent_only_0.png').convert('RGBA') if os.path.exists(FL + 'spr_flowery_crescent_only_0.png') else Image.open(OM + 'spr_flowery_crescent_only_0.png').convert('RGBA')
cr = cr.crop(cr.getbbox())
fx = []
S = 48
for i, (sc, al) in enumerate([(0.25, 1.0), (0.38, 1.0), (0.5, 0.9), (0.58, 0.7), (0.64, 0.45), (0.68, 0.2)]):
    c = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    im = cr.resize((max(1, int(cr.width * sc * 0.7)), max(1, int(cr.height * sc * 0.7))), Image.NEAREST).rotate(-25 * i, expand=True)
    a = im.split()[3].point(lambda v: int(v * al))
    im.putalpha(a)
    c.paste(im, ((S - im.width) // 2, (S - im.height) // 2), im)
    fx.append(c)
sprites['spr_knfl_hitfx'] = {'frames': fx, 'ox': S // 2, 'oy': S // 2, 'w': S, 'h': S, 'start': {}}

# pack
allf = [(n, i, f) for n, d in sprites.items() for i, f in enumerate(d['frames'])]
AW = 2048
x = y = rowh = 0
pos = {}
for n, i, f in allf:
    if x + f.width + 1 > AW:
        x = 0; y += rowh + 1; rowh = 0
    pos[(n, i)] = (x, y)
    x += f.width + 1; rowh = max(rowh, f.height)
AH = 1
while AH < y + rowh:
    AH *= 2
atlas = Image.new('RGBA', (AW, AH), (0, 0, 0, 0))
meta = {}
for n, i, f in allf:
    px, py = pos[(n, i)]
    atlas.paste(f, (px, py))
    d = sprites[n]
    m = meta.setdefault(n, {'donor': 'spr_headflowery', 'w': d['w'], 'h': d['h'], 'ox': d['ox'], 'oy': d['oy'], 'start': d['start'], 'frames': []})
    m['frames'].append({'x': px, 'y': py, 'w': f.width, 'h': f.height})
atlas.save(os.path.join(OUT, 'fl_atlas.png'))
json.dump({'width': AW, 'height': AH, 'sprites': meta, 'noelle_anchor': NOE}, open(os.path.join(OUT, 'fl_atlas.json'), 'w'), indent=1)
print('fl_atlas: %d sprites, %d frames, %dx%d; Noelle body/feet from origin %r' % (len(meta), len(allf), AW, AH, NOE))
for n, m in meta.items():
    print('  %-26s %3dx%-3d origin %4d,%-4d frames %2d %s' % (n, m['w'], m['h'], m['ox'], m['oy'], len(m['frames']), m['start'] or ''))
