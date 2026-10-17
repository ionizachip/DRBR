"""Knight Hub menu sprites in DELTARUNE's own dark-menu style.
- tab buttons (33x24, 3 frames like spr_darkequipbt: 0 = hovered with heart, 1 = idle, 2 = chosen)
- tab captions for the top-left of the menu bar (35x18, tall thin letters like spr_darkmenudesc)
- section captions (76x9, the small boxed labels like spr_dmenu_captions: CHAR / STATS ...)
Letters that the game's caption sprites already contain are cut out of them; the few missing ones are drawn here
in the same 6x6 style. Output: <out>/hub_atlas.png + hub_atlas.json (imported by build.csx like the blue fire atlas)."""
import sys, os, json
from PIL import Image
import numpy as np

SPR = '/home/claude/work/uiref/sprites'
OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/work/out'
PREVIEW = sys.argv[2] if len(sys.argv) > 2 else None

YEL = (255, 201, 14, 255)
GRY = (97, 78, 107, 255)
RED = (237, 28, 36, 255)
BLK = (0, 0, 0, 255)
WHT = (255, 255, 255, 255)
CLR = (0, 0, 0, 0)

def grid(rows):
    return [list(r) for r in rows]

# ---------------- tab icons (16x16 masks, drawn at x 14..29, y 4..19 of the button like the game's own) -------------
ICON_KNIGHT = [  # a four-point star, like the stars of the knight's attacks
    ".......##.......",
    ".......##.......",
    ".......##.......",
    "......####......",
    "......####......",
    ".....######.....",
    "...##########...",
    "################",
    "################",
    "...##########...",
    ".....######.....",
    "......####......",
    "......####......",
    ".......##.......",
    ".......##.......",
    ".......##.......",
]
ICON_PARTY = [  # two figures
    "................",
    "....###.........",
    "...#####...###..",
    "...#####..#####.",
    "...#####..#####.",
    "....###...#####.",
    "...........###..",
    "..#######.......",
    ".#########.####.",
    ".##.###.#######.",
    ".##.###.##.##.##",
    ".##.###.##.##.##",
    ".##.###.##.##.##",
    "....#.#.........",
    "....#.#.........",
    "................",
]
ICON_RULES = [  # skull
    "................",
    ".....######.....",
    "...##########...",
    "..############..",
    "..############..",
    "..###..##..###..",
    "..##....#...##..",
    "..##...###..##..",
    "..###.#####.##..",
    "...#####.#####..",
    "....#########...",
    ".....#.#.#.#....",
    ".....#######....",
    "................",
    "................",
    "................",
]

def make_button(icon):
    frames = []
    for f in range(3):
        im = Image.new('RGBA', (33, 24), BLK)
        px = im.load()
        col = GRY if f == 1 else YEL
        for x in range(33):
            px[x, 0] = col; px[x, 23] = col
        for y in range(24):
            px[0, y] = col; px[32, y] = col
        for y, row in enumerate(icon):
            for x, ch in enumerate(row):
                if ch == '#':
                    px[14 + x, 4 + y] = col
        if f == 0:
            heart = ["##.##", "#######", "#######", "#######", ".#####", "..###", "...#"]
            heart = [".##.##.", "#######", "#######", "#######", ".#####.", "..###..", "...#..."]
            for y, row in enumerate(heart):
                for x, ch in enumerate(row):
                    if ch == '#':
                        px[4 + x, 9 + y] = RED
        frames.append(im)
    return frames

# ---------------- tall captions (35x18) -------------
def tall(word_cols):
    """word_cols: list of letter bitmaps (each a list of 16 strings). Centered into 35x18 with black background."""
    widths = [len(c[0]) for c in word_cols]
    total = sum(widths) + (len(widths) - 1)
    x0 = (35 - total) // 2
    im = Image.new('RGBA', (35, 18), BLK)
    px = im.load()
    x = x0
    for c in word_cols:
        for y, row in enumerate(c):
            for i, ch in enumerate(row):
                if ch == '#':
                    px[x + i, 1 + y] = WHT
        x += len(c[0]) + 1
    return im

def L(rows):
    assert len(rows) == 16, rows
    return rows

T_K = L(["#..#", "#..#", "#..#", "#.#.", "#.#.", "#.#.", "##..", "#...", "##..", "#.#.", "#.#.", "#.#.", "#..#", "#..#", "#..#", "#..#"])
T_N = L(["#...#", "#...#", "#...#", "##..#", "##..#", "##..#", "##..#", "##..#", "#.#.#", "#.#.#", "#..##", "#..##", "#..##", "#..##", "#...#", "#...#"])
T_I = L(["#####"] + ["..#.."] * 14 + ["#####"])
T_G = L(["####", "#...", "#...", "#...", "#...", "#...", "#.##", "#..#", "#..#", "#..#", "#..#", "#..#", "#..#", "#..#", "#..#", "####"])
T_H = L(["#..#"] * 6 + ["####"] + ["#..#"] * 9)
T_T = L(["#####"] + ["..#.."] * 15)
T_P = L(["####"] + ["#..#"] * 5 + ["####"] + ["#..."] * 9)
T_A = L([".##.", "#..#", "#..#", "#..#", "#..#", "#..#", "####"] + ["#..#"] * 9)
T_R = L(["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####.", "#..#.", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#"])
T_Y = L(["#...#"] * 6 + [".#.#."] + ["..#.."] * 9)
T_U = L(["#..#"] * 15 + ["####"])
T_L = L(["#..."] * 15 + ["####"])
T_E = L(["####"] + ["#..."] * 5 + ["###."] + ["#..."] * 8 + ["####"])
T_S = L(["####"] + ["#..."] * 5 + ["####"] + ["...#"] * 8 + ["####"])

TALL = {
    'KNIGHT': [T_K, T_N, T_I, T_G, T_H, T_T],
    'PARTY': [T_P, T_A, T_R, T_T, T_Y],
    'RULES': [T_R, T_U, T_L, T_E, T_S],
}

# ---------------- small boxed captions (76x9) -------------
def cut_letters():
    """letters 6x6 (I and T are 5 wide) cut from spr_dmenu_captions frames"""
    words = {0: 'CHAR', 1: 'EQUIPPED', 2: 'ARMORS', 3: 'WEAPONS', 4: 'STATS', 5: 'SPELLS'}
    out = {}
    for f, w in words.items():
        a = np.array(Image.open(os.path.join(SPR, 'spr_dmenu_captions_%d.png' % f)).convert('RGBA'))
        on = (a[..., 0] > 200) & (a[..., 3] > 0)
        cols = [x for x in range(a.shape[1]) if on[1:7, x].any()]
        # split into runs separated by >=2 empty columns
        runs = []
        cur = [cols[0]]
        for x in cols[1:]:
            if x - cur[-1] > 2:
                runs.append(cur); cur = [x]
            else:
                cur.append(x)
        runs.append(cur)
        # merge runs that belong to one letter (letters are 5-6 px wide; the gap between letters is 2 columns)
        letters = []
        for r in runs:
            letters.append((r[0], r[-1]))
        if len(letters) != len(w):
            # some letters have inner gaps of 1 col; recompute with gap threshold 1
            letters = []
            x = cols[0]
            while x <= cols[-1]:
                start = x
                while x <= cols[-1] and (on[1:7, x].any() or (x + 1 <= cols[-1] and on[1:7, x + 1].any() and not (not on[1:7, x].any() and not on[1:7, x - 1].any()))):
                    x += 1
                letters.append((start, x - 1))
                while x <= cols[-1] and not on[1:7, x].any():
                    x += 1
        for ch, (x0, x1) in zip(w, letters):
            if ch in out:
                continue
            bm = []
            for y in range(1, 7):
                bm.append(''.join('#' if on[y, x] else '.' for x in range(x0, x1 + 1)))
            out[ch] = bm
    return out

EXTRA = {
    'G': [".#####", "#.....", "#.....", "#..###", "#....#", ".#####"],
    'K': ["#....#", "#...#.", "####..", "#...#.", "#....#", "#....#"],
    'Y': ["#....#", "#....#", ".#..#.", "..##..", "..##..", "..##.."],
    'F': ["######", "#.....", "#.....", "####..", "#.....", "#....."],
    'B': ["#####.", "#....#", "#####.", "#....#", "#....#", "#####."],
    'V': ["#....#", "#....#", "#....#", "#....#", ".#..#.", "..##.."],
    'X': ["#....#", ".#..#.", "..##..", "..##..", ".#..#.", "#....#"],
    'Z': ["######", "....#.", "...#..", "..#...", ".#....", "######"],
    'J': ["....#", "....#", "....#", "....#", "#...#", ".###."],
    ' ': ["..", "..", "..", "..", "..", ".."],
}

def caption(word, letters):
    im = Image.new('RGBA', (76, 9), CLR)
    px = im.load()
    bms = [letters.get(c) or EXTRA[c] for c in word]
    width = 6 + sum(len(b[0]) for b in bms) + 2 * (len(bms) - 1) + 8
    assert width <= 76, (word, width)
    for y in range(9):
        for x in range(width):
            px[x, y] = BLK
    x = 6
    for b in bms:
        for yy, row in enumerate(b):
            for xx, ch in enumerate(row):
                if ch == '#':
                    px[x + xx, 1 + yy] = WHT
        x += len(b[0]) + 2
    return im

CAPTIONS = ['KNIGHTS', 'INFO', 'MEMBERS', 'RULES', 'OPTIONS', 'PRESETS', 'RECORDS', 'CREDITS', 'MUSIC', 'PARTY', 'SLOT', 'DETAILS', 'BEST', 'TOTAL', 'LOADOUTS', 'ATTACKS', 'TAG TEAM', 'REMIX', 'ONLINE', 'PLAYERS', 'ROOM', 'SETTINGS', 'KEYBINDS', 'SOULS', 'MY SOUL', 'VIEW', 'BOTS', 'BOT', 'INVITE', 'SKINS', 'BOSSES']

def soul_frames():
    d = Image.open(os.path.join(SPR, 'spr_dodgeheart_0.png')).convert('RGBA')
    heart = Image.new('RGBA', d.size, (0, 0, 0, 0))
    whole = Image.new('RGBA', d.size, (0, 0, 0, 0))
    for y in range(d.size[1]):
        for x in range(d.size[0]):
            r, g, b, a = d.getpixel((x, y))
            if a == 0:
                continue
            if r > 128 and g < 100:
                heart.putpixel((x, y), (255, 255, 255, 255))
            else:
                whole.putpixel((x, y), (255, 255, 255, 255))
    # build 48: frame 2 = the heart cracked down the middle (Deltarune's spr_heartbreak: a zig-zag split, the halves 1 px apart);
    # frame 3 = one shard (a small piece, turned as it flies)
    W, Hh = d.size
    xs = [x for y in range(Hh) for x in range(W) if heart.getpixel((x, y))[3]]
    cx = (min(xs) + max(xs)) // 2 if xs else W // 2
    crack = Image.new('RGBA', d.size, (0, 0, 0, 0))
    for y in range(Hh):
        zx = cx + (1 if (y // 2) % 2 else 0)
        for x in range(W):
            if not heart.getpixel((x, y))[3] or x == zx:
                continue
            nx = x if x < zx else x + 1
            if 0 <= nx < W:
                crack.putpixel((nx, y), (255, 255, 255, 255))
    shard = Image.new('RGBA', d.size, (0, 0, 0, 0))
    for (x, y) in [(9, 9), (10, 9), (9, 10), (10, 10), (11, 10), (10, 11)]:
        shard.putpixel((x, y), (255, 255, 255, 255))
    return [heart, whole, crack, shard]

def main():
    letters = cut_letters()
    for k in EXTRA:
        letters.setdefault(k, EXTRA[k])
    sprites = {}
    sprites['spr_khub_bt_knight'] = ('spr_darkequipbt', make_button(ICON_KNIGHT))
    sprites['spr_khub_bt_party'] = ('spr_darkequipbt', make_button(ICON_PARTY))
    sprites['spr_khub_bt_rules'] = ('spr_darkequipbt', make_button(ICON_RULES))
    sprites['spr_khub_menudesc'] = ('spr_darkmenudesc', [tall(TALL[w]) for w in ('KNIGHT', 'PARTY', 'RULES')])
    sprites['spr_khub_captions'] = ('spr_dmenu_captions', [caption(w, letters) for w in CAPTIONS])
    # build 48: a WHITE SOUL (spr_dodgeheart's size and origin), drawn tinted with a player's colour - no fog, no shader:
    # frame 0 = the heart (spr_heart's shape, 2 px in), frame 1 = only its 2-px edge (the game's own black SOUL edge, heart-shaped)
    sprites['spr_khub_soul'] = ('spr_dodgeheart', soul_frames())
    # atlas
    frames = []
    for name, (donor, fr) in sprites.items():
        for i, im in enumerate(fr):
            frames.append((name, donor, i, im))
    W = max(f[3].size[0] for f in frames) + 2
    H = sum(f[3].size[1] + 2 for f in frames) + 2
    atlas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    y = 1
    meta = {}
    for name, donor, i, im in frames:
        atlas.paste(im, (1, y))
        meta.setdefault(name, {'donor': donor, 'frames': []})['frames'].append({'x': 1, 'y': y, 'w': im.size[0], 'h': im.size[1]})
        y += im.size[1] + 2
    os.makedirs(OUT, exist_ok=True)
    atlas.save(os.path.join(OUT, 'hub_atlas.png'))
    json.dump({'width': W, 'height': H, 'sprites': meta, 'captions': CAPTIONS}, open(os.path.join(OUT, 'hub_atlas.json'), 'w'), indent=1)
    # renderer copies (so the menu previews can draw them)
    for name, (donor, fr) in sprites.items():
        for i, im in enumerate(fr):
            im.save(os.path.join(SPR, '%s_%d.png' % (name, i)))
        open(os.path.join(SPR, name + '.txt'), 'w').write('origin=0,0\nsize=%dx%d\n' % fr[0].size)
    if PREVIEW:
        big = Image.new('RGBA', (360, 300), (40, 40, 60, 255))
        yy = 4
        for name, (donor, fr) in sprites.items():
            xx = 4
            for im in fr:
                big.paste(im, (xx, yy), im)
                xx += im.size[0] + 4
                if xx > 320:
                    xx = 4; yy += im.size[1] + 4
            yy += fr[0].size[1] + 8
        big.resize((big.size[0] * 3, big.size[1] * 3), Image.NEAREST).save(PREVIEW)
    print('hub atlas', W, H, {k: len(v[1]) for k, v in sprites.items()})
    print('caption letters cut:', ''.join(sorted(k for k in letters if k not in EXTRA)))

if __name__ == '__main__':
    main()
