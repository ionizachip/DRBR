from harness import *
sim=make_sim()
def t(party,hp,tgt):
    sim.run('global.char=%s; global.hp=%s;'%(party,hp))
    return sim.eval('knight_fix_target(%d)'%tgt)
bad=0
# Kris downed, Ralsei gone (slot1 empty), Noelle alive in slot 2
for tg in (0,1,2):
    r=t('[1,0,4]','[0,-20,90,90,19]',tg)
    if r!=2: bad+=1; print('FAIL',tg,r)
# all valid stays
for tg in (0,1,2):
    if t('[1,2,4]','[0,50,50,50,50]',tg)!=tg: bad+=1; print('FAIL keep',tg)
# duplicates
r=[t('[1,1,1]','[0,50,50,50,50]',2)]; 
if r[0]!=2: bad+=1
# nobody alive: unchanged
if t('[1,0,4]','[0,-20,90,90,-5]',1)!=1: bad+=1; print('FAIL none')
print('alive any',sim.eval('knight_party_alive_any()') if False else '')
print('FIXTARGET bad',bad); import sys; sys.exit(bad)
