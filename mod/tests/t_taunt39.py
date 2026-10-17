"""Build 39: when Susie is not in the fight, the first of Ralsei / Noelle in party order who is standing says her talk-phase lines
(turns 6-14) in their own words, in their own balloon voice and spot (Ralsei 74, Noelle 76); Noelle as the Angel on a Weird Route
save; Kris never speaks. Susie keeps her lines, naming the friends who are really there (Normal / Supercharged / Thorn used to name
Kris and Ralsei whoever was in the party). Kaizo's frozen check and Violet's Side B are respected; the Cyan Knight gets joke lines;
the narration before the Roaring names whoever is there. Runs the real merged talk phase of every knight in the emulator."""
import sys, os, time, re
SRC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 't_wr38.py')).read()
exec(SRC[:SRC.index('t0 = time.time()')])   # setup(), scene(), end_turn(), ok(), eq() from the build 38 Weird Route test
t0 = time.time()
VOICE = {74: 3, 75: 2, 76: 4}

def talk(sim, turn):
    """one enemy talk phase at balloonturn `turn` (6..14): returns [(speaker, text, x, y)] for every balloon it shows"""
    sim.calls.clear()
    sim.run('global.K.balloonturn = %d; global.K.talked = 0; global.K.end_cutscene_version = 0; global.mnfight = 1; global.myfight = 0; '
            'global.K.myblcon = instance_create(0, 0, obj_b39bl); with (obj_writer) instance_destroy();' % (turn - 1))
    out = []
    for i in range(4):
        good, err = auto(sim, lambda: sim.step(1))
        assert good, err
        for c in sim.calls:
            if c[0] == 'scr_enemyblcon':
                out.append((VOICE.get(c[-1], c[-1]), c[-2], c[1], c[2]))
        sim.calls.clear()
        sim.run('with (obj_writer) instance_destroy(); global.K.myblcon = instance_create(0, 0, obj_b39bl);')
        if sim.eval('global.K.talked') not in (0.6, 0.7) and i > 0:
            break
    return out

def mk39(key, party, weird=0, **kw):
    sim = setup(key, party, weird=weird, **kw)
    try: sim.define_object('obj_b39bl')
    except Exception: pass
    sim.run('global.flag[456] = %d;' % weird)
    return sim

def plain(s):
    return re.sub(r'\\\\c\w|\^\d', '', s).replace('/%', '')

def width_ok(s):
    return all(len(seg) <= 25 for seg in plain(s).split('&'))

# ---------- who speaks, in which voice and where ----------
CASES = [
    # key, party, weird, turn, want speaker, want first line, want second line (None: single balloon)
    ('base', [1, 3, 4], 0, 6, 3, 'Haha.../%', "We're... still&standing! Kris,&we're still standing!/%"),
    ('base', [1, 4, 3], 0, 6, 4, 'Faha.../%', "D-didn't think&we'd still be&standing, did you?/%"),
    ('base', [1, 4, 3], 1, 6, 4, 'Haha... haha.../%', "Didn't... think we'd&still be standing...?&...Me neither./%"),
    ('base', [1, 2, 3], 0, 6, 2, 'Heheh.../%', "Didn't... think&we'd still be&standing, did you?/%"),
    ('base', [2, 4, 0], 0, 8, 2, "You? You're all&damn alone.../%", 'Me? I got...&Noelle here&behind me./%'),
    ('base', [1, 3, 4], 0, 8, 3, "You're... all alone,&aren't you...?/%", "...I'm not.&I have Kris&and Noelle here./%"),
    ('base', [4, 1, 0], 0, 7, 4, 'Th-thing is,&you actually.../%', 'You actually messed&up, picking a fight&with... with US!/%'),
    ('base', [3, 0, 0], 0, 7, 3, "I don't think&you understand.../%", "I'm not going to&give up. My friends&are counting on me!/%"),
    ('base', [4, 1, 0], 1, 12, 4, "You can't win...!&So give up...!&GIVE UP!!!/%", None),
    ('base', [4, 1, 0], 1, 8, 4, "You're... all alone,&aren't you...?/%", 'Me? I have Kris.&Kris is ALWAYS&behind me.../%'),
    ('base', [4, 3, 0], 1, 13, 4, "... You won't&even.../%", "...say a thing...&...It's so quiet.&It's so cold.../%"),
    ('base', [1, 3, 0], 0, 11, 3, 'So... please...&stop this.../%', None),
    ('elec', [4, 3, 1], 0, 6, 4, 'Faha.../%', "D-didn't think&we'd still be&standing, did you?/%"),
    ('thorn', [3, 1, 4], 0, 13, 3, "... You won't&even.../%", "...tell us why&you're doing this...?/%"),
    ('violet', [3, 4, 0], 0, 6, 3, 'Haha.../%', "We're... still&standing! Noelle,&we're still standing!/%"),
    ('kaizo', [1, 3, 4], 0, 6, 3, 'Haha.../%', "We're... still&standing! Kris,&we're still standing!/%"),
    ('kaizo', [1, 2, 3], 0, 6, 2, 'Heheh.../%', "Didn't... think&we'd still be&standing, did you?/%"),
    ('cyan', [1, 3, 4], 0, 6, 3, '\\c5Um, so.../%', '\\c5Is anyone else&worried about what&the Knight is doing?/%'),
    ('cyan', [1, 2, 3], 0, 6, 2, '\\c5So, uh.../%', '\\c5Anyone gonna comment on&what the HELL the&Knight is doing...?/%'),
]
for key, party, weird, turn, who, l1, l2 in CASES:
    name = '%s %s%s T%d' % (key, party, ' weird' if weird else '', turn)
    sim = mk39(key, party, weird)
    out = talk(sim, turn)
    want = [l1] + ([l2] if l2 else [])
    eq([o[0] for o in out], [who] * len(want), name + ': who speaks (voice)')
    eq([o[1] for o in out], want, name + ': the lines')
    sim.run('global.HX = knight_hero_inst(%d).x; global.HY = knight_hero_inst(%d).y;' % (who, who))
    hx, hy = sim.eval('global.HX'), sim.eval('global.HY')
    off = (92, 38) if who == 2 else (85, 45)
    ok(all((o[2], o[3]) == (hx + off[0], hy + off[1]) for o in out), name + ': the balloon comes from the speaker (%s)' % [(o[2], o[3]) for o in out])
    print(name, 'ok %.0fs' % (time.time() - t0), flush=True)

# ---------- nobody speaks ----------
for key, party, kw, why in (('base', [1, 0, 0], {}, 'Kris alone (Kris never speaks)'), ('base', [1, 3, 4], {'practice': 1}, 'practice'),
                            ('kaizo', [1, 3, 0], {'practice': 1}, 'Kaizo practice')):
    sim = mk39(key, party, **kw)
    if kw.get('practice'):
        sim.run('global.K.practicemode = 1;')
    out = talk(sim, 6)
    eq(out, [], '%s %s: %s - no balloon' % (key, party, why))
# the hub's own practice flag alone is enough too
sim = mk39('base', [1, 3, 4])
sim.run('global.krun.practice = true; global.K.practicemode = 0;')
eq(talk(sim, 6), [], 'base KRN with the hub in practice: no balloon')
# the speaker is down: the next one in party order speaks; both down: nobody
sim = mk39('base', [1, 3, 4])
sim.run('global.hp[3] = 0;')
eq([o[0] for o in talk(sim, 6)], [4, 4], 'base KRN with Ralsei down: Noelle speaks instead')
sim.run('global.hp[4] = 0;')
eq(talk(sim, 6), [], 'base KRN with Ralsei and Noelle down: nobody')
# Susie down (but here): nobody takes her lines (as before)
sim = mk39('base', [2, 3, 4])
sim.run('global.hp[2] = 0;')
eq(talk(sim, 6), [], 'base SRN with Susie down: nobody (the fight\'s own rule)')
# the Weird Route took Susie: the next one speaks
sim = mk39('base', [1, 3, 2])
sim.run('global.krun.wr.slain[2] = true; global.hp[2] = -9999;')
eq([o[0] for o in talk(sim, 6)], [3, 3], 'base KRS with Susie taken by the Knight: Ralsei speaks')
# Violet Side B: after the first loss the survivors' own talk takes over
sim = mk39('violet', [3, 4, 0])
sim.run('global.K.vb_losses = 1;')
eq(talk(sim, 6), [], 'violet RN after a loss: no stand-in taunts')
# Kaizo: a frozen speaker only shakes
sim = mk39('kaizo', [1, 3, 4])
sim.run('global.K.k_freeze = [0, 0, 0, 1, 0];')
eq(talk(sim, 6), [], 'kaizo KRN with Ralsei frozen: no balloon (he shakes)')

# ---------- friends down: the beats change ----------
sim = mk39('base', [3, 4, 0])
sim.run('global.hp[4] = 0;')
eq([o[1] for o in talk(sim, 9)], ['Even if you&knock her down.../%', "I'll heal her.&As many times&as it takes!/%"], 'base RN, Noelle down: Ralsei T9')
eq([o[1] for o in talk(sim, 10)], ["As long as I'm&here to lift her&back up.../%", "...we won't lose.&We won't!/%"], 'base RN, Noelle down: Ralsei T10')
sim = mk39('base', [2, 4, 0])
sim.run('global.hp[4] = 0;')
eq([o[1] for o in talk(sim, 9)], ['Even... even if&you knock her down.../%', "As long as&I'm here.../%"], 'base SN, Noelle down: Susie T9 names her (was "them", Kris and Ralsei)')

# ---------- every beat, every voice: a line for each, short enough for the balloon ----------
for key, party, weird, who in (('base', [3, 1, 4], 0, 3), ('base', [4, 1, 3], 0, 4), ('base', [4, 1, 3], 1, 4), ('base', [3, 0, 0], 0, 3), ('base', [4, 0, 0], 0, 4),
                               ('cyan', [3, 1, 4], 0, 3), ('cyan', [4, 1, 0], 0, 4)):
    sim = mk39(key, party, weird)
    seq = []
    for turn in range(6, 15):
        out = talk(sim, turn)
        seq += out
        ok(len(out) >= 1 and all(o[0] == who for o in out), '%s %s%s T%d: %s speaks (%s)' % (key, party, ' weird' if weird else '', turn, who, out))
    lines = [o[1] for o in seq]
    eq(len(lines), 19 if key == 'cyan' else 17, '%s %s%s: all the beats (%d balloons; 3-part lines on turns 14 and the Cyan 9/10)' % (key, party, ' weird' if weird else '', len(lines)))
    bad = [l for l in lines if not width_ok(l) and 'GOD.' not in l]
    eq(bad, [], '%s %s%s: every line fits the balloon (25 characters a row)' % (key, party, ' weird' if weird else ''))
    if key != 'cyan':
        orig = set(['Heheh.../%', "Didn't... think&we'd still be&standing, did you?/%", '... people like you...&just piss me off./%'])
        eq([l for l in lines if l in orig], [], '%s %s: none of Susie\'s own lines' % (key, party))
    print(key, party, weird, 'beats ok %.0fs' % (time.time() - t0), flush=True)

# ---------- the Cyan Knight's narration after the first line ----------
sim = mk39('cyan', [1, 3, 4])
talk(sim, 6)
sim.run('with (global.K) global.TMP = knight_cyan_shake("ORIG");')
eq(sim.eval('global.TMP'), "* Kris doesn't respond. They're dead.&* Noelle shakes her head.", 'cyan KRN: the narration names who is there')
sim = mk39('cyan', [1, 2, 3])
talk(sim, 6)
sim.run('with (global.K) global.TMP = knight_cyan_shake("ORIG");')
eq(sim.eval('global.TMP'), 'ORIG', "cyan KSR: the mod's own narration")

# ---------- the narration before the Roaring ----------
for key, party, weird, up, want in (('base', [1, 3, 4], 0, True, '* Ralsei grew pale.'), ('base', [1, 4, 3], 0, True, '* Noelle grew pale.'),
                                    ('base', [1, 4, 3], 1, True, '* The Angel grew pale.'), ('base', [1, 0, 0], 0, True, '* Kris grew pale.'),
                                    ('base', [1, 2, 3], 0, True, '* Susie grew pale.'), ('base', [1, 3, 0], 0, False, '* Ralsei struggled to give some kind of warning.')):
    sim = mk39(key, party, weird)
    if not up:
        sim.run('global.hp[3] = 0;')
    sim.run('with (global.K) global.TMP = knight_pale_up();')
    eq(bool(sim.eval('global.TMP')), up, '%s %s: up' % (key, party))
    sim.run('with (global.K) global.TMP = knight_pale_text(%d, "Susie");' % (0 if up else 1))
    eq(sim.eval('global.TMP'), want, '%s %s%s: %s' % (key, party, ' weird' if weird else '', want))
rd = lambda f: open(M + f, encoding='utf8', errors='replace').read()
STEP = rd('gml_Object_obj_knight_enemy_Step_0.gml')
eq(STEP.count('knight_pale_text(0, "Susie")'), 5, 'pale line hooked in Normal, Supercharged, Thorn (x2), Cyan')
eq(STEP.count('knight_pale_name(susietitle)'), 2, 'pale lines hooked in Violet (its titles)')
eq(len(re.findall(r'knight_taunt_balloon\(\);', STEP)), 12, 'the talk-phase balloons of all six knights go through the speaker (2 each)')
# ---------- Ralsei stays Ralsei: no demands, threats or anger in any of his lines ----------
ralsei_all = []
for party in ([3, 1, 4], [3, 0, 0], [3, 4, 0]):
    for down in (False, True):
        sim = mk39('base', party)
        if down:
            sim.run('global.hp[4] = 0; global.hp[1] = 0;')
        for turn in range(6, 15):
            ralsei_all += [o[1] for o in talk(sim, turn) if o[0] == 3]
BAD = ['DEMAND', 'demand', 'polite', 'Mr. Knight', 'piss', 'hate', 'mad', 'won\'t let you', 'make you', 'pay', 'destroy', 'END YOU']
eq(sorted(set(l for l in ralsei_all for w in BAD if w in l)), [], 'Ralsei never demands, threatens or rages (%d lines checked)' % len(ralsei_all))

# ---------- Noelle's N-Action: the Angel's own words on a Weird Route save ----------
def nact(sim, n):
    sim.mock('scr_nextact', 0)
    sim.run('global.K.actingnoe = 1; global.K.actconnoe = 1; global.K.actcon = 0; global.myfight = 3; global.msgno = 0; global.msg = array_create(20, ""); '
            'global.charname = ["", "Kris", "Susie", "Ralsei", "Noelle"]; global.K.nactcount = %d;' % (n - 1))
    good, err = auto(sim, lambda: sim.step(1))
    assert good, err
    return ' | '.join(str(sim.eval('global.msg[%d]' % i)) for i in range(12) if sim.eval('global.msg[%d]' % i))
for key in ('base', 'elec', 'violet', 'thorn', 'cyan'):
    sim = mk39(key, [1, 4, 3], 1)
    txt = nact(sim, 1)
    ok("I'M the scary thing" in txt and '\\Ee' in txt and 'h-hello' not in txt, key + ' N-Action on a Weird Route: the Angel (%s)' % txt[:160])
    txt = nact(sim, 2)
    ok("It's so cold, Kris" in txt, key + ' second N-Action on a Weird Route (%s)' % txt[:120])
    sim = mk39(key, [1, 4, 3], 0)
    txt = nact(sim, 1)
    ok("You d-don't have to do this" in txt and 'stronger' not in txt, key + ' N-Action otherwise: as before (%s)' % txt[:120])

# the Kaizo Knight keeps its own Noelle ACT (the mod's: "a strange chill made her unable to speak")
sim = mk39('kaizo', [1, 4, 3], 1)
txt = nact(sim, 1)
ok('a strange chill' in txt, "kaizo N-Action: the mod's own Noelle lines (%s)" % txt[:100])
print('taunt39 tests', N[0], 'fails', len(FAILS), '%.0fs' % (time.time() - t0)); sys.exit(1 if FAILS else 0)
