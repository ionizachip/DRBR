// ===== DRBR: GERSON - THE HAMMER OF JUSTICE (DELTARUNE Chapter 4's secret boss, encounter 160) =====
// Online only. His pieces are Chapter 4's own objects (make_gerson.py: obj_hj_*, from the player's Chapter 4 data.win); this
// file is his battle object (obj_hj_gerson: the knights' arm / hold / attack handshake), his shot list runner (Chapter 4's
// obj_hammer_of_justice_enemy Step), his look, lines, background and clean-up.
// THE GREEN SOUL: Chapter 4's green attacks make their own shield (obj_hj_shield: special 36, or special 1 - Gerson's swing and
// the chevron); while it is up, obj_heart is pulled to the box's middle and the arrows turn the shield (kbr_hj_heart_lock, the
// hook Chapter 4's obj_heart has and Chapter 3's has not). Spears fly at the LOCAL shield (every game the same spears at the
// same times; a block or a hit is that game's own). A red hammer breaks the shield: the SOUL is red for the rest of the attack.
// Source survey: online/notes/src_gerson.md.

function kbr_enc_def_gerson()
{
    // [phase, id, name, flags]; pat: Chapter 4's pattern number (kbr_hj_build); tt: the attack's length in frames - where
    // Chapter 4 itself ends the turn (its pieces' end writes, noted by kbr_hj_done, measured in the emulator: t_gerson53.py)
    // plus 15-28 frames; the finale ("Final Rounds") is the Roaring's place
    return { key: "gerson", cat: "secret", fid: KBR_FAM_GERSON, chapter: 4, soul: "green", sends: [32, 33, 34, 35, 36, 37], song: "HAMMER OF JUSTICE - Toby Fox",
        desc: "Chapter 4's secret boss. A green SOUL:#turn your shield and BLOCK the spears!",
        name: "Gerson", short: "GERSON", title: "HAMMER OF JUSTICE", col: make_color_rgb(120, 220, 140), lu: KBR_ENC_BASE + 1,
        music: "ch4_extra_boss.ogg", obj: "obj_hj_gerson", spr: "spr_hj_gerson_idle", px: 460, py: 161, roar: 18, roar_dur: 610,
        atk: [[1, 0, "Green Switch", 0], [1, 1, "Spear Lesson", 0], [1, 2, "Crossfire", 0], [1, 3, "Diagonals", 0], [1, 4, "Red Hammer", 0],
              [2, 5, "Shell Kick", 0], [2, 6, "Hammer Toss", 0], [2, 7, "Diagonal Barrage", 0], [2, 8, "Shell Bounce", 0], [2, 9, "Shell Storm", 0],
              [2, 10, "Hammer Swings", 0], [2, 11, "Box Squish", 0],
              [3, 12, "Double Bounce", 0], [3, 13, "Shell Gauntlet", 0], [3, 14, "Spiral", 0], [3, 15, "Random Rush", 0], [3, 16, "Slow Flood", 0],
              [3, 17, "Shell Medley", 0], [4, 18, "Final Rounds", 2]],
        pat: [0, 1, 2, 3, 4, 72, 70, 6, 7, 12, 9, 47, 13, 14, 53, 55, 56, 220, 19],
        tt: [250, 250, 250, 270, 310, 370, 430, 280, 330, 390, 330, 410, 430, 430, 320, 430, 530, 380, 610],
        line: ["As long as you're GREEN,&you can't run away!", "You gotta BLOCK, you&understand?!", "Did you ever hear&that old tale?",
               "Yes, the old tale,&based upon the&prophecy...", "Unless you FACE DANGER&HEAD ON... These bullets&will do you in!", "Put some shell into&it, will ya?", "Lord of the Hammer.",
               "Chapter 1&The March of&the Dark King.", "...What happens next?", "Geheheh! Who knows?", "It all stopped.",
               "That next book, it&never did get written.", "But you, my dear?&I see a story lit&up in your eyes...", "Burnin' bright...&Burnin' black.&Burnin' up&everything.",
               "So... how do you &think it all ends?", "You choose eternity.", "And soon, an ocean&of ink shall wash&across the pages.",
               "There's no prophecy&or legend 'bout anyone&like that.", "The bell's ringin' now.&Seems we've reached&the final rounds."],
        again: ["Now, where's my&haircut? Geh ha ha!", "You aren't givin' up&now, are ya?", "Put some shell into&it, will ya?",
                "If you've got guts,&c'mon and let your&axe do the talking!"],
        flavor: ["* The air crackles green with freedom.", "* The bells ring in justice...", "* The bell of justice is ringing... it's for you.",
                 "* The white wind howls!", "* Smells like steel and leather.", "* It's one shell of a battle!"],
        objs: [obj_hj_spear, obj_hj_shield, obj_hj_shieldpiece, obj_hj_justpart, obj_hj_shellpop, obj_hj_notepart, obj_hj_switch, obj_hj_chevron,
               obj_hj_fakeheart, obj_hj_teleport, obj_hj_afterimage, obj_hj_column, obj_hj_swing2, obj_hj_squish, obj_hj_boxthrow, obj_hj_shellkick,
               obj_hj_boxshrink, obj_hj_jumparc, obj_hj_shakey, obj_hj_bell, obj_hj_bellhit, obj_hj_shakedir, obj_hj_bellctrl, obj_hj_mfancy],
        // his pieces that read the box (a send's go when the box does, between two attacks; the shield and the spears read the
        // SOUL only - a SPEAR VOLLEY goes on across the gap)
        boxy: [obj_hj_hammer, obj_hj_pinball, obj_hj_swinghit, obj_hj_swing, obj_hj_swing2, obj_hj_bellctrl, obj_hj_teleport, obj_hj_fakeheart, obj_hj_column],
        cut: kbr_hj_cut };
}

// a read of Gerson's battle object by one of his pieces: his value, or - while he is not on stage (a send made during a
// knight's attack) - what it would be with him standing at his place
function kbr_hj_gv(_f)
{
    var _g = instance_find(obj_hj_gerson, 0);
    if (_g != noone)
        return variable_instance_exists(_g, _f) ? variable_instance_get(_g, _f) : 0;
    switch (_f)
    {
        case "x":
        case "xstart":
            return camerax() + 460;
        case "y":
        case "ystart":
            return cameray() + 161;
        case "visible":
            return false;
        case "depth":
            return 0;
    }
    return 0;
}

// Chapter 4's obj_heart lock (its Step, after the arrows are read): while the green shield is up the SOUL is green, does not
// move and is pulled to the box's middle (the arrows turn the shield instead)
function kbr_hj_heart_lock()
{
    if (!instance_exists(obj_hj_shield))
        return 0;
    // (the shield that is up: a SPEAR VOLLEY send's may be fading out beside his own)
    var _s = noone;
    with (obj_hj_shield)
    {
        if (vanish == 0 && _s == noone)
            _s = id;
    }
    if (_s == noone || !variable_instance_exists(id, "color") || color == 0)
        return 0;
    sprite_index = spr_hj_greenheart;
    press_l = 0;
    press_r = 0;
    press_d = 0;
    press_u = 0;
    if (_s.forceheartpos && instance_exists(obj_growtangle))
    {
        if (x != (obj_growtangle.x - 10))
            x = lerp(x, obj_growtangle.x - 10, 0.2);
        if (y != (obj_growtangle.y - 10))
            y = lerp(y, obj_growtangle.y - 10, 0.2);
    }
    return 1;
}

// ---------- his battle object (obj_hj_gerson) ----------
function kbr_hj_create()
{
    image_xscale = 2;
    image_yscale = 2;
    image_speed = 0;
    visible = true;
    myself = 0;
    state = 0;
    siner = 0;
    fsiner = 0;
    flash = 0;
    shakex = 0;
    hurtspriteoffx = 0;
    hurtspriteoffy = 0;
    idlesprite = spr_hj_gerson_idle;
    hurtsprite = spr_hj_gerson_idle;
    sparedsprite = spr_hj_gerson_idle;
    thissprite = idlesprite;
    sprite_index = idlesprite;
    hairindex = 0;
    movesiner = 0;
    laughtimer = 0;
    attacked = 1;
    talked = 1;
    acting = 0;
    rtimer = 0;
    attackchosen = false;
    // what Chapter 4's pieces read and write on him (obj_hammer_of_justice_enemy's Create)
    attackpattern = 0;
    trueturn = 0;
    turn = 0;
    difficulty = 0;
    attackcon = 0;
    attacktimer = 0;
    attackcount = 0;
    attackcountmax = 0;
    reachedendphase = 0;
    have_used_final_attack = false;
    swingdown_ex = 0;
    swingdown_multitelegraph = 0;
    diagonal_enabled = 0;
    transformsfx = 0;
    fasterheart = false;
    goldcon = 0;
    goldalpha = 0;
    squishbox = false;
    boxoffset = false;
    introtalkcon = -1;
    rudebusterhitcount = 0;
    hitbox_con = 0;
    endcon = 0;
    kbr_hj_pat_reset();
    say = "";
    say_t = 0;
    said = [];
    if (!instance_exists(obj_hj_bg))
        instance_create_depth(0, 0, 49000, obj_hj_bg);
    return 1;
}

function kbr_hj_on()
{
    return kbr_enc_is("gerson");
}

function kbr_hj_step()
{
    if (!kbr_on())
        exit;
    if (say_t > 0)
        say_t--;
    // the knights' handshake: the box at 1.5, the count held at 11 by the shared clock (kbr_rgate), the attack at 12
    if (global.mnfight == 1.5)
    {
        if (!instance_exists(obj_growtangle))
            instance_create(camerax() + 320, cameray() + 170, obj_growtangle);
        if (!instance_exists(obj_moveheart) && !instance_exists(obj_heart))
            scr_moveheart();
        global.mnfight = 2;
        scr_turntimer(90);
    }
    if (global.mnfight == 2 && attacked == 0)
    {
        rtimer += kbr_rgate();
        if (rtimer == 12)
        {
            kbr_hj_attack();
            attacked = 1;
        }
    }
    // the shot list (Chapter 4's runner: one entry, then its wait; the conversation waits and the turn-timer end are not here)
    if (attackcon == 1)
    {
        if (attackcount < attackcountmax)
        {
            kbr_hj_shot(list_attackdirection[attackcount], list_attackspeed[attackcount], list_attackframes[attackcount], list_attackspecial[attackcount], list_attackspecial2[attackcount]);
            attackcon = 2;
        }
        else
        {
            attackcon = 3;
            swingdown_ex = 0;
        }
        attackcount++;
    }
    if (attackcon == 2)
    {
        attacktimer++;
        if (attacktimer >= list_attackwait[attackcount - 1])
        {
            attacktimer = 0;
            attackcon = 1;
            if (reachedendphase == 1)
                have_used_final_attack = true;
        }
    }
    // Chapter 4 ends the turn 10 frames after the list when no spear is left - a note now (kbr_hj_done)
    if (attackcon == 3 && !instance_exists(obj_hj_spear))
    {
        kbr_hj_done(10);
        attackcon = 0;
    }
    if (attacked == 1 && variable_global_exists("kbr_hj_f"))
        global.kbr_hj_f++;
    // the squished box (Chapter 4's Step_2): the SOUL stays inside the flat box
    if (squishbox && instance_exists(obj_heart) && instance_exists(obj_growtangle))
    {
        with (obj_heart)
            y = clamp(y, obj_growtangle.y - (obj_growtangle.sprite_height / 2) + 4, (obj_growtangle.y + (obj_growtangle.sprite_height / 2)) - 24);
    }
    return 1;
}

// the attack of the cycle (self = obj_hj_gerson; on the frame the shared clock releases it - kbr_rgate seeded the stream)
function kbr_hj_attack()
{
    var _d = kbr_enc_by_key("gerson");
    var _ai = clamp(global.knight_lu.plan_i, 0, array_length(_d.pat) - 1);
    var _p = _d.pat[_ai];
    global.turntimer = _d.tt[_ai];
    global.monsterattackname[0] = _d.atk[_ai][2];
    // the box and the SOUL as they are now: put back at the attack's end (the box throw turns it, the squish flattens it)
    if (instance_exists(obj_growtangle))
    {
        var _b = instance_find(obj_growtangle, 0);
        global.kbr_hj_box = { x: _b.x, y: _b.y, xs: _b.image_xscale, ys: _b.image_yscale, a: _b.image_angle };
    }
    global.kbr_hj_dirty = true;
    // Chapter 4: the shield is diagonal from the 4th turn on (special 3 switches it on, every later shield starts diagonal)
    diagonal_enabled = (_p != 0 && _p != 1 && _p != 2) ? 1 : 0;
    transformsfx = 0;
    reachedendphase = 0;
    have_used_final_attack = false;
    swingdown_multitelegraph = 0;
    squishbox = false;
    goldcon = 0;
    visible = true;
    state = 0;
    trueturn++;
    turn++;
    global.kbr_hj_turns = (variable_global_exists("kbr_hj_turns") ? global.kbr_hj_turns : 0) + 1;
    global.kbr_hj_f = 0;
    global.kbr_hj_end = -1;
    kbr_hj_build(_p);
    attackcon = 1;
    attacktimer = 0;
    kbr_hj_say(_d, _ai);
    return 1;
}

// where Chapter 4 would have ended the turn (its pieces' end writes, kept as notes): _n frames from now. Nothing ends by it -
// the shared timeline's cut ends every attack at its length - the tests measure each attack's real length by it.
function kbr_hj_done(_n)
{
    if (!variable_global_exists("kbr_hj_f"))
        return 0;
    var _t = global.kbr_hj_f + _n;
    if (global.kbr_hj_end < 0 || _t < global.kbr_hj_end)
        global.kbr_hj_end = _t;
    return 1;
}

// his line for attack _ai: its own the first time in this match, then one of his repeats
function kbr_hj_say(_d, _ai)
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
        say = _d.line[_ai];
    }
    else
        say = _d.again[kbr_irandom(array_length(_d.again) - 1)];
    say_t = 90;
    return 1;
}

// Chapter 4's body drawing (obj_hammer_of_justice_enemy's Draw: the sway, the hair over the shoulders, the laugh) and his balloon
function kbr_hj_draw()
{
    if (state == 0)
        movesiner += (1/3);
    x = xstart + (sin(movesiner / 5) * 10);
    if (state == 0)
    {
        var _hx = 18;
        // (GameMaker's compiler cannot index an array literal directly)
        var _hys = [5, 4, 3, 4, 5, 6, 7, 5, 4, 3, 3, 4, 6, 7, 5];
        var _hy = _hys[clamp(floor(siner) mod 15, 0, 14)];
        draw_sprite_ext(spr_hj_gerson_hair, hairindex, x + (_hx * 2), y + (_hy * 2), 2, 2, image_angle, image_blend, image_alpha);
        hairindex += 0.2;
        fsiner += 1;
        siner += (1/3);
        if (siner > 14)
            siner -= 14;
        thissprite = idlesprite;
        draw_monster_body_part(thissprite, siner, x, y);
    }
    if (state == 12)
    {
        // the laugh (special 9): 62 frames, then idle
        sprite_index = spr_hj_gerson_laugh;
        image_index += 0.23333333333333334;
        draw_self();
        laughtimer++;
        if (laughtimer == 1)
            snd_play(snd_gerlaugh);
        if (laughtimer >= 62)
        {
            laughtimer = 0;
            state = 0;
            sprite_index = idlesprite;
            // the finale's laugh ended Chapter 4's turn (2 frames later)
            if (attackpattern == 19)
                kbr_hj_done(2);
        }
    }
    if (say_t > 0)
        kbr_enc_say(x, y - 20, x + 134, y + 78, say, min(1, say_t / 10));
    return 1;
}

// ---------- the attack's end (kbr_enc_cut, every cut): the SOUL red again, the box as it was, Gerson back ----------
function kbr_hj_cut(_all)
{
    if (!variable_global_exists("kbr_hj_dirty") || !global.kbr_hj_dirty)
        return 0;
    global.kbr_hj_dirty = false;
    with (obj_hj_swing)
    {
        if (_all || !(variable_instance_exists(id, "kbrx") && kbrx > 0))
            instance_destroy();
    }
    // the SOUL red again - unless a SPEAR VOLLEY sent to you is still on (its shield: it puts the SOUL back when it ends)
    var _sent = false;
    with (obj_hj_shield)
    {
        if (variable_instance_exists(id, "kbrx") && kbrx > 0 && vanish == 0)
            _sent = true;
    }
    if (!_sent)
    {
        with (obj_heart)
        {
            if (variable_instance_exists(id, "color"))
                color = 0;
            sprite_index = spr_dodgeheart;
            image_alpha = 1;
        }
    }
    if (variable_global_exists("kbr_hj_box") && is_struct(global.kbr_hj_box))
    {
        var _B = global.kbr_hj_box;
        with (obj_growtangle)
        {
            x = _B.x;
            y = _B.y;
            image_xscale = _B.xs;
            image_yscale = _B.ys;
            image_angle = _B.a;
            if (variable_instance_exists(id, "maxxscale"))
                maxxscale = _B.xs;
            if (variable_instance_exists(id, "maxyscale"))
                maxyscale = _B.ys;
        }
    }
    sprite_set_offset(spr_hj_spearblocker, 32, 32);
    with (obj_hj_gerson)
    {
        visible = true;
        state = 0;
        sprite_index = idlesprite;
        x = xstart;
        y = ystart;
        attackcon = 0;
        squishbox = false;
    }
    return 1;
}

// ---------- the background: Chapter 4's arena (obj_dw_church_arena_bg) while he is out ----------
// The gradient, the stained-glass window with its rain and green bell, the arena in its palette (pal_swap_set, as Chapter 4) and
// the spotlight; the colours follow his turns as Chapter 4's follow the story (card castle, mansion, TV world, garden, dark,
// the bell). Not drawn: the prophecy hammer (Chapter 4 draws it with a shader Chapter 3 does not have) and the city.
function kbr_hj_bg_create()
{
    on = 0;
    image_alpha = 0;
    con = 0;
    colcon = 0;
    bgsurface = -1;
    windowsurface = -1;
    bellalpha = 0;
    staralpha = 0;
    cols = [[3165210, 5163080, 201738, 2584886], [4139303, 8667457, 2692114, 7819857], [5959081, 13873450, 3483914, 11184674],
            [4591889, 6697522, 3483683, 8931914], [4591889, 6697522, 3483683, 8931914], [4261519, 2992324, 2102325, 6663647],
            [3278918, 5910896, 2952729, 4850001], [3165210, 5163080, 201738, 2584886]];
    grads = [[3297554, 2381604], [7623249, 4790561], [6478178, 14065681], [4591889, 7811634], [4591889, 7811634], [52667135, 7410175],
             [6422882, 2752785], [3297554, 2381604]];
    cur_g = [3297554, 2381604];
    return 1;
}

function kbr_hj_bg_step()
{
    on = kbr_hj_on() ? 1 : 0;
    image_alpha = on ? min(1, image_alpha + 0.15) : max(0, image_alpha - 0.1);
    // his turns in this match: Chapter 4's story colours (trueturn 3, 4, 5, 6, 7, 8, 12)
    var _t = variable_global_exists("kbr_hj_turns") ? global.kbr_hj_turns : 0;
    var _c = 0;
    if (_t >= 3) _c = 1;
    if (_t >= 4) _c = 2;
    if (_t >= 5) _c = 3;
    if (_t >= 6) _c = 4;
    if (_t >= 7) _c = 5;
    if (_t >= 8) _c = 6;
    if (_t >= 12) _c = 7;
    con = _c;
    staralpha = scr_approach(staralpha, (con == 3) ? 1 : 0, 0.033);
    bellalpha = scr_approach(bellalpha, (con == 7) ? 1 : 0, 0.033);
    return 1;
}

function kbr_hj_bg_draw()
{
    if (image_alpha <= 0)
        exit;
    var cx = camerax();
    var cy = cameray();
    if (!surface_exists(bgsurface))
        bgsurface = surface_create(640, 480);
    if (!surface_exists(windowsurface))
        windowsurface = surface_create(302, 122);
    var _g = grads[clamp(con, 0, 7)];
    cur_g[0] = merge_color(cur_g[0], _g[0], 0.02);
    cur_g[1] = merge_color(cur_g[1], _g[1], 0.02);
    var t = 0.002 * current_time;
    var rain_speed = 0.012 * current_time;
    surface_set_target(windowsurface);
    draw_clear_alpha(c_black, 0);
    draw_sprite_ext(spr_hj_dw_church_bell_Large_topcenter, 0, 151, 10, 1.5, 1.5, sin(t * 0.5) * 24, c_green, bellalpha * 0.75);
    if (staralpha > 0)
    {
        for (var i = 0; i < 10; i++)
            draw_sprite_ext(spr_sparestar_anim, (current_time / 160) + i, (i * 30) + 8, 20 + ((i * 37) mod 100), 1, 1, 0, #323299, staralpha * 0.8);
    }
    draw_sprite_ext(spr_hj_gersonwindow_water, rain_speed, 232, 0, 2, 2, 0, c_white, 0.4);
    draw_sprite_ext(spr_hj_gersonwindow_water, rain_speed, -38, 0, 2, 2, 0, c_white, 0.4);
    draw_sprite_ext(spr_hj_gersonwindow_water, rain_speed, 92, 0, 2, 2, 0, c_white, 0.4);
    draw_sprite_ext(spr_hj_bg_dw_gerson_arena_stained_glass, 0, 44, 0, 2, 2, 0, c_white, 0.5);
    surface_reset_target();
    surface_set_target(bgsurface);
    draw_clear_alpha(c_black, 0);
    draw_sprite_ext(spr_pxwhite, 0, 0, 0, 640, 480, 0, cur_g[1], 1);
    draw_sprite_ext(spr_hj_20px_white_gradient, 0, 640, 160, 640, 8, 180, cur_g[0], 1);
    draw_set_blend_mode(bm_add);
    draw_surface(windowsurface, 168, 0);
    draw_set_blend_mode(bm_normal);
    surface_reset_target();
    draw_set_alpha(image_alpha);
    draw_set_color(c_black);
    draw_rectangle(cx - 10, cy - 10, cx + 650, cy + 490, false);
    draw_set_alpha(1);
    draw_surface_part_ext(bgsurface, 320 - (320 * image_alpha), 0, 640 * image_alpha, 480, (cx + 320) - (320 * image_alpha), cy, 1, 1, c_white, image_alpha);
    draw_set_color(c_black);
    draw_set_alpha(image_alpha);
    draw_rectangle(cx + 257, cy, cx + 266, cy + 200, false);
    draw_rectangle(cx + 372, cy, cx + 381, cy + 200, false);
    draw_set_alpha(1);
    draw_set_color(c_white);
    colcon = scr_approach(colcon, con + 1, (colcon < 1) ? 0.1 : 0.01);
    pal_swap_set(spr_hj_dw_gerson_arena_palette, colcon, false);
    draw_sprite_ext(spr_hj_bg_dw_gerson_arena_battle, 0, cx, cy, 2, 2, 0, c_white, image_alpha);
    pal_swap_reset();
    draw_sprite_ext(spr_hj_dw_gerson_arena_shadow, 0, (cx + 320) - 2, cy + 200, 2, 2, 0, cur_g[1], 0.4 * image_alpha);
    return 1;
}

// ===================================================================================================================
// ---------- his SENDS (ids 32-37, the GERSON family) ----------
// Made in the TARGET's game only, from his own Chapter 4 pieces, around THEIR SOUL / in their box while their own boss fights
// on (make_gerson.py made the pieces sendable: they join the send that makes them, end with it, and never move the box, the
// SOUL or his battle object - except SPEAR VOLLEY, whose green SOUL is the attack).
//   32 HAMMER TOSS (low)     his thrown hammers (obj_hj_hammer) arc in over your box from the right, around your SOUL's column
//   33 SHELL PINBALL (mid)   a shell (obj_hj_pinball) kicked at your SOUL bounces off the box's top and bottom, then bursts
//   34 SWING DOWN (mid)      he swings his hammer down at your box from three sides (obj_hj_swing2: his eye flashes, then the
//                            strike along your SOUL's row / column)
//   35 SPEAR VOLLEY (full)   your SOUL turns GREEN behind his shield (obj_hj_shield): eight spears (obj_hj_spear) from the four
//                            sides - turn the shield with the arrows to block them; then your SOUL is as it was. A SOUL in
//                            another colour (a yellow / purple / orange fight) gets a HAMMER TOSS instead.
//   36 BELL OF JUSTICE (full) two bells beside your box (obj_hj_bellctrl, Chapter 4's unused bell attack): he hammers them
//                            and arcs of notes (obj_hj_note) rain into the box
//   37 GIGA HAMMER (mid)     one giant hammer arcs over the box, hangs, and crashes down through it at your SOUL's column
function kbr_hj_sa_step(_G, _t, _g, _B, _S)
{
    switch (_G.sid)
    {
        case 32:
            if (_t == 0)
                kbr_hj_sa_ghost(_G, _B, spr_hj_gerson_hammer_throw, 52);
            if (_t >= 8 && ((_t - 8) mod 7) == 0 && _t < 50)
                kbr_hj_sa_hammer(_G, _B, _S, _g, (_t - 8) div 7, false);
            _G.end_t = 112;
            break;
        case 33:
            if (_t == 0)
                kbr_hj_sa_ghost(_G, _B, spr_hj_gerson_swing, 30);
            if (_t == 14)
            {
                var _pb = kbr_sa_mk(_G, _B[0] + _B[2] + 123, _B[1] - 5, obj_hj_pinball);
                with (_pb)
                {
                    scr_bullet_init();
                    direction = point_direction(x, y, _S[0], _S[1]);
                    speed = 12;
                    depth -= 1;
                    image_xscale += 0.25;
                    image_yscale += 0.25;
                    active = 1;
                    target = 3;
                    damage = 1;
                    grazed = 0;
                    grazepoints = 2.5;
                    destroyonhit = false;
                }
                kbr_sa_sfx(snd_rudebuster_swing, 1);
            }
            _G.end_t = 210;
            break;
        case 34:
            if (_t == 0 || _t == 24 || _t == 48)
            {
                var _k = _t div 24;
                var _sw;
                if (_k == 0)
                {
                    // from the right, along your SOUL's row (Chapter 4's shot 32, -1)
                    _sw = kbr_sa_mk(_G, _B[0] + 70, _S[1] - 10, obj_hj_swing2);
                    _sw.image_angle = 270;
                    _sw.direction = 540;
                    _sw.gravity_direction = 540;
                }
                else if (_k == 1)
                {
                    // from above, along your SOUL's column (shot 32 at the top)
                    _sw = kbr_sa_mk(_G, _S[0] - 10, _B[1] - 70, obj_hj_swing2);
                    _sw.image_angle = 0;
                    _sw.direction = 270;
                    _sw.gravity_direction = 270;
                }
                else
                {
                    // from the left, along your SOUL's row (shot 32, -2)
                    _sw = kbr_sa_mk(_G, _B[0] - 70, _S[1] - 10, obj_hj_swing2);
                    _sw.image_angle = 90;
                    _sw.direction = 360;
                    _sw.gravity_direction = 360;
                }
            }
            _G.end_t = 110;
            break;
        case 35:
            kbr_hj_sa_volley(_G, _t, _g, _B, _S);
            break;
        case 36:
            if (_t == 0)
            {
                kbr_sa_mk(_G, _B[0], _B[1], obj_hj_bellctrl);
                kbr_sa_sfx(snd_bell, 1);
            }
            _G.end_t = 150;
            // his bells ring on as long as the attack does (Chapter 4's turn ended them): the send stops them here, the notes
            // in the air fly on
            if (_t == _G.end_t)
                kbr_hj_sa_stop(_G, [obj_hj_shakedir, obj_hj_bellctrl, obj_hj_bellhit, obj_hj_bell, obj_hj_teleport]);
            break;
        case 37:
            if (_t == 0)
                kbr_hj_sa_ghost(_G, _B, spr_hj_gerson_hammer_throw, 40);
            if (_t == 12)
                kbr_hj_sa_hammer(_G, _B, _S, _g, 0, true);
            _G.end_t = 130;
            break;
    }
    return 1;
}

// the send's own pieces of these objects go now (a looping controller's end)
function kbr_hj_sa_stop(_G, _l)
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

// his phantom beside your box while he throws (the knights' sends show their sender's knight the same way)
function kbr_hj_sa_ghost(_G, _B, _spr, _d)
{
    var _T = kbr_sa_tel(_G, "spr", _B[0] + _B[2] + 95, _B[1] - 30, _d, 0);
    _T.spr = _spr;
    _T.xs = 2;
    return _T;
}

// one of his thrown hammers (Chapter 4's box throw: from his hand beside the box, an arc onto your SOUL's column); _giga: the
// giant one (it hangs at the top of its arc, then drops straight down through the box)
function kbr_hj_sa_hammer(_G, _B, _S, _g, _k, _giga)
{
    var _off = (_S[0] - _B[0]) + (kbr_rng_int(_g, 41) - 20);
    var _vy = -14 + ((kbr_rng_int(_g, 21) - 10) / 10);
    var _h = kbr_sa_mk(_G, _B[0] + _B[2] + 123, _B[1] - 5, obj_hj_hammer);
    with (_h)
    {
        scr_bullet_init();
        active = 1;
        scr_darksize();
        if (_giga)
        {
            image_xscale += 6;
            image_yscale += 6;
            mask_index = spr_hj_gerson_gigahammer_mask;
            fakehspeed = -abs((x - (_B[0] + _off)) / 25.5);
            fakevspeed = -16;
            destroyonhit = false;
            gigahammer = true;
        }
        else
        {
            fakehspeed = (-abs(x - (_B[0] + _off)) / 45) + ((_k - 2.5) * 0.3);
            fakevspeed = _vy;
        }
        gravity_direction = 270;
        fakegravity = 0.6;
        depth -= 1;
        target = 3;
        damage = 1;
        grazed = 0;
        grazepoints = 2.5;
    }
    kbr_sa_sfx(snd_smallswing, 0.75 + (_k * 0.05));
    return _h;
}

// SPEAR VOLLEY: _G.sv - 1 his shield is this send's (your SOUL was red), 2 a shield was already up (his own green attack:
// the spears join it), 3 your SOUL is in another colour (a HAMMER TOSS instead)
function kbr_hj_sa_volley(_G, _t, _g, _B, _S)
{
    if (_t == 0)
    {
        _G.sv = 3;
        var _md = kbr_soul_mode();
        if (_md == "green")
            _G.sv = 2;
        else if (_md == "red")
        {
            _G.sv = 1;
            var _h = instance_find(obj_heart, 0);
            _G.svc = [_h.color, _h.sprite_index, _h.image_alpha];
            kbr_sa_mk(_G, _S[0], _S[1], obj_hj_shield);
            kbr_sa_sfx(snd_boost, 1);
        }
        _G.onend = kbr_hj_sa_volley_end;
    }
    if (_G.sv == 3)
    {
        if (_t == 0)
            kbr_hj_sa_ghost(_G, _B, spr_hj_gerson_hammer_throw, 52);
        if (_t >= 8 && ((_t - 8) mod 7) == 0 && _t < 50)
            kbr_hj_sa_hammer(_G, _B, _S, _g, (_t - 8) div 7, false);
        _G.end_t = 112;
        return 1;
    }
    // eight spears, one every 14 frames from frame 24, each from one of the four sides (the send's own stream), 45 frames away
    if (_t >= 24 && ((_t - 24) mod 14) == 0 && _t < 24 + (14 * 8) && instance_exists(obj_hj_shield))
    {
        var _dir = kbr_rng_int(_g, 4) * 90;
        var _sp = kbr_sa_mk(_G, -9999, -9999, obj_hj_spear);
        _sp.special = 0;
        _sp.direction = _dir;
        _sp.fakespeed = 6;
        _sp.len = 6 * 45;
        _sp.image_angle = _dir;
    }
    _G.end_t = 24 + (14 * 8) + 50;
    // the volley is over: the shield fades, the SOUL is as it was (the send's end does it too, if it ends sooner)
    if (_t == _G.end_t - 10)
        kbr_hj_sa_volley_end(_G);
    return 1;
}

function kbr_hj_sa_volley_end(_G)
{
    if (!variable_struct_exists(_G, "sv") || _G.sv != 1)
        return 0;
    _G.sv = 0;
    var _gx = _G.gx;
    with (obj_hj_shield)
    {
        if (variable_instance_exists(id, "kbrx") && kbrx == _gx)
            vanish = 1;
    }
    // his own green attack keeps its shield (and the SOUL green): only a red SOUL is put back
    var _other = false;
    with (obj_hj_shield)
    {
        if (!(variable_instance_exists(id, "kbrx") && kbrx > 0))
            _other = true;
    }
    if (!_other && instance_exists(obj_heart))
    {
        var _c = _G.svc;
        with (obj_heart)
        {
            color = _c[0];
            sprite_index = _c[1];
            image_alpha = _c[2];
        }
    }
    return 1;
}

// the host's bots in his green attacks: each bot's SOUL sits behind its own shield on the box's middle, and the bot turns that
// shield as a player does (DRBR 1.0.1: kbr_hj_bot_face - before, a block was a roll of the dice and its shield never moved): it
// faces the spear coming soonest once it has seen it (its REACTION TIME), now and then the wrong way (MISTAKES), a little late
// when it plays less precisely, and turns AWAY from a red hammer (it breaks the shield). A spear reaching the shields is blocked
// by the bots facing it (kbr_hj_bots_spear), else it hurts as a player's hit does. (The spears of one game reach every SOUL there
// at once - the bots' and the host's - so the host's spears are theirs too.) Its shield's direction goes to everyone with its
// place, so whoever watches the bot sees its shield turn (kbr_hj_puppet).
function kbr_hj_bot_face(_b, _c, _s)
{
    var _sh = kbr_hj_up_shield();
    if (_sh == noone)
    {
        _s.gd = -1;
        return 0;
    }
    if (!variable_struct_exists(_s, "gd") || _s.gd < 0)
    {
        _s.gd = _sh.idealdir;
        _s.gdk = noone;
        _s.gdw = 0;
        _s.gdn = _s.gd;
    }
    // (frames: the bots' own count - kfo_bot_track)
    var _F = (variable_global_exists("kfo_bt") && is_struct(global.kfo_bt)) ? global.kfo_bt.f : 0;
    // the spear coming soonest that it has seen for its reaction time
    var _bestl = 999999;
    var _best = noone;
    var _react = _c.react;
    with (obj_hj_spear)
    {
        if ((variable_instance_exists(id, "kbrx") && kbrx > 0) || variable_instance_exists(id, "kbr_hjb"))
            continue;
        // (when the bots first saw it: kept on the spear)
        if (!variable_instance_exists(id, "kbr_seen"))
            kbr_seen = _F;
        if (_F - kbr_seen < _react)
            continue;
        if (len < _bestl)
        {
            _bestl = len;
            _best = id;
        }
    }
    if (_best != noone && _best != _s.gdk)
    {
        // a new spear to face: where the shield has to point (a red hammer: away), the shield's own directions (4, or 8 when it
        // takes diagonals); MISTAKES: now and then another one; PRECISION: a frame or two later
        _s.gdk = _best;
        var _ang = (_best.bouncespear == 2) ? _best.direction : _best.image_angle;
        var _want = _best.redhammer ? _ang : (_ang + 180);
        var _step = _sh.diagonal_enabled ? 45 : 90;
        _want = ((round(_want / _step) * _step) mod 360 + 360) mod 360;
        if (_c.miss > 0 && random(100) < _c.miss)
            _want = (_want + (_step * (1 + irandom((360 / _step) - 2)))) mod 360;
        _s.gdn = _want;
        _s.gdw = max(0, round((100 - _c.prec) / 25));
    }
    if (_s.gdw > 0)
        _s.gdw--;
    else
        _s.gd = _s.gdn;
    return 1;
}

// a shield direction from the network: one of the shield's 8 (0, 45 ... 315) or -1
function kbr_hj_dir_ok(_v)
{
    if (!is_numeric(_v) || _v < 0)
        return -1;
    return ((round(_v / 45) * 45) mod 360 + 360) mod 360;
}

// the shield that is up in this game (his own, not a send's fading one) or noone
function kbr_hj_up_shield()
{
    var _o = noone;
    with (obj_hj_shield)
    {
        if (_o == noone && vanish == 0 && !(variable_instance_exists(id, "kbrx") && kbrx > 0))
            _o = id;
    }
    return _o;
}

// where this game's player is turning the green shield (-1: no shield up) - sent with the SOUL's place, for whoever watches
function kbr_hj_my_dir()
{
    var _o = kbr_hj_up_shield();
    return (_o == noone) ? -1 : _o.idealdir;
}

// a watcher's shield turns as the followed one's does (their direction from the host's positions; -1: none)
function kbr_hj_puppet(_q)
{
    if (!variable_struct_exists(_q, "gd") || !is_numeric(_q.gd) || _q.gd < 0)
        return 0;
    var _o = kbr_hj_up_shield();
    if (_o != noone)
        _o.idealdir = _q.gd;
    return 1;
}

function kbr_hj_bots_spear(_red)
{
    if (!kbr_on() || !kfo_is_host() || !is_struct(global.kfo.H))
        return 0;
    // a sent spear (in the host's own game, at the host) is not the bots'
    if (variable_instance_exists(id, "kbrx") && kbrx > 0)
        return 0;
    var _h = global.kfo.H;
    var _e = _h.eff;
    var _nb = 0;
    var _n = 0;
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        var _b = _h.pl[_i];
        if (!_b.bot)
            continue;
        var _bi = _nb;
        _nb++;
        if (!_b.inm || !_b.al || !is_struct(_b.bt))
            continue;
        var _s = _b.bt;
        if (_s.inv > 0)
            continue;
        // blocked by the bot's own shield (kbr_hj_bot_face): facing the spear - a red hammer: facing anywhere else
        var _ang = (bouncespear == 2) ? direction : image_angle;
        var _sl = (instance_exists(obj_hj_shield) && obj_hj_shield.diagonal_enabled) ? 30 : 50;
        var _faces = variable_struct_exists(_s, "gd") && _s.gd >= 0 && abs(angle_difference(_ang, _s.gd + 180)) < _sl;
        if (_red ? !_faces : _faces)
            continue;
        var _t = kbr_hit_dmg(_red ? 1 : 2, false);
        var _dmg = max(1, round(_t[0] * (_e.dmul / 100)));
        if (_e.ohko)
            _dmg = _b.hp;
        kfo_bot_take(_b, _dmg);
        _b.hits++;
        _s.inv = round(_t[1] * (_e.ifr / 100));
        _n++;
        if (_b.hp <= 0)
            kfo_host_out_report(_b.pid, round(kfo_host_tick_now()), "out", _b.lby);
    }
    return _n;
}

// the bots' SOULs while his shield is up in the host's game (his green attacks): on the box's middle, as everyone's
function kbr_hj_bots_green(_box)
{
    if (!instance_exists(obj_hj_shield) || is_undefined(_box))
        return false;
    var _s = instance_find(obj_hj_shield, 0);
    if (_s.vanish != 0 || (variable_instance_exists(_s, "kbrx") && _s.kbrx > 0))
        return false;
    return true;
}
