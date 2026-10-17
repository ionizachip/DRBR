"""Add the Chapter 5 FireShock donor assets (from data_2.win, loaded as MODS_DIR/c5.win) to build/assets.json. Idempotent."""
import json,sys
P='/home/claude/work/build/assets.json'
A=json.load(open(P));M=A['manifest']
def add(kind,name,new=None,dx=0,dy=0):
    new=new or name
    for m in M[kind]:
        if m['new']==new and m['src']=='c5':
            m['name']=name; m['dx']=dx; m['dy']=dy; return
    M[kind].append({'name':name,'new':new,'src':'c5','users':['c5'],'keep':False,'added':True,'dx':dx,'dy':dy})
for n in ('spr_firespell_flame','spr_firespell_smallflame','spr_ralsei_spell_fireball_right','spr_spell_fireball'): add('sprites',n)
add('sounds','snd_firespell')
for n in ('obj_firespell','obj_firespell_hexagon'): add('objects',n)
# build 50: FLOWERY as a playable look (walking, UI, battle poses). The battle copies (spr_knfl_*) are moved up 14 px (his
# standing sprite is 60 px tall, Noelle's battle sprite 46: he plays in her slot) so his feet stand where hers do; the walking ones stay as they are
for n in ('spr_flowery_walk_down','spr_flowery_walk_up','spr_flowery_walk_left','spr_flowery_walk_right','spr_headflowery','spr_bnameflowery',
          'spr_ja_bnameflowery','spr_flowery_equipchar','spr_dmenu_equip_flowery','spr_dmenu_items_floweryhead','spr_face_flowery'):
    add('sprites',n)
# his battle poses and moves are all fl_atlas sprites now (make_fl_atlas.py: mirrored where Chapter 5 faced left, every frame
# anchored on his body and feet, lined up with Noelle's): the copies of earlier build-50 versions leave the manifest
for n in ('spr_flowery_crescent_only','spr_omegaflowery_explosion_a','spr_omegaflowery_explosion_b','spr_omegaflowery_explosion_c',
          'spr_omegaflowery_heart'):
    add('sprites',n)
_gone=('spr_omegaflowery_idle','spr_omegaflowery_powerup','spr_omegaflowery_pose','spr_omegaflowery_jarona','spr_omegaflowery_punch',
       'spr_omegaflowery_windup','spr_omegaflowery_clash','spr_omegaflowery_deflect','spr_omegaflowery_hurt','spr_omegaflowery_axekick',
       'spr_omegaflowery_flashkick','spr_flowery_kick','spr_flowery_kick_crescent','spr_flowery_pose','spr_flowery_spin_to_idle')
M['sprites']=[m for m in M['sprites'] if not (m.get('src')=='c5' and (m['new'].startswith('spr_knfl_') or m['new'] in _gone))]
# PRISM RUSH's power-up: the other flowers of Chapter 5 (the ones his fight brings in: Aqua, Seth - the purple one -, Orange,
# Green, Blue, Yellow, and Pink) around him, giving him their power; the bell sparkles and the flower sparkles;
# HONEY KISS's blown petals (his blow kiss: spr_spin_petal)
M['sprites']=[m for m in M['sprites'] if not (m.get('src')=='c5' and m['new'].endswith('_power'))]
# PRISM RUSH / OMEGA: Chapter 5's six Omega flowers (obj_plat_finalflowery's draw_ghost: a main sprite and its overlay, _o)
for n in ('spr_omegaf_green','spr_omegaf_green_o','spr_omegaf_aqua','spr_omegaf_aqua_o','spr_omegaf_yellow','spr_omegaf_yellow_o',
          'spr_omegaf_blue','spr_omegaf_blue_o','spr_omegaf_seth','spr_omegaf_seth_o','spr_omegaf_orange','spr_omegaf_orange_o'):
    add('sprites',n)
for n in ('spr_enemy_aqua_idle','spr_seth_idle_serious_flowery','spr_enemy_orange_idle_base','spr_green_together','spr_enemy_blue_ballet',
          'spr_yellow_idle','spr_pink_sing_idle','spr_sparestar_anim','spr_bellsparkle','spr_spin_petal'):
    add('sprites',n)
for n in ('snd_japanese_yo_hit2','snd_flowery_power_up','snd_strongwind_loop','snd_flowery_voicenoise_1','snd_flowery_voicenoise_2','snd_flowery_voicenoise_3'):
    add('sounds',n)
for n in ['flowers_blooms_in_your_heart', 'give_to_you', 'great_style', 'hah', 'heh_it_s_my_jarona', 'hereicome', 'hereicomesanfrandisc', 'hereicomesanfrandisco_strong', 'hey', 'heyguys', 'hoo', 'huh', 'im_falling', 'its_all_yours', 'itsmeflowery', 'jarona1', 'jarona2', 'jarona3', 'jarona4', 'leaf_it_to_me', 'lend_me_your_power', 'nonono', 'omega_flowery', 'prism_blow', 'sanfran', 'smile_again', 'spiral_dance', 'take_that', 'thatsgreat', 'try_my_flavor', 'with_your_powers_combined', 'wow', 'yes', 'youre_a_hero', 'sorryabouttheguy', 'last_jarona', 'powering_up']:
    add('sounds','snd_flowery_voiceclip_'+n)
json.dump(A,open(P,'w'),indent=1); print('c5 assets in manifest')
