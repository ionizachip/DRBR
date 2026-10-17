"""Generate practice-mode rules for every knight fight (base/elec/thorn/cyan/violet), modelled on Kaizo's picker.
Writes rules/practice_rules.json. Names come from the attack ids/types actually used by each fight."""
import json,re,os,sys
GML='/home/claude/work/gml'
HERE=os.path.dirname(os.path.abspath(__file__))
TYPE={98:"Stars",99:"Splitters",102:"Sword Tunnel",103:"X Slashes",104:"Spinning Slashes",105:"Combination Attack",
 106:"Box Cluster",107:"Roaring",108:"Sword Hail",109:"Crescent Slash",151:"Tracking Swords",152:"Diamond Storm",
 153:"Sword Tunnel",154:"Sword Vortex",101:"Knightlines",100:"Crescent Slash",155:"Epic Orbs",999:"Thorn Flurry",
 988:"Children",958:"Pseudo Roaring",666:"Lightsplitter",777:"Quickstorm",97:"Quickslash",1511:"Tracking Swords",
 15111:"Tracking Swords",1533:"Sword Tunnel",1044:"Spinning Slashes",2000:"Roaring Flames"}
# per-variant id overrides where the first dc.type is not the attack's real identity
OVR={
 'base':{7:"Combination Attack",16:"Slashes + Swords",15:"Vortex + Swords"},
 'elec':{7:"Combination Attack",16:"Slashes + Swords",15:"Tracking Swords",51:"Alternating Swords",
         50:"Tunnel + Swords",54:"Tunnel + Swords",52:"Sword Vortex",53:"Epic Orbs"},
 'thorn':{1:"Stars",2:"Splitters",6:"Box Cluster",7:"Spinning Slashes",15:"Sword Tunnel",11:"Spinning Slashes",
          20:"Quickslash",22:"Splitters",25:"Box Cluster",4:"Thorn Flurry",5:"Tracking Swords",16:"Spinning Slashes"},
 'cyan':{0:"Crescent Slash",1:"Stars",2:"Splitters",3:"Sword Tunnel",4:"X Slashes",6:"Box Cluster",7:"Roaring",
         11:"X Slashes",14:"Tracking Swords",15:"Tracking Swords",16:"Spinning Slashes",100:"Tracking Swords"},
 'violet':{0:"Crescent Slash",3:"Crescent Slash",10:"Crescent Slash",1:"Stars",2:"Splitters",4:"Tracking Swords",
           6:"Fountains",7:"Sword Vortex",12:"Diamond Eruption",13:"Sword Tunnel",15:"Sword Vortex",17:"Tracking Swords",
           20:"Tracking Swords",32:"Splitters",70:"Crescent Slash",71:"Sword Tunnel",5:"Spinning Slashes"},
}
THR={'base':0.8,'elec':0.8,'cyan':0.8,'thorn':0.5,'violet':'knight_hp_threshold'}
def rd(v,e): return open(f'{GML}/{v}/CodeEntries/{e}.gml',encoding='utf8').read()
def id_names(v):
    t=rd(v,'gml_Object_obj_knight_enemy_Step_0')
    i=t.index('if (rtimer == 12)'); seg=t[i:i+18000]
    parts=re.split(r'(?:else )?if \(myattackchoice == (-?\d+)\)',seg)
    out={}
    for k in range(1,len(parts),2):
        n=int(parts[k])
        if n in out: continue
        body=parts[k+1].split('else if (myattackchoice')[0]
        ty=[int(x) for x in re.findall(r'dc\.type = (\d+)',body)]
        nm=[]
        for x in ty:
            s=TYPE.get(x,'Attack')
            if s not in nm: nm.append(s)
        s=nm[0] if nm else 'Attack'
        if len(nm)>1 and 'Tracking Swords' in nm[1:]: s+=' + Swords'
        out[n]=s
    out.update(OVR.get(v,{}))
    return out
def parse(v,ent):
    t=rd(v,ent); names=id_names(v)
    res={}; ph=None; pt=None
    for l in t.split('\n'):
        m=re.match(r'\s*if \(phase == (\d+)\)\s*$',l)
        if m: ph=int(m.group(1)); pt=None; continue
        m=re.match(r'\s*if \(phaseturn == (\d+)\)\s*$',l)
        if m: pt=int(m.group(1)); continue
        if ph in (1,2,3) and pt is not None and pt<50:
            e=res.setdefault(ph,{}).setdefault(pt,{'id':None,'comment':None,'trans':False})
            m=re.search(r'myattackchoice = (-?\d+);',l)
            if m: e['id']=int(m.group(1))
            m=re.search(r'comment = "([^"]*)";',l)
            if m: e['comment']=m.group(1)
            if re.match(r'\s*phase = \d;',l): e['trans']=True
    out=[]; seen={}
    for ph in sorted(res):
        turns=sorted(res[ph]); end=None
        for tn in turns:
            if res[ph][tn]['trans']: end=tn; break
        for tn in turns:
            e=res[ph][tn]
            if e['id'] is None: continue
            nm=e['comment'] or names.get(e['id'],'Attack %d'%e['id'])
            out.append([ph,tn,nm,bool(end is not None and tn>end)])
    return out,names
def number(lst):
    # number repeated names in order of appearance: "Stars 1", "Stars 2"... (kept if the name came from a mod comment)
    cnt={}
    for x in lst: cnt[x[2]]=cnt.get(x[2],0)+1
    seen={}
    for x in lst:
        if cnt[x[2]]>1 and not re.search(r'\d$',x[2]):
            seen[x[2]]=seen.get(x[2],0)+1
            x[2]=x[2]+' '+str(seen[x[2]])
    return lst
def gml_list(lst):
    return '['+','.join('[%d,%d,"%s"]'%(p,t,n+(' (unused)' if u else '')) for p,t,n,u in lst)+']'
def build():
    R=[]; info={}
    SC=["solo","dup","noelle","nokris"]
    for v in ['base','elec','thorn','cyan','violet']:
        ent10='gml_Object_obj_knight_enemy_Other_10'
        la,names=parse(v,ent10); la=number(la)
        p4=[]
        # phase 4 lead-in attack and Roaring
        p4n=names.get(24 if v=='thorn' else 5,'Spinning Slashes')
        p4=[[4,1,p4n+' (Phase 4)',False],[4,3,'Roaring',False]]
        la=la+p4
        lists={'a':la}
        if v=='violet':
            lb,_=parse(v,'gml_Object_obj_knight_enemy_Other_19'); lb=number(lb)
            lb=lb+[[4,1,'Spinning Slashes (Phase 4)',False],[4,3,'Roaring',False]]
            lists['b']=lb
        info[v]=lists
        if v=='violet':
            plist='(((global.flag[456] != 0) && !(global.tempflag[30] >= 1)) ? %s : %s)'%(gml_list(lists['b']),gml_list(lists['a']))
        else:
            plist=gml_list(la)
        R.append({"id":"P1-create-"+v,"variants":[v],"entry":"gml_Object_obj_knight_enemy_Create_0","find":"overrideAttack = 0;\n",
          "replace":"overrideAttack = 0;\npracticemode = (variable_global_exists(\"kaizo_practice\") && global.kaizo_practice) ? 1 : 0;\nprac_sel = 0;\nif (!variable_instance_exists(id, \"difficulty\"))\n    difficulty = 0;\nprac_list = %s;\n"%plist,
          "why":"Practice mode (hub option): named attack picker list of (phase, turn).","scenarios":SC})
        # Other_10 forcing
        if v=='violet':
            find="if (phase != 4 && practice == false)\n{\n    turn++;\n    phaseturn++;\n}\n"
            anchor=find
        else:
            find="if (scr_debug() && overrideAttack > 0)\n{\n    phaseturn = overrideAttack;\n}\n"
        # for violet, phase4turn is not advanced while practicemode (guard patched below), so use phaseturn directly
        p4expr = "phaseturn" if v=='violet' else "phaseturn - 1"
        force="if (practicemode)\n{\n    phase = prac_list[prac_sel][0];\n    phaseturn = prac_list[prac_sel][1];\n    rotatingslash3used = false;\n    haveusedroaring = false;\n    phase4turn = 0;\n    if (phase == 4)\n        phase4turn = %s;\n}\n"%p4expr
        ents=[ent10]+(['gml_Object_obj_knight_enemy_Other_19'] if v=='violet' else [])
        for e in ents:
            if v=='violet':
                f=find
            else: f=find
            R.append({"id":"P2-force-%s-%s"%(v,e.split('_')[-2]+e.split('_')[-1]),"variants":[v],"entry":e,"find":f,"replace":f+force,
              "why":"Practice: force the picked phase/turn each enemy turn.","scenarios":SC})
        if v=='violet':
            for e in ents:
                R.append({"id":"P2b-noguard-%s"%e.split('_')[-1],"variants":[v],"entry":e,"regex":True,
                  "find":r"if \(practice == false\)","replace":"if (practice == false && !practicemode)",
                  "why":"Practice: the fight's own phase-change/cutscene steps must not run while practising.","scenarios":SC})
        th=THR[v]
        R.append({"id":"P3-step-"+v,"variants":[v],"entry":"gml_Object_obj_knight_enemy_Step_0",
          "find":"if (global.monsterhp[myself] <= (global.monstermaxhp[myself] * %s))\n{\n    global.tempflag[96] = 1;\n}\n"%th,
          "replace":"if (practicemode)\n{\n    global.monsterhp[myself] = global.monstermaxhp[myself];\n    for (var _pi = 1; _pi < min(array_length(global.hp), array_length(global.maxhp)); _pi++)\n    {\n        if (scr_havechar(_pi))\n            global.hp[_pi] = global.maxhp[_pi] * 2;\n    }\n}\nif (global.monsterhp[myself] <= (global.monstermaxhp[myself] * %s))\n{\n    global.tempflag[96] = 1;\n}\n"%th,
          "why":"Practice: Knight never loses HP, party never dies.","scenarios":SC})
        R.append({"id":"P4-battlecontroller-"+v,"variants":[v],"entry":"gml_Object_obj_battlecontroller_Step_0",
          "find":"        var can_input = true;\n",
          "replace":"        var can_input = true;\n        with (obj_knight_enemy)\n        {\n            if (variable_instance_exists(id, \"practicemode\") && practicemode)\n                can_input = false;\n        }\n",
          "why":"Practice: the normal command menu is replaced by the attack picker.","scenarios":SC})
    return R,info
if __name__=='__main__':
    R,info=build()
    json.dump(R,open(HERE+'/rules/practice_rules.json','w'),indent=1)
    json.dump({v:{k:l for k,l in d.items()} for v,d in info.items()},open('/tmp/prac_info.json','w'),indent=1)
    for v,d in info.items():
        for k,l in d.items():
            print('==',v,k)
            for x in l: print('  ',x)
