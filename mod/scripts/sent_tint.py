"""DRBR 1.0.3: a boss's send in the sender's SOUL colour (online_sent50.gml: kbr_ov_*).

Every event of the bosses' own objects - obj_jv_ (Jevil), obj_hj_ (Gerson), obj_fl_ (Flowery), obj_sn_ (Spamton NEO), obj_pk_
(Pink) - draws through kbr_ov_* (their Draw events, and the draw functions their Create / Step events make): for a piece of a
player's send each picture is drawn again over itself in the sender's colour (and its shapes / words take that colour mixed
in); for everything else - the boss's own pieces in his own fight - the call is the very draw call it was. The Draw (0) event
also marks a piece as drawing itself (kbrovd), so the drawer for the default-drawn pieces (obj_knight_saov) leaves it alone.
The GUI layers (64, 74, 75) are not touched. Idempotent: run last in gen_hub.py, after every boss's code is written and
patched."""
import os
import re

M = '/home/claude/work/build/merged/'
# every event of theirs but the GUI layers' (a piece's draw function is made in its Create - obj_fl_mfancy's draw_func - or by
# another's Step - obj_fl_jarona's for its effects)
PFX = re.compile(r'^gml_Object_obj_(jv|hj|fl|sn|pk)_[a-z0-9_]+?_([A-Za-z]+)_(\w+)\.gml$')
# (the longer names first: draw_sprite_part_ext before draw_sprite_part, draw_sprite_ext before draw_sprite)
CALLS = [
    (re.compile(r'(?<![\w.])draw_sprite_part_ext\('), 'kbr_ov_dspe('),
    (re.compile(r'(?<![\w.])draw_sprite_part\('), 'kbr_ov_dsp('),
    (re.compile(r'(?<![\w.])draw_sprite_ext\('), 'kbr_ov_dse('),
    (re.compile(r'(?<![\w.])draw_sprite\('), 'kbr_ov_ds('),
    (re.compile(r'(?<![\w.])draw_self\(\s*\)'), 'kbr_ov_dself()'),
    (re.compile(r'(?<![\w.])draw_set_colou?r\('), 'kbr_ov_col('),
]
MARK = 'if (global.kbr_san > 0)\n    kbrovd = 1;\n'


def main(m=M):
    files = 0
    calls = 0
    for f in sorted(os.listdir(m)):
        mm = PFX.match(f)
        if not mm or (mm.group(2) == 'Draw' and mm.group(3) in ('64', '74', '75')):
            continue
        p = m + f
        t = open(p, encoding='utf8').read()
        o = t
        for rx, rep in CALLS:
            t, k = rx.subn(rep, t)
            calls += k
        if mm.group(2) == 'Draw' and mm.group(3) == '0' and not t.startswith(MARK):
            t = MARK + t
        if t != o:
            open(p, 'w', encoding='utf8').write(t)
            files += 1
    print('sent tint: %d boss events draw through kbr_ov_* (%d draw calls)' % (files, calls))
    return files


if __name__ == '__main__':
    main()
