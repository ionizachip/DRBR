import struct,sys,hashlib
def chunks(p):
    d=open(p,'rb').read()
    assert d[:4]==b'FORM'
    pos=8;out={}
    while pos<len(d):
        n=d[pos:pos+4].decode();l=struct.unpack('<I',d[pos+4:pos+8])[0]
        out[n]=(pos+8,l,hashlib.md5(d[pos+8:pos+8+l]).hexdigest()[:8]);pos+=8+l
    return out
base=chunks('/mnt/user-data/uploads/data.win')
W='/home/claude/work/out/'
mods={m:chunks(W+m+'.win') for m in ['cyan','elec','thorn','violet','kaizo']}
print('%-5s %10s'%('chunk','base'),*['%9s'%m for m in mods])
for c,(o,l,h) in base.items():
    row=[]
    for m in mods:
        mo,ml,mh=mods[m][c]
        row.append('same' if mh==h else '%+d'%(ml-l))
    print('%-5s %10d'%(c,l),*['%9s'%r for r in row])
