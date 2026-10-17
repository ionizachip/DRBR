"""Merge per-variant GML into one runtime-switched set. Output: build/merged/*.gml + build/merge_report.json"""
import os,re,json,collections,sys
W='/home/claude/work/';G=W+'gml/';B=W+'build/'
V=json.load(open('/home/claude/scripts/knights.json'))['variants'];keys=[v['key'] for v in V]
A=json.load(open(B+'assets.json'));RN=A['rename']
VAR='global.knight_variant'
def ents(k):
    d=G+k+'/CodeEntries';return {f[:-4]:open(f'{d}/{f}',encoding='utf8',errors='replace').read() for f in os.listdir(d)}
T={k:ents(k) for k in keys}
BASE0=dict(T['base'])
sys.path.insert(0,'/home/claude/scripts')
import rules_apply
_ap,_pr=rules_apply.apply_all(T)
print('audited rules applied:',len(_ap))
if _pr:
    print('RULE PROBLEMS',_pr);sys.exit(1)
EV=r'(?:Create|Destroy|Alarm|Step|Collision|Keyboard|Mouse|Other|Draw|KeyPress|KeyRelease|Gesture|PreCreate|CleanUp|Trigger)'

# ---------- asset-index literals: decompiled ints are indices in each mod's own data file; re-map to base indices ----------
import difflib
def _idx(k):
    d={}
    for l in open(f'{W}idx/{k}.tsv',encoding='utf8'):
        t,i,n=l.rstrip('\n').split('\t');d[(t,int(i))]=n
    return d
_IDX={k:_idx(k) for k in keys}
_INT=re.compile(r'(?<![\w.])(\d{2,5})(?![\w.])')
# numeric object ids that point at objects split into per-variant copies (obj_knight_rotating_slash -> __vN) must become NAMES here,
# otherwise norm_literals reverts them to the base number = the plain object, whose variant branches are empty (attack chain stalls)
_SPLITOBJ={'obj_knight_rotating_slash','obj_knight_stream','obj_fallingsword','obj_bullet_knight_stream','obj_diagonal_bullet'}
_SPLRX=re.compile(r'\b(new_knight|knight)(\s*(?:==|!=|=)\s*)(\d{3,4})\b')
_nspl=0
_PRE_SPR=re.compile(r'(\b\w*(?:sprite|spr)\w*\s*(?:==|!=|=)\s*)(\d{3,5})\b(?!\s*[-+*/])')
_PRE_DS=re.compile(r'(\bdraw_sprite\w*\(\s*)(\d{3,5})\b')
_PRE_MK=re.compile(r'(\b(?:scr_marker|scr_dark_marker|scr_afterimage\w*)\(\s*[^,()]+,\s*[^,()]+,\s*)(\d{3,5})\b')
_PRE_IC=re.compile(r'(\binstance_create\w*\([^;\n]*?,\s*)(\d{3,5})(\s*\))')
for _k in keys:
    if _k=='base':continue
    _m=_IDX[_k]
    for _e in list(T[_k]):
        _t=T[_k][_e]
        if 'knight' not in _t:continue
        def _fs(mm):
            global _nspl
            nm=_m.get(('obj',int(mm.group(3))))
            if nm in _SPLITOBJ:
                _nspl+=1;return mm.group(1)+mm.group(2)+nm
            return mm.group(0)
        _t2=_SPLRX.sub(_fs,_t)
        def _mk(kind):
            def f(mm):
                global _nspl
                nm=_m.get((kind,int(mm.group(2))))
                if nm and nm in RN.get(_k,{}):
                    _nspl+=1;return mm.group(1)+nm+(mm.group(3) if mm.lastindex>=3 else '')
                return mm.group(0)
            return f
        _t2=_PRE_SPR.sub(_mk('spr'),_t2);_t2=_PRE_DS.sub(_mk('spr'),_t2);_t2=_PRE_MK.sub(_mk('spr'),_t2);_t2=_PRE_IC.sub(_mk('obj'),_t2)
        if _t2!=_t:T[_k][_e]=_t2
print('split-object numeric ids -> names:',_nspl)
_ren=[0]
def norm_literals(k,text,btext):
    if k=='base' or btext is None or text==btext:return text,0
    m=_IDX[k];b=_IDX['base']
    tl=text.split('\n');bl=btext.split('\n');out=list(tl);fixed=0
    for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,bl,tl,autojunk=False).get_opcodes():
        if tag=='replace' and i2-i1==j2-j1:
            for off in range(i2-i1):
                bt=_INT.split(bl[i1+off]);tt=_INT.split(tl[j1+off])
                if len(bt)!=len(tt):continue
                if any(bt[x]!=tt[x] for x in range(0,len(bt),2)):continue
                ok=True;ch=False;nt=list(bt)
                for x in range(1,len(bt),2):
                    if bt[x]!=tt[x]:
                        bi,mi=int(bt[x]),int(tt[x])
                        _hit=[K for K in ('obj','spr','snd','room','scr','font') if m.get((K,mi)) and m.get((K,mi))==b.get((K,bi))]
                        if not _hit:ok=False;break
                        ch=True
                        # asset has a per-variant copy (renamed later to __vN): keep it as a NAME so it resolves to this variant's copy
                        if m.get((_hit[0],mi)) in RN.get(k,{}):nt[x]=m.get((_hit[0],mi));_ren[0]+=1
                if ok and ch:out[j1+off]=''.join(nt);fixed+=1
    return '\n'.join(out),fixed
_nfix=0
for _k in keys:
    if _k=='base':continue
    for _e in list(T[_k]):
        T[_k][_e],_f=norm_literals(_k,T[_k][_e],T['base'].get(_e));_nfix+=_f

# ---- context rules for index literals the line-diff could not align (mod-only code / new lines) ----
_MN={}
for _l in open(f'{W}idx/merged.tsv',encoding='utf8') if os.path.exists(f'{W}idx/merged.tsv') else []:
    _t,_i,_n=_l.rstrip('\n').split('\t');_MN.setdefault(_t,set()).add(_n)
_CTX=[
 (re.compile(r'(\b(?:knight_sprite|_afterspr|_bgsprite|_swordsprite|_bar_sprite|_cutout_sprite|cut_sprite|_fspr|actor_sprite|remspellsprite)\s*(?:==|!=|=)\s*)(\d{3,5})\b'),'spr'),
 (re.compile(r'(\b(?:kn|_ob|kill_target|_whospos|target|actor_target|_splitter_obj|_splitter|knight)\s*(?:==|!=|=)\s*)(\d{3,5})\b'),'obj'),
 (re.compile(r'(\b(?:instance_exists|i_ex)\()(\d{3,5})\b'),'obj'),
 (re.compile(r'(\binstance_create\()(\d{3,5})(?=\))'),'obj'),
 (re.compile(r'(\) && )(\d{3,5})(?=\))'),'obj'),
 (re.compile(r'(\bdraw_sprite\w*\()(\d{3,5})\b'),'spr'),
 (re.compile(r'(\bc_var_instance\(\w+, "[rld]sprite", )(\d{3,5})\b'),'spr'),
]

# name-agnostic: variables that are used as an object / sprite anywhere are asset holders, so their integer literals are asset ids
_AV={}
_ASG=re.compile(r'(?m)^\s*(?:var\s+)?([A-Za-z_]\w*)\s*(?:=|==|!=)\s*\d{3,4}\s*[;)]?\s*$')
_ALLTXT='\n'.join(_t for _k in keys for _t in T[_k].values())
_assigned=set(_ASG.findall(_ALLTXT))
_ou=set()
for _rx in (r'instance_create\w*\([^;\n]*,\s*([A-Za-z_]\w*)\)',r'with \(\s*([A-Za-z_]\w*)\s*\)',r'\b(?:i_ex|instance_exists|instance_number|instance_destroy|instance_find)\(\s*([A-Za-z_]\w*)\b',r'object_index\s*(?:==|!=)\s*([A-Za-z_]\w*)\b'):
    _ou|=set(re.findall(_rx,_ALLTXT))
_su=set(re.findall(r'sprite_index\s*=\s*([A-Za-z_]\w*)\s*;',_ALLTXT))|set(re.findall(r'draw_sprite\w*\(\s*([A-Za-z_]\w*)\b',_ALLTXT))
_OKN=re.compile(r'obj|knight|splitter|bullet|target|inst|sprite|spr|actor|kris|susie|ralsei|noelle|hero',re.I)
for _v in _assigned:
    if not _OKN.search(_v):continue
    if _v in _ou:_AV[_v]='obj'
    elif _v in _su:_AV[_v]='spr'
print('asset-holder variables:',len(_AV),sorted(_AV)[:80])
_CHOOSE=re.compile(r'(\b\w*sprite\w* = choose\()([^)]*)(\))')
def ctx_literals(k,text,btext):
    if k=='base':return text,0
    m=_IDX[k];bl=set(btext.split('\n')) if btext else set();fx=0;out=[]
    _avrx=re.compile(r'^(\s*(?:var\s+)?)([A-Za-z_]\w*)(\s*(?:=|==|!=)\s*)(\d{3,4})(\s*[;)]?\s*)$')
    for line in text.split('\n'):
        if line in bl or not re.search(r'\d{2,5}',line):out.append(line);continue
        def sub(kind):
            def f(mm):
                nonlocal fx
                n=int(mm.group(2));nm=m.get((kind,n))
                if nm and nm in _MN.get(kind,()):fx+=1;return mm.group(1)+nm
                return mm.group(0)
            return f
        for rx,kind in _CTX:
            line=rx.sub(sub(kind),line)
        if k=='thorn':
            _cm=re.search(r'new_knight\s*(==|!=)\s*(1173|630|802|669)\b',line)
            if _cm:
                _nm0={'1173':'obj_knight_weird_bottom_manager','630':'obj_knight_swordfall','802':'obj_knight_tunnel_slasher_2_revised','669':'obj_knight_rotating_slash'}[_cm.group(2)]
                line=line[:_cm.start(2)]+_nm0+line[_cm.end(2):];fx+=1
            _tm=re.match(r'^(\s*new_knight\s*=\s*)(1173|630|802|669);\s*$',line)
            if _tm:
                line=_tm.group(1)+{'1173':'obj_knight_weird_bottom_manager','630':'obj_knight_swordfall','802':'obj_knight_tunnel_slasher_2_revised','669':'obj_knight_rotating_slash'}[_tm.group(2)]+';';fx+=1;out.append(line);continue
        _am=_avrx.match(line)
        if _am and _am.group(2) in _AV:
            _kind=_AV[_am.group(2)];_nm=m.get((_kind,int(_am.group(4))))
            if _nm and _nm in _MN.get(_kind,()):line=_am.group(1)+_am.group(2)+_am.group(3)+_nm+_am.group(5);fx+=1
        def fc(mm):
            nonlocal fx
            items=[x.strip() for x in mm.group(2).split(',')];new=[]
            for x in items:
                nm=m.get(('spr',int(x))) if x.isdigit() else None
                if nm and nm in _MN.get('spr',()):new.append(nm);fx+=1
                else:new.append(x)
            return mm.group(1)+', '.join(new)+mm.group(3)
        line=_CHOOSE.sub(fc,line)
        if k=='violet' and 'var getachance = choose(520, 521);' in line:
            line=line.replace('choose(520, 521)','choose(snd_flowery_voiceclip_get_a_chance_1, snd_flowery_voiceclip_get_a_chance_2)');fx+=1
        out.append(line)
    return '\n'.join(out),fx
for _k in keys:
    if _k=='base':continue
    for _e in list(T[_k]):
        T[_k][_e],_f=ctx_literals(_k,T[_k][_e],T['base'].get(_e));_nfix+=_f
print('literal lines re-mapped:',_nfix,' kept-as-variant-name:',_ren[0])
if __import__('os').environ.get('KH_DUMP'):
    for _k in keys:
        _d=f'{W}normdump/{_k}';__import__('os').makedirs(_d,exist_ok=True)
        for _e,_t in T[_k].items():open(f'{_d}/{_e}.gml','w',encoding='utf8').write(_t)
allobj=set()
for k in keys:
    for l in open(f'{W}inv/{k}/objects.tsv',encoding='utf8'):
        allobj.add(l.split('\t')[0])
allobj=sorted(allobj,key=len,reverse=True)
def owner_of(entry):
    if not entry.startswith('gml_Object_'):return None
    rest=entry[len('gml_Object_'):]
    for n in allobj:
        if rest.startswith(n+'_') and re.match(EV+r'_',rest[len(n)+1:]):return n,rest[len(n)+1:]
    return None
# ---------- identifier rewriting ----------
_cache={}
def rewriter(k):
    m=RN[k]
    if not m:return lambda s:s
    if k in _cache:return _cache[k]
    pat=re.compile(r'(?<![A-Za-z0-9_])('+'|'.join(re.escape(x) for x in sorted(m,key=len,reverse=True))+r')(?![A-Za-z0-9_])')
    f=lambda s:pat.sub(lambda mo:m[mo.group(1)],s)
    _cache[k]=f;return f
def final_entry_name(k,e):
    if e.startswith('gml_Object_'):
        o=owner_of(e)
        if o and o[0] in RN[k]:return 'gml_Object_'+RN[k][o[0]]+'_'+o[1]
    return e
# ---------- GML top-level function splitter ----------
def split_top(text):
    """returns list of (name|None, chunk). chunks at brace depth 0 starting with 'function'."""
    out=[];i=0;n=len(text);depth=0;start=0;cur=None;buf_start=0
    def skip_str(i):
        q=text[i];i+=1
        while i<n and text[i]!=q:
            if text[i]=='\\':i+=1
            i+=1
        return i+1
    chunks=[];seg_start=0;i=0;in_func=False;fname=None;fstart=0
    while i<n:
        c=text[i]
        if text.startswith('//',i):
            j=text.find('\n',i);i=n if j<0 else j;continue
        if text.startswith('/*',i):
            j=text.find('*/',i);i=n if j<0 else j+2;continue
        if c in '"\'':i=skip_str(i);continue
        if c=='{':depth+=1
        elif c=='}':
            depth-=1
            if depth==0 and in_func:
                chunks.append(('fn',fname,text[fstart:i+1]));in_func=False;seg_start=i+1
        elif depth==0 and not in_func and text.startswith('function',i) and (i==0 or not (text[i-1].isalnum() or text[i-1]=='_')):
            m=re.match(r'function\s+([A-Za-z_]\w*)\s*\(',text[i:])
            if m:
                if text[seg_start:i].strip():chunks.append(('code',None,text[seg_start:i]))
                in_func=True;fname=m.group(1);fstart=i
        i+=1
    if text[seg_start:].strip():chunks.append(('code',None,text[seg_start:]))
    return chunks
# ---------- default behaviour of an event a variant doesn't define ----------
base_parent={};base_objs=set()
for l in open(f'{W}inv/base/objects.tsv',encoding='utf8'):
    p=l.rstrip('\n').split('\t')
    if p and p[0]:
        base_objs.add(p[0]);pr=p[3].split('|')[0] if len(p)>3 else ''
        base_parent[p[0]]=pr
base_events=collections.defaultdict(set)
for e in T['base']:
    o=owner_of(e)
    if o:base_events[o[0]].add(o[1])
def default_body(fe):
    o=owner_of(fe)
    if not o or o[0] not in base_objs:return ''
    obj,ev=o
    p=base_parent.get(obj,'');seen=0
    while p and seen<30:
        if ev in base_events.get(p,()):return 'event_inherited();'
        p=base_parent.get(p,'');seen+=1
    if ev=='Draw_0':return 'draw_self();'
    return ''
# ---------- hub patches (applied to every variant's text) ----------
MUSIC_RE=re.compile(r'(global\.batmusic\[0\]\s*=\s*snd_init\()(.+)(\);)')
def patch_variant(entry,k,t):
    if entry in ('gml_Object_obj_ch3_PTB02_Step_0','gml_Object_obj_testoverworldenemy_Other_10'):
        t=MUSIC_RE.sub(lambda m:m.group(1)+'knight_song_file('+m.group(2)+')'+m.group(3),t)
    if entry=='gml_GlobalScript_scr_complete_save_file':
        t=t.replace('function scr_get_knight_total_attempts()\n{\n','function scr_get_knight_total_attempts()\n{\n    if (global.knight_run == 1)\n    {\n        return 1;\n    }\n',1)
    if entry=='gml_Object_obj_ch3_PTB02_CleanUp_0':
        t=t.replace('global.char = [rem_char[0], rem_char[1], rem_char[2]];','if (variable_instance_exists(id, "rem_char"))\n        global.char = [rem_char[0], rem_char[1], rem_char[2]];')
    if entry=='gml_Object_obj_ch3_PTB02_Step_0':
        t=t.replace('room_goto(room_insert_violet_sideb);','knight_fight_finished(room_town_krisyard_dark);')
        t=t.replace('room_goto(room_town_krisyard_dark);','knight_fight_finished(room_town_krisyard_dark);')
    return t
POST={
 'gml_Object_obj_npc_sign_Other_10':('pre','if (room == room_dw_snow_zone && extflag == "kaizo settings")\n{\n    global.interact = 1;\n    knight_menu_open(id);\n    exit;\n}\n'),
 'gml_Object_obj_ch3_PTB02_Create_0':('post','\nif (!variable_instance_exists(id, "rem_char"))\n    rem_char = [global.char[0], global.char[1], global.char[2]];\nif (global.plot >= 310 && global.plot < 330 && room == room_dw_snow_zone)\n{\n    knight_ensure_ctrl();\n    var _knight_has_sign = false;\n    with (obj_npc_sign)\n    {\n        if (extflag == "kaizo settings")\n            _knight_has_sign = true;\n    }\n    if (!_knight_has_sign)\n    {\n        var _knight_sign = instance_create(352, 200, obj_npc_sign);\n        _knight_sign.extflag = "kaizo settings";\n    }\n}\n'),
}
# ---------- collect final entries per variant ----------
F=collections.defaultdict(dict)   # final_name -> {variant key: text}
for k in keys:
    rw=rewriter(k)
    for e,t in T[k].items():
        fe=final_entry_name(k,e)
        t=patch_variant(e,k,t)
        F[fe][k]=rw(t) if k!='base' else t
report={'switch_entries':0,'script_entries':0,'unchanged':0,'dispatchers':0,'constructor_conflicts':[],'static_conflicts':[],'new_entries':0}
OUT=B+'merged';os.makedirs(OUT,exist_ok=True)
for f in os.listdir(OUT):os.remove(OUT+'/'+f)

ENUM_RE=re.compile(r'^enum\s+(\w+)\s*\{[^}]*\}[ \t]*\n?',re.M)
def strip_enums(text):
    found=[]
    def rep(m):
        found.append((m.group(1),m.group(0).strip()));return ''
    return ENUM_RE.sub(rep,text),found
NAMEDFN_RE=re.compile(r'^([ \t]*)function\s+(\w+)\s*\(',re.M)
def collect_enums(parts):
    """parts: list of (gid,text) -> (cleaned parts, enum block text). conflicting enum bodies get renamed per group."""
    seen={};out=[];extra=[]
    for gid,t in parts:
        t2,fnd=strip_enums(t)
        for name,block in fnd:
            if name not in seen:seen[name]=block;extra.append(block)
            elif seen[name]!=block:
                nn=f'{name}_g{gid}';t2=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(name)+r'(?![A-Za-z0-9_])',nn,t2)
                extra.append(re.sub(r'(?<![A-Za-z0-9_])'+re.escape(name)+r'(?![A-Za-z0-9_])',nn,block));report.setdefault('enum_renames',[]).append((name,gid))
        out.append((gid,t2))
    return out,'\n\n'.join(extra)
def dedupe_named_fns(parts):
    """later branches: 'function foo(' -> 'foo = function(' when foo already declared in an earlier branch"""
    declared=set();out=[]
    for gid,t in parts:
        mine=set(m.group(2) for m in NAMEDFN_RE.finditer(t))
        def rep(m):
            return f'{m.group(1)}{m.group(2)} = function (' if m.group(2) in declared else m.group(0)
        t2=NAMEDFN_RE.sub(rep,t);declared|=mine;out.append((gid,t2))
    return out

def case_labels(ks):return ''.join(f'    case {keys.index(k)}:\n' for k in ks)
PERSIST=set()
for _k in keys:
    for _l in open(f'{W}inv/{_k}/objects.tsv',encoding='utf8'):
        _p=_l.rstrip('\n').split('\t')
        if len(_p)>3:
            _f=_p[3].split('|')
            if len(_f)>5 and _f[5]=='True':PERSIST.add(_p[0])
# build 42: the battle room's world objects (the arena cutscene and its actors, the sign, the dark world controller, the cutscene
# master) always run the code of the variant they were made under. In a single fight that is the fight's own variant anyway (the
# variant changes at Room End, before the room's objects are made); in a Tag Team / Attack Remix battle the other knights then
# never run their own arena cutscene on the host's cutscene object (which has none of their variables).
PINNED={'obj_ch3_PTB02','obj_ch3_PTB02_roaringknight','obj_ch3_PTB02_roaringknight_pull_test','obj_ch3_PTB02_roaringknight_speardodge_sequence',
        'obj_npc_sign','obj_darkcontroller','obj_cutscene_master'}
def switch_merge(texts,fe=None):
    """texts: {variantkey: text or None}"""
    groups=collections.OrderedDict()
    dflt=default_body(fe) if fe else ''
    for k in keys:
        t=texts.get(k)
        groups.setdefault(t if t is not None else dflt,[]).append(k)
    default_group=None
    for t,ks in groups.items():
        if 'base' in ks:default_group=t
    if default_group is None:default_group=next(iter(groups))
    order=[t for t in groups if t==default_group]+[t for t in groups if t!=default_group]
    parts,enums=collect_enums([(keys.index(groups[t][0]),t) for t in order])
    parts=dedupe_named_fns(parts)
    body={t:p for t,(g,p) in zip(order,parts)}
    sv=VAR
    om=owner_of(fe) if fe else None
    if (fe and re.match(r'gml_Object_.+_(CleanUp|Destroy)_0$',fe)) or (om and (om[0] in PERSIST or (om[0] in PINNED and not om[1].startswith('Create_')))):sv='(variable_instance_exists(id, "knight_v") ? knight_v : global.knight_variant)'
    s=f'switch ({sv})\n{{\n'
    for t,ks in groups.items():
        if t==default_group:continue
        s+=case_labels(ks)+'    {\n'+indent(body[t])+'\n    }\n    break;\n'
    s+='    default:\n    {\n'+indent(body[default_group])+'\n    }\n    break;\n}\n'
    if enums:s+='\n'+enums+'\n'
    return s
def indent(t):return '\n'.join(('        '+l if l.strip() else l) for l in t.rstrip().split('\n'))
nsw=0
for fe,vt in sorted(F.items()):
    is_script=fe.startswith('gml_GlobalScript_')
    texts={k:vt.get(k) for k in keys}
    present=[k for k in keys if texts[k] is not None]
    vals={texts[k] for k in present}
    if len(vals)==1 and len(present)==len(keys):
        _only=next(iter(vals))
        if BASE0.get(fe)==_only:
            report['unchanged']+=1;continue
        # identical in every variant but different from the game's own file (a rule / hook applies to all variants): it still has to be written
        open(f'{OUT}/{fe}.gml','w',encoding='utf8').write(_only);report.setdefault('uniform_patched',[]).append(fe);continue
    if not is_script and re.match(r'gml_Object_.+__v\d+_'+EV+r'_',fe):
        if len(vals)>1:print('CLONE CONFLICT (variants sharing one object clone have different code):',fe,[k for k in present])
        open(f'{OUT}/{fe}.gml','w',encoding='utf8').write(next(iter(vals)));report['clone_entries']=report.get('clone_entries',0)+1;continue
    if is_script:
        # function-level merge
        enum_seen={};enum_out=[]
        for k in present:
            t2,fnd=strip_enums(texts[k]);texts[k]=t2
            for name,block in fnd:
                if name not in enum_seen:enum_seen[name]=block;enum_out.append(block)
                elif enum_seen[name]!=block:report.setdefault('enum_conflict_scripts',[]).append((fe,name))
        per={k:split_top(texts[k]) for k in present}
        order=[];fn_defs=collections.OrderedDict();pre=collections.OrderedDict()
        for k in keys:
            if k not in per:continue
            for kind,name,chunk in per[k]:
                if kind=='fn':
                    fn_defs.setdefault(name,collections.OrderedDict()).setdefault(chunk,[]).append(k)
                else:
                    pre.setdefault(chunk,[]).append(k)
        body=''
        for chunk,ks in pre.items():body+=chunk.strip()+'\n\n'
        for name,gs in fn_defs.items():
            if len(gs)==1:
                body+=next(iter(gs)).strip()+'\n\n';continue
            # differing function: dispatcher
            for chunk,ks in gs.items():
                if re.search(r'\)\s*constructor|\bconstructor\b\s*$',chunk.split('{',1)[0]):report['constructor_conflicts'].append((fe,name))
                if re.search(r'\bstatic\b',chunk):report['static_conflicts'].append((fe,name))
            report['dispatchers']+=1
            # default group = base's else first
            defg=None
            for chunk,ks in gs.items():
                if 'base' in ks:defg=chunk
            if defg is None:defg=next(iter(gs))
            lines=[];
            for chunk,ks in gs.items():
                gid=keys.index(ks[0]);vn=f'{name}__g{gid}'
                body+=re.sub(r'^function\s+'+re.escape(name)+r'\s*\(','function '+vn+'(',chunk.strip(),count=1)+'\n\n'
            body+=f'function {name}()\n{{\n    var _a = [];\n    for (var _i = 0; _i < argument_count; _i++)\n        _a[_i] = argument[_i];\n    switch ({VAR})\n    {{\n'
            for chunk,ks in gs.items():
                if chunk==defg:continue
                gid=keys.index(ks[0])
                body+=case_labels(ks)+f'        return script_execute_ext({name}__g{gid}, _a);\n'
            body+=f'        default:\n            return script_execute_ext({name}__g{keys.index(gs[defg][0])}, _a);\n    }}\n}}\n\n'
        if enum_out:body+='\n'+'\n\n'.join(enum_out)+'\n'
        open(f'{OUT}/{fe}.gml','w',encoding='utf8').write(body)
        report['script_entries']+=1
    else:
        open(f'{OUT}/{fe}.gml','w',encoding='utf8').write(switch_merge(texts,fe))
        report['switch_entries']+=1
        if 'base' not in present:report['new_entries']+=1
for fe,(where,code) in POST.items():
    p=f'{OUT}/{fe}.gml'
    base_txt=open(p,encoding='utf8').read() if os.path.exists(p) else patch_variant(fe,'base',F[fe]['base'])
    new=(code+base_txt) if where=='pre' else (base_txt+code)
    open(p,'w',encoding='utf8').write(new);report.setdefault('post_hooks',[]).append(fe)
# instances remember the variant they were created under (needed by CleanUp/Destroy after a variant change + room restart)
for f in sorted(os.listdir(OUT)):
    m=re.match(r'(gml_Object_.+)_(?:CleanUp|Destroy|Create|Step|Draw|Alarm|Other|Collision|KeyPress|Keyboard)_\d+\.gml$',f)
    if m and 'exists(id, "knight_v")' in open(f'{OUT}/{f}',encoding='utf8').read() and '_Create_0' not in f:
        cn=m.group(1)+'_Create_0'
        cp=f'{OUT}/{cn}.gml'
        if os.path.exists(cp):
            ct=open(cp,encoding='utf8').read()
        elif cn in F and 'base' in F[cn]:
            ct=patch_variant(cn,'base',F[cn]['base'])
        else:
            report.setdefault('knight_v_no_create',[]).append(f);continue
        if 'knight_v =' not in ct:
            open(cp,'w',encoding='utf8').write('knight_v = global.knight_variant;\n'+ct);report['knight_v_creates']=report.get('knight_v_creates',0)+1
json.dump(report,open(B+'merge_report.json','w'),indent=1)
print({k:(v if not isinstance(v,list) else len(v)) for k,v in report.items()})
print('written',len(os.listdir(OUT)))
if report['constructor_conflicts']:print('CONSTRUCTOR conflicts',report['constructor_conflicts'][:10])
if report['static_conflicts']:print('STATIC conflicts',report['static_conflicts'][:10])
