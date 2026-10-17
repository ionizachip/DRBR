import sys,re,os,glob
from harness import *
def setup(variant,party):
    sim=make_sim()
    sim.define_object('obj_ch3_PTB02')
    for ev in ('Create_0','Step_0'):
        sim.load_file(M+'gml_Object_obj_ch3_PTB02_%s.gml'%ev,entry='gml_Object_obj_ch3_PTB02_%s'%ev)
    return sim
def DUM(sm):
    if not hasattr(sm,'_dum') or not sm.eval('instance_exists(%d)'%sm._dum):
        sm.define_object('obj_dummy') if not getattr(sm,'_dd',False) else None
        sm._dd=True
        sm._dum=sm.eval('instance_create(0,0,obj_dummy)')
    return sm._dum
def auto(sim,fn):
    """run fn, auto-mocking unknown functions/assets; returns (ok,err)"""
    for _ in range(400):
        _snap=sim.snapshot() if getattr(sim,'_snapauto',False) else None
        try:
            fn(); return True,None
        except Exception as e:
            m=str(e)
            if _snap is not None: sim.restore(_snap)
            # DRBR: a retry without a snapshot runs the frame's first part twice (a boss test counts these: none allowed)
            if _snap is None and getattr(sim,'retrylog',None) is not None: sim.retrylog.append(m[:200])
            r=re.search(r"global variable name '(\w+)'",m)
            if r:
                if getattr(sim,'autolog',None) is not None: sim.autolog.append(('global',r.group(1),m[:160]))
                sim.run('global.%s=0;'%r.group(1)); continue
            r=re.search(r'undefined function (\w+)',m)
            if r:
                nm=r.group(1)
                _p=B+'gml_GlobalScript_%s.gml'%nm
                if os.path.exists(_p) and getattr(sim,'_snapauto',False) and not getattr(sim,'_nobase',False):
                    try: sim.load_file(_p,entry='gml_GlobalScript_%s'%nm); continue
                    except Exception: pass
                sim.mock(nm,(lambda n:(lambda sm,*a: DUM(sm)))(nm)); continue
            r=re.search(r'(?:unknown|undefined) (?:variable|identifier|asset|name)[: ]+(\w+)',m)
            if r:
                try: sim.define_asset(r.group(1)); continue
                except Exception: pass
            r0=re.search(r'Variable (obj_\w+)\.(\w+) not set before reading it',m)
            if r0 and getattr(sim,'_snapauto',False) and not getattr(sim,'_nobase',False):
                _o=r0.group(1)
                if not hasattr(sim,'_baseloaded'): sim._baseloaded=set()
                if _o not in sim._baseloaded:
                    sim._baseloaded.add(_o); _n=0
                    for _p in glob.glob(B+'gml_Object_%s_*.gml'%_o):
                        _bn=os.path.basename(_p)
                        if os.path.exists(M+_bn): continue
                        try: sim.load_file(_p,entry=_bn[:-4]); _n+=1
                        except Exception: pass
                    if _n: continue
            r=re.search(r'Variable [\w]+\.(\w+) not set before reading it',m)
            if r:
                nm=r.group(1)
                if nm.startswith('obj_') or nm.startswith('DEVICE'):
                    sim.define_object(nm); continue
                if re.match(r'(spr|snd|room|bg|font|path|c|ch|mus|tile|shd|pal|ps)_',nm) or nm.startswith('spr') or nm.startswith('snd'):
                    try: sim.define_asset(nm); continue
                    except Exception: pass
            return False,m
    return False,'too many mocks'
if __name__=='__main__':
    sim=setup(0,[1,2,3])
    ok,err=auto(sim,lambda: sim.run('global.knight_variant=0; global.p=instance_create(0,0,obj_ch3_PTB02);'))
    print(ok,err)
