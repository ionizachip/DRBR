
// ===== Build 45: you in the shared battle - your HP, gauge, Hold Breath, hits, the others' SOULs =====
// All of it is this game's own: your hits are decided on your screen, your HP and gauge change here, and the host is told
// (your SOUL 15 times a second, the rest twice a second) and only steps in when something does not add up.

// ---------- the match struct (the battle royale part of global.kfo.M) ----------
function kbr_match_fill(_M, _m)
{
    _M.eff = kbr_eff(_M.set);
    _M.tl = kbr_tl_new(_M.seed, _M.set);
    _M.go = false;
    _M.t0ms = 0;
    var _ft = kfo_jn(_m, "ft", -1);
    if (_ft >= 0)
        kbr_tl_set_ft(_M.tl, _ft);
    // DRBR: the GROUP MERCY's phase announcements so far (a watcher joining late, a resync)
    kbr_tl_flph_load(_M.tl, kfo_ja(_m, "fp"));
    _M.flg = kfo_jn(_m, "fg", 0) / 10;
    _M.flm = [-1, 0];
    _M.R = kbr_runner_new();
    _M.stage = -1;
    _M.cyc_seen = 0;
    _M.cur_ok = -1;
    _M.cur_k = -1;
    _M.sd_on = false;
    _M.ft_on = false;
    _M.g = clamp(_M.eff.g0, 0, 100);
    _M.gz = 0;
    _M.gz_all = 0;
    _M.hold = false;
    _M.hold_was = false;
    _M.hold_on = false;
    _M.hold_t = 0;
    _M.hits = 0;
    _M.hseq = 0;
    _M.taken = 0;
    _M.healed = 0;
    _M.spect = -1;
    _M.ps = {};
    _M.log = [];
    _M.t_pos = 0;
    _M.t_st = 0;
    _M.alive_f = 0;
    _M.died_t = -1;
    _M.died_k = -1;
    _M.flash = 0;
    _M.swfx = 0;
    _M.hitfx = 0;
    _M.sk = kbr_skills_new(_M.eff);
    // build 48: targeting (my mode, who I target, who targets me) and the last player who hurt me (the knockout's credit)
    _M.tg = kbr_tg_new();
    _M.lby = -1;
    _M.ck = { rtt: -1, ra: -1, best: 999999, samples: [], t_ping: 0, n: 0, fixes: 0, jumps: 0 };
    _M.resyncs = 0;
    _M.t_rs_local = 0;
    _M.tab = false;
    // build 47: what this game draws of the match (the others' SOULs, watching, quick settings: online_view.gml)
    _M.vw = kbr_vw_new();
    return _M;
}

// the player's party member (the one character online)
function kbr_char()
{
    return global.krun.party[0];
}

// ---------- the log (bottom of the screen) ----------
function kbr_log(_t, _col)
{
    var _M = kbr_match();
    if (is_undefined(_M))
        return 0;
    // build 51: the same line again within a second is one line with x2, x3...
    var _nl = array_length(_M.log);
    if (_nl > 0)
    {
        var _last = _M.log[_nl - 1];
        if (variable_struct_exists(_last, "base") && _last.base == _t && current_time - _last.at < 1000)
        {
            _last.rep++;
            _last.t = _t + " x" + string(_last.rep);
            _last.n = string_length(_last.t);
            _last.life = 300;
            _last.at = current_time;
            return 1;
        }
    }
    array_push(_M.log, { t: _t, c: _col, life: 300, n: 0, base: _t, rep: 1, at: current_time });
    if (array_length(_M.log) > 12)
        array_delete(_M.log, 0, array_length(_M.log) - 12);
    return 1;
}

// ---------- every step of the battle ----------
function kbr_me_tick()
{
    var _M = kbr_match();
    if (is_undefined(_M) || !kbr_on())
        return 0;
    var _e = _M.eff;
    var _c = kbr_char();
    for (var _i = array_length(_M.log) - 1; _i >= 0; _i--)
    {
        _M.log[_i].life--;
        if (_M.log[_i].n < string_length(_M.log[_i].t))
            _M.log[_i].n += 2;
        if (_M.log[_i].life <= 0)
            array_delete(_M.log, _i, 1);
    }
    if (_M.flash > 0)
        _M.flash--;
    if (_M.swfx > 0)
        _M.swfx--;
    if (_M.hitfx > 0)
        _M.hitfx--;
    _M.tab = kbr_key_held("list");
    // build 47: the view's own clock (blinks, shatters, notices) and QUICK SETTINGS (it has the keys while it is open)
    kbr_view_tick(_M);
    var _qs = kbr_qs_tick(_M);
    if (_M.out || !_M.me)
    {
        _M.hold = false;
        _M.hold_was = false;
        _M.hold_on = false;
        if (!_qs)
            kbr_spectate_tick();
        else
        {
            global.inv = 9999;
            with (obj_heart)
            {
                visible = false;
                canmove = 0;
            }
        }
        // build 52: the followed player's battle (their SOUL, the sends at them)
        kbr_spec_follow(_M);
        // build 48: the targeted sends still start in a watcher's box (they see every attack)
        kbr_tg_tick(_M);
        kbr_skill_pending();
        kbr_send_state(false);
        return 1;
    }
    var _running = (_M.R.ph == "run" || _M.R.ph == "arm" || _M.R.ph == "idle");
    if (_running && instance_exists(obj_heart))
    {
        _M.alive_f++;
        // the gauge: about one point a second (CHARGE RATE) and the grazes (build 46: no bonus for clean seconds any more)
        if ((_M.alive_f mod 30) == 0)
            kbr_gauge_add(_e.gmul / 100, false);
    }
    // Hold Breath (build 47: the fights' own HoldBreath, as you asked): while its key is held (S unless changed in KEYBINDS)
    // the SOUL moves faster - one more than the room's SOUL SPEED (5 at the Chapter 3 speed of 4), two more while a Roaring
    // attack is on (6), the numbers every knight fight uses after its HoldBreath ACT. Nothing else: no gauge cost, no damage
    // or graze change, no log line (build 46's version only worked with gauge points, drained them and flickered on and off).
    // X still halves the movement on top of it (the game's own slow walk).
    // build 50: a TOGGLE - one press turns it on, the next press turns it off (no need to keep the key down)
    if (!variable_struct_exists(_M, "hold_on"))
        _M.hold_on = false;
    if (kbr_key_pressed("breath") && !_M.vw.qs && !kfo_chat_typing())
        _M.hold_on = !_M.hold_on;
    // DRBR: off while the SOUL itself uses the confirm key (the orange dash, the yellow shots: HOLD BREATH's key is USE SKILL's then)
    var _h = _M.hold_on && instance_exists(obj_heart) && !_M.vw.qs && !kbr_orange_on();
    if (_h != _M.hold_was)
        _M.hold_t = 0;
    else
        _M.hold_t++;
    _M.hold = _h;
    _M.hold_was = _h;
    // sudden death: max HP drops every second, down to the floor
    if (_M.sd_on && (_M.alive_f mod 30) == 0 && global.maxhp[_c] > _e.sdfloor)
    {
        global.maxhp[_c] = max(_e.sdfloor, global.maxhp[_c] - _e.sdrate);
        global.hp[_c] = min(global.hp[_c], global.maxhp[_c]);
    }
    // the SOUL: the room's speed (Slow takes 1 off, Hold Breath adds 1 - 2 in a Roaring attack), its size (GIANT / TINY SOULS)
    var _sp = _e.spd - ((_M.sk.slow_t > 0) ? 1 : 0) + kbr_breath_bonus(_h) + kbr_jv_speed_bonus() + kbr_sn_speed_bonus() + kbr_pk_speed_bonus();
    with (obj_heart)
    {
        wspeed = max(1, _sp);
        if (image_xscale != _e.soul && !kbr_pk_soul_scaled())
        {
            image_xscale = _e.soul;
            image_yscale = _e.soul;
        }
    }
    // the TP bar shows the gauge
    global.tension = (clamp(_M.g, 0, 100) / 100) * global.maxtension;
    if (!_M.vw.qs)
        kbr_skills_tick();
    kbr_tg_tick(_M);
    kbr_send_state(false);
    return 1;
}

// Hold Breath's speed: +1, +2 while a Roaring attack is on screen (obj_knight_roaring2, Violet Knight's obj_knight_roaring3) - the
// knights' own "if (holdbreathcount > 0) obj_heart.wspeed = 5 (6 in the Roaring)" on top of the room's speed
function kbr_breath_bonus(_h)
{
    if (!_h)
        return 0;
    if (instance_exists(obj_knight_roaring2) || instance_exists(obj_knight_roaring3))
        return 2;
    return 1;
}

function kbr_gauge_add(_n, _graze)
{
    var _M = kbr_match();
    if (is_undefined(_M) || _M.out)
        return 0;
    // build 48: OUTNUMBERED BONUS - faster for each player targeting you
    if (_n > 0)
        _n *= kbr_tg_outn_mul();
    _M.g = clamp(_M.g + _n, 0, 100);
    return 1;
}

// a new attack starts: SHIELD MADNESS shields everyone for the first one
function kbr_gauge_cycle(_c)
{
    var _M = kbr_match();
    if (is_undefined(_M) || !_M.me || _M.out)
        return 0;
    if (_M.eff.shieldmad && !_M.sk.mad0)
    {
        _M.sk.mad0 = true;
        _M.sk.shield = _M.eff.shp;
        _M.sk.shield_t = 300;
        kbr_log("* SHIELD MADNESS: you start shielded.", c_white);
    }
    return 0;
}

// the graze box (patched in by br_patch.py): a first graze of a bullet
function kbr_on_graze()
{
    if (!kbr_on())
        return 0;
    var _M = global.kfo.M;
    if (_M.out || !_M.me)
        return 0;
    _M.gz++;
    _M.gz_all++;
    kbr_gauge_add(_M.eff.grz / 100, true);
    return 1;
}

// ---------- hits ----------
// what a bullet costs online: one flat table by kind (the knights' own numbers are tuned for a full, armoured party);
// Knightmare's attacks hit harder. Self = the bullet (scr_damage runs in it).
function kbr_hit_kind(_obj)
{
    var _n = object_get_name(_obj);
    if (string_pos("growtangle", _n) > 0 || string_pos("boxsplitter", _n) > 0)
        return 4;
    if (string_pos("tracking", _n) > 0)
        return 3;
    // DRBR: Gerson's hammer swings and thrown hammers hit as hard as a knight's sword
    if (string_pos("obj_hj_swing", _n) == 1 || string_pos("obj_hj_hammer", _n) == 1)
        return 1;
    // DRBR: Spamton NEO's arm laser and his BIG SHOTs (Chapter 2: twice his other pieces' damage) hit as hard
    if (_n == "obj_sn_biglaser" || _n == "obj_sn_bigshot" || _n == "obj_sn_lasthit")
        return 1;
    if (string_pos("sword", _n) > 0 || string_pos("slash", _n) > 0 || string_pos("blade", _n) > 0 || string_pos("tunnel", _n) > 0 || string_pos("scythe", _n) > 0)
        return 1;
    return 2;
}

// damage (and the frames of invincibility after it) of a hit of kind _kind
function kbr_hit_dmg(_kind, _nm)
{
    if (_nm)
        return [32, 45];
    switch (_kind)
    {
        case 1: return [24, 40];
        case 3: return [12, 30];
        case 4: return [8, 20];
    }
    return [16, 30];
}

// scr_damage -> knight_scale_taken -> here (online): the HP a hit takes. A hit that would end you leaves 1 HP and makes you
// OUT instead (you keep watching), so the battle never sees the party fall.
function kbr_dmg_taken(_d)
{
    var _M = kbr_match();
    if (is_undefined(_M) || _M.out || !_M.me)
        return 0;
    var _e = _M.eff;
    var _c = kbr_char();
    var _dmg = 0;
    var _ifr = 30;
    var _by = -1;
    if (variable_instance_exists(id, "kbr") && kbr != 0)
    {
        // a rival's skill
        _dmg = kbrd * (_e.skdmg / 100);
        _ifr = 30;
        if (variable_instance_exists(id, "kbrf") && kbrf >= 0 && kbrf != global.kfo.my)
        {
            _M.lby = kbrf;
            _by = kbrf;
        }
    }
    else
    {
        var _kind = kbr_hit_kind(object_index);
        var _nm = (_M.cur_ok >= 0 && kbr_nightmare(_M.cur_ok));
        var _t = kbr_hit_dmg(_kind, _nm);
        _dmg = _t[0];
        _ifr = _t[1];
    }
    _dmg *= _e.dmul / 100;
    _dmg = kbr_skill_absorb(_dmg);
    _dmg = max(0, round(_dmg));
    global.invc = (_ifr * (_e.ifr / 100)) / 30;
    _M.hits++;
    _M.hseq++;
    if (_dmg <= 0)
        return 0;
    _M.taken += _dmg;
    _M.hitfx = 8;
    // build 52: who hurt me and how much (the host heals a sender whose LIFESTEAL is on)
    if (_by >= 0)
        kfo_up({ k: "dg", mid: _M.mid, to: _by, d: min(_dmg, global.hp[_c]) });
    // build 51: HOW TO PLAY - nobody falls (the lesson tops HP up again)
    if (kfo_tut_on() && global.hp[_c] - _dmg <= 0)
        return max(0, global.hp[_c] - 1);
    if (_e.ohko || global.hp[_c] - _dmg <= 0)
    {
        var _left = max(0, global.hp[_c] - 1);
        // build 52: DETERMINATION - left at 1 HP instead of OUT
        if (kbr_det_save(_M))
            return _left;
        kbr_local_death();
        return _left;
    }
    return _dmg;
}

// your HP ran out: OUT. The battle goes on - you watch the others (the SOUL stays, unseen and untouchable).
function kbr_local_death()
{
    var _M = kbr_match();
    if (is_undefined(_M) || _M.out)
        return 0;
    kfo_out_note(_M, _M.eff.ohko ? "a hit with ONE HIT OUT on" : "a hit emptied your HP");
    _M.out = true;
    _M.died_t = round(kbr_now());
    _M.died_k = _M.R.k;
    snd_play(snd_hurt1);
    // build 48: your SOUL breaks as in Chapter 3's GAME OVER, then the GAME OVER itself over the battle (it goes on), then you watch
    kbr_ko_me_start(_M);
    with (obj_heart)
    {
        visible = false;
        canmove = 0;
    }
    kbr_log("* Your SOUL shattered... you are OUT.", c_red);
    kfo_up({ k: "out", mid: _M.mid, t: _M.died_t, ck: _M.R.k, hits: _M.hits, by: _M.lby });
    kbr_send_state(true);
    return 1;
}

// watching: kbr_spectate_tick (online_view.gml, build 47: camera modes, the watching keys)

// ---------- what this game tells the host ----------
function kbr_send_state(_force)
{
    var _M = kbr_match();
    if (is_undefined(_M) || !_M.me)
        return 0;
    var _now = current_time;
    if (!_M.out && instance_exists(obj_heart) && _now - _M.t_pos >= 66)
    {
        _M.t_pos = _now;
        var _h = instance_find(obj_heart, 0);
        // build 47: in tenths of a pixel (whole numbers in the message, so it stays short): the others draw your SOUL
        // where it is to 0.05 px (whole pixels put it up to half a pixel off when an attack moves it by fractions)
        // build 49: relative to the battle's camera (the arena is far into the cold place: x about 2000-2700 in the real
        // game - build 48 sent room positions and the host cut them at 1000, so nobody's SOUL was where it was drawn)
        // DRBR: on Flowery's board also its dash (d) and the board's dash speed (fa, tenths): a watcher's board follows it
        var _fo = kbr_fl_pos_extra();
        kfo_up_fast({ k: "p", mid: _M.mid, x: round((_h.x - kbr_ox()) * 10), y: round((_h.y - kbr_oy()) * 10), c: _M.R.k, h: _M.hold ? 1 : 0, d: _fo[0], fa: _fo[1] });
    }
    if (_force || _now - _M.t_st >= 500)
    {
        _M.t_st = _now;
        var _c = kbr_char();
        // the cycle this game is on (running, armed, or next) and the one after it: the host checks both against its own
        // timeline, so a game that went out of step is caught within half a second, not only when the next attack starts
        var _cc = (_M.R.ph == "arm") ? _M.R.arm_k : _M.R.k;
        var _sig = "";
        var _sig2 = "";
        if (_M.go && _M.R.ph != "boot" && _M.R.ph != "wait" && _cc >= 0)
        {
            _sig = kbr_tl_sig(kbr_tl_get(_M.tl, _cc));
            _sig2 = kbr_tl_sig(kbr_tl_get(_M.tl, _cc + 1));
        }
        kfo_up({ k: "s", mid: _M.mid, hp: _M.out ? 0 : max(0, global.hp[_c]), mhp: global.maxhp[_c], g: floor(_M.g), al: _M.out ? 0 : 1,
            c: _cc, ph: _M.R.ph, sig: _sig, sig2: _sig2, t: round(kbr_now()), gz: _M.gz, hit: _M.hits, bc: _M.R.bc, sk: kbr_skill_flags(), sd: _M.out ? 0 : _M.sk.shield,
            lat: round(kbr_rtt_shown(_M)), sp: _M.R.skipped, tk: _M.taken, hl: _M.healed, q: kbr_skill_q(), qs: _M.sk.sel, qh: is_undefined(_M.sk.hold) ? -1 : _M.sk.hold.sid,
            fm: kbr_fl_fm(_M) });
        _M.gz = 0;
    }
    return 1;
}

// ---------- the others ----------
// positions from the host ("ps": [[pid, x, y, hold], ...]) - drawn between the last two they sent
function kbr_on_ps(_m)
{
    var _M = kbr_match();
    if (is_undefined(_M))
        return 0;
    var _l = kfo_ja(_m, "l");
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        var _e = _l[_i];
        if (!is_array(_e) || array_length(_e) < 3 || !is_numeric(_e[0]) || !is_numeric(_e[1]) || !is_numeric(_e[2]))
            continue;
        var _id = string(_e[0]);
        // the host sends the places in tenths of a pixel (build 47)
        var _ex = _e[1] / 10;
        var _ey = _e[2] / 10;
        var _p = variable_struct_exists(_M.ps, _id) ? variable_struct_get(_M.ps, _id) : undefined;
        if (is_undefined(_p))
        {
            _p = { x: _ex, y: _ey, px: _ex, py: _ey, t: current_time, pt: current_time, h: 0 };
            variable_struct_set(_M.ps, _id, _p);
        }
        _p.px = kbr_ps_rx(_p);
        _p.py = kbr_ps_ry(_p);
        _p.pt = current_time;
        _p.x = _ex;
        _p.y = _ey;
        _p.t = current_time + 66;
        _p.h = (array_length(_e) > 3 && is_numeric(_e[3])) ? _e[3] : 0;
        // DRBR: Flowery's board (their dash, their board's dash speed in tenths)
        _p.fd = (array_length(_e) > 4 && is_numeric(_e[4])) ? _e[4] : 0;
        _p.ffa = (array_length(_e) > 5 && is_numeric(_e[5])) ? (_e[5] / 10) : 0;
    }
    return 1;
}

function kbr_ps_k(_p)
{
    var _span = max(1, _p.t - _p.pt);
    return clamp((current_time - _p.pt) / _span, 0, 1);
}

// build 49: the positions travel relative to the battle's camera (kbr_ox / kbr_oy); kbr_ps_x / kbr_ps_y give this game's
// room position (where to draw), kbr_ps_rx / kbr_ps_ry the camera-relative one
function kbr_ox()
{
    return kbr_cam_logical(0);
}

function kbr_oy()
{
    return kbr_cam_logical(1);
}

function kbr_ps_rx(_p)
{
    return lerp(_p.px, _p.x, kbr_ps_k(_p));
}

function kbr_ps_ry(_p)
{
    return lerp(_p.py, _p.y, kbr_ps_k(_p));
}

function kbr_ps_x(_p)
{
    return kbr_ps_rx(_p) + kbr_ox();
}

function kbr_ps_y(_p)
{
    return kbr_ps_ry(_p) + kbr_oy();
}

// the players still standing (pids, not me), from the host's last state
function kbr_alive_ids()
{
    var _M = kbr_match();
    var _o = [];
    if (is_undefined(_M) || !is_struct(_M.st))
        return _o;
    var _pl = kfo_ja(_M.st, "pl");
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        if (kfo_jn(_pl[_i], "al", 0) == 1 && kfo_jn(_pl[_i], "pid", -1) != global.kfo.my)
            array_push(_o, kfo_jn(_pl[_i], "pid", -1));
    }
    return _o;
}

// a player's colour: their place in the match's player list
function kbr_pslot(_pid)
{
    var _M = kbr_match();
    if (is_undefined(_M))
        return 0;
    for (var _i = 0; _i < array_length(_M.players); _i++)
    {
        if (kfo_jn(_M.players[_i], "pid", -2) == _pid)
            return _i;
    }
    return 7;
}

function kbr_pcol(_slot)
{
    switch (_slot mod 8)
    {
        case 0: return make_color_rgb(80, 160, 255);
        case 1: return make_color_rgb(255, 220, 60);
        case 2: return make_color_rgb(90, 230, 120);
        case 3: return make_color_rgb(200, 120, 255);
        case 4: return make_color_rgb(255, 150, 60);
        case 5: return make_color_rgb(70, 230, 230);
        case 6: return make_color_rgb(255, 120, 190);
    }
    return make_color_rgb(235, 235, 235);
}

// the others' SOULs: kbr_draw_souls (online_view.gml, build 47)
