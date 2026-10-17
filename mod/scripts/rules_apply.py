"""Apply audited party-compatibility patch rules to per-variant source text (before literal normalisation)."""
import json,re,os
K=['base','kaizo','elec','violet','thorn','cyan']
RD=os.path.join(os.path.dirname(os.path.abspath(__file__)),'rules')
ORDER=['kaizo_violet_rules.json','cyan_elec_thorn_base_rules.json','engine_rules.json','hub_rules.json','practice_rules.json','weird_route_rules.json','noelle_act_rules.json','down_guard_rules.json','b37_rules.json','b38_rules.json','b39_rules.json','b41_rules.json']
DISABLE=set(json.load(open(RD+'/disabled.json'))) if os.path.exists(RD+'/disabled.json') else set()
def load():
    R=[]
    for f in ORDER:
        p=RD+'/'+f
        if not os.path.exists(p):continue
        for x in json.load(open(p)):
            x['variants']=[K[v] if isinstance(v,int) else v for v in x['variants']]
            if x['id'] in DISABLE:continue
            R.append(x)
    return R
def apply_all(T,report=None):
    """T: {variant:{entry:text}} modified in place. returns list of problems."""
    probs=[];applied=[]
    _xd=os.path.join(os.path.dirname(os.path.abspath(__file__)),"extra_entries")
    if os.path.exists(_xd+"/practice_Draw_64.gml"):
        for _v in ("base","elec","thorn","cyan","violet"):
            if _v in T:
                T[_v]["gml_Object_obj_knight_enemy_Draw_64"]=open(_xd+"/practice_Draw_64.gml",encoding="utf8").read()
    for r in load():
        for v in r['variants']:
            e=r['entry']
            if v not in T or e not in T[v]:
                probs.append((r['id'],v,'entry missing'));continue
            t=T[v][e]
            if r.get('regex'):
                n=len(re.findall(r['find'],t))
                exp=r.get('count',r.get('expected_count_per_variant'))
                if n==0 or (exp is not None and n!=exp):probs.append((r['id'],v,f'regex count {n} expected {exp}'));continue
                t2=re.sub(r['find'],r['replace'],t)
            else:
                n=t.count(r['find'])
                if n!=1:probs.append((r['id'],v,f'find count {n}'));continue
                t2=t.replace(r['find'],r['replace'],1)
            T[v][e]=t2;applied.append((r['id'],v))
    return applied,probs
