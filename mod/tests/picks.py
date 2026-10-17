import re,sys
G='/home/claude/work/gml/%s/CodeEntries/gml_Object_obj_knight_enemy_Other_10.gml'
def picks(v):
    t=open(G%v).read().split('\n')
    ph=None; out=[]; pt=None
    for ln in t:
        m=re.search(r'if \(phase == (\d+)\)',ln)
        if m: ph=int(m.group(1)); continue
        m=re.search(r'if \(phaseturn == (\d+)\)',ln)
        if m and ph is not None: pt=int(m.group(1)); out.append((ph,pt,'t')); continue
        m=re.search(r'if \(phase4turn == (\d+)\)',ln)
        if m: out.append((4,int(m.group(1)),'p4'))
    return sorted(set(out))
if __name__=='__main__':
    for v in ['base','elec','violet','thorn','cyan']:
        p=picks(v); print(v,len(p),p[:80])
