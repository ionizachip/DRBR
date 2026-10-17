"""Build 52: the online-only skins' art (BERDLY, AQUA; DRBR: SETH, ORANGE, GREEN, YELLOW, BLUE, PINK) in build/assets.json. Idempotent.
Donors: c2 = Chapter 2 (data_5.win, MODS_DIR/c2.win) for Berdly's Dark World walking frames; c5 = Chapter 5 (data_2/7.win) for
Aqua's walking frames, her right-facing battle idle and hurt pose, and her dialogue face (the knife, spr_miniface_aqua - the one
scr_miniface_init_aquaseth gives her text). Berdly's battle idle (spr_berdlyb_idle_right) and his dialogue face
(spr_face_berdly_dark) are already in Chapter 3."""
import json
P='/home/claude/work/build/assets.json'
A=json.load(open(P));M=A['manifest']
def add(src,kind,name,new=None):
    new=new or name
    for m in M[kind]:
        if m['new']==new and m['src']==src:
            return
    M[kind].append({'name':name,'new':new,'src':src,'users':[src],'keep':False,'added':True,'dx':0,'dy':0})
for d in ('down','up','left','right'):
    add('c2','sprites','spr_berdly_walk_%s_dw'%d)
    add('c5','sprites','spr_aqua_walk_%s'%d)
for n in ('spr_enemy_aqua_idle_r','spr_enemy_aqua_hurt','spr_miniface_aqua'):
    add('c5','sprites',n)
# DRBR: the other Chapter 5 flowers (Seth, Orange, Green, Yellow, Blue) and Pink as online-only looks (online_skin52.gml): their
# walking frames, battle idles and text / dialogue faces. (Pink's battle idle is her fight's copy, spr_pk_pink_idle - make_pink.py;
# small Spamton's art is Chapter 3's own.)
for n in ('spr_seth_walk_down','spr_seth_walk_right','spr_seth_walk_up','spr_seth_walk_left','spr_seth_idle_r','spr_miniface_seth',
          'spr_enemy_orange_walk_down','spr_enemy_orange_walk_right','spr_enemy_orange_walk_up','spr_enemy_orange_walk_left','spr_enemy_orange_idle_base','spr_miniface_orange',
          'spr_enemy_green_walk','spr_enemy_green_walk_right','spr_enemy_green_behind','spr_enemy_green_wave_right','spr_miniface_green',
          'spr_yellow_walk_down','spr_yellow_walk_right','spr_yellow_walk_up','spr_yellow_walk_left','spr_yellow_idle','spr_miniface_yellow',
          'spr_blue_walk_r','spr_blue_walk_l','spr_blue_walk_back','spr_enemy_blue_ballet_r','spr_face_blue',
          'spr_pink_walk_down','spr_pink_walk_right','spr_pink_walk_up','spr_pink_walk_left'):
    add('c5','sprites',n)
json.dump(A,open(P,'w'),indent=1); print('skin assets in manifest')
