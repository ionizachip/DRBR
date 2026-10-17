"""Decide which assets need per-variant copies (rename map). Output build/assets.json"""
import json,collections,hashlib
W='/home/claude/work/'
V=json.load(open('/home/claude/scripts/knights.json'))['variants']   # list of {id,key,name,...}
keys=[v['key'] for v in V]           # index == variant id ; key 'base' is id 0
def rd(path,ncol):
    d={}
    for l in open(path,encoding='utf8'):
        p=l.rstrip('\n').split('\t')
        if p and p[0]:d[p[0]]=p[1:]
    return d
spr={k:rd(f'{W}sprh/{k}.tsv',1) for k in keys}
obj={k:rd(f'{W}inv/{k}/objects.tsv',3) for k in keys}
snd={k:rd(f'{W}inv/{k}/sounds.tsv',2) for k in keys}
import os
G=W+'gml/'
def ents(k):
    d=G+k+'/CodeEntries';return {f[:-4]:open(f'{d}/{f}',encoding='utf8',errors='replace').read() for f in os.listdir(d)}
T={k:ents(k) for k in keys}
import re
EV=r'(Create|Destroy|Alarm|Step|Collision|Keyboard|Mouse|Other|Draw|KeyPress|KeyRelease|Gesture|PreCreate|CleanUp|Trigger)'
allobj=sorted({n for k in keys for n in obj[k]},key=len,reverse=True)
def owner_of(entry):
    if not entry.startswith('gml_Object_'):return None
    rest=entry[len('gml_Object_'):]
    for n in allobj:
        if rest.startswith(n+'_') and re.match(EV+r'_',rest[len(n)+1:]):return n
    return None
# object event texts per variant
objev={k:collections.defaultdict(dict) for k in keys}
for k in keys:
    for e,t in T[k].items():
        o=owner_of(e)
        if o:objev[k][o][e[len('gml_Object_'+o+'_'):]]=t
def groups(defs):
    """defs: {variantkey: signature or None}. returns list of (sig,[keys]) ordered by lowest variant id"""
    g=collections.OrderedDict()
    for k in keys:
        if defs.get(k) is None:continue
        g.setdefault(defs[k],[]).append(k)
    return list(g.items())
rename={k:{} for k in keys}   # k -> {orig: newname}
manifest={'sprites':[],'sounds':[],'objects':[]}
def assign(kind,names,sigf):
    for n in sorted(names):
        defs={k:sigf(k,n) for k in keys}
        gs=groups(defs)
        base_has=defs.get('base') is not None
        if len(gs)==1:
            if not base_has:
                manifest[kind].append({'name':n,'new':n,'src':gs[0][1][0],'users':gs[0][1],'keep':False,'added':True})
            continue
        if len(gs)==0:continue
        for sig,ks in gs:
            first=ks[0]
            keep=(first=='base') or (not base_has and gs[0][0]==sig)
            newn=n if keep else f'{n}__v{keys.index(first)}'
            for k in ks:
                if newn!=n:rename[k][n]=newn
            if first!=ks[0]:pass
            if newn!=n or True:
                manifest[kind].append({'name':n,'new':newn,'src':first,'users':ks,'keep':keep})
assign('sprites',{n for k in keys for n in spr[k]},lambda k,n:spr[k].get(n,[None])[0])
assign('sounds',{n for k in keys for n in snd[k]},lambda k,n:('|'.join(snd[k][n][:2]) if n in snd[k] else None))
_RW={}
def _rw(k,t):
    # apply this variant's current rename map (sprites / sounds / already-decided object clones) so two variants that use the same NAME
    # for DIFFERENT art (or different clones) never share one object clone
    m=rename[k]
    if not m:return t
    key=(k,len(m))
    if key not in _RW:
        _RW[key]=re.compile(r'(?<![A-Za-z0-9_])('+'|'.join(re.escape(x) for x in sorted(m,key=len,reverse=True))+r')(?![A-Za-z0-9_])')
    return _RW[key].sub(lambda mo:m[mo.group(1)],t)
def objsig(k,n):
    if n not in obj[k]:return None
    ev={e:_rw(k,t) for e,t in objev[k].get(n,{}).items()}
    return _rw(k,obj[k][n][2])+'#'+hashlib.md5(json.dumps(ev,sort_keys=True).encode()).hexdigest()
# objects: rename when PROPS differ, or when added by several mods with different content
def objprops(k,n):return obj[k][n][2] if n in obj[k] else None
allo={n for k in keys for n in obj[k]}
# step 1 props-based grouping (existing objects with prop changes, added objects)
props_conf=set()
for n in allo:
    defs={k:objprops(k,n) for k in keys}
    if len({v for v in defs.values() if v is not None})>1:props_conf.add(n)
# added by exactly one mod (not in base): no rename needed
# added by several: compare event content
for n in allo:
    if obj['base'].get(n) is None:
        present=[k for k in keys if n in obj[k]]
        if len(present)>1:
            sigs={objsig(k,n) for k in present}
            if len(sigs)>1:props_conf.add(n)
_snap_r={k:dict(v) for k,v in rename.items()};_snap_m=list(manifest['objects'])
for _it in range(8):
    for k in keys:
        rename[k].clear();rename[k].update(_snap_r[k])
    manifest['objects']=list(_snap_m)
    _RW.clear()
    assign('objects',props_conf,lambda k,n:(objsig(k,n)))
    _state=json.dumps(rename,sort_keys=True)
    if _it and _state==_prev:break
    _prev=_state
    # next round: variants see the object clones decided so far
    _snap_obj=_state
print('object clone iterations:',_it+1)

# refs: sprites referenced by object props need mapping later; objects added (single mod) still must be copied
done={m['new'] for m in manifest['objects']}
for k in keys[1:]:
    for n in obj[k]:
        if n not in obj['base'] and n not in props_conf and n not in done:
            done.add(n);manifest['objects'].append({'name':n,'new':n,'src':k,'users':[k for kk in keys if n in obj[kk]],'keep':False,'added':True})
json.dump({'rename':rename,'manifest':manifest},open(W+'build/assets.json','w'),indent=1)
print('renames per variant:',{k:len(v) for k,v in rename.items()})
print('conflict objects:',sorted(props_conf))
for kd in manifest:
    print(kd,len(manifest[kd]),'to copy;',sum(1 for m in manifest[kd] if m['src']=='base'),'from base')
print([ (m['name'],m['new']) for m in manifest['sounds']])
print([ (m['name'],m['new'],m['users']) for m in manifest['objects']][:60])
