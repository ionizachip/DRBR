"""Build 48: TARGETING in three emulated games over the simulated network (br_multi: the real merged fight code, the real online
code, the host's real resolution and relay). Checks every mode's rule, the sends (every game starts the pattern around the
target; the sender's bullets are harmless to it and tinted in its colour; aimed swords go for the target), SHARDS (knockout
credit and steal, the Knight's hit credited to the last player who hurt you), TIRED, DEFEND / PACIFY fallbacks, the "!",
OUTNUMBERED BONUS, the keys (Q / E / A / 1-8), retargeting when a target falls, and TARGETING OFF (the old behaviour).
Usage: python3 t_target48.py"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_multi import *

FAILS = []
N = [0]


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)


def keep(f, sims, prev):
    if f % 15 == 0:
        for s in sims:
            s.run('if (is_struct(global.kfo.M) && !global.kfo.M.out && !variable_global_exists("NOHEAL")) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
            s.log.clear()


def go(net, sims, n):
    rec = run(net, sims, n, 'none', on_frame=keep, wall=900)
    errs = {c: rec[c]['errors'][:1] for c in range(1, len(sims) + 1) if rec[c]['errors']}
    if errs:
        ok(False, 'no errors in the games: %r' % errs)
        raise SystemExit(1)
    return rec


def J(s, e):
    return s.py(s.eval(e))


def host_p(H, pid, field):
    return J(H, 'kfo_host_player(%d).%s' % (pid, field))


def st_row(s, pid):
    return J(s, '(function(){ var _pl = kfo_ja(global.kfo.M.st, "pl"); for (var _i = 0; _i < array_length(_pl); _i++) if (kfo_jn(_pl[_i], "pid", -1) == %d) return _pl[_i]; return undefined; })()' % pid)


def set_mode(s, m, pick=-1):
    s.run('global.kfo.M.tg.mode = %d; global.kfo.M.tg.pick = %d; kbr_tg_send(global.kfo.M, true);' % (m, pick))


def send(s, sid):
    s.run('var _S = global.kfo.M.sk; array_push(_S.slots, { sid: %d, rev: 0 }); _S.sel = array_length(_S.slots) - 1; _S.cd = 0; global.USED = kbr_skill_use();' % sid)
    return s.eval('global.USED')


def kbr_bullets(s):
    # build 50: a send in the target's game is the Knights' real attack objects (kbrx; its colour in kbrcol); the host's copies
    # for its bots are still twin bullets
    s.run('global.KB = []; with (obj_bulletparent) { if (variable_instance_exists(id, "kbr") && kbr != 0) array_push(global.KB, [kbrf, kbrt, kbrd,'
          ' variable_instance_exists(id, "kbrcol") ? kbrcol : image_blend, active, round(x), round(y), 0]); }')
    return J(s, 'global.KB')


t0 = time.time()
net, sims = make_room(3, 'lan', 4848, setx='_s.mhp = 300; _s.cdm = 25; _s.g0 = 50;')
H, C2, C3 = sims
print('room up', round(time.time() - t0, 1), 's', flush=True)
go(net, sims, 330)
ok(J(H, 'kbr_tg_on(global.kfo.M.eff)'), 'TARGETING is on by default')
ok(J(H, 'global.kfo.M.go') and J(H, 'global.kfo.M.R.ph') in ('run', 'arm', 'idle'), 'the match runs (%s)' % J(H, 'global.kfo.M.R.ph'))

# ---- CHAOS (default): one living target each, never yourself
go(net, sims, 12)
for pid in (1, 2, 3):
    tg = host_p(H, pid, 'tg')
    ok(len(tg) == 1 and tg[0] != pid and tg[0] in (1, 2, 3), 'CHAOS: player %d has one target %r' % (pid, tg))
ok(st_row(C2, 1)['tm'] == 0 and len(st_row(C2, 1)['tg']) == 1, 'the standings carry mode and targets to the other games')

# ---- CHECK on player 2, a Sword: every game makes it around player 2's SOUL; the sender's own bullets are harmless
set_mode(H, 4, 2)
go(net, sims, 10)
ok(host_p(H, 1, 'tg') == [2] and host_p(H, 1, 'tmx') == 4, 'CHECK picks player 2 (%r)' % host_p(H, 1, 'tg'))
# wait for a running attack (the sends start while one runs)
for _ in range(40):
    if all(J(s, 'global.kfo.M.R.ph') == 'run' for s in sims):
        break
    go(net, sims, 10)
ok(send(H, 1) == 1, 'player 1 uses Sword')
go(net, sims, 8)
col1 = J(H, 'kbr_pcol(kbr_pslot(1))')
bl = [kbr_bullets(s) for s in sims]
ok([len(b) >= 1 for b in bl] == [False, True, False], 'build 49: only the target\'s game (player 2) makes the Sword (%r)' % [len(b) for b in bl])
ok(all(all(x[0] == 1 and x[1] == 2 for x in b) for b in bl), 'from player 1, at player 2')
ok(all(all(x[3] == col1 for x in b) for b in bl), "tinted in player 1's colour (%d)" % col1)
go(net, sims, 30)
ok(len(kbr_bullets(H)) == 0 and len(kbr_bullets(C3)) == 0, "build 49: the sender's game and player 3's show none of it")
ok(any(x[4] == 1 for x in kbr_bullets(C2)), 'it is live in the target\'s game')
ok(J(H, 'kfo_host_player(2).sr') >= 1, 'the host counts it as received by player 2')

# ---- PROCEED: the least HP
C3.run('global.NOHEAL = 1; global.hp[kbr_char()] = 40; kbr_send_state(true);')
set_mode(C2, 1)
go(net, sims, 25)
ok(host_p(H, 2, 'tg') == [3], 'PROCEED goes for player 3 (least HP) %r' % host_p(H, 2, 'tg'))

# ---- BIG SHOT: most shards
H.run('kfo_host_player(1).sh = 5;')
set_mode(C3, 2)
go(net, sims, 10)
ok(host_p(H, 3, 'tg') == [1], 'BIG SHOT goes for player 1 (5 shards) %r' % host_p(H, 3, 'tg'))

# ---- DEFEND: who targets me (player 1 CHECKs 2, player 3 aims at 1); player 2 on DEFEND -> [1]; nobody -> CHAOS
set_mode(C2, 3)
go(net, sims, 10)
ok(host_p(H, 2, 'tg') == [1], 'DEFEND: player 2 goes for player 1 who targets them %r' % host_p(H, 2, 'tg'))
set_mode(H, 6)
set_mode(C3, 4, 1)
go(net, sims, 10)
ok(sorted(host_p(H, 2, 'tg')) == [1], 'DEFEND follows who targets it (ROARING player 1) %r' % host_p(H, 2, 'tg'))
set_mode(H, 4, 3)
go(net, sims, 10)
tg2 = host_p(H, 2, 'tg')
ok(len(tg2) == 1 and tg2[0] in (1, 3), 'DEFEND with nobody on me falls back to CHAOS %r' % tg2)

# ---- ROARING: everyone at reduced strength, with the shard step on top
set_mode(H, 6)
go(net, sims, 10)
ok(sorted(host_p(H, 1, 'tg')) == [2, 3], 'ROARING: every other player %r' % host_p(H, 1, 'tg'))
for s in sims:
    s.run('with (obj_knight_twin_bullet) instance_destroy(); kbr_sa_clear();')
go(net, sims, 80)
ok(send(H, 2) == 1, 'player 1 uses Flurry on ROARING')
go(net, sims, 8)
bl = kbr_bullets(C2)
tgs = sorted(set(x[1] for x in bl))
ok(tgs == [2], 'build 49: in player 2\'s game only the pattern aimed at player 2 %r' % tgs)
d = sorted(set(x[2] for x in bl))
ok(len(d) == 1 and abs(d[0] - 20 * 0.5 * 1.3) < 0.01, 'each part: base 20 x ROARING 0.5 x 4-shard step 1.3 = 13 (%r)' % d)

# ---- PACIFY: a heal makes you TIRED
for s in sims:
    s.run('with (obj_knight_twin_bullet) instance_destroy(); kbr_sa_clear();')
C3.run('global.kfo.M.g = 100; kbr_send_state(true);')
C2.run('global.kfo.M.g = 100; kbr_send_state(true);')
H.run('global.kfo.M.g = 100; kbr_send_state(true);')
go(net, sims, 20)
set_mode(H, 5)
go(net, sims, 10)
tgp = host_p(H, 1, 'tg')
ok(len(tgp) == 1, 'PACIFY with nobody TIRED: CHAOS %r' % tgp)
ok(send(C3, 11) == 1, 'player 3 heals (Heal 40)')
go(net, sims, 15)
ok(host_p(H, 1, 'tg') == [3], 'PACIFY goes for the TIRED player 3 %r' % host_p(H, 1, 'tg'))
ok(st_row(H, 3)['ti'] == 1, 'TIRED in the standings')

# ---- the "!" and OUTNUMBERED BONUS (player 2 and player 1 both on player 3)
C3.run('global.kfo.M.tg.exc_t = 0;')
set_mode(H, 4, 3)
set_mode(C2, 4, 3)
go(net, sims, 20)
ok(sorted(J(C3, 'global.kfo.M.tg.att')) == [1, 2], 'player 3 sees two players targeting them %r' % J(C3, 'global.kfo.M.tg.att'))
ok(J(C3, 'global.kfo.M.tg.exc_t') > 0 or J(C3, 'global.kfo.M.tg.exc_n') >= 1, 'the "!" popped over player 3\'s SOUL')
ok(abs(J(C3, 'kbr_tg_outn_mul()') - 1.5) < 1e-6, 'OUTNUMBERED: 2 on you -> the gauge fills x1.5 (%r)' % J(C3, 'kbr_tg_outn_mul()'))
C3.run('global.kfo.M.g = 10; kbr_gauge_add(2, false);')
ok(abs(J(C3, 'global.kfo.M.g') - 13) < 1e-6, 'a +2 to the gauge is +3 for player 3')
# build 49: the callouts are gone - a high charge aimed at me shows nothing
C2.run('global.kfo.M.g = 95; kbr_send_state(true);')
go(net, sims, 20)
ok(J(C3, 'global.kfo.M.tg.call_txt') == '' and J(C3, 'global.kfo.M.tg.call_t') <= 0,
   'build 49: no callout any more (it covered the HP bars): %r' % J(C3, 'global.kfo.M.tg.call_txt'))

# ---- the keys: E / Q change the mode, 1-8 pick, A the next
C2.run('global.kfo.M.tg.mode = 0;')
def keytick(s, keys):
    held = set(keys)
    s.input.pressed = held - s.input.held
    s.input.released = s.input.held - held
    s.input.held = held
    s.input.cleared = set()
    s.run('kbr_tg_tick(global.kfo.M);')
keytick(C2, {ord('E')}); keytick(C2, set())
ok(J(C2, 'global.kfo.M.tg.mode') == 1, 'E: CHAOS -> PROCEED (%r)' % J(C2, 'global.kfo.M.tg.mode'))
keytick(C2, {ord('Q')}); keytick(C2, set()); keytick(C2, {ord('Q')}); keytick(C2, set())
ok(J(C2, 'global.kfo.M.tg.mode') == 6, 'Q twice: PROCEED -> CHAOS -> ROARING (%r)' % J(C2, 'global.kfo.M.tg.mode'))
keytick(C2, {ord('3')}); keytick(C2, set())
ok(J(C2, 'global.kfo.M.tg.mode') == 4 and J(C2, 'global.kfo.M.tg.pick') == 3, '3: CHECK the player in slot 3 (%r, %r)' % (J(C2, 'global.kfo.M.tg.mode'), J(C2, 'global.kfo.M.tg.pick')))
keytick(C2, {ord('A')}); keytick(C2, set())
ok(J(C2, 'global.kfo.M.tg.pick') == 1, 'A: the next standing player after 3 is 1 (%r)' % J(C2, 'global.kfo.M.tg.pick'))
ok(J(C2, 'kfo_key("hold")') == ord('D') and J(C2, 'kfo_key("quick")') == ord('F'), 'HOLD SLOT moved to D, QUICK SETTINGS to F')

# ---- a knockout by a skill: credit, shards (1 + half the victim's), retarget at once
go(net, sims, 10)
H.run('kfo_host_player(1).sh = 0; kfo_host_player(3).sh = 4; kfo_host_player(2).sh = 0;')
set_mode(H, 4, 3)
go(net, sims, 10)
C3.run('global.kfo.M.lby = 2; kbr_local_death();')
go(net, sims, 40)
ok(host_p(H, 2, 'sh') == 3, 'player 2 knocked out player 3: 1 + half of 4 = 3 shards (%r)' % host_p(H, 2, 'sh'))
ok(host_p(H, 2, 'kos') == 1, 'one knockout for player 2')
ok(host_p(H, 1, 'tg') == [2], 'player 1 (CHECK on 3) retargets the next standing player (%r)' % host_p(H, 1, 'tg'))
ok(st_row(H, 2)['sh'] == 3, 'the shards reach the standings')
ok(abs(J(H, 'kbr_tg_shard_mul(3)') - 1.15) < 1e-6, '3 shards: step 1 (x1.15)')
feed = ' '.join(x[1] for x in J(H, 'global.kfo.H.feed'))
ok('knocked out' in feed, 'the feed says who knocked out whom')

# ---- the final two (2 left of 3): the next cycle is the Roaring
ok(J(H, 'global.kfo.H.ft_done'), 'two left: the final two was announced')
k = J(H, 'global.kfo.H.ftk')
ok(J(H, 'kbr_tl_get(global.kfo.H.tl, %d).roar' % k), 'the first cycle of the final two is a Roaring')

print('frames done', round(time.time() - t0, 1), 's', flush=True)

# ---- TARGETING OFF: the old behaviour (every rival, no tg in the message, no shards)
net, sims = make_room(3, 'lan', 4849, setx='_s.mhp = 300; _s.cdm = 25; _s.tg = 0;')
H, C2, C3 = sims
go(net, sims, 330)
ok(not J(H, 'kbr_tg_on(global.kfo.M.eff)'), 'TARGETING OFF in the room')
for _ in range(40):
    if all(J(s, 'global.kfo.M.R.ph') == 'run' for s in sims):
        break
    go(net, sims, 10)
ok(send(H, 1) == 1, 'player 1 uses Sword (untargeted)')
go(net, sims, 8)
b = [kbr_bullets(s) for s in sims]
ok(len(b[0]) == 0 and len(b[1]) >= 1 and len(b[2]) >= 1, 'only the rivals make it, around their own SOUL (%r)' % [len(x) for x in b])
ok(all(x[0] == 1 for x in b[1] + b[2]), 'build 50: the old path\'s sends know their sender too (the real objects carry it: credit)')
C3.run('global.kfo.M.lby = 2; kbr_local_death();')
go(net, sims, 40)
ok(host_p(H, 2, 'sh') == 0, 'no shards with TARGETING OFF')
ok(J(H, 'kfo_preset_apply(8).tg') == 0 and J(H, 'kfo_preset_name(8)') == 'UNTARGETED', 'the UNTARGETED preset turns it off')

print('PASS' if not FAILS else 'FAIL', N[0] - len(FAILS), '/', len(FAILS), round(time.time() - t0, 1), 's')
sys.exit(1 if FAILS else 0)
