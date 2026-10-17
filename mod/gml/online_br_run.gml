
// ===== Build 45: the shared battle on this screen - one attack after another, no player turns =====
// The battle stays in its bullet phase for the whole match. For every cycle of the timeline:
//   idle -> the knight changes when the cycle's knight is another one (the lineup switches it in, with its entrance flash,
//           tr ticks before the attack); 16 ticks before the attack the cycle is ARMED:
//   arm  -> the old box goes, the knight's own turn start makes the new box (the size and place of that attack) and counts
//           rtimer up to 11, where kbr_rgate holds it; the SOUL is set to the new box's middle
//   run  -> at the cycle's tick the hold lets go: the attack stream is seeded for this cycle and the knight's own code starts
//           the attack. It ends by its own turn timer (the battle controller never ends the turn online: kbr_hold_end), or
//           when the next cycle has to be armed, whichever comes first; then its bullets and helpers go (kbr_cut)
// A game that started late, lagged or was paused simply joins at the next cycle it can still arm in time: the timeline
// never waits for anyone and never changes for anyone.

#macro KBR_ARM 16
#macro KBR_LATE 12

function kbr_match()
{
    var _M = kfo_match();
    if (is_undefined(_M) || !variable_struct_exists(_M, "tl"))
        return undefined;
    return _M;
}

// the online battle royale is running in this game
function kbr_on()
{
    if (!is_struct(global.kfo) || !is_struct(global.kfo.M) || !variable_struct_exists(global.kfo.M, "tl"))
        return false;
    if (!knight_active() || global.krun.state != "battle")
        return false;
    return knight_lu_kind_of(global.krun.cfg) == "online";
}

// The battle's own command menu (FIGHT / ACT / ITEM / SPARE / DEFEND) never opens online. The battle controller runs that
// menu whenever global.myfight is 0 - its keys, its sounds, its buttons in the party box - and with a one-member party
// it walks past the last party slot (build 45, your report: "Variable Index [3] out of range [3] - global.char" in
// obj_battlecontroller). So online myfight is never 0 (KBR_NOMENU: a value no battle code acts on, as the hub's own
// scenes use), and once the shared battle runs the battle never goes back to a player turn either. Called first thing in
// the battle controller's Step and Draw (br_patch.py) and by the online runner.
function kbr_menu_block()
{
    if (!kbr_on() || !variable_global_exists("myfight") || !variable_global_exists("mnfight"))
        return 0;
    if (global.myfight == 0 || global.myfight == 5)
        global.myfight = KBR_NOMENU;
    // build 47 (your report: the box kept "showing all the buttons"): nobody's turn, -1, the value the game's own scenes use.
    // The party box rises to show FIGHT / ACT / ITEM / SPARE / DEFEND only on the slot whose turn it is (scr_charbox), and
    // build 46 left that on your slot; now it stays down for the whole match. Nothing online reads the turn (the menu that
    // would is held shut above).
    if (variable_global_exists("charturn") && global.charturn != -1)
        global.charturn = -1;
    if (global.mnfight == 0 && is_struct(global.knight_lu) && global.knight_lu.ready)
        global.mnfight = 2;
    return 1;
}

// ---------- the shared clock ----------
// ticks since the match's tick 0 (30 a second), from this game's clock: t0ms is this game's current_time of the host's
// tick 0 (kept in step by the ping / pong exchange, online_play.gml). Before the host said GO there is no tick yet.
function kbr_now()
{
    var _M = kbr_match();
    if (is_undefined(_M) || !_M.go)
        return -999999;
    return (current_time - _M.t0ms) * 0.03;
}

// ---------- hooks in the fight code ----------
// the knight's Step: rtimer += kbr_rgate() (self = the knight). Offline 1. Online the count waits at 11 until the attack's
// tick, and the release seeds the attack stream for the cycle.
function kbr_rgate()
{
    if (!kbr_on())
        return 1;
    if (rtimer < 11)
        return 1;
    var _M = global.kfo.M;
    var _R = _M.R;
    if (_R.ph != "arm" || _R.arm_k < 0)
        return 0;
    // the attack starts the same number of frames after its arm in every game (_R.armf, from the shared clock at the arm):
    // every game's knight, box and SOUL are then in the same state when it starts
    if (_R.armc < _R.armf)
        return 0;
    var _c = kbr_tl_get(_M.tl, _R.arm_k);
    kbr_det_seed(_c.seed);
    global.kbr_det.on = true;
    _R.ph = "run";
    _R.k = _R.arm_k;
    _R.af = 0;
    _R.run_k = _c.k;
    _R.t_spawn = kbr_now();
    array_push(_R.started, _c.k);
    if (array_length(_R.started) > 64)
        array_delete(_R.started, 0, 1);
    kbr_cycle_started(_c);
    return 1;
}

// the battle controller's Step: online the battle never goes back to the menu when the turn timer runs out
function kbr_hold_end()
{
    return kbr_on();
}

// the lineup may switch knights now (knight_lu_late): between two attacks
function kbr_swap_ok()
{
    var _M = kbr_match();
    if (is_undefined(_M))
        return false;
    return _M.R.ph == "idle" || _M.R.ph == "wait";
}

// a knight just switched in (knight_lu_swap): it does nothing until its attack is armed
function kbr_after_swap(_b)
{
    // set by id: the instance may still count as switched off inside this event (a with() would not reach it)
    _b.attacked = 1;
    _b.talked = 1;
    _b.rtimer = 0;
    _b.attackchosen = false;
    return 1;
}

// ---------- the runner ----------
function kbr_runner_new()
{
    return { ph: "boot", k: 0, arm_k: -1, run_k: -1, af: 0, t_spawn: 0, swapped_k: -1, centred: false, cut_k: -1, late: 0,
        bc: [], skipped: 0, cycles: 0, started: [], cut_why: "", first_k: -1, mark: -1, armc: 0, armf: KBR_ARM };
}

function kbr_lu_slot(_ok)
{
    var _lu = global.knight_lu;
    var _reg = kbr_reg_of(_ok);
    for (var _j = 0; _j < _lu.n; _j++)
    {
        if (_lu.ks[_j] == _reg)
            return _j;
    }
    return 0;
}

// the first cycle this game can still arm on time at tick _t
function kbr_next_armable(_tl, _t)
{
    var _k = kbr_tl_at(_tl, _t);
    while (kbr_tl_get(_tl, _k).t0 - KBR_LATE < _t)
        _k++;
    return _k;
}

// the frame of attack _c (counted from its start) at which it is cut when it runs into the next cycle _nx: one tick before
// the next knight's switch-in / arm time, in this attack's own frames (Hyper speed: 38 frames a second, ticks are 1/30 s)
function kbr_cut_af(_c, _nx)
{
    var _tick = _nx.t0 - KBR_ARM - (_nx.sw ? max(_nx.tr, 2) : 0) - 1;
    var _f = (_tick - _c.t0) * (_c.hyper ? (38 / 30) : 1);
    return max(4, floor(_f));
}

// every step of the battle (from kfo_play_tick)
function kbr_step()
{
    var _M = kbr_match();
    if (is_undefined(_M) || !kbr_on() || global.knight_frozen)
        return 0;
    // build 51: the party's HP panel sits at the very bottom online (the battle's text box under it is never used here),
    // which frees the space between the box and the panel for the targeting strip, the feed and the announcements
    // The panel's frame is drawn from bp (480 - bp) and its contents from bpoff (= yy + bpy - bp, plus 336), so only bp
    // moves: once the battle's slide-in is over (intro 0) bp goes from 152 to 40 and both move down 112 together.
    with (obj_battlecontroller)
    {
        if (variable_instance_exists(id, "intro") && intro == 0 && variable_instance_exists(id, "bp") && bp > 40)
            bp = 40;
    }
    kbr_roar_soul(_M);
    // build 52: an online-only look's hero hidden (the HUD draws the look's battle art in its place)
    kbr_skin_hero_tick(_M);
    // build 52: Jevil's music while he is out (DRBR: every other boss's too)
    kbr_jv_music();
    kbr_enc_music();
    if (!is_struct(global.knight_lu) || !global.knight_lu.ready)
    {
        // the lineup sets itself up in the battle's first turn; the command menu never opens (kbr_menu_block)
        kbr_menu_block();
        return 0;
    }
    var _lu = global.knight_lu;
    var _R = _M.R;
    // the Knight never falls online
    global.monsterhp[0] = global.monstermaxhp[0];
    _lu.hp = global.monsterhp[0];
    switch (_R.ph)
    {
        case "boot":
            // no menu, ever: the battle sits in its bullet phase from here on
            global.mnfight = 2;
            global.myfight = KBR_NOMENU;
            global.turntimer = 0;
            with (obj_monsterparent)
            {
                attacked = 1;
                talked = 1;
            }
            _R.ph = "wait";
            kfo_ready_up();
            break;
        case "wait":
            // waiting for the host's GO (every player's battle is up)
            global.turntimer = 0;
            if (!_M.go)
                break;
            var _t0 = kbr_now();
            _R.k = kbr_next_armable(_M.tl, _t0 + KBR_ARM);
            if (_R.k > 0)
                _R.skipped += _R.k;
            _R.first_k = _R.k;
            _R.ph = "idle";
            break;
        case "idle":
            var _t = kbr_now();
            var _c = kbr_tl_get(_M.tl, _R.k);
            // a game that fell behind (a long load, a pause, a lag spike): on to the next cycle it can still arm on time
            if (_t > _c.t0 - KBR_LATE)
            {
                var _nk = kbr_next_armable(_M.tl, _t);
                _R.skipped += max(1, _nk - _R.k);
                _R.k = _nk;
                break;
            }
            // the knight changes: switch it in for its entrance tr ticks before the attack (the swap itself runs in the
            // hub controller's Draw GUI End: knight_lu_late)
            var _slot = kbr_lu_slot(_c.ok);
            if (_slot != _lu.act && _R.swapped_k != _c.k && _t >= _c.t0 - KBR_ARM - max(_c.tr, 2))
            {
                _R.swapped_k = _c.k;
                _lu.want = _slot;
                _lu.pend = true;
                kbr_switch_fx(_c);
            }
            if (_t >= _c.t0 - KBR_ARM - 0.5 && _lu.act == _slot && !_lu.pend)
            {
                kbr_arm(_c);
                // on time (or a frame or two behind - clock jitter): always the same number of frames to the start, so every
                // game's knight, box and SOUL are in the same state when the attack starts; armed really late (a slow switch, a
                // lag spike): fewer frames, to start as close to the shared tick as it can
                _R.armf = (_t <= _c.t0 - KBR_ARM + 2.5) ? KBR_ARM : max(11, round(_c.t0 - _t));
            }
            break;
        case "arm":
            _R.armc++;
            var _ca = kbr_tl_get(_M.tl, _R.arm_k);
            // the new box is up: the SOUL starts every attack in its middle, like a Chapter 3 turn does
            if (!_R.centred && instance_exists(obj_growtangle) && instance_exists(obj_heart))
            {
                _R.centred = true;
                var _b = instance_find(obj_growtangle, 0);
                with (obj_heart)
                {
                    x = _b.x - 10;
                    y = _b.y - 10;
                }
            }
            // the knight never got to its count (it should not happen): this cycle is lost for this game
            if (kbr_now() > _ca.t0 + 30)
            {
                _R.skipped++;
                _R.cut_why = "arm";
                kbr_cut();
                _R.ph = "idle";
                _R.k = _R.arm_k + 1;
            }
            break;
        case "run":
            _R.af++;
            var _cr = kbr_tl_get(_M.tl, _R.k);
            kbr_checkpoint(_cr);
            var _nx = kbr_tl_get(_M.tl, _R.k + 1);
            var _end = (_R.af > 3 && global.turntimer <= 0);
            // an attack that runs longer than its place in the timeline ends a set number of its own frames after it started
            // (the same frame in every game: the knight is left in the same state for the next one), early enough for the next
            // knight's entrance and arm to come on time; the shared clock is the backstop for a game that runs slow
            var _forced = (_R.af >= kbr_cut_af(_cr, _nx)) || (kbr_now() >= _nx.t0 - KBR_ARM - 0.5);
            if (_end || _forced)
            {
                _R.cut_why = _end ? "end" : "next";
                kbr_cut();
                _R.cycles++;
                _R.ph = "idle";
                _R.k++;
            }
            break;
    }
    return 1;
}

// start the knight's own turn for cycle _c: the attack is forced through the lineup plan (knight_force_want), the knight
// makes its box at mnfight 1.5 and counts rtimer up to 11, where kbr_rgate holds it until the cycle's tick
function kbr_arm(_c)
{
    var _M = global.kfo.M;
    var _R = _M.R;
    var _lu = global.knight_lu;
    var _slot = kbr_lu_slot(_c.ok);
    _lu.plan_k = _slot;
    _lu.plan_i = _c.ai;
    _lu.plan_name = kbr_atk_name(_c.ok, _c.ai);
    _lu.want = _slot;
    _lu.pend = false;
    kbr_cycle_look(_c);
    // build 50: the players' sent attacks: what reads the box goes with it (the rest flies on, the timelines wait); the
    // Twin Knight's real attacks end with the attack before
    kbr_sa_boxless();
    kbr_sa_twin_end(true);
    with (obj_growtangle)
        instance_destroy();
    var _sp = kbr_split_objs();
    for (var _i = 0; _i < array_length(_sp); _i++)
    {
        with (_sp[_i])
            instance_destroy();
    }
    global.turntimer = 0;
    global.mnfight = 1.5;
    global.myfight = KBR_NOMENU;
    with (obj_battlecontroller)
        reset = 0;
    with (obj_monsterparent)
    {
        attacked = 0;
        talked = 1;
        acting = 0;
    }
    // the knight's own counters as they would be had this game played every cycle (a game that skipped some stays in step)
    var _turns = 0;
    for (var _j = 0; _j < _c.k; _j++)
    {
        if (_M.tl.cyc[_j].reg == _c.reg)
            _turns++;
    }
    var _home = _lu.home[_lu.act];
    with (_lu.inst[_lu.act])
    {
        talked = 1;
        attackchosen = false;
        rtimer = 0;
        attacked = 0;
        if (variable_instance_exists(id, "turns"))
            turns = _turns;
        // its place and its idle sway the same in every game (a game that joined late or skipped a cycle would differ, and
        // some attacks start from where the knight is)
        if (variable_instance_exists(id, "siner"))
            siner = 0;
        if (variable_instance_exists(id, "siner2"))
            siner2 = 0;
        if (variable_instance_exists(id, "fsiner"))
            fsiner = 0;
        if (is_array(_home))
        {
            x = _home[0];
            y = _home[1];
        }
    }
    // the Twin Knight too: its place, its pattern memory and its count start every attack the same in every game (a game
    // that skipped a cycle would remember another last pattern)
    with (obj_knight_twin)
    {
        if (is_array(_home))
        {
            x = _home[0] - 64;
            y = _home[1] - 40;
        }
        siner = 0;
        t = 0;
        active = false;
        lastpat = -1;
        lastpat2 = -1;
        ph_a = 0;
    }
    // the attack stream from a seed of its own for the arm frames too: whatever draws from it before the attack starts (the
    // Twin Knight picks its pattern as the box comes up) draws the same in every game, whatever the last cycle left
    kbr_det_seed(kbr_mix(_c.seed, 17));
    global.kbr_det.on = true;
    _R.ph = "arm";
    _R.arm_k = _c.k;
    _R.centred = false;
    _R.mark = kbr_id_mark();
    _R.armc = 0;
    _R.armf = KBR_ARM;
    return 1;
}

// the newest instance there is now (instance ids only grow): what is made after this belongs to the coming attack
function kbr_id_mark()
{
    var _m = 0;
    with (all)
        _m = max(_m, real(id));
    return _m;
}

// the end of an attack: its bullets, generators, controllers and every attack object that would outlive it go; the box
// stays until the next attack makes its own. Skill bullets (kbr) are this game's own and live on.
function kbr_cut()
{
    // build 50: the Twin Knight's real attacks (and their helpers) end with the Knight's attack
    kbr_sa_twin_end(true);
    with (obj_bulletparent)
    {
        if (!(variable_instance_exists(id, "kbr") && kbr != 0))
            instance_destroy();
    }
    // build 50: a player's sent attack (kbrx) is not the Knight's: it lives on
    with (obj_bulletgenparent)
    {
        if (!(variable_instance_exists(id, "kbrx") && kbrx > 0))
            instance_destroy();
    }
    with (obj_dbulletcontroller)
        instance_destroy();
    // the attack's own helpers: only the ones made since the attack was armed (a knight's own helpers - Elecknight's drawer,
    // made with the knight - stay)
    var _M0 = kbr_match();
    var _mark = is_undefined(_M0) ? -1 : _M0.R.mark;
    var _l = kbr_atk_objs();
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        with (_l[_i])
        {
            if (real(id) > _mark && !(variable_instance_exists(id, "kbrx") && kbrx > 0))
                instance_destroy();
        }
    }
    // a box-splitting attack moves the battle box away while its halves are up: it comes back for the breath
    var _sp = kbr_split_objs();
    for (var _i = 0; _i < array_length(_sp); _i++)
    {
        with (_sp[_i])
            instance_destroy();
    }
    with (obj_growtangle)
    {
        if (x < -1000)
            x = xstart;
    }
    // DRBR: the bosses' pieces that are not bullets, the SOUL's mode, the box (kbr_enc_cut)
    kbr_enc_cut(false);
    global.turntimer = 0;
    global.mnfight = 2;
    with (obj_monsterparent)
        attacked = 1;
    var _M = kbr_match();
    if (!is_undefined(_M))
        _M.R.cut_k = _M.R.k;
    return 1;
}

// the match is over for this game (the results, the connection lost): the attack on screen ends at once - its bullets, its
// generators and helpers, a split box - before the screen freezes under the box (a split box left without the battle box
// it reads would stop the game)
function kbr_end_clean()
{
    with (obj_bulletparent)
        instance_destroy();
    with (obj_bulletgenparent)
        instance_destroy();
    with (obj_dbulletcontroller)
        instance_destroy();
    var _l = kbr_atk_objs();
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        with (_l[_i])
            instance_destroy();
    }
    var _sp = kbr_split_objs();
    for (var _i = 0; _i < array_length(_sp); _i++)
    {
        with (_sp[_i])
            instance_destroy();
    }
    with (obj_knight_twin)
        instance_destroy();
    // DRBR: every boss's pieces, sends' too
    kbr_enc_cut(true);
    // build 50: the players' sent attacks, their sounds and surface
    kbr_sa_clear();
    global.kbr_det.on = false;
    return 1;
}

// the objects a Knight's box-splitting attack puts up in place of the box
function kbr_split_objs()
{
    return [obj_knight_split_growtangle, obj_knight_split_growtangle_Copy, obj_knight_split_growtangle_vertical, obj_knight_split_growtangle_vertical_Copy,
        obj_knight_split_growtangle_backup];
}

// ---------- what every game checks about its own attack (the host compares) ----------
// the number of bullets 30, 60 and 90 frames into the attack: the same attack started from the same seed puts up the same
// number of bullets in every game unless it reacts to the SOUL
function kbr_checkpoint(_c)
{
    var _R = global.kfo.M.R;
    if (_R.af == 30 || _R.af == 60 || _R.af == 90)
    {
        if (_R.af == 30)
            _R.bc = [_c.k];
        // build 50: the Knight's own bullets only (a player's sends are in one game: never part of the check)
        var _nb = 0;
        with (obj_bulletparent)
        {
            if (!(variable_instance_exists(id, "kbr") && kbr != 0))
                _nb++;
        }
        array_push(_R.bc, _nb);
    }
}

// a new attack started (the release in kbr_rgate)
function kbr_cycle_started(_c)
{
    var _M = global.kfo.M;
    _M.cyc_seen++;
    _M.cur_ok = _c.ok;
    _M.cur_k = _c.k;
    kbr_stage_fx(_c);
    kbr_gauge_cycle(_c);
    return 1;
}

// the extras of the coming attack: the Twin Knight layer, Hyper speed (both the same in every game, from the cycle)
function kbr_cycle_look(_c)
{
    var _r = global.krun;
    var _was = _r.cfg.c_twin;
    _r.cfg.c_twin = _c.twin ? 1 : 0;
    _r.cfg.c_speed = _c.hyper ? 1 : 0;
    if (_was && !_r.cfg.c_twin)
    {
        with (obj_knight_twin)
            instance_destroy();
    }
    return 1;
}

// the Twin Knight's turn count for the attack that is running (its patterns get harder with it)
function kbr_twin_turn()
{
    var _M = kbr_match();
    if (is_undefined(_M))
        return 1;
    return kbr_tl_twin_n(_M.tl, _M.R.k) + 1;
}

function kbr_stage_fx(_c)
{
    var _M = global.kfo.M;
    if (_c.st != _M.stage)
    {
        var _was = _M.stage;
        _M.stage = _c.st;
        if (_was >= 0 && _c.st > _was)
        {
            // build 51: the big announcement (no feed line: the band says it)
            kbr_bn_show("STAGE " + string(_c.st) + ": " + kfo_stage_name(_c.st), kbr_bn_stage(_c.st, _c.k), c_white);
        }
        if (_c.st >= 3 && _was < 3 && _M.set.ftmus)
            kfo_mus_situ("nm");
    }
    if (_c.sd && !_M.sd_on)
    {
        _M.sd_on = true;
        kbr_sudden_death();
    }
    if (_c.ft && !_M.ft_on)
    {
        _M.ft_on = true;
        kbr_final_two_fx();
    }
    return 1;
}

// the knight switching in: its name, the white flash of its entrance (knight_lu_swap does the flash), a bell
function kbr_switch_fx(_c)
{
    // build 51: the big announcement - the knight's name in its colour and one flavour line (no feed line any more)
    kbr_bn_show(_c.nm ? "KNIGHTMARE" : string_upper(kbr_ok_name(_c.ok)), kbr_bn_knight(_c.ok, _c.nm, _c.k), _c.nm ? make_color_rgb(255, 60, 60) : kbr_ok_color(_c.ok));
    var _M = kbr_match();
    if (!is_undefined(_M))
        _M.swfx = 20;
    return 1;
}

// the stage names and banners
function kfo_stage_name(_st)
{
    switch (_st)
    {
        case 1: return "GUESTS";
        case 2: return "SHUFFLE";
        case 3: return "KNIGHTMARE";
        case 4: return "OVERDRIVE";
    }
    return "PURE";
}

function kfo_stage_banner(_st)
{
    switch (_st)
    {
        case 1: return "THE KNIGHT REMEMBERS ANOTHER FORM...";
        case 2: return "FORMS BLUR TOGETHER.";
        case 3: return "KNIGHTMARE! A SECOND KNIGHT JOINS IN!";
        case 4: return "IT WILL NOT END.";
    }
    return "";
}


// build 51: your SOUL keeps your colour in a Roaring. The Roaring draws obj_heart itself (draw_self / draw_sprite_ext with
// its sprite and blend), past the hub's own SOUL draw, so the game's red heart showed. While a Roaring is on screen the
// SOUL's sprite is the white copy of the same heart (spr_khub_soul: same size, same place) tinted your colour; its
// collision mask stays the game's own sprite. Everything goes back when the Roaring is over.
function kbr_roar_soul(_M)
{
    var _roar = instance_exists(obj_knight_roaring2) || instance_exists(obj_knight_roaring3);
    var _on = _roar && _M.me && !_M.out;
    with (obj_heart)
    {
        var _saved = variable_instance_exists(id, "kbr_rs") && kbr_rs >= 0;
        if (_on && (sprite_index == spr_dodgeheart || _saved))
        {
            if (!_saved)
            {
                kbr_rs = sprite_index;
                kbr_rm = mask_index;
                kbr_rb = image_blend;
            }
            mask_index = (kbr_rm >= 0) ? kbr_rm : kbr_rs;
            sprite_index = spr_khub_soul;
            image_blend = kfo_look().col;
        }
        else if (!_on && _saved)
        {
            sprite_index = kbr_rs;
            mask_index = kbr_rm;
            image_blend = kbr_rb;
            kbr_rs = -1;
        }
    }
    return 1;
}
