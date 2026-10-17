// ===== Build 51: HOW TO PLAY - a guided practice match =====
// The ONLINE page's HOW TO PLAY row starts a local practice room (no server, no other players) against one DUMMY bot and
// walks you through the match one step at a time in a dialogue box over the battle. Steps that teach a key wait until you
// have done it ("Try it!"), the others just need NEXT. ENTER / the controller's START: next. ESC / hold the controller's
// BACK: leave the tutorial. Nobody can be knocked out while it runs (your HP and the DUMMY's are topped up), sudden death and
// the time limit are off. Finishing it is remembered in knightfights_online.ini ([player] tut_done); it can be played again
// any time. It is only offered on the ONLINE page, so it can never be opened in a room or during a match.

function kfo_tut()
{
    var _o = kfo_get();
    if (!variable_struct_exists(_o, "tut") || !is_struct(_o.tut))
        _o.tut = { on: false, step: 0, t: 0, ok: false, moved: 0, lx: 0, ly: 0, seen: [false, false, false, false, false, false, false], drew0: 0, used0: 0, sent0: 0, skip_t: 0 };
    return _o.tut;
}

function kfo_tut_on()
{
    return kfo_tut().on;
}

function kfo_tut_count()
{
    return 22;
}

// finished once (the ONLINE page says so)
function kfo_tut_done()
{
    ossafe_ini_open(kfo_ini_file());
    var _d = ini_read_real("player", "tut_done", 0);
    ossafe_ini_close();
    return _d == 1;
}

// the ONLINE page's HOW TO PLAY: a practice room set up for the lesson, started at once
function kfo_tut_start()
{
    if (kfo_in_room() || kfo_busy())
        return "Leave the room first.";
    kfo_practice_start();
    var _h = global.kfo.H;
    if (!is_struct(_h))
        return "Could not start the tutorial.";
    var _s = kfo_set_clean({});
    _s.kn = [0];
    _s.mhp = 150;
    _s.dmul = 25;
    _s.sd = 0;
    _s.tlim = 0;
    _s.fullheal = 1;
    _s.skills = 1;
    _s.tg = 1;
    _s.shards = 1;
    for (var _i = 0; _i < kbr_tg_count(); _i++)
        variable_struct_set(_s, "tgm" + string(_i), 1);
    _s.botp = 0;
    _s.bots = 1;
    _h.set = _s;
    _h.botcfg = [];
    kfo_host_bots(1);
    var _T = kfo_tut();
    _T.on = true;
    _T.began = false;
    _T.step = 0;
    _T.t = 0;
    _T.ok = false;
    _T.moved = 0;
    _T.seen = [false, false, false, false, false, false, false];
    _T.skip_t = 0;
    _T.auto_t = 0;
    _T.slow_f = 0;
    _T.tn = 0;
    var _why = kfo_host_start();
    if (is_string(_why) && _why != "")
    {
        _T.on = false;
        return _why;
    }
    return "";
}

// the step's text (the keys are the player's own, from KEYBINDS). "#" starts a new line.
// build 52: 22 steps in 8 lessons - the screen, moving, TP and skills, targeting, the fight, special skills, winning,
// playing online. The calm steps first (the Knight waits), then three with the Knight attacking, then calm again.
function kfo_tut_text(_st)
{
    var _T = kfo_tut();
    var _n = 0;
    for (var _i = 0; _i < 7; _i++)
    {
        if (_T.seen[_i])
            _n++;
    }
    switch (_st)
    {
        case 0: return "* Welcome to DRBR - DELTARUNE BATTLE ROYALE!#* This is a practice fight against a DUMMY. Nobody can lose here, and the Knight waits while you read.";
        case 1: return "* Down at the bottom: your HP.#* Get hit too much and your SOUL breaks. Then you're OUT.";
        case 2: return "* These cards are the other players: their SOUL, name, HP and SHADOW CRYSTALS.#* The last SOUL standing wins!";
        case 3: return "* Up here: the Knight you're fighting, its next attack, and the time until a new Knight steps in.";
        case 4: return "* Here comes the Knight! The ARROW KEYS move your SOUL around the box.#* Keep moving, stay away from the bullets.";
        case 5: return "* HOLD X (or SHIFT) while you move to go slowly.#* Great for slipping between bullets. Try it!";
        case 6: return "* " + kfo_key_label("breath") + " is HOLD BREATH: press it once to move faster, again to breathe out.#* Turn it on!";
        case 7: return "* The bar on the left is your TP. The white line is 60%: the price of ONE skill.#* HOLD " + kfo_key_label("charge") + ", let the red part pass the line, then LET GO.";
        case 8: return "* You got a skill! Your skills are the diamonds at the top left.#* TAP " + kfo_key_label("use") + " to pick one, HOLD " + kfo_key_label("use") + " to use it. Try it now!";
        case 9: return "* Press " + kfo_key_label("hold") + " to put the picked skill in HOLD, the diamond on the right.#* It waits there until you want it back.";
        case 10: return "* The big green plus is MAX: a full heal.#* Everyone starts with exactly one. Keep it for a real emergency!";
        case 11: return "* This strip picks who your RED skills hit.#* " + kfo_key_label("tgl") + " / " + kfo_key_label("tgr") + " change the mode. Look at all seven! (" + string(_n) + "/7)";
        case 12: return "* Now get through one whole attack without a single hit.#* (Slow walk and HOLD BREATH help!)";
        case 13: return "* TP fills slowly by itself, and FAST when you GRAZE:#* brush past bullets without touching them. Graze 3 times!";
        case 14: return "* Your turn to attack! Here's a SWORD.#* Pick it with " + kfo_key_label("use") + " and HOLD " + kfo_key_label("use") + " to send it at the DUMMY.";
        case 15: return "* Next attack, the DUMMY sends you DARKNESS!#* Anything on you shows as a chip with a timer, under your skills. Wait it out.";
        case 16: return "* RED skills bother the others: SLOW, CONFUSE, DARKNESS, and LOCK (it padlocks one of their skills).#* GREEN ones help you: heals, SHIELD, LIFESTEAL, and DETERMINATION (once a match).";
        case 17: return "* Knocking someone out gives you SHADOW CRYSTALS. They make your attacks hit harder.#* When only two are left, the FINAL TWO face the Roaring.";
        case 18: return "* To play with friends: on the ONLINE page, HOST A ROOM gives you a code.#* Friends type it in JOIN WITH CODE. FIND ROOMS shows open ones.";
        case 19: return "* The host's SETTINGS pick the bosses, the rules and BOTS. Some bosses change your SOUL!#* ONLINE > BOSSES shows every boss - and lets you practice against one.";
        case 20: return "* In a match: TAB shows everyone and your keys. T opens the chat.#* BACKSPACE gives up. PRACTICE plays a bot match any time.";
        case 21: return "* That's everything! Dodge, graze, charge, attack.#* You're filled with DETERMINATION. Good luck out there!";
    }
    return "";
}

// build 52: the lesson each step belongs to (shown over the box)
function kfo_tut_lesson(_st)
{
    if (_st <= 3)
        return "THE SCREEN";
    if (_st <= 6)
        return "MOVING";
    if (_st <= 10)
        return "TP AND SKILLS";
    if (_st == 11)
        return "TARGETING";
    if (_st <= 14)
        return "THE FIGHT";
    if (_st <= 16)
        return "SPECIAL SKILLS";
    if (_st == 17)
        return "WINNING";
    if (_st <= 20)
        return "PLAYING ONLINE";
    return "ALL DONE";
}

function kfo_tut_lesson_no(_st)
{
    var _l = ["THE SCREEN", "MOVING", "TP AND SKILLS", "TARGETING", "THE FIGHT", "SPECIAL SKILLS", "WINNING", "PLAYING ONLINE", "ALL DONE"];
    var _n = kfo_tut_lesson(_st);
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        if (_l[_i] == _n)
            return _i;
    }
    return 0;
}

// the steps you finish by doing something (they move on by themselves); the others need NEXT
function kfo_tut_action(_st)
{
    return (_st >= 4 && _st <= 9) || (_st >= 11 && _st <= 15);
}

// the Knight attacks only in these steps; in the others it waits (the match's clock stops between two attacks). build 52:
// the moving lessons fight too - between two attacks there is no box to move in
function kfo_tut_fight(_st)
{
    return (_st >= 4 && _st <= 6) || (_st >= 12 && _st <= 15);
}

// what the step waits for (true: done)
function kfo_tut_check(_M, _st)
{
    var _T = kfo_tut();
    var _S = _M.sk;
    switch (_st)
    {
        case 4: return _T.moved >= 200;
        case 5: return _T.slow_f >= 25;
        case 6: return variable_struct_exists(_M, "hold_on") && _M.hold_on;
        case 7: return _S.drawn > _T.drew0;
        case 8: return _S.used > _T.used0;
        case 9: return !is_undefined(_S.hold);
        case 11:
            for (var _i = 0; _i < 7; _i++)
            {
                if (!_T.seen[_i])
                    return false;
            }
            return true;
        case 12: return _T.dodged;
        case 13: return (_M.gz_all - _T.gz0) >= 3;
        case 14: return _S.sent > _T.sent0;
        case 15: return _T.dark_sent && _S.dark_t <= 0;
    }
    return true;
}

// build 52: what the step points at - [x0, y0, x1, y1] on the screen (from the camera's corner), or undefined
function kfo_tut_point(_M, _st)
{
    var _n = clamp(_M.eff.slots, 1, 4);
    var _box = undefined;
    with (obj_growtangle)
    {
        if (x > -1000 && bbox_right - bbox_left > 20)
            _box = [bbox_left - knight_cam_x() - 4, bbox_top - knight_cam_y() - 4, bbox_right - knight_cam_x() + 4, bbox_bottom - knight_cam_y() + 4];
    }
    switch (_st)
    {
        case 1: return [4, 438, 636, 478];
        case 2: return [466, 4, 632, 34];
        case 3: return [250, 2, 432, 36];
        case 4:
        case 5:
        case 6:
        case 12:
            return _box;
        case 7:
        case 13:
            return [4, 92, 62, 300];
        case 8:
        case 10:
        case 14:
            return [8, 8, 14 + 46 + ((_n - 1) * 27) + 4, 92];
        case 9:
            var _hx = 14 + 23 + (_n * 27) + 16;
            return [_hx - 27, 8, _hx + 27, 74];
        case 11: return [12, 404, 628, 434];
        case 15: return [76, 108, 210, 152];
    }
    return undefined;
}

// a step begins: what it needs set up
function kfo_tut_enter(_M, _st)
{
    var _T = kfo_tut();
    var _S = _M.sk;
    _T.step = _st;
    _T.t = 0;
    _T.ok = false;
    if (!variable_struct_exists(_S, "drawn"))
        _S.drawn = 0;
    _T.drew0 = _S.drawn;
    _T.used0 = _S.used;
    _T.sent0 = _S.sent;
    _T.gz0 = _M.gz_all;
    _T.hits0 = _M.hits;
    _T.k0 = _M.R.k;
    _T.dodged = false;
    // an attack already running when the dodge lesson begins counts too, as long as it lands no hit from here on
    _T.inrun = (_M.R.ph == "run");
    _T.clean = true;
    _T.auto_t = 0;
    _T.ouch = 0;
    // build 52: the text types out again; the movement lessons count from here
    _T.tn = 0;
    _T.moved = 0;
    _T.slow_f = 0;
    // HOLD BREATH: off at the start of its lesson (so turning it on is the lesson)
    if (_st == 6 && variable_struct_exists(_M, "hold_on"))
        _M.hold_on = false;
    // the charge lesson: enough TP to pass the line, not to fill it
    if (_st == 7)
        _M.g = max(_M.g, 75);
    // the skill lessons need a skill: a Heal 40 when the hand is empty
    if ((_st == 8 || _st == 9) && array_length(_S.slots) == 0)
        array_push(_S.slots, { sid: 11, rev: 0 });
    // the DARKNESS demo: 5 seconds of it, in the next attack (kfo_tut_tick)
    _T.dark_sent = false;
    // the SWORD lesson: a Sword in the first slot, picked
    if (_st == 14)
    {
        if (array_length(_S.slots) >= clamp(_M.eff.slots, 1, 4))
            array_delete(_S.slots, array_length(_S.slots) - 1, 1);
        array_insert(_S.slots, 0, { sid: 1, rev: 0 });
        _S.sel = 0;
        _S.cd = 0;
    }
    return 1;
}

// every step of the tutorial's match (from kfo_play_tick)
function kfo_tut_tick(_M)
{
    var _T = kfo_tut();
    if (!_T.on || is_undefined(_M))
        return 0;
    // the first step's set-up once (it used to run again every frame and keep the step's clock at 0)
    if (!variable_struct_exists(_T, "began") || !_T.began)
    {
        _T.began = true;
        kfo_tut_enter(_M, _T.step);
    }
    _T.t++;
    // nobody falls: your HP and the DUMMY's are topped up
    var _c = kbr_char();
    if (global.hp[_c] < global.maxhp[_c] * 0.4)
        global.hp[_c] = global.maxhp[_c];
    var _h = global.kfo.H;
    if (is_struct(_h))
    {
        for (var _i = 0; _i < array_length(_h.pl); _i++)
        {
            var _b = _h.pl[_i];
            if (_b.bot && _b.inm && _b.al && _b.hp < _b.mh * 0.5)
                _b.hp = _b.mh;
        }
    }
    // the lesson's own counters: how far the SOUL moved, the modes seen
    if (instance_exists(obj_heart))
    {
        var _hx = obj_heart.x;
        var _hy = obj_heart.y;
        var _mv = (_T.t > 1) ? min(20, point_distance(_T.lx, _T.ly, _hx, _hy)) : 0;
        _T.moved += _mv;
        // the slow-walk lesson: frames moving with X / SHIFT held
        if (_mv > 0 && button2_h())
            _T.slow_f = (variable_struct_exists(_T, "slow_f") ? _T.slow_f : 0) + 1;
        _T.lx = _hx;
        _T.ly = _hy;
    }
    if (variable_struct_exists(_M, "tg"))
        _T.seen[clamp(_M.tg.mode, 0, 6)] = true;
    // the dodge lesson: an attack that started after the step began and ended with no hit taken
    if (_T.step == 12 && !_T.dodged)
    {
        // an attack counts once it was seen running in this step and then ends (build 51 waited for the attack counter
        // to pass k0 + 1, which only happens when the SECOND attack ends: the first clean dodge never counted)
        if (_M.hits > _T.hits0)
        {
            _T.hits0 = _M.hits;
            _T.ouch = 60;
            _T.clean = false;
        }
        if (_M.R.ph == "run")
        {
            if (!_T.inrun)
            {
                _T.inrun = true;
                _T.clean = true;
            }
        }
        else if (_T.inrun)
        {
            _T.inrun = false;
            if (_T.clean && _M.hits == _T.hits0)
                _T.dodged = true;
        }
    }
    if (variable_struct_exists(_T, "ouch") && _T.ouch > 0)
        _T.ouch--;
    // build 52: the DARKNESS demo lands once an attack is running (there is a SOUL and a box to see it on)
    if (_T.step == 15 && !_T.dark_sent && _M.R.ph == "run" && instance_exists(obj_heart))
    {
        _T.dark_sent = true;
        _M.sk.dark_t = 150;
        _M.sk.dark_max = 150;
        _M.sk.dark_r = 58;
        snd_play(snd_knight_jump_quick);
    }
    // the Knight waits in the calm steps: between two attacks the match's clock stands still (this game's, the host's and
    // the clock target), so no new attack starts; an attack already running plays to its end
    var _now = current_time;
    var _dt = (variable_struct_exists(_T, "last_ms") && _T.last_ms > 0) ? (_now - _T.last_ms) : 0;
    _T.last_ms = _now;
    if (!kfo_tut_fight(_T.step) && _M.go && _M.R.ph != "run" && _M.R.ph != "arm" && _dt > 0 && _dt < 1000)
    {
        _M.t0ms += _dt;
        if (variable_struct_exists(_M, "ck") && is_struct(_M.ck) && variable_struct_exists(_M.ck, "target"))
            _M.ck.target += _dt;
        if (is_struct(global.kfo.H) && global.kfo.H.go)
            global.kfo.H.t0ms += _dt;
    }
    if (!_T.ok && kfo_tut_check(_M, _T.step))
    {
        _T.ok = true;
        _T.auto_t = 0;
        snd_play(snd_bell);
    }
    // the charge lesson never runs dry
    if (_T.step == 7 && !_T.ok && _M.g < 65 && !_M.sk.charging)
        _M.g = 75;
    // a step you finished by doing it moves on by itself a moment later
    if (_T.ok && kfo_tut_action(_T.step))
    {
        _T.auto_t++;
        if (_T.auto_t >= 45)
        {
            kfo_tut_enter(_M, _T.step + 1);
            return 1;
        }
    }
    // NEXT (ENTER / START), only once the step is done; ESC / holding BACK leaves
    if ((keyboard_check_pressed(vk_enter) || knight_pad_pressed(gp_start)) && kfo_tut_next(_M) == 2)
        return 1;
    var _padback = false;
    if (instance_exists(obj_gamecontroller))
    {
        var _g = instance_find(obj_gamecontroller, 0);
        if (variable_instance_exists(_g, "gamepad_id") && _g.gamepad_id >= 0)
            _padback = gamepad_button_check(_g.gamepad_id, gp_select);
    }
    _T.skip_t = _padback ? (_T.skip_t + 1) : 0;
    if ((keyboard_check_pressed(vk_escape) && !kfo_chat_typing()) || _T.skip_t >= 30)
        kfo_tut_finish(false);
    return 1;
}

// NEXT: 0 not yet (too soon, or the step is not done: a "can't" sound), 1 the next step, 2 finished
function kfo_tut_next(_M)
{
    var _T = kfo_tut();
    if (!_T.on || _T.t <= 10)
        return 0;
    // build 52: still typing - NEXT shows the whole text first
    if (variable_struct_exists(_T, "tn") && _T.tn < string_length(kfo_tut_text(_T.step)))
    {
        _T.tn = 9999;
        return 0;
    }
    if (!_T.ok)
    {
        snd_play(snd_cantselect);
        return 0;
    }
    if (_T.step + 1 >= kfo_tut_count())
    {
        kfo_tut_finish(true);
        return 2;
    }
    snd_play(snd_select);
    kfo_tut_enter(_M, _T.step + 1);
    return 1;
}

// the end (finished or left): back to the ONLINE page
function kfo_tut_finish(_done)
{
    var _T = kfo_tut();
    _T.on = false;
    if (_done)
    {
        ossafe_ini_open(kfo_ini_file());
        ini_write_real("player", "tut_done", 1);
        ossafe_ini_close();
        snd_play(snd_won);
    }
    kfo_back_to_lobby();
    kfo_close("");
    return 1;
}

// the dialogue box (over the top of the battle, between the skills and the player list) - build 52: Deltarune's own text
// box look (black, a thick white edge), the lesson's name and how far along you are over it, the text typed out with the
// text blip, and a yellow frame with a bouncing arrow on whatever the step talks about
function kfo_tut_draw(xx, yy)
{
    var _T = kfo_tut();
    if (!_T.on)
        return 0;
    var _M = kbr_match();
    // the pointer first (under the box)
    if (!is_undefined(_M))
        kfo_tut_draw_point(xx, yy, kfo_tut_point(_M, _T.step));
    var _x0 = xx + 186;
    var _x1 = xx + 454;
    var _full = kfo_tut_text(_T.step);
    // typing: about 1.5 letters a frame, a blip every other letter
    if (!variable_struct_exists(_T, "tn"))
        _T.tn = 0;
    var _len = string_length(_full);
    if (_T.tn < _len)
    {
        var _was = floor(_T.tn);
        _T.tn = min(_len, _T.tn + 1.5);
        if (floor(_T.tn) != _was && (floor(_T.tn) mod 2) == 0 && string_char_at(_full, floor(_T.tn)) != " ")
            snd_play(snd_text);
    }
    var _shown = floor(_T.tn);
    scr_84_set_draw_font("main");
    // the lines of the whole text (so the box does not grow while typing), then how much of each is shown
    var _lines = [];
    var _parts = [];
    var _rest = _full;
    while (string_pos("#", _rest) > 0)
    {
        array_push(_parts, string_copy(_rest, 1, string_pos("#", _rest) - 1));
        _rest = string_delete(_rest, 1, string_pos("#", _rest));
    }
    array_push(_parts, _rest);
    for (var _i = 0; _i < array_length(_parts); _i++)
    {
        var _wl = knight_wrap_font(_parts[_i], (_x1 - _x0) - 22, "main");
        for (var _j = 0; _j < array_length(_wl); _j++)
            array_push(_lines, _wl[_j]);
    }
    var _h = 12 + (array_length(_lines) * 15) + 18;
    // build 52: never over the battle box - under it (over the targeting strip), or at the usual place under where the box
    // goes when there is none between two attacks; a box too low for that: over it
    var _y0 = yy + 262;
    with (obj_growtangle)
    {
        if (x > -1000)
        {
            var _bb = bbox_bottom - yy;
            var _bt = bbox_top - yy;
            if (_bb + 22 + _h <= 400)
                _y0 = yy + max(_bb + 22, 250);
            else if (_bt - 8 - _h >= 52)
                _y0 = yy + _bt - 8 - _h;
            else
                _y0 = yy + 400 - _h;
        }
    }
    _y0 = min(_y0, yy + 400 - _h);
    // the lesson tab over the box
    draw_set_font(fnt_small);
    var _les = "LESSON " + string(kfo_tut_lesson_no(_T.step) + 1) + ": " + kfo_tut_lesson(_T.step);
    var _tw = string_width(_les) + 16;
    draw_set_color(c_black);
    draw_rectangle(_x0, _y0 - 14, _x0 + _tw, _y0, false);
    draw_set_color(c_white);
    draw_rectangle(_x0, _y0 - 14, _x0 + _tw, _y0, true);
    kbr_hud_text(_x0 + 8, _y0 - 12, _les, c_yellow);
    // progress: one pip a step, filled up to this one
    for (var _i = 0; _i < kfo_tut_count(); _i++)
    {
        var _px = _x1 - ((kfo_tut_count() - _i) * 5);
        draw_set_color((_i < _T.step) ? c_white : ((_i == _T.step) ? c_yellow : make_color_rgb(70, 70, 70)));
        draw_rectangle(_px, _y0 - 6, _px + 2, _y0 - 4, false);
    }
    // the box: Deltarune's (black, a 3-pixel white edge)
    draw_set_alpha(0.92);
    draw_set_color(c_black);
    draw_rectangle(_x0, _y0, _x1, _y0 + _h, false);
    draw_set_alpha(1);
    draw_set_color(c_white);
    for (var _k = 0; _k < 3; _k++)
        draw_rectangle(_x0 + _k, _y0 + _k, _x1 - _k, _y0 + _h - _k, true);
    scr_84_set_draw_font("main");
    var _left = _shown;
    var _cut = 0;
    for (var _i = 0; _i < array_length(_lines) && _left > 0; _i++)
    {
        var _ln = _lines[_i];
        var _part = string_copy(_ln, 1, _left);
        kbr_hud_text(_x0 + 11, _y0 + 9 + (_i * 15), _part, c_white);
        // the text's characters, the "#" breaks and the spaces the wrap took between lines
        _left -= string_length(_ln) + 1;
    }
    draw_set_font(fnt_small);
    var _fy = _y0 + _h - 14;
    var _typing = (_shown < _len);
    var _wait = !_T.ok;
    var _act = kfo_tut_action(_T.step);
    var _foot = _typing ? "" : (_wait ? (_act ? "TRY IT!" : "") : (_act ? "NICE!" : ((_T.step + 1 >= kfo_tut_count()) ? "ENTER: FINISH" : "ENTER: NEXT")));
    if (_T.step == 12 && variable_struct_exists(_T, "ouch") && _T.ouch > 0)
        _foot = "OUCH! TRY THE NEXT ONE";
    var _fc = _wait ? merge_color(c_yellow, c_orange, 0.5 + (0.5 * sin(current_time / 200))) : c_lime;
    kbr_hud_text(_x0 + 11, _fy, _foot, _fc);
    // NEXT's little arrow, bobbing (the game's own text box has one)
    if (!_typing && !_wait && !_act)
        kbr_tut_tri(_x1 - 72, _fy + 4 + round(sin(current_time / 150)), 4, 1, c_white);
    draw_set_halign(fa_right);
    kbr_hud_text(_x1 - 9, _fy, "ESC: LEAVE", c_gray);
    draw_set_halign(fa_left);
    return 1;
}

// a small filled triangle pointing down (_dir 1) or up (-1), its tip at _x, _y
function kbr_tut_tri(_x, _y, _s, _dir, _c)
{
    draw_set_color(_c);
    draw_triangle(_x - _s, _y - (_s * _dir), _x + _s, _y - (_s * _dir), _x, _y, false);
    return 1;
}

// the yellow frame on what the step talks about, and an arrow bouncing toward it from the middle of the screen
function kfo_tut_draw_point(xx, yy, _r)
{
    if (is_undefined(_r))
        return 0;
    var _a = 0.65 + (0.35 * sin(current_time / 180));
    var _x0 = xx + _r[0];
    var _y0 = yy + _r[1];
    var _x1 = xx + _r[2];
    var _y1 = yy + _r[3];
    draw_set_alpha(_a);
    draw_set_color(c_yellow);
    draw_rectangle(_x0, _y0, _x1, _y1, true);
    draw_rectangle(_x0 + 1, _y0 + 1, _x1 - 1, _y1 - 1, true);
    draw_set_alpha(1);
    var _cx = round((_x0 + _x1) / 2);
    var _bob = round(abs(sin(current_time / 160)) * 5);
    // over it pointing down when it is in the lower half, under it pointing up otherwise
    if (((_y0 + _y1) / 2) - yy > 240)
    {
        kbr_tut_tri(_cx, _y0 - 3 - _bob, 7, 1, c_black);
        kbr_tut_tri(_cx, _y0 - 5 - _bob, 5, 1, c_yellow);
    }
    else
    {
        kbr_tut_tri(_cx, _y1 + 3 + _bob, 7, -1, c_black);
        kbr_tut_tri(_cx, _y1 + 5 + _bob, 5, -1, c_yellow);
    }
    return 1;
}

// ===== Build 51: the big moments' announcements =====
// A knight stepping in, a new stage, the final two, sudden death: a black band opens across the middle of the screen, the
// title slams in (big, in the knight's colour, a shake and a white slash across it), then one flavour line types out under
// it with the text blip, and it all folds away. The flavour line is picked from the match's own timeline (the cycle number),
// so every player in the room reads the same one.
function kbr_bn_show(_title, _sub, _col)
{
    var _M = kbr_match();
    // build 52: HOW TO PLAY's box has that place to itself
    if (is_undefined(_M) || kfo_tut_on())
        return 0;
    _M.bn = { title: _title, sub: _sub, col: _col, t: 0, n: 0 };
    return 1;
}

// one of a few lines, the same in every game (_k: the cycle)
function kbr_bn_pick(_l, _k)
{
    return _l[abs(_k * 7 + 3) mod array_length(_l)];
}

function kbr_bn_knight(_ok, _nm, _k)
{
    // build 52: a secret boss: his own battle text (Jevil's from Chapter 1)
    var _en = kbr_ok_enc(_ok);
    if (is_struct(_en))
        return kbr_bn_pick(_en.flavor, _k);
    if (_nm)
        return kbr_bn_pick(["* The Knight's shadow stands up on its own.", "* Don't blink.", "* Two of them. That's twice as much Knight."], _k);
    switch (_ok)
    {
        case 0: return kbr_bn_pick(["* The Roaring Knight. It never really left.", "* The Knight raises its sword. The air goes very still.", "* Smells like cold steel and old stories."], _k);
        case 1: return kbr_bn_pick(["* Its outline sharpens. Everything feels faster.", "* It doesn't believe in second chances.", "* The bullets look... meaner, somehow."], _k);
        case 2: return kbr_bn_pick(["* The Knight crackles to life. Your hair stands up.", "* Something smells like burnt toast.", "* The air hums at a really rude frequency."], _k);
        case 3: return kbr_bn_pick(["* Violet light spills across the floor like a dream you forgot.", "* It's humming a song only it can hear.", "* Everything turns the color of a bruise."], _k);
        case 4: return kbr_bn_pick(["* Thorns curl out of the dark. Watch your step.", "* Something is growing where it shouldn't.", "* Every hit is going to sting."], _k);
    }
    return "* The Knight changes. You change with it.";
}

function kbr_bn_stage(_st, _k)
{
    switch (_st)
    {
        case 1: return kbr_bn_pick(["* The Knight remembers someone else's face.", "* It's trying on a different form."], _k);
        case 2: return kbr_bn_pick(["* Forms blur together. Who are you even fighting?", "* The Knight can't decide who to be."], _k);
        case 3: return kbr_bn_pick(["* A second Knight joins in. Rude.", "* The shadow gets up and draws its sword."], _k);
        case 4: return kbr_bn_pick(["* It will not end. (It will end eventually.)", "* Faster. Harder. No breaks."], _k);
    }
    return "";
}

// every step of the HUD: the clock
function kbr_bn_tick(_M)
{
    if (!variable_struct_exists(_M, "bn") || !is_struct(_M.bn))
        return 0;
    var _b = _M.bn;
    _b.t++;
    // the line types out (a blip every other letter)
    if (_b.t >= 22)
    {
        var _want = min(string_length(_b.sub), floor((_b.t - 22) * 1.2));
        if (_want > _b.n)
        {
            if ((_want mod 2) == 0 && string_char_at(_b.sub, _want) != " ")
                snd_play(snd_text);
            _b.n = _want;
        }
    }
    if (_b.t == 8)
        snd_play(snd_impact);
    if (_b.t > 150)
        _M.bn = undefined;
    return 1;
}

function kbr_bn_draw(xx, yy, _M)
{
    if (!variable_struct_exists(_M, "bn") || !is_struct(_M.bn))
        return 0;
    var _b = _M.bn;
    var _t = _b.t;
    // the band: opens (0-8), holds, folds away (130-150)
    var _open = (_t < 8) ? (_t / 8) : ((_t > 130) ? max(0, 1 - ((_t - 130) / 20)) : 1);
    // never over the battle box: under it when there is room above the targeting strip, else over it, else as low as
    // it can go (with no box on screen: the place under where the box usually is)
    var _half = 26;
    var _cy = yy + 376;
    with (obj_growtangle)
    {
        var _bt = bbox_top - yy;
        var _bb = bbox_bottom - yy;
        // just over the targeting strip (under the box); a box reaching that low: over the box, else as low as it goes
        if (_bb + 4 > 402 - (2 * _half))
        {
            if (_bt - 4 - (2 * _half) >= 118)
                _cy = yy + _bt - 4 - _half;
            else
                _cy = yy + 402 - _half;
        }
    }
    var _hh = round(_half * _open);
    if (_hh <= 0)
        return 0;
    draw_set_alpha(0.86);
    draw_set_color(c_black);
    draw_rectangle(xx, _cy - _hh, xx + 640, _cy + _hh, false);
    draw_set_alpha(1);
    draw_set_color(_b.col);
    draw_rectangle(xx, _cy - _hh, xx + 640, _cy - _hh + 1, false);
    draw_rectangle(xx, _cy + _hh - 1, xx + 640, _cy + _hh, false);
    if (_open < 1 && _t < 8)
        return 1;
    var _fade = (_t > 130) ? _open : 1;
    // the title: slams in from big, shakes, settles
    var _sc = (_t < 16) ? (1 + ((16 - _t) / 16) * 0.8) : 1;
    var _sh = (_t >= 8 && _t < 20) ? ((20 - _t) / 4) : 0;
    var _sx = (_sh > 0) ? (irandom_range(-1, 1) * _sh) : 0;
    var _sy = (_sh > 0) ? (irandom_range(-1, 1) * _sh) : 0;
    scr_84_set_draw_font("mainbig");
    draw_set_halign(fa_center);
    draw_set_alpha(_fade);
    draw_set_color(c_black);
    draw_text_transformed(xx + 322 + _sx, _cy - 23 + _sy + 2, _b.title, _sc, _sc, 0);
    draw_set_color(merge_color(_b.col, c_white, (_t < 14) ? 0.6 : 0));
    draw_text_transformed(xx + 320 + _sx, _cy - 23 + _sy, _b.title, _sc, _sc, 0);
    // the slash: a white line sweeping across the title once
    if (_t >= 8 && _t < 22)
    {
        var _f = (_t - 8) / 14;
        draw_set_alpha(_fade * (1 - _f));
        draw_set_color(c_white);
        var _lx = xx + 120 + (_f * 400);
        draw_line_width(_lx - 60, _cy - 2, _lx + 60, _cy - 26, 3);
    }
    // the flavour line, typing
    draw_set_alpha(_fade);
    scr_84_set_draw_font("main");
    draw_set_color(c_white);
    draw_text(xx + 320, _cy + 5, string_copy(_b.sub, 1, _b.n));
    draw_set_halign(fa_left);
    draw_set_alpha(1);
    draw_set_font(fnt_small);
    return 1;
}
