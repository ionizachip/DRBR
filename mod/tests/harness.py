import sys,os,re
sys.path.insert(0,'/home/claude/gmlsim')
from gmlsim import Sim,GMError,Fault
import os
M=os.environ.get('KH_MERGED','/home/claude/work/build/merged/')
B='/home/claude/work/gml/base/CodeEntries/'
class Env:
    pass
_BOBJS=[]
_BOSS=[]
def _boss_objs():
    """DRBR (update 9): the imported bosses' objects, sprites and sounds (build/assets.json, the entries with a "boss" key). The
    game has them from the start and the hub's code names them (the boss list: kbr_enc_def_gerson's objs) - update 10: the
    menu / network harnesses define them too (they crashed on obj_hj_spear before)"""
    if not _BOSS:
        import json
        try:
            A=json.load(open('/home/claude/work/build/assets.json'))['manifest']
        except Exception:
            A={}
        # (Jevil's, update 8, have no "boss" key: every object the build adds counts)
        objs=[m['new'] for m in A.get('objects',[]) if 'boss' in m or m.get('added')]
        # and the bosses' own driver objects the boss makers add with their code (make_spamton.py: obj_sn_ysoul ...)
        import glob as _g
        for _p in sorted(_g.glob(M+'gml_Object_obj_*.gml')):
            _m=re.match(r'gml_Object_(obj_(?:jv|hj|fl|sn|pk|drbr)_\w+?)_(?:Create|Step|Draw|Destroy|Alarm|Other|CleanUp|Collision|PreCreate|KeyPress|Keyboard|KeyRelease|Mouse)_',os.path.basename(_p))
            if _m and _m.group(1) not in objs: objs.append(_m.group(1))
        _BOSS.append((objs,[m['new'] for k in ('sprites','sounds') for m in A.get(k,[]) if 'boss' in m or m.get('added')]))
    return _BOSS[0]
def _battle_objs():
    if not _BOBJS:
        _kc=open(M+'gml_GlobalScript_knight_core.gml',encoding='utf8').read()
        _l=['obj_bulletparent','obj_bulletgenparent','obj_dbulletcontroller','obj_monsterparent']
        for _fn in ('kbr_atk_objs','kbr_split_objs'):
            _m=re.search(r'function %s\(\)\s*\{\s*return \[([^\]]*)\]'%_fn,_kc)
            if _m: _l+=[x.strip() for x in _m.group(1).split(',') if x.strip()]
        _BOBJS.extend(dict.fromkeys(_l))
    return _BOBJS
_RT=[]
def _rt_tables():
    """build 47, the round trip: the built data.win's own numbers for its objects / sprites / sounds / fonts / paths ...
    (assetidx.csx -> <rt folder>_assets.tsv). The decompiler writes an asset as its NUMBER where it cannot know the type
    (_src = obj_herokris comes back as _src = 1410): the emulator gives every asset the data.win's number, so such a
    number means the same thing here as in the game."""
    if not _RT:
        p=os.environ.get('KH_ASSETS') or (M.rstrip('/')+'_assets.tsv')
        T={'obj':{},'asset':{}}
        if os.path.exists(p):
            for ln in open(p,encoding='utf8'):
                k,n,i=ln.rstrip('\n').split('\t')
                if k=='obj': T['obj'][n]=int(i)
                elif k!='room': T['asset'].setdefault(n,int(i))
        _RT.append(T)
    return _RT[0]
def _rt_numbers(sim):
    T=_rt_tables()
    if not T['obj']:
        return
    od=sim.define_object
    cnt=[30000]
    def dobj(name,parent=None,persistent=None,sprite=None,index=None,**kw):
        if name not in sim.objects:
            if name in T['obj']:
                index=T['obj'][name]
            elif index is None:
                # an object of the tests only (not in data.win): out of the data.win's range
                index=cnt[0]; cnt[0]+=1
        return od(name,parent=parent,persistent=persistent,sprite=sprite,index=index,**kw)
    sim.define_object=dobj
    da=sim.define_asset
    def dasset(name):
        if name not in sim.assets and name in T['asset']:
            sim.assets[name]=T['asset'][name]
            return sim.assets[name]
        return da(name)
    sim.define_asset=dasset
    sim.asset_index=dasset
def obj_index_table():
    """the object numbers the fight harnesses give the objects (the game's code has some as numbers): the data.win's of
    the round trip when that table is there (build 47), else the merged build's list in idx/merged.tsv"""
    if os.environ.get('KH_MERGED'):
        T=_rt_tables()
        if T['obj']:
            return dict(T['obj'])
    out={}
    for _ln in open('/home/claude/work/idx/merged.tsv'):
        _p=_ln.rstrip('\n').split('\t')
        if len(_p)==3 and _p[0]=='obj': out[_p[2]]=int(_p[1])
    return out
_GAME_FN=[]
def game_functions():
    """DRBR 1.0.4: every global function name of the built game - Chapter 3's (its SCPT chunk) and DRBR's own (the templates);
    cached in idx/game_functions.txt (rebuilt when a template is newer)"""
    if not _GAME_FN:
        import glob as _g
        c='/home/claude/work/idx/game_functions.txt'
        tp=_g.glob('/home/claude/scripts/gml_templates_v6/*.gml')
        if not os.path.exists(c) or any(os.path.getmtime(x)>os.path.getmtime(c) for x in tp):
            sys.path.insert(0,'/home/claude/scripts')
            import fnclash
            open(c,'w').write('\n'.join(sorted(fnclash.target_functions()))+'\n')
        _GAME_FN.append(set(l.strip() for l in open(c) if l.strip()))
    return _GAME_FN[0]
def make_sim(seed=1,load_vanilla=('scr_flag_set','scr_ini_chapter')):
    sim=Sim(seed=seed)
    # DRBR 1.0.4: a read of an instance variable named like one of the game's global functions is an error here, as it is a
    # bug in the game (the compiled code reads the FUNCTION there: Jevil's Devilsknives, centerx / centery). KH_FNSHADOW=0: off
    if os.environ.get('KH_FNSHADOW','1')!='0': sim.fn_shadow_check=game_functions()
    # DRBR 1.0.4: and a sprite draw with an argument that is not a number stops the test as it stops the game (Spamton NEO's
    # playback sprite, looked up through Chapter 3's map: undefined). KH_STRICTDRAW=0: off
    if os.environ.get('KH_STRICTDRAW','1')!='0': sim.strict_draw=True
    if os.environ.get('KH_MERGED'):
        # build 46, the round trip (code decompiled from the built data.win): the decompiler writes a 0 compared with a
        # sprite as the name of sprite 0 (IMAGE_LOGO in Chapter 3); the same value
        sim.define_const('IMAGE_LOGO',0)
        _rt_numbers(sim)
    sim.load_file(M+'gml_GlobalScript_knight_core.gml',entry='gml_GlobalScript_knight_core')
    # 1.0.1: the KF Song Pack's own script (kf_song_path ...) - the game has it; the song checks reach it
    if os.path.exists(M+'gml_GlobalScript_scr_kf_song.gml'):
        sim.load_file(M+'gml_GlobalScript_scr_kf_song.gml',entry='gml_GlobalScript_scr_kf_song')
    for n in ('kaizo_set_music',):
        pass
    import glob
    # objects used by the hub
    for o in ['obj_knight_ctrl','obj_knight_menu','obj_knight_prompt','obj_battlecontroller','obj_knight_enemy','obj_time','obj_gamecontroller','obj_border_controller','obj_mainchara',
              'obj_herokris','obj_herosusie','obj_heroralsei']:
        sim.define_object(o,persistent=(o in ('obj_knight_ctrl','obj_time','obj_gamecontroller','obj_border_controller')))
    # battle objects the hub code names (high indices so they never collide with the game's own object numbers used by emu_atk)
    for _i,o in enumerate(['obj_heart','obj_knight_twin','obj_knight_twin_bullet','obj_knight_roaring2','obj_growtangle','obj_knight_herocc']):
        if o not in sim.objects: sim.define_object(o,index=90000+_i)
    for o,p in [('obj_knight_ghost_kris','obj_herokris'),('obj_knight_ghost_susie','obj_herosusie'),('obj_knight_ghost_ralsei','obj_heroralsei')]:
        sim.define_object(o,parent=p)
    # build 45: the battle objects the online code clears when a match ends for this game (kbr_end_clean / kbr_cut). They always
    # exist in the game; the menu / network harnesses run no battle, so they are made here, empty (high numbers, as above)
    for _i,o in enumerate(_battle_objs()):
        if o not in sim.objects: sim.define_object(o,index=96000+_i)
    _bo,_ba=_boss_objs()
    for _i,o in enumerate(_bo):
        if o not in sim.objects: sim.define_object(o,index=98000+_i)
    # update 10: and every object of Chapter 3 itself (idx/objparents.tsv) - the bosses' clean-up names the game's own helpers
    # (with (obj_move_to_point) ...), which the real game always has; names only (no instances, no parents)
    # (DRBR 1.0.1: numbered from 60000 - from 110000 they were in the instances' range (100000 up), so the emulator took
    # obj_actor for an instance: instance_number(obj_actor) was 0 with stand-ins made - t_kmenu's 3 failures)
    for _i,_ln in enumerate(open('/home/claude/work/idx/objparents.tsv',encoding='utf8')):
        _p=_ln.rstrip('\n').split('\t')
        if len(_p)>=2 and _p[1] and _p[1] not in sim.objects: sim.define_object(_p[1],index=60000+_i)
    for a in _ba:
        try: sim.define_asset(a)
        except Exception: pass
    for p in sorted([p for p in glob.glob(M+'gml_Object_obj_knight_*.gml') if re.search(r'obj_knight_(menu|prompt|ctrl|ghost|saov)',p)]):
        sim.load_file(p,entry=os.path.basename(p)[:-4])
    for r in ('room_dw_snow_zone','room_town_krisyard_dark'):
        sim.define_room(r)
    for a in ['spr_heart','spr_dodgeheart','spr_morearrow','spr_equipchar_ch2','spr_dmenu_captions','spr_darkequipbt','spr_darktalkbt','spr_darktechbt','spr_darkitembt','spr_darkconfigbt','spr_heart_harrows',
              'snd_menumove','snd_select','snd_cantselect','snd_smallswing','snd_hurt1','c_black']:
        try: sim.define_asset(a)
        except Exception: pass
    # input
    sim.inp={'up':0,'down':0,'left':0,'right':0,'ok':0,'back':0,'alt':0}
    for n,k in [('up_p','up'),('down_p','down'),('left_p','left'),('right_p','right'),('button1_p','ok'),('button2_p','back'),('button3_p','alt')]:
        sim.mock(n,(lambda kk:(lambda s,*a:s.inp[kk]))(k))
    # held keys (the game's own button*_h / *_h scripts; build 45's online match reads them): held = pressed this frame here
    for n,k in [('up_h','up'),('down_h','down'),('left_h','left'),('right_h','right'),('button1_h','ok'),('button2_h','back'),('button3_h','alt')]:
        if n not in getattr(sim,'mocks',{}):
            sim.mock(n,(lambda kk:(lambda s,*a:s.inp[kk]))(k))
    for n in ['scr_refreshchar','scr_darkbox','scr_84_set_draw_font','draw_item_icon','snd_play','snd_free_all','snd_stop_all','ossafe_savedata_save','snd_volume']:
        sim.mock(n,0)
    sim.load_file(B+'gml_GlobalScript_scr_spellinfo.gml',entry='gml_GlobalScript_scr_spellinfo')
    for _n in ('scr_weaponinfo','scr_armorinfo','scr_weaponinfo_mine','scr_armorinfo_mine'):
        sim.load_file(B+'gml_GlobalScript_%s.gml'%_n,entry='gml_GlobalScript_%s'%_n)
    sim.load_source('gml_GlobalScript_i_ex','function i_ex(_a)\n{\n    return instance_exists(_a);\n}\n')
    sim.mock('stringsetloc',lambda s,a,b=None:a)
    sim.mock('stringset',lambda s,a,*r:a)
    sim.flags_set=[]
    sim.mock('scr_flag_set',lambda s,i,v:(sim.run('global.flag[%d] = %s;'%(int(i),repr(v)))) or 0)
    sim.mock('scr_ini_chapter',lambda s,*a:'CH3')
    sim.mock('kaizo_set_music',lambda s,f:'kaizoknight.ogg')
    g=dict(chapter=3,char=[1,2,3],hp=[0,90,110,140,100],maxhp=[0,90,110,140,100],at=[0,10,12,8,5],df=[0,2,3,1,1],mag=[0,1,2,9,4],
           item=[1,2,3,0,0,0,0,0,0,0,0,0,0],tension=25,plot=320,orighpkris=0,orighpsusie=0,orighpralsei=0,
           interact=0,launcher=False,filechoice=0,charweapon=[0,1,2,3,4,0],chararmor1=[0,1,2,3,4,0],chararmor2=[0,0,0,0,0,0],maxtension=250)
    sim.define_globals(**g)
    sim.ensure_script('knight_count')
    sim.run_global_inits()
    sim.run('global.flag = []; for (var i = 0; i < 1300; i++) global.flag[i] = 0; global.flag[16] = 1; global.flag[456] = 0;'
            'global.tempflag = []; for (var i = 0; i < 100; i++) global.tempflag[i] = 0;'
            'global.spell = []; for (var c = 0; c < 5; c++) { for (var s = 0; s < 12; s++) global.spell[c][s] = 0; } global.spell[1][0] = 1; global.spell[2][0] = 4; global.spell[3][0] = 2;'
            'global.itembolts = []; global.itemgrazeamt = []; global.itemgrazesize = []; global.itemat = []; global.itemdf = []; global.itemmag = []; for (var c = 0; c < 5; c++) { global.itemat[c] = [0,0,0]; global.itembolts[c] = [0,0,0]; global.itemgrazeamt[c] = [0,0,0]; global.itemgrazesize[c] = [0,0,0]; global.itemdf[c] = [0,0,0]; global.itemmag[c] = [0,0,0]; }')
    os.makedirs(sim.sandbox,exist_ok=True)
    return sim
