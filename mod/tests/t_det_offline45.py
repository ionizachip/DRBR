"""Build 45 (P0): the Knights' attack code now calls kbr_random / kbr_irandom / kbr_random_range / kbr_irandom_range /
kbr_choose / kbr_list_shuffle / kbr_randomize / kbr_random_set_seed instead of the built-ins (det_rewrite, 1,572 places in 85 code entries).
Offline (no online battle running) they must be the built-ins: from the same generator state they give exactly the
built-ins' numbers, in the same order, and leave the generator where the built-in would. Online they draw from the shared
stream: the same seed gives the same numbers in every game, and the stream never touches the built-in generator (so the
player's own game - menus, the overworld, the SOUL - is not shifted by it). Also: the stream is off again after a match."""
import sys, os, random as pyrandom
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import *

FAILS = []
N = [0]


def ok(c, m):
    N[0] += 1
    if not c:
        FAILS.append(m)
        print('FAIL', m, flush=True)


CALLS = [
    ('random(%s)', 'kbr_random(%s)', lambda R: '%.3f' % (R.random() * 500)),
    ('irandom(%s)', 'kbr_irandom(%s)', lambda R: str(R.randint(0, 40))),
    ('random_range(%s)', 'kbr_random_range(%s)', lambda R: '%d, %d' % (R.randint(-300, 0), R.randint(0, 300))),
    ('irandom_range(%s)', 'kbr_irandom_range(%s)', lambda R: '%d, %d' % (R.randint(-30, 5), R.randint(5, 30))),
    ('choose(%s)', 'kbr_choose(%s)', lambda R: ', '.join(str(R.randint(0, 99)) for _ in range(R.randint(1, 7)))),
]


def seq(sim, exprs, seed):
    sim.run('random_set_seed(%d); global.SQ = [];' % seed)
    for e in exprs:
        sim.run('array_push(global.SQ, %s);' % e)
    sim.run('array_push(global.SQ, random(1000000));')  # where the generator was left
    return sim.py(sim.eval('global.SQ'))


sim = make_sim()
ok(sim.eval('global.kbr_det.on') in (False, 0), 'the shared stream is off when the game starts')
R = pyrandom.Random(45)
# offline: 200 runs of 60 mixed calls each, built-in vs wrapper from the same seed
bad = 0
for run in range(200):
    picks = [R.choice(CALLS) for _ in range(60)]
    args = [p[2](R) for p in picks]
    b = seq(sim, [p[0] % a for p, a in zip(picks, args)], 1000 + run)
    w = seq(sim, [p[1] % a for p, a in zip(picks, args)], 1000 + run)
    if b != w:
        bad += 1
ok(bad == 0, 'offline: 200 x 60 mixed calls give exactly the built-ins\' numbers and leave the generator in the same place (%d runs differ)' % bad)
# ds_list_shuffle offline: the same order as the built-in from the same seed
sim.run('random_set_seed(77); global.L1 = ds_list_create(); for (var _i = 0; _i < 30; _i++) ds_list_add(global.L1, _i); ds_list_shuffle(global.L1);'
        'global.A1 = []; for (var _i = 0; _i < 30; _i++) array_push(global.A1, global.L1[| _i]); global.R1 = random(1000);'
        'random_set_seed(77); global.L2 = ds_list_create(); for (var _i = 0; _i < 30; _i++) ds_list_add(global.L2, _i); kbr_list_shuffle(global.L2);'
        'global.A2 = []; for (var _i = 0; _i < 30; _i++) array_push(global.A2, global.L2[| _i]); global.R2 = random(1000);')
ok(sim.py(sim.eval('global.A1')) == sim.py(sim.eval('global.A2')) and sim.eval('global.R1') == sim.eval('global.R2'),
   'offline: kbr_list_shuffle is ds_list_shuffle')
# build 46: kbr_list_shuffle ONLINE (the stream on) on a real ds_list - build 45's version used the [| ] accessor, which the
# build's compiler turned into an array read: "trying to index a variable which is not an array" in the rotating slash attack
# (your report). A permutation of the list, the same order in every game from the same seed, the built-in generator untouched.
# (Run on code decompiled from the built data.win too: see the round trip in TESTING_REPORT.)
sim.run('random_set_seed(31); global.kbr_det.on = true; kbr_det_seed(777); global.L3 = ds_list_create(); for (var _i = 0; _i < 30; _i++) ds_list_add(global.L3, _i * 10);'
        'kbr_list_shuffle(global.L3); global.A3 = []; for (var _i = 0; _i < ds_list_size(global.L3); _i++) array_push(global.A3, ds_list_find_value(global.L3, _i));'
        'kbr_det_seed(777); global.L4 = ds_list_create(); for (var _i = 0; _i < 30; _i++) ds_list_add(global.L4, _i * 10); kbr_list_shuffle(global.L4);'
        'global.A4 = []; for (var _i = 0; _i < ds_list_size(global.L4); _i++) array_push(global.A4, ds_list_find_value(global.L4, _i));'
        'global.kbr_det.on = false; global.R3 = random(1000); random_set_seed(31); global.R4 = random(1000);')
a3, a4 = sim.py(sim.eval('global.A3')), sim.py(sim.eval('global.A4'))
ok(sorted(a3) == [i * 10 for i in range(30)] and a3 != [i * 10 for i in range(30)] and a3 == a4 and sim.eval('global.R3') == sim.eval('global.R4'),
   'online: kbr_list_shuffle shuffles a real ds_list (a permutation, the same from the same seed, the built-in generator untouched)')
sim.run('global.kbr_det.on = true; kbr_det_seed(5); global.L5 = ds_list_create(); kbr_list_shuffle(global.L5); ds_list_add(global.L5, 7); kbr_list_shuffle(global.L5);'
        'global.A5 = ds_list_find_value(global.L5, 0); global.kbr_det.on = false;')
ok(sim.eval('global.A5') == 7, 'online: an empty and a one-item list are fine')
# kbr_array_shuffle (Chapter 3's runtime has no array_shuffle): a shuffled copy, the input left as it was, both ways
sim.run('global.SA = []; for (var _i = 0; _i < 40; _i++) array_push(global.SA, _i); global.SB = kbr_array_shuffle(global.SA);'
        'global.kbr_det.on = true; kbr_det_seed(99); global.SC = kbr_array_shuffle(global.SA); kbr_det_seed(99); global.SD = kbr_array_shuffle(global.SA); global.kbr_det.on = false;')
sa, sb, sc, sd = (sim.py(sim.eval('global.%s' % n)) for n in ('SA', 'SB', 'SC', 'SD'))
ok(sa == list(range(40)) and sorted(sb) == sa and sb != sa and sorted(sc) == sa and sc == sd,
   'kbr_array_shuffle: a shuffled copy offline and online (the same seed, the same order), the input untouched')
# randomize / random_set_seed offline: they reseed as the built-ins do
sim.run('kbr_random_set_seed(99); global.Q1 = random(1000); random_set_seed(99); global.Q2 = random(1000);')
ok(sim.eval('global.Q1') == sim.eval('global.Q2'), 'offline: kbr_random_set_seed reseeds the built-in generator')

# online: the same seed -> the same numbers in two games; the built-in generator is not touched
sim2 = make_sim()
outs = []
for s in (sim, sim2):
    s.run('random_set_seed(5); global.kbr_det.on = true; kbr_det_seed(424242); global.DQ = [];'
          'for (var _i = 0; _i < 500; _i++) { array_push(global.DQ, kbr_irandom_range(-50, 50)); array_push(global.DQ, kbr_choose(1, 2, 3, 4, 5));'
          ' array_push(global.DQ, kbr_random(10)); array_push(global.DQ, kbr_irandom(9)); }'
          'kbr_randomize(); kbr_random_set_seed(1); global.DQB = random(1000000); global.kbr_det.on = false;'
          'random_set_seed(5); global.DQC = random(1000000);')
    outs.append(s.py(s.eval('global.DQ')))
    ok(s.eval('global.DQB') == s.eval('global.DQC'), 'online: 2,000 stream draws (and the attack code\'s randomize / random_set_seed) leave the built-in generator alone')
ok(outs[0] == outs[1], 'online: the same seed gives the same 2,000 numbers in two games')
ok(all(-50 <= x <= 50 for x in outs[0][0::4]) and all(x in (1, 2, 3, 4, 5) for x in outs[0][1::4]) and all(0 <= x < 10 for x in outs[0][2::4])
   and all(0 <= x <= 9 and x == int(x) for x in outs[0][3::4]), 'online: every number in its range')
sim2.run('random_set_seed(5); global.kbr_det.on = true; kbr_det_seed(424243); global.DQ2 = []; for (var _i = 0; _i < 50; _i++) array_push(global.DQ2, kbr_random(1));'
         'global.kbr_det.on = false;')
ok(sim2.py(sim2.eval('global.DQ2')) != [x for x in outs[0][2::4][:50]], 'online: another seed, other numbers')
# the stream is off again after a match ends for this game
sim.run('global.kbr_det.on = true; kbr_end_clean();')
ok(sim.eval('global.kbr_det.on') in (False, 0), 'kbr_end_clean (the results / a lost connection) turns the stream off')
print('det offline / online: %d checks, %d failed' % (N[0], len(FAILS)))
sys.exit(1 if FAILS else 0)
