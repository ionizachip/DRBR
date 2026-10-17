import struct,hashlib,json,sys
def u32(d,o):return struct.unpack_from('<I',d,o)[0]
def i32(d,o):return struct.unpack_from('<i',d,o)[0]
def load(p):
    d=open(p,'rb').read();pos=8;ch={}
    while pos<len(d):
        n=d[pos:pos+4].decode();l=u32(d,pos+4);ch[n]=(pos+8,l);pos+=8+l
    return d,ch
def s(d,ptr):  # string pointer points at chars; length precedes
    l=u32(d,ptr-4);return d[ptr:ptr+l].decode('utf8','replace')
def plist(d,ch,n):
    o,l=ch[n];c=u32(d,o);return [u32(d,o+4+4*i) for i in range(c)]
def names(d,ch,n):
    return [s(d,u32(d,p)) for p in plist(d,ch,n)]
def code(d,ch):
    res={}
    for p in plist(d,ch,'CODE'):
        nm=s(d,u32(d,p));ln=u32(d,p+4);rel=i32(d,p+12);st=p+12+rel
        res[nm]=hashlib.md5(d[st:st+ln]).hexdigest()
    return res
def scan(p):
    d,ch=load(p);r={'CODE':code(d,ch)}
    for n in ['OBJT','SPRT','SCPT','SOND','ROOM']:
        r[n]={nm:hashlib.md5(d[a:b]).hexdigest() for nm,a,b in span(d,ch,n)}
    return r
def span(d,ch,n):
    ps=plist(d,ch,n);o,l=ch[n];end=o+l
    out=[]
    srt=sorted(ps)
    nxt={p:(srt[i+1] if i+1<len(srt) else end) for i,p in enumerate(srt)}
    for p in ps:out.append((s(d,u32(d,p)),p,nxt[p]))
    return out
if __name__=='__main__':
    W='/home/claude/work/out/'
    base=scan('/mnt/user-data/uploads/data.win')
    res={}
    for m in ['cyan','elec','thorn','violet','kaizo']:
        x=scan(W+m+'.win');res[m]={}
        for k in base:
            add=[n for n in x[k] if n not in base[k]]
            chg=[n for n in x[k] if n in base[k] and x[k][n]!=base[k][n]]
            res[m][k]={'added':add,'changed':chg}
    json.dump(res,open('/home/claude/work/diff.json','w'))
    for m in res:
        print('==',m)
        for k in res[m]:print('  %-4s +%d ~%d'%(k,len(res[m][k]['added']),len(res[m][k]['changed'])))
