"""Build 50: the Knight Hub's sign. In the snow zone with the hub save's story point (plot 320, as the tester pack's
filech3_2 has it) the fight's setup object makes the sign (extflag "kaizo settings") and the hub's controller, and reading
the sign opens the hub; with a save from after the Knight (plot 330+) there is no sign - and a note says which save to load.
Usage: python3 t_sign50.py"""
import sys, os
os.environ.setdefault('WALL', '200')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu_atk import *
FAILS = []
N = [0]


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)


SAVE = '/home/claude/work/tp50/Save file/filech3_2'
lines = open(SAVE, newline='').read().split('\r\n')
_ln = [x for x in lines if x.strip() != '']
plot = int(float(_ln[-3].strip()))
ok(plot == 320, 'the tester pack\'s save (Save file/filech3_2) is at story point 320 (the hub\'s 310-329) %r' % plot)
M_ = os.environ.get('KH_MERGED', '/home/claude/work/build/merged/')
_src = open(M_ + 'gml_Object_obj_ch3_PTB02_Create_0.gml').read()
ok('if (global.plot >= 310 && global.plot < 330 && room == room_dw_snow_zone)' in _src and '_knight_sign.extflag = "kaizo settings";' in _src and 'knight_ensure_ctrl();' in _src, 'the fight\'s setup makes the hub sign (and the hub controller) at story points 310-329 in the snow zone')
_sg = open(M_ + 'gml_Object_obj_npc_sign_Other_10.gml').read()
ok('knight_menu_open(id);' in _sg, 'reading that sign opens the hub')
for p_, key in ((340, 'base'),):
    sim = mk(key, [1, 2, 3])
    for _m in ('scr_84_get_sprite', 'scr_84_get_font'):
        sim.mock(_m, 0)
    for o in ('obj_npc_sign', 'obj_knight_ctrl', 'obj_mainchara'):
        try:
            sim.define_object(o)
        except Exception:
            pass
    sim._snapauto = True
    # (the cutscene's own actor setup - the base game's - is not what is tested here)
    for _m in ('scr_maincharacters_actors', 'c_wait', 'c_waitcustom'):
        sim.mock(_m, lambda sm, *a: 0)
    try:
        sim.define_object('obj_tmarker')
    except Exception:
        pass
    sim.mock('scr_dark_marker', lambda sm, *a: sm.create_instance('obj_tmarker').id)
    D = []
    sim.mock('draw_text', lambda sm, x, y, s, *a: D.append(str(s)))
    sim.mock('draw_text_transformed', lambda sm, x, y, s, *a: D.append(str(s)))
    _ri = sim.eval('room_dw_snow_zone')
    sim.room_index = _ri
    r = []
    try:
        sim.create_instance('obj_mainchara', 320, 240)
    except Exception:
        pass
    ok_, err = auto(sim, lambda: sim.run('global.plot = %d; global.knight_variant = 0; global.knight_run = 0; with (obj_npc_sign) instance_destroy(); with (obj_ch3_PTB02) instance_destroy();'
                                         'global.P = instance_create(0, 200, obj_ch3_PTB02);'
                                         'global.S = [instance_number(obj_npc_sign), 0, instance_exists(obj_knight_ctrl), room == room_dw_snow_zone];'
                                         'with (obj_npc_sign) { if (extflag == "kaizo settings") global.S[1] = 1; }' % p_))
    if not ok_:
        ok(False, 'plot %d: %s' % (p_, err)); continue
    S = sim.py(sim.eval('global.S'))
    ok_, err = auto(sim, lambda: sim.run('global.H = knight_hub_hint_draw();'))
    H = sim.eval('global.H') if ok_ else ('err', err)
    print(p_, S, H, D[:3])
    if p_ == 320:
        ok(S[3] in (True, 1) and S[0] >= 1 and S[1] == 1 and S[2] in (True, 1) and H == 0, 'plot 320 in the snow zone: the hub sign is made (with the hub controller); no note %r' % ([S, H],))
    else:
        ok(S[1] == 0 and H == 1 and any('SAVE SLOT 3' in d for d in D), 'plot 340 (a save after the Knight): no hub sign - the note says to load SAVE SLOT 3 %r' % ([S, H],))
print('%d checks, %d failed' % (N[0], len(FAILS)))
for f_ in FAILS:
    print('FAILED:', f_)
sys.exit(1 if FAILS else 0)
