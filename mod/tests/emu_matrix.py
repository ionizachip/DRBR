import sys
from emu_end2 import *
P=[[1,2,3],[1,0,0],[2,0,0],[4,0,0],[1,2,4],[1,1,1],[3,2,1],[1,4,0],[2,3,4],[3,0,0]]
keys=sys.argv[1].split(',') if len(sys.argv)>1 else list(KEYS)
bad=0
for k in keys:
    for p in P:
        try: r=play(k,p,frames=900)
        except Exception as e: r=('EXC',str(e)[:150],[])
        flag='ok ' if r[0]=='done' else 'ERR'
        if r[0]!='done': bad+=1
        print(flag,k,p,r[0],(r[1] or '')[:160],flush=True)
print('bad',bad)
