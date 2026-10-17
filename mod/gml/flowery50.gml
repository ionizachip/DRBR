// ===== Build 50: FLOWERY (Chapter 5) - a playable party member of his own (custom character 5, cc50.gml) =====
// Not Noelle: his own character id (5), his own hero (obj_knight_herocc), his own HP / AT / DF / MAG, his own MAGIC and ACTION,
// his own gear, his own HP-bar box (golden, as Chapter 5 draws it), his own voice. He and Noelle can be in one party.
//   - his battle poses are his Chapter 5 fight's, turned to face the knight (fl_atlas: mirrored copies);
//   - his moves are built from his own fight in Chapter 5: the runner's dash, crouch and crescent kick (MY JARONA), the flash
//     kick (SANFRANDISCO), the pirouette (EZ2DANCE), the hug and the kiss (AFINIHUG, HONEY KISS), OMEGA FLOWERY's power-up,
//     rush, clash, wind-up and punch with its explosions (PRISM RUSH) - with Kris jumping in to slash when Kris is in the party;
//   - F-ACTION: his own ACTION, the first entry of his MAGIC;
//   - his voice clips only where he says them (no passive lines).
// TP costs (TP is out of 250): Sanfrandisco 0%, My Jarona 50%, Ez2Dance 20%, Prism Rush 100%, Afinihug 35%, Honey Kiss 40%.

global.knight_fl = undefined;

// his assets, looked up by name once (the build copies them from Chapter 5; the mirrored poses come from fl_atlas)
function knight_fl_a()
{
    if (is_struct(global.knight_fl))
        return global.knight_fl;
    global.knight_fl = {
        walk_d: asset_get_index("spr_flowery_walk_down"), walk_u: asset_get_index("spr_flowery_walk_up"), walk_l: asset_get_index("spr_flowery_walk_left"), walk_r: asset_get_index("spr_flowery_walk_right"),
        head: asset_get_index("spr_headflowery"), bname: asset_get_index("spr_bnameflowery"), bname_ja: asset_get_index("spr_ja_bnameflowery"), eqchar: asset_get_index("spr_flowery_equipchar"),
        // fl_atlas (make_fl_atlas.py): every one anchored on his body and feet, lined up with the party, facing the knight
        idle: asset_get_index("spr_knfl_idle"), walk: asset_get_index("spr_knfl_walk"), act: asset_get_index("spr_knfl_act"), ready: asset_get_index("spr_knfl_attackready"),
        attack: asset_get_index("spr_knfl_attack"), defend: asset_get_index("spr_knfl_defend"), hurt: asset_get_index("spr_knfl_hurt"), defeat: asset_get_index("spr_knfl_defeat"),
        victory: asset_get_index("spr_knfl_victory"), spell: asset_get_index("spr_knfl_spell"), spellready: asset_get_index("spr_knfl_spellready"), item: asset_get_index("spr_knfl_item"),
        kiss: asset_get_index("spr_knfl_kiss"), dance: asset_get_index("spr_knfl_dance"), pose: asset_get_index("spr_knfl_pose"), jarona: asset_get_index("spr_knfl_jarona"),
        // his own fight's moves: the flash kick (0 run, 1 crouch, 2 crescent kick); the runner (0-3 run, 4 crouch, 5 crescent
        // kick, 6 kick); OMEGA FLOWERY (0-2 pose, 3-5 power-up, 6-8 rush, 9-11 clash, 12-16 wind-up, 17-19 punch, 20-22 idle)
        flashkick: asset_get_index("spr_knfl_flashkick"), runner: asset_get_index("spr_knfl_runner"), omega: asset_get_index("spr_knfl_omega"),
        hitfx: asset_get_index("spr_knfl_hitfx"), pressfront: asset_get_index("spr_knfl_pressfront"),
        crescent: asset_get_index("spr_flowery_crescent_only"), o_heart: asset_get_index("spr_omegaflowery_heart"),
        o_ex: [asset_get_index("spr_omegaflowery_explosion_a"), asset_get_index("spr_omegaflowery_explosion_b"), asset_get_index("spr_omegaflowery_explosion_c")],
        // (build 50: no shockwave - Chapter 3's spr_swatchling_shockwave is one tall white spike, not a ring: it showed as a stray
        // triangle under him when he landed and at the foe. Every knight_fl_fx1(_a.shock, ...) draws nothing now.)
        shock: -1,
        // his OMEGA FLOWERY battle poses (fl_atlas, lined up like his own): put on his hero for good in the last stand
        om_idle: asset_get_index("spr_knfl_om_idle"), om_ready: asset_get_index("spr_knfl_om_ready"), om_attack: asset_get_index("spr_knfl_om_attack"),
        om_hurt: asset_get_index("spr_knfl_om_hurt"), om_defend: asset_get_index("spr_knfl_om_defend"), om_spellready: asset_get_index("spr_knfl_om_spellready"),
        om_spell: asset_get_index("spr_knfl_om_spell"), om_pose: asset_get_index("spr_knfl_om_pose")
    };
    return global.knight_fl;
}

function knight_fl_spr_ok(_s)
{
    return knight_cc_spr(_s);
}

// the party value is the game's character: Flowery is 5 (kept for the menus' old calls)
function knight_ch_real(_v)
{
    return _v;
}

// his registry entry (cc50.gml): every place the game's battle code and the hub's menus need him
function knight_fl_register()
{
    var _a = knight_fl_a();
    return knight_cc_register({
        cid: 5, key: "flowery", name: "Flowery", short: "F", pron: "him",
        // HP bar: Chapter 5's own colour for him (189950 = #FEE502); his FIGHT bar box and damage numbers in gold too
        color: 189950, bar: merge_color(189950, c_orange, 0.3), dmtype: 6,
        head: _a.head, head_dy: -11, menu_dx: -4, menu_dy: -8, bname: _a.bname, bname_ja: _a.bname_ja,
        eqchar: _a.eqchar, eq_dx: 6, eq_dy: -8,
        walk: [_a.walk_d, _a.walk_r, _a.walk_u, _a.walk_l],
        width: 30, height: 47,
        poses: { normal: _a.walk, idle: _a.idle, act: _a.act, actready: _a.act, attack: _a.attack, attackready: _a.ready, defend: _a.defend,
                 hurt: _a.hurt, defeat: _a.defeat, item: _a.item, itemready: _a.item, spell: _a.spell, spellready: _a.spellready, victory: _a.victory },
        // obj_heroparent's frame counts for his poses (wind-up 0-3, the punch 4-6; the power-up 0-4)
        frames: { attack: 6, attackspeed: 0.5, item: 0, spell: 4 },  // attack: frame 6 is his stance again
        hitfx: _a.hitfx, pressfront: _a.pressfront, sound_pitch: 1.25,
        // his face (Chapter 5's spr_face_flowery, 35 expressions; face number 23 as in Chapter 5) and his voice (his blips)
        face_code: "F", fc: 23, face: asset_get_index("spr_face_flowery"), face_dx: 8, face_dy: 0,
        voice: [asset_get_index("snd_flowery_voicenoise_1"), asset_get_index("snd_flowery_voicenoise_2"), asset_get_index("snd_flowery_voicenoise_3")],
        spells: [16, 17, 18, 19, 20, 21], opt: [24], action: 27, extra: [22, 23, 25, 26, 28, 29, 30], flurry: _a.jarona,
        gear: { weapon: [30], armor: [30, 31], start: [30, 30, 31] },
        stats: knight_fl_stats, onbegin: knight_fl_begin, tick: knight_fl_tick, taken: knight_fl_taken,
        spellinfo: knight_fl_spellinfo, spell: knight_fl_spell, spelltext: knight_fl_spelltext, kspell: knight_fl_kspell_tick,
        weaponinfo: knight_fl_weaponinfo, armorinfo: knight_fl_armorinfo
    });
}
knight_fl_register();

// ---------- his stats ----------
// Max HP 300 (as asked). AT / DF 90% and MAG 115% of the party's standard (the average of Kris, Susie, Ralsei and Noelle's own
// values at that moment - so they follow the player's file and the hub's stat options); a magic and utility member.
function knight_fl_stats()
{
    var _at = 0, _df = 0, _mg = 0;
    for (var _i = 1; _i <= 4; _i++)
    {
        _at += global.at[_i];
        _df += global.df[_i];
        _mg += global.mag[_i];
    }
    global.maxhp[5] = 300;
    global.at[5] = max(1, round((_at / 4) * 0.9));
    global.df[5] = max(0, round((_df / 4) * 0.9));
    global.mag[5] = max(1, round((max(_mg / 4, 4)) * 1.15));
    return 1;
}

// ---------- his gear (Chapter 5's names; Chapter 5 shows them only, so the stats are the hub's) ----------
function knight_fl_weaponinfo(_id)
{
    if (_id != 30)
        return 0;
    weaponnametemp = "WinningSmile";
    weapondesctemp = "Flowery's own smile. It wins every#heart it meets. Only he can use it.";
    wmessage2temp = "Heh.";
    wmessage3temp = "Heh.";
    wmessage4temp = "Heh.";
    weaponattemp = 14;
    weaponmagtemp = 16;
    weapondftemp = 2;
    weaponstyletemp = "smile";
    weaponicontemp = 21;
    return 1;
}

function knight_fl_armorinfo(_id)
{
    if (_id == 30)
    {
        armornametemp = "PetalMantle";
        armordesctemp = "A mantle of soft petals.#Only Flowery wears it well.";
        armordftemp = 10;
        armormagtemp = 8;
        armorattemp = 3;
        armoricontemp = 4;
        return 1;
    }
    if (_id == 31)
    {
        armornametemp = "SundayBest";
        armordesctemp = "Flowery's finest vest and tie.#Only Flowery wears it.";
        armordftemp = 11;
        armorattemp = 5;
        armormagtemp = 5;
        armoricontemp = 4;
        return 1;
    }
    return 0;
}

// ---------- his voice ----------
// one of his clips, by name (never stops another clip: no line is cut short)
// the same line asked for again within 2 seconds is not played twice (his transformation used to say OMEGA FLOWERY! twice)
global.knight_fl_vlast = -1;
global.knight_fl_vname = "";
global.knight_fl_vtime = -100000;
function knight_fl_voice(_name)
{
    var _s = asset_get_index("snd_flowery_voiceclip_" + _name);
    if (_s < 0 || !audio_exists(_s))
        return -1;
    if (_name == global.knight_fl_vname && (current_time - global.knight_fl_vtime) < 2000)
        return -1;
    global.knight_fl_vname = _name;
    global.knight_fl_vtime = current_time;
    global.knight_fl_vlast = snd_play(_s);
    return global.knight_fl_vlast;
}

function knight_fl_snd(_name)
{
    var _s = asset_get_index(_name);
    if (_s < 0 || !audio_exists(_s))
        return -1;
    return snd_play(_s);
}

// ---------- the fight ----------
// turn-long effects: Ez2Dance (the party's SOUL), Afinihug (one member), Honey Kiss (the knight) - each armed when cast, on for
// the next enemy turn (global.mnfight == 2), gone once it ends; casting again never stacks
function knight_fl_begin()
{
    global.knight_fl_fxs = { dance: 0, hug: [0, 0, 0], charm: 0, wlast: -1, wbase: -1, t: 0 };
    // the Violet Knight's last stand: off at the start of every fight
    var _n0 = 0;
    var _p0 = [];
    for (var _ci = 0; _ci < 3; _ci++)
    {
        if (global.char[_ci] != 0)
        {
            _n0++;
            array_push(_p0, global.char[_ci]);
        }
    }
    global.knight_fl_om = { on: false, trig: false, cd: 0, mn: -1, wait: 0, fol: noone, fol2: noone, n0: _n0, p0: _p0, pose: undefined, ft: 0, gt: -1, gx0: 0, gy0: 0, hx: 0, hy: 0 };
    knight_fl_om_undress();
    global.knight_fl_fj = undefined;
    global.knight_fl_song = "";
    global.knight_fl_actmenu = 0;
    global.knight_fl_chk = 0;
    return 1;
}

function knight_fl_fx()
{
    if (!variable_global_exists("knight_fl_fxs") || !is_struct(global.knight_fl_fxs))
        knight_fl_begin();
    return global.knight_fl_fxs;
}

// 0 off, 1 armed (cast this turn), 2 on (the enemy turn); an armed effect turns on when the enemy turn starts, an on one ends with it
function knight_fl_fx_step(_v, _mn)
{
    if (_v == 1 && _mn == 2)
        return 2;
    if (_v == 2 && _mn != 2)
        return 0;
    return _v;
}

function knight_fl_tick()
{
    if (!variable_global_exists("mnfight") || !instance_exists(obj_battlecontroller))
        return 0;
    var _f = knight_fl_fx();
    var _mn = global.mnfight;
    _f.dance = knight_fl_fx_step(_f.dance, _mn);
    for (var _i = 0; _i < 3; _i++)
        _f.hug[_i] = knight_fl_fx_step(_f.hug[_i], _mn);
    _f.charm = knight_fl_fx_step(_f.charm, _mn);
    _f.t++;
    // his guards shown: Afinihug's shield on the hugged member, Honey Kiss's charm on the foe (while they last)
    for (var _gi = 0; _gi < 3; _gi++)
        knight_om_guard_set(_gi, 5, global.charinstance[_gi], _f.hug[_gi] > 0 && global.char[_gi] != 0 && global.hp[global.char[_gi]] > 0);
    knight_om_guard_set(3, 6, instance_find(obj_knight_enemy, 0), _f.charm > 0);
    // his FIGHT (one Jarona) and his last stand (the Violet Knight)
    knight_fl_fight_tick();
    knight_fl_om_tick();
    knight_fl_vis_guard();
    knight_fl_act_tick();
    // EZ2DANCE: the SOUL moves about 10% faster (one more pixel on 2 frames out of 5); its own speed comes back afterwards
    if (instance_exists(obj_heart))
    {
        var _h = instance_find(obj_heart, 0);
        if (_f.dance == 2)
        {
            if (_f.wlast < 0 || _h.wspeed != _f.wlast)
                _f.wbase = _h.wspeed;
            _h.wspeed = _f.wbase + (((_f.t mod 5) < 2) ? 1 : 0);
            _f.wlast = _h.wspeed;
        }
        else if (_f.wlast >= 0)
        {
            if (_h.wspeed == _f.wlast)
                _h.wspeed = _f.wbase;
            _f.wlast = -1;
        }
    }
    return 1;
}

// a hit on party slot _slot: Afinihug's guard on that member (-20%), Honey Kiss's charm on the knight (-15% for everyone)
function knight_fl_taken(_d, _slot)
{
    if (!variable_global_exists("knight_fl_fxs") || !is_struct(global.knight_fl_fxs))
        return _d;
    var _f = global.knight_fl_fxs;
    var _o = _d;
    if (_slot >= 0 && _slot < 3 && _f.hug[_slot] > 0)
        _o = _o * 0.8;
    if (_f.charm > 0)
        _o = _o * 0.85;
    // OMEGA FLOWERY: 25% less damage taken
    if (knight_fl_om_on() && _slot >= 0 && _slot < 3 && global.char[_slot] == 5)
        _o = _o * 0.75;
    return ceil(_o);
}

// ---------- F-ACTION: his own ACTION (technique 22, 0 TP) - the party's TP up (as much as a DEFEND), his line ----------
// a line of his in the battle box: his face (Chapter 5's portraits, expression _e) and his voice
// His line goes in a speech balloon in front of him (like Susie's), in his own voice; the battle box says what he did, in
// the battle's own text (no face, its own voice) - his name as the fight calls him (the Violet Knight: The Flower Man).
// _bal: the balloon's line ('&' breaks it); _did: "used SANFRANDISCO!" and so on; _narr: a second line for the box.
function knight_fl_say(_e, _bal, _did, _narr)
{
    var _box = "* " + knight_charname(5) + " " + _did;
    if (_narr != "")
        _box += "&" + _narr;
    _box += "/%";
    // (no speech balloon for his moves: his voice clips say it - the battle box says what he did)
    knight_cc_say(5, _e, _box, "");
    return _box;
}

// (the TP comes with the cast - knight_fl_spell; this is the line, with the clip he says in it)
function knight_fl_faction()
{
    if (!variable_global_exists("knight_fl_fan"))
        global.knight_fl_fan = 0;
    var _k = global.knight_fl_fan mod 4;
    switch (_k)
    {
        case 0:
            knight_fl_voice("give_to_you");
            return knight_fl_say(0, "Watch this.&It's good&for you./%", "cheered everyone on!", "* Everyone's TP went up!");
        case 1:
            knight_fl_voice("leaf_it_to_me");
            return knight_fl_say(2, "Hey team!&Leaf it&to me./%", "cheered everyone on!", "* Everyone's TP went up!");
        case 2:
            knight_fl_voice("try_my_flavor");
            return knight_fl_say(8, "Have a taste&of my flavor,&everyone!/%", "cheered everyone on!", "* Everyone's TP went up!");
    }
    knight_fl_voice("thatsgreat");
    return knight_fl_say(16, "That's berry&good,&everyone!/%", "cheered everyone on!", "* Everyone's TP went up!");
}

// ---------- his techniques (16-21) and F-Action (22) ----------
function knight_fl_spell_info(_id)
{
    switch (_id)
    {
        case 16: return { name: "Sanfrandisco", descb: "Flash#Kick", desc: "Here he comes! A flashing crescent#kick at one foe. Costs nothing.", target: 2, cost: 0 };
        case 17: return { name: "MyJarona", descb: "Blue#Rush", desc: "His blue rush: he dashes, crouches and#crescent-kicks again and again. One foe.", target: 2, cost: 125 };
        case 18: return { name: "Ez2Dance", descb: "SOUL#Speed", desc: "A spiral dance. On the next enemy#turn the SOUL moves 10% faster.", target: 0, cost: 50 };
        case 19: return { name: "PrismRush", descb: "OMEGA#Rush", desc: "OMEGA FLOWERY! Every flower's light#in one final rush at one foe.", target: 2, cost: 250 };
        case 20: return { name: "Afinihug", descb: "Guard#ally", desc: "A big hug: on the next enemy turn#that ally takes 20% less damage.", target: 1, cost: 88 };
        case 21: return { name: "HoneyKiss", descb: "Charm#+Heal", desc: "Charms the foe (MERCY up, or its#next attack -15%) and heals the#team 12% of their HP.", target: 2, cost: 100 };
        case 25: return { name: "SmileAgain", descb: "Heal#40%", desc: "OMEGA FLOWERY smiles again: he (and#anyone still up) heals 40% HP.", target: 0, cost: 80 };
        case 24: return { name: "OmegaForm", descb: "Become#OMEGA", desc: "He becomes OMEGA FLOWERY for the#rest of the fight (MAGIC: LAST#JARONA + PRISM RUSH only).", target: 0, cost: 100 };
        case 22: return { name: "F-Action", descb: "TP#+32%", desc: "Flowery's own ACTION: he cheers#the team on - TP +32%.", target: 0, cost: 0 };
        // build 50: his ACT (the first MAGIC entry) opens his ACT list in the MAGIC menu, like Kris's ACT entry does
        case 27: return { name: "ACT", descb: "Open#ACTs", desc: "Flowery's ACTs: Check, HoldBreath,#F-Action (and Unleash / Bravery#when the SOUL can shine).", target: 0, cost: 0 };
        case 28: return { name: "Check", descb: "Check#enemy", desc: "He takes a good look at the foe.", target: 0, cost: 0 };
        case 29: return { name: "HoldBreath", descb: "SOUL#faster", desc: "He holds his breath: the SOUL#moves faster.", target: 0, cost: 0 };
        case 26: return { name: "Unleash", descb: "Reveal#Enemy", desc: "Your SOUL's light through Flowery:#reveals the Knight (as Kris's#Unleash does).", target: 0, cost: 200 };
        case 30: return { name: "Bravery", descb: "Graze size#way up", desc: "Gathers courage: GRAZE SIZE up#this turn.", target: 0, cost: 12.5 };
        case 23:
            // LAST JARONA: 100% TP, no charging (in the Omega form one of his only two moves, with PRISM RUSH)
            if (knight_fl_om_on())
                return { name: "LastJarona", descb: "Final#Jarona", desc: "OMEGA FLOWERY's LAST JARONA: three#rushes at one foe.", target: 2, cost: 100 };
            return { name: "LastJarona", descb: "Final#Jarona", desc: "His LAST JARONA: everything he has#in three rushes at one foe.", target: 2, cost: 100 };
    }
    return undefined;
}

// scr_spellinfo (self: the caller)
function knight_fl_spellinfo(_id)
{
    var _i = knight_fl_spell_info(_id);
    if (is_undefined(_i))
        return 0;
    spellname = _i.name;
    spellnameb = _i.name;
    spelldescb = _i.descb;
    spelldesc = _i.desc;
    spelltarget = _i.target;
    cost = _i.cost;
    spellusable = 0;
    return 1;
}

// his attacks: a share of a basic attack (AT) plus his MAG - Sanfrandisco ~0.85 of a good FIGHT hit, My Jarona ~1.6, Prism
// Rush ~2.5 (spread over its hits). The knight's own damage reduction (blocking, phases) applies like it does to a FIGHT hit.
function knight_fl_dmg(_caster, _star, _at, _mg)
{
    var _d = ceil((global.battleat[_caster] * _at) + (global.battlemag[_caster] * _mg) - (global.monsterdf[_star] * 3));
    // the knight's damage reduction as the game's own spells take it (scr_spell: reduction + 0.65)
    if (global.chapter == 3 && i_ex(obj_knight_enemy) && variable_instance_exists(obj_knight_enemy, "damagereduction"))
        _d = ceil(_d * (obj_knight_enemy.damagereduction + 0.65));
    if (global.automiss[_star] == 1)
        _d = 0;
    return max(1, _d);
}

// scr_spell (self: the battle's spell code; _caster the party slot, _star the target)
function knight_fl_spell(_id, _caster, _star)
{
    switch (_id)
    {
        case 16:
        case 17:
        case 19:
        case 21:
        case 23:
            if (global.monster[_star] == 0)
                scr_retarget_spell();
            break;
    }
    var _k = undefined;
    switch (_id)
    {
        case 16:
            knight_kspell_start(20, _caster, _star, knight_fl_dmg(_caster, _star, 4.4, 0.8));
            global.spelldelay = 50;
            break;
        case 17:
            knight_kspell_start(21, _caster, _star, knight_fl_dmg(_caster, _star, 8, 2.5));
            global.spelldelay = 125;
            break;
        case 18:
            knight_kspell_start(22, _caster, 0, 0);
            global.spelldelay = 60;
            break;
        case 19:
            // (as OMEGA FLOWERY it hits half as hard again)
            knight_kspell_start(23, _caster, _star, knight_fl_dmg(_caster, _star, knight_fl_om_on() ? 18 : 12, knight_fl_om_on() ? 6.75 : 4.5));
            global.spelldelay = knight_fl_om_on() ? 200 : 390;
            break;
        case 20:
            knight_kspell_start(24, _caster, _star, 0);
            global.spelldelay = 55;
            break;
        case 21:
            knight_kspell_start(25, _caster, _star, 0);
            global.spelldelay = 105;
            break;
        case 25:
            // SMILE AGAIN (OMEGA FLOWERY's heal)
            knight_kspell_start(31, _caster, 0, 0);
            global.spelldelay = 70;
            break;
        case 24:
            // OMEGA FORM (an optional technique): his transformation, then OMEGA FLOWERY for the rest of the fight
            knight_kspell_start(30, _caster, 0, 0);
            global.spelldelay = 215;
            break;
        case 23:
            // LAST JARONA (the Violet Knight's finisher when Flowery is the one left on top)
            knight_kspell_start(27, _caster, _star, knight_fl_dmg(_caster, _star, 18, 6));
            global.spelldelay = 180;
            break;
        case 27:
            // (the ACT entry opens his ACT list - knight_kris_actpick; it is never cast)
            global.spelldelay = 1;
            break;
        case 28:
            // CHECK
            knight_kspell_start(26, _caster, 0, 0);
            global.spelldelay = 30;
            break;
        case 29:
            // HOLDBREATH: the knight's own hold-breath counter (the SOUL moves faster, as Kris's ACT does)
            with (obj_knight_enemy)
            {
                if (variable_instance_exists(id, "holdbreathcount"))
                    holdbreathcount = 1;
            }
            knight_kspell_start(26, _caster, 0, 0);
            global.spelldelay = 30;
            break;
        case 30:
            // BRAVERY (the Elec Knight's phase 5)
            snd_play(snd_boost);
            with (obj_knight_enemy)
            {
                if (variable_instance_exists(id, "braveried"))
                    braveried = true;
            }
            knight_kspell_start(26, _caster, 0, 0);
            global.spelldelay = 30;
            break;
        case 26:
            // UNLEASH (the Elec Knight's phase 5): the purify light from him, as Kris's / Susie's Unleash; the spell phase waits for it
            knight_kspell_start(32, _caster, 0, 0);
            global.spelldelay = 20;
            break;
        case 22:
            // F-ACTION: the party's TP up (as much as a DEFEND gives); its line is the spell text's
            if (!variable_global_exists("knight_fl_fan"))
                global.knight_fl_fan = 0;
            global.knight_fl_fan++;
            global.tension = min(global.maxtension, global.tension + round(global.maxtension * 0.32));
            snd_play(snd_boost);
            knight_kspell_start(26, _caster, 0, 0);
            global.spelldelay = 30;
            break;
    }
    knight_fl_ks_init();
    return 1;
}

// scr_spelltext: what the battle says as he casts - in his own voice, with his face (one page each: the spell text is never
// waited on)
function knight_fl_spelltext(_id)
{
    switch (_id)
    {
        case 16: return knight_fl_say(2, "Here I come..&SANFRANDISCO!/%", "used SANFRANDISCO!", "");
        case 17: return knight_fl_say(16, "Watch closely!&It's my&JARONA!/%", "used MY JARONA!", "");
        case 18: return knight_fl_say(8, "Spiral&dance!/%", "used EZ2DANCE!", "* The SOUL feels light!");
        case 19: return knight_fl_say(21, "Everyone!&Lend me&your power!/%", "used PRISM RUSH!", "");
        case 20: return knight_fl_say(8, "Flowers bloom&in your&heart!/%", "gave a big hug!", "");
        case 21: return knight_fl_say(26, "Don't worry..&I'm a&gentleman./%", "blew a kiss!", "* Everyone feels better!");
        case 22: return knight_fl_faction();
        case 27: return "* .../%";
        case 28:
            if (!variable_global_exists("knight_fl_chk"))
                global.knight_fl_chk = 0;
            global.knight_fl_chk++;
            if (global.knight_fl_chk == 1)
                return knight_fl_say(2, "", "analyzed the enemy!", "* But " + knight_charname(5) + " couldn't learn anything.");
            return knight_fl_say(2, "", "points into the distance.", "* Nothing happened.");
        case 29:
            if (knight_fl_breath() > 0)
                return knight_fl_say(2, "", "held his breath...", "* He felt dizzy. Nothing happened.");
            return knight_fl_say(2, "", "held his breath.", "* His heartbeat quickened. The SOUL now moves faster.");
        case 30: return knight_fl_say(2, "", "gathered courage...", "* GRAZE SIZE increased this turn!");
        case 26:
            if (knight_fl_unleash_ok())
                return "* Your SOUL emitted a brilliant light!/%";
            return knight_fl_say(2, "", "reached out to the SOUL...", "* But nothing happened.");
        case 23: return knight_fl_say(21, "This is it..&My LAST&JARONA!/%", "used LAST JARONA!", "");
        case 24: return knight_fl_say(21, "With your&powers&combined.../%", "became OMEGA FLOWERY!", "");
        case 25: return knight_fl_say(8, "Smile&again!/%", "smiled again!", "* HP was restored!");
    }
    return "* .../%";
}

// ---------- the moves ----------
// a pose of his own (a marker; his sprites are anchored like his hero's, so at the hero's x / y he stands exactly where it does).
// _frame: the frame shown (-1: animate at _spd)
function knight_fl_mk(_k, _spr, _x, _y, _frame, _spd)
{
    if (!knight_cc_spr(_spr))
        return noone;
    var _a0 = knight_fl_a();
    if ((_spr == _a0.omega || knight_fl_om_on()) && knight_cc_spr(_a0.omega))
    {
        // Omega Flowery (obj_knight_omega draws him as Chapter 5 does); once he is Omega for good, every pose of his
        // shows as its Omega frame
        var _om = knight_om_make(0, _x, _y);
        _om.sprite_index = _a0.omega;
        _om.srcspr = (_spr == _a0.omega) ? -1 : _spr;
        _om.image_index = max(0, _frame);
        _om.image_speed = (_frame < 0) ? _spd : 0;
        _om.depth = -5;
        array_push(_k.fl, _om);
        return _om;
    }
    var _m = scr_dark_marker(_x, _y, _spr);
    _m.image_index = max(0, _frame);
    _m.image_speed = (_frame < 0) ? _spd : 0;
    _m.depth = -5;
    array_push(_k.fl, _m);
    return _m;
}

function knight_fl_hero(_k)
{
    var _s = _k.caster;
    if (_s < 0 || _s > 2 || !i_ex(global.charinstance[_s]))
        return noone;
    return global.charinstance[_s];
}

// his hero hides while a move shows him (its place kept in _k.fx / fy)
function knight_fl_hide(_k)
{
    var _h = knight_fl_hero(_k);
    if (!i_ex(_h))
        return 0;
    _k.fx = _h.x;
    _k.fy = _h.y;
    _h.image_alpha = 0;
    return 1;
}

// the move is over (or the fight is): every marker of it goes, his hero is back
function knight_fl_end(_k)
{
    for (var _i = 0; _i < array_length(_k.fl); _i++)
    {
        if (i_ex(_k.fl[_i]))
        {
            with (_k.fl[_i])
                instance_destroy();
        }
    }
    _k.fl = [];
    var _h = knight_fl_hero(_k);
    if (i_ex(_h))
    {
        // (in his last-stand Omega form his hero wears the Omega poses itself)
        _h.image_alpha = 1;
        _h.image_blend = c_white;
    }
    if (variable_struct_exists(_k, "kris") && i_ex(_k.kris))
        _k.kris.image_alpha = 1;
    if (variable_struct_exists(_k, "wind") && is_numeric(_k.wind) && _k.wind >= 0)
        audio_stop_sound(_k.wind);
    if (variable_struct_exists(_k, "km") && i_ex(_k.km))
    {
        with (_k.km)
            instance_destroy();
        with (obj_knight_enemy)
            visible = 1;
    }
    global.knight_ks = undefined;
    return 1;
}

function knight_fl_drop(_k, _m)
{
    if (i_ex(_m))
    {
        with (_m)
            instance_destroy();
    }
    return noone;
}

// Chapter 5's rainbow (flrainbow)
function knight_fl_rainbow(_i)
{
    var _r = [255, 45311, 65535, 3663159, 16773632, 15623011, 16711922];
    return _r[((_i mod 7) + 7) mod 7];
}

// an afterimage of a marker (_col tint), like the runner's rainbow fog
function knight_fl_trail(_m, _col)
{
    if (!i_ex(_m))
        return noone;
    if (_m.object_index == obj_knight_omega)
    {
        // Omega Flowery's afterimages: his frame as one solid colour (scr_afterimage_monochrome), quick to fade
        var _oi = instance_create_depth(_m.x, _m.y, _m.depth + 1, obj_afterimage);
        _oi.sprite_index = _m.sprite_index;
        _oi.image_index = knight_om_frame(_m.srcspr, _m.image_index);
        _oi.image_xscale = _m.image_xscale;
        _oi.image_yscale = _m.image_yscale;
        _oi.image_blend = _col;
        _oi.image_alpha = 0.5 * _m.a;
        _oi.fadeSpeed = 0.12;
        return _oi;
    }
    var _ai = instance_create_depth(_m.x, _m.y, _m.depth + 1, obj_afterimage);
    _ai.sprite_index = _m.sprite_index;
    _ai.image_index = _m.image_index;
    _ai.image_xscale = _m.image_xscale;
    _ai.image_yscale = _m.image_yscale;
    _ai.image_blend = _col;
    _ai.image_alpha = 0.7;
    _ai.fadeSpeed = 0.08;
    return _ai;
}

// a one-shot effect (removes itself when its animation ends)
function knight_fl_fx1(_spr, _x, _y, _sc, _col, _spd)
{
    if (!knight_cc_spr(_spr))
        return noone;
    var _e = instance_create(_x, _y, obj_marker_animateOnce);
    _e.sprite_index = _spr;
    _e.image_index = 0;
    _e.image_speed = _spd;
    _e.image_xscale = _sc;
    _e.image_yscale = _sc;
    _e.image_blend = _col;
    _e.depth = -20;
    return _e;
}

// one hit on the foe: the slash mark, the sound, the damage (its own number)
function knight_fl_hit(_k, _d, _col, _first)
{
    if (global.monster[_k.star] != 1 || global.monsterhp[_k.star] <= 0)
        return 0;
    var _p = knight_kspell_pos(_k.star);
    var _att = instance_create(_p[0] + irandom_range(-20, 20), _p[1] + irandom_range(-20, 20), obj_basicattack);
    _att.image_xscale = choose(2, -2);
    _att.image_yscale = 2;
    _att.image_blend = _col;
    snd_pitch(snd_play(snd_damage), 0.9 + random(0.3));
    caster = _k.caster;
    if (_first)
        global.hittarget[_k.star] = 0;
    scr_damage_enemy(_k.star, max(1, _d));
    return 1;
}

// the TP a FIGHT-like hit gives (Sanfrandisco: a little, through the game's own TP gain)
function knight_fl_tp(_n)
{
    global.tension = min(global.maxtension, global.tension + _n);
    return 1;
}

// knight_kspell kinds 20-26 (global.knight_ks.cc == 5)
function knight_fl_kspell_tick(_k)
{
    // the fight ended in the middle of a move (or a move ran far past its length): everything of it goes, nothing is left
    if (!instance_exists(obj_battlecontroller) || _k.t > 600)
        return knight_fl_end(_k);
    var _a = knight_fl_a();
    var _p = knight_kspell_pos(_k.star);
    if (_k.t == 1)
        knight_fl_hide(_k);
    var _hx = _k.fx, _hy = _k.fy;
    switch (_k.kind)
    {
        case 20:
            // SANFRANDISCO - his flash kick, in his place: the ready stance (1-8), a beat in the crouch (9-14), the crescent
            // kick (15) sending his crescent across at the foe in a rainbow trail (15-20), the hit when it gets there (21),
            // the kick held, then the crouch and back to his stance
            if (_k.t == 1)
            {
                knight_fl_voice("hereicomesanfrandisco_strong");
                _k.m = knight_fl_mk(_k, _a.flashkick, _hx, _hy, 0, 0);
            }
            if (_k.t == 9 && i_ex(_k.m))
                _k.m.image_index = 1;
            if (_k.t == 15)
            {
                if (i_ex(_k.m))
                    _k.m.image_index = 2;
                snd_play(snd_swing);
                knight_fl_snd("snd_ultraswing");
                _k.w = knight_fl_mk(_k, _a.crescent, _hx + 50, _hy + 30, 0, 0);
                if (i_ex(_k.w))
                {
                    var _cx2 = _p[0] - 40, _cy2 = _p[1] - 40;
                    with (_k.w)
                    {
                        scr_lerpvar("x", x, _cx2, 6, 2, "in");
                        scr_lerpvar("y", y, _cy2, 6, 2, "in");
                    }
                }
            }
            if (_k.t > 15 && _k.t < 21 && i_ex(_k.w))
                knight_fl_trail(_k.w, knight_fl_rainbow(_k.t));
            if (_k.t == 21)
            {
                _k.w = knight_fl_drop(_k, _k.w);
                knight_fl_fx1(_a.hitfx, _p[0], _p[1], 3, c_white, 0.5);
                knight_fl_hit(_k, _k.dmg, c_yellow, true);
                knight_fl_tp(5);
            }
            if (_k.t == 30 && i_ex(_k.m))
                _k.m.image_index = 1;
            if (_k.t == 36 && i_ex(_k.m))
                _k.m.image_index = 0;
            if (_k.t >= 44)
                knight_fl_end(_k);
            break;
        case 21:
            // MY JARONA - Chapter 5's Jarona rush (obj_orangeheart_floweryjarona), three charges, 30 frames each: the wind-up
            // with a white flash ("Jarona!"), the lunge at the foe punching, blue, with blue afterimages; CONTACT (the hit
            // lands on the frame he reaches the foe: a blue flash, a shockwave and the crescent at the foe; 25% / 30% / 45%
            // of the damage); knocked back, sliding back to his place as the blue fades - and charging again. Then his pose:
            // "Heh. It's my Jarona."
            if (_k.t == 1)
                _k.m = knight_fl_mk(_k, knight_cc_spr(_a.jarona) ? _a.jarona : _a.attack, _hx, _hy, 0, 0);
            if (_k.t >= 4 && _k.t < 94 && i_ex(_k.m))
            {
                var _st = (_k.t - 4) mod 30;
                var _n = (_k.t - 4) div 30;
                var _blue = make_color_rgb(70, 130, 255);
                // [Z] just before he connects (the gold ring closing on the foe): a STRONG Jarona, x1.5
                knight_fl_jz(_k, _n, _st, 4, 12, 15);
                if (_st == 12)
                    knight_om_ring(_p[0], _p[1], 60, 12, 3, make_color_rgb(255, 220, 90), 3);
                if (_st == 0)
                {
                    _k.m.x = _hx;
                    _k.m.image_index = 0;
                    _k.m.image_blend = c_white;
                    with (_k.m)
                        scr_oflash();
                    knight_fl_voice("jarona" + string(_n + 1));
                    snd_pitch(snd_play(snd_boost), 1 + (_n * 0.08));
                }
                if (_st < 10)
                    _k.m.image_index = min(4, _st div 2);
                if (_st == 10)
                {
                    // the lunge: a short burst (ease in), at the foe on frame 15
                    _k.m.image_index = 5;
                    _k.m.image_blend = _blue;
                    var _lx = _p[0] - 100;
                    with (_k.m)
                        scr_lerpvar("x", x, _lx, 5, 2, "in");
                    snd_play(snd_swing);
                }
                if (_st > 10 && _st <= 15)
                {
                    var _ai = knight_fl_trail(_k.m, _blue);
                    if (i_ex(_ai))
                        _ai.image_alpha = 0.45;
                }
                if (_st == 15)
                {
                    var _sh = [0.25, 0.3, 0.45];
                    var _dd = (_n < 2) ? ceil(_k.dmg * _sh[_n]) : (_k.dmg - ceil(_k.dmg * 0.25) - ceil(_k.dmg * 0.3));
                    if (_k.zb[_n] == 1)
                    {
                        _dd = ceil(_dd * 1.5);
                        knight_om_ring(_p[0], _p[1], 6, 110, 5, make_color_rgb(255, 220, 90), 12);
                        knight_fl_snd("snd_bell");
                        if (_n < 2)
                            instance_create(0, 0, obj_shake);
                    }
                    knight_fl_fx1(_a.hitfx, _p[0], _p[1], 2.5, _blue, 0.5);
                    knight_fl_fx1(_a.shock, _p[0] - 30, _p[1] + 60, 1.5, merge_color(c_aqua, c_blue, 0.3), 0.5);
                    if (variable_global_exists("knight_om_surf"))
                        knight_om_orb(_p[0] - 20, _p[1], 4, 26, merge_color(_blue, c_white, 0.5), 8);
                    knight_fl_snd("snd_punchheavythunder");
                    if (_n == 2)
                        instance_create(0, 0, obj_shake);
                    knight_fl_hit(_k, _dd, _blue, (_n == 0));
                }
                if (_st == 18)
                {
                    // knocked back to his place
                    _k.m.image_index = 6;
                    var _hx2 = _hx;
                    with (_k.m)
                        scr_lerpvar("x", x, _hx2, 10, 2, "out");
                }
                if (_st > 18)
                    _k.m.image_blend = merge_color(_blue, c_white, (_st - 18) / 10);
            }
            if (_k.t == 94)
            {
                _k.m = knight_fl_drop(_k, _k.m);
                _k.m = knight_fl_mk(_k, _a.pose, _hx, _hy, 0, 0);
                knight_fl_voice("heh_it_s_my_jarona");
                snd_play(snd_great_shine);
            }
            if (_k.t >= 116)
                knight_fl_end(_k);
            break;
        case 22:
            // EZ2DANCE - his pirouette into his spin-to-idle flourish, in rainbow afterimages
            if (_k.t == 1)
            {
                knight_fl_voice("spiral_dance");
                _k.m = knight_fl_mk(_k, _a.dance, _hx, _hy, 0, 0);
            }
            if (i_ex(_k.m) && _k.t < 56)
            {
                _k.m.image_index = min(15, _k.t div 3.5);
                if ((_k.t mod 3) == 0 && _k.t < 30)
                    knight_fl_trail(_k.m, knight_fl_rainbow(_k.t div 3));
            }
            if (_k.t == 30)
            {
                snd_play(snd_power);
                var _f = knight_fl_fx();
                _f.dance = 1;
            }
            if (_k.t >= 60)
                knight_fl_end(_k);
            break;
        case 23:
            // PRISM RUSH: "Everyone! Lend me your power!" - the other flowers (Aqua, Seth, Orange, Green, Blue, Yellow, Pink,
            // as his Chapter 5 fight brings them in) appear in a ring round him, sending sparkles of their colours into him while
            // he kneels and powers up; one after another they flash and fly into him in trails of their colour; he rises
            // pointing up in a burst of every colour - OMEGA FLOWERY, in a soft rainbow: three rushes through the foe, each
            // hit in a flower's colour (LAST JARONA), the clash (Kris jumps in when Kris is in the party), the wind-up and
            // the final punch; then he is himself again
            knight_fl_prism(_k, _a, _p, _hx, _hy);
            break;
        case 24:
            // AFINIHUG: arms wide (his pose) - a big hug: that ally glows gold and is guarded on the next enemy turn
            if (_k.t == 1)
            {
                knight_fl_voice("flowers_blooms_in_your_heart");
                _k.m = knight_fl_mk(_k, _a.victory, _hx, _hy, 0, 0);
            }
            if (_k.t == 18)
            {
                var _ts = clamp(_k.star, 0, 2);
                var _f2 = knight_fl_fx();
                _f2.hug[_ts] = 1;
                if (i_ex(global.charinstance[_ts]))
                {
                    with (global.charinstance[_ts])
                    {
                        scr_oflash();
                        var _ai2 = instance_create_depth(x, y, depth - 1, obj_afterimage_grow);
                        _ai2.sprite_index = sprite_index;
                        _ai2.image_index = image_index;
                        _ai2.image_xscale = 2;
                        _ai2.image_yscale = 2;
                        _ai2.image_blend = 189950;
                    }
                }
                snd_play(snd_power);
            }
            if (_k.t >= 44)
                knight_fl_end(_k);
            break;
        case 25:
            // HONEY KISS - his blow kiss from Chapter 5: the kiss pose, a step in and back with a gust ("Prism Blow!"), and a
            // stream of spinning petals blown across to the foe on the wind; the foe reels
            if (_k.t == 1)
            {
                knight_fl_voice("prism_blow");
                _k.m = knight_fl_mk(_k, _a.kiss, _hx, _hy, 0, 0);
                if (i_ex(_k.m))
                {
                    _k.m.image_speed = 1 / 6;
                    _k.m.speed = 4;
                    _k.m.direction = 0;
                    _k.m.friction = 0.5;
                }
                snd_play(snd_wing);
            }
            if (_k.t == 9 && i_ex(_k.m))
            {
                _k.m.speed = 10;
                _k.m.direction = 180;
                _k.m.friction = 0.5;
                snd_pitch(snd_play(snd_wing), 1.2);
                _k.wind = knight_fl_snd("snd_strongwind_loop");
                if (_k.wind >= 0)
                    audio_sound_gain(_k.wind, 0.2, 0);
            }
            if (_k.t == 12 && i_ex(_k.m))
            {
                _k.m.image_speed = 0;
                _k.m.image_index = 3;
                _k.m.speed = 0;
                _k.m.x = _hx;
            }
            if (_k.t >= 20 && _k.t < 80)
                knight_fl_petal(_k, _a, _hx + 60, _hy + 50);
            if (_k.t == 86)
            {
                for (var _q = 0; _q < array_length(_k.fl); _q++)
                {
                    if (i_ex(_k.fl[_q]) && _k.fl[_q] != _k.m)
                    {
                        with (_k.fl[_q])
                            scr_lerpvar("image_alpha", image_alpha, 0, 12);
                    }
                }
            }
            if (_k.t == 40)
            {
                with (global.monsterinstance[clamp(_k.star, 0, 2)])
                    scr_oflash();
            }
            if (_k.t == 60)
            {
                knight_fl_honey(_k.star);
                knight_fl_team_heal(0.12);
                snd_play(snd_spare);
                if (variable_struct_exists(_k, "wind") && _k.wind >= 0)
                    audio_sound_gain(_k.wind, 0, 500);
            }
            if (_k.t >= 100)
            {
                if (variable_struct_exists(_k, "wind") && _k.wind >= 0)
                    audio_stop_sound(_k.wind);
                knight_fl_end(_k);
            }
            break;
        case 27:
            knight_fl_lastjarona(_k, _a, _p, _hx, _hy);
            break;
        case 28:
            knight_fl_laststand(_k, _a, _p, _hx, _hy);
            break;
        case 29:
            knight_fl_clash(_k, _a, _p, _hx, _hy);
            break;
        case 30:
            knight_fl_omform(_k, _a, _p, _hx, _hy);
            break;
        case 31:
            knight_fl_smile(_k, _a, _p, _hx, _hy);
            break;
        case 32:
            knight_fl_unleash(_k, _a, _hx, _hy);
            break;
        case 26:
            // F-ACTION: his pose, pointing cool (the line and TP came with the text)
            if (_k.t == 1)
                _k.m = knight_fl_mk(_k, _a.act, _hx, _hy, 0, 0);
            if (_k.t == 8 && i_ex(_k.m))
            {
                with (_k.m)
                    scr_oflash();
            }
            if (_k.t >= 26)
                knight_fl_end(_k);
            break;
        default:
            knight_fl_end(_k);
            break;
    }
    return 1;
}

// HONEY KISS's petals (Chapter 5's drop_petal, mirrored to blow toward the foe): a spinning petal on the wind, fading in;
// they fade out at the end of the move and go with it
function knight_fl_petal(_k, _a, _x, _y)
{
    var _ps = asset_get_index("spr_spin_petal");
    if (!knight_cc_spr(_ps))
        return noone;
    var _m = knight_fl_mk(_k, _ps, _x + irandom_range(-10, 10), _y + irandom_range(-20, 20), -1, 0.1 + random(0.2));
    if (!i_ex(_m))
        return noone;
    _m.image_xscale = 2;
    _m.image_yscale = 2;
    _m.image_index = irandom(max(0, sprite_get_number(_ps) - 1));
    _m.hspeed = 5;
    _m.gravity = 0.75;
    _m.gravity_direction = 55 - irandom(110);
    _m.image_alpha = 0;
    with (_m)
        scr_lerpvar("image_alpha", 0, 1, 6);
    return _m;
}

// the six Omega flowers of Chapter 5 (obj_plat_finalflowery's ghosts), in the formation of its scene around him: main
// sprite, overlay, its colour (draw_ghost's colours), its place round him (dx, dy at 2x) and its own hover (Chapter 5's
// ghost offsets: sin(tt * speed + phase) * 6)
function knight_fl_flowers()
{
    return [
        { n: "Aqua",   s: "spr_omegaf_aqua",   o: "spr_omegaf_aqua_o",   c: 16777079, dx: -100, dy: -72, hs: 1.8, hp: 0.4 },
        { n: "Blue",   s: "spr_omegaf_blue",   o: "spr_omegaf_blue_o",   c: 16742263, dx: 0,    dy: -112, hs: 0.8, hp: 2.1 },
        { n: "Green",  s: "spr_omegaf_green",  o: "spr_omegaf_green_o",  c: 7864183,  dx: 104,  dy: -70, hs: 0.6, hp: 0.1 },
        { n: "Seth",   s: "spr_omegaf_seth",   o: "spr_omegaf_seth_o",   c: 16742399, dx: -112, dy: 28,  hs: 1.1, hp: 0.9 },
        { n: "Yellow", s: "spr_omegaf_yellow", o: "spr_omegaf_yellow_o", c: 7864319,  dx: 112,  dy: 30,  hs: 0.8, hp: 2.1 },
        { n: "Orange", s: "spr_omegaf_orange", o: "spr_omegaf_orange_o", c: 7829503,  dx: 0,    dy: 92,  hs: 1.3, hp: 1.6 }
    ];
}

// a flower's colour (Prism Rush's hits, trails and rings are coloured by the flowers' power)
function knight_fl_fcol(_i)
{
    var _f = knight_fl_flowers();
    return _f[((_i mod array_length(_f)) + array_length(_f)) mod array_length(_f)].c;
}

// a soft rainbow (an afterimage / glow colour): Chapter 5's rainbow, softened toward white
function knight_fl_pastel(_i)
{
    return merge_color(merge_color(knight_fl_rainbow(_i div 2), knight_fl_rainbow((_i div 2) + 1), (_i mod 2) * 0.5), c_white, 0.35);
}

// a sparkle of a flower's colour drifting from (_x, _y) toward (_tx, _ty)
function knight_fl_mote(_k, _x, _y, _tx, _ty, _col)
{
    var _ss = asset_get_index("spr_sparestar_anim");
    var _e = knight_fl_fx1(knight_cc_spr(_ss) ? _ss : asset_get_index("spr_bellsparkle"), _x, _y, 2, _col, 0.2);
    if (i_ex(_e))
    {
        _e.direction = point_direction(_x, _y, _tx, _ty);
        _e.speed = point_distance(_x, _y, _tx, _ty) / 24;
    }
    return _e;
}

// is the Omega form on for good (the Violet Knight's last stand)?
function knight_fl_om_on()
{
    return variable_global_exists("knight_fl_om") && is_struct(global.knight_fl_om) && global.knight_fl_om.on;
}

// PRISM RUSH (case 23), a phase after another (each with its frames):
//   1-49    GATHERING: he steps forward into the middle and kneels, powering up ("Lend me your power!"); the six Omega flowers
//           appear one after another, gliding in to their places round him (the formation of Chapter 5's scene)
//   50-79   FORMATION: they hover (each its own hover), sparkles of their colours drifting into him
//   80-99   PREPARATION: they glow full, a ripple in each one's colour, his power-up pulses
//   100-149 TRANSFER: one after another they flash and rush into him in a trail of their colour, shrinking into him
//   150-169 ABSORPTION: he rises pointing up; the colours ring out from him (six ripples)
//   170-189 OMEGA: OMEGA FLOWERY (outline, body and rainbow pass) - his pose, "OMEGA FLOWERY"
//   190-365 ATTACK: power-up with rainbow afterimages, three rushes through the foe (explosions, ripples, an orb at each
//           hit), the clash (Kris jumps in when Kris is in the party), the wind-up, the PRISM punch (three explosions, three
//           ripples, a flash, a shake), and back: he is himself again
// With his last-stand Omega form on (Violet Knight) the transformation is skipped: the attack starts at once and he
// stays Omega Flowery.
function knight_fl_prism(_k, _a, _p, _hx, _hy)
{
    if (_k.t == 1)
    {
        _k.om0 = knight_fl_om_on() ? 189 : 0;
        _k.fx2 = _hx + 96;
        if (_k.om0 > 0 || _k.cut)
            _k.fx2 = _hx;
    }
    var _t = _k.t + _k.om0;
    var _F = _k.fx2;
    var _cx = _F + 22, _cy = _hy + 50;
    var _pu = asset_get_index("spr_knfl_powerup");
    var _bs = asset_get_index("spr_bellsparkle");
    var _fl = knight_fl_flowers();
    var _nf = array_length(_fl);
    if (_t == 1)
    {
        // (not in his transformation scenes: they said "With your powers combined..." just before)
        if (!(variable_struct_exists(_k, "cut") && _k.cut))
            knight_fl_voice("lend_me_your_power");
        knight_fl_snd("snd_flowery_power_up");
        _k.m = knight_fl_mk(_k, knight_cc_spr(_pu) ? _pu : _a.spell, _hx, _hy, 0, 0);
        if (i_ex(_k.m))
        {
            var _fx = _F;
            with (_k.m)
                scr_lerpvar("x", x, _fx, 16, 2, "out");
        }
        _k.rc = [];
        for (var _i = 0; _i < _nf; _i++)
            array_push(_k.rc, noone);
    }
    if (_t < 190)
    {
        // him: kneeling and pulsing, then rising
        if (i_ex(_k.m))
        {
            if (_t < 150)
            {
                _k.m.image_index = (_t div 8) mod 2;
                var _gl = (_t >= 80) ? (0.25 + 0.15 * sin(_t / 3)) : (0.1 + 0.08 * sin(_t / 5));
                _k.m.image_blend = merge_color(c_white, knight_fl_fcol(_t div 10), _gl);
            }
            else if (_t < 170)
            {
                _k.m.image_index = 2 + min(4, (_t - 150) div 4);
                _k.m.image_blend = c_white;
            }
        }
        // the flowers
        for (var _j = 0; _j < _nf; _j++)
        {
            var _d = _fl[_j];
            var _gx = _cx + _d.dx, _gy = _cy + _d.dy;
            var _in = 12 + (_j * 6);
            var _go = 100 + (_j * 8);
            if (_t == _in)
            {
                var _gs = asset_get_index(_d.s);
                if (knight_cc_spr(_gs))
                {
                    var _g = knight_om_make(1, _cx + (_d.dx * 1.5), _cy + (_d.dy * 1.5));
                    _g.sprite_index = _gs;
                    _g.ovl = asset_get_index(_d.o);
                    _g.col = _d.c;
                    _g.image_xscale = -2;
                    _g.image_yscale = 2;
                    _g.image_speed = 0.125;
                    _g.a = 0;
                    _g.depth = (_d.dy > 0) ? -6 : -4;
                    with (_g)
                    {
                        scr_lerpvar("x", x, _gx, 18, 2, "out");
                        scr_lerpvar("y", y, _gy, 18, 2, "out");
                        scr_lerpvar("a", 0, 0.75, 14);
                    }
                    array_push(_k.fl, _g);
                    _k.rc[_j] = _g;
                    if (knight_cc_spr(_bs))
                        knight_fl_fx1(_bs, _gx, _gy, 2, _d.c, 0.5);
                    snd_pitch(snd_play(snd_bell), 0.9 + (_j * 0.06));
                }
            }
            var _g2 = _k.rc[_j];
            if (!i_ex(_g2))
                continue;
            // hover (after gliding in)
            if (_t >= _in + 18 && _t < _go)
            {
                var _tt = (current_time * 0.07) * 0.1;
                _g2.x = _gx + (sin((_tt * _d.hs) + _d.hp) * 6);
                _g2.y = _gy + (sin((_tt * _d.hs * 0.7) + _d.hp + 1) * 3);
                if (_t >= 50 && ((_t + (_j * 5)) mod 16) == 0)
                    knight_fl_mote(_k, _g2.x, _g2.y, _cx, _cy, _d.c);
            }
            if (_t == 80)
            {
                with (_g2)
                    scr_lerpvar("a", a, 1, 10);
            }
            if (_t == 85 + (_j * 2))
                knight_om_ring(_g2.x, _g2.y, 10, 70, 6, _d.c, 20);
            // the transfer
            if (_t == _go)
            {
                with (_g2)
                {
                    scr_oflash();
                    scr_lerpvar("x", x, _cx, 12, 2, "in");
                    scr_lerpvar("y", y, _cy, 12, 2, "in");
                    scr_lerpvar("image_xscale", image_xscale, -0.6, 12);
                    scr_lerpvar("image_yscale", image_yscale, 0.6, 12);
                }
                snd_pitch(snd_play(snd_power), 0.85 + (_j * 0.06));
            }
            if (_t > _go && _t < _go + 12 && ((_t - _go) mod 2) == 1)
            {
                var _ai = instance_create_depth(_g2.x, _g2.y, _g2.depth + 1, obj_afterimage);
                _ai.sprite_index = _g2.ovl;
                _ai.image_index = _g2.image_index;
                _ai.image_xscale = _g2.image_xscale;
                _ai.image_yscale = _g2.image_yscale;
                _ai.image_blend = _d.c;
                _ai.image_alpha = 0.5;
                _ai.fadeSpeed = 0.1;
            }
            if (_t == _go + 12)
            {
                knight_fl_snd("snd_japanese_yo_hit2");
                knight_om_ring(_cx, _cy, 4, 34, 4, _d.c, 12);
                if (i_ex(_k.m))
                    _k.m.image_blend = merge_color(c_white, _d.c, 0.6);
                with (_g2)
                    instance_destroy();
                _k.rc[_j] = noone;
            }
        }
        if (_t == 150)
            knight_fl_snd("snd_weaponpull");
        if (_t == 160)
        {
            // absorption: every colour rings out from him
            for (var _b = 0; _b < _nf; _b++)
                knight_om_ring(_cx, _cy - 10, 8 + (_b * 4), 120 + (_b * 18), 5, _fl[_b].c, 24 + (_b * 2));
            knight_fl_snd("snd_great_shine");
            if (i_ex(_k.m))
            {
                with (_k.m)
                    scr_oflash();
            }
        }
        if (_t == 170)
        {
            // OMEGA FLOWERY
            _k.m = knight_fl_drop(_k, _k.m);
            _k.m = knight_fl_mk(_k, _a.omega, _F, _hy, 0, 0);
            knight_om_orb(_cx, _cy - 10, 10, 70, c_white, 14);
            knight_fl_voice("omega_flowery");
            snd_play(snd_boost);
        }
        if (_t >= 170 && i_ex(_k.m))
            _k.m.image_index = ((_t - 170) div 6) mod 3;
        return 1;
    }
    // ATTACK (o: 1-176)
    var _o = _t - 189;
    if (_o == 1 && !i_ex(_k.m))
        _k.m = knight_fl_mk(_k, _a.omega, _F, _hy, 0, 0);
    if (_o < 24 && i_ex(_k.m))
        _k.m.image_index = (_o div 6) mod 3;
    if (_o == 24)
        knight_fl_snd("snd_great_shine");
    if (_o >= 24 && _o < 50 && i_ex(_k.m))
    {
        _k.m.image_index = 3 + ((_o div 4) mod 3);
        if ((_o mod 2) == 0)
            knight_fl_trail(_k.m, knight_om_hue());
    }
    if (_o >= 50 && _o < 104 && i_ex(_k.m))
    {
        // three rushes, each from his spot THROUGH the foe (frames 0-9, speeding up) and back in an arc (10-17): every
        // position set frame by frame, no jumps
        var _rs = (_o - 50) mod 18;
        var _rn = (_o - 50) div 18;
        var _ax = _F, _ay = _hy;
        var _bx = _p[0] + 40, _by = _hy - 30 + ((_rn mod 2) ? 30 : 0);
        if (_rs == 0)
        {
            if (_rn == 0)
                knight_fl_voice("last_jarona");
            knight_fl_snd("snd_ultraswing");
        }
        if (_rs < 10)
        {
            var _q = (_rs + 1) / 10;
            _k.m.x = lerp(_ax, _bx, _q * _q);
            _k.m.y = lerp(_ay, _by, _q);
            _k.m.image_index = 6 + ((_o div 3) mod 3);
            if ((_rs mod 2) == 0)
                knight_fl_trail(_k.m, knight_fl_fcol(_rn * 2));
        }
        else
        {
            var _r2 = (_rs - 9) / 8;
            var _e2 = 1 - ((1 - _r2) * (1 - _r2));
            _k.m.x = lerp(_bx, _ax, _e2);
            _k.m.y = lerp(_by, _ay, _e2) - (sin(_r2 * pi) * 30);
            _k.m.image_index = 3 + ((_o div 4) mod 3);
            if ((_rs mod 3) == 0)
                knight_fl_trail(_k.m, knight_om_hue());
        }
        if (_rs == 8)
        {
            // contact: the explosion, a ripple and an orb at the foe, the hit
            knight_om_boom(_p[0], _p[1], 0.55);
            knight_om_ring(_p[0], _p[1], 10, 140 + (_rn * 40), 7, knight_fl_fcol(_rn * 2), 22);
            knight_om_orb(_p[0] + 10, _p[1] - 6, 6, 34, c_white, 10);
            knight_fl_snd("snd_punchheavythunder");
            knight_fl_hit(_k, ceil(_k.dmg * 0.15), knight_fl_fcol(_rn * 2), (_rn == 0));
        }
    }
    if (_o == 104 && i_ex(_k.m))
    {
        knight_fl_snd("snd_explosion_mmx");
        knight_om_ring(_p[0] - 80, _p[1], 10, 90, 5, c_white, 16);
        // (build 50: Kris no longer jumps in at the clash - Prism Rush is Flowery's alone)
    }
    if (_o >= 104 && _o <= 110 && i_ex(_k.m))
    {
        // into the clash: from his spot to the foe in 6 frames
        var _q3 = (_o - 104) / 6;
        _k.m.x = lerp(_F, _p[0] - 140, _q3);
        _k.m.y = lerp(_hy, _hy - 20, _q3);
    }
    if (_o >= 104 && _o < 124 && i_ex(_k.m))
        _k.m.image_index = 9 + ((_o div 4) mod 3);
    if (_o == 116)
    {
        knight_om_boom(_p[0], _p[1], 0.4);
        knight_fl_hit(_k, ceil(_k.dmg * 0.2), c_white, false);
    }
    if (_o >= 124 && _o < 142 && i_ex(_k.m))
        _k.m.image_index = 12 + min(4, (_o - 124) div 4);
    if (_o == 130)
    {
        // the wind-up gathers the colours
        for (var _w = 0; _w < 3; _w++)
            knight_om_ring(_k.m.x + 40, _k.m.y + 50, 120 - (_w * 30), 8, 4, knight_fl_fcol(_w * 2 + 1), 12);
    }
    if (_o == 142)
    {
        knight_fl_voice("take_that");
        knight_fl_snd("snd_ultraswing");
    }
    if (_o >= 142 && _o < 160 && i_ex(_k.m))
        _k.m.image_index = 17 + min(2, (_o - 142) div 3);
    if (_o == 148)
    {
        // the PRISM punch: Chapter 5's bwooshes (440 / 330 / 220) and explosions at the foe
        for (var _e2 = 0; _e2 < 3; _e2++)
        {
            knight_om_boom(_p[0] + irandom_range(-30, 30), _p[1] + irandom_range(-30, 30), 0.9 - (_e2 * 0.2));
            knight_om_ring(_p[0], _p[1], 10, 220 + (_e2 * 110), 8, make_color_hsv((random_range(1, 7) / 7) * 255, 255, 255), 30 + (_e2 * 10));
        }
        knight_om_orb(_p[0], _p[1], 10, 90, c_white, 16);
        knight_fl_snd("snd_explosion_mmx3");
        instance_create(0, 0, obj_shake);
        knight_fl_hit(_k, _k.dmg - (3 * ceil(_k.dmg * 0.15)) - ceil(_k.dmg * 0.2), c_white, false);
    }
    if (_o > 148 && _o < 158 && i_ex(_k.m) && (_o mod 3) == 0)
        knight_fl_trail(_k.m, knight_om_hue());
    if (_o >= 142 && _o <= 148 && i_ex(_k.m))
        _k.m.x = lerp(_p[0] - 140, _p[0] - 100, (_o - 142) / 6);
    if (_o >= 160 && _o <= 174 && i_ex(_k.m))
    {
        // back: he bounces off the foe in an arc to his own place
        if (_o == 160)
        {
            _k.bx0 = _k.m.x;
            _k.by0 = _k.m.y;
            snd_play(snd_wing);
            if (variable_struct_exists(_k, "kris") && i_ex(_k.kris))
                _k.kris.image_alpha = 1;
        }
        var _r4 = (_o - 160) / 14;
        var _e4 = 1 - ((1 - _r4) * (1 - _r4));
        _k.m.x = lerp(_k.bx0, _hx, _e4);
        _k.m.y = lerp(_k.by0, _hy, _e4) - (sin(_r4 * pi) * 34);
        _k.m.image_index = 24 + ((_o div 4) mod 3);
        if ((_o mod 3) == 0)
            knight_fl_trail(_k.m, knight_om_hue());
    }
    if (_o == 174)
    {
        // landed: he is himself again in his place (or stays Omega Flowery)
        knight_fl_fx1(_a.shock, _hx + 22, _hy + 94, 0.8, c_white, 0.5);
        snd_play(snd_bump);
        if (!knight_fl_om_on())
        {
            if (i_ex(_k.m))
            {
                with (_k.m)
                    scr_lerpvar("a", 1, 0, 8);
            }
            _k.m2 = knight_fl_mk(_k, _a.victory, _hx, _hy, 0, 0);
            if (i_ex(_k.m2))
            {
                _k.m2.image_alpha = 0;
                with (_k.m2)
                    scr_lerpvar("image_alpha", 0, 1, 8);
            }
            knight_om_orb(_hx + 22, _hy + 50, 6, 40, c_white, 10);
        }
        snd_play(snd_great_shine);
    }
    if (_o >= 186)
        knight_fl_end(_k);
    return 1;
}

// (unused since build 50) Prism Rush's clash: Kris jumping at the foe and slashing
function knight_fl_kris_jump(_k, _p)
{
    for (var _i = 0; _i < 3; _i++)
    {
        if (global.char[_i] == 1 && global.hp[1] > 0 && i_ex(global.charinstance[_i]))
        {
            var _h = global.charinstance[_i];
            var _m = knight_fl_mk(_k, _h.attacksprite, _h.x, _h.y, -1, 0.5);
            if (i_ex(_m))
            {
                var _tx = _p[0] - 40;
                var _ty = _p[1] - 90;
                with (_m)
                {
                    scr_lerpvar("x", x, _tx, 10, 2, "out");
                    scr_lerpvar("y", y, _ty, 10, 2, "out");
                }
                _h.image_alpha = 0;
                _k.kris = _h;
            }
            snd_play(snd_criticalswing);
            var _att = instance_create(_p[0], _p[1], obj_basicattack);
            _att.image_xscale = 2.5;
            _att.image_yscale = 2.5;
            return 1;
        }
    }
    return 0;
}

// Honey Kiss on the foe: MERCY up 20% where the fight has MERCY; a knight has none - it is charmed instead (its next attack
// hurts everyone 15% less)
function knight_fl_honey(_star)
{
    var _f = knight_fl_fx();
    var _ma = asset_get_index("scr_mercyadd");
    if (!i_ex(obj_knight_enemy) && _ma >= 0 && _star >= 0 && _star < 3 && global.monster[_star] == 1)
    {
        script_execute(_ma, _star, 20);
        return 1;
    }
    _f.charm = 1;
    return 1;
}

// ---------- overworld (older calls) ----------
function knight_fl_walk_spr(_f)
{
    return knight_cc_walk_spr(5, _f);
}

// LAST JARONA (kspell 27): his Jarona three times over, every one bigger. Each charge (34 frames): he winds up while three
// rings of the flowers' colours close in on him and he flashes white; the lunge (5 frames, speeding up) in a rainbow glow
// with rainbow afterimages; CONTACT on the frame he reaches the foe - an explosion (white, then a hue), a ripple and an
// orb there, the hit (30% / 25% / 45%), a held beat with a little shake; then he BOUNCES back off the foe in an arc to his
// place (his knocked-back frame), landing with a small shockwave at his feet - and charges again. The last one: three
// explosions, the big ripples, a screen shake. Every position is set frame by frame (no jumps). When the Violet Knight's
// Side B is at its end (it has Roared) and he is the one on top, his clash with the Knight follows (kspell 29).
function knight_fl_lastjarona(_k, _a, _p, _hx, _hy)
{
    var _t = _k.t;
    var _lx = _p[0] - 100;
    if (_t == 1)
    {
        // always as OMEGA FLOWERY (his Omega frames: wind-up 12-16, punch 17-19, deflect 24-26, idle 20-22)
        // (in his Omega form he floats: the move starts where he is drawn)
        _k.oy = knight_fl_om_float();
        _k.zb = [0, 0, 0];
        _k.m = knight_fl_mk(_k, _a.omega, _hx, _hy + _k.oy, 20, 0);
        knight_om_orb(_hx + 22, _hy + 50, 8, 50, c_white, 10);
        knight_fl_voice("last_jarona");
        snd_play(snd_boost);
    }
    // three punches, 40 frames each from frame 6: wind-up leaning back (0-11), the lunge (12-17, contact on 17), the hit-stop
    // (4 frames, 6 on the last), the bounce back in an arc (to 34), the landing and settling (34-39). Press [Z] just before
    // he connects (the gold ring closing on the foe) for a STRONG punch: x1.5 damage. Too early and that punch is a plain one.
    var _hy2 = _hy + (variable_struct_exists(_k, "oy") ? _k.oy : 0);
    if (_t >= 6 && _t < 126 && i_ex(_k.m))
    {
        var _st = (_t - 6) mod 40;
        var _n = (_t - 6) div 40;
        var _m = _k.m;
        var _hs = (_n == 2) ? 6 : 4;
        var _bs = 17 + _hs;
        knight_fl_jz(_k, _n, _st, 6, 14, 17);
        if (_st == 0)
        {
            _m.x = _hx;
            _m.y = _hy2;
            for (var _r = 0; _r < 3; _r++)
                knight_om_ring(_hx + 22, _hy2 + 50, 90 - (_r * 22), 6, 4, knight_fl_fcol(_n * 2 + _r), 10);
            snd_pitch(snd_play(snd_power), 1 + (_n * 0.1));
        }
        if (_st < 12)
        {
            // the wind-up: he draws back a little (eased), his Omega wind-up frames
            var _w = _st / 11;
            _m.image_index = 12 + min(4, _st div 3);
            _m.x = _hx - round(8 * (1 - ((1 - _w) * (1 - _w))));
            _m.y = _hy2;
        }
        if (_st == 8)
        {
            with (_m)
                scr_oflash();
        }
        if (_st == 14)
            knight_om_ring(_p[0], _p[1], 64, 12, 3, make_color_rgb(255, 220, 90), 4);
        if (_st >= 12 && _st <= 17)
        {
            // the lunge, punching: speeding up from where he drew back, at the foe on frame 17
            var _q = (_st - 12) / 5;
            _m.image_index = 17 + min(2, (_st - 12) div 2);
            _m.x = lerp(_hx - 8, _lx, _q * _q);
            _m.y = _hy2;
            if (_st == 12)
            {
                knight_fl_snd("snd_ultraswing");
                // "JARONA!" on every punch
                knight_fl_voice("jarona" + string(_n + 1));
            }
            if (_st > 12)
                knight_fl_trail(_m, knight_om_hue());
        }
        if (_st == 17)
        {
            var _sh = [0.3, 0.25, 0.45];
            var _d = (_n < 2) ? ceil(_k.dmg * _sh[_n]) : (_k.dmg - ceil(_k.dmg * 0.3) - ceil(_k.dmg * 0.25));
            var _strong = (_k.zb[_n] == 1);
            if (_strong)
            {
                _d = ceil(_d * 1.5);
                knight_om_boom(_p[0] + 10, _p[1] - 10, 0.7);
                knight_om_ring(_p[0], _p[1], 6, 120, 5, make_color_rgb(255, 220, 90), 14);
                knight_fl_snd("snd_bell");
            }
            knight_om_boom(_p[0], _p[1], (_n == 2) ? 0.9 : 0.55);
            knight_om_ring(_p[0], _p[1], 10, 150 + (_n * 50), 7, knight_fl_fcol(_n * 2), 22);
            knight_om_orb(_p[0] - 10, _p[1], 6, 36, c_white, 10);
            if (_n == 2)
            {
                for (var _e = 0; _e < 2; _e++)
                {
                    knight_om_boom(_p[0] + irandom_range(-30, 30), _p[1] + irandom_range(-30, 30), 0.7 - (_e * 0.2));
                    knight_om_ring(_p[0], _p[1], 10, 330 + (_e * 110), 8, make_color_hsv((random_range(1, 7) / 7) * 255, 255, 255), 34 + (_e * 8));
                }
                instance_create(0, 0, obj_shake);
                knight_fl_snd("snd_explosion_mmx3");
            }
            else
            {
                knight_fl_snd("snd_punchheavythunder");
                if (_strong)
                    instance_create(0, 0, obj_shake);
            }
            knight_fl_hit(_k, _d, knight_fl_fcol(_n * 2 + 1), (_n == 0));
        }
        if (_st > 17 && _st < _bs)
        {
            // the hit-stop: the punch held on the foe, the shake dying down
            var _amp = round(3 * (1 - ((_st - 17) / _hs)));
            _m.image_index = 19;
            _m.x = _lx + irandom_range(-_amp, _amp);
            _m.y = _hy2 + irandom_range(-_amp, _amp);
        }
        if (_st >= _bs && _st <= 34)
        {
            // the bounce: back off the foe in an arc (eased out), to his place
            var _b = (_st - _bs) / (34 - _bs);
            var _eb = 1 - power(1 - _b, 3);
            _m.image_index = 24 + min(2, floor(_b * 3));
            _m.x = lerp(_lx, _hx, _eb);
            _m.y = _hy2 - (sin(_b * pi) * ((_n == 2) ? 40 : 26));
            if (_st == _bs)
                snd_play(snd_wing);
            if ((_st mod 3) == 0)
            {
                var _ai = knight_fl_trail(_m, knight_om_hue());
                if (i_ex(_ai))
                    _ai.image_alpha = 0.35;
            }
        }
        if (_st == 34)
        {
            _m.x = _hx;
            knight_fl_fx1(_a.shock, _hx + 22, _hy2 + 94, 0.8, c_white, 0.5);
            snd_play(snd_bump);
        }
        if (_st >= 34)
        {
            // the landing: a little dip, then he settles into his idle
            var _dip = [3, 2, 1, 0, 0, 0];
            _m.x = _hx;
            _m.y = _hy2 + _dip[_st - 34];
            _m.image_index = 20 + (((_st - 34) div 2) mod 3);
        }
    }
    if (_t == 128 && i_ex(_k.m))
    {
        // his Omega pose; then (if he is not Omega Flowery for good) he is himself again
        _k.m.image_index = 0;
        snd_play(snd_great_shine);
    }
    if (_t > 128 && _t < 140 && i_ex(_k.m))
        _k.m.image_index = ((_t - 128) div 4) mod 3;
    if (_t == 140 && !knight_fl_om_on())
    {
        if (i_ex(_k.m))
        {
            with (_k.m)
                scr_lerpvar("a", 1, 0, 8);
        }
        _k.m2 = knight_fl_mk(_k, _a.victory, _hx, _hy, 0, 0);
        if (i_ex(_k.m2))
        {
            _k.m2.image_alpha = 0;
            with (_k.m2)
                scr_lerpvar("image_alpha", 0, 1, 8);
        }
        knight_om_orb(_hx + 22, _hy + 50, 6, 40, c_white, 10);
    }
    if (_t >= 148)
    {
        var _fin = false;
        with (obj_knight_enemy)
        {
            if (variable_instance_exists(id, "v_sideb") && v_sideb && variable_instance_exists(id, "haveusedroaring") && haveusedroaring
                && variable_instance_exists(id, "chargeupcon") && chargeupcon == 0 && knight_cc_ok(knight_vb_fin()))
                _fin = true;
        }
        var _cs = _k.caster;
        knight_fl_end(_k);
        // the Violet Knight's Side B, after its Roaring, with Flowery on top: this ends it - with his own last clash with the
        // Knight (in place of the black and red screen), then the Knight's own death scene
        if (_fin)
        {
            knight_kspell_start(29, _cs, 0, 0);
            knight_fl_ks_init();
        }
    }
    return 1;
}

// his Jaronas' timed press: [Z] (the game's CONFIRM, button1) during punch _n's window (_w0.._hit, the frames of _st) -
// pressed in the last frames before contact (_g.._hit) it is a STRONG punch (1), earlier it is a miss (-1); one press a punch
function knight_fl_jz(_k, _n, _st, _w0, _g, _hit)
{
    if (!variable_struct_exists(_k, "zb") || !is_array(_k.zb))
        _k.zb = [0, 0, 0];
    if (_n < 0 || _n >= array_length(_k.zb) || _k.zb[_n] != 0)
        return 0;
    if (_st >= _w0 && _st <= _hit && button1_p())
        _k.zb[_n] = (_st >= _g) ? 1 : -1;
    return _k.zb[_n];
}

// a move, a FIGHT or a scene of his is on screen (his permanent Omega drawing steps aside for it)
function knight_fl_busy()
{
    if (!is_undefined(global.knight_ks) && is_struct(global.knight_ks) && variable_struct_exists(global.knight_ks, "cc") && global.knight_ks.cc == 5)
        return true;
    if (variable_global_exists("knight_fl_fj") && is_struct(global.knight_fl_fj))
        return true;
    return false;
}

// ---------- his FIGHT: one Jarona ----------
// FIGHT is one Jarona charge, timed on the game's own FIGHT hit (obj_heroparent deals its damage 11 frames after the swing
// starts, finishattacktimer): the wind-up with a white flash and a "Jarona!" (frames 0-5), the lunge at the foe in blue with
// blue afterimages (6-11) - reaching it on the frame the game's hit lands, with a blue flash and a shockwave there - then
// knocked back to his place (15-26). The damage is the game's own FIGHT damage (the attack bar), once.
global.knight_fl_fj = undefined;
global.knight_fl_song = "";

// his FIGHT as OMEGA FLOWERY (the hero's own drawing, global.knight_fl_om.pose): wind-up 1-5, the lunge 6-11 (eased in, at the
// foe on 11), the hit, a beat, the bounce back 15-25 (eased out, in an arc), settling to 30
function knight_fl_fight_om(_j, _a, _t)
{
    var _om = global.knight_fl_om;
    if (!is_struct(_om.pose))
        _om.pose = { spr: _a.omega, f: 12, dx: 0 };
    var _ps = _om.pose;
    var _lx = (_j.px - 90) - _j.hx;
    var _t3 = (_t div 4) mod 3;
    if (_t <= 5)
    {
        _ps.f = 12 + min(4, _t - 1);
        _ps.dx = -round(6 * (_t / 5));
        _ps.dy = 0;
    }
    if (_t == 6)
        snd_play(snd_swing);
    if (_t >= 6 && _t <= 11)
    {
        var _q = (_t - 6) / 5;
        _ps.f = 17 + min(2, (_t - 6) div 2);
        _ps.dx = round(lerp(-6, _lx, _q * _q));
        _ps.dy = 0;
        // afterimages in the cycling hue
        var _ai = instance_create_depth(_j.hx + _ps.dx, _j.hy, _j.h.depth + 1, obj_afterimage);
        _ai.sprite_index = _a.omega;
        _ai.image_index = _ps.f;
        _ai.image_xscale = 2;
        _ai.image_yscale = 2;
        _ai.image_blend = knight_om_hue();
        _ai.image_alpha = 0.45;
        _ai.fadeSpeed = 0.12;
    }
    if (_t == 11)
    {
        knight_fl_fx1(_a.shock, _j.px - 30, _j.py + 60, 1.2, knight_om_hue(), 0.5);
        knight_om_orb(_j.px - 20, _j.py, 4, 22, c_white, 7);
        knight_om_ring(_j.px, _j.py, 8, 90, 5, knight_om_hue(), 14);
    }
    if (_t > 11 && _t < 15)
    {
        _ps.f = 19;
        _ps.dx = _lx + irandom_range(-2, 2);
    }
    if (_t >= 15 && _t <= 25)
    {
        var _b = (_t - 15) / 10;
        var _eb = 1 - power(1 - _b, 3);
        _ps.f = 24 + min(2, floor(_b * 3));
        _ps.dx = round(lerp(_lx, 0, _eb));
        _ps.dy = -round(sin(_b * pi) * 20);
        if (_t == 15)
            snd_play(snd_wing);
    }
    if (_t > 25)
    {
        _ps.f = 20 + _t3;
        _ps.dx = 0;
        _ps.dy = (_t == 26) ? 2 : ((_t == 27) ? 1 : 0);
    }
    if (_t >= 30)
        knight_fl_fight_end(_j);
    return 1;
}

function knight_fl_fight_end(_j)
{
    if (variable_global_exists("knight_fl_om") && is_struct(global.knight_fl_om))
        global.knight_fl_om.pose = undefined;
    for (var _i = 0; _i < array_length(_j.fl); _i++)
    {
        if (i_ex(_j.fl[_i]))
        {
            with (_j.fl[_i])
                instance_destroy();
        }
    }
    if (i_ex(_j.h))
    {
        // (his hero is shown again right away - in his Omega form too: it draws itself as Omega Flowery)
        _j.h.image_alpha = 1;
        // his FIGHT is over: the hero goes back to its stance instead of holding the swing (obj_heroparent's force ends it)
        with (_j.h)
        {
            if (state == 1)
            {
                force = 1;
                attacktimer = max(attacktimer, attackframes);
            }
        }
    }
    global.knight_fl_fj = undefined;
    return 1;
}

function knight_fl_fight_tick()
{
    var _j = global.knight_fl_fj;
    if (!instance_exists(obj_battlecontroller))
    {
        if (is_struct(_j))
            knight_fl_fight_end(_j);
        return 0;
    }
    var _a = knight_fl_a();
    if (!is_struct(_j))
    {
        var _h = noone;
        with (obj_knight_herocc)
        {
            if (char == 5 && state == 1 && variable_instance_exists(id, "finishattacktimer") && finishattacktimer >= 10)
                _h = id;
        }
        if (_h == noone || !knight_cc_spr(_a.jarona) || !is_undefined(global.knight_ks))
            return 0;
        var _s = clamp(_h.myself, 0, 2);
        var _p = knight_kspell_pos(clamp(global.chartarget[_s], 0, 2));
        // (in his Omega form he floats: the Jarona starts where he is drawn)
        _j = { h: _h, t: 0, hx: _h.x, hy: _h.y + knight_fl_om_float(), px: _p[0], py: _p[1], fl: [], m: noone, om: knight_fl_om_on() };
        global.knight_fl_fj = _j;
        if (_j.om)
        {
            // OMEGA FLOWERY: his hero does the Jarona itself (its own Omega Draw, a pose and an offset) - nothing is handed
            // over to a marker, so he never blinks out between the two
            global.knight_fl_om.pose = { spr: _a.omega, f: 12, dx: 0 };
            knight_fl_voice("jarona" + string(irandom_range(1, 4)));
            return 1;
        }
        _j.m = knight_fl_mk(_j, _a.jarona, _j.hx, _j.hy, 0, 0);
        _h.image_alpha = 0;
        if (i_ex(_j.m))
        {
            with (_j.m)
                scr_oflash();
        }
        knight_fl_voice("jarona" + string(irandom_range(1, 4)));
        return 1;
    }
    _j.t++;
    var _t = _j.t;
    var _m = _j.m;
    var _blue = make_color_rgb(70, 130, 255);
    if (!i_ex(_j.h) || _t > 60)
        return knight_fl_fight_end(_j);
    if (variable_struct_exists(_j, "om") && _j.om)
        return knight_fl_fight_om(_j, _a, _t);
    if (i_ex(_m))
    {
        if (_t <= 5)
            _m.image_index = min(4, _t);
        if (_t == 6)
        {
            _m.image_index = 5;
            _m.image_blend = _blue;
            var _lx = _j.px - 90;
            with (_m)
                scr_lerpvar("x", x, _lx, 5, 2, "in");
            snd_play(snd_swing);
        }
        if (_t > 6 && _t <= 11)
        {
            var _ai = knight_fl_trail(_m, _blue);
            if (i_ex(_ai))
                _ai.image_alpha = 0.45;
        }
        if (_t == 11)
        {
            knight_fl_fx1(_a.shock, _j.px - 30, _j.py + 60, 1.2, merge_color(c_aqua, c_blue, 0.3), 0.5);
            knight_om_orb(_j.px - 20, _j.py, 4, 22, merge_color(_blue, c_white, 0.5), 7);
        }
        if (_t == 15)
        {
            _m.image_index = 6;
            var _hx = _j.hx;
            with (_m)
                scr_lerpvar("x", x, _hx, 10, 2, "out");
        }
        if (_t > 15)
            _m.image_blend = merge_color(_blue, c_white, min(1, (_t - 15) / 10));
    }
    if (_t >= 27)
        knight_fl_fight_end(_j);
    return 1;
}

// the fields every move of his keeps (knight_kspell_start made the struct)
function knight_fl_ks_init()
{
    if (is_undefined(global.knight_ks))
        return 0;
    global.knight_ks.cc = 5;
    global.knight_ks.fl = [];
    global.knight_ks.m = noone;
    global.knight_ks.m2 = noone;
    global.knight_ks.w = noone;
    global.knight_ks.kris = noone;
    global.knight_ks.wind = -1;
    global.knight_ks.rc = [];
    global.knight_ks.om0 = 0;
    global.knight_ks.fx2 = 0;
    global.knight_ks.cut = false;
    global.knight_ks.km = noone;
    global.knight_ks.bx0 = 0;
    global.knight_ks.by0 = 0;
    return 1;
}

// ---------- his last stand: OMEGA FLOWERY for the rest of the fight ----------
// At the end of an enemy turn (scr_mnendturn -> knight_wr_turnend), in any knight's hub fight, when Flowery is up and nobody
// else in the party is (down, taken by the Knight, or never there): the battle holds (like the Weird Route's scenes), his
// scene plays (kspell 28) and he becomes OMEGA FLOWERY for good: his Omega drawing on his hero, AT +25%, DF +15%, MAG +20%,
// max HP +20% (and 30% of it back), LAST JARONA in his ACTION's place (once every 3 turns), his HP box in Omega colours.
// Once per fight. The fight's own turns, its attacks and its end are untouched.
function knight_fl_laststand_check()
{
    // (every knight's hub fight - not an online match, whose kit has none of his moves)
    if (!knight_active() || kfo_run_on())
        return false;
    if (!variable_global_exists("knight_fl_om") || !is_struct(global.knight_fl_om) || global.knight_fl_om.trig)
        return false;
    if (!i_ex(obj_knight_enemy) || !is_undefined(global.knight_ks))
        return false;
    // (not while the fight already holds for a scene of its own)
    if (global.myfight != 0 || global.mnfight != 0)
        return false;
    var _busy = false;
    with (obj_knight_enemy)
    {
        if (variable_instance_exists(id, "knightkillcon") && knightkillcon != 0)
            _busy = true;
    }
    if (_busy)
        return false;
    // only once every teammate has been TAKEN by the Knight (swooned and killed off: the Violet Knight's taking removes them
    // from the party, the hub's Weird Route marks them slain); a teammate who is only knocked down (still in the party, and
    // can be revived) does not count. Alone from the start: no last stand (OMEGA FORM is his technique for that)
    var _fs = -1;
    for (var _s = 0; _s < 3; _s++)
    {
        var _c = global.char[_s];
        if (_c == 0)
            continue;
        if (_c == 5)
        {
            if (global.hp[5] > 0 && _fs < 0)
                _fs = _s;
            continue;
        }
        if (!knight_wr_slain(_c))
            return false;
    }
    if (knight_fl_gone_count() == 0 || _fs < 0 || !i_ex(global.charinstance[_fs]))
        return false;
    return knight_fl_laststand_go(_fs);
}

// teammates of his taken by the Knight this fight: in the party at its start and no longer in it, or marked slain
function knight_fl_gone_count()
{
    var _om = global.knight_fl_om;
    var _n = 0;
    var _p0 = variable_struct_exists(_om, "p0") ? _om.p0 : [];
    for (var _i = 0; _i < array_length(_p0); _i++)
    {
        var _c = _p0[_i];
        if (_c == 5)
            continue;
        var _in = false;
        for (var _s = 0; _s < 3; _s++)
        {
            if (global.char[_s] == _c)
                _in = true;
        }
        if (!_in || knight_wr_slain(_c))
            _n++;
    }
    return _n;
}

// the Violet Knight's Side B with Flowery on top, after its second taking (knightkillcon 130): his transformation is his
// power-up scene (self: the Knight)
function knight_fl_laststand_force()
{
    if (!knight_active() || kfo_run_on())
        return false;
    if (!variable_global_exists("knight_fl_om") || !is_struct(global.knight_fl_om) || global.knight_fl_om.trig)
        return false;
    if (!is_undefined(global.knight_ks))
        return false;
    var _fs = -1;
    for (var _s = 0; _s < 3; _s++)
    {
        if (global.char[_s] == 5 && _fs < 0)
            _fs = _s;
    }
    if (_fs < 0 || !i_ex(global.charinstance[_fs]))
        return false;
    if (global.hp[5] <= 0)
    {
        global.hp[5] = 1;
        scr_revive(_fs);
    }
    with (global.charinstance[_fs])
        visible = 1;
    return knight_fl_laststand_go(_fs);
}

function knight_fl_laststand_go(_fs)
{
    global.knight_fl_om.trig = true;
    global.myfight = 99;
    global.mnfight = 99;
    global.charturn = -1;
    knight_kspell_start(28, _fs, 0, 0);
    knight_fl_ks_init();
    global.knight_fl_om.cut = true;
    return true;
}

// the scene: his reaction (alone), the Knight takes note, the six flowers give him their power (Prism Rush's power-up),
// OMEGA FLOWERY
function knight_fl_laststand(_k, _a, _p, _hx, _hy)
{
    var _t = _k.t;
    if (_t == 1)
    {
        _k.cut = true;
        _k.m = knight_fl_mk(_k, _a.defeat, _hx, _hy, 0, 0);
        snd_play(snd_hurt1);
    }
    if (_t == 14)
        knight_fl_voice("huh");
    if (_t == 30)
    {
        // the Knight acknowledges him
        with (obj_knight_enemy)
            scr_oflash();
        snd_play_x(snd_knight_cut, 0.5, 0.7);
    }
    if (_t == 44)
    {
        _k.m = knight_fl_drop(_k, _k.m);
        _k.m = knight_fl_mk(_k, _a.spellready, _hx, _hy, 0, 0);
        knight_fl_voice("with_your_powers_combined");
    }
    if (_t >= 60 && _t < 249)
    {
        if (_t == 60)
            _k.m = knight_fl_drop(_k, _k.m);
        var _sv = _k.t;
        _k.t = _t - 59;
        knight_fl_prism(_k, _a, _p, _hx, _hy);
        _k.t = _sv;
    }
    if (_t == 249)
        knight_fl_om_become(_k);
    if (_t >= 262)
    {
        knight_fl_end(_k);
        // his line, then the turn goes on (knight_fl_om_tick waits for the text)
        var _nm = knight_charname(5);
        with (obj_knight_enemy)
        {
            msgset(0, "* " + _nm + " became OMEGA FLOWERY!&* (Now \\cYLAST JARONA\\cW, \\cYPRISM RUSH\\cW, \\cYSMILE AGAIN\\cW.)/%");
            scr_battletext_default();
        }
        global.knight_fl_om.cut = false;
        global.knight_fl_om.wait = 1;
    }
    return 1;
}

// nobody but him up in the party
function knight_fl_om_alone()
{
    for (var _s = 0; _s < 3; _s++)
    {
        var _c = global.char[_s];
        // (a knocked-down teammate is still there on the line; a taken one is gone)
        if (_c != 0 && _c != 5 && !knight_wr_slain(_c))
            return false;
    }
    return true;
}

// SMILE AGAIN (technique 25, kspell 31; only in his Omega form): his Omega pose, the six flowers' rings closing on him,
// then he and anyone still up heal 40% of their max HP (the game's own heal numbers)
function knight_fl_smile(_k, _a, _p, _hx, _hy)
{
    var _t = _k.t;
    var _hy2 = _hy + knight_fl_om_float();
    if (_t == 1)
    {
        _k.m = knight_fl_mk(_k, _a.omega, _hx, _hy2, 0, 0);
        knight_fl_voice("smile_again");
        snd_play(snd_power);
    }
    if (i_ex(_k.m))
    {
        _k.m.y = _hy2;
        _k.m.image_index = (_t < 40) ? ((_t div 5) mod 3) : (20 + ((_t div 4) mod 3));
    }
    if (_t >= 4 && _t < 34 && (_t mod 5) == 4)
        knight_om_ring(_hx + 22, _hy2 + 50, 80, 8, 4, knight_fl_fcol((_t div 5) mod 6), 10);
    if (_t == 36)
    {
        knight_om_orb(_hx + 22, _hy2 + 50, 8, 70, c_white, 14);
        snd_play(snd_great_shine);
        knight_fl_team_heal(0.4);
    }
    if (_t >= 62)
        knight_fl_end(_k);
    return 1;
}

// Flower Man stays on: when the fight puts another song on in its place (a taking scene's music, a phase's song), Flower
// Man comes back where it was (its track position kept every frame) once his moves are done
function knight_fl_om_song_keep()
{
    var _om = global.knight_fl_om;
    if (!_om.on || !variable_global_exists("knight_fl_song") || global.knight_fl_song == "" || !knight_mus_ok())
        return 0;
    if (!variable_struct_exists(_om, "snd"))
        return 0;
    if (global.batmusic[0] == _om.snd)
    {
        if (audio_is_playing(global.batmusic[1]))
            _om.pos = audio_sound_get_track_position(global.batmusic[1]);
        return 0;
    }
    if (!audio_is_playing(global.batmusic[1]) || knight_fl_busy())
        return 0;
    knight_mus_cut(15);
    _om.snd = snd_init(global.knight_fl_song);
    global.batmusic[0] = _om.snd;
    global.batmusic[1] = mus_loop(_om.snd);
    audio_sound_set_track_position(global.batmusic[1], _om.pos);
    mus_volume(global.batmusic[1], 0, 0);
    mus_volume(global.batmusic[1], 1, 20);
    return 1;
}

// his hero left hidden (a move or a pose of another scene ending without showing him again): once nothing of his is on
// screen and no scene holds a pose of him for 10 frames, he is shown again (not when the Knight has taken him)
function knight_fl_vis_guard()
{
    // (only in his Omega form, where his own Draw shows him; the Weird Route's scenes hide members their own way)
    if (!knight_fl_om_on())
        return 0;
    with (obj_knight_herocc)
    {
        var _pm = variable_global_exists("knight_cc_pm") && is_struct(global.knight_cc_pm);
        if (char == 5 && image_alpha <= 0 && !knight_fl_busy() && !_pm && !knight_wr_slain(5) && global.hp[5] > 0)
        {
            if (!variable_instance_exists(id, "klvis"))
                klvis = 0;
            klvis++;
            if (klvis >= 10)
            {
                image_alpha = 1;
                klvis = 0;
            }
        }
        else
            klvis = 0;
    }
    return 1;
}

// OMEGA FORM (technique 24, kspell 30): the transformation as a move of his own - in his place, the six flowers gather and
// give him their power (Prism Rush's power-up, 1-189), OMEGA FLOWERY; then he stays it (knight_fl_om_become) for the rest of
// the fight. The battle's spell text says it; the turn goes on as after any spell.
function knight_fl_omform(_k, _a, _p, _hx, _hy)
{
    var _t = _k.t;
    if (_t == 1)
    {
        _k.cut = true;
        knight_fl_voice("with_your_powers_combined");
    }
    if (_t >= 1 && _t < 190)
        knight_fl_prism(_k, _a, _p, _hx, _hy);
    if (_t == 190)
        knight_fl_om_become(_k);
    if (_t >= 200)
        knight_fl_end(_k);
    return 1;
}

// Omega Flowery's poses in place of all of Flowery's: on his registry entry (what knight_cc_dress and the talk / Violet code
// read) and on his battle hero(es) - the originals are kept and put back at the start of the next fight
function knight_fl_om_dress()
{
    var _d = knight_cc(5);
    var _a = knight_fl_a();
    if (is_undefined(_d) || !knight_cc_spr(_a.om_idle))
        return 0;
    if (!variable_global_exists("knight_fl_poses0") || !is_struct(global.knight_fl_poses0))
        global.knight_fl_poses0 = { poses: _d.poses, frames: _d.frames, flurry: _d.flurry };
    if (_d.poses.idle != _a.om_idle)
    {
        _d.poses = { normal: _a.om_idle, idle: _a.om_idle, act: _a.om_pose, actready: _a.om_ready, attack: _a.om_attack, attackready: _a.om_ready,
                     defend: _a.om_defend, hurt: _a.om_hurt, defeat: _a.om_hurt, item: _a.om_pose, itemready: _a.om_ready,
                     spell: _a.om_spell, spellready: _a.om_spellready, victory: _a.om_pose };
        _d.frames = { attack: 6, attackspeed: 0.5, item: 0, spell: 2 };
        _d.flurry = _a.om_attack;
    }
    with (obj_knight_herocc)
    {
        if (char == 5 && idlesprite != _a.om_idle)
        {
            // (knight_cc_dress puts every pose on again from the entry)
            ccdressed = -1;
            knight_cc_dress();
            if (sprite_index == _a.idle || sprite_index == _a.walk)
                sprite_index = _a.om_idle;
            if (variable_instance_exists(id, "thissprite") && (thissprite == _a.idle || thissprite == _a.walk))
                thissprite = _a.om_idle;
        }
    }
    return 1;
}

function knight_fl_om_undress()
{
    if (!variable_global_exists("knight_fl_poses0") || !is_struct(global.knight_fl_poses0))
        return 0;
    var _d = knight_cc(5);
    if (!is_undefined(_d))
    {
        _d.poses = global.knight_fl_poses0.poses;
        _d.frames = global.knight_fl_poses0.frames;
        _d.flurry = global.knight_fl_poses0.flurry;
    }
    global.knight_fl_poses0 = undefined;
    // a hero already made for this fight was dressed from the Omega entry: dress it again in his own poses
    var _a = knight_fl_a();
    with (obj_knight_herocc)
    {
        if (char == 5)
        {
            ccdressed = -1;
            knight_cc_dress();
            if (variable_instance_exists(id, "thissprite") && thissprite == _a.om_idle)
                thissprite = idlesprite;
        }
    }
    return 1;
}

// his Omega form is over (a fight ends, is left or is lost; the next one starts): off, his own poses back, no Flower Man hold
function knight_fl_om_reset()
{
    if (variable_global_exists("knight_fl_om") && is_struct(global.knight_fl_om))
    {
        global.knight_fl_om.on = false;
        global.knight_fl_om.gt = -1;
        global.knight_fl_om.wait = 0;
        global.knight_fl_om.pose = undefined;
    }
    global.knight_fl_song = "";
    knight_fl_om_undress();
    return 1;
}

// where he goes once he is the last one up: the middle of the party's line - with three it is the middle member's place (Susie's,
// global.heromakex / heromakey[1], where the battle made that hero), with two halfway between both, alone his own place
function knight_fl_om_target(_h)
{
    var _om = global.knight_fl_om;
    var _tx = _h.x;
    var _ty = _h.y;
    if (variable_global_exists("heromakex") && is_array(global.heromakex) && array_length(global.heromakex) >= 2)
    {
        if (_om.n0 >= 3)
        {
            _tx = global.heromakex[1];
            _ty = global.heromakey[1];
        }
        else if (_om.n0 == 2)
        {
            _tx = (global.heromakex[0] + global.heromakex[1]) / 2;
            _ty = (global.heromakey[0] + global.heromakey[1]) / 2;
        }
    }
    _om.gx0 = _h.x;
    _om.gy0 = _h.y;
    _om.hx = round(_tx);
    _om.hy = round(_ty);
    _om.gt = 0;
    return 1;
}

// every frame (self: his hero): the glide to that place (40 frames, eased), then he stays there (between his moves; a move
// starts from where he is)
function knight_fl_om_place(_h)
{
    var _om = global.knight_fl_om;
    if (_om.gt < 0 || !i_ex(_h) || knight_fl_busy())
        return 0;
    if (_om.gt < 40)
    {
        _om.gt++;
        var _q = _om.gt / 40;
        var _e = 1 - power(1 - _q, 3);
        _h.x = round(lerp(_om.gx0, _om.hx, _e));
        _h.y = round(lerp(_om.gy0, _om.hy, _e));
        if ((_om.gt mod 4) == 0)
        {
            var _ai = knight_fl_trail(_h, knight_om_hue());
            if (i_ex(_ai))
            {
                // (heroes draw themselves at 2x)
                _ai.image_xscale = 2;
                _ai.image_yscale = 2;
                _ai.y += knight_fl_om_float();
                _ai.image_alpha = 0.3;
            }
        }
        return 1;
    }
    _h.x = _om.hx;
    _h.y = _om.hy;
    return 1;
}

// his float (like the Knight's): up and down, about 3 seconds a round
function knight_fl_om_float()
{
    if (!variable_global_exists("knight_fl_om") || !is_struct(global.knight_fl_om) || !global.knight_fl_om.on)
        return 0;
    return round(sin(global.knight_fl_om.ft / 15) * 6);
}

// Flower Man (the game's own file, mus/Flowerman_Arrangement.ogg) from the start, in place of the fight's song
function knight_fl_om_song()
{
    var _f = "Flowerman_Arrangement.ogg";
    if (!knight_mus_ok() || !knight_music_exists(_f))
        return 0;
    // (a KF Song Pack song gives way to Flower Man)
    knight_kf_stop();
    knight_mus_cut_ext(20, true);
    global.batmusic[0] = snd_init(_f);
    global.batmusic[1] = mus_loop(global.batmusic[0]);
    global.knight_fl_song = _f;
    global.knight_fl_om.snd = global.batmusic[0];
    global.knight_fl_om.pos = 0;
    return 1;
}

// obj_knight_herocc's Draw (self: the hero) - obj_heroparent's own Draw with Omega Flowery's look: the outline in the cycling
// hue, his white sprite at 0.8, the additive rainbow pass (as Chapter 5 draws him), and his float. Returns false when it is
// not him in his Omega form (the hero's own Draw runs then).
function knight_cc_hero_draw()
{
    if (char != 5 || !knight_fl_om_on() || state == 8)
        return false;
    var _dy = knight_fl_om_float();
    var _spr = thissprite;
    var _fi = index;
    var _dx = 0;
    // (his Omega FIGHT: the Jarona's pose and offset, drawn by his own hero)
    var _ps = variable_struct_exists(global.knight_fl_om, "pose") ? global.knight_fl_om.pose : undefined;
    if (is_struct(_ps) && hurt != 1)
    {
        sprite_index = thissprite;
        image_index = index;
        image_blend = c_white;
        knight_fl_om_drawspr(_ps.spr, _ps.f, x + _ps.dx, y + _dy + (variable_struct_exists(_ps, "dy") ? _ps.dy : 0), max(image_alpha, 1));
        specdraw = 0;
        if (becomeflash == 0)
            flash = 0;
        becomeflash = 0;
        return true;
    }
    if (hurt == 1 && global.hp[global.char[myself]] > 0)
    {
        specdraw = 1;
        if (global.faceaction[myself] != 4)
        {
            _spr = hurtsprite;
            _fi = hurtindex;
        }
        else
        {
            thissprite = defendsprite;
            index = defendtimer;
            _spr = defendsprite;
            _fi = defendtimer;
        }
        _dx = -20 + (hurtindex * 10);
    }
    else
    {
        sprite_index = thissprite;
        image_index = index;
    }
    image_blend = c_white;
    // (a pose that is not a sprite: his idle, never nothing)
    if (!is_real(_spr) || !sprite_exists(_spr))
    {
        _spr = idlesprite;
        _fi = siner / 5;
    }
    knight_fl_om_drawspr(_spr, _fi, x + _dx, y + _dy, image_alpha);
    if (specdraw == 0 && flash == 1)
    {
        fsiner += 1;
        gpu_set_fog(true, c_white, 0, 1);
        draw_sprite_ext(_spr, _fi, x, y + _dy, 2, 2, 0, c_white, (-cos(fsiner / 5) * 0.4) + 0.6);
        gpu_set_fog(false, c_black, 0, 0);
    }
    specdraw = 0;
    if (becomeflash == 0)
        flash = 0;
    becomeflash = 0;
    return true;
}

function knight_fl_om_drawspr(_spr, _f, _x, _y, _al)
{
    if (_al <= 0 || !sprite_exists(_spr))
        return 0;
    var _ff = floor(_f) mod max(1, sprite_get_number(_spr));
    knight_om_outline(_spr, _ff, _x, _y, 2, 2, knight_om_hue(), _al);
    draw_sprite_ext(_spr, _ff, _x, _y, 2, 2, 0, c_white, 0.8 * _al);
    knight_om_chroma(_spr, _ff, _x, _y, 2, 2, 0.5 * _al);
    return 1;
}

// he becomes Omega Flowery for good
function knight_fl_om_become(_k)
{
    var _om = global.knight_fl_om;
    if (_om.on)
        return 0;
    _om.on = true;
    _om.trig = true;
    _om.cd = 0;
    var _s = _k.caster;
    var _h = knight_fl_hero(_k);
    if (i_ex(_k.m))
    {
        with (_k.m)
            instance_destroy();
    }
    _k.m = noone;
    // every one of his battle poses becomes Omega Flowery's (his hero and his registry entry, so nothing puts Flowery back)
    knight_fl_om_dress();
    if (i_ex(_h))
    {
        _h.image_alpha = 1;
        knight_om_orb(_h.x + 22, _h.y + 50, 8, 60, c_white, 12);
    }
    // Flower Man starts again from the top
    knight_fl_om_song();
    // stronger, not invincible
    var _mh = global.maxhp[5];
    global.maxhp[5] = ceil(_mh * 1.2);
    global.hp[5] = min(global.maxhp[5], global.hp[5] + ceil(global.maxhp[5] * 0.3));
    if (_s >= 0 && _s < 3)
    {
        global.battleat[_s] = ceil(global.battleat[_s] * 1.25);
        global.battledf[_s] = ceil(global.battledf[_s] * 1.5);
        global.battlemag[_s] = ceil(global.battlemag[_s] * 1.2);
    }
    // his MAGIC is now only LAST JARONA, PRISM RUSH and his heal SMILE AGAIN (no ACT, no other technique)
    // (build 50: in the Elec Knight's phase 5 his ACT entry stays first, for Unleash)
    global.knight_fl_actmenu = 0;
    knight_fl_list_set(knight_fl_normal_list());
    scr_spellmenu_setup();
    // (the scene's OMEGA FLOWERY! line has just played - the 2-second rule in knight_fl_voice keeps it to once)
    knight_fl_voice("omega_flowery");
    return 1;
}

// every frame of a fight: the scene's text, LAST JARONA's charging (one turn less at the end of each enemy turn)
function knight_fl_om_tick()
{
    if (!variable_global_exists("knight_fl_om") || !is_struct(global.knight_fl_om))
        return 0;
    var _om = global.knight_fl_om;
    if (_om.wait == 1 && !w_ex())
    {
        _om.wait = 0;
        with (obj_knight_enemy)
            scr_mnendturn();
    }
    _om.mn = global.mnfight;
    if (_om.on)
    {
        // a battle's heroes can be made again: dress the new one too, and put his aura back on it
        knight_fl_om_dress();
        knight_fl_om_song_keep();
        _om.ft++;
        with (obj_knight_herocc)
        {
            // once nobody else in the party is up, he moves to the middle of the party's line (where Susie stands in a
            // party of three) and floats there
            if (char == 5 && global.knight_fl_om.gt < 0 && !knight_fl_busy() && knight_fl_om_alone())
                knight_fl_om_target(id);
            if (char == 5)
                knight_fl_om_place(id);
        }
    }
    return 1;
}

// ---------- the Weird Route's end with Flowery: his last clash with the Knight (kspell 29) ----------
// In place of the black and red screen: the Knight and he face each other (the Violet Knight's colour on the screen's edges,
// the music fading), he says his piece, the Knight raises its blade, he charges with his Jarona, they CLASH in the middle
// (rings, sparks, shakes, both pushing), it grows, and he breaks through: explosions on the Knight - then the Knight's own
// death scene of this fight (its dissolve, the fade, the fight's end), started where it would be after its black screen.
function knight_fl_clash(_k, _a, _p, _hx, _hy)
{
    var _t = _k.t;
    var _ke = instance_find(obj_knight_enemy, 0);
    if (_ke == noone)
        return knight_fl_end(_k);
    var _kx = _ke.x, _ky = _ke.y;
    var _mx = lerp(_hx + 40, _kx + 60, 0.5);
    if (_t == 1)
    {
        _k.m = knight_fl_mk(_k, knight_fl_om_on() ? _a.omega : _a.ready, _hx, _hy, knight_fl_om_on() ? 20 : 0, 0);
        _k.km = scr_dark_marker(_kx, _ky, _ke.sprite_index);
        _k.km.image_index = _ke.image_index;
        _k.km.image_speed = 0;
        _k.km.depth = _ke.depth;
        _ke.visible = 0;
        with (instance_create_depth(_kx + 75, _ky + 50, -9999, obj_knight_vignette))
        {
            r = 118;
            g = 0;
            b = 255;
        }
        if (variable_global_exists("batmusic") && is_array(global.batmusic))
            mus_volume(global.batmusic[1], 0, 60);
    }
    if (_t == 16)
        knight_say(5, "...Heh.^2&Last one,&pal./%", 2);
    if (_t == 80)
    {
        // the Knight raises its blade
        var _ks = knight_wr_marker_sprite();
        if (i_ex(_k.km) && knight_cc_spr(_ks))
        {
            _k.km.sprite_index = _ks;
            _k.km.image_index = 0;
        }
        snd_play(snd_wing);
    }
    if (_t == 100)
    {
        // they charge
        knight_fl_voice("last_jarona");
        if (i_ex(_k.m))
        {
            _k.m.image_index = knight_fl_om_on() ? 6 : 0;
            if (!knight_fl_om_on())
            {
                _k.m = knight_fl_drop(_k, _k.m);
                _k.m = knight_fl_mk(_k, _a.jarona, _hx, _hy, 5, 0);
            }
            var _fx = _mx - 60;
            with (_k.m)
                scr_lerpvar("x", x, _fx, 10, 2, "in");
        }
        if (i_ex(_k.km))
        {
            _k.km.image_index = 1;
            var _kmx = _mx - 60;
            with (_k.km)
                scr_lerpvar("x", x, _kmx, 10, 2, "in");
        }
        snd_play_x(snd_knight_cut, 1, 1.2);
    }
    if (_t > 100 && _t < 110 && i_ex(_k.m) && (_t mod 2) == 0)
        knight_fl_trail(_k.m, knight_fl_om_on() ? knight_om_hue() : make_color_rgb(70, 130, 255));
    // the clash
    if (_t >= 110 && _t < 166)
    {
        var _cx = _mx + 10, _cy = _hy + 40;
        if (_t == 110)
        {
            if (i_ex(_k.m) && knight_fl_om_on())
                _k.m.image_index = 9;
            snd_play(snd_impact);
            snd_play_x(snd_bell, 0.8, 1.2);
            instance_create(0, 0, obj_shake);
            knight_om_orb(_cx, _cy, 6, 40, c_white, 10);
        }
        if ((_t mod 6) == 4)
        {
            var _n = (_t - 110) div 6;
            knight_om_ring(_cx, _cy, 6, 60 + (_n * 14), 4 + (_n div 3), (_n mod 2) ? c_white : knight_fl_fcol(_n), 14);
            knight_fl_fx1(asset_get_index("spr_bellsparkle"), _cx + irandom_range(-14, 14), _cy + irandom_range(-24, 24), 2, c_white, 0.5);
            snd_pitch(snd_play(snd_impact), 0.8 + (_n * 0.05));
        }
        // both pushing
        if (i_ex(_k.m))
            _k.m.x = (_mx - 60) + irandom_range(-2, 2) + ((_t >= 150) ? 6 : 0);
        if (i_ex(_k.km))
            _k.km.x = (_mx - 60) + irandom_range(-2, 2) + ((_t >= 150) ? 6 : 0);
        if (_t == 150)
        {
            knight_fl_snd("snd_punchheavythunder");
            instance_create(0, 0, obj_shake);
            knight_om_ring(_cx, _cy, 10, 200, 8, knight_om_hue(), 24);
        }
    }
    if (_t == 166)
    {
        // he breaks through
        knight_fl_voice("take_that");
        if (i_ex(_k.m))
        {
            _k.m.image_index = knight_fl_om_on() ? 17 : 5;
            var _bx = _kx + 60;
            with (_k.m)
                scr_lerpvar("x", x, _bx, 8, 2, "out");
        }
        if (i_ex(_k.km))
        {
            with (_k.km)
            {
                scr_oflash();
                scr_lerpvar("x", x, _kx, 14, 2, "out");
            }
            _k.km.sprite_index = _ke.sprite_index;
        }
    }
    if (_t == 172)
    {
        for (var _e = 0; _e < 3; _e++)
        {
            knight_om_boom(_kx + 119 + irandom_range(-30, 30), _ky + 76 + irandom_range(-30, 30), 0.9 - (_e * 0.2));
            knight_om_ring(_kx + 119, _ky + 76, 10, 220 + (_e * 110), 8, make_color_hsv((random_range(1, 7) / 7) * 255, 255, 255), 30 + (_e * 10));
        }
        knight_om_orb(_kx + 119, _ky + 76, 10, 90, c_white, 16);
        knight_fl_snd("snd_explosion_mmx3");
        snd_play_x(snd_knight_hurt, 0.8, 0.4);
        instance_create(0, 0, obj_shake);
    }
    if (_t == 196)
    {
        // the Knight's own death scene from its dissolve on (its black-and-red screen is left out: an invisible stand-in)
        var _bl = scr_dark_marker(0, 0, spr_pxwhite);
        _bl.image_alpha = 0;
        _bl.visible = 0;
        var _km = _k.km;
        _k.km = noone;
        if (i_ex(_km))
            _km.image_blend = c_white;
        with (obj_knight_enemy)
        {
            whatsact3 = "deathanim";
            acting = 3;
            blind_soon = _bl;
            knightmarker = _km;
            visible = 0;
            actcon = 64;
            alarm[4] = 20;
        }
        if (i_ex(_k.m))
        {
            var _hb = _hx;
            with (_k.m)
                scr_lerpvar("x", x, _hb, 14, 2, "out");
        }
    }
    if (_t >= 214)
        knight_fl_end(_k);
    return 1;
}

// Honey Kiss: the team feels better - every member who is up heals _f of their max HP (the game's own heal, its numbers and
// sparkle; a member the Knight took or who is down is left as they are)
function knight_fl_team_heal(_f)
{
    for (var _i = 0; _i < 3; _i++)
    {
        var _c = global.char[_i];
        if (_c == 0 || global.hp[_c] <= 0 || !i_ex(global.charinstance[_i]) || knight_wr_slain(_c))
            continue;
        var _n = max(1, ceil(global.maxhp[_c] * _f));
        var _got = scr_heal(_i, _n);
        with (global.charinstance[_i])
        {
            var _ha = instance_create(x, y, obj_healanim);
            _ha.target = id;
            var _dw = scr_dmgwriter_selfchar();
            with (_dw)
            {
                delay = 8 + (_i * 4);
                type = 3;
            }
            _dw.damage = _got;
            if (global.hp[_c] >= global.maxhp[_c])
            {
                with (_dw)
                    specialmessage = 3;
            }
        }
    }
    return 1;
}


// ---------- build 50: his ACT - the first MAGIC entry "ACT" (27) opens his own ACT list in the MAGIC menu ----------
// (Check 28, HoldBreath 29, in the Elec Knight's phase 5 Unleash 26 and Bravery 30, then F-Action 22). X goes back to his
// MAGIC; once he has picked one (or his turn is over) his MAGIC is his own again.
function knight_fl_elec5()
{
    if (!variable_global_exists("knight_variant") || global.knight_variant != 2 || !instance_exists(obj_knight_enemy))
        return false;
    var _e = instance_find(obj_knight_enemy, 0);
    return variable_instance_exists(_e, "phase") && _e.phase == 5 && variable_instance_exists(_e, "phasing") && _e.phasing;
}

// Unleash can still go off: phase 5, nobody else's Unleash under way (Kris's ACT, Susie's, an earlier one this turn)
function knight_fl_unleash_ok()
{
    if (!knight_fl_elec5() || instance_exists(obj_purify_event))
        return false;
    var _e = instance_find(obj_knight_enemy, 0);
    return !(variable_instance_exists(_e, "unleash_con") && _e.unleash_con != 0);
}

function knight_fl_breath()
{
    if (!instance_exists(obj_knight_enemy))
        return 0;
    var _e = instance_find(obj_knight_enemy, 0);
    return variable_instance_exists(_e, "holdbreathcount") ? _e.holdbreathcount : 0;
}

function knight_fl_act_on()
{
    return variable_global_exists("knight_fl_actmenu") && global.knight_fl_actmenu == 1;
}

function knight_fl_act_list()
{
    var _l = [28, 29];
    if (knight_fl_elec5())
    {
        array_push(_l, 26);
        array_push(_l, 30);
    }
    array_push(_l, 22);
    return _l;
}

// his MAGIC when it is not the ACT list: ACT + his chosen techniques; as OMEGA FLOWERY only LAST JARONA, PRISM RUSH and
// SMILE AGAIN (with the ACT entry first only in the Elec Knight's phase 5, so Unleash can still be used)
function knight_fl_normal_list()
{
    if (knight_fl_om_on())
        return knight_fl_elec5() ? [27, 23, 19, 25] : [23, 19, 25];
    var _d = knight_cc(5);
    var _o = [is_undefined(_d) ? 27 : _d.action];
    var _l = knight_cc_spl(5);
    for (var _j = 0; _j < 12 && array_length(_o) < 12; _j++)
    {
        if (_l[_j] != 0)
            array_push(_o, _l[_j]);
    }
    return _o;
}

function knight_fl_list_set(_l)
{
    for (var _i = 0; _i < 12; _i++)
        global.spell[5][_i] = (_i < array_length(_l)) ? _l[_i] : 0;
    return 1;
}

// knight_kris_actpick: ACT picked in his MAGIC - the list becomes his ACTs, the cursor on the first
function knight_fl_act_open()
{
    knight_fl_list_set(knight_fl_act_list());
    global.knight_fl_actmenu = 1;
    scr_spellmenu_setup();
    global.bmenucoord[2][global.charturn] = 0;
    return true;
}

function knight_fl_act_close()
{
    global.knight_fl_actmenu = 0;
    knight_fl_list_set(knight_fl_normal_list());
    scr_spellmenu_setup();
    return 1;
}

function knight_fl_act_tick()
{
    if (!variable_global_exists("charturn") || !variable_global_exists("bmenuno"))
        return 0;
    var _mine = (global.myfight == 0 && global.charturn >= 0 && global.charturn < 3 && global.char[global.charturn] == 5);
    if (!knight_fl_act_on())
    {
        // OMEGA FLOWERY: the ACT entry comes and goes with the Elec Knight's phase 5 (never while his MAGIC is open)
        if (knight_fl_om_on() && !(_mine && global.bmenuno == 2))
        {
            var _want = knight_fl_normal_list();
            var _diff = false;
            for (var _wi = 0; _wi < 12; _wi++)
            {
                if (global.spell[5][_wi] != ((_wi < array_length(_want)) ? _want[_wi] : 0))
                    _diff = true;
            }
            if (_diff)
            {
                knight_fl_list_set(_want);
                scr_spellmenu_setup();
            }
        }
        return 0;
    }
    if (_mine && global.bmenuno == 2)
        return 0;
    // X in his ACT list (the battle went back to the main menu on his turn, nothing picked): back to his MAGIC, on ACT
    var _back = _mine && global.bmenuno == 0 && global.charaction[global.charturn] != 2 && instance_exists(obj_battlecontroller) && obj_battlecontroller.twobuffer >= -1;
    knight_fl_act_close();
    if (_back)
    {
        global.bmenuno = 2;
        global.bmenucoord[2][global.charturn] = 0;
    }
    return 1;
}

// kspell 32: UNLEASH - his ACT pose; once the battle text is gone the SOUL's light (obj_purify_event) comes from him, as it
// does from Kris or Susie (at its end the Knight's end_phase5); the spell phase waits until the light is over
function knight_fl_unleash(_k, _a, _hx, _hy)
{
    if (_k.t == 1)
    {
        _k.m = knight_fl_mk(_k, _a.act, _hx, _hy, 0, 0);
        _k.u = knight_fl_unleash_ok() ? 0 : -1;
    }
    if (_k.u == -1)
    {
        if (_k.t >= 26)
            knight_fl_end(_k);
        return 1;
    }
    with (obj_spellphase)
        spelltimer = 0;
    if (_k.u == 0 && (!instance_exists(obj_writer) || _k.t >= 90))
    {
        _k.u = 1;
        if (i_ex(_k.m))
        {
            with (_k.m)
                scr_oflash();
        }
        instance_create(_hx + 30, _hy + 50, obj_purify_event);
        knight_fl_voice("leaf_it_to_me");
    }
    if (_k.u == 1 && !instance_exists(obj_purify_event))
        knight_fl_end(_k);
    return 1;
}
