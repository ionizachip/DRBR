from harness import *
FAILS=[];N=[0]
def eq(a,b,msg):
    N[0]+=1
    if a!=b:FAILS.append(msg);print('FAIL',msg,'got',repr(a),'want',repr(b))
sim=make_sim(); sim.load_file(M+'gml_GlobalScript_scr_damage_calculation.gml',entry='gml_GlobalScript_scr_damage_calculation')
sim.run('global.knight_run=1; global.krun={cfg:{}}; global.char=[1,1,1]; global.battledf=[0,0,0]; global.maxhp=[0,90,90,90,90];')
eq(sim.eval('scr_damage_calculation(30,0)'),10,'3 Kris single hit: a third each')
sim.run('global.knight_calc_loop=true;'); eq(sim.eval('scr_damage_calculation(30,0)'),30,'loop mode: unscaled (scaled at subtraction)'); sim.run('global.knight_calc_loop=false;')
sim.run('global.char=[1,2,3];'); eq(sim.eval('scr_damage_calculation(30,0)'),30,'trio unchanged')
sim.run('global.char=[1,2,0];'); eq(sim.eval('scr_damage_calculation(20,0)'),17,'duo x0.85')
sim.run('global.knight_run=0;'); eq(sim.eval('scr_damage_calculation(20,0)'),20,'outside hub unchanged')
# defence still applied before scaling
sim.run('global.knight_run=1; global.char=[1,1,1]; global.battledf=[1,1,1];'); eq(sim.eval('scr_damage_calculation(30,0)')<=10,True,'defence then split')
print('calc tests',N[0],'fails',len(FAILS)); sys.exit(1 if FAILS else 0)
