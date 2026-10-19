"""Render hub screens: run the real hub GML in the simulator with drawing mocked, then rasterise the recorded
draw calls with the game's own fonts and sprites (gmrender). Used to look at every menu screen and to check layout."""
import sys, os, math
sys.path.insert(0, '/home/claude/work/uiref')
from harness import *
import gmrender as G

FONTMAP = {'mainbig': 'fnt_mainbig', 'main': 'fnt_main', 'small': 'fnt_small', '8bit': 'fnt_8bit', 'tinynoelle': 'fnt_tinynoelle',
           'dotumche': 'fnt_dotumche', 'comicsans': 'fnt_comicsans', '8bit_mixed': 'fnt_8bit'}

class Recorder:
    def __init__(self, sim):
        self.sim = sim
        self.ops = []
        self.st = {'color': 16777215, 'alpha': 1.0, 'font': 'fnt_mainbig', 'halign': 0, 'valign': 0}
        self.rev = {}
        self.install()

    def name_of(self, idx):
        if isinstance(idx, str):
            return idx
        if not self.rev or idx not in self.rev:
            self.rev = {v: k for k, v in self.sim.assets.items()}
        return self.rev.get(idx, '?%s' % idx)

    def fontobj(self):
        try:
            return G.font(self.st['font'])
        except Exception:
            return G.font('fnt_mainbig')

    def install(self):
        s = self.sim
        R = self
        def setc(sim, c):
            R.st['color'] = int(c); return 0
        def seta(sim, a):
            R.st['alpha'] = float(a); return 0
        def setf(sim, f):
            n = R.name_of(f)
            R.st['font'] = n if (n.startswith('fnt_') or n == 'hpfont') else 'fnt_mainbig'
            return 0
        def set84(sim, f):
            R.st['font'] = FONTMAP.get(str(f), 'fnt_mainbig'); return 0
        def seth(sim, h):
            R.st['halign'] = int(h); return 0
        def setv(sim, v):
            R.st['valign'] = int(v); return 0
        for n, fn in (('draw_set_color', setc), ('draw_set_colour', setc), ('draw_set_alpha', seta), ('draw_set_font', setf),
                      ('scr_84_set_draw_font', set84), ('draw_set_halign', seth), ('draw_set_valign', setv)):
            s.mock(n, fn)
        s.mock('draw_get_color', lambda sim: R.st['color'])
        s.mock('draw_get_colour', lambda sim: R.st['color'])
        s.mock('draw_get_alpha', lambda sim: R.st['alpha'])
        s.mock('draw_get_font', lambda sim: s.assets.get(R.st['font'], 0))
        s.mock('draw_get_halign', lambda sim: R.st['halign'])
        s.mock('draw_get_valign', lambda sim: R.st['valign'])
        def sw(sim, t):
            return R.fontobj().width(R.gtext(t))
        def sh(sim, t):
            return R.fontobj().height(R.gtext(t))
        s.mock('string_width', sw)
        s.mock('string_height', sh)
        def swe(sim, t, sep, w):
            lines = R.wrap(R.gtext(t), w)
            return max([R.fontobj().line_width(l) for l in lines] or [0])
        def she(sim, t, sep, w):
            lines = R.wrap(R.gtext(t), w)
            lh = R.fontobj().h if sep < 0 else sep
            return lh * len(lines)
        s.mock('string_width_ext', swe)
        s.mock('string_height_ext', she)
        def text(sim, x, y, t):
            R.op('text', x, y, R.gtext(t), 1, 1, 0, -1, -1, None); return 0
        def text_tr(sim, x, y, t, xs, ys, a):
            R.op('text', x, y, R.gtext(t), xs, ys, a, -1, -1, None); return 0
        def text_ext(sim, x, y, t, sep, w):
            R.op('text', x, y, R.gtext(t), 1, 1, 0, sep, w, None); return 0
        def text_ext_tr(sim, x, y, t, sep, w, xs, ys, a):
            R.op('text', x, y, R.gtext(t), xs, ys, a, sep, w, None); return 0
        def text_col(sim, x, y, t, c1, c2, c3, c4, al):
            R.op('text', x, y, R.gtext(t), 1, 1, 0, -1, -1, (c1, al)); return 0
        def text_tr_col(sim, x, y, t, xs, ys, a, c1, c2, c3, c4, al):
            R.op('text', x, y, R.gtext(t), xs, ys, a, -1, -1, (c1, al)); return 0
        s.mock('draw_text', text)
        s.mock('draw_text_transformed', text_tr)
        s.mock('draw_text_ext', text_ext)
        s.mock('draw_text_ext_transformed', text_ext_tr)
        s.mock('draw_text_color', text_col)
        s.mock('draw_text_colour', text_col)
        s.mock('draw_text_transformed_color', text_tr_col)
        from gmlsim.lib_mocks import check_draw_args as _cda
        def spr(sim, sp, im, x, y):
            _cda(sim, 'draw_sprite', (sp, im, x, y))
            R.ops.append(('spr', R.name_of(sp), im, x, y, 1, 1, 0, R.fogc(16777215), R.st['alpha'], None, None)); return 0
        def spr_ext(sim, sp, im, x, y, xs, ys, rot, col, al):
            _cda(sim, 'draw_sprite_ext', (sp, im, x, y, xs, ys, rot, col, al))
            R.ops.append(('spr', R.name_of(sp), im, x, y, xs, ys, rot, R.fogc(col), al, None, None)); return 0
        # build 47: gpu_set_fog(true, col, 0, 0) draws sprites as flat silhouettes (the online SOUL colours)
        R.st['fog'] = None
        def fog(sim, en, col, a=0, b=0):
            R.st['fog'] = int(col) if en else None; return 0
        s.mock('gpu_set_fog', fog)
        def spr_st(sim, sp, im, x, y, w, h):
            _cda(sim, 'draw_sprite_stretched', (sp, im, x, y, w, h))
            R.ops.append(('spr', R.name_of(sp), im, x, y, 1, 1, 0, R.fogc(16777215), R.st['alpha'], (w, h), None)); return 0
        def spr_st_ext(sim, sp, im, x, y, w, h, col, al):
            _cda(sim, 'draw_sprite_stretched_ext', (sp, im, x, y, w, h, col, al))
            R.ops.append(('spr', R.name_of(sp), im, x, y, 1, 1, 0, R.fogc(col), al, (w, h), None)); return 0
        def spr_part(sim, sp, im, l, t, w, h, x, y):
            _cda(sim, 'draw_sprite_part', (sp, im, l, t, w, h, x, y))
            R.ops.append(('spr', R.name_of(sp), im, x, y, 1, 1, 0, R.fogc(16777215), R.st['alpha'], None, (l, t, w, h))); return 0
        def spr_part_ext(sim, sp, im, l, t, w, h, x, y, xs, ys, col, al):
            _cda(sim, 'draw_sprite_part_ext', (sp, im, l, t, w, h, x, y, xs, ys, col, al))
            R.ops.append(('spr', R.name_of(sp), im, x, y, xs, ys, 0, R.fogc(col), al, None, (l, t, w, h))); return 0
        s.mock('draw_sprite', spr)
        s.mock('draw_sprite_ext', spr_ext)
        s.mock('draw_sprite_stretched', spr_st)
        s.mock('draw_sprite_stretched_ext', spr_st_ext)
        s.mock('draw_sprite_part', spr_part)
        s.mock('draw_sprite_part_ext', spr_part_ext)
        def rect(sim, x1, y1, x2, y2, outline):
            R.ops.append(('rect', x1, y1, x2, y2, R.st['color'], R.st['alpha'], bool(outline))); return 0
        def rectc(sim, x1, y1, x2, y2, c1, c2, c3, c4, outline):
            R.ops.append(('rect', x1, y1, x2, y2, c1, R.st['alpha'], bool(outline))); return 0
        s.mock('draw_rectangle', rect)
        s.mock('draw_rectangle_color', rectc)
        s.mock('draw_rectangle_colour', rectc)
        def line(sim, x1, y1, x2, y2):
            R.ops.append(('line', x1, y1, x2, y2, R.st['color'], R.st['alpha'], 1)); return 0
        def linew(sim, x1, y1, x2, y2, w):
            R.ops.append(('line', x1, y1, x2, y2, R.st['color'], R.st['alpha'], w)); return 0
        s.mock('draw_line', line)
        s.mock('draw_line_width', linew)
        def circ(sim, x, y, r, outline):
            R.ops.append(('circle', x, y, r, R.st['color'], R.st['alpha'], bool(outline))); return 0
        s.mock('draw_circle', circ)
        def tri(sim, x1, y1, x2, y2, x3, y3, outline):
            R.ops.append(('tri', x1, y1, x2, y2, x3, y3, R.st['color'], R.st['alpha'], bool(outline))); return 0
        s.mock('draw_triangle', tri)
        def item_icon(sim, x, y, t):
            R.ops.append(('spr', 'spr_dmenu_items', t, x, y, 2, 2, 0, R.st['color'], 1, None, None)); return 0
        s.mock('draw_item_icon', item_icon)
        def darkbox(sim, x0, y0, x2, y2):
            R.ops.append(('darkbox', x0, y0, x2, y2)); return 0
        s.mock('scr_darkbox', darkbox)
        def darkbox_black(sim, x0, y0, x2, y2):
            R.ops.append(('rect', x0 + 20, y0 + 20, x2 - 20, y2 - 20, 0, 1.0, False))
            R.ops.append(('darkbox', x0, y0, x2, y2)); return 0
        s.mock('scr_darkbox_black', darkbox_black)
        R.prim = None
        def pbegin(sim, kind):
            R.prim = (int(kind), []); return 0
        def pvert(sim, x, y, c, a):
            if R.prim is not None:
                R.prim[1].append((x, y, int(c), float(a)))
            return 0
        def pend(sim):
            if R.prim is not None:
                R.ops.append(('prim', R.prim[0], R.prim[1]))
            R.prim = None; return 0
        s.mock('draw_primitive_begin', pbegin)
        s.mock('draw_vertex_color', pvert)
        s.mock('draw_vertex_colour', pvert)
        s.mock('draw_primitive_end', pend)
        for n in ('gpu_set_blendmode', 'shader_set', 'shader_reset', 'draw_set_circle_precision'):
            s.mock(n, 0)
        s.mock('sprite_get_width', lambda sim, sp: G.sprite(R.name_of(sp)).w or 16)
        s.mock('sprite_get_height', lambda sim, sp: G.sprite(R.name_of(sp)).h or 16)
        s.mock('sprite_get_xoffset', lambda sim, sp: G.sprite(R.name_of(sp)).ox)
        s.mock('sprite_get_yoffset', lambda sim, sp: G.sprite(R.name_of(sp)).oy)
        def _bb(sp, k):
            S = G.sprite(R.name_of(sp)); bs = [f.split()[3].getbbox() for f in S.frames if f is not None and f.split()[3].getbbox()]
            if not bs:
                return [0, 0, (S.w or 16) - 1, (S.h or 16) - 1][k]
            return [min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs) - 1, max(b[3] for b in bs) - 1][k]
        s.mock('sprite_get_bbox_left', lambda sim, sp: _bb(sp, 0))
        s.mock('sprite_get_bbox_top', lambda sim, sp: _bb(sp, 1))
        s.mock('sprite_get_bbox_right', lambda sim, sp: _bb(sp, 2))
        s.mock('sprite_get_bbox_bottom', lambda sim, sp: _bb(sp, 3))
        s.mock('sprite_get_number', lambda sim, sp: max(1, len(G.sprite(R.name_of(sp)).frames)))
        s.mock('sprite_exists', lambda sim, sp: R.name_of(sp) in R.sim.assets or bool(G.sprite(R.name_of(sp)).frames))
        s.mock('camera_get_view_x', lambda sim, *a: 0)
        s.mock('camera_get_view_y', lambda sim, *a: 0)
        s.mock('camera_get_view_width', lambda sim, *a: 640)
        s.mock('camera_get_view_height', lambda sim, *a: 480)

    def fogc(self, col):
        return ('fog', self.st['fog']) if self.st.get('fog') is not None else col

    def gtext(self, t):
        if isinstance(t, float) and t == int(t):
            t = int(t)
        return str(t)

    def wrap(self, t, w):
        f = self.fontobj()
        out = []
        for ln in t.split('\n'):
            cur = ''
            for wd in ln.split(' '):
                tt = wd if cur == '' else cur + ' ' + wd
                if cur != '' and f.line_width(tt) > w:
                    out.append(cur); cur = wd
                else:
                    cur = tt
            out.append(cur)
        return out

    def op(self, kind, x, y, t, xs, ys, a, sep, w, col):
        c = self.st['color'] if col is None else col[0]
        al = self.st['alpha'] if col is None else col[1]
        self.ops.append(('text', self.st['font'], x, y, t, xs, ys, a, sep, w, c, al, self.st['halign'], self.st['valign']))

    def render(self, path, bg=(24, 24, 36), scale=1):
        C = G.Canvas(640, 480, bg)
        for o in self.ops:
            k = o[0]
            if k == 'text':
                _, fnt, x, y, t, xs, ys, a, sep, w, c, al, ha, va = o
                C.text(fnt, x, y, t, c, al, ha, va, xs, ys, sep, w)
            elif k == 'spr':
                _, nm, im, x, y, xs, ys, rot, col, al, st, part = o
                C.spr(nm, im, x, y, xs, ys, rot, col, al, st, part)
            elif k == 'rect':
                _, x1, y1, x2, y2, c, al, ol = o
                C.rect(x1, y1, x2, y2, c, al, ol)
            elif k == 'line':
                _, x1, y1, x2, y2, c, al, w = o
                C.line(x1, y1, x2, y2, c, al, w)
            elif k == 'circle':
                _, x, y, r, c, al, ol = o
                C.circle(x, y, r, c, al, ol)
            elif k == 'tri':
                # build 51: filled triangles are drawn (the skill diamonds and their icons use them); outlines as 3 lines
                _, x1, y1, x2, y2, x3, y3, c, al, ol = o
                if ol:
                    C.line(x1, y1, x2, y2, c, al, 1); C.line(x2, y2, x3, y3, c, al, 1); C.line(x3, y3, x1, y1, c, al, 1)
                else:
                    C.tri([(x1, y1, c, al), (x2, y2, c, al), (x3, y3, c, al)])
            elif k == 'prim':
                _, kind, vs = o
                if kind == 5:   # pr_trianglestrip
                    for i in range(len(vs) - 2):
                        C.tri(vs[i:i + 3])
                elif kind == 4:   # pr_trianglelist
                    for i in range(0, len(vs) - 2, 3):
                        C.tri(vs[i:i + 3])
            elif k == 'darkbox':
                _, x0, y0, x2, y2 = o
                darkbox(C, x0, y0, x2, y2)
        C.save(path, scale)
        return C

def darkbox(C, x0, y0, x2, y2, jewel=0):
    tw = x2 - x0 - 63; th = y2 - y0 - 63
    if tw > 0:
        C.spr('spr_textbox_top', 0, x0 + 32, y0, stretch=(tw, 32))
        C.spr('spr_textbox_top', 0, x0 + 32, y2 + 1, tw, -2)
    if th > 0:
        C.spr('spr_textbox_left', 0, x2 + 1, y0 + 32, -2, th)
        C.spr('spr_textbox_left', 0, x0, y0 + 32, 2, th)
    C.spr('spr_textbox_topleft', jewel, x0, y0, 2, 2)
    C.spr('spr_textbox_topleft', jewel, x2 + 1, y0, -2, 2)
    C.spr('spr_textbox_topleft', jewel, x0, y2 + 1, 2, -2)
    C.spr('spr_textbox_topleft', jewel, x2 + 1, y2 + 1, -2, -2)

def menu_sim(seed=1):
    sim = make_sim(seed=seed)
    # the hub's own spells (12-15) and descriptions live in the merged spell info
    sim.load_file(M + 'gml_GlobalScript_scr_spellinfo.gml', entry='gml_GlobalScript_scr_spellinfo')
    sim.run('global.knight_variant = 0;')
    sim.define_asset('hpfont')
    sim.run('global.hpfont = hpfont;')
    for fn in ('fnt_mainbig', 'fnt_main', 'fnt_small', 'fnt_8bit'):
        sim.define_asset(fn)
    # every sprite exported for the previews is a real asset of the merged game
    import glob as _g
    for _p in _g.glob('/home/claude/work/uiref/sprites/*.txt'):
        sim.define_asset(os.path.basename(_p)[:-4])
    # build 47: objects the online view code looks for (the Roaring attacks for Hold Breath, the screen shake, the cold
    # place's walls and followers)
    for _o in ('obj_knight_roaring2', 'obj_knight_roaring3', 'obj_shake', 'obj_caterpillarchara', 'obj_solidblock', 'obj_mainchara',
               'obj_heart', 'obj_growtangle', 'obj_bulletparent'):
        if _o not in sim.objects:
            sim.define_object(_o)
    # DRBR: the bosses' objects and assets (the encounter list, the presets and the boss pages name them)
    try:
        import br_harness
        _bd = br_harness.BOSS_DRAW
        br_harness.BOSS_DRAW = False
        br_harness.jv_assets(sim)
        br_harness.BOSS_DRAW = _bd
    except Exception as _e:
        print('menu_sim: no boss assets (%s)' % (_e,))
    rec = Recorder(sim)
    return sim, rec

def shot(sim, rec, path, code='knight_ui_draw();', scale=1):
    rec.ops.clear()
    sim.run(code)
    return rec.render(path, scale=scale)
