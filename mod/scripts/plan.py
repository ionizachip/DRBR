import os,json,collections,re
G='/home/claude/work/gml/'
V=['base','kaizo','elec','violet','thorn','cyan']   # variant ids 0..5
def load(n):
    d=f'{G}{n}/CodeEntries';return {f[:-4]:open(f'{d}/{f}',encoding='utf8',errors='replace').read() for f in os.listdir(d)}
T={v:load(v) for v in V}
names=set().union(*[set(T[v]) for v in V])
cls=collections.Counter();plan={}
for n in sorted(names):
    texts=[T[v].get(n) for v in V]
    groups=collections.defaultdict(list)
    for i,t in enumerate(texts):groups[t].append(i)
    if len(groups)==1:cls['same']+=1;continue
    kind='obj' if n.startswith('gml_Object_') else 'scr' if n.startswith('gml_GlobalScript_') else 'room' if n.startswith('gml_Room') else 'other'
    inbase=texts[0] is not None
    plan[n]={'kind':kind,'inbase':inbase,'groups':[[t is None,g] for t,g in groups.items() for t in [t]]}
    cls[(kind,'edited' if inbase else 'added',len(groups))]+=1
print(sum(1 for _ in names),'entries total;',cls['same'],'identical everywhere')
for k,v in sorted((k,v) for k,v in cls.items() if k!='same'):print(' ',k,v)
json.dump({n:{'kind':p['kind'],'inbase':p['inbase'],'groups':[g for _,g in p['groups']],'missing':[g for m,g in p['groups'] if m]} for n,p in plan.items()},open('/home/claude/work/merge/plan.json','w'))
