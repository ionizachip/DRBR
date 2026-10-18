// ===== Build 52: SECRET BOSSES - JEVIL (DELTARUNE Chapter 1) in KNIGHT FIGHTS ONLINE =====
// Online only: the offline hub, its registry and every offline fight are unchanged.
// An ENCOUNTER that is not a Roaring Knight: a row of the online roster (kbr_roster) with an "enc" key, and an entry here.
// The timeline treats it like a knight (its attack list, phases, lengths, its finale in the Roaring's place); the lineup holds
// it under an id of 1000 + n (never a hub registry index: knight_reg() answers those ids from here, offline never sees them).
// Jevil's pieces are his own Chapter 1 objects (make_jevil.py: obj_jv_*, from the player's Chapter 1 data.win); this file is
// his battle object (obj_jv_joker: the knights' arm / hold / attack handshake), his look, lines, background, music and
// clean-up.
// TO ADD THE NEXT SECRET BOSS: its pieces (like make_jevil.py), an entry in kbr_enc_defs, a roster row with its "enc" key,
// its battle object with the same handshake (kbr_jv_* as the model). Nothing else in the match engine changes.

#macro KBR_ENC_BASE 1000

function kbr_enc_defs()
{
    if (variable_global_exists("kbr_enc_t") && is_array(global.kbr_enc_t))
        return global.kbr_enc_t;
    // Jevil: obj_joker's 16 attacks (its user event 5) in his own order. [phase, id, name, flags] as a knight's list (flags:
    // 2 = the finale); phase 1 = his turns 0-3, phase 2 = 4-7, phase 3 = 8-14 (the late ones), the finale BYE-BYE (15).
    // type: the obj_dbulletcontroller type; tt: his own turn timer for it (frames at 30 a second - its length here); cond: his
    // body for it (2 = he sinks into the box, 5 = he becomes the Devilsknife, 0 = he stays); inv: the hit's invincibility;
    // line: what he says (Chapter 1's text, obj_joker turns 0-18 in order).
    global.kbr_enc_t = [
        { key: "jevil", cat: "secret", fid: KBR_FAM_JEVIL, chapter: 1, soul: "red", sends: [26, 27, 28, 29, 30, 31], song: "THE WORLD REVOLVING - Toby Fox",
          desc: "Chapter 1's secret boss. Chaos,#chaos! His own 16 attacks.",
          name: "Jevil", short: "JEVIL", title: "JEVIL", col: make_color_rgb(200, 140, 255), lu: KBR_ENC_BASE,
          music: "joker.ogg", obj: "obj_jv_joker", spr: "spr_jv_joker_main", roar: 15, roar_dur: 640,
          atk: [[1, 0, "Chaos Teleport", 0], [1, 1, "Ring-Around", 0], [1, 2, "Heart Bombs", 0], [1, 3, "Devilsknife", 0],
                [2, 4, "Carousel", 0], [2, 5, "Club Bombs", 0], [2, 6, "Diamond Rain", 0], [2, 7, "Spade Spin", 0],
                [3, 8, "Carousel Race", 0], [3, 9, "Spade Bombs", 0], [3, 10, "Dark Clubs", 0], [3, 11, "Devilsknife Swing", 0],
                [3, 12, "Teleport Frenzy", 0], [3, 13, "Chaos Bombs", 0], [3, 14, "Diamond Storm", 0], [4, 15, "BYE-BYE", 2]],
          type: [70, 65, 49, 75, 62, 50, 73, 68, 61, 48, 72, 76, 71, 46, 74, 77],
          tt: [240, 240, 240, 240, 240, 300, 240, 240, 240, 270, 240, 240, 240, 330, 240, 1500],
          cond: [2, 0, 2, 5, 0, 2, 0, 0, 0, 2, 0, 5, 2, 2, 0, 5],
          inv: [60, 60, 60, 60, 20, 60, 60, 60, 20, 60, 60, 60, 60, 60, 60, 60],
          line: ["CHAOS, CHAOS,&&CATCH ME&IF YOU CAN!", "SHALL WE&PLAY THE&RING-AROUND?", "MY HEARTS GO&OUT TO ALL&YOU SINNERS!",
                 "HA, HA, LET'S&MAKE THE&DEVILSKNIFE.", "PIIP PIIP,&LET'S RIDE THE&CAROUSEL GAME.", "HEE HEE,&HAVING FUN!?&JOIN THE&CLUB!",
                 "HEARTS,&DIAMONDS,&I CAN DO&ANYTHING!", "WHO KEEPS&SPINNING THE&WORLD&AROUND?", "YOU KIDS ARE&REALLY&KEEPING UP!",
                 "NU-HA!!&I NEVER HAD&SUCH FUN,&FUN!!", "A BEAUTY IS&JOYING IN&MY HEART!", "EVEN&DEVILSKNIFE&IS SMILING!",
                 "IT'S SO&EXCITING...&I CAN'T&TAKE IT!!!", "THIS IS IT,&BOISENGIRLS!&SEE YA!", "ENOUGH!!&YOU KIDS&TIRED ME UP!",
                 "KIDDING!!&HERE'S MY&FINAL CHAOS!"],
          again: ["A CHAOS,&CHAOS!", "PLEASE, IT'S&JUST A&SIMPLE&CHAOS.", "I CAN DO&ANYTHING!!", "THIS BODY&CANNOT BE&KILLED!",
                  "THESE&CURTAINS&ARE REALLY&ON FIRE!", "IT'S ALL&TOO MUCH&FUN!!!"],
          flavor: ["* The world is spinning, spinning.", "* The air crackles with freedom.", "* JEVIL is laughing incomprehensibly.",
                   "* It feels like a whirlwind.", "* Smells like chaos."], px: 500, py: 160 }
    ];
    // DRBR: the other bosses (each its own template file; the order is their lineup id: 1000 + n)
    array_push(global.kbr_enc_t, kbr_enc_def_gerson());
    array_push(global.kbr_enc_t, kbr_enc_def_flowery());
    array_push(global.kbr_enc_t, kbr_enc_def_spamton());
    array_push(global.kbr_enc_t, kbr_enc_def_pink());
    return global.kbr_enc_t;
}

// the encounter of a lineup id (1000 + n), undefined for a knight
function kbr_enc_of_lu(_id)
{
    if (!is_numeric(_id) || _id < KBR_ENC_BASE)
        return undefined;
    var _d = kbr_enc_defs();
    var _i = floor(_id) - KBR_ENC_BASE;
    return (_i >= 0 && _i < array_length(_d)) ? _d[_i] : undefined;
}

// the encounter of an online id (undefined for a knight row)
function kbr_ok_enc(_ok)
{
    var _r = kbr_ok_row(_ok);
    if (!variable_struct_exists(_r, "enc"))
        return undefined;
    var _d = kbr_enc_defs();
    for (var _i = 0; _i < array_length(_d); _i++)
    {
        if (_d[_i].key == _r.enc)
            return _d[_i];
    }
    return undefined;
}

// an encounter can be fought in this build: its battle object and its look are here
function kbr_enc_ready(_d)
{
    return is_struct(_d) && asset_get_index(_d.obj) >= 0 && asset_get_index(_d.spr) >= 0;
}

// what knight_reg() gives for an encounter's lineup id: shaped like a hub registry entry, so the lineup's names, colours and
// lists work for it as for a knight (it is never in the hub registry itself)
function kbr_enc_reg(_id)
{
    var _d = kbr_enc_of_lu(_id);
    if (!is_struct(_d))
        _d = kbr_enc_def0();
    return { id: _d.lu, key: _d.key, name: _d.name, short: _d.short, title: _d.title, desc: "", author: "Toby Fox", skip_flag: -1, has_practice: false,
        music_rename: undefined, music: _d.music, joke: false, rush: false, weird: false, needs_kris: false, color: _d.col, tint: false,
        portrait: _d.spr, credits: [], songcredit: variable_struct_exists(_d, "song") ? _d.song : "THE WORLD REVOLVING - Toby Fox", pace: { gate: 1, tmin: 15, gate_b: 1, tmin_b: 15 }, twin_star: "spr_knight_bullet_star", twin_small: "spr_smallbullet", twin_sword: "spr_roaringknight_sword_ol", twin_blend: c_white, atk: _d.atk, chapter: variable_struct_exists(_d, "chapter") ? _d.chapter : 1, enc: true };
}

// ---------- the lineup: the encounter's battle object (instead of knight_lu_make's obj_knight_enemy) ----------
function kbr_enc_make(_i)
{
    var _lu = global.knight_lu;
    var _d = kbr_enc_of_lu(_lu.ks[_i]);
    var _o = asset_get_index(_d.obj);
    // DRBR: what its Create makes (Flowery's tower and friends, Jevil's body, Spamton's yellow SOUL...) is its entourage, as a
    // knight's is (knight_lu_make): switched off with it until it comes on stage - its background aside (each fades itself)
    var _seen = {};
    with (all)
        variable_struct_set(_seen, string(id), 1);
    // (where Chapter 1 puts him: the screen's 500, 160 - scr_encountersetup's encounter 25; the knights stand at 425, 78)
    // (DRBR: each boss stands where its own chapter puts it: px, py on the screen)
    var _e = instance_create(camerax() + (variable_struct_exists(_d, "px") ? _d.px : 500), cameray() + (variable_struct_exists(_d, "py") ? _d.py : 160), _o);
    _e.myself = 0;
    _lu.inst[_i] = _e;
    _lu.home[_i] = [_e.x, _e.ystart];
    var _s = knight_lu_slot_save();
    _s.name = _d.name;
    _lu.slot[_i] = _s;
    var _mine = [];
    with (all)
    {
        if (id != _e && !variable_struct_exists(_seen, string(id)) && string_pos("_bg", object_get_name(object_index)) == 0)
            array_push(_mine, id);
    }
    _lu.ent[_i] = _mine;
    _lu.look[_i] = { spr: asset_get_index(_d.spr), xs: 2, ys: 2, blend: c_white, x: _e.x, y: _e.y };
    for (var _j = 0; _j < array_length(_mine); _j++)
        instance_deactivate_object(_mine[_j]);
    instance_deactivate_object(_e);
    return _e;
}

// DRBR: boss lineup id _k is leaving the stage: its own objects still about (the ones its Create made and what its fight left
// on: Flowery's tower, his friends...) - its background aside (it fades itself), and never a player's send (that is the target's)
function kbr_enc_entourage(_k, _not)
{
    var _o = [];
    var _d = kbr_enc_of_lu(_k);
    if (!is_struct(_d))
        return _o;
    var _pre = string_copy(_d.obj, 1, 7);
    with (all)
    {
        var _n = object_get_name(object_index);
        if (id != _not && string_pos(_pre, _n) == 1 && string_pos("_bg", _n) == 0 && !(variable_instance_exists(id, "kbrx") && kbrx > 0))
            array_push(_o, id);
    }
    return _o;
}

// the encounter on stage now (undefined: a knight)
function kbr_enc_now()
{
    if (!is_struct(global.knight_lu) || !global.knight_lu.ready)
        return undefined;
    var _lu = global.knight_lu;
    return kbr_enc_of_lu(_lu.ks[_lu.act]);
}

function kbr_jv_on()
{
    var _d = kbr_enc_now();
    return is_struct(_d) && _d.key == "jevil";
}

// ---------- Jevil's battle object (obj_jv_joker) ----------
function kbr_jv_create()
{
    image_xscale = 2;
    image_yscale = 2;
    image_speed = 0;
    visible = true;
    idlesprite = spr_jv_joker_main;
    sprite_index = spr_jv_joker_main;
    attacked = 1;
    talked = 1;
    acting = 0;
    rtimer = 0;
    attackchosen = false;
    turns = 0;
    siner = 0;
    jattack = 0;
    beepnoise = 0;
    beepbuffer = 0;
    burstnoise = 0;
    say = "";
    say_t = 0;
    said = [];
    whiteflash = 0;
    body = instance_create(x, y, obj_jv_body);
    body.owner = id;
    body.depth = depth;
    // his background: in front of the knights' arena (obj_bgfountaintest, depth 50000 - switched off with its knight anyway),
    // behind everything of the battle; it fades in over whatever is behind it (a black ground first)
    if (!instance_exists(obj_jv_bg))
        instance_create_depth(0, 0, 49000, obj_jv_bg);
    return 1;
}

function kbr_jv_step()
{
    if (!kbr_on())
        exit;
    if (instance_exists(body))
    {
        body.x = x;
        body.y = y;
    }
    if (burstnoise == 1)
    {
        snd_stop(snd_bomb);
        snd_play(snd_bomb);
        burstnoise = 0;
    }
    if (say_t > 0)
        say_t--;
    if (whiteflash > 0)
        whiteflash--;
    // the knights' handshake: the box at 1.5 (as Chapter 1's Jevil makes his: the screen's middle, 170 down), then the count
    // held at 11 by the shared clock (kbr_rgate), the attack at 12
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
            kbr_jv_attack();
            attacked = 1;
        }
    }
    return 1;
}

// his dance by the match's stage (Chapter 1: the dance at 80% HP, the shadow-dance from 40%, the finale's)
function kbr_jv_dance()
{
    var _M = kbr_match();
    var _st = is_undefined(_M) ? 0 : max(0, _M.stage);
    if (_st >= 3)
        return 3;
    if (_st >= 1)
        return 1;
    return 0;
}

// the attack of the cycle (self = obj_jv_joker; called on the frame the shared clock releases it, kbr_rgate seeded the stream)
function kbr_jv_attack()
{
    var _d = kbr_enc_def0();
    var _ai = clamp(global.knight_lu.plan_i, 0, array_length(_d.type) - 1);
    jattack = _ai;
    turns++;
    global.turntimer = _d.tt[_ai];
    global.monsterattackname[0] = _d.atk[_ai][2];
    var _dc = instance_create(x, y, obj_jv_dbc);
    _dc.type = _d.type[_ai];
    _dc.joker = 1;
    _dc.target = 0;
    _dc.damage = 100;
    _dc.grazepoints = 3;
    _dc.inv = _d.inv[_ai];
    // (DRBR 1.0.2: whether his body turns into the Devilsknife now - its own Draw then says "METAMORPHOSIS!")
    var _morph = false;
    if (instance_exists(body))
    {
        body.dancelv = kbr_jv_dance();
        if (_d.cond[_ai] == 2)
        {
            body.condition = 2;
            body.size = 2;
            body.sndcon = 0;
        }
        else if (_d.cond[_ai] == 5 && body.condition < 4)
        {
            body.condition = 5;
            body.timer = 0;
            _morph = true;
        }
    }
    kbr_jv_say(_d, _ai, _morph);
    return 1;
}

// his line for attack _ai: its own the first time in this match, then one of his repeats; his voice with it (Chapter 1's).
// DRBR 1.0.2: the Devilsknife attacks (his body turns into the scythe: _morph) and the finale have Chapter 1's own clip -
// "METAMORPHOSIS!" from his body as it turns, "BYE-BYE!" from the finale's bullets - and nothing on top of it (a laugh or
// "CHAOS, CHAOS!" played over it: your report "uses the wrong voiceline"); a Devilsknife whose body is already the scythe
// says it here instead. DRBR 1.0.3: and it IS Chapter 1's clip - the build's snd_joker_metamorphosis is the Cyan Knight mod's
// (another voice line); his are snd_jv_joker_metamorphosis and snd_jv_joker_laugh0 (make_jevil.py OWN_SND)
function kbr_jv_say(_d, _ai, _morph)
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
    say_t = 75;
    var _snd = -1;
    if (_ai == 15 || (_d.cond[_ai] == 5 && !is_undefined(_morph) && _morph))
        _snd = -1;
    else if (_d.cond[_ai] == 5)
        _snd = snd_jv_joker_metamorphosis;
    else if (_ai == 0 || string_pos("CHAOS", say) > 0)
        _snd = snd_joker_chaos;
    else if (string_pos("ANYTHING", say) > 0)
        _snd = snd_joker_anything;
    else
        _snd = choose(snd_jv_joker_laugh0, snd_joker_ha0, snd_joker_ha1);
    if (_snd >= 0)
        snd_play(_snd);
    return 1;
}

// his speech balloon (Chapter 1's & line breaks; DRBR's balloon, VIEW > BOSS LINES)
function kbr_jv_draw()
{
    if (!kbr_on() || say_t <= 0 || say == "")
        return 0;
    // (where his body is drawn: obj_jv_body, its x + 20, y + 18 at 2x)
    var _bx = x;
    var _by = y;
    if (variable_instance_exists(id, "body") && instance_exists(body))
    {
        _bx = body.x;
        _by = body.y;
    }
    return kbr_enc_say(_bx - 22, _by - 22, _bx + 62, _by + 60, say, clamp(say_t / 10, 0, 1));
}

// ---------- the background: on while Jevil is out; the knights' arena hidden meanwhile ----------
function kbr_jv_bg_step()
{
    on = kbr_jv_on() ? 1 : 0;
    // its rotation speeds up with the match (Chapter 1: as his HP goes down)
    var _M = kbr_match();
    if (!is_undefined(_M))
        rotspeed = max(rotspeed, 1 + (min(4, max(0, _M.stage)) * 0.35));
    return 1;
}

// ---------- the music: THE WORLD REVOLVING while he is out, the match's song after ----------
// (1.0.1: kbr_enc_music does it, as for every boss - two handlers queued two songs when he came on after another boss)
function kbr_jv_music()
{
    return 0;
}

// ---------- his attacks' pieces: the SOUL's extra speed, the bots' box, clean-up ----------
// Chapter 1 sets the SOUL's speed for two attacks (Spade Spin 5, BYE-BYE 10, from its 4): online that is a bonus on top of
// the room's speed (the same for the bots)
function kbr_jv_speed_bonus()
{
    var _b = 0;
    with (obj_jv_dbc)
    {
        if (type == 68)
            _b = max(_b, 1);
        if (type == 77)
            _b = max(_b, 6);
    }
    return _b;
}

// BYE-BYE takes the box away: the SOUL (a player's and a bot's) has the screen
function kbr_jv_boxless()
{
    with (obj_jv_dbc)
    {
        if (type == 77 && !instance_exists(obj_growtangle))
            return true;
    }
    return false;
}

// obj_jv_dbc's Create: what to put back when it goes
function kbr_jv_dbc_create()
{
    jv_fx = [];
    return 1;
}

// obj_jv_dbc's Destroy (the attack's end, kbr_cut): BYE-BYE's darkness, white-out, the giant scythe and its rumble go with it
function kbr_jv_dbc_destroy()
{
    if (variable_instance_exists(id, "darkfader") && instance_exists(darkfader))
        with (darkfader) instance_destroy();
    if (variable_instance_exists(id, "fadewhite") && instance_exists(fadewhite))
        with (fadewhite) instance_destroy();
    if (variable_instance_exists(id, "lastscythe") && instance_exists(lastscythe))
        with (lastscythe) instance_destroy();
    if (variable_instance_exists(id, "rumnoise"))
        audio_stop_sound(rumnoise);
    with (obj_heart)
    {
        if (variable_instance_exists(id, "boundaryup"))
            boundaryup = 0;
    }
    with (obj_jv_lscythe)
        instance_destroy();
    return 1;
}

// Jevil's entry (a call's result cannot be indexed directly in this compiler)
function kbr_enc_def0()
{
    // DRBR: Jevil's entry by its key (more bosses are in the table now)
    var _d = kbr_enc_defs();
    for (var _i = 0; _i < array_length(_d); _i++)
    {
        if (_d[_i].key == "jevil")
            return _d[_i];
    }
    return _d[0];
}

// every Jevil piece's Create ends with this: what Chapter 3's scr_bullet_inherit reads from whoever calls it (Chapter 1's pieces
// do not all have these; -1 = "not passed on", as Chapter 3's obj_dbulletcontroller sets them)
function kbr_jv_vars()
{
    var _l = ["damage", "grazepoints", "timepoints", "inv", "target", "grazed", "grazetimer"];
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        if (!variable_instance_exists(id, _l[_i]))
            variable_instance_set(id, _l[_i], -1);
    }
    if (!variable_instance_exists(id, "element"))
        element = "none";
    if (!variable_instance_exists(id, "creatorid"))
        creatorid = id;
    if (!variable_instance_exists(id, "creator"))
        creator = id;
    // DRBR: a bullet of his (a child of obj_collidebullet) is complete from its Create on - Chapter 1's rule: destroyed when it
    // hits (Chapter 1's user event 5 always destroyed it; a permanent piece has its own user event 5 and never reads it)
    if (object_is_ancestor(object_index, obj_collidebullet))
        kbr_bullet_contract(1);
    return 1;
}

// a plain bullet one of Jevil's pieces makes (obj_collidebullet has no Create of its own to adopt it): it joins its maker's send
function kbr_jv_adopt(_i)
{
    // DRBR: first of all it is a complete bullet (Chapter 1 made it with nothing but instance_create; drbr53.gml)
    if (instance_exists(_i))
    {
        with (_i)
            kbr_bullet_contract(1);
    }
    if (global.kbr_san > 0 && instance_exists(_i) && variable_instance_exists(id, "kbrx") && kbrx > 0 && !variable_instance_exists(_i, "kbrx"))
    {
        var _G = kbr_sa_find(kbrx);
        if (is_struct(_G) && !_G.dead)
        {
            with (_i)
                kbr_sa_tag(_G);
        }
    }
    return _i;
}
