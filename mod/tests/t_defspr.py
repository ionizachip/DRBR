"""Every object whose default sprite is variant art must set that sprite (renamed per variant) in the merged Create event."""
import json,os,re,sys
W='/home/claude/work/'
M=W+'build/merged/'
ren=json.load(open(W+'build/assets.json'))['rename']
cand=json.load(open('/home/claude/scripts/variant_default_sprites.json'))
skip={'obj_npc_butler','obj_rabbick_enemy','titan_spawn_enemy','obj_screen_channel_change_sprite_test','obj_heartmarker'}
fails=0;n=0
for v,o,s,bs,has in cand:
    if o in skip or not has: continue
    n+=1
    want=ren[v].get(s,s)
    # split copy (object renamed per variant) or the shared object
    vid={'kaizo':1,'elec':2,'violet':3,'thorn':4,'cyan':5}[v]
    for name in (f'{o}__v{vid}',o):
        p=M+f'gml_Object_{name}_Create_0.gml'
        if os.path.exists(p): break
    else:
        print('FAIL no create',v,o);fails+=1;continue
    t=open(p,encoding='utf8').read()
    if f'sprite_index = {want};' not in t:
        print('FAIL',v,o,'expected',want,'in',os.path.basename(p));fails+=1
print('defspr checks',n,'fails',fails)
sys.exit(1 if fails else 0)
