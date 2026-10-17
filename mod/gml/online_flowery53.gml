// ===== DRBR: FLOWERY (DELTARUNE Chapter 5's boss, encounter 225) =====
// Online only. His pieces are Chapter 5's own objects (make_flowery.py: obj_fl_*, from the player's Chapter 5 data.win): the
// ORANGE SOUL (hold the confirm key - Z - to charge, let go to DASH; up / down only), its scrolling board, the bamboo, vases,
// cacti, lilypads, the thorn wall, Seth's boxes and words, Aqua's knives, Blue's flowers and Yellow's beam, Orange's gloves,
// Green's flames and Flowery's own JARONA lunges and decoys. This file is his battle object (obj_fl_flowery: the knights' arm /
// hold / attack handshake), his friends' entrances and exits (Chapter 5's markers and timings), his lines, the tower
// background (Chapter 5's obj_flowery_towery and its shaders), the clean-up, the GROUP MERCY that moves his phases, the bots'
// orange SOUL and his sends.
// ONE ORANGE SOUL PER GAME: every game runs the same attack (the same set-up, the same COURSE - its own random stream, seeded
// by the cycle - started and cut on the same tick); the board's scroll is each player's own (their dashes), so a fast player
// meets more of the same course before the cut. Hits, parries and breaks are each game's own.
// Source survey: online/notes/src_flowery.md.

function kbr_enc_def_flowery()
{
    // [phase, id, name, flags]: his phases (Chapter 5's, each with its own friends on stage): 1 Flowery alone, 2 Aqua and Seth,
    // 3 Orange and Green, 4 Blue and Yellow, 5 Flowery alone again (after the trial); the finale THE FINAL JARONA (flags 2,
    // the Roaring's place). type: Chapter 5's attack type (kbr_fl_build); tt: the attack's length (measured: t_flowery53.py)
    return { key: "flowery", cat: "story", fid: KBR_FAM_FLOWERY, chapter: 5, soul: "orange", sends: [38, 39, 40, 41, 42, 43, 44], song: "FLOWER MAN - Toby Fox",
        desc: "Chapter 5's boss. An ORANGE SOUL:#hold Z, let go to DASH and PARRY!",
        name: "Flowery", short: "FLOWERY", title: "FLOWERY", col: make_color_rgb(255, 170, 60), lu: KBR_ENC_BASE + 2,
        music: "Flowerman_Arrangement.ogg", obj: "obj_fl_flowery", spr: "spr_fl_flowery_idle3", px: 500, py: 114, roar: 12, roar_dur: 640,
        atk: [[1, 0, "Bamboo Run", 0], [1, 1, "Jarona!", 0], [1, 2, "Thorn Chase", 0], [1, 3, "Petal Jarona", 0],
              [2, 4, "Seth's Book", 0], [2, 5, "Aqua's Knives", 0], [2, 6, "Seth's Book II", 0],
              [3, 7, "Tag Team", 0], [3, 8, "Just Kidding!", 0], [3, 9, "Cactus Chase", 0],
              [4, 10, "Justice Chase", 0], [5, 11, "Max Jarona", 0], [6, 12, "The Final Jarona", 2]],
        type: [623, 620, 624, 634, 630, 641, 631, 636, 638, 632, 635, 622, 639],
        tt: [420, 360, 330, 360, 330, 330, 330, 360, 360, 330, 330, 360, 640],
        // his opening lines (Chapter 5's, by phase) and his repeats
        line: ["Hah! You think&you can&match&my style!?", "Kris... isn't&your mother&calling you?", "If everyone&could just&be friends...",
               "Is that really&just what \"HEROES\"&can do!?", "I won't lose...&My friends are&behind me!", "Seth, remember&the patterns&I taught you!?",
               "Heh, I improved&them! Watch!", "Orange! Be brave,&it's your turn!", "Green! How&about&a $999 tip!?", "Don't cry, Orange.&Tears are for a&wedding's day...",
               "Yellow! Tonight...&justice rides&together!", "Feel it!&Smell it!&The power&of flowers!", "Enough, Kris!&I don't need a trial&to expose the truth!"],
        again: ["You might&turn over&a new leaf.", "Imagine that...&a branch&where we didn't&have to fight.", "I'll never let you&get to the Dark&Fountain...!",
                "But, I see your&hearts are set&in stone."],
        flavor: ["* Flowery emits the fragrance of hope!", "* Flowery holds onto his dream.", "* Flowery blooms in bravery.",
                 "* Flowery shows Aqua how to safely hold a knife!", "* Orange rides on Flowery's fist as they punch together!",
                 "* Flowery and Yellow point towards you side-by-side!"],
        objs: [obj_fl_box, obj_fl_book, obj_fl_pickup, obj_fl_wordflower, obj_fl_mfancy, obj_fl_mfog, obj_fl_mcenter, obj_fl_particle],
        boxy: [obj_fl_soul, obj_fl_ctrl, obj_fl_wall, obj_fl_bullet, obj_fl_word, obj_fl_pad, obj_fl_thorns, obj_fl_bloom, obj_fl_jarona, obj_fl_box, obj_fl_book, obj_fl_beam],
        pool: kbr_fl_pool, cut: kbr_fl_cut, finale: kbr_fl_finale };
}

// ---------- the attack pool: his phase decides (each phase's friends have their own attacks) ----------
// the phase of cycle _k: the match's stage (stage 0 phase 1 ... stage 4 phase 5) or the GROUP MERCY the host announced for
// it (kbr_tl_set_flph), whichever is further (the announcement of phase 6 is the finale's: kbr_fl_finale)
function kbr_fl_phase_of(_tl, _k, _st)
{
    var _p = clamp(_st + 1, 1, 5);
    if (variable_struct_exists(_tl, "flph"))
    {
        for (var _i = 0; _i < array_length(_tl.flph); _i++)
        {
            var _e = _tl.flph[_i];
            if (_e[0] <= _k && _e[1] <= 5)
                _p = max(_p, _e[1]);
        }
    }
    return clamp(_p, 1, 5);
}

// the finale (THE FINAL JARONA and the tower's ascent) on cycle _k: the first of Flowery's cycles from the one the host
// announced when the GROUP MERCY finished SUSIE'S IDEA (phase 6). The cycles before _k are made (kbr_tl_get makes them in order).
function kbr_fl_finale(_tl, _k)
{
    if (!variable_struct_exists(_tl, "flph"))
        return false;
    var _k6 = -1;
    for (var _i = 0; _i < array_length(_tl.flph); _i++)
    {
        if (_tl.flph[_i][1] == 6)
            _k6 = _tl.flph[_i][0];
    }
    if (_k6 < 0 || _k < _k6)
        return false;
    var _lu = kbr_enc_by_key("flowery").lu;
    for (var _j = _k6; _j < _k; _j++)
    {
        if (_j < array_length(_tl.cyc) && _tl.cyc[_j].reg == _lu)
            return false;
    }
    return true;
}

function kbr_fl_pool(_tl, _k, _st, _hard)
{
    var _d = kbr_enc_by_key("flowery");
    var _ph = kbr_fl_phase_of(_tl, _k, _st);
    var _o = [];
    for (var _i = 0; _i < array_length(_d.atk); _i++)
    {
        if (_d.atk[_i][3] == 0 && _d.atk[_i][0] == _ph)
            array_push(_o, _i);
    }
    if (array_length(_o) == 0)
        _o = [0];
    return _o;
}

// ---------- his battle object's fields, as his pieces read them (a send: no Flowery on stage - the defaults) ----------
function kbr_fl_gv(_f)
{
    var _g = instance_find(obj_fl_flowery, 0);
    if (_g != noone && variable_instance_exists(_g, _f))
        return variable_instance_get(_g, _f);
    switch (_f)
    {
        case "x":
            return camerax() + 500;
        case "y":
            return cameray() + 114;
        case "target":
            return 0;
        case "damage":
            return 99;
        case "moar_tension":
            return 1;
        case "introcon":
            return 3;
        case "open_chase_counter":
            return 0;
        case "thissprite":
            return spr_fl_flowery_idle3;
        case "siner":
            return 0;
        case "image_speed":
            return 1/6;
        case "phase":
            return 1;
        case "orange_marker":
        case "green_marker":
            return noone;
    }
    return 0;
}

// a field of the instance one of his fields holds (his friends' markers)
function kbr_fl_gv2(_f, _g)
{
    var _i = kbr_fl_gv(_f);
    if (is_numeric(_i) && _i != noone && instance_exists(_i) && variable_instance_exists(_i, _g))
        return variable_instance_get(_i, _g);
    return (_g == "x") ? (camerax() + 530) : ((_g == "y") ? (cameray() + 160) : 0);
}

// ---------- the attack's own clock and course (the same in every game) ----------
// global.kbr_fl_t replaces Chapter 5's global.time (the save's play time: every game's differs); the board's draws come from
// the attack's stream (kbr_fl_g, seeded by the cycle) - a hit, a parry or a dash in one game never moves another's course
function kbr_fl_g()
{
    if (!variable_global_exists("kbr_fl_gen") || !is_struct(global.kbr_fl_gen))
        global.kbr_fl_gen = kbr_rng(1);
    return global.kbr_fl_gen;
}

function kbr_fl_random(_n)
{
    return kbr_rng_unit(kbr_fl_g()) * _n;
}

function kbr_fl_irandom(_n)
{
    return kbr_rng_int(kbr_fl_g(), floor(_n) + 1);
}

function kbr_fl_random_range(_a, _b)
{
    return _a + (kbr_rng_unit(kbr_fl_g()) * (_b - _a));
}

function kbr_fl_irandom_range(_a, _b)
{
    var _lo = floor(min(_a, _b));
    var _hi = floor(max(_a, _b));
    return _lo + kbr_rng_int(kbr_fl_g(), (_hi - _lo) + 1);
}

function kbr_fl_choose()
{
    return argument[kbr_rng_int(kbr_fl_g(), argument_count)];
}

function kbr_fl_list_shuffle(_l)
{
    var _n = ds_list_size(_l);
    for (var _i = _n - 1; _i > 0; _i--)
    {
        var _j = kbr_rng_int(kbr_fl_g(), _i + 1);
        var _a = ds_list_find_value(_l, _i);
        ds_list_replace(_l, _i, ds_list_find_value(_l, _j));
        ds_list_replace(_l, _j, _a);
    }
    return _l;
}

// where Chapter 5 would have ended the turn (its pieces' end writes, kept as notes): _n frames from now. Nothing ends by it -
// the shared timeline's cut ends every attack - the tests measure each attack's real length by it.
function kbr_fl_done(_n)
{
    if (!variable_global_exists("kbr_fl_f"))
        return 0;
    var _t = global.kbr_fl_f + _n;
    if (global.kbr_fl_end < 0 || _t < global.kbr_fl_end)
        global.kbr_fl_end = _t;
    return 1;
}

// his voice clips (Chapter 5's snd_play_flowery: a voice line at its volume and pitch)
function kbr_fl_voice(_s, _v = 1, _p = 1)
{
    if (!is_numeric(_s) || _s < 0)
        return -1;
    return snd_play(_s, _v, _p);
}

function kbr_fl_on()
{
    return kbr_enc_is("flowery");
}

// the attacks whose Flowery is a Jarona copy (Chapter 5's choices 0, 1, 2, 16, 18, 19: he hides, the copy lunges)
function kbr_fl_is_jarona(_type)
{
    return _type == 620 || _type == 621 || _type == 634 || _type == 636 || _type == 638 || _type == 639;
}

// ---------- his battle object (obj_fl_flowery) ----------
function kbr_fl_create()
{
    image_xscale = 2;
    image_yscale = 2;
    image_speed = 1/6;
    visible = true;
    myself = 0;
    state = 0;
    siner = 0;
    float_siner = 0;
    idlesprite = spr_fl_flowery_idle3;
    thissprite = idlesprite;
    sprite_index = idlesprite;
    attacked = 1;
    talked = 1;
    acting = 0;
    rtimer = 0;
    // what Chapter 5's pieces read on him (obj_flowery_enemy's Create)
    target = 0;
    damage = 99;
    moar_tension = 1;
    introcon = 3;
    open_chase_counter = 0;
    phase = 1;
    myattackchoice = 0;
    jtype = 0;
    say = "";
    say_t = 0;
    said = [];
    // his friends (Chapter 5's obj_flowery_marker places: they wait off the screen's right edge, Yellow high above)
    purple_marker = kbr_fl_marker(camerax() + camerawidth() + 200, cameray() + 72, spr_seth_idle_serious_flowery, 1/6, 2);
    aqua_marker = kbr_fl_marker(camerax() + camerawidth() + 200, cameray() + 228, spr_fl_enemy_aqua_spin, 1/3, 2);
    orange_marker = kbr_fl_marker(camerax() + camerawidth() + 200, (cameray() + 90) - 40, spr_fl_enemy_orange_flowery_angry, 0, 2);
    orange_marker.image_index = 1;
    green_marker = kbr_fl_marker(camerax() + camerawidth() + 200, cameray() + 214, spr_green_together, 1/6, 2);
    blue_marker = kbr_fl_marker(camerax() + camerawidth() + 200, cameray() + 40, spr_enemy_blue_ballet, 1/6, 2);
    yellow_marker = kbr_fl_marker(camerax() + 532 + 72, (cameray() + 160) - 600, spr_fl_yellow_cool_fall_armsraised, 1/6, -2);
    on_stage = 1;
    enter_t = 0;
    // Chapter 5's start sets the pillars' perspective (obj_initializer2: global.parallax_focal_length = 160)
    if (!variable_global_exists("parallax_focal_length"))
        global.parallax_focal_length = 160;
    // the tower behind (Chapter 5's obj_flowery_towery: it makes its pillars; Chapter 5's lyrics are the hub's own)
    if (!instance_exists(obj_fl_towery))
        towery = instance_create_depth(camerax() + 320, cameray(), depth + 1000, obj_fl_towery);
    else
        towery = instance_find(obj_fl_towery, 0);
    return 1;
}

function kbr_fl_marker(_x, _y, _spr, _sp, _xs)
{
    var _m = instance_create_depth(_x, _y, depth + 100, obj_fl_friend);
    _m.sprite_index = _spr;
    _m.image_xscale = _xs;
    _m.image_yscale = 2;
    _m.image_speed = _sp;
    _m.image_alpha = 1;
    _m.xstart = _x;
    _m.ystart = _y;
    return _m;
}

function kbr_fl_step()
{
    if (!kbr_on())
        exit;
    if (say_t > 0)
        say_t--;
    float_siner++;
    // the knights' handshake: the box at 1.5 (Chapter 5's: full width, a third tall), the count held at 11 by the shared clock,
    // the attack at 12
    if (global.mnfight == 1.5)
    {
        var _d = kbr_enc_by_key("flowery");
        var _ai = clamp(global.knight_lu.plan_i, 0, array_length(_d.type) - 1);
        jtype = _d.type[_ai];
        // the cycle this attack is (the GROUP MERCY's count is by cycle)
        var _Ma = kbr_match();
        global.kbr_fl_k = is_struct(_Ma) ? _Ma.R.arm_k : -1;
        global.kbr_fl_tpk = 0;
        // the pieces' own streams (kbr_fl_pg) start from the cycle's seed: the same in every game
        var _cy0 = (is_struct(_Ma) && global.kbr_fl_k >= 0) ? kbr_tl_get(_Ma.tl, global.kbr_fl_k) : undefined;
        global.kbr_fl_pseed = is_struct(_cy0) ? kbr_mix(_cy0.seed, 4441) : 1;
        global.kbr_fl_pn = 0;
        if (!instance_exists(obj_growtangle))
            instance_create(camerax() + 320, cameray() + 170, obj_growtangle);
        var _b = instance_find(obj_growtangle, 0);
        global.kbr_fl_box = { x: _b.x, y: _b.y, xs: _b.image_xscale, ys: _b.image_yscale, mxs: variable_instance_exists(_b, "maxxscale") ? _b.maxxscale : _b.image_xscale,
            mys: variable_instance_exists(_b, "maxyscale") ? _b.maxyscale : _b.image_yscale };
        with (obj_growtangle)
        {
            maxxscale = camerawidth() / 70;
            maxyscale = 0.6779661016949152;
            x -= 5;
        }
        // a Jarona attack: Flowery's copy at his place lunges, he hides (The Final Jarona: the copy waits unseen for the
        // gauntlet, he goes behind the box); the others: he goes behind the box
        if (kbr_fl_is_jarona(jtype))
        {
            var _jarona = instance_create(x, y, obj_fl_jarona);
            if (jtype == 638)
                _jarona.can_kidding = true;
            if (jtype == 639)
            {
                _jarona.visible = false;
                depth = obj_growtangle.depth + 1;
            }
            else
                visible = false;
        }
        else
            depth = obj_growtangle.depth + 1;
        global.kbr_fl_dirty = true;
        if (!instance_exists(obj_moveheart) && !instance_exists(obj_heart))
        {
            with (scr_moveheart())
            {
                distx = (obj_growtangle.x - 10 - 75) + 10;
                disty = (obj_growtangle.y - 10) + 10;
                dist = point_distance(x, y, distx, disty);
                move_towards_point(distx, disty, dist / 12);
                alarm[0] = 12;
            }
        }
        global.mnfight = 2;
        scr_turntimer(90);
    }
    if (global.mnfight == 2 && attacked == 0)
    {
        rtimer += kbr_rgate();
        if (rtimer == 12)
        {
            kbr_fl_attack();
            attacked = 1;
        }
    }
    if (attacked == 1 && variable_global_exists("kbr_fl_f"))
        global.kbr_fl_f++;
    // the attack's own clock (Chapter 5's global.time)
    global.kbr_fl_t = (variable_global_exists("kbr_fl_t") ? global.kbr_fl_t : 0) + 1;
    kbr_fl_friends();
    return 1;
}

// the attack of the cycle (self = obj_fl_flowery; on the frame the shared clock releases it)
function kbr_fl_attack()
{
    var _d = kbr_enc_by_key("flowery");
    var _ai = clamp(global.knight_lu.plan_i, 0, array_length(_d.type) - 1);
    jtype = _d.type[_ai];
    global.turntimer = _d.tt[_ai];
    global.monsterattackname[0] = _d.atk[_ai][2];
    // the course's stream: one draw from the cycle's shared stream (kbr_rgate seeded it: every game the same) seeds it; the
    // board then draws from its own stream only, so nothing a player does moves the shared one
    global.kbr_fl_gen = kbr_rng(kbr_mix(floor(kbr_random(2147480000)), 5011));
    global.kbr_fl_t = 0;
    global.kbr_fl_f = 0;
    global.kbr_fl_end = -1;
    global.kbr_fl_dirty = true;
    phase = _d.atk[_ai][0];
    // the friends of this phase come on stage (Chapter 5: they came with their phase)
    kbr_fl_cast(phase);
    // Chapter 5's open_chase_counter grew with your hits (adaptive): fixed by phase here (the same course for everyone)
    open_chase_counter = (phase >= 3) ? 2 : ((phase == 2) ? 1 : 0);
    kbr_fl_build(jtype);
    // THE FINAL JARONA: the tower climbs (Chapter 5's climb after SUSIE'S IDEA, as the battle's own tower shows it)
    kbr_fl_ascent(jtype == 639);
    // the SOUL under the orange one does not move on its own (Chapter 3's obj_heart reads the arrows; the orange SOUL drags it)
    with (obj_heart)
    {
        if (variable_instance_exists(id, "canmove"))
            canmove = 0;
    }
    global.kbr_fl_turns = (variable_global_exists("kbr_fl_turns") ? global.kbr_fl_turns : 0) + 1;
    kbr_fl_say(_d, _ai);
    return 1;
}

// his line for attack _ai: its own the first time in this match, then one of his repeats
function kbr_fl_say(_d, _ai)
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
    }
    else
        say = _d.again[kbr_rng_int(kbr_fl_g(), array_length(_d.again))];
    say_t = 75;
    return 1;
}

// ---------- his friends (Chapter 5's entrances and exits, in the phase that has them) ----------
// on_stage: the phase whose friends are out now (1: none). A phase change sends the old pair off (Chapter 5's exits) and brings
// the new pair in (its entrances) at the start of the attack that has them
function kbr_fl_cast(_ph)
{
    var _want = (_ph == 2 || _ph == 3 || _ph == 4) ? _ph : 1;
    if (_want == on_stage)
        return 0;
    // the old pair leaves
    switch (on_stage)
    {
        case 2:
            snd_play(snd_awkward);
            with (purple_marker)
            {
                sprite_index = spr_fl_seth_idle_dizzy_flowery;
                speed = 4;
                direction = 180;
                gravity_direction = 0;
                gravity = 0.3;
            }
            with (aqua_marker)
            {
                sprite_index = spr_fl_enemy_aqua_spin;
                image_speed = 1/3;
                speed = 4;
                direction = 180;
                gravity_direction = 0;
                gravity = 0.3;
            }
            break;
        case 3:
            with (green_marker)
            {
                sprite_index = spr_fl_enemy_green_witharmandpan_flowery;
                image_speed = 0;
                vspeed = -10;
                scr_delay_var("image_index", 1, 13);
                scr_script_delayed(snd_play, 13, snd_item);
            }
            with (orange_marker)
                scr_delay_var("visible", false, 13);
            break;
        case 4:
            with (blue_marker)
            {
                scr_oflash();
                scr_lerpvar("x", x, xstart, 56, 2, "in");
                vspeed = -2;
                sprite_index = spr_fl_blue_hover;
                image_speed = 1/3;
            }
            with (yellow_marker)
            {
                sprite_index = spr_fl_yellow_jump;
                scr_lerpvar("x", x, xstart + 200, 60, 2, "in");
                vspeed = -2;
            }
            break;
    }
    on_stage = _want;
    enter_t = 0;
    // the new pair comes in
    switch (_want)
    {
        case 2:
            kbr_fl_marker_home(purple_marker, spr_seth_idle_serious_flowery, 1/6);
            kbr_fl_marker_home(aqua_marker, spr_fl_enemy_aqua_spin, 1/3);
            with (purple_marker)
                scr_lerpvar("x", x, camerax() + 532, 15, 2, "out");
            with (aqua_marker)
            {
                scr_lerpvar("x", x, camerax() + 543, 15, 2, "out");
                scr_delay_var("sprite_index", spr_enemy_aqua_idle, 22);
                scr_delay_var("image_speed", 1/6, 22);
            }
            break;
        case 3:
            kbr_fl_marker_home(orange_marker, spr_fl_enemy_orange_flowery_angry, 0);
            kbr_fl_marker_home(green_marker, spr_green_together, 1/6);
            with (green_marker)
                scr_lerpvar("x", x, camerax() + 536, 15, 2, "out");
            break;
        case 4:
            kbr_fl_marker_home(blue_marker, spr_enemy_blue_ballet, 1/6);
            kbr_fl_marker_home(yellow_marker, spr_fl_yellow_cool_fall_armsraised, 1/6);
            with (blue_marker)
                scr_lerpvar("x", x, camerax() + 502, 15, 2, "out");
            break;
    }
    return 1;
}

// a friend back at its waiting place (off the screen), still, its look
function kbr_fl_marker_home(_m, _spr, _sp)
{
    if (!instance_exists(_m))
        return 0;
    with (_m)
    {
        speed = 0;
        gravity = 0;
        vspeed = 0;
        hspeed = 0;
        x = xstart;
        y = ystart;
        visible = true;
        sprite_index = _spr;
        image_speed = _sp;
        image_index = 0;
    }
    return 1;
}

// every step: the entrances that take more than one step (Orange's jump, Yellow's fall), the friends' floating
function kbr_fl_friends()
{
    enter_t++;
    if (on_stage == 3 && enter_t <= 5 && instance_exists(orange_marker))
    {
        // Orange jumps in beside him (Chapter 5: 5 frames from his side to her place)
        orange_marker.x = lerp(xstart + 150, camerax() + 494, enter_t / 5);
        orange_marker.y = lerp(ystart - 80, cameray() + 90, enter_t / 5);
        if (enter_t == 5)
        {
            with (orange_marker)
            {
                xstart = x;
                ystart = y;
            }
        }
    }
    if (on_stage == 4 && instance_exists(yellow_marker))
    {
        // Yellow falls from above (12 frames, yellow afterimages), lands with a whack, stands at 43
        if (enter_t < 13)
        {
            with (yellow_marker)
                y = lerp((cameray() + 160) - 600, cameray() + 160, other.enter_t / 12);
        }
        if (enter_t == 13)
        {
            with (yellow_marker)
                sprite_index = spr_fl_yellow_cool_landing;
            snd_play(snd_whack_absurdlyloud, 0.2, 0.8);
        }
        if (enter_t == 43)
        {
            with (yellow_marker)
            {
                sprite_index = spr_yellow_idle;
                image_xscale = 2;
                x -= 72;
                ystart = y;
            }
        }
    }
    // Seth floats (Chapter 5: his marker bobs 8 px)
    if (on_stage == 2 && instance_exists(purple_marker) && enter_t > 15)
        purple_marker.y = purple_marker.ystart + (sin(float_siner * 0.5) * 8);
    return 1;
}

// ---------- his look ----------
function kbr_fl_draw()
{
    // Chapter 5: spr_flowery_idle3, floating sin(t * 0.33) * 5
    siner += image_speed;
    var _fy = sin(float_siner * 0.33) * 5;
    draw_sprite_ext(thissprite, siner, x, y + _fy, image_xscale, image_yscale, 0, image_blend, image_alpha);
    if (say_t > 0)
        kbr_enc_balloon(x - 8, y + 40, say, min(1, say_t / 10));
    return 1;
}

// every one of his pieces' objects (the cut, the bots' view of his board)
function kbr_fl_pieces()
{
    return [obj_fl_jarona, obj_fl_soul, obj_fl_ctrl, obj_fl_wall, obj_fl_bullet, obj_fl_word, obj_fl_orbit, obj_fl_pad, obj_fl_thorns, obj_fl_bloom, obj_fl_box,
        obj_fl_book, obj_fl_pickup, obj_fl_wordflower, obj_fl_beam, obj_fl_mfancy, obj_fl_mfog, obj_fl_mcenter, obj_fl_particle];
}

// ---------- the cut (every game the same frame): his pieces go, the SOUL, the box and he come back ----------
function kbr_fl_cut(_all)
{
    if (!variable_global_exists("kbr_fl_dirty") || !global.kbr_fl_dirty)
        return 0;
    global.kbr_fl_dirty = false;
    // the GROUP MERCY: this game's FLOWERY TP in the attack goes to the host with the next status
    kbr_fl_mercy_note();
    kbr_fl_ascent(false);
    // (his pieces sent by players go too: a Flowery send lives on his board, and the board ends here)
    var _l = kbr_fl_pieces();
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        with (_l[_i])
            instance_destroy();
    }
    with (obj_heart)
    {
        visible = true;
        if (variable_instance_exists(id, "canmove"))
            canmove = 1;
        image_alpha = 1;
    }
    with (obj_grazebox)
    {
        image_angle = 0;
        if (variable_instance_exists(id, "angle"))
            angle = 0;
    }
    if (variable_global_exists("kbr_fl_box") && is_struct(global.kbr_fl_box))
    {
        var _B = global.kbr_fl_box;
        // (the box as the next attack expects it: its own place and full size - it was growing when Flowery widened it)
        with (obj_growtangle)
        {
            x = _B.x;
            y = _B.y;
            maxxscale = _B.mxs;
            maxyscale = _B.mys;
            image_xscale = _B.mxs;
            image_yscale = _B.mys;
        }
    }
    with (obj_fl_flowery)
    {
        visible = true;
        depth = object_get_depth(object_index);
        x = xstart;
        y = ystart;
        thissprite = idlesprite;
    }
    // his voice and the charge's loop stop with the attack
    audio_stop_sound(snd_chargeshot_charge);
    return 1;
}

// ---------- the tower's ascent (THE FINAL JARONA) ----------
// Chapter 5: after SUSIE'S IDEA the party climbs Flowery's tower. Online the battle stays, and the battle's own tower
// (obj_fl_towery, its shaders) climbs during THE FINAL JARONA: it rises and spins faster, its golden leaves fall (its petals);
// the cut brings it back to the battle's slow turn
function kbr_fl_ascent(_on)
{
    with (obj_fl_towery)
    {
        if (_on)
        {
            rise = 2;
            petals = true;
            scr_lerpvar("spin", spin, 3, 40, 2, "inout");
        }
        else if (rise != 0 || petals)
        {
            rise = 0;
            petals = false;
            scr_lerpvar("spin", spin, 1, 40, 2, "inout");
        }
    }
    global.kbr_fl_asc = _on;
    return 1;
}

// ---------- GROUP MERCY (Chapter 5's ACT / MERCY as a shared Battle Royale rule) ----------
// Chapter 5: Flowery's MERCY moves his phases (10 / 20 / 30 / 40 / 50 %); the party raises it with its ACTs - POSEY and
// BLOWAWAY (Flowery alone), SPIN (Aqua & Seth), PRAISE (Orange & Green), JUSTICE (Blue & Yellow), SUSIE'S IDEA (Flowery alone
// again: it ends the battle and the climb begins). Online there is no command menu and there are many SOULs, so the ACT is
// what the ORANGE SOUL does - and it is the whole room's:
//  - each game counts its own player's FLOWERY TP in each of his attacks (Chapter 5's own TP numbers: a blue piece broken
//    3.75 and up, a Jarona struck 12, a fast parry 10 more, a lilypad 7.5, a word flower 10) and tells the host;
//  - the HOST adds a tenth of the AVERAGE of the SOULs standing at that attack's end (at most 8 % an attack): one player
//    cannot carry the boss alone or stall it, a full room is not faster than a small one;
//  - every Chapter 5 threshold is announced for a cycle a little ahead (like the final two): Flowery moves to his next phase
//    in every game on the same cycle (his friends come in or leave, his attacks change). The time ramp moves him on as well,
//    so a room that never parries still meets every phase.
//  - at 60 % (SUSIE'S IDEA done) his next attack is THE FINAL JARONA, with the tower's ascent.
// What each player gets from it stays their own: the TP goes to their gauge (a fifth of Chapter 5's TP, times GRAZE TP).
#macro KBR_FL_STEP 10
#macro KBR_FL_MAXGAIN 8
#macro KBR_FL_FINALE 60

// the group's ACT at GROUP MERCY _g: [name, who]
function kbr_fl_act_of(_g)
{
    if (_g < 10)
        return ["POSEY", "FLOWERY"];
    if (_g < 20)
        return ["BLOWAWAY", "FLOWERY"];
    if (_g < 30)
        return ["SPIN", "AQUA & SETH"];
    if (_g < 40)
        return ["PRAISE", "ORANGE & GREEN"];
    if (_g < 50)
        return ["JUSTICE", "BLUE & YELLOW"];
    if (_g < KBR_FL_FINALE)
        return ["SUSIE'S IDEA", "FLOWERY"];
    return ["THE FINAL ASCENT", "FLOWERY"];
}

// Chapter 5's TP for what the orange SOUL's dash did (self = the piece): this player's gauge, and the attack's count
function kbr_fl_tp(_amt)
{
    if (!is_numeric(_amt) || _amt <= 0)
        return 0;
    // a sent board's pieces are the target's (they count for whoever's game they are in); only while the match runs
    if (!kbr_on())
        return 0;
    var _M = kbr_match();
    if (is_undefined(_M) || _M.out || !_M.me)
        return 0;
    kbr_gauge_add((_amt / 5) * (_M.eff.grz / 100), false);
    global.kbr_fl_tpk = (variable_global_exists("kbr_fl_tpk") ? global.kbr_fl_tpk : 0) + _amt;
    return _amt;
}

// the attack ended (its cut): its TP goes out with the next status message ([cycle, TP], kept until the next attack)
function kbr_fl_mercy_note()
{
    var _M = kbr_match();
    if (is_undefined(_M) || !variable_global_exists("kbr_fl_k") || global.kbr_fl_k < 0)
        return 0;
    var _tp = variable_global_exists("kbr_fl_tpk") ? global.kbr_fl_tpk : 0;
    _M.flm = [global.kbr_fl_k, round(clamp(_tp, 0, 200))];
    global.kbr_fl_tpk = 0;
    return 1;
}

function kbr_fl_fm(_M)
{
    if (!variable_struct_exists(_M, "flm") || !is_array(_M.flm))
        return [-1, 0];
    return _M.flm;
}

// ----- the host -----
function kbr_fl_host_g()
{
    var _h = global.kfo.H;
    if (!is_struct(_h) || !variable_struct_exists(_h, "flg"))
        return 0;
    return _h.flg;
}

// player _p's game told its TP of a Flowery attack ("fm": [cycle, TP]; numbers only, at most 200)
function kbr_fl_host_fm(_p, _m)
{
    var _f = kfo_jv(_m, "fm");
    if (!is_array(_f) || array_length(_f) < 2 || !is_numeric(_f[0]) || !is_numeric(_f[1]) || _f[0] < 0)
        return 0;
    if (!variable_struct_exists(_p, "flm") || !is_struct(_p.flm))
        _p.flm = {};
    variable_struct_set(_p.flm, string(floor(_f[0])), clamp(_f[1], 0, 200));
    return 1;
}

// every frame of the host's match: each Flowery cycle that ended a second and a half ago is counted once
function kbr_fl_host_tick()
{
    var _h = global.kfo.H;
    if (!_h.go || !is_struct(_h.tl))
        return 0;
    if (!variable_struct_exists(_h, "flg"))
    {
        _h.flg = 0;
        _h.fl_next = 0;
    }
    var _now = kfo_host_tick_now();
    var _lu = kbr_enc_by_key("flowery").lu;
    var _n = 0;
    while (_n < 4)
    {
        var _c = kbr_tl_get(_h.tl, _h.fl_next);
        if (_c.t1 + 45 > _now)
            break;
        if (_c.reg == _lu)
            kbr_fl_host_count(_c);
        _h.fl_next++;
        _n++;
    }
    return 1;
}

// the GROUP MERCY of Flowery's cycle _c: the average FLOWERY TP of the SOULs standing at its end
function kbr_fl_host_count(_c)
{
    var _h = global.kfo.H;
    var _key = string(_c.k);
    var _sum = 0;
    var _num = 0;
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        var _p = _h.pl[_i];
        if (!_p.inm)
            continue;
        // standing at the attack's end (out later, or not out at all)
        var _stood = _p.al || (_p.outt >= 0 && _p.outt >= _c.t1);
        if (!_stood)
            continue;
        _num++;
        if (variable_struct_exists(_p, "flm") && is_struct(_p.flm) && variable_struct_exists(_p.flm, _key))
            _sum += variable_struct_get(_p.flm, _key);
    }
    if (_num == 0)
        return 0;
    var _g0 = _h.flg;
    var _gain = clamp((_sum / _num) / 10, 0, KBR_FL_MAXGAIN);
    _h.flg = min(100, _h.flg + _gain);
    // a threshold crossed: its phase from a cycle a little ahead (every game makes that cycle with it)
    for (var _t = KBR_FL_STEP; _t <= KBR_FL_FINALE; _t += KBR_FL_STEP)
    {
        if (_g0 < _t && _h.flg >= _t)
            kbr_fl_host_phase(_t);
    }
    return _gain;
}

// GROUP MERCY threshold _t reached: 10 (POSEY -> BLOWAWAY: only the ACT changes), 20-50 his next phase, 60 the finale
function kbr_fl_host_phase(_t)
{
    var _h = global.kfo.H;
    var _a = kbr_fl_act_of(_t);
    if (_t >= 20)
    {
        // 20 -> phase 2 (Aqua & Seth), 30 -> 3 (Orange & Green), 40 -> 4 (Blue & Yellow), 50 -> 5 (alone), 60 -> the finale
        var _ph = (_t >= KBR_FL_FINALE) ? 6 : (_t div KBR_FL_STEP);
        var _ck = kbr_tl_at(_h.tl, kfo_host_tick_now() + KBR_ARM + 30) + 1;
        if (kbr_tl_set_flph(_h.tl, _ck, _ph))
            kfo_down(0, { k: "flph", mid: _h.mid, ck: _ck, ph: _ph });
    }
    kfo_host_feed("* GROUP MERCY " + string(_t) + "%! " + ((_t >= KBR_FL_FINALE) ? "THE FINAL ASCENT!" : ("ACT: " + _a[0] + " (" + _a[1] + ")")), make_color_rgb(255, 170, 60));
    _h.ds = true;
    return 1;
}

// ----- every game -----
// the host announced phase ph from cycle ck
function kbr_fl_on_flph(_m)
{
    var _M = kfo_match();
    if (!kfo_mid_ok(_m))
        return 0;
    var _ck = kfo_jn(_m, "ck", -1);
    var _ph = kfo_jn(_m, "ph", -1);
    if (_ck < 0 || _ph < 1)
        return 0;
    kbr_fl_apply(_M, _ck, _ph);
    return 1;
}

// an announcement into this game's timeline; a cycle this game already armed or ran cannot change: it resyncs (as for the
// final two)
function kbr_fl_apply(_M, _ck, _ph)
{
    if (!variable_struct_exists(_M, "tl") || !is_struct(_M.tl))
        return 0;
    var _busy = (_M.R.ph == "run" || _M.R.ph == "arm") ? ((_M.R.ph == "run") ? _M.R.k : _M.R.arm_k) : -1;
    if (!kbr_tl_set_flph(_M.tl, _ck, _ph))
        return 0;
    if (_busy >= _ck)
        kfo_resync_local("flph");
    return 1;
}

// the standings (4 a second): the GROUP MERCY, and the announcements (one this game missed is applied now)
function kbr_fl_on_st(_M, _m)
{
    if (variable_struct_exists(_m, "fg") && is_numeric(_m.fg))
        _M.flg = clamp(_m.fg / 10, 0, 100);
    var _l = kfo_ja(_m, "fp");
    for (var _i = 0; _i < array_length(_l) && _i < 12; _i++)
    {
        var _e = _l[_i];
        if (is_array(_e) && array_length(_e) >= 2 && is_numeric(_e[0]) && is_numeric(_e[1]))
            kbr_fl_apply(_M, _e[0], _e[1]);
    }
    return 1;
}

// ----- the HUD: under the boss's name while one of his attacks is on (or armed): the GROUP MERCY bar and the group's ACT -----
function kbr_fl_hud(xx, yy, _M)
{
    var _k = -1;
    if (_M.R.ph == "run" || _M.R.ph == "idle")
        _k = _M.R.k;
    else if (_M.R.ph == "arm")
        _k = _M.R.arm_k;
    if (_k < 0 || !_M.go)
        return 0;
    var _c = kbr_tl_get(_M.tl, _k);
    if (_c.reg != kbr_enc_by_key("flowery").lu)
        return 0;
    var _g = variable_struct_exists(_M, "flg") ? _M.flg : 0;
    var _a = kbr_fl_act_of(_g);
    var _x0 = xx + 262;
    // (DRBR: the top middle's stack - kbr_hud_draw - from its first free line: 38 under the boss's two lines)
    var _y0 = (variable_struct_exists(_M, "hud_ty") ? _M.hud_ty : (yy + 36)) + 2;
    _M.hud_ty = _y0 + 18;
    var _w = 156;
    // the bar: Chapter 5's MERCY yellow, the phase marks every 10 %, the finale's at 60
    draw_set_alpha(0.85);
    draw_set_color(c_black);
    draw_rectangle(_x0 - 1, _y0 - 1, _x0 + _w + 1, _y0 + 6, false);
    draw_set_alpha(1);
    draw_set_color(make_color_rgb(70, 50, 0));
    draw_rectangle(_x0, _y0, _x0 + _w, _y0 + 5, false);
    var _f = clamp(_g / KBR_FL_FINALE, 0, 1);
    draw_set_color(c_yellow);
    if (_f > 0)
        draw_rectangle(_x0, _y0, _x0 + round(_w * _f), _y0 + 5, false);
    draw_set_color(c_black);
    for (var _t = KBR_FL_STEP; _t < KBR_FL_FINALE; _t += KBR_FL_STEP)
    {
        var _tx = _x0 + round((_w * _t) / KBR_FL_FINALE);
        draw_line(_tx, _y0, _tx, _y0 + 5);
    }
    draw_set_font(fnt_small);
    draw_set_halign(fa_center);
    var _txt = "MERCY " + string(floor(min(_g, 100))) + "%  ACT: " + _a[0];
    kbr_hud_text(_x0 + (_w / 2), _y0 + 8, kbr_fit(_txt, 176), (_g >= KBR_FL_FINALE) ? make_color_rgb(255, 170, 60) : c_yellow);
    // the ORANGE SOUL's keys, his first two attacks of the match (the KEY HINTS view setting hides them): Chapter 5's own
    // tutorial line, and where USE SKILL went
    if (_M.me && !_M.out && kfo_view().hints && instance_exists(obj_fl_soul) && (!variable_global_exists("kbr_fl_turns") || global.kbr_fl_turns <= 2))
    {
        var _ck = kfo_key_name(variable_global_exists("input_k") && is_array(global.input_k) && array_length(global.input_k) > 4 ? global.input_k[4] : ord("Z"));
        // (DRBR: under the box, but never over the top stack nor down into the feed and the targeting strip)
        var _hy = instance_exists(obj_growtangle) ? (instance_find(obj_growtangle, 0).bbox_bottom + 8) : (yy + 253);
        _hy = clamp(_hy, yy + 250, yy + 338);
        kbr_hud_text(xx + 320, _hy, kbr_fit("HOLD " + _ck + ": CHARGE - LET GO: DASH. DASH INTO BLUE AND INTO HIS LUNGES!", 600), make_color_rgb(255, 170, 60));
        kbr_hud_text(xx + 320, _hy + 14, kbr_fit("UP / DOWN: MOVE    USE SKILL: " + kfo_key_label("use"), 600), c_ltgray);
    }
    draw_set_halign(fa_left);
    draw_set_color(c_white);
    return 1;
}

// ----- the bots: an ORANGE SOUL of their own needs a board of their own - they play his attacks by the odds -----
// A bot cannot dash through the host's board (its scroll is the host player's own dashes), so while one of his attacks is
// on, each bot meets a hazard every so often (a Jarona's lunge every 70 frames, a piece of the chase every 40) and passes it
// by its PRECISION, MISTAKES and REACTION (a PERFECT bot almost always; a DUMMY almost never): a pass is a break or a parry
// (its FLOWERY TP for the GROUP MERCY), a miss is a hit by the attack's own damage. Its SOUL sits where the orange SOULs
// sit (the box's left, moving up and down). Self: nothing (the host's game). True when it played the bot's frame.
function kbr_fl_bot_tick(_h, _b, _c, _box, _e)
{
    if (!instance_exists(obj_fl_ctrl) || !variable_global_exists("kbr_fl_k") || global.kbr_fl_k < 0)
        return false;
    var _s = _b.bt;
    if (!variable_struct_exists(_s, "flk") || _s.flk != global.kbr_fl_k)
    {
        _s.flk = global.kbr_fl_k;
        _s.flt = 0;
        _s.flw = 20 + irandom(30);
        _s.fly = lerp(_box[1], _box[3], 0.5);
    }
    // where the orange SOULs sit (Chapter 5: 75 px left of the box's middle line... the SOUL's own x)
    var _sx = instance_exists(obj_fl_soul) ? obj_fl_soul.x : (_box[0] + 40);
    _s.x = clamp(_sx, _box[0], _box[2]);
    if (abs(_s.y - _s.fly) < 2 || irandom(60) == 0)
        _s.fly = lerp(_box[1] + 10, _box[3] - 10, random(1));
    _s.y = clamp(lerp(_s.y, _s.fly, 0.12), _box[1], _box[3]);
    if (_s.inv > 0)
        _s.inv--;
    // a player's Flowery send at it: more of his pieces, one every 30 frames (the send's damage, its sender's credit)
    // (one older than 40 seconds withered: no orange board came in time)
    while (variable_struct_exists(_s, "flx") && array_length(_s.flx) > 0 && current_time - _s.flx[0].t > 40000 && _s.flx[0].n == _s.flx[0].n0)
        array_delete(_s.flx, 0, 1);
    if (variable_struct_exists(_s, "flx") && array_length(_s.flx) > 0 && (_s.alive_f mod 30) == 0)
    {
        var _x0 = _s.flx[0];
        _x0.n--;
        if (_x0.n <= 0)
            array_delete(_s.flx, 0, 1);
        var _pass0 = clamp((_c.prec / 100) * (1 - (_c.miss / 100)) * (1 - (_c.react / 90)), 0.02, 0.995);
        if (random(1) < _pass0)
            _s.flt += 3.75;
        else if (_s.inv <= 0)
        {
            var _dmg0 = max(1, round(_x0.d * (_e.skdmg / 100) * (_e.dmul / 100)));
            if (_e.ohko)
                _dmg0 = _b.hp;
            var _tk0 = kfo_bot_take(_b, _dmg0);
            if (_x0.from >= 0)
            {
                _b.lby = _x0.from;
                kfo_host_dealt(_x0.from, _tk0);
            }
            _b.hits++;
            _s.inv = 30;
            if (_b.hp <= 0)
            {
                kfo_host_out_report(_b.pid, round(kfo_host_tick_now()), "out", _x0.from);
                return true;
            }
        }
    }
    _s.flw--;
    if (_s.flw <= 0)
    {
        var _jarona = (instance_exists(obj_fl_flowery) && kbr_fl_is_jarona(obj_fl_flowery.jtype));
        _s.flw = (_jarona ? 70 : 40) + irandom(10);
        var _pass = clamp((_c.prec / 100) * (1 - (_c.miss / 100)) * (1 - (_c.react / 90)), 0.02, 0.995);
        if (random(1) < _pass)
        {
            // a break (3.75) or a parry (12, a fast one 22 - the better the bot, the faster)
            var _tp = _jarona ? ((random(100) < _c.prec) ? 22 : 12) : 3.75;
            _s.flt += _tp;
            _b.g = min(100, _b.g + ((_tp / 5) * (_e.grz / 100)));
        }
        else if (_s.inv <= 0)
        {
            var _t = kbr_hit_dmg(2, false);
            var _dmg = max(1, round(_t[0] * (_e.dmul / 100)));
            if (_e.ohko)
                _dmg = _b.hp;
            kfo_bot_take(_b, _dmg);
            _b.hits++;
            _s.inv = round(_t[1] * (_e.ifr / 100));
            if (_b.hp <= 0)
                kfo_host_out_report(_b.pid, round(kfo_host_tick_now()), "out", -1);
        }
    }
    // its TP of this attack, as a player's game would tell it
    if (!variable_struct_exists(_b, "flm") || !is_struct(_b.flm))
        _b.flm = {};
    variable_struct_set(_b.flm, string(_s.flk), round(_s.flt));
    return true;
}

// ---------- a piece's own decisions (make_flowery.py rewrites the Jarona's and Seth's book's random calls to these) ----------
// The Jarona's waits between lunges, its tag-ins with Orange, its fake-outs and its bullet patterns, Seth's book's first word:
// drawn from the piece's own stream, seeded by the cycle (the same in every game) and the order the piece was made in, so a
// Jarona makes the same choices in every game that played it the same way. A sent piece draws from its send's stream.
function kbr_fl_pg()
{
    if (variable_instance_exists(id, "kbrg") && is_struct(kbrg))
        return kbrg;
    if (!variable_instance_exists(id, "kbrpg"))
    {
        global.kbr_fl_pn = (variable_global_exists("kbr_fl_pn") ? global.kbr_fl_pn : 0) + 1;
        kbrpg = kbr_rng(kbr_mix(variable_global_exists("kbr_fl_pseed") ? global.kbr_fl_pseed : 1, 7919 + global.kbr_fl_pn));
    }
    return kbrpg;
}

function kbr_fl_p_random(_n)
{
    return kbr_rng_unit(kbr_fl_pg()) * _n;
}

function kbr_fl_p_irandom(_n)
{
    return kbr_rng_int(kbr_fl_pg(), floor(_n) + 1);
}

function kbr_fl_p_random_range(_a, _b)
{
    return _a + (kbr_rng_unit(kbr_fl_pg()) * (_b - _a));
}

function kbr_fl_p_irandom_range(_a, _b)
{
    var _lo = floor(min(_a, _b));
    var _hi = floor(max(_a, _b));
    return _lo + kbr_rng_int(kbr_fl_pg(), (_hi - _lo) + 1);
}

function kbr_fl_p_choose()
{
    return argument[kbr_rng_int(kbr_fl_pg(), argument_count)];
}

// a sent Jarona's lunges (kbrjl, made by its send): true while it may lunge again; at 0 it fades out and goes (self = it)
function kbr_fl_jr_more()
{
    if (!variable_instance_exists(id, "kbrjl"))
        return true;
    if (kbrjl > 0)
    {
        kbrjl--;
        return true;
    }
    if (!variable_instance_exists(id, "kbrjgo"))
    {
        kbrjgo = 1;
        scr_lerpvar("image_alpha", image_alpha, 0, 14);
        scr_doom(id, 15);
        if (orange_dopple != -4 && instance_exists(orange_dopple))
        {
            with (orange_dopple)
            {
                scr_lerpvar("image_alpha", image_alpha, 0, 14);
                scr_doom(id, 15);
            }
        }
    }
    return false;
}

// ---------- FLOWERY'S SENDS (skills 38-44): his Chapter 5 pieces on the target's own orange board ----------
// A Flowery send lands while one of his attacks runs in the target's game (its orange SOUL and board are up) with at least
// four seconds of it left; until then it WAITS (the INCOMING list says so) for his next attack - forty seconds at most, then
// it withers (no orange board came). Every piece is Chapter 5's own object, made the way his board's controller makes it
// (Chapter 5's numbers), scrolled by the target's board, broken or parried by the target's dash, and tagged as the send's: the
// sender's colour, the send's damage, its own random stream (the board's course stays the room's). The board's end ends
// them (a send never outlives the attack it landed in).
//  38 JARONA          a Jarona copy runs in from the board's right edge: 3 lunges (Chapter 5's JARONA!, speed 20), then it goes
//  39 BAMBOO RUSH     Chapter 5's unused bamboo pattern (its difficulty 11): 4 stalks, 2 pairs, a triple - 240 tall with a
//                     160-px blue joint that throws petals when broken
//  40 AQUA'S KNIVES   Aqua's lilypads (difficulty 10): 4 pads, between two pads two columns of 5 knife chains (jump over them)
//  41 SETH'S BOOKS    Seth's books (attack type 3): two books streaming his words across the board, his word flower between
//  42 ORANGE & GREEN  the tag team (JUST KIDDING!): a Jarona with Orange beside it, Green's shrug for the fake-outs; 4 lunges
//                     at 26
//  43 BLUE & YELLOW   Blue's flower bombs (difficulty 6): 2 blooms - Yellow's reticle, her beam, Blue's butterflies - with
//                     blue vases between
//  44 LAST JARONA     the Omega fight's LAST JARONA, as the box battle can have it: his "Last Jarona!", an 80-frame rainbow
//                     charge, then 4 rushes at 24 (Chapter 5's numbers) - not THE FINAL JARONA (his multi-copy finale) nor
//                     the party's PRISM RUSH
function kbr_fl_is_send(_sid)
{
    return _sid >= 38 && _sid <= 44;
}

// the target's board: its controller (the attack's own, not a send's), or noone
function kbr_fl_main()
{
    var _r = noone;
    with (obj_fl_ctrl)
    {
        if (_r == noone && !(variable_instance_exists(id, "kbrx") && kbrx > 0))
            _r = id;
    }
    return _r;
}

// a Flowery send can land now: his board is up in this game, and 4 seconds (120 frames) of the attack are left
function kbr_fl_sa_ready()
{
    if (!instance_exists(obj_fl_soul) || kbr_fl_main() == noone)
        return false;
    var _M = kbr_match();
    if (is_undefined(_M) || _M.R.ph != "run")
        return false;
    var _c = kbr_tl_get(_M.tl, _M.R.k);
    // (THE FINAL JARONA's gauntlet moves every Jarona on the board: his own finale stays his)
    if (instance_exists(obj_fl_flowery) && obj_fl_flowery.jtype == 639)
        return false;
    return (_c.t1 - kbr_now()) >= 120;
}

// one piece of the send (made inside it: its Create adopts it)
function kbr_fl_sa_mk(_G, _x, _y, _obj)
{
    var _i = kbr_sa_mk(_G, _x, _y, _obj);
    if (instance_exists(_i))
        _i.orangeheartControlled = true;
    return _i;
}

// the send's distance clock: Chapter 5's board counts its spawns by how far it scrolled (abs(speed) / 16 a frame), so the
// pieces come as fast as the target dashes, as the board's own do
function kbr_fl_sa_d(_G, _C)
{
    if (!variable_struct_exists(_G, "d"))
        _G.d = 0;
    if (!_C.hitstop)
        _G.d += abs((_C.fakecamxspeedbase + _C.fakecamxspeedadditional) / 16);
    return _G.d;
}

// one Jarona copy of the send: from the board's right edge to its place, then mode 0 (Chapter 5's lunges); _n lunges
function kbr_fl_sa_jarona(_G, _C, _spd, _n, _orange)
{
    var _y = ((_C.boxbot + _C.boxtop) / 2) - 59;
    var _j = kbr_fl_sa_mk(_G, camerax() + 700, _y, obj_fl_jarona);
    with (_j)
    {
        x = camerax() + 700;
        y = _y;
        remx = x;
        remy = y;
        sprite_index = spr_fl_flowery_idle3;
        image_speed = 1/6;
        visible = true;
        mode = 0;
        difficulty = 0;
        attack_speed = _spd;
        do_bullets = false;
        kbrjl = _n;
        waittime = 34;
        scr_lerpvar("x", x, camerax() + 560, 20, 1, "out");
        if (_orange)
        {
            orange_dopple = kbr_fl_sa_mk(_G, x + 30, y + 110, obj_fl_mfancy);
            with (orange_dopple)
            {
                depth = other.depth;
                sprite_index = spr_fl_orange_animepunch_finished_cent;
                image_speed = 1/3;
                scr_darksize();
            }
            can_kidding = true;
        }
    }
    return _j;
}

function kbr_fl_sa_step(_G, _t)
{
    var _C = kbr_fl_main();
    // no board (the attack was cut, the SOUL is not orange): the send is over
    if (_C == noone || !instance_exists(obj_fl_soul))
    {
        _G.dead = true;
        return 0;
    }
    var _ss = camerax() + 680;
    var _mid = scr_get_box(5);
    // the board's course draws stay the board's: the send's pieces draw from the send's stream
    var _keep = global.kbr_fl_gen;
    global.kbr_fl_gen = _G.rg;
    switch (_G.sid)
    {
        case 38:
            if (_t == 0)
            {
                kbr_fl_sa_jarona(_G, _C, 20, 3, false);
                kbr_sa_sfx(snd_jump, 1.2);
            }
            _G.end_t = 330;
            break;
        case 39:
            // Chapter 5's difficulty 11, its timing by the board's distance (timer_goal 16, one less each stalk)
            var _d = kbr_fl_sa_d(_G, _C);
            if (!variable_struct_exists(_G, "wc"))
            {
                _G.wc = 0;
                _G.goal = 16;
            }
            if (_d > _G.goal && _G.wc < 7)
            {
                var _x0 = _ss - ((_d - _G.goal) * 16);
                var _gap = 120 + (sin(global.kbr_fl_t * 0.1) * 40);
                var _n = (_G.wc < 4) ? 1 : ((_G.wc < 6) ? 2 : 3);
                kbr_sa_in(_G);
                for (var _i = 0; _i < _n; _i++)
                {
                    with (_C)
                        wall_create(_x0 + (_i * 80), _mid, 16, 240, _gap, 160, true);
                }
                kbr_sa_out();
                if (_G.wc == 6)
                {
                    _G.goal = 10;
                    _G.d -= 60;
                }
                else if (_G.wc < 6)
                    _G.goal--;
                _G.wc++;
                _G.d -= _G.goal;
                if (_n > 0)
                    kbr_sa_sfx(snd_wing, 1.1);
            }
            _G.end_t = 320;
            break;
        case 40:
            // Aqua's difficulty 10: a lilypad every 28 of the board's distance, two knife columns between pads
            var _d2 = kbr_fl_sa_d(_G, _C);
            if (!variable_struct_exists(_G, "wc"))
            {
                _G.wc = 0;
                _G.lp = _mid;
            }
            if (_d2 > 28 && _G.wc < 4)
            {
                var _px = _ss - ((_d2 - 28) * 16);
                var _pad;
                if (_G.wc == 0)
                    _pad = kbr_fl_sa_mk(_G, _px, _mid, obj_fl_pad);
                else
                {
                    _pad = kbr_fl_sa_mk(_G, _px, _G.lp + ((30 + kbr_fl_irandom(10)) * kbr_fl_choose(-1, 1)), obj_fl_pad);
                    with (_pad)
                    {
                        vspeed = kbr_fl_choose(-1, 1);
                        if (y > (_mid + 60))
                            vspeed = -1;
                        if (y < (_mid - 60))
                            vspeed = 1;
                    }
                }
                _G.lp = clamp(_pad.y, _mid - 40, _mid + 40);
                if (_G.wc > 0)
                {
                    for (var _col = 0; _col < 2; _col++)
                    {
                        for (var _a = 0; _a < 5; _a++)
                        {
                            var _kx = (_px + (28 * 8) + ((_col == 0) ? 30 : -30));
                            var _ky = (_mid - 187.5) + (75 * _a) + ((_col == 0) ? 0 : 37.5);
                            var _kn = kbr_fl_sa_mk(_G, _kx, _ky, obj_fl_bullet);
                            with (_kn)
                            {
                                graze = 0;
                                vspeed = ((_G.wc mod 2) == 0) ? 5 : -5;
                                sprite_index = spr_fl_attack_knifechain;
                                image_angle = sign(-vspeed) * 90;
                                image_speed = 1;
                                scr_darksize();
                                drawprevious = false;
                                kbrmid = _mid;
                                scr_script_repeat(function()
                                {
                                    if (y <= (kbrmid - 150) || y >= (kbrmid + 150))
                                        image_alpha = scr_approach(image_alpha, 0, 0.15);
                                    else
                                        image_alpha = scr_approach(image_alpha, 1, 0.15);
                                    if (y < (kbrmid - 187.5))
                                        y += 375;
                                    if (y > (kbrmid + 187.5))
                                        y -= 375;
                                }, 999, 1);
                            }
                        }
                    }
                }
                _G.wc++;
                _G.d -= 28;
                kbr_sa_sfx(snd_splash, 1);
            }
            _G.end_t = 300;
            break;
        case 41:
            // Seth's books (attack type 3's word streams, without his boxes: they belong to his own course)
            if (_t == 0 || _t == 70)
            {
                var _bx = camerax() + 700 + ((_t == 0) ? 0 : 60);
                var _dir = kbr_fl_choose(1, -1);
                var _bk = kbr_fl_sa_mk(_G, _bx, 0, obj_fl_book);
                with (_bk)
                {
                    timer_goal = 22;
                    b_speed = 6;
                    timer = kbr_fl_irandom(timer_goal - 1);
                    dir = _dir;
                    y = (cameray() + (cameraheight() * 0.5)) - (((cameraheight() * 0.5) + 30) * dir);
                    image_angle = (dir > 0) ? -90 : 90;
                    kbr_sa_in(_G);
                    init();
                    kbr_sa_out();
                }
                if (_t == 0)
                {
                    var _wf = kbr_fl_sa_mk(_G, _bx + 150, _mid + kbr_fl_irandom_range(-50, 50), obj_fl_wordflower);
                    _wf.depth = _C.depth - 100;
                }
                kbr_sa_sfx(snd_paper_rise, 1.2);
            }
            _G.end_t = 300;
            break;
        case 42:
            if (_t == 0)
            {
                kbr_fl_sa_jarona(_G, _C, 26, 4, true);
                kbr_sa_sfx(snd_jump, 1);
            }
            _G.end_t = 380;
            break;
        case 43:
            // Blue's flower bombs (difficulty 6): a bloom every 5 of the board's spawns, vases between
            var _d3 = kbr_fl_sa_d(_G, _C);
            if (!variable_struct_exists(_G, "wc"))
                _G.wc = 0;
            if (_d3 >= 5 && _G.wc < 10)
            {
                var _bx3 = _ss - ((_d3 - 6) * 16);
                var _by = _mid + (sin(global.kbr_fl_t * 0.96 * 4) * 40) + (cos(global.kbr_fl_t * 0.14 * 4) * 40);
                if ((_G.wc mod 5) == 0)
                    kbr_fl_sa_bloom(_G, _bx3, _by);
                kbr_sa_in(_G);
                with (_C)
                {
                    with (wall_create(_bx3, _mid + (sin(global.kbr_fl_t * 0.25) * 50) + (cos(global.kbr_fl_t * 0.015) * 40), 16, 100, 100, 100))
                    {
                        tensionvalue = 1;
                        vase = true;
                    }
                }
                kbr_sa_out();
                _G.wc++;
                _G.d = ((_G.wc mod 4) == 0) ? -20 : 0;
            }
            _G.end_t = 330;
            break;
        case 44:
            kbr_fl_sa_last(_G, _C, _t);
            break;
    }
    global.kbr_fl_gen = _keep;
    return 1;
}

// Blue's flower (Chapter 5's difficulty-6 bloom, its own code): it spins in, slows, Yellow's reticle and three bomb-fall
// beeps, then her beam from the board's right and Blue's butterflies spiralling out
function kbr_fl_sa_bloom(_G, _x, _y)
{
    var _b = kbr_fl_sa_mk(_G, _x, _y, obj_fl_bloom);
    with (_b)
    {
        bomb_timer = 0;
        scr_darksize();
        image_blend = merge_color(c_aqua, c_blue, 0.5);
        direction = 180;
        speed = 12;
        scr_lerpvar("speed", 12, 0.5, 30, 1, "out");
        trigger = false;
        scr_script_repeat(function()
        {
            image_angle += 4;
            if (trigger)
                bomb_timer++;
            if (speed == 0.5 && !trigger)
            {
                trigger = true;
                reticle = true;
                kbr_snd_play(snd_bombfall);
                scr_script_delayed(kbr_snd_play, 2, snd_bombfall);
                scr_script_delayed(kbr_snd_play, 4, snd_bombfall);
            }
            if (bomb_timer == 16)
            {
                kbr_snd_play(snd_bomb);
                kbr_snd_play(snd_magicsprinkle, 0.5);
                with (instance_create_depth(x, y, depth - 100, obj_fl_beam))
                    setup(camerax() + 680, scr_get_box(5), x, y, 12, 0, 48, 8, 8);
                timer = 0;
                dir = kbr_fl_p_choose(1, -1);
                randir = kbr_fl_p_irandom(360);
                visible = false;
                scr_script_repeat(function()
                {
                    for (var a = 0; a < 2; a++)
                    {
                        with (instance_create(x, y, obj_fl_bullet))
                        {
                            timer = 0;
                            depth -= 100;
                            speed = 10 + kbr_fl_p_irandom(6);
                            scr_lerpvar("speed", speed, 3, 20);
                            mydir = other.dir;
                            x_accel = 16;
                            sprite_index = spr_fl_enemy_blue_bullet_butterfly;
                            image_speed = 0.5;
                            image_xscale = 1.8;
                            image_yscale = 1.8;
                            direction = (other.timer * 45) + other.randir + (a * 180);
                            other.timer++;
                            image_angle = 0;
                            scr_script_repeat(function()
                            {
                                timer++;
                                x += x_accel;
                                x_accel -= 0.375;
                                direction += (mydir * 2);
                                if (timer >= 120)
                                    instance_destroy();
                            }, 160, 1);
                        }
                    }
                    if (timer >= 8)
                        instance_destroy();
                }, 20, 1);
            }
        }, 600, 1);
    }
    return _b;
}

// LAST JARONA (the Omega fight's, as a box attack): t 0 his voice and the charge (80 frames, rainbow afterimages - Chapter 5's
// make_bwoosh colours), then a Jarona copy rushes four times at 24, tinted round the rainbow
function kbr_fl_sa_last(_G, _C, _t)
{
    if (_t == 0)
    {
        kbr_fl_voice(snd_flowery_voiceclip_last_jarona, KBR_SENT_GAIN, 1);
        var _T = kbr_sa_tel(_G, "rainbow", camerax() + 560, ((_C.boxbot + _C.boxtop) / 2) - 59, 80, 0);
        _T.spr = spr_fl_flowery_idle3;
        _T.xs = 2;
    }
    if (_t == 80)
    {
        var _j = kbr_fl_sa_jarona(_G, _C, 24, 4, false);
        with (_j)
        {
            x = camerax() + 560;
            waittime = 6;
            attack_speed_limit = 36;
            kbrrb = 1;
        }
        kbr_sa_sfx(snd_great_shine, 1);
    }
    // the copy's colour goes round the rainbow (Chapter 5: make_color_hsv by time)
    with (obj_fl_jarona)
    {
        if (variable_instance_exists(id, "kbrrb") && variable_instance_exists(id, "kbrx") && kbrx == _G.gx)
            image_blend = make_color_hsv((current_time / 6) mod 255, 160, 255);
    }
    _G.end_t = 400;
    return 1;
}

// a player's Flowery send at a bot (the host's game): its pieces become more hazards in the bot's next Flowery attack (a
// JARONA 3, BAMBOO RUSH 8, AQUA'S KNIVES 6, SETH'S BOOKS 5, ORANGE & GREEN 4, BLUE & YELLOW 6, LAST JARONA 4) - 40 seconds to
// wait for one, as a player's
function kbr_fl_bot_send(_s, _d)
{
    if (!kfo_is_host() || !is_struct(global.kfo.H) || !variable_struct_exists(_s, "tg"))
        return 0;
    var _b = kfo_host_player(_s.tg);
    if (is_undefined(_b) || !_b.bot || !is_struct(_b.bt))
        return 0;
    var _tab = [3, 8, 6, 5, 4, 6, 4];
    var _n = _tab[clamp(_s.sid - 38, 0, 6)];
    if (!variable_struct_exists(_b.bt, "flx"))
        _b.bt.flx = [];
    array_push(_b.bt.flx, { n: _n, n0: _n, d: _d * (variable_struct_exists(_s, "mul") ? _s.mul : 1), from: variable_struct_exists(_s, "from") ? _s.from : -1, t: current_time });
    return 1;
}

// ---------- the orange SOUL for the others: what this player's position message adds, and a watcher's puppet ----------
// [dashing 0/1, the board's dash speed in tenths] (0, 0 off Flowery's board)
function kbr_fl_pos_extra()
{
    if (!instance_exists(obj_fl_soul))
        return [0, 0];
    var _C = kbr_fl_main();
    var _fa = (_C != noone) ? round(_C.fakecamxspeedadditional * 10) : 0;
    return [obj_fl_soul.dashing ? 1 : 0, _fa];
}

// the game's own input, as the orange SOUL reads it (make_flowery.py rewrites its button1_h / up_h / down_h): nothing while this
// game only watches (OUT, or a watcher) - its orange SOUL is then the followed player's puppet
function kbr_fl_watching()
{
    var _M = kbr_match();
    return !is_undefined(_M) && kbr_on() && (_M.out || !_M.me);
}

function kbr_fl_in_b1()
{
    return kbr_soul_keys_off() ? 0 : button1_h();
}

function kbr_fl_in_up()
{
    return kbr_soul_keys_off() ? 0 : up_h();
}

function kbr_fl_in_dn()
{
    return kbr_soul_keys_off() ? 0 : down_h();
}

// a watcher's orange SOUL on the followed one's height, with their dash and their board's dash speed (_q: their stream)
function kbr_fl_puppet(_q, _ty)
{
    if (!instance_exists(obj_fl_soul))
        return 0;
    var _fd = variable_struct_exists(_q, "fd") ? _q.fd : 0;
    var _fa = variable_struct_exists(_q, "ffa") ? _q.ffa : 0;
    with (obj_fl_soul)
    {
        y = _ty - 10;
        if (_fd && !dashing)
        {
            dashing = 1;
            dashstate = 2;
        }
        else if (!_fd && dashing)
        {
            dashing = 0;
            dashstate = 0;
        }
    }
    var _C = kbr_fl_main();
    if (_C != noone)
        _C.fakecamxspeedadditional = _fa;
    return 1;
}
