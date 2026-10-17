// ===== DRBR: PINK (DELTARUNE Chapter 5's secret boss, encounter 224) =====
// Online only. Her pieces are Chapter 5's own objects (make_pink.py: obj_pk_*, from the player's Chapter 5 data.win): the PURPLE
// SOUL's engine (obj_purplecontrols: the three lanes, the bomb grid, the rolling box, the 3D tunnel, the node maze), Pink inside
// the battle (the ball that jumps onto the box, the bomb throws, the concert stage), her cats, hearts and fuse bombs, the rolling
// box's lane bullets and the ghost's huge face, the tunnel's zaps, the concert's fans and haters; obj_dbulletcontroller's types
// 199-210 as obj_pk_dbc. This file is her battle object (obj_pk_pink: the knights' arm / hold / attack handshake, her body,
// her lines), the stage behind her, the clean-up, the purple SOUL's place in the hub (keys, watchers, the bots) and her sends.
// ONE PURPLE SOUL PER GAME: every game runs the same attack (the same cats and bombs from the same seeds on the same ticks);
// what a player does with their own SOUL (a bomb kicked, a heart collected, the tunnel's speed) is their game's own. Her fight's
// DOKI, dates and TP cap are not online (no command menu); her HEARTS charge your gauge instead. Source survey:
// online/notes/src_pink.md.

function kbr_enc_def_pink()
{
    // [phase, id, name, flags] in Chapter 5's own order (obj_pink_enemy's user event 0: before the first date - phase 1, after
    // it - phase 2, after the ghost split - phase 3; her last date's maze is the finale, flags 2). type / dif: obj_dbulletcontroller's
    // type and difficulty. tt: the attack's place in the timeline - Chapter 5's own turn timer (measured: t_pink53.py) plus a margin.
    return { key: "pink", cat: "secret", fid: KBR_FAM_PINK, chapter: 5, soul: "purple", sends: [51, 52, 53, 54, 55, 56], song: "PINK'S THEME - DELTARUNE Chapter 5",
        desc: "Chapter 5's secret boss. A PURPLE SOUL:#the arrows move you from lane to lane!",
        name: "Pink", short: "PINK", title: "PINK", col: make_color_rgb(230, 36, 123), lu: KBR_ENC_BASE + 4,
        music: "pink.ogg", obj: "obj_pk_pink", spr: "spr_pk_pink_idle", px: 470, py: 131, roar: 18, roar_dur: 1040,
        atk: [[1, 0, "Kitty Lanes", 0], [1, 1, "Bomb Grid", 0], [1, 2, "Kitty Lanes + Bombs", 0], [1, 3, "Heart Bombs", 0],
              [1, 4, "Mewers Live!", 0], [1, 5, "Kitty Mix", 0],
              [2, 6, "Rolling Box", 0], [2, 7, "3D Tunnel", 0], [2, 8, "Bomb Grid II", 0], [2, 9, "Mewers Live! Encore", 0],
              [2, 10, "Rolling Box Bursts", 0],
              [3, 11, "Ghost Face Push", 0], [3, 12, "Big Bomb Storm", 0], [3, 13, "Kitty Conga", 0], [3, 14, "3D Tunnel II", 0],
              [3, 15, "Kitty Rush", 0], [3, 16, "Bomb Chain", 0], [3, 17, "Mewers Live! Finale", 0], [4, 18, "Final Date", 2]],
        type: [200, 203, 200, 203, 209, 200, 202, 208, 203, 209, 202, 202, 203, 200, 208, 200, 203, 209, 210],
        dif: [0, 1, 1, 0, 0, 4, 0, 0, 4, 1, 2, 1, 2, 2, 1, 3, 3, 2, 0],
        tt: [540, 340, 500, 420, 460, 500, 420, 660, 390, 540, 240, 530, 460, 380, 660, 480, 420, 540, 1040],
        line: ["Purple, PURPLE,&you can't move,&WHATEVER!", "Figure out how&to move, see if&I care, MEW!", "Now that you're&PURPLE, you're&restricted in my&FELINE WEB!",
               "Before this body,&I was NOBODY!&A ghost! A NOTHING!", "WAIT, it's almost&time for my concert!", "Jealous!?&I BET you are!",
               "Bet you wanna STEAL&this body, like a&little grubby&puppet gremlin!!", "Well, who WOULDN'T!?&It's even got its&own limited-edition&voice clips!",
               "Hey, you stupid&gel pens!!&Stop FLIRTING!!", "You've also gotta&be an idol on&top of it!", "Haha, you guys&really are doomed!",
               "What the heck&is happening!?&Why are we SPLIT!?", "It's YOU! You&guys are making&her act funny&Die. Die! DIE!!!",
               "Hey, you're MY&body, GET IT!?&My body means...", "You do... what&I WANT!!!", "No... NO, it&can't be! It's&ME! It needs to do&what I SAY!!!",
               "AND STOP! MAKING!&MY HEART BEAT!!", "What? Nowadays just&being a tough battle&isn't enough to&scrape by, mew!", "Body! Listen!!&I'll... I'll&show you!!"],
        again: ["Stop... looking!", "Stop making my&body purr, you&jerks!", "Mew.&Mew!&MEW!", "What! WHAT do&I look like,&a pincushion!?", "I want to&DATE, mew!", "I like you,&mew!"],
        flavor: ["* Pink mews madly!", "* Pink spins her head around and laughs.", "* Pink stares at a mirror.. she doesn't turn around.",
                 "* The air swirls in rosy chaos.", "* Smells like perfume and plastic."],
        // her pieces that are not bullets (the cut's own clean-up never sees them)
        objs: [obj_pk_purple, obj_pk_move, obj_pk_smoke, obj_pk_chargeball, obj_pk_chargestar, obj_pk_meteor, obj_pk_flamebit, obj_pk_rollbg,
               obj_pk_curtains, obj_pk_dust, obj_pk_trail, obj_pk_ripple, obj_pk_sweat, obj_pk_tea, obj_pk_node, obj_pk_nodeact, obj_pk_sparkle,
               obj_pk_doki, obj_pk_healheart],
        // the ones that read the box (a send's go when the box does)
        boxy: [obj_pk_cat, obj_pk_lanebullet, obj_pk_bomb, obj_pk_bigbomb],
        cut: kbr_pk_cut };
}

// ---------- her battle object's fields, as her pieces read them (a send: Pink not on stage - the defaults) ----------
function kbr_pk_gv(_f)
{
    var _g = instance_find(obj_pk_pink, 0);
    if (_g != noone && variable_instance_exists(_g, _f))
        return variable_instance_get(_g, _f);
    switch (_f)
    {
        case "damage":
            return 10;
        case "c_pink":
            return make_color_rgb(230, 36, 123);
        case "visible":
            return true;
        case "x":
            return camerax() + 470;
        case "y":
            return cameray() + 131;
    }
    return 0;
}

function kbr_pk_on()
{
    return kbr_enc_is("pink");
}

// one of her attacks is running in this game (from its start to its cut)
function kbr_pk_attacking()
{
    return variable_global_exists("kbr_pk_dirty") && global.kbr_pk_dirty;
}

// Chapter 5's bomb dial (an NPC by her door: Default / Nicer / Meaner bombs, a save flag): online every game the same - Default
function kbr_pk_dial()
{
    return 0;
}

// Chapter 5's scr_wrap (an inclusive range: a value past _hi comes back at _lo, one step on)
function kbr_pk_wrap(_v, _lo, _hi)
{
    if ((_v mod 1) == 0)
    {
        while (_v > _hi || _v < _lo)
        {
            if (_v > _hi)
                _v = (_lo + _v) - _hi - 1;
            else if (_v < _lo)
                _v = ((_hi + _v) - _lo) + 1;
        }
        return _v;
    }
    var _old = _v + 1;
    while (_v != _old)
    {
        _old = _v;
        if (_v < _lo)
            _v = _hi - (_lo - _v);
        else if (_v > _hi)
            _v = _lo + (_v - _hi);
    }
    return _v;
}

// Chapter 5's scr_shakescreen(strength) (Chapter 3's has no strength)
function kbr_pk_shake(_n)
{
    with (instance_create(x, y, obj_shake))
    {
        shakex = _n;
        shakey = _n;
    }
    return 1;
}

// a HEART collected (Chapter 5: 1 HP to each member, the TP cap and TP up - her fight's own economy): online your gauge charges
// (GRAZE CHARGE applies: a cat's trailing heart is worth a graze or so, a bomb's or the tunnel's three) and you heal a little
function kbr_pk_heart(_tv)
{
    if (!kbr_mine())
        return 0;
    var _M = kbr_match();
    if (is_undefined(_M) || !kbr_on() || _M.out || !_M.me)
        return 0;
    kbr_gauge_add((_tv * 2.5 / 5) * (_M.eff.grz / 100), false);
    kbr_heal(_tv, false, false);
    return 1;
}

// the purple SOUL's keys (obj_purplecontrols reads them itself): off while you watch, type in the chat or have the quick settings
// open; CONFUSE / MIRROR CONTROLS turn them around
function kbr_pk_key(_k)
{
    var _M = kbr_match();
    if (!is_undefined(_M) && kbr_on() && variable_struct_exists(_M, "sk"))
    {
        var _inv = (_M.sk.conf_t > 0) != (_M.eff.mirror == 1);
        if (_inv)
        {
            switch (_k)
            {
                case "l": return "r";
                case "r": return "l";
                case "u": return "d";
                case "d": return "u";
            }
        }
    }
    return _k;
}

function kbr_pk_in_h(_k)
{
    if (kbr_soul_keys_off())
        return 0;
    switch (kbr_pk_key(_k))
    {
        case "l": return left_h();
        case "r": return right_h();
        case "u": return up_h();
        case "d": return down_h();
    }
    return 0;
}

function kbr_pk_in_p(_k)
{
    if (kbr_soul_keys_off())
        return 0;
    switch (kbr_pk_key(_k))
    {
        case "l": return left_p();
        case "r": return right_p();
        case "u": return up_p();
        case "d": return down_p();
    }
    return 0;
}

// the purple SOUL is on (her lanes, grid, box, tunnel or maze hold this game's SOUL)
function kbr_pk_purple_on()
{
    return instance_exists(obj_pk_purple);
}

// the tunnel sizes the SOUL by its ring (the room's GIANT / TINY SOUL waits until it is over)
function kbr_pk_soul_scaled()
{
    with (obj_pk_purple)
    {
        if (mode == 7)
            return true;
    }
    return false;
}

// her concert (type 209): Chapter 5's SOUL moves at 1.5 times the battle's speed there - two more on the room's SOUL SPEED
function kbr_pk_speed_bonus()
{
    with (obj_pk_dbc)
    {
        if (type == 209 && !(variable_instance_exists(id, "kbrx") && kbrx > 0))
            return 2;
    }
    return 0;
}

// a watcher's purple SOUL: on the followed one's lane (the lanes / the grid move it there as theirs moved; elsewhere it is put
// where theirs is). _tx, _ty: their SOUL's middle
function kbr_pk_puppet(_tx, _ty)
{
    with (obj_pk_purple)
    {
        var _dx = _tx - x - 1;
        var _dy = _ty - y - 1;
        switch (mode)
        {
            case 1:
                lane_y = clamp(round(_dy / 56) + 1, 0, 2);
                x_ongrid = clamp(_dx, -63, 63);
                break;
            case 2:
                lane_x = clamp(round((_dx / 40) + 1.5), 0, 3);
                lane_y = clamp(round((_dy / 40) + 1.5), 0, 3);
                break;
            default:
                x_ongrid = _dx;
                y_ongrid = _dy;
                break;
        }
    }
    return 1;
}

// ---------- her battle object (obj_pk_pink) ----------
function kbr_pk_create()
{
    scr_enemy_object_init();
    myself = 0;
    attacked = 1;
    talked = 1;
    acting = 0;
    rtimer = 0;
    difficulty = 0;
    myattackchoice = 1;
    datecount = 0;
    damage = 10;
    target = 4;
    mytarget = 0;
    c_pink = make_color_rgb(230, 36, 123);
    image_xscale = 2;
    image_yscale = 2;
    image_speed = 0;
    idlesprite = spr_pk_pink_idle;
    pose_t = 0;
    siner = 0;
    fsiner = 0;
    flash = 0;
    visible = true;
    say = "";
    say_t = 0;
    said = [];
    // Chapter 5's heartbeat count (obj_pink_enemy at her last date: the node maze's boxes pulse with it - obj_pk_nodeact's Draw)
    explosiontimer = 0;
    if (!instance_exists(obj_pk_bg))
        instance_create_depth(0, 0, 49000, obj_pk_bg);
    return 1;
}

function kbr_pk_step()
{
    if (!kbr_on())
        exit;
    explosiontimer++;
    if (say_t > 0)
        say_t--;
    if (pose_t > 0)
    {
        pose_t--;
        if (pose_t <= 0)
            idlesprite = spr_pk_pink_idle;
    }
    // the knights' handshake: the box at 1.5 (Chapter 5's place: the view's 320, 170) and, for her cats, the purple SOUL already
    // then (as her own Step does); the count held at 11 by the shared clock; the attack at 12
    if (global.mnfight == 1.5)
    {
        kbr_pk_arm();
        global.mnfight = 2;
        scr_turntimer(90);
    }
    if (global.mnfight == 2 && attacked == 0)
    {
        rtimer += kbr_rgate();
        if (rtimer == 12)
        {
            kbr_pk_attack();
            attacked = 1;
        }
    }
    return 1;
}

function kbr_pk_arm()
{
    var _d = kbr_enc_by_key("pink");
    var _ai = clamp(global.knight_lu.plan_i, 0, array_length(_d.type) - 1);
    var _ty = _d.type[_ai];
    difficulty = _d.dif[_ai];
    x = xstart;
    y = ystart;
    visible = true;
    idlesprite = spr_pk_pink_idle;
    if (!instance_exists(obj_growtangle))
        instance_create(camerax() + 320, cameray() + 170, obj_growtangle);
    var _b = instance_find(obj_growtangle, 0);
    global.kbr_pk_box = { x: _b.x, y: _b.y, mxs: variable_instance_exists(_b, "maxxscale") ? _b.maxxscale : _b.image_xscale,
        mys: variable_instance_exists(_b, "maxyscale") ? _b.maxyscale : _b.image_yscale };
    if (!instance_exists(obj_moveheart) && !instance_exists(obj_heart))
        scr_moveheart();
    // her cats: the purple SOUL from the box's arrival (Chapter 5: obj_pink_enemy at mnfight 1.5)
    if (_ty == 200)
    {
        with (obj_growtangle)
            instance_create_depth(x, y, 4, obj_pk_purple);
    }
    global.kbr_pk_dirty = true;
    return 1;
}

// the attack (self = obj_pk_pink; the frame the shared clock releases it): Chapter 5's set-up for it, her controller, her line
function kbr_pk_attack()
{
    var _d = kbr_enc_by_key("pink");
    var _ai = clamp(global.knight_lu.plan_i, 0, array_length(_d.type) - 1);
    var _ty = _d.type[_ai];
    difficulty = _d.dif[_ai];
    global.monsterattackname[0] = _d.atk[_ai][2];
    global.kbr_pk_dirty = true;
    var _M = kbr_match();
    var _cy = (is_struct(_M) && _M.R.k >= 0) ? kbr_tl_get(_M.tl, _M.R.k) : undefined;
    kbr_p_cycle(is_struct(_cy) ? kbr_mix(_cy.seed, 3301) : 1);
    if (!instance_exists(obj_growtangle))
        instance_create(camerax() + 320, cameray() + 170, obj_growtangle);
    switch (_ty)
    {
        case 203:
            // the bomb grid: the purple SOUL on its 4 x 4 nodes
            with (obj_growtangle)
            {
                if (!instance_exists(obj_pk_purple))
                    instance_create_depth(x, y, 4, obj_pk_purple);
            }
            with (obj_pk_purple)
                mode = 2;
            break;
        case 208:
            // the 3D tunnel: the big box, the purple SOUL on its rings
            with (obj_growtangle)
            {
                maxxscale = 3.75;
                maxyscale = 3.75;
                if (!instance_exists(obj_pk_purple))
                    instance_create_depth(x, y, 4, obj_pk_purple);
            }
            with (obj_pk_purple)
            {
                mode = 7;
                difficulty = other.difficulty;
            }
            break;
    }
    var _dc = scr_bulletspawner(x, y, obj_pk_dbc);
    _dc.type = _ty;
    _dc.difficulty = difficulty;
    myattackchoice = (_ty == 200) ? 1 : ((_ty == 202) ? 3 : ((_ty == 208) ? 4 : ((_ty == 209) ? 5 : ((_ty == 203) ? 6 : 1))));
    // Chapter 5's turn timer (her Step: scr_turntimer(300); the type's own first step sets its own)
    global.turntimer = 300;
    kbr_pk_say(_d, _ai);
    return 1;
}

function kbr_pk_say(_d, _ai)
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
        say = _d.line[clamp(_ai, 0, array_length(_d.line) - 1)];
        say_t = 75;
    }
    else
    {
        say = _d.again[kbr_irandom(array_length(_d.again) - 1)];
        say_t = 60;
    }
    idlesprite = (kbr_irandom(1) == 0) ? spr_pk_pink_laugh : spr_pk_pink_front_ohoho;
    pose_t = 45;
    snd_play((kbr_irandom(1) == 0) ? snd_pink_laugh_short : snd_pink_laugh_long);
    return 1;
}

// her body (Chapter 5's Draw: the pose at 2x, each with its own offset); hidden while she is in the battle herself (obj_pk_move
// - the ball, the bomb throws, the stage - shows her instead)
function kbr_pk_draw()
{
    if (!visible)
        return 0;
    siner += (1 / 6);
    var _ox = 0;
    var _oy = 0;
    var _sp = idlesprite;
    if (_sp == spr_pk_pink_laugh)
    {
        _ox = 52;
        _oy = 34;
        siner += (1 / 6);
    }
    else if (_sp == spr_pk_pink_front_ohoho)
    {
        _ox = 46;
        _oy = 39;
        siner += (1 / 6);
    }
    draw_sprite_ext(_sp, siner, x + _ox, y + _oy, 2, 2, 0, c_white, image_alpha);
    if (say_t > 0)
        kbr_enc_balloon(x - 6, y + 30, say, min(1, say_t / 10));
    return 1;
}

// ---------- the cut (the attack's end in this game): her pieces go, the SOUL is itself again, the box and she come back ----------
function kbr_pk_cut(_all)
{
    if (!kbr_pk_attacking() && !_all)
        return 0;
    global.kbr_pk_dirty = false;
    with (obj_pk_dbc)
    {
        if (_all || !(variable_instance_exists(id, "kbrx") && kbrx > 0))
            instance_destroy();
    }
    // (the purple controls' Destroy puts the box's scale back; obj_pk_move's puts her and the box back)
    with (obj_pk_purple)
        instance_destroy();
    with (obj_pk_move)
        instance_destroy();
    with (obj_pk_face)
        instance_destroy();
    with (obj_pk_rollbg)
        instance_destroy();
    with (obj_heart)
    {
        sprite_index = spr_dodgeheart;
        mask_index = spr_dodgeheartmask;
        visible = true;
        canmove = 1;
        image_alpha = 1;
    }
    with (obj_grazebox)
        grazetimefactor = 1;
    if (variable_global_exists("kbr_pk_box") && is_struct(global.kbr_pk_box))
    {
        var _B = global.kbr_pk_box;
        // (her last date's node maze takes the box away - type 210: it comes back where it was)
        if (!instance_exists(obj_growtangle))
            instance_create(_B.x, _B.y, obj_growtangle);
        with (obj_growtangle)
        {
            x = _B.x;
            y = _B.y;
            maxxscale = _B.mxs;
            maxyscale = _B.mys;
            visible = true;
            image_angle = 0;
        }
    }
    with (obj_pk_pink)
    {
        x = xstart;
        y = ystart;
        visible = true;
        idlesprite = spr_pk_pink_idle;
        say_t = min(say_t, 10);
    }
    with (obj_heroparent)
        image_alpha = 1;
    audio_stop_sound(snd_rumble);
    audio_stop_sound(snd_electroshock);
    return 1;
}

// ---------- the stage behind her (obj_pk_bg): Chapter 5's concert while she is out - dark, her spotlight, a row of fans ----------
function kbr_pk_bg_create()
{
    a = 0;
    t = 0;
    visible = true;
    return 1;
}

function kbr_pk_bg_step()
{
    a = clamp(a + (kbr_pk_on() ? 0.05 : -0.05), 0, 1);
    t++;
    return 1;
}

function kbr_pk_bg_draw()
{
    if (a <= 0)
        return 0;
    var _cx = camerax();
    var _cy = cameray();
    draw_set_alpha(a);
    draw_set_color(make_color_rgb(18, 4, 22));
    draw_rectangle(_cx - 10, _cy - 10, _cx + 650, _cy + 490, false);
    draw_set_alpha(1);
    draw_set_color(c_white);
    // her spotlight (Chapter 5's spr_pink_spotlight_pink over her place)
    draw_sprite_ext(spr_pk_pink_spotlight_pink, 0, _cx + 470 + 40, _cy, 2, 2, 0, c_white, a * 0.6);
    // the back row of the audience (Chapter 5: 16 dummies, every other one jumping with the beat)
    for (var _i = 0; _i < 16; _i++)
    {
        var _jy = ((((t div 15) + _i) mod 2) == 0) ? -4 : 0;
        draw_sprite_ext(((_i mod 3) == 0) ? spr_pk_pink_bg_dummy_glowstick : spr_pk_pink_bg_dummy, 0, _cx + 10 + (_i * 40), _cy + 440 + _jy, 2, 2, 0, c_white, a * 0.8);
    }
    return 1;
}

// ---------- the host's bots in her attacks ----------
// A bot dodges with free moves; inside her lanes, grid or rolling box a SOUL only moves along them: each step the bot's SOUL is put
// on the nearest lane / node of the purple SOUL's layout (Chapter 5's obj_purplecontrols: 3 lanes 56 apart and free along them,
// a 4 x 4 grid 40 apart, a "+" of 5 nodes 56 apart), then the normal dodging and hits apply. In the tunnel and the maze (rings,
// a graph) the bots play by the odds instead - as on Flowery's boards: now and then a ring's zap or a maze's box reaches the
// bot, which gets through as often as it plays well.
function kbr_pk_bot_snap(_s)
{
    if (!instance_exists(obj_pk_purple))
        return 0;
    var _p = instance_find(obj_pk_purple, 0);
    var _dx = _s.x - _p.x;
    var _dy = _s.y - _p.y;
    switch (_p.mode)
    {
        case 1:
            _s.y = _p.y + (clamp(round(_dy / 56), -1, 1) * 56);
            _s.x = _p.x + clamp(_dx, -63, 63);
            break;
        case 2:
            _s.x = _p.x + ((clamp(round((_dx / 40) + 1.5), 0, 3) - 1.5) * 40);
            _s.y = _p.y + ((clamp(round((_dy / 40) + 1.5), 0, 3) - 1.5) * 40);
            break;
        case 3:
            if (abs(_dx) >= abs(_dy))
            {
                _s.x = _p.x + (clamp(round(_dx / 56), -1, 1) * 56);
                _s.y = _p.y;
            }
            else
            {
                _s.x = _p.x;
                _s.y = _p.y + (clamp(round(_dy / 56), -1, 1) * 56);
            }
            break;
    }
    return 1;
}

function kbr_pk_bot_odds(_h, _b, _c, _box, _e)
{
    if (!instance_exists(obj_pk_purple))
        return false;
    var _p = instance_find(obj_pk_purple, 0);
    if (_p.mode != 7 && _p.mode != 8)
        return false;
    var _s = _b.bt;
    _s.x = _p.x;
    _s.y = _p.y + ((_p.mode == 7) ? 40 : 0);
    if (_s.inv > 0)
        _s.inv--;
    if (!variable_struct_exists(_s, "pkw"))
        _s.pkw = 30 + irandom(30);
    _s.pkw--;
    if (_s.pkw > 0)
        return true;
    _s.pkw = 45 + irandom(20);
    var _pass = clamp((_c.prec / 100) * (1 - (_c.miss / 100)) * (1 - (_c.react / 90)), 0.02, 0.995);
    if (random(1) < _pass || _s.inv > 0)
    {
        _b.g = min(100, _b.g + ((2.5 / 5) * (_e.grz / 100)));
        return true;
    }
    var _t = kbr_hit_dmg(2, false);
    var _dmg = max(1, round(_t[0] * (_e.dmul / 100)));
    if (_e.ohko)
        _dmg = _b.hp;
    kfo_bot_take(_b, _dmg);
    _b.hits++;
    _s.inv = round(_t[1] * (_e.ifr / 100));
    if (_b.hp <= 0)
        kfo_host_out_report(_b.pid, round(kfo_host_tick_now()), "out", -1);
    return true;
}

// ---------- her SENDS (ids 51-56, the PINK family) ----------
// Made in the TARGET's game only, from her own Chapter 5 pieces, around THEIR SOUL while their own boss fights on (make_pink.py
// made the pieces sendable: they join the send that makes them, end with it, and never touch the box, the SOUL or her controls).
// Each leaves a way out with any SOUL - free, or held by her lanes (rows / columns 56 apart, as her lanes are; a blast never
// wider than a lane step); no hearts come with a send (a send is an attack, not a gift).
//   51 KITTY PARADE (low)    six cats race through your SOUL's row and the rows 56 above and below it, from alternate sides
//   52 KITTY RAIN (low)      her vertical-lane cats (the unused type 204's columns): falling either side of you, rising through you
//   53 HEART SHOTS (mid)     five volleys of the rolling box's lane bullets from the four sides, each three abreast (52 apart),
//                            the middle one aimed where your SOUL is when it fires: step aside, not too far
//   54 FUSE BOMBS (mid)      three fuse bombs land on the nodes beside your SOUL (shown as they fly) and blow along their row and
//                            column one after another
//   55 MEGA BOMB (full)      one big bomb lands where your SOUL is: its cross-shaped blast (warned in red) is sized to your box
//                            and leaves its corners
//   56 ENCORE (full)         her audience pops up round your box (left, below, right) and throws its hearts at you; two haters
//                            lob their bars
function kbr_pk_is_send(_sid)
{
    return _sid >= 51 && _sid <= 56;
}

// a spot _off from _v along one axis, kept inside the box's [_lo, _hi] (the other side when that one is out)
function kbr_pk_sa_spot(_v, _off, _lo, _hi)
{
    var _p = _v + _off;
    if (_p < _lo || _p > _hi)
        _p = _v - _off;
    return clamp(_p, _lo, _hi);
}

function kbr_pk_sa_step(_G, _t, _g, _B, _S)
{
    switch (_G.sid)
    {
        case 51:
            if (_t == 0)
            {
                kbr_pk_sa_ghost(_G, _B, 40);
                _G.a = _S[1];
            }
            if (_t >= 10 && _t <= 85 && ((_t - 10) mod 15) == 0)
            {
                var _k = (_t - 10) div 15;
                var _rows = [1, 0, 2, 1, 2, 0];
                var _row = _rows[_k mod 6];
                var _side = ((_k mod 2) == 0) ? 1 : -1;
                var _cat = kbr_sa_mk(_G, _B[0] + (_side * 416), _G.a + ((_row - 1) * 56), obj_pk_cat);
                with (_cat)
                {
                    direction = 90 + (_side * 90);
                    speed = 9.6;
                    spin_radius = 1.5;
                    target = 3;
                    damage = 1;
                    depth = -20;
                }
                kbr_sa_sfx(snd_pink_throw, 1.1);
            }
            _G.end_t = 150;
            break;
        case 52:
            if (_t == 0)
            {
                kbr_pk_sa_ghost(_G, _B, 40);
                _G.a = _S[0];
            }
            if (_t >= 6 && _t <= 120)
            {
                var _top = (_B[1] - _B[3]) - 24;
                var _bot = (_B[1] + _B[3]) + 24;
                if (((_t - 6) mod 7) == 0)
                    kbr_pk_sa_cat(_G, _G.a - 28, _top, 270, 3.2);
                if (((_t - 6) mod 10) == 0)
                    kbr_pk_sa_cat(_G, _G.a, _bot, 90, 2);
                if (((_t - 6) mod 36) == 0)
                    kbr_pk_sa_cat(_G, _G.a + 28, _top, 270, 1.25);
            }
            _G.end_t = 240;
            break;
        case 53:
            if (_t == 0)
                kbr_pk_sa_ghost(_G, _B, 40);
            // (Chapter 5's type 202: from 352 px out at 8 a frame; the lanes beside the middle one 52 px apart)
            if (_t >= 10 && _t <= 90 && ((_t - 10) mod 20) == 0)
            {
                var _k = (_t - 10) div 20;
                var _dirs = [180, 270, 0, 90, 180];
                var _bd = _dirs[_k mod 5];
                for (var _ln = -1; _ln <= 1; _ln++)
                {
                    var _lb = kbr_sa_mk(_G, (_S[0] + lengthdir_x(352, _bd + 180)) + lengthdir_x(52 * _ln, _bd + 90), (_S[1] + lengthdir_y(352, _bd + 180)) + lengthdir_y(52 * _ln, _bd + 90), obj_pk_lanebullet);
                    with (_lb)
                    {
                        direction = _bd;
                        speed = 8;
                        image_angle = _bd;
                        if (_ln != 0)
                            sprite_index = spr_pk_pinklanebullet_lane;
                        target = 3;
                        damage = 1;
                        depth = -20;
                    }
                }
            }
            _G.end_t = 170;
            break;
        case 54:
            // (_G.b0: the send's own clock, restarted when a box change - a knight's split or hidden box, the attack's end - took
            // its bombs before any went off: they are thrown again round where your SOUL is then, while the send lives; _G.c
            // counts the throws)
            if ((_t - (variable_struct_exists(_G, "b0") ? _G.b0 : 0)) > 34 && _G.age < 480 && !variable_struct_exists(_G.seen, "obj_pk_boom") && kbr_pk_sa_alive(_G.gx, obj_pk_bomb) == 0)
            {
                _G.c++;
                _G.b0 = _t;
            }
            var _t4 = _t - (variable_struct_exists(_G, "b0") ? _G.b0 : 0);
            if (_t4 == 0)
            {
                kbr_pk_sa_ghost(_G, _B, 50);
                _G.a = _S[0];
                _G.b = _S[1];
            }
            // three bombs beside your SOUL (never on it: 40 px off on each axis it is moved, kept in the box), thrown from the
            // box's top right, each on its own node (a sent bomb is on no grid: make_pink.py's rules)
            if (_t4 == 6 || _t4 == 20 || _t4 == 34)
            {
                var _k = (_t4 - 6) div 14;
                var _ox = [-40, 40, 40 * ((kbr_rng_int(_g, 2) * 2) - 1)];
                var _oy = [-40, 0, 40];
                var _lx = (_B[0] - _B[2]) + 12;
                var _hx = (_B[0] + _B[2]) - 12;
                var _ly = (_B[1] - _B[3]) + 12;
                var _hy = (_B[1] + _B[3]) - 12;
                var _bx = kbr_pk_sa_spot(_G.a, _ox[_k], _lx, _hx);
                var _by = (_oy[_k] == 0) ? clamp(_G.b, _ly, _hy) : kbr_pk_sa_spot(_G.b, _oy[_k], _ly, _hy);
                var _sx = (_B[0] + _B[2]) + 60;
                var _sy = (_B[1] - _B[3]) - 40;
                var _gid = 100 + ((_G.gx mod 997) * 3) + _k;
                var _bm = kbr_sa_mk(_G, _sx, _sy, obj_pk_bomb);
                with (_bm)
                {
                    x = _sx;
                    y = _sy;
                    dest_x = _bx;
                    dest_y = _by;
                    grid_x = _gid;
                    grid_y = _gid * 7;
                    fuse_time = 70 + (_k * 12);
                    air_time = 1;
                    air_height = 90;
                    target = 3;
                    damage = 1;
                }
                kbr_sa_sfx(snd_pink_throw2, 1);
            }
            _G.end_t = max(200, _t - _t4 + 200);
            break;
        case 55:
            // (thrown again, as FUSE BOMBS', when a box change took it before it went off)
            if ((_t - (variable_struct_exists(_G, "b0") ? _G.b0 : 0)) > 10 && _G.age < 520 && !variable_struct_exists(_G.seen, "obj_pk_boom") && kbr_pk_sa_alive(_G.gx, obj_pk_bigbomb) == 0)
            {
                _G.c++;
                _G.b0 = _t;
            }
            var _t5 = _t - (variable_struct_exists(_G, "b0") ? _G.b0 : 0);
            if (_t5 == 0)
            {
                kbr_pk_sa_ghost(_G, _B, 60);
                _G.a = _S[0];
                _G.b = _S[1];
            }
            if (_t5 == 10)
            {
                // her blast's arms are 96 px across at full size (spr_fusebomb_explosion_2_oldmask x 8): here a size that leaves
                // the box's corners (and a lane step) clear - the red warning bands show the same size
                var _sm = clamp((min(_B[2], _B[3]) - 24) / 48, 0.3, 0.6);
                var _sx = (_B[0] + _B[2]) + 60;
                var _sy = (_B[1] - _B[3]) - 60;
                var _gid = 100 + ((_G.gx mod 997) * 3);
                var _bb = kbr_sa_mk(_G, _sx, _sy, obj_pk_bigbomb);
                with (_bb)
                {
                    x = _sx;
                    y = _sy;
                    dest_x = _G.a;
                    dest_y = _G.b;
                    grid_x = _gid;
                    grid_y = _gid * 7;
                    scale_multiplier = _sm;
                    air_time = 1;
                    target = 3;
                    damage = 1;
                }
                kbr_sa_sfx(snd_pink_throw2, 0.8);
            }
            _G.end_t = max(210, _t - _t5 + 210);
            break;
        case 56:
            if (_t == 0)
                kbr_pk_sa_ghost(_G, _B, 50);
            // her audience as Chapter 5 seats it (obj_pink_curtains: left, below and right of the box, 24 apart), each popping
            // in from 40 px out and throwing its heart (it turns to you, then flies); the 4th and 8th are haters
            if (_t >= 4 && _t <= 64 && ((_t - 4) mod 6) == 0)
            {
                var _k = (_t - 4) div 6;
                var _edge = _k mod 3;
                var _fx, _fy, _fa;
                switch (_edge)
                {
                    case 0:
                        _fx = (_B[0] - _B[2]) - 12;
                        _fy = (_B[1] - _B[3]) + 12 + (24 * kbr_rng_int(_g, max(1, floor(((_B[3] * 2) - 24) / 24) + 1)));
                        _fa = 270;
                        break;
                    case 1:
                        _fx = (_B[0] - _B[2]) + 12 + (24 * kbr_rng_int(_g, max(1, floor(((_B[2] * 2) - 24) / 24) + 1)));
                        _fy = (_B[1] + _B[3]) + 12;
                        _fa = 0;
                        break;
                    default:
                        _fx = (_B[0] + _B[2]) + 12;
                        _fy = (_B[1] - _B[3]) + 12 + (24 * kbr_rng_int(_g, max(1, floor(((_B[3] * 2) - 24) / 24) + 1)));
                        _fa = 90;
                        break;
                }
                var _fan = kbr_sa_mk(_G, _fx, _fy, obj_pk_fan);
                with (_fan)
                {
                    start_x = _fx;
                    start_y = _fy;
                    image_angle = _fa;
                    audience_hater = (_k == 3 || _k == 7) ? 1 : 0;
                    audience_shoottime = kbr_p_irandom(6);
                    audience_sway = 2;
                    target = 3;
                    damage = 1;
                    depth = -20;
                }
            }
            _G.end_t = 230;
            break;
    }
    return 1;
}

// how many of _obj send _gx has now
function kbr_pk_sa_alive(_gx, _obj)
{
    var _n = 0;
    with (_obj)
    {
        if (variable_instance_exists(id, "kbrx") && kbrx == _gx)
            _n++;
    }
    return _n;
}

// one of her cats (obj_pinkcatbullet) at _x, _y going _dir at _spd (wobbling: its mode 2, type 204's)
function kbr_pk_sa_cat(_G, _x, _y, _dir, _spd)
{
    var _c = kbr_sa_mk(_G, _x, _y, obj_pk_cat);
    with (_c)
    {
        direction = _dir;
        speed = _spd;
        mode = 2;
        target = 3;
        damage = 1;
        depth = -20;
    }
    return _c;
}

// her phantom beside your box while she sends it (the knights' sends show their sender's knight the same way)
function kbr_pk_sa_ghost(_G, _B, _d)
{
    var _T = kbr_sa_tel(_G, "spr", _B[0] + _B[2] + 50, _B[1] - _B[3] - 40, _d, 0);
    _T.spr = spr_pk_pink_front_ohoho;
    _T.xs = 2;
    return _T;
}

// the host's hidden copies at a bot (twin bullets round its SOUL: the same shapes and times as the real ones)
function kbr_pk_sa_bot(_s, _hx, _hy, _bx, _g, _d)
{
    var _bw = abs(_bx.sprite_width) / 2;
    var _bh = abs(_bx.sprite_height) / 2;
    switch (_s.sid)
    {
        case 51:
            for (var _k = 0; _k < 6; _k++)
            {
                var _rows = [1, 0, 2, 1, 2, 0];
                var _side = ((_k mod 2) == 0) ? 1 : -1;
                var _sh = kbr_skill_shot(_bx.x + (_side * 416), _hy + ((_rows[_k] - 1) * 56), spr_pk_bullet_catface, 10 + (_k * 15), 90 + (_side * 90), 9.6, _d);
                _sh.aim = false;
            }
            break;
        case 52:
            for (var _t = 6; _t <= 120; _t++)
            {
                if (((_t - 6) mod 7) == 0)
                    kbr_skill_shot(_hx - 28, _bx.y - _bh - 24, spr_pk_bullet_catface, _t, 270, 3.2, _d).aim = false;
                if (((_t - 6) mod 10) == 0)
                    kbr_skill_shot(_hx, _bx.y + _bh + 24, spr_pk_bullet_catface, _t, 90, 2, _d).aim = false;
            }
            break;
        case 53:
            // (each volley's middle bullet aimed at the bot's SOUL when it fires: the shot's own aim)
            for (var _k = 0; _k < 5; _k++)
            {
                var _dirs = [180, 270, 0, 90, 180];
                var _bd = _dirs[_k];
                kbr_skill_shot(_hx + lengthdir_x(352, _bd + 180), _hy + lengthdir_y(352, _bd + 180), spr_pk_pinklanebullet_animation, 10 + (_k * 20), _bd, 8, _d);
                for (var _ln = -1; _ln <= 1; _ln += 2)
                    kbr_skill_shot((_hx + lengthdir_x(352, _bd + 180)) + lengthdir_x(52 * _ln, _bd + 90), (_hy + lengthdir_y(352, _bd + 180)) + lengthdir_y(52 * _ln, _bd + 90), spr_pk_pinklanebullet_lane, 10 + (_k * 20), _bd, 8, _d).aim = false;
            }
            break;
        case 54:
            for (var _k = 0; _k < 3; _k++)
            {
                var _ox = [-40, 40, 40];
                var _oy = [-40, 0, 40];
                for (var _a = 0; _a < 4; _a++)
                    kbr_skill_shot(_hx + _ox[_k], _hy + _oy[_k], spr_pk_fusebomb, 76 + (_k * 26), _a * 90, 12, _d).aim = false;
            }
            break;
        case 55:
            for (var _a = 0; _a < 4; _a++)
                kbr_skill_shot(_hx, _hy, spr_pk_fusebomb_big, 90, _a * 90, 14, _d).aim = false;
            break;
        case 56:
            for (var _k = 0; _k < 11; _k++)
            {
                var _e = _k mod 3;
                var _ex = (_e == 0) ? (_bx.x - _bw - 12) : ((_e == 1) ? _bx.x : (_bx.x + _bw + 12));
                var _ey = (_e == 1) ? (_bx.y + _bh + 12) : _bx.y;
                kbr_skill_shot(_ex, _ey, spr_heartbullet, 24 + (_k * 6) + 32, point_direction(_ex, _ey, _hx, _hy), 4, _d);
            }
            break;
    }
    return 1;
}
