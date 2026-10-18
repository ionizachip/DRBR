// ===== DRBR: SPAMTON NEO (DELTARUNE Chapter 2's boss, encounter 61) =====
// Online only. His pieces are Chapter 2's own objects (make_spamton.py: obj_sn_*, from the player's Chapter 2 data.win): the
// flying heads and their bullets, the RECREW mail walls and their bombs, the wire hearts he pulls from his chest, the phone and
// its pipis thrower, eggs and their little heads, the phone hands, the face and its eye lasers, the final forme, its dollars and
// BIG SHOTs. His body is Chapter 2's own drawing (his Create's parts and wires, his Draw's dances). This file is his battle
// object (obj_sn_neo: the knights' arm / hold / attack handshake, his box for each attack, his lines), the YELLOW SOUL (every
// player's own: the confirm key fires, hold it for a BIG SHOT - obj_sn_ysoul drives it on the battle's SOUL), the background
// (Chapter 2's basement ride: black, the three coaster rails racing by, the cityscape), the clean-up.
// ONE YELLOW SOUL PER GAME. Every game runs the same attack (the same set-up, the same pieces from the same seeds, started on
// the same tick). What a player's shots break is that game's own, and so is what it does to the attack's length - Chapter 2's
// own rules: shooting the big heart, breaking the face, clearing the pipis end YOUR attack sooner (your game then waits for
// the next shared attack). Each piece draws from its own stream (kbr_p_*): a broken egg in one game never moves another game's
// hearts. Source survey: online/notes/src_spamton.md.

function kbr_enc_def_spamton()
{
    // [phase, id, name, flags] in Chapter 2's own order (his user event 0: turns 1-6, then 7-12 - phase 2 - then the HP-30%
    // turns - phase 3 - and the finale in the Roaring's place, flags 2). rr / dif: Chapter 2's attack and its variant. tt: the
    // attack's place in the timeline - Chapter 2's own turn timer when nobody shoots (measured: t_spamton53.py) plus a margin;
    // a player who shoots well ends it sooner in their own game.
    return { key: "spamton", cat: "secret", fid: KBR_FAM_SPAMTON, chapter: 2, soul: "yellow", sends: [45, 46, 47, 48, 49, 50], song: "BIG SHOT - Toby Fox",
        desc: "Chapter 2's secret boss. A YELLOW SOUL:#Z shoots, hold Z for a BIG SHOT!",
        name: "Spamton NEO", short: "NEO", title: "SPAMTON NEO", col: make_color_rgb(255, 120, 200), lu: KBR_ENC_BASE + 3,
        music: "spamton_neo_mix_ex_wip.ogg", obj: "obj_sn_neo", spr: "spr_sneo_example", px: 460, py: 80, roar: 14, roar_dur: 1230,
        atk: [[1, 0, "Flying Heads", 0], [1, 1, "RECREW Columns", 0], [1, 2, "Heart Attack", 0], [1, 3, "Pipis Call", 0],
              [1, 4, "Phonehands", 0], [1, 5, "Look In My Eyes", 0],
              [2, 6, "Heart Attack II", 0], [2, 7, "BIG SHOT Dance", 0], [2, 8, "Look In My Eyes II", 0], [2, 9, "Phonehands II", 0],
              [2, 10, "Pipis Call II", 0], [2, 11, "RECREW Columns II", 0],
              [3, 12, "Heart Attack III", 0], [3, 13, "Pipis Call III", 0], [4, 14, "NEO Finale", 2]],
        rr: [0, 6, 2, 8, 8.5, 7, 2, 0, 7, 8.5, 8, 6, 2, 8, 9],
        dif: [1, 0, 0, 0, 0, 0, 2, 3, 0, 2, 1, 1, 1, 3, 0],
        tt: [270, 360, 780, 640, 290, 330, 780, 330, 330, 290, 660, 360, 880, 270, 1230],
        // his line before the attack (Chapter 2's, the first time each comes in this match); a phone call that talks (its first
        // ring, and Pipis Call III) says its own lines instead
        line: ["KRIS! ISN'T THIS&[Body] JUST [Heaven]LY!?", "WE'LL TURN THOSE&[Schmoes] AND [Daves]&INTO [Rosen Graves]",
               "KRIS, DON'T YOU&WANNA BE [Part]&OF MY BEAUTIFUL [Heart]?!", "ALL YOU GOTTA&DO IS [Big].",
               "IT'S CALLING, KRIS...&MY [Heart]...&MY [Hands]...", "KRIS!&CAN YOU REALLY&LOOK IN MY [Eyes]&AND SAY NO!?",
               "I CAN'T STAND IT!!!&I THINK I'M GONNA&HAVE A [HeartAttack]!", "KRIS, I'LL EVEN&GIVE YOU A&[Free Value]",
               "KRIS. IF YOU GIVE&ME THAT [Soul] I&WILL GIVE YOU&EVERYTHING I HAVE.", "[Friends]!? KRIS!?&WHAT ARE YOU&TALKING ABOUT!?",
               "DON'T YOU&WANNA HELP YOUR&OLD PAL SPAMTON?", "BUT KRIS, IF YOU&REFUSE. THAT'S YOUR&CHOICE. I CAN'T&FORCE YOU.",
               "KRIS!!! TAKE THE&DEAL!!! TAKE IT!!!", "OR...&DID YOU WANT&TO BE...", "KRIS...&I WON'T FORCE YOU.&I CAN'T.&I CAN'T FORCE YOU."],
        again: ["CAN A [Little&Sponge] DO THIS?", "[BreaKing] and&[CracKing]", "[The Smooth&Taste Of] NEO", "THE [@$@!] TASTE&OF SPAMTON",
                "DON'T YOU&WANNA BE A&BIG SHOT?", "[Clown]!? NO!!!&I FEEL SICK!!!"],
        flavor: ["* The stage lights are shattered.", "* It pulls the strings and makes them ring.", "* The air crackles with freedom.", "* Smells like rotten glass."],
        // his pieces that are not bullets (the cut's own clean-up never sees them)
        objs: [obj_sn_armtel, obj_sn_wallctrl, obj_sn_heartlaser, obj_sn_heartbomb, obj_sn_headpuff, obj_sn_pipthrow, obj_sn_pipfx, obj_sn_pippiece, obj_sn_pipwall,
               obj_sn_armsmoke, obj_sn_facetarget, obj_sn_crescent, obj_sn_formemouth, obj_sn_playback, obj_sn_lastattack, obj_sn_lasthit, obj_sn_smoke, obj_sn_wpipis,
               obj_sn_yshot, obj_sn_yshotanim, obj_sn_ytrail, obj_sn_yspark, obj_sn_superend],
        // the ones that read the box (a send's go when the box does, between two attacks)
        boxy: [obj_sn_wallctrl, obj_sn_wallcell, obj_sn_wallbomb, obj_sn_pipthrow, obj_sn_pipwall, obj_sn_handhead, obj_sn_phonehand, obj_sn_face],
        cut: kbr_sn_cut };
}

// ---------- his battle object's fields, as his pieces read them (a send: Spamton not on stage - the defaults) ----------
function kbr_sn_gv(_f)
{
    var _g = instance_find(obj_sn_neo, 0);
    if (_g != noone && variable_instance_exists(_g, _f))
        return variable_instance_get(_g, _f);
    switch (_f)
    {
        case "x":
        case "xstart":
            return camerax() + 460;
        case "y":
        case "ystart":
            return cameray() + 80;
        case "image_alpha":
            return 1;
        case "heart_health":
            return 25;
        case "eyeshp":
        case "nosehp":
        case "mouthhp":
            return 16;
        case "depth":
            return 0;
    }
    return 0;
}

// a read of his attack's controller (obj_sn_bc) by one of his pieces: its value, or - a sent piece, no attack of his running -
// the default (target 3: whoever is hit)
function kbr_sn_bcv(_f)
{
    var _c = instance_find(obj_sn_bc, 0);
    if (_c != noone && variable_instance_exists(_c, _f))
        return variable_instance_get(_c, _f);
    if (_f == "target")
        return 3;
    return 0;
}

function kbr_sn_on()
{
    return kbr_enc_is("spamton");
}

// ---------- the turn timer (Chapter 2's pieces end or stretch their attack: make_spamton.py routes their writes here) ----------
// His own pieces write the battle's timer, as in Chapter 2 (this game's attack ends sooner - or later - only here); a SENT piece
// never touches anybody's attack (its send's end is its own).
function kbr_sn_tt(_v)
{
    if (!kbr_mine())
        return 0;
    global.turntimer = _v;
    return 1;
}

function kbr_sn_tt_sub(_v)
{
    if (!kbr_mine())
        return 0;
    global.turntimer -= _v;
    return 1;
}

// Chapter 2's SOUL colour switches (the final forme swallowing the SOUL, giving it back): the yellow SOUL's driver
function kbr_sn_heart_yellow(_on)
{
    if (!kbr_mine())
        return 0;
    with (obj_sn_ysoul)
        kbr_sn_ys_on(_on && kbr_sn_attacking());
    return 1;
}

// NEO's user event 2 (Chapter 2: a share of every member's HP) online: one hit through the room's table, from the piece that
// hits (self) - the forme's bite, a BIG SHOT, a dollar
function kbr_sn_hurt()
{
    if (global.inv >= 0)
        return 0;
    if (!variable_instance_exists(id, "target") || target < 0)
        target = 3;
    if (!variable_instance_exists(id, "damage") || damage < 0)
        damage = 10;
    scr_damage_all();
    return 1;
}

// one of his attacks is running in this game (from its start to its cut)
function kbr_sn_attacking()
{
    return variable_global_exists("kbr_sn_dirty") && global.kbr_sn_dirty;
}

// ---------- his battle object (obj_sn_neo): Chapter 2's Create runs first (his parts, wires, the head box), then this ----------
function kbr_sn_create()
{
    myself = 0;
    attacked = 1;
    talked = 1;
    acting = 0;
    rtimer = 0;
    rr = 0;
    difficulty = 0;
    hellmode = 0;
    say = "";
    say_t = 0;
    say_max = 75;
    said = [];
    phoneevent = 0;
    // (the Chapter 2 battle object's own fields his pieces read)
    target = 3;
    damage = 10;
    mytarget = 0;
    visible = true;
    global.sp = 4;
    // his background: in front of the arena, behind everything of the battle (Jevil's place)
    if (!instance_exists(obj_sn_bg))
        instance_create_depth(0, 0, 49000, obj_sn_bg);
    // the YELLOW SOUL's driver (one per game; the SOUL is yellow only while one of his attacks runs)
    if (!instance_exists(obj_sn_ysoul))
        instance_create_depth(0, 0, -100, obj_sn_ysoul);
    return 1;
}

function kbr_sn_step()
{
    if (!kbr_on())
        exit;
    if (say_t > 0)
        say_t--;
    // the knights' handshake: his box at 1.5 (Chapter 2's for the attack: its place and size), his move to his spot for it,
    // then the count held at 11 by the shared clock, the attack at 12
    if (global.mnfight == 1.5)
    {
        kbr_sn_arm();
        global.mnfight = 2;
        scr_turntimer(90);
    }
    if (global.mnfight == 2 && attacked == 0)
    {
        rtimer += kbr_rgate();
        if (rtimer == 12)
        {
            kbr_sn_attack();
            attacked = 1;
        }
    }
    // Chapter 2's End Step part: no controller -> his head at rest
    if (!instance_exists(obj_sn_bc))
    {
        idealx[5] = 0;
        idealrot[5] = 0;
        partsiner[5] = 0;
        partrot[5] = 0;
        partx[5] = 0;
        party[5] = 0;
        partxoff[5] = sprite_get_xoffset(partsprite[5]) * 2;
        partyoff[5] = sprite_get_yoffset(partsprite[5]) * 2;
    }
    return 1;
}

// the attack of the cycle this arm is for: Chapter 2's box for it (instance_create at the view's 245, 170, then its offsets and
// size), his move to his spot (scr_move_to_point_over_time), the SOUL; his own state as every game has it at this cycle (a
// game that skipped a cycle - or whose player broke something last time - starts it like every other)
function kbr_sn_arm()
{
    var _d = kbr_enc_by_key("spamton");
    var _ai = clamp(global.knight_lu.plan_i, 0, array_length(_d.rr) - 1);
    rr = _d.rr[_ai];
    difficulty = _d.dif[_ai];
    hellmode = 0;
    // the counters Chapter 2 keeps on him (the face's first time, the phone's first call): from the timeline, so a game that
    // skipped a cycle counts the same
    var _M = kbr_match();
    faceattackcount = 0;
    phoneevent = 0;
    if (is_struct(_M) && _M.R.arm_k >= 0)
    {
        var _c = kbr_tl_get(_M.tl, _M.R.arm_k);
        for (var _j = 0; _j < _c.k; _j++)
        {
            var _cj = kbr_tl_get(_M.tl, _j);
            if (_cj.reg != _d.lu)
                continue;
            var _rj = _d.rr[clamp(_cj.ai, 0, array_length(_d.rr) - 1)];
            if (_rj == 7)
                faceattackcount++;
            if (_rj == 8 && _d.dif[clamp(_cj.ai, 0, array_length(_d.dif) - 1)] != 3)
                phoneevent++;
        }
    }
    // his look and his pieces' memory at rest
    with (obj_move_to_point)
    {
        if (variable_instance_exists(id, "target") && instance_exists(target) && target.object_index == obj_sn_neo)
            instance_destroy();
    }
    x = xstart;
    y = ystart;
    image_alpha = 1;
    partmode = 1;
    makeheart = 0;
    makeheartinit = 0;
    makeheartalt = 0;
    heart_release_con = 0;
    // (what the player broke of his face stays broken for his next face attack - Chapter 2's own rule, this game's own)
    if (!instance_exists(obj_growtangle))
        instance_create(camerax() + 245, cameray() + 170, obj_growtangle);
    var _b = instance_find(obj_growtangle, 0);
    global.kbr_sn_box = { x: _b.x, y: _b.y, mxs: variable_instance_exists(_b, "maxxscale") ? _b.maxxscale : _b.image_xscale,
        mys: variable_instance_exists(_b, "maxyscale") ? _b.maxyscale : _b.image_yscale };
    var _ox = 0;
    var _oy = 0;
    var _mx = 2;
    var _my = 2;
    switch (rr)
    {
        case 0:
            _ox = 54;
            _mx = 3.2;
            _my = 1.5;
            chargesfxtimer = 0;
            dance_timer = 0;
            armaim = -80;
            if (difficulty == 3)
            {
                scr_rememberxy();
                scr_move_to_point_over_time(x + 50, y, 8);
            }
            break;
        case 7:
            _ox = 15;
            scr_rememberxy();
            break;
        case 8:
            scr_rememberxy();
            scr_move_to_point_over_time(x, cameray() + 20, 8);
            break;
        case 8.5:
            _ox = 64;
            _oy = 8;
            _mx = 3.2;
            _my = 1.5;
            break;
        case 6:
            _ox = 58;
            _mx = 3.3333333333333335;
            _my = 2.3;
            scr_rememberxy();
            scr_move_to_point_over_time(x + 200, y, 16);
            break;
        case 9:
            _oy = 10;
            _mx = 2.5;
            _my = 1.9;
            break;
    }
    with (obj_growtangle)
    {
        x = (camerax() + 245) + _ox;
        y = (cameray() + 170) + _oy;
        maxxscale = _mx;
        maxyscale = _my;
    }
    global.kbr_sn_dirty = true;
    if (!instance_exists(obj_moveheart) && !instance_exists(obj_heart))
        scr_moveheart();
    return 1;
}

// the attack (self = obj_sn_neo; the frame the shared clock releases it): Chapter 2's controller (or his phone), the turn timer
// Chapter 2 gives it, the yellow SOUL, his line
function kbr_sn_attack()
{
    var _d = kbr_enc_by_key("spamton");
    var _ai = clamp(global.knight_lu.plan_i, 0, array_length(_d.rr) - 1);
    rr = _d.rr[_ai];
    difficulty = _d.dif[_ai];
    global.monsterattackname[0] = _d.atk[_ai][2];
    global.kbr_sn_dirty = true;
    // his pieces' streams start from the cycle's seed (the same in every game)
    var _M = kbr_match();
    var _cy = (is_struct(_M) && _M.R.k >= 0) ? kbr_tl_get(_M.tl, _M.R.k) : undefined;
    kbr_p_cycle(is_struct(_cy) ? kbr_mix(_cy.seed, 2207) : 1);
    global.kbr_sn_lgs = kbr_rng(is_struct(_cy) ? kbr_mix(_cy.seed, 991) : 991);
    var _talk = false;
    var _dc = noone;
    if (rr == 8)
    {
        // the phone (it makes the pipis' controller itself); its first call (and the last one, his own) talks
        _dc = instance_create(x - 10, y + 20, obj_sn_phonecall);
        _dc.isattack = 1;
        _dc.target = mytarget;
        if (difficulty == 3)
        {
            phoneevent = 2;
            _talk = true;
        }
        else
        {
            if (phoneevent >= 1)
                _dc.skipintro = 1;
            else
                _talk = true;
            phoneevent++;
        }
    }
    else
    {
        // (Chapter 2's scr_bulletspawner: the controller's creator, target and damage are his)
        _dc = scr_bulletspawner(x, y, obj_sn_bc);
        _dc.type = (rr == 0) ? 0 : ((rr == 2) ? 1.5 : ((rr == 6) ? 6 : ((rr == 8.5) ? 8.5 : ((rr == 7) ? 12 : 9))));
        _dc.special = 0;
        if (rr == 9)
            _dc.target = 3;
        if (rr == 7)
            faceattackcount++;
    }
    // Chapter 2's turn timer for it (his Step: scr_turntimer after the controller - the controller's own first step may set
    // another: the flying heads 240 / 300 / 360, the finale 1200, the phone 430 until its pipis come)
    global.turntimer = 260;
    if (rr == 2)
        global.turntimer = (difficulty == 1) ? 850 : 750;
    if (rr == 6)
        global.turntimer = 330;
    if (rr == 7)
        global.turntimer = 300;
    // the YELLOW SOUL from now to the cut (Chapter 2: scr_heartcolor("yellow") with every one of his attacks)
    with (obj_sn_ysoul)
        kbr_sn_ys_on(true);
    if (!_talk)
        kbr_sn_say(_d, _ai);
    return 1;
}

// his line for attack _ai: its own the first time in this match, then one of his repeats; his laugh
function kbr_sn_say(_d, _ai)
{
    var _first = true;
    for (var _i = 0; _i < array_length(said); _i++)
    {
        if (said[_i] == _ai)
            _first = false;
    }
    if (_first)
    {
        array_push(said, _ai);
        kbr_sn_line(_d.line[clamp(_ai, 0, array_length(_d.line) - 1)], 75);
    }
    else
        kbr_sn_line(_d.again[kbr_irandom(array_length(_d.again) - 1)], 60);
    if (rr == 9)
        snd_play(snd_sneo_laugh_long);
    else
        snd_play(snd_spamton_laugh);
    return 1;
}

// a line in his balloon for _n frames (Chapter 2's text: "&" breaks lines; the end codes go)
function kbr_sn_line(_txt, _n)
{
    var _t = string(_txt);
    var _p = string_pos("/", _t);
    if (_p > 0)
        _t = string_copy(_t, 1, _p - 1);
    say = _t;
    say_t = _n;
    say_max = max(1, _n);
    return 1;
}

// after Chapter 2's Draw (his body): his balloon (Spamton's: white, left of him), faded in its last 10 frames
function kbr_sn_draw_extra()
{
    if (say_t > 0)
        kbr_enc_say(x - 10, y - 20, x + 165, y + 172, say, min(1, say_t / 10));
    return 1;
}

// his body's look (make_spamton.py: his Draw's jitter - it also turns his arm, where his cannon shots start): a stream of its
// own, started from the cycle's seed with each of his attacks, so every game draws him the same way
function kbr_sn_lg()
{
    if (!variable_global_exists("kbr_sn_lgs") || !is_struct(global.kbr_sn_lgs))
        global.kbr_sn_lgs = kbr_rng(7717);
    return global.kbr_sn_lgs;
}

function kbr_sn_lrandom(_n)
{
    return kbr_rng_unit(kbr_sn_lg()) * _n;
}

function kbr_sn_lrandom_range(_a, _b)
{
    return _a + (kbr_rng_unit(kbr_sn_lg()) * (_b - _a));
}

function kbr_sn_lirandom(_n)
{
    return kbr_rng_int(kbr_sn_lg(), floor(_n) + 1);
}

// the SOUL's speed: Chapter 2's yellow SOUL moves 5 (the battle's 4) - one more on the room's SOUL SPEED while it is yellow
function kbr_sn_speed_bonus()
{
    return kbr_sn_yellow_on() ? 1 : 0;
}

// the host's bots: their SOULs are yellow (and move at 5) while his attack runs in the host's game
function kbr_sn_bot_speed()
{
    return (kbr_sn_on() && kbr_sn_attacking()) ? 1 : 0;
}

// DRBR 1.0.3: a bot shoots on the YELLOW SOUL too (your report: "bots aren't shooting"). What a bot's shots would hit is the
// host's own game, so they are shown, not played: the host counts each bot's shots (as each player's game counts its own) and
// the "ps" list carries the counts; every game draws the new ones flying from that SOUL (kbr_gshot_seen). A bot fires like a
// player: up to three shots on the screen, a little faster the better it is, and now and then it holds for a BIG SHOT.
function kbr_sn_bot_fire(_b, _c, _s)
{
    if (!variable_struct_exists(_b, "ys"))
    {
        _b.ys = 0;
        _b.yb = 0;
    }
    if (!(kbr_sn_on() && kbr_sn_attacking()))
    {
        _s.ys_hold = 0;
        return 0;
    }
    if (!variable_struct_exists(_s, "ys_cd"))
    {
        _s.ys_cd = irandom(12);
        _s.ys_hold = 0;
        _s.ys_age = [];
    }
    // its shots on the screen (one crosses the box in about 26 frames: 16 a frame)
    for (var _i = array_length(_s.ys_age) - 1; _i >= 0; _i--)
    {
        _s.ys_age[_i]--;
        if (_s.ys_age[_i] <= 0)
            array_delete(_s.ys_age, _i, 1);
    }
    // a BIG SHOT: Z held for 40 frames, then let go
    if (_s.ys_hold > 0)
    {
        _s.ys_hold++;
        if (_s.ys_hold >= 42)
        {
            _s.ys_hold = 0;
            _b.yb = (_b.yb + 1) mod 1000;
            _s.ys_cd = 8;
        }
        return 1;
    }
    if (_s.ys_cd > 0)
    {
        _s.ys_cd--;
        return 1;
    }
    if (random(100) < 0.3 + ((_c.aggr / 100) * 0.7))
    {
        _s.ys_hold = 1;
        return 1;
    }
    if (array_length(_s.ys_age) < 3)
    {
        _b.ys = (_b.ys + 1) mod 1000;
        array_push(_s.ys_age, 26);
        _s.ys_cd = 4 + irandom(max(0, round((100 - _c.prec) / 10))) + ((_c.pre <= 1) ? 6 : 0);
    }
    return 1;
}

// this game's own shot counts for the others (the "p" message: -1 = not on the yellow SOUL)
function kbr_sn_shots(_big)
{
    var _n = -1;
    with (obj_sn_ysoul)
        _n = (_big ? bigs : shots) mod 1000;
    return _n;
}

// ---------- the cut (the attack's end in this game): his pieces go, the SOUL is red again, the box and he come back ----------
function kbr_sn_cut(_all)
{
    if (!kbr_sn_attacking() && !_all)
        return 0;
    global.kbr_sn_dirty = false;
    with (obj_sn_ysoul)
        kbr_sn_ys_on(false);
    // (the controller's Destroy puts his pose back; the finale's box, the warped box and the fake heart put the battle's own
    // back in theirs - all are bullets: the cut's own clean-up has run them)
    with (obj_sn_bc)
        instance_destroy();
    with (obj_sn_phonecall)
        instance_destroy();
    with (obj_sn_finalebox)
        instance_destroy();
    with (obj_sn_warpbox)
        instance_destroy();
    with (obj_sn_fakeheart)
        instance_destroy();
    with (obj_move_to_point)
    {
        if (variable_instance_exists(id, "target") && instance_exists(target) && target.object_index == obj_sn_neo)
            instance_destroy();
    }
    with (obj_heart)
    {
        visible = true;
        image_alpha = 1;
    }
    with (obj_growtangle)
    {
        visible = true;
        image_alpha = 1;
    }
    if (variable_global_exists("kbr_sn_box") && is_struct(global.kbr_sn_box))
    {
        var _B = global.kbr_sn_box;
        with (obj_growtangle)
        {
            x = _B.x;
            y = _B.y;
            maxxscale = _B.mxs;
            maxyscale = _B.mys;
        }
    }
    with (obj_sn_neo)
    {
        x = xstart;
        y = ystart;
        image_alpha = 1;
        partmode = 1;
        makeheart = 0;
        heart_release_con = 0;
        say_t = min(say_t, 10);
    }
    audio_stop_sound(snd_chargeshot_charge);
    audio_stop_sound(snd_sneo_overpower);
    audio_stop_sound(snd_rumble);
    global.sp = 4;
    return 1;
}

// ---------- the YELLOW SOUL (obj_sn_ysoul: one per game, on the battle's SOUL) ----------
// Chapter 2's obj_heart yellow block on Chapter 3's SOUL: the confirm key (Z) fires (3 shots at most on screen); hold it - the
// charge sparkles close in, the charge sound rises - and let go after 20 frames held for a BIG SHOT. The SOUL is drawn
// yellow and moves at 5. The shots are this game's own (no one else sees them): what they break is this game's.
// (Not Chapter 3's own colour code: it would make the hub's obj_yheart_shot, another knight's.)
function kbr_sn_yellow_on()
{
    with (obj_sn_ysoul)
        return on;
    return false;
}

function kbr_sn_ys_create()
{
    on = false;
    z_hold = 0;
    z_hold_f = 0;
    z_charge = 0;
    chargeshot_delay = 0;
    chargeshotcount = 0;
    chargeshot_sound = -1;
    shots = 0;
    bigs = 0;
    f = 2;
    persistent = false;
    visible = true;
    return 1;
}

function kbr_sn_ys_on(_on)
{
    if (_on == on)
        return 0;
    on = _on;
    z_hold = 0;
    z_hold_f = 0;
    chargeshot_delay = 0;
    if (chargeshot_sound >= 0)
        snd_stop(chargeshot_sound);
    chargeshot_sound = -1;
    with (obj_heart)
    {
        sprite_index = _on ? spr_yellowheart : spr_dodgeheart;
        image_index = 0;
    }
    with (obj_grazebox)
        sprite_index = _on ? spr_grazeappear_yellow : spr_grazeappear;
    if (!_on)
    {
        with (obj_sn_yshot)
            instance_destroy();
    }
    return 1;
}

// the keys: the game's confirm (USE SKILL moves to HOLD BREATH's key meanwhile: online_net.gml); never while you watch, type in
// the chat or have the quick settings open
function kbr_sn_ys_step()
{
    if (!on || !instance_exists(obj_heart) || kbr_soul_keys_off())
    {
        if (chargeshot_sound >= 0)
            snd_stop(chargeshot_sound);
        chargeshot_sound = -1;
        z_hold = 0;
        z_hold_f = 0;
        return 0;
    }
    var _h = instance_find(obj_heart, 0);
    if (chargeshot_delay > 0)
        chargeshot_delay--;
    if (button1_p() || (z_hold >= 10 && z_hold <= 39 && button1_r()))
    {
        if (instance_number(obj_sn_yshot) < 3 && chargeshot_delay == 0)
        {
            instance_create(_h.x + 10, _h.y + 10, obj_sn_yshot);
            snd_play(snd_heartshot_dr_b);
            shots++;
        }
    }
    if (z_hold == 20)
    {
        chargeshot_sound = snd_loop(snd_chargeshot_charge);
        snd_pitch(chargeshot_sound, 0.1);
        snd_volume(chargeshot_sound, 0, 0);
        snd_volume(chargeshot_sound, 0.3, 20);
    }
    if (z_hold >= 20 && z_hold < 40 && chargeshot_sound >= 0)
        snd_pitch(chargeshot_sound, 0.1 + ((z_hold - 20) / 20));
    if (z_hold >= 40)
        _h.image_index = 2;
    if (z_hold >= 40 && button1_r())
    {
        if (chargeshot_sound >= 0)
            snd_stop(chargeshot_sound);
        chargeshot_sound = -1;
        snd_play(snd_chargeshot_fire);
        var _bs = instance_create(_h.x + 10, _h.y + 10, obj_sn_yshot);
        _bs.big = 1;
        _bs.sprite_index = spr_yheart_bigshot;
        _bs.hspeed = 4 * f;
        _bs.friction = -0.2 * f;
        _bs.image_alpha = 0.5;
        _bs.image_xscale = 0.1;
        _bs.image_yscale = 2;
        z_hold = 0;
        chargeshot_delay = 5;
        _h.image_index = 0;
        chargeshotcount++;
        bigs++;
    }
    if (button1_h())
        z_hold_f += 1;
    else
    {
        z_hold_f = 0;
        if (chargeshot_sound >= 0)
            snd_stop(chargeshot_sound);
        chargeshot_sound = -1;
    }
    z_hold = z_hold_f * 2;
    return 1;
}

// End Step: the SOUL stays yellow while he attacks (the battle may put its own sprite back)
function kbr_sn_ys_end()
{
    if (!on)
        return 0;
    with (obj_heart)
    {
        if (sprite_index != spr_yellowheart)
            sprite_index = spr_yellowheart;
    }
    return 1;
}

// Chapter 2's charge look around the SOUL: the pulsing ghost hearts, the four sparkles closing in
function kbr_sn_ys_draw()
{
    if (!on || !instance_exists(obj_heart))
        return 0;
    var _h = instance_find(obj_heart, 0);
    var _nl = z_hold - 35;
    if (_nl >= 0)
    {
        var _sc = abs(sin(_nl / 10));
        draw_sprite_ext(_h.sprite_index, 0, _h.x - (_sc * 10), _h.y - (_sc * 10), 1 + _sc, 1 + _sc, _h.image_angle, _h.image_blend, 0.3);
        _sc = abs(sin(_nl / 14));
        draw_sprite_ext(_h.sprite_index, 0, _h.x - 2 - (_sc * 10), _h.y - 2 - (_sc * 10), 1.2 + _sc, 1.2 + _sc, _h.image_angle, _h.image_blend, 0.3);
    }
    if (z_hold >= 15)
    {
        z_charge = min(35, z_hold - 15);
        for (var _i = 0; _i < 4; _i++)
        {
            var _rx = (_i * 90) + (z_charge * 5);
            var _xx = sin(degtorad(_rx)) * (35 - z_charge);
            var _yy = cos(degtorad(_rx)) * (35 - z_charge);
            draw_sprite_ext(spr_yheart_charge, 0, (_h.x + 9) - _xx, (_h.y + 10) - _yy, 4 - ((z_charge * 2) / 35), 4 - ((z_charge * 2) / 35), 0, c_white, z_charge / 5);
        }
    }
    return 1;
}

// ---------- the background (obj_sn_bg): Chapter 2's basement ride while he is out ----------
// Chapter 2 (obj_ch2_sceneex2's Draw during the battle): black over the basement, the three coaster rails at y 70 / 150 / 230
// racing left at 15 a frame, the cityscape's three layers along the top drifting at 5 (the near ones faster)
function kbr_sn_bg_create()
{
    a = 0;
    trackx = 0;
    cs = [0, 0, 0];
    visible = true;
    return 1;
}

function kbr_sn_bg_step()
{
    a = clamp(a + (kbr_sn_on() ? 0.05 : -0.05), 0, 1);
    trackx -= 15;
    if (trackx <= -640)
        trackx += 640;
    var _sp = [1, 1.1, 1.2];
    for (var _l = 0; _l < 3; _l++)
    {
        cs[_l] -= 5 * _sp[_l];
        if (cs[_l] <= -396)
            cs[_l] += 396;
    }
    return 1;
}

function kbr_sn_bg_draw()
{
    if (a <= 0)
        return 0;
    var _cx = camerax();
    var _cy = cameray();
    draw_set_alpha(a);
    draw_set_color(c_black);
    draw_rectangle(_cx - 10, _cy - 10, _cx + 650, _cy + 490, false);
    draw_set_alpha(1);
    draw_set_color(c_white);
    var _ty = [70, 150, 230];
    for (var _r = 0; _r < 3; _r++)
    {
        for (var _k = -1; _k <= 1; _k++)
            draw_sprite_ext(spr_sneo_track, 0, _cx + trackx + (_k * 640), _cy + _ty[_r], 2, 2, 0, c_white, a);
    }
    var _sl = [spr_sn_bg_dw_mansion_basement_cityscape_background, spr_sn_bg_dw_mansion_basement_cityscape_midground, spr_sn_bg_dw_mansion_basement_cityscape_foreground];
    for (var _l = 0; _l < 3; _l++)
        scr_draw_sprite_tiled_area(_sl[_l], 0, _cx + cs[_l], _cy, _cx + cs[_l], _cy, _cx + 640, _cy + (sprite_get_height(_sl[_l]) * 2), 2, 2, c_white, a);
    return 1;
}

// ---------- his SENDS (ids 45-50, the SPAMTON family) ----------
// Made in the TARGET's game only, from his own Chapter 2 pieces, around THEIR SOUL / in their box while their own boss fights
// on (make_spamton.py made the pieces sendable: they join the send that makes them, end with it, and never touch the box, the
// SOUL, his battle object or anyone's turn timer). Every one can be dodged with any SOUL - a red one never HAS to shoot (a mail
// wall always leaves a gap at your height); a yellow SOUL (his own fight) can shoot them down as in Chapter 2.
//   45 PIPIS (low)          two pipis eggs drop in at the box's edge and hatch: a spray of little heads at your SOUL
//   46 FLYING HEADS (low)   two rows of his flying heads swoop past above and below the box, each spitting a head-bullet at you
//   47 HEART ATTACK (mid)   a wire heart darts around in front of your box, firing at you, then flies off
//   48 KROMER RAIN (mid)    his [[KROMER]]: dollar bills of three sizes stream across your box
//   49 MAIL WALL (full)     two RECREW mail walls rush across the box - each with a gap at your height (and a pipis bomb)
//   50 [[BIG SHOT]] (full)   his arm cannon charges on your row, fires its beam along it, and three cannon shots come at you
function kbr_sn_is_send(_sid)
{
    return _sid >= 45 && _sid <= 50;
}

function kbr_sn_sa_step(_G, _t, _g, _B, _S)
{
    switch (_G.sid)
    {
        case 45:
            if (_t == 0)
                kbr_sn_sa_ghost(_G, _B, 60);
            if (_t == 10 || _t == 42)
            {
                // an egg thrown at the box's edge (Chapter 2's direct throw: it sinks once it is over the box, then hatches inside it)
                var _ey = _B[1] - _B[3] - 30 - kbr_rng_int(_g, 20);
                var _eg = kbr_sa_mk(_G, _B[0] + _B[2] + 70 + kbr_rng_int(_g, 30), _ey, obj_sn_pipegg);
                with (_eg)
                {
                    type = 2;
                    directhit = 1;
                    gravity = 0.063 + (kbr_p_random(4) / 100);
                    vspeed = 1;
                    hspeed = -3.5;
                    target = 3;
                    damage = 1;
                    depth = -20;
                }
                kbr_sa_sfx(snd_bump, 1);
            }
            _G.end_t = 150;
            break;
        case 46:
            if (_t == 0)
                kbr_sn_sa_ghost(_G, _B, 40);
            // Chapter 2's FLYING HEADS rows 0 and 1 (obj_sneo_guymaker type 1): four heads each, five frames apart, curving back
            if (_t >= 5 && _t <= 20 && (_t mod 5) == 0)
                kbr_sn_sa_guy(_G, _B, 0);
            if (_t >= 50 && _t <= 65 && (_t mod 5) == 0)
                kbr_sn_sa_guy(_G, _B, 1);
            _G.end_t = 160;
            break;
        case 47:
            if (_t == 0)
            {
                kbr_sn_sa_ghost(_G, _B, 40);
                // the smaller wire heart (type 1), on a wire from above the box's right
                var _hx = _B[0] + _B[2] + 90;
                var _hy = _B[1] - _B[3] - 70;
                var _wh = kbr_sa_mk(_G, _hx, _hy, obj_sn_wireheart);
                with (_wh)
                {
                    type = 1;
                    boss = noone;
                    bossx = _hx;
                    bossy = _hy;
                    target = 3;
                    damage = 1;
                    depth = -20;
                }
                kbr_sa_sfx(snd_spamton_laugh, 1);
            }
            _G.end_t = 210;
            // his heart goes back up its wire at the end (the shots in the air fly on)
            if (_t == _G.end_t)
                kbr_sn_sa_stop(_G, [obj_sn_wireheart]);
            break;
        case 48:
            if (_t == 0)
                kbr_sn_sa_ghost(_G, _B, 40);
            // the finale's dollars (obj_sneo_dollar), streaming left to right across the box at three sizes
            if (_t >= 6 && _t <= 96 && (_t mod 6) == 0)
            {
                var _k = (_t - 6) div 6;
                var _sz = (_k mod 7 == 6) ? 2 : (((_k mod 3) == 2) ? 1.5 : 1);
                var _dy = (_B[1] - _B[3]) + 8 + kbr_rng_int(_g, max(1, floor((_B[3] * 2) - 16)));
                var _dl = kbr_sa_mk(_G, _B[0] - _B[2] - 50, _dy, obj_sn_dollar);
                with (_dl)
                {
                    startscale = _sz;
                    image_xscale = _sz;
                    image_yscale = _sz;
                    direction = 0;
                    speed = 3.5 + kbr_p_random(1.5);
                    friction = -0.06;
                    target = 3;
                    damage = 1;
                    depth = -20;
                }
            }
            if (_t == 6)
                kbr_sa_sfx(snd_sneo_laugh_long, 1.2);
            _G.end_t = 200;
            break;
        case 49:
            if (_t == 0)
            {
                kbr_sn_sa_ghost(_G, _B, 40);
                var _wc = kbr_sa_mk(_G, 0, 0, obj_sn_wallctrl);
                with (_wc)
                    kbr_sn_sa_walls(_S[1], _G.g);
            }
            // (Chapter 2's cells leave with the turn; a sent wall's go once past the screen's left, and its controller - the
            // cells' speed - stays until the last of them has gone)
            if (_t >= 60)
            {
                var _cx0 = camerax() - 60;
                var _left = 0;
                with (obj_sn_wallcell)
                {
                    if (variable_instance_exists(id, "kbrx") && kbrx == _G.gx)
                    {
                        if (x < _cx0)
                            instance_destroy();
                        else
                            _left++;
                    }
                }
                with (obj_sn_wallbomb)
                {
                    if (variable_instance_exists(id, "kbrx") && kbrx == _G.gx)
                    {
                        if (x < _cx0)
                            instance_destroy();
                        else
                            _left++;
                    }
                }
                if (_left == 0)
                    kbr_sn_sa_stop(_G, [obj_sn_wallctrl]);
            }
            _G.end_t = 190;
            break;
        case 50:
            var _ax = _B[0] + _B[2] + 70;
            if (_t == 0)
            {
                kbr_sn_sa_ghost(_G, _B, 100);
                _G.a = clamp(_S[1], _B[1] - _B[3] + 10, _B[1] + _B[3] - 10);
                // the arm cannon's charge on your row (Chapter 2's arm laser: obj_sneo_biglaser), aimed along it
                var _bl = kbr_sa_mk(_G, _ax, _G.a, obj_sn_biglaser);
                with (_bl)
                {
                    direction = 180;
                    image_angle = 180;
                    target = 3;
                    damage = 1;
                    depth = -20;
                    // (DRBR 1.0.3: its orb and beam sized for the box: half his own)
                    kbrsz = 0.5;
                }
                _G.b = _bl;
                kbr_sa_sfx(snd_chargeshot_charge, 0.6);
            }
            if (_t == 46)
            {
                with (obj_sn_biglaser)
                {
                    if (variable_instance_exists(id, "kbrx") && kbrx == _G.gx)
                    {
                        firecon = 1;
                        active = 1;
                        image_blend = c_white;
                    }
                }
                kbr_sa_sfx(snd_chargeshot_fire, 1);
            }
            if (_t == 82)
            {
                with (obj_sn_biglaser)
                {
                    if (variable_instance_exists(id, "kbrx") && kbrx == _G.gx)
                        firecon = 2;
                }
            }
            // the cannon's shots at your SOUL (Chapter 2's obj_spamtonshot), from above and below the beam
            if (_t == 90 || _t == 100 || _t == 110)
            {
                var _sy = _G.a + ((_t == 100) ? 0 : ((_t == 90) ? -50 : 50));
                var _cs = kbr_sa_mk(_G, _ax, _sy, obj_sn_cannonshot);
                with (_cs)
                {
                    move_towards_point(_S[0] - 10, _S[1] - 10, 5);
                    target = 3;
                    damage = 1;
                }
                kbr_sa_sfx(snd_heartshot_dr_b, 0.8);
            }
            _G.end_t = 200;
            break;
    }
    return 1;
}

// one of his flying heads (obj_sneo_guymaker's rows 0 / 1: in from the right, curving back - here below / above the target's
// box); its head-bullet at the SOUL comes at its alarm 1
function kbr_sn_sa_guy(_G, _B, _row)
{
    var _y = (_row == 0) ? (_B[1] + _B[3] + 50) : (_B[1] - _B[3] - 50);
    var _gy = kbr_sa_mk(_G, camerax() + 700, _y, obj_sn_lilguy);
    with (_gy)
    {
        hspeed = -18;
        friction = -0.1;
        vspeed = (_row == 0) ? -2 : 2;
        alarm[0] = 44;
        alarm[1] = 40;
        alarm[2] = 32;
        gravity = 0.5;
        gravity_direction = 0;
        destroyable = 1;
        image_blend = make_color_rgb(0, 162, 232);
        changedirection = 0;
        altdirection = 0;
        altspeed = 4;
        altfriction = -0.2;
        altgravity = 0;
        target = 3;
        damage = 1;
    }
    return _gy;
}

// a sent wall controller's own walls (self = it): two walls, each with a gap of two cells at the SOUL's height, the other cells
// mail, a crew head that a yellow SOUL may shoot, and one pipis bomb
function kbr_sn_sa_walls(_sy, _g)
{
    wallcountmax = 2;
    wallcount = 0;
    wallsetupcount = 0;
    timer = 0;
    var _yy = cameray();
    for (var _w = 0; _w < 2; _w++)
    {
        // the five cells' rows (Chapter 2: the view's middle + i * 34 - 172, i = 1..5 - the cells' middles: spr_sneo_mail's
        // origin is its middle): the gap is the row nearest the SOUL and the next nearest, so the SOUL's whole height is in it
        // wherever it stands between two rows
        var _best = 1;
        for (var _i = 1; _i <= 5; _i++)
        {
            var _cy = (_yy + 240 + (_i * 34)) - 172;
            var _by = (_yy + 240 + (_best * 34)) - 172;
            if (abs(_cy - _sy) < abs(_by - _sy))
                _best = _i;
        }
        var _bc = (_yy + 240 + (_best * 34)) - 172;
        var _two = (_sy >= _bc) ? (_best + 1) : (_best - 1);
        if (_two > 5)
            _two = 4;
        if (_two < 1)
            _two = 2;
        emptyspot1[_w] = _best;
        emptyspot2[_w] = _two;
        emptyspot3[_w] = -1;
        emptyspot4[_w] = -1;
        emptyspot5[_w] = -1;
        breakspot1[_w] = -1;
        breakspot2[_w] = -1;
        breakspot3[_w] = -1;
        breakspot4[_w] = -1;
        breakspot5[_w] = -1;
        redbreakspot1[_w] = -1;
        redbreakspot2[_w] = -1;
        redbreakspot3[_w] = -1;
        redbreakspot4[_w] = -1;
        redbreakspot5[_w] = -1;
        pipispot1[_w] = -1;
        pipispot2[_w] = -1;
        pipispot3[_w] = -1;
        pipispot4[_w] = -1;
        pipispot5[_w] = -1;
        var _rest = [];
        for (var _i = 1; _i <= 5; _i++)
        {
            if (_i != _best && _i != _two)
                array_push(_rest, _i);
        }
        var _p = _rest[kbr_rng_int(_g, array_length(_rest))];
        pipispot1[_w] = _p;
        var _c = _rest[kbr_rng_int(_g, array_length(_rest))];
        if (_c != _p)
            breakspot1[_w] = _c;
        wallcreatetimer[_w] = (_w == 0) ? 1 : 55;
        wallspeed[_w] = -7;
        walltype[_w] = 1;
    }
    return 1;
}

// a mail wall's cell / pipis bomb has its own controller (make_spamton.py: ctrl, handed over by the controller that made it)
function kbr_sn_wc_ok()
{
    return variable_instance_exists(id, "ctrl") && instance_exists(ctrl);
}

// self and cell _o belong to the same wall controller (cells without one count as one wall: Chapter 2's)
function kbr_sn_same_ctrl(_o)
{
    var _a = variable_instance_exists(id, "ctrl") ? ctrl : noone;
    var _b = (instance_exists(_o) && variable_instance_exists(_o, "ctrl")) ? _o.ctrl : noone;
    return _a == _b;
}

// his phantom beside your box while he sends it (the knights' sends show their sender's knight the same way)
function kbr_sn_sa_ghost(_G, _B, _d)
{
    // (DRBR 1.0.3: smaller and closer to the box)
    var _T = kbr_sa_tel(_G, "spr", _B[0] + _B[2] + 44, _B[1] - _B[3] - 30, _d, 0);
    _T.spr = spr_sneo_example;
    _T.xs = 0.6;
    return _T;
}

// the send's own pieces of these objects go now (a looping controller's end)
function kbr_sn_sa_stop(_G, _l)
{
    var _gx = _G.gx;
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        with (_l[_i])
        {
            if (variable_instance_exists(id, "kbrx") && kbrx == _gx)
                instance_destroy();
        }
    }
    return 1;
}

// the host's hidden copies at a bot (twin bullets around its SOUL, the same shapes and times as the real ones)
function kbr_sn_sa_bot(_s, _hx, _hy, _bx, _g, _d)
{
    var _bw = abs(_bx.sprite_width) / 2;
    var _bh = abs(_bx.sprite_height) / 2;
    switch (_s.sid)
    {
        case 45:
            for (var _e = 0; _e < 2; _e++)
            {
                for (var _i = 0; _i < 10; _i++)
                {
                    var _sh = kbr_skill_shot(_bx.x + _bw, _bx.y, spr_sneo_crew, 40 + (_e * 32), point_direction(_bx.x + _bw, _bx.y, _hx, _hy) + kbr_rng_int(_g, 51) - 25, 15 + kbr_rng_int(_g, 5), _d);
                    _sh.aim = false;
                }
            }
            break;
        case 46:
            for (var _i = 0; _i < 8; _i++)
            {
                var _gy = (_i < 4) ? (_bx.y + _bh + 50) : (_bx.y - _bh - 50);
                kbr_skill_shot(_bx.x + kbr_rng_int(_g, 120) - 60, _gy, spr_sneo_crew, 45 + ((_i mod 4) * 5) + ((_i >= 4) ? 45 : 0), point_direction(_bx.x, _gy, _hx, _hy), 8, _d);
            }
            break;
        case 47:
            for (var _i = 0; _i < 6; _i++)
                kbr_skill_shot(_bx.x + _bw + 20, _bx.y - 20 + kbr_rng_int(_g, 41), spr_sneo_wireheart_smaller, 30 + (_i * 25), point_direction(_bx.x + _bw + 20, _bx.y, _hx, _hy), 7, _d);
            break;
        case 48:
            for (var _i = 0; _i < 16; _i++)
                kbr_skill_shot(_bx.x - _bw - 50, _bx.y - _bh + 8 + kbr_rng_int(_g, max(1, floor((_bh * 2) - 16))), spr_spamton_dollar, 6 + (_i * 6), 0, 4, _d);
            break;
        case 49:
            // the walls' cells at the bot: the ones not in its gap (it is on its row: the gap)
            for (var _w = 0; _w < 2; _w++)
            {
                for (var _i = -2; _i <= 2; _i++)
                {
                    if (abs(_i) <= 0)
                        continue;
                    kbr_skill_shot(_bx.x + _bw + 60, _hy + (_i * 34), spr_sneo_mail, 1 + (_w * 55), 180, 7, _d);
                }
            }
            break;
        case 50:
            var _bl = kbr_skill_shot(_bx.x + _bw + 70, _hy, spr_sneo_bigshot_s, 46, 180, 14, _d);
            _bl.aim = false;
            for (var _i = 0; _i < 3; _i++)
                kbr_skill_shot(_bx.x + _bw + 70, _hy + ((_i - 1) * 50), spr_sneo_crew, 90 + (_i * 10), point_direction(_bx.x + _bw + 70, _hy + ((_i - 1) * 50), _hx, _hy), 5, _d);
            break;
    }
    return 1;
}

// ---------- the host's bots in his attacks ----------
// A bot's SOUL never shoots. Chapter 2's RECREW walls (solid mail with crew heads a yellow SOUL shoots away) would hit it every
// time, so the bots dodge everything else of his as usual and play a wall by the odds: when one reaches a bot, the bot gets
// through as often as it plays well (the same odds as on Flowery's boards), or takes one hit.
function kbr_sn_bot_skip(_i)
{
    return _i.object_index == obj_sn_wallcell || _i.object_index == obj_sn_wallbomb;
}

function kbr_sn_bot_walls(_b, _c, _e)
{
    if (!instance_exists(obj_sn_wallcell))
        return false;
    var _s = _b.bt;
    if (!variable_struct_exists(_s, "snw") || !is_struct(_s.snw))
        _s.snw = {};
    var _pid = _b.pid;
    var _sx = _s.x;
    var _new = [];
    var _ck = is_struct(global.kfo.M) ? global.kfo.M.R.k : 0;
    with (obj_sn_wallcell)
    {
        // (the host's own attack's walls, and the sends at this bot)
        if (variable_instance_exists(id, "kbrt") && kbrt != _pid)
            continue;
        if (abs(x - _sx) > 14)
            continue;
        var _key = string(_ck) + "_" + string(variable_instance_exists(id, "kbrx") ? kbrx : 0) + "_" + string(wallnumber);
        var _have = false;
        for (var _j = 0; _j < array_length(_new); _j++)
        {
            if (_new[_j][0] == _key)
                _have = true;
        }
        if (!_have)
            array_push(_new, [_key, (variable_instance_exists(id, "kbr") && kbr != 0) ? kbrd : -1, variable_instance_exists(id, "kbrf") ? kbrf : -1]);
    }
    for (var _j = 0; _j < array_length(_new); _j++)
    {
        var _k = _new[_j][0];
        if (variable_struct_exists(_s.snw, _k))
            continue;
        variable_struct_set(_s.snw, _k, 1);
        // (how many walls it has met in the match: the record above is cleared now and then)
        _s.snw_n = (variable_struct_exists(_s, "snw_n") ? _s.snw_n : 0) + 1;
        var _pass = clamp((_c.prec / 100) * (1 - (_c.miss / 100)) * (1 - (_c.react / 90)), 0.02, 0.995);
        if (random(1) < _pass || _s.inv > 0)
            continue;
        var _t = kbr_hit_dmg(2, false);
        var _dmg = max(1, round(_t[0] * (_e.dmul / 100)));
        // (a player's MAIL WALL at the bot: its damage and its sender's credit)
        if (_new[_j][1] >= 0)
            _dmg = max(1, round(_new[_j][1] * (_e.skdmg / 100) * (_e.dmul / 100)));
        if (_e.ohko)
            _dmg = _b.hp;
        var _tk = kfo_bot_take(_b, _dmg);
        if (_new[_j][2] >= 0)
        {
            _b.lby = _new[_j][2];
            kfo_host_dealt(_new[_j][2], _tk);
        }
        _b.hits++;
        _s.inv = round(_t[1] * (_e.ifr / 100));
        if (_b.hp <= 0)
        {
            kfo_host_out_report(_b.pid, round(kfo_host_tick_now()), "out", _new[_j][2]);
            return true;
        }
    }
    // (the record of the walls already played: only this cycle's)
    if (array_length(variable_struct_get_names(_s.snw)) > 40)
        _s.snw = {};
    return false;
}
