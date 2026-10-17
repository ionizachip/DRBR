"""Runtime sprite monitor: run every practice-list attack of a variant in the GML simulator (real merged code) and flag any instance whose
sprite_index is the BASE-art name of a sprite the variant replaces (i.e. the normal knight / normal bullet showing in a modded fight).
usage: t_sprmon.py KEY [frames] [WALL env seconds]"""
import sys,os,re,json,time,collections
from emu_atk import *
import emu_atk as E
W='/home/claude/work/'
KEYS_={'base':0,'kaizo':1,'elec':2,'violet':3,'thorn':4,'cyan':5}
REN=json.load(open(W+'build/assets.json'))['rename']
def props(path):
    return {l.split('\t')[0]:l.rstrip('\n').split('\t')[1:] for l in open(path) if '\t' in l}
PM=props(W+'props_merged.txt')
PV={k:props(W+f'props_{k}.txt') for k in KEYS_}
cur={'key':None}
VIOL=collections.OrderedDict()
def default_sprite(o,key):
    m=re.match(r'(.+)__v(\d)$',o)
    if m:
        v=[k for k,i in KEYS_.items() if i==int(m.group(2))][0]
        s=PV[v].get(m.group(1))
        return REN[v].get(s[0],s[0]) if s and s[0] else None
    p=PM.get(o)
    return p[0] if p and p[0] else None
orig_mk=E.mk
def mk2(key,party):
    sim=orig_mk(key,party)
    cur['key']=key; cur['seen']=collections.Counter()
    for nm,od in sim.objects.items():
        s=default_sprite(nm,key)
        if s:
            try: od.sprite=sim.define_asset(s)
            except Exception: pass
    for _m in json.load(open(W+'build/assets.json'))['manifest']['sounds']:
        for _n in (_m['name'],_m['new']): sim.define_asset(_n)
    rev={v:k for k,v in sim.assets.items()}
    cur['rev']=rev; cur['sim']=sim
    st=sim.step
    n=[0]
    def step2(*a,**k):
        r=st(*a,**k)
        n[0]+=1
        if n[0]%3==0:
            bad=REN[key]
            rv={v:k2 for k2,v in sim.assets.items()}
            for inst in list(sim.instances.values()):
                si=inst.vars.get('sprite_index')
                nm=rv.get(si) if isinstance(si,int) else None
                if nm and nm in bad: cur['seen'][(inst.obj,nm)]+=1
        return r
    if os.environ.get('SPRSELFTEST'):
        sim.define_object('obj_zz'); sim.objects['obj_zz'].sprite=sim.define_asset('spr_roaringknight_point_ol')
        _first=[True]
        _st2=step2
        def step3(*a,**k):
            if not any(i.obj=='obj_zz' for i in sim.instances.values()):
                sim.run('instance_create(0,0,obj_zz);')
            return _st2(*a,**k)
        sim.step=step3
        return sim
    sim.step=step2
    return sim
E.mk=mk2
if __name__=='__main__':
    key=sys.argv[1]; frames=int(sys.argv[2]) if len(sys.argv)>2 else 500
    if key=='kaizo':
        names=re.findall(r'^\s*(atk_\w+) = ',open(W+'gml/kaizo/CodeEntries/gml_Object_obj_knight_enemy_Other_24.gml').read(),re.M)
        pts=[(1,1,n) for n in names]
    else:
        t=open(W+'build/merged/gml_Object_obj_knight_enemy_Create_0.gml').read()
        cases={2:'case 2:',3:'case 3:',4:'case 4:',5:'case 5:',0:'default:'}
        a=t.index(cases[KEYS_[key]])
        src=t[a:a+60000]
        L=re.search(r'prac_list = (.*?);\n',src).group(1)
        pts=sorted({(int(x),int(y),None) for x,y in re.findall(r'\[(\d+),(\d+),"',L)})
        os.environ.setdefault('PRAC','1')
    total=0
    only=os.environ.get('ONLY')
    for ph,tn,nm in pts:
        if only and only not in str(nm) and only!=f'{ph}:{tn}': continue
        t0=time.time()
        r=attack(key,[1,2,3],ph,tn,frames=frames,name=nm)
        seen=cur['seen']
        total+=len(seen)
        print(key,ph,tn,nm or '',r[0],(r[1] or '')[:60],'| BASE-ART:',dict(seen) if seen else 'none',round(time.time()-t0,1),flush=True)
    print('SPRMON',key,'attacks',len(pts),'violating (obj,sprite) pairs',total)
