// ===== Weird Route for every fight and every party, and party-aware fixes for the game code (build 37; party order: build 38) =====

// ---------- the SOUL holder ----------
// The battle heart flies out of (and back into) Kris; without Kris it is the party leader's.
function knight_soul_hero()
{
    if (!variable_global_exists("charinstance") || !is_array(global.charinstance))
        return noone;
    var _s = knight_slot_of(1);
    if (_s < 0)
    {
        for (var _i = 0; _i < 3; _i++)
        {
            if (global.char[_i] != 0)
            {
                _s = _i;
                break;
            }
        }
    }
    if (_s < 0 || _s >= array_length(global.charinstance))
        return noone;
    var _h = global.charinstance[_s];
    if (i_ex(_h))
        return _h;
    return noone;
}

function knight_soul_x()
{
    var _h = knight_soul_hero();
    if (_h != noone)
        return _h.x + 10;
    return camerax() - 120;
}

function knight_soul_y()
{
    var _h = knight_soul_hero();
    if (_h != noone)
        return _h.y + 40;
    return cameray() + 170;
}

// The fights switch a member's ACT off with "global.battleactcount[1] = 0", i.e. for party slot 2 whoever is there. The magic menu
// is rebuilt right after (scr_spellmenu_setup counts the ACT rows again), so every slot starts from 0 instead.
function knight_actcount_fix()
{
    for (var _s = 0; _s < 3; _s++)
        global.battleactcount[_s] = 0;
}

// ---------- Shadow Mantle by party slot ----------
// The game's knight code checks Kris's armor for slot 1, Susie's for slot 2 and Ralsei's for slot 3, whoever stands there.
function knight_mantle_slot(_s)
{
    if (_s < 0 || _s > 2)
        return false;
    var _c = global.char[_s];
    if (_c < 1 || _c > 4)
        return false;
    return (global.chararmor1[_c] == 23 || global.chararmor2[_c] == 23);
}

function knight_mantle_party()
{
    for (var _s = 0; _s < 3; _s++)
    {
        if (knight_mantle_slot(_s))
            return true;
    }
    return false;
}

function knight_slot_down(_s)
{
    if (_s < 0 || _s > 2)
        return true;
    var _c = global.char[_s];
    if (_c < 1 || _c > 4)
        return true;
    return (global.hp[_c] < 1);
}

function knight_slot_up(_s)
{
    return !knight_slot_down(_s);
}

// Thorn Knight: every hit takes some max HP from whoever it hit (Noelle included). The mod's floors were 90 / 110 / 70 for
// Kris / Susie / Ralsei; Noelle's is 50. A floor never raises a max HP that is already lower (Half max HP, Weird stats).
function knight_thorn_erode(_s, _lost, _lostm)
{
    // build 47: an encounter's own HP rule - off in an online match (the room's MAX HP stays; found by t_kaizo47's ledger)
    if (_s < 0 || _s > 2 || knight_infhp() || !knight_enc_hp_rules())
        return 0;
    var _c = global.char[_s];
    if (_c < 1 || _c > 4)
        return 0;
    var _fl = [0, 90, 110, 70, 50];
    var _m0 = global.maxhp[_c];
    global.maxhp[_c] -= knight_mantle_slot(_s) ? _lostm : _lost;
    var _f = min(_fl[_c], _m0);
    if (global.maxhp[_c] < _f)
        global.maxhp[_c] = _f;
    return 1;
}

// ---------- THORNS rule: only hits count ----------
// knight_scale_taken runs once for every hit a party member takes; the Thorns tick only counts HP that was lost to a marked hit,
// so the ThornRing's drain (and anything else that is not a hit) never wears max HP down.
function knight_thorns_mark(_slot)
{
    if (!knight_active())
        return 0;
    var _r = global.krun;
    if (!variable_struct_exists(_r, "thhit") || _slot < 0 || _slot > 2)
        return 0;
    var _c = global.char[_slot];
    if (_c >= 1 && _c <= 5)
        _r.thhit[_c] = true;
    return 1;
}

// ---------- Weird Route: who stays to the end ----------
// The member on top of the party (build 38: the order matters): the Knight never takes them, and in the Violet Knight's
// Side B they finish the fight. The Knight takes the others from the bottom up.
function knight_wr_fin_of_party()
{
    for (var _i = 0; _i < 3; _i++)
    {
        var _c = global.char[_i];
        if (_c >= 1 && (_c <= 4 || knight_cc_ok(_c)))
            return _c;
    }
    return 1;
}

function knight_hero_obj(_c)
{
    switch (_c)
    {
        case 1: return obj_herokris;
        case 2: return obj_herosusie;
        case 3: return obj_heroralsei;
        case 4: return obj_heronoelle;
    }
    // build 50: the custom characters (Flowery, ...) share one hero object
    if (_c >= 5 && knight_cc_ok(_c))
        return obj_knight_herocc;
    return -4;
}

function knight_hero_char(_o)
{
    if (_o == obj_herokris)
        return 1;
    if (_o == obj_herosusie)
        return 2;
    if (_o == obj_heroralsei)
        return 3;
    if (_o == obj_heronoelle)
        return 4;
    if (_o == obj_knight_herocc)
        return 5;
    return 0;
}

function knight_char_alive(_c)
{
    return (scr_havechar(_c) && global.hp[_c] > 0);
}

// the name the battle shows for a member (the fights rename them: The Angel, The Cage, ...)
function knight_charname(_c)
{
    // build 50: in the Violet Knight's fight, Flowery is The Flower Man (its titles: The Cage, The Girl, The Prince, The Angel)
    if (_c >= 5 && knight_cc_ok(_c) && variable_global_exists("knight_variant") && global.knight_variant == 3 && instance_exists(obj_battlecontroller))
        return "The Flower Man";
    if (variable_global_exists("charname") && is_array(global.charname) && _c >= 0 && _c < array_length(global.charname) && is_string(global.charname[_c]) && global.charname[_c] != "")
        return global.charname[_c];
    return knight_char_proper(_c);
}

// the battle hero of a party member: its slot's instance, else the hero object's first instance (noone if absent)
function knight_hero_inst(_c)
{
    var _s = knight_slot_of(_c);
    if (_s >= 0 && variable_global_exists("charinstance") && is_array(global.charinstance) && _s < array_length(global.charinstance) && i_ex(global.charinstance[_s]))
        return global.charinstance[_s];
    var _o = knight_hero_obj(_c);
    if (_o != -4 && instance_exists(_o))
        return instance_find(_o, 0);
    return noone;
}

function knight_slot_inst(_s)
{
    if (_s >= 0 && _s < 3 && variable_global_exists("charinstance") && is_array(global.charinstance) && _s < array_length(global.charinstance) && i_ex(global.charinstance[_s]))
        return global.charinstance[_s];
    var _o = knight_hero_obj(global.char[_s]);
    if (_o != -4 && instance_exists(_o))
        return instance_find(_o, 0);
    return noone;
}

// balloon voice / position for a party member's speech bubble (Ralsei 74, Susie 75, Noelle 76: the game's own battle voices).
// Party members are on the left, so their balloon opens to the RIGHT of them with the tail pointing back at them (type 14 =
// side -1, what scr_heroblcon does). Susie's spot is the mod's own; Ralsei's is the game's (the Rouxls fight), Noelle has his size.
function knight_say(_c, _text, _rate)
{
    var _h = knight_hero_inst(_c);
    if (_h == noone)
        return noone;
    msgset(0, _text);
    var _b = noone;
    switch (_c)
    {
        case 2:
            global.typer = 75;
            _b = scr_enemyblcon(_h.x + 92, _h.y + 38, 14);
            break;
        case 3:
            global.typer = 74;
            _b = scr_enemyblcon(_h.x + 85, _h.y + 45, 14);
            break;
        case 4:
            global.typer = 76;
            _b = scr_enemyblcon(_h.x + 85, _h.y + 45, 14);
            break;
        default:
            if (knight_cc_ok(_c))
            {
                // build 50: a custom character (Flowery) - a balloon like Susie's, in his own voice
                global.knight_cc_typer = _c;
                global.typer = 303;
                _b = scr_enemyblcon(_h.x + 85, _h.y + 45, 14);
                break;
            }
            global.typer = 50;
            _b = scr_enemyblcon(_h.x + 90, _h.y + 40, 14);
            break;
    }
    if (i_ex(_b))
    {
        var _ke = instance_find(obj_knight_enemy, 0);
        _b.depth = (_ke != noone) ? (_ke.depth - 100) : -1000;
        if (_rate > 1)
        {
            with (obj_writer)
                rate = _rate;
        }
    }
    return _b;
}

// ---------- Violet Knight Side B for any party ----------
// Build 38: the party order decides. The member on top finishes the fight; the Knight takes the bottom member at the end of
// phase 1 and the next one up at the end of phase 2 (Kris too, when Kris is not on top). With Kris on top the mod's own Kris
// story plays (X-Slash once Susie falls). Otherwise the member on top gets a power-up scene and ends it with their own move.
// After every loss the others talk (Susie first) and learn (knight_learn_after); a lone member parries the blade instead.
function knight_vb_fin()
{
    if (variable_instance_exists(id, "vb_fin") && vb_fin > 0)
        return vb_fin;
    return knight_wr_fin_of_party();
}

function knight_vb_kris()
{
    return (knight_vb_fin() == 1);
}

// the hero object the Knight goes for (-4: only the member on top is left)
function knight_vb_victim(_n)
{
    var _c = knight_wr_bottom(knight_vb_fin());
    if (_c <= 0)
        return -4;
    return knight_hero_obj(_c);
}

function knight_vb_init()
{
    vb_fin = knight_wr_fin_of_party();
    vb_t = 0;
    vb_fin_idx = -1;
    vb_whospos = -4;
    vb_losses = 0;
    vb_q = [];
    vb_qi = 0;
    vb_sp = [];
    vb_after = 10;
    vb_dfl = 0;
}

// after the Knight's blade has landed and come back (knightkillcon 9): the others talk first (90), then the mod's scene for
// Kris (X-Slash, when Susie fell and Kris is on top) or the consequences (10)
function knight_vb_route9()
{
    var _v = knight_hero_char(kill_target);
    vb_after = 10;
    if (knight_vb_kris() && _v == 2)
        vb_after = 30;
    if (_v == 1)
        knight_hb_give();
    vb_sp = knight_talk_speakers(_v);
    vb_q = knight_talk_build(_v, vb_losses > 0);
    vb_qi = 0;
    vb_t = 0;
    return 90;
}

// the member whose "learned" line the finisher's power-up scene gives instead (no Kris, second loss)
function knight_vb_quiet()
{
    if (!knight_vb_kris() && phase >= 3)
        return knight_vb_fin();
    return 0;
}

// Kris is taken (not on top): the hurt stance while the blade comes
function knight_vb_hurt_kris()
{
    with (obj_herokris)
    {
        if (global.hp[1] > 0)
        {
            snd_play(snd_hurt1);
            scr_shakeobj();
        }
        idlesprite = spr_krisb_hurt;
    }
    var _ks = knight_slot_of(1);
    if (_ks >= 0 && global.hp[1] > 0)
        global.faceaction[_ks] = 5;
}

// only the member on top is left when the Knight comes for someone: it charges them and they knock the blade back (95-98)
function knight_vb_deflect_start()
{
    var _c = knight_vb_fin();
    var _h = knight_hero_inst(_c);
    if (_h == noone || !knight_wr_here(_c) || global.hp[_c] <= 0)
    {
        knight_vb_deflect_after();
        return 0;
    }
    vb_dfl = _c;
    visible = 0;
    knight_marker = scr_dark_marker(x, y, spr_roaringknight_attack_ol__v3);
    knight_marker.image_index = 1;
    var _tx = _h.x - 10;
    var _ty = _h.y - 10;
    with (knight_marker)
    {
        scr_lerpvar("x", x, _tx, 25, 7, "in");
        scr_lerpvar("y", y, _ty, 25, 7, "in");
    }
    snd_play_x(snd_knight_cut, 1, 1.5);
    vb_t = 0;
    knightkillcon = 95;
    return 1;
}

// after the parry (or when there was nobody to parry): what the mod did when there was nobody to take
function knight_vb_deflect_after()
{
    kill_skipped = 1;
    if (knight_vb_kris())
    {
        if (phase >= 3)
        {
            if (variable_instance_exists(id, "whatsact3") && whatsact3 == "xslash")
            {
                // Kris already has X-Slash (Susie fell first): the fight just goes on
                kill_target = -4;
                knightkillcon = 0;
                kill_skipped = 0;
                global.battlemsg[0] = "* The enemy became stronger.";
                scr_mnendturn();
                return 1;
            }
            kill_target = obj_herosusie;
            knightkillcon = 30;
        }
        else
        {
            kill_target = obj_heroralsei;
            knight_mus_cut(10);
            knightkillcon = 10;
        }
        return 1;
    }
    kill_target = -4;
    if (phase < 3)
        knight_mus_cut(10);
    knightkillcon = 10;
    return 1;
}

// the members' battle stances (Ralsei: his current hatless set spr_ralsei_*; spr_ralseib_* is his Chapter 1 look with the hat)
function knight_vb_ready_sprite(_c)
{
    switch (_c)
    {
        case 2: return spr_susieb_attackready_unhappy;
        case 3: return spr_ralsei_spellready;
        case 4: return spr_noelleb_spellready;
    }
    if (knight_cc_ok(_c))
        return knight_cc(_c).poses.spellready;
    return spr_krisb_attackready;
}

function knight_vb_idle_sprite(_c)
{
    switch (_c)
    {
        case 2: return spr_susieb_idle_serious;
        case 3: return spr_ralsei_idle;
        case 4: return (global.flag[456] > 0) ? spr_noelleb_idle_sideb : spr_noelleb_idle;
    }
    if (knight_cc_ok(_c))
        return knight_cc(_c).poses.idle;
    return spr_krisb_idle;
}

// the finisher: the member's learned double move when they have it (Susie's RUDER BUSTER, Ralsei's FIRESTORM), Noelle's SnowGrave
function knight_vb_fin_name(_c)
{
    switch (_c)
    {
        case 2: return knight_learned(2) ? "RuderBuster" : "RudeBuster";
        case 3: return knight_learned(3) ? "FireStorm" : "FireShock";
        case 4: return "SnowGrave";
    }
    if (_c >= 5)
        return "LastJarona";
    return "X-Slash";
}

function knight_vb_fin_upper(_c)
{
    switch (knight_vb_fin_name(_c))
    {
        case "RuderBuster": return "RUDER BUSTER";
        case "RudeBuster": return "RUDE BUSTER";
        case "FireStorm": return "FIRESTORM";
        case "FireShock": return "FIRESHOCK";
        case "SnowGrave": return "SNOWGRAVE";
        case "LastJarona": return "LAST JARONA";
    }
    return "X-SLASH";
}

function knight_vb_fin_spell(_c)
{
    switch (_c)
    {
        case 2: return 4;
        case 3: return 13;
        case 4: return 10;
    }
    if (_c >= 5)
        return 23;
    return 1;
}

function knight_vb_set_act(_c, _i, _name, _desc, _cost)
{
    if (_c == 2)
    {
        global.canactsus[myself][_i] = 1;
        global.actnamesus[myself][_i] = _name;
        global.actdescsus[myself][_i] = _desc;
        global.actcostsus[myself][_i] = _cost;
        global.actsimulsus[myself][_i] = 0;
        global.actactorsus[myself][_i] = 0;
    }
    if (_c == 3)
    {
        global.canactral[myself][_i] = 1;
        global.actnameral[myself][_i] = _name;
        global.actdescral[myself][_i] = _desc;
        global.actcostral[myself][_i] = _cost;
        global.actsimulral[myself][_i] = 0;
        global.actactorral[myself][_i] = 0;
    }
    if (_c == 4)
    {
        global.canactnoe[myself][_i] = 1;
        global.actnamenoe[myself][_i] = _name;
        global.actdescnoe[myself][_i] = _desc;
        global.actcostnoe[myself][_i] = _cost;
        global.actsimulnoe[myself][_i] = 0;
        global.actactornoe[myself][_i] = 0;
    }
    knight_actcount_fix();
    scr_spellmenu_setup();
}

// knightkillcon 10 without Kris (replaces the mod's Kris-only consequences)
function knight_vb_end_kill()
{
    knightkillcon = 0;
    kristitle = "Kris";
    susietitle = "Susie";
    ralseititle = "Ralsei";
    global.charname[1] = "Kris";
    global.charname[2] = "Susie";
    global.charname[3] = "Ralsei";
    global.charname[4] = "Noelle";
    var _vc = knight_hero_char(kill_target);
    if (_vc == 3)
    {
        ralseidownmessage = true;
        ral_dead = true;
    }
    if (_vc == 2)
    {
        susiedownmessage = true;
        sus_dead = true;
    }
    var _skip = (variable_instance_exists(id, "kill_skipped") && kill_skipped) || _vc == 0;
    var _who = (_vc == 4) ? "The Angel" : ((_vc == 0) ? "" : knight_vtitle(_vc));
    global.battlemsg[0] = _skip ? "* The enemy became stronger." : stringsetsub("* ~1 was completely obliterated.&* The enemy became stronger.", _who);
    if (_skip && variable_instance_exists(id, "vb_dfl") && vb_dfl > 0)
        global.battlemsg[0] = "* " + knight_vtitle(vb_dfl) + " stands alone.&* The enemy became stronger.";
    vb_dfl = 0;
    kill_skipped = 0;
    if (phase >= 3)
    {
        knightkillcon = 130;
        return 1;
    }
    with (obj_herosusie)
    {
        normalsprite = spr_susier_dark_unhappy;
        idlesprite = spr_susieb_idle_serious;
        defendsprite = spr_susieb_defend_unhappy;
        actreadysprite = spr_susieb_actready;
        attackreadysprite = spr_susieb_attackready_unhappy;
        attacksprite = spr_susieb_attack_serious;
        if (global.charweapon[2] == 0)
            idlesprite = spr_susieb_idle_unarmed_unhappy;
        itemsprite = spr_susieb_item_unhappy;
        itemreadysprite = spr_susieb_itemready_unhappy;
        spellreadysprite = spr_susieb_spellready_unhappy;
        spellsprite = spr_susieb_spell_unhappy;
        remspellsprite = spr_susieb_spell_unhappy;
    }
    knight_mus_switch(violetknight_sideb, 60);
    scr_mnendturn();
    return 1;
}

// unlock the finisher of the member on top: their learned move's row when they have it, else Susie's first free row (her talk
// may be gone) and Ralsei's / Noelle's talk row (index 0)
function knight_vb_fin_unlock()
{
    var _c = knight_vb_fin();
    if (knight_cc_ok(_c))
    {
        // build 50: a custom character finishes with its own technique: Flowery's LAST JARONA takes the place of his
        // ACTION (F-ACTION) in his MAGIC
        global.spell[_c][0] = knight_vb_fin_spell(_c);
        scr_spellmenu_setup();
        vb_fin_idx = 0;
        whatsact3 = "finisher";
        return 1;
    }
    var _i = knight_act_find(_c, knight_vb_fin_name(_c));
    if (_i < 0)
        _i = (_c == 2) ? knight_act_first_free(2) : 0;
    if (_i < 0)
        _i = 0;
    var _d = "Physical#damage";
    if (_c == 3)
        _d = "Fire#damage";
    if (_c == 4)
        _d = "Ice#damage";
    if (knight_learned(_c) && _c != 4)
        _d = (_c == 2) ? "Rude x2#Damage" : "Fire x2#Damage";
    knight_vb_set_act(_c, _i, knight_vb_fin_name(_c), _d, 62.5);
    vb_fin_idx = _i;
    whatsact3 = "finisher";
}

// the scenes added to the Violet Knight's Side B: the talk after a loss (90-92), the lone member's parry (95-98) and the
// finisher's power-up (130-145)
function knight_vb_extra()
{
    if (!v_sideb)
        return 0;
    var _c = knight_vb_fin();
    // the others talk after a loss: Susie first, then the rest in party order (knight_vb_route9 built the lines)
    if (knightkillcon == 90)
    {
        vb_t++;
        if (vb_t >= 20 && !w_ex())
        {
            if (vb_qi < array_length(vb_q))
            {
                var _ln = vb_q[vb_qi];
                vb_qi++;
                knight_talk_fx(_ln[0], _ln[3]);
                knight_say(_ln[0], _ln[1], _ln[2]);
                vb_t = 15;
            }
            else
            {
                knight_talk_end(vb_sp);
                knightkillcon = 91;
            }
        }
    }
    // ...then what they learn
    if (knightkillcon == 91 && !w_ex())
    {
        var _msg = knight_learn_after(knight_hero_char(kill_target), knight_vb_quiet(), phase < 3);
        vb_losses++;
        if (_msg != "")
        {
            scr_speaker("noone");
            knight_msg_pages(_msg);
            scr_battletext();
        }
        knightkillcon = 92;
    }
    if (knightkillcon == 92 && !w_ex())
        knightkillcon = vb_after;
    // the lone member's parry (knight_vb_deflect_start sent the shadow at them)
    if (knightkillcon == 95)
    {
        vb_t++;
        if (vb_t >= 24)
        {
            knightkillcon = 96;
            vb_t = 0;
            knight_dfl_hit(vb_dfl, knight_marker, x, y);
            var _dh = knight_hero_inst(vb_dfl);
            if (_dh != noone)
            {
                with (_dh)
                    scr_oflash();
            }
        }
    }
    if (knightkillcon == 96)
    {
        vb_t++;
        if (vb_t >= 26)
        {
            knightkillcon = 97;
            vb_t = 0;
            var _bx = x;
            var _by = y;
            if (i_ex(knight_marker))
            {
                with (knight_marker)
                {
                    scr_lerpvar("x", x, _bx, 12, 2, "in");
                    scr_lerpvar("y", y, _by, 12, 2, "in");
                }
            }
        }
    }
    if (knightkillcon == 97)
    {
        vb_t++;
        if (vb_t >= 14)
        {
            if (i_ex(knight_marker))
            {
                with (knight_marker)
                    instance_destroy();
            }
            knight_marker = -4;
            visible = 1;
            knight_dfl_pose(vb_dfl, false);
            scr_speaker("noone");
            msgset(0, knight_dfl_text(vb_dfl));
            scr_battletext();
            knightkillcon = 98;
        }
    }
    if (knightkillcon == 98 && !w_ex())
        knight_vb_deflect_after();
    // the finisher's power-up scene (the X-Slash flurry in Kris's colours, for the member who is left)
    // build 50: Flowery on top - his own power-up is his transformation: OMEGA FLOWERY (his last stand scene), LAST JARONA
    // unlocked; the turn goes on when its text is read (knight_fl_om_tick)
    if (knightkillcon == 130 && _c == 5 && knight_fl_laststand_force())
    {
        knightkillcon = 0;
        knight_vb_fin_unlock();
        global.tempflag[82] = 1;
        return 1;
    }
    if (knightkillcon == 130)
    {
        knightkillcon = 130.5;
        var _fs = knight_slot_of(_c);
        if (_fs >= 0 && global.hp[_c] <= 0)
        {
            global.hp[_c] = 1;
            scr_revive(_fs);
        }
        with (knight_hero_obj(_c))
        {
            visible = 1;
            scr_minishakeobj();
        }
        snd_play(snd_wing);
        scr_delay_var("knightkillcon", 131, global.tempflag[82] ? 15 : 30);
    }
    if (knightkillcon == 131)
    {
        knightkillcon = 131.5;
        var _rdy = knight_vb_ready_sprite(_c);
        with (knight_hero_obj(_c))
        {
            idlesprite = _rdy;
            scr_shakeobj();
        }
        snd_play(snd_noise);
        scr_delay_var("knightkillcon", 132, global.tempflag[82] ? 20 : 45);
    }
    if (knightkillcon >= 132 && knightkillcon <= 140 && frac(knightkillcon) == 0)
    {
        var _n = knightkillcon - 132;
        var _delays = [14, 14, 10, 9, 8, 6, 4, 3, 3];
        if (_n == 0)
            _cutxslashdmg = irandom_range(76, 85);
        else
            _cutxslashdmg = ceil(_cutxslashdmg * ((_n >= 6) ? 1.05 : 1.1));
        knight_vb_hit(_c, _n);
        knightkillcon += 0.5;
        scr_delay_var("knightkillcon", knightkillcon + 0.5, _delays[_n]);
        if (_n == 8)
        {
            with (instance_create_depth(x + 75, y + 50, -9999, obj_knight_vignette))
            {
                r = 118;
                g = 0;
                b = 255;
            }
            snd_play_x(snd_knight_hurt, 0.7, 0.4);
            snd_play_x(snd_knight_hurtb, 0.6, 0.5);
            vignette_count += 1;
        }
    }
    if (knightkillcon == 141)
    {
        knightkillcon = 141.5;
        scr_act_charsprite_end();
        knight_cc_pose_marker_end();
        scr_delay_var("knightkillcon", 142, 20);
    }
    if (knightkillcon == 142)
    {
        knightkillcon = 142.5;
        var _idl = knight_vb_idle_sprite(_c);
        with (knight_hero_obj(_c))
        {
            idlesprite = _idl;
            scr_minishakeobj();
        }
        snd_play(snd_bump);
        scr_delay_var("knightkillcon", 143, global.tempflag[82] ? 20 : 40);
    }
    if (knightkillcon == 143)
    {
        knightkillcon = 144;
        scr_speaker("noone");
        var _nm = knight_charname(_c);
        msgset(0, "* (" + _nm + " will now use \\cY" + knight_vb_fin_upper(_c) + "\\cW.)/%");
        scr_battletext();
        global.tempflag[82] = 1;
    }
    if (knightkillcon == 144 && !w_ex())
    {
        knightkillcon = 0;
        knight_vb_fin_unlock();
        if (!audio_is_playing(global.batmusic[1]))
            knight_mus_switch(violetknight_sideb, 60);
        scr_mnendturn();
    }
    return 1;
}

// one hit of the power-up flurry: the member's attack / spell pose and a slash in their colour
function knight_vb_hit(_c, _n)
{
    var _nm = "susie";
    var _spr = spr_susieb_attack;
    var _col = make_color_rgb(234, 121, 200);
    if (_c == 3)
    {
        _nm = "ralsei";
        _spr = spr_ralsei_spell;
        _col = make_color_rgb(96, 255, 128);
    }
    if (_c == 4)
    {
        _nm = "noelle";
        _spr = spr_noelleb_spell;
        _col = make_color_rgb(150, 230, 255);
    }
    if (_n > 0)
        scr_act_charsprite_end();
    if (knight_cc_ok(_c))
    {
        var _ch = knight_hero_inst(_c);
        if (_ch != noone)
            knight_cc_pose_marker(_ch, knight_cc_flurry_spr(_c), 0.5);
        _col = knight_cc_barcolor(_c);
    }
    var _o = knight_cc_ok(_c) ? -4 : knight_hero_obj(_c);
    if (i_ex(_o))
    {
        krs = scr_act_charsprite(_nm, _spr, 0.25, 1);
        if (i_ex(krs))
            krs.depth = _o.depth + 1;
    }
    snd_pitch(snd_play(snd_scytheburst), ((_n mod 2) == 0) ? 1.2 : 0.8);
    att = instance_create(x + 119, y + 76, obj_basicattack);
    att.image_xscale = ((_n mod 2) == 0) ? 2 : -2;
    att.image_yscale = 2;
    att.image_blend = _col;
    var _cs = knight_slot_of(_c);
    caster = (_cs >= 0) ? _cs : 0;
    global.hittarget[20] = 0;
    scr_damage_enemy(0, _cutxslashdmg);
}

// the finisher of the member on top (no Kris): after the Roaring it ends the fight; before it, it is their own move
// (RUDER BUSTER / FIRESTORM cast twice). Runs before the other S / R / N-Actions and uses the action up.
function knight_vb_acts()
{
    if (!v_sideb || knight_vb_kris())
        return 0;
    if (vb_fin_idx < 0)
        return 0;
    var _c = knight_vb_fin();
    var _hit = false;
    if (_c == 2 && actingsus == (vb_fin_idx + 1) && actconsus == 1)
    {
        _hit = true;
        actconsus = 0;
    }
    if (_c == 3 && actingral == (vb_fin_idx + 1) && actconral == 1)
    {
        _hit = true;
        actconral = 0;
    }
    if (_c == 4 && actingnoe == (vb_fin_idx + 1) && actconnoe == 1)
    {
        _hit = true;
        actconnoe = 0;
    }
    if (!_hit)
        return false;
    if (haveusedroaring && chargeupcon == 0)
    {
        // the end: the same black-screen death of the Knight as Kris's X-Slash
        whatsact3 = "deathanim";
        acting = 3;
        actcon = 0;
        return true;
    }
    // before the Roaring the finisher is the member's own spell (twice for a learned move), paid by the ACT's TP
    var _s = knight_act_slot(_c);
    var _sp = knight_vb_fin_spell(_c);
    if (_s >= 0)
    {
        global.faceaction[_s] = 2;
        global.charaction[_s] = 2;
        global.charspecial[_s] = _sp;
        global.chartarget[_s] = 0;
        global.acting[_s] = 0;
        var _fn = knight_vb_fin_name(_c);
        if (_fn == "RuderBuster" || _fn == "FireStorm")
            knight_dbl_set(_s, _sp);
    }
    msgset(0, "* " + knight_charname(_c) + ((_c == 3 || _c >= 5) ? " gathered his strength!/%" : " gathered her strength!/%"));
    scr_battletext_default();
    actcon = 1;
    return true;
}

// the member who finishes the Knight gets the mod's joke reward (300-499 max HP; the hub puts stats back after the fight)
function knight_vb_fin_char()
{
    if (variable_instance_exists(id, "vb_fin") && vb_fin > 0)
        return vb_fin;
    return 1;
}

// ---------- Kaizo Knight Side B without Kris ----------
// Kris's X-Slash ACT has nobody to use it without Kris: Susie gets the same deal on her own S-Action list (her Rude Buster for 25% TP).
function knight_kz_init()
{
    kz_rb = -1;
    if (!k_sideb || scr_havechar(1) || !scr_havechar(2))
        return 0;
    for (var _i = 0; _i < 6; _i++)
    {
        if (global.canactsus[myself][_i] == 0)
        {
            kz_rb = _i;
            break;
        }
    }
    if (kz_rb < 0)
        return 0;
    knight_vb_set_act(2, kz_rb, "RudeBuster", "Physical#damage", 62.5);
    return 1;
}

function knight_kz_acts()
{
    if (!variable_instance_exists(id, "kz_rb") || kz_rb < 0)
        return 0;
    if (actingsus != (kz_rb + 1) || actconsus != 1)
        return 0;
    actconsus = 0;
    var _s = knight_soul_slot(2);
    if (_s >= 0)
    {
        global.faceaction[_s] = 2;
        global.charaction[_s] = 2;
        global.charspecial[_s] = 4;
        global.chartarget[_s] = 0;
        global.acting[_s] = 0;
    }
    msgset(0, "* Susie gripped her axe tight!/%");
    scr_battletext_default();
    actcon = 1;
    return 1;
}

// ---------- Weird Route for the knights without a Side B (Normal, Supercharged, Thorn, Cyan) ----------
// Halfway through the fight's attack list the Knight takes one member, like the Violet Knight's Side B does. Build 38: the
// party order decides: the bottom member goes first, the member on top is never taken (nor the last one standing). The others
// talk (Susie first) and learn their moves, the Knight hits 25% harder from then on, and the member who is lost cannot be healed
// back this fight. When only one member is left (a solo run at halfway, or a two-member party at about 3/4 of the list) the Knight
// charges that member instead and they knock the blade back: nobody dies.
function knight_wr_reset(_r)
{
    _r.wr = { on: false, st: 0, t: 0, vic: 0, vslot: -1, mk: noone, q: [], qi: 0, mult: 1, done: false, at: 99, at2: 99, dfl: false, sp: [], turn: -1,
              look: false, slain: [false, false, false, false, false, false], k: noone, kx: 0, ky: 0 };
}

function knight_wr_setup(_r)
{
    if (!variable_struct_exists(_r, "wr") || !is_struct(_r.wr))
        knight_wr_reset(_r);
    var _reg = knight_reg(knight_cur_knight());
    var _w = _r.wr;
    // build 48: never for the Normal Knight - it plays Chapter 3's fight, where nobody in the party can be taken.
    // build 50: never for ANY knight - only the Violet Knight's own Side B takes party members (its own code, not this);
    // the Supercharged, Thorn and Cyan Knights no longer take anyone, Weird Route or not
    _w.on = false;
    var _p = _reg.pace;
    _w.at = (_p.tmin > 0) ? ceil(_p.tmin / 2) : 6;
    _w.at2 = max(_w.at + 1, (_p.tmin > 0) ? ceil((_p.tmin * 3) / 4) : 9);
}

// the knight is at or under its Roaring gate (its Roaring starts at the end of this enemy turn or has been set up already)
function knight_wr_gate_now()
{
    if (!i_ex(obj_knight_enemy) || global.monstermaxhp[0] <= 0)
        return false;
    var _p = knight_pace_now(knight_cur_knight());
    if (_p.tmin <= 0)
        return false;
    return global.monsterhp[0] <= floor(global.monstermaxhp[0] * _p.gate);
}

// end of every enemy turn (scr_mnendturn): start a scene when it is time, freezing the battle like the Violet Knight does
function knight_wr_turnend()
{
    if (!knight_active())
        return 0;
    var _r = global.krun;
    if (_r.state != "battle" || !variable_struct_exists(_r, "wr") || !is_struct(_r.wr))
        return 0;
    var _w = _r.wr;
    if (!_w.on || (_w.st != 0 && _w.st != 9))
        return 0;
    if (!i_ex(obj_knight_enemy) || knight_roared())
        return 0;
    // the knight fighting now is the Normal Knight (a Remix or Tag Team switches knights mid-battle): it never takes anyone
    if (knight_reg(knight_cur_knight()).key == "base")
        return 0;
    if (global.myfight != 0 || global.mnfight != 0)
        return 0;
    var _v = 0;
    var _st = 0;
    // halfway / three quarters through the attack list, or as soon as a strong party has the knight at its Roaring gate
    // (build 39 lets a very strong party reach the Roaring a little early; the scenes come before it instead of never)
    var _gate = knight_wr_gate_now();
    if (!_w.done)
    {
        if (_r.eturns < _w.at && !_gate)
            return 0;
        _v = knight_wr_pick();
        _st = 1;
        if (_v == 0)
        {
            _v = knight_wr_lone();
            _st = 21;
        }
    }
    else if (!_w.dfl && _r.eturns > _w.turn && (_r.eturns >= _w.at2 || _gate))
    {
        _v = knight_wr_lone();
        _st = 21;
    }
    if (_v == 0)
        return 0;
    if (_st == 21 && global.hp[_v] <= 0)
        return 0;
    _w.vic = _v;
    _w.vslot = knight_slot_of(_v);
    _w.st = _st;
    _w.t = 0;
    _w.turn = _r.eturns;   // a second scene (the parry) waits for another enemy turn
    global.myfight = 99;
    global.mnfight = 99;
    global.charturn = -1;
    return 1;
}

// the member the Knight takes: the lowest one still here (bottom slot first) who is not on top, as long as somebody else stays up
function knight_wr_pick()
{
    var _top = knight_wr_fin_of_party();
    for (var _s = 2; _s >= 0; _s--)
    {
        var _c = global.char[_s];
        if (_c == _top || !knight_wr_here(_c))
            continue;
        for (var _o = 0; _o < 3; _o++)
        {
            var _oc = global.char[_o];
            if (_oc != 0 && _oc != _c && knight_wr_here(_oc) && global.hp[_oc] > 0)
                return _c;
        }
    }
    return 0;
}

function knight_wr_marker_sprite()
{
    var _key = knight_active() ? knight_reg(knight_cur_knight()).key : "";
    switch (_key)
    {
        case "kaizo": return spr_roaringknight_attack_ol__v1;
        case "violet": return spr_roaringknight_attack_ol__v3;
        case "thorn": return spr_roaringknight_attack_ol__v4;
        case "cyan": return spr_roaringknight_attack_ol__v5;
    }
    return spr_roaringknight_attack_ol;
}

function knight_wr_slay(_w)
{
    var _c = _w.vic;
    _w.slain[_c] = true;
    for (var _s = 0; _s < 3; _s++)
    {
        if (global.char[_s] != _c)
            continue;
        var _h = knight_slot_inst(_s);
        if (_h != noone)
        {
            var _d = instance_create(_h.x, _h.y, obj_deathanim);
            _d.sprite_index = _h.sprite_index;
            _d.image_index = _h.image_index;
            _d.depth = _h.depth - 1;
            _d.image_xscale = 2;
            _d.image_yscale = 2;
            _h.visible = 0;
        }
        global.faceaction[_s] = 8;
    }
    global.hp[_c] = -9999;
    for (var _s = 0; _s < 3; _s++)
    {
        if (global.char[_s] == _c)
            scr_dead(_s);
    }
    // Kris is gone: the others get HoldBreath (only Kris had it)
    if (_c == 1)
    {
        with (obj_knight_enemy)
            knight_hb_give();
        scr_spellmenu_setup();
    }
}

// a member the Knight has taken cannot be healed back in this fight (items, spells, passives)
function knight_wr_noheal(_slot)
{
    if (!knight_active() || _slot < 0 || _slot > 2)
        return false;
    var _r = global.krun;
    if (!variable_struct_exists(_r, "wr") || !is_struct(_r.wr) || _r.state != "battle")
        return false;
    var _c = global.char[_slot];
    return (_c >= 1 && _c <= 4 && _r.wr.slain[_c]);
}

function knight_wr_taken_mult()
{
    if (!knight_active())
        return 1;
    var _r = global.krun;
    if (!variable_struct_exists(_r, "wr") || !is_struct(_r.wr))
        return 1;
    return _r.wr.mult;
}

// the weird-route looks (Susie unhappy, Noelle as the Angel is done by the hero objects themselves)
function knight_wr_look()
{
    with (obj_herosusie)
    {
        if (!variable_instance_exists(id, "knight_ghost"))
        {
            normalsprite = spr_susier_dark_unhappy;
            idlesprite = spr_susieb_idle_serious;
            defendsprite = spr_susieb_defend_unhappy;
            actreadysprite = spr_susieb_actready;
            attacksprite = spr_susieb_attack_serious;
            if (global.charweapon[2] == 0)
                idlesprite = spr_susieb_idle_unarmed_unhappy;
            itemsprite = spr_susieb_item_unhappy;
            itemreadysprite = spr_susieb_itemready_unhappy;
            spellreadysprite = spr_susieb_spellready_unhappy;
            spellsprite = spr_susieb_spell_unhappy;
        }
    }
}

// every battle frame (hub tick)
function knight_wr_tick(_r)
{
    if (!variable_struct_exists(_r, "wr") || !is_struct(_r.wr))
        return 0;
    var _w = _r.wr;
    if (!_w.on)
        return 0;
    if (!_w.look && i_ex(obj_knight_enemy) && instance_exists(obj_herosusie))
    {
        _w.look = true;
        knight_wr_look();
    }
    if (_w.st == 0 || _w.st == 9)
        return 0;
    // keep the battle frozen while the scene runs (nothing else may start a turn)
    global.myfight = 99;
    global.mnfight = 99;
    global.charturn = -1;
    _w.t++;
    var _k = instance_find(obj_knight_enemy, 0);
    if (!i_ex(_k))
    {
        knight_wr_finish(_r);
        return 0;
    }
    var _vh = (_w.vslot >= 0) ? knight_slot_inst(_w.vslot) : noone;
    switch (_w.st)
    {
        case 1:
        case 21:
            // the Knight vanishes and its shadow lunges at the member
            _w.kx = _k.x;
            _w.ky = _k.y;
            _k.visible = 0;
            _w.mk = scr_dark_marker(_k.x, _k.y, knight_wr_marker_sprite());
            _w.mk.image_index = 1;
            _w.mk.depth = _k.depth;
            var _tx = i_ex(_vh) ? (_vh.x - 10) : _k.x;
            var _ty = i_ex(_vh) ? (_vh.y - 10) : _k.y;
            with (_w.mk)
            {
                scr_lerpvar("x", x, _tx, 25, 7, "in");
                scr_lerpvar("y", y, _ty, 25, 7, "in");
            }
            snd_play_x(snd_knight_cut, 1, 1.5);
            if (i_ex(_vh))
            {
                with (_vh)
                    scr_shakeobj();
            }
            if (_w.st == 1)
            {
                if (_w.vic == 4)
                    snd_play(snd_noelle_scared);
                if (_w.vic == 2)
                    snd_play(snd_sussurprise);
                if (_w.vic == 3)
                    snd_play(snd_txtral);
                if (_w.vic == 1)
                    snd_play(snd_hurt1);
            }
            if (variable_global_exists("batmusic") && is_array(global.batmusic))
                mus_volume(global.batmusic[1], 0, 20);
            _w.st = (_w.st == 1) ? 2 : 22;
            _w.t = 0;
            break;
        case 2:
            if (_w.t >= 27)
            {
                var _hx = i_ex(_vh) ? _vh.x : _k.x;
                var _hy = i_ex(_vh) ? _vh.y : _k.y;
                var _dw = instance_create(_hx + 51, _hy + 41, obj_dmgwriter);
                _dw.damage = 9999;
                _dw.type = 12;
                _dw.depth = _w.mk.depth - 1;
                _w.mk.image_index = 3;
                knight_wr_slay(_w);
                if (!i_ex(obj_shake))
                    instance_create(0, 0, obj_shake);
                snd_play(snd_damage);
                _w.st = 3;
                _w.t = 0;
            }
            break;
        case 3:
            if (i_ex(_w.mk) && _w.mk.image_index < 5)
                _w.mk.image_index += 0.25;
            if (_w.t >= 45)
            {
                var _bx = _w.kx;
                var _by = _w.ky;
                with (_w.mk)
                {
                    scr_lerpvar("x", x, _bx, 25, 7, "out");
                    scr_lerpvar("y", y, _by, 25, 7, "out");
                }
                _w.st = 4;
                _w.t = 0;
            }
            break;
        case 4:
            if (_w.t >= 28)
            {
                with (_w.mk)
                    instance_destroy();
                _w.mk = noone;
                _k.visible = 1;
                _w.sp = knight_talk_speakers(_w.vic);
                _w.q = knight_talk_build(_w.vic, false);
                _w.qi = 0;
                _w.st = 5;
                _w.t = 0;
            }
            break;
        case 5:
            // the others talk: Susie first, then the rest in party order
            if (_w.t >= 20 && !w_ex())
            {
                if (_w.qi < array_length(_w.q))
                {
                    var _ln = _w.q[_w.qi];
                    _w.qi++;
                    knight_talk_fx(_ln[0], _ln[3]);
                    knight_say(_ln[0], _ln[1], _ln[2]);
                    _w.t = 15;
                }
                else
                {
                    knight_talk_end(_w.sp);
                    _w.st = 6;
                    _w.t = 0;
                }
            }
            break;
        case 6:
            // what they learn (Susie's RUDER BUSTER, Noelle's courage and ICESTORM, Ralsei's FIRESTORM)
            if (_w.t >= 10 && !w_ex())
            {
                var _lm = knight_learn_after(_w.vic, 0, false);
                if (_lm != "")
                {
                    scr_speaker("noone");
                    knight_msg_pages(_lm);
                    scr_battletext();
                    var _ns = knight_soul_slot(4);
                    if (_ns >= 0 && _w.vic != 4)
                    {
                        var _nh = knight_slot_inst(_ns);
                        if (_nh != noone)
                        {
                            with (_nh)
                                scr_oflash();
                        }
                    }
                }
                _w.st = 7;
                _w.t = 0;
            }
            break;
        case 7:
            if (!w_ex())
                knight_wr_finish(_r);
            break;
        case 22:
            // ...and the last member knocks the blade back
            if (_w.t >= 24)
            {
                knight_dfl_hit(_w.vic, _w.mk, _w.kx, _w.ky);
                if (i_ex(_vh))
                {
                    with (_vh)
                        scr_oflash();
                }
                _w.st = 23;
                _w.t = 0;
            }
            break;
        case 23:
            if (_w.t >= 26)
            {
                var _bx2 = _w.kx;
                var _by2 = _w.ky;
                if (i_ex(_w.mk))
                {
                    with (_w.mk)
                    {
                        scr_lerpvar("x", x, _bx2, 12, 2, "in");
                        scr_lerpvar("y", y, _by2, 12, 2, "in");
                    }
                }
                _w.st = 24;
                _w.t = 0;
            }
            break;
        case 24:
            if (_w.t >= 14)
            {
                if (i_ex(_w.mk))
                {
                    with (_w.mk)
                        instance_destroy();
                }
                _w.mk = noone;
                _k.visible = 1;
                knight_dfl_pose(_w.vic, false);
                scr_speaker("noone");
                msgset(0, knight_dfl_text(_w.vic));
                scr_battletext();
                _w.st = 25;
                _w.t = 0;
            }
            break;
        case 25:
            if (!w_ex())
                knight_wr_dfl_finish(_r);
            break;
    }
    return 1;
}

function knight_has_spell(_c, _sp)
{
    for (var _i = 0; _i < 12; _i++)
    {
        if (global.spell[_c][_i] == _sp)
            return true;
    }
    return false;
}

// the parry is over: nobody was lost, the fight goes on
function knight_wr_dfl_finish(_r)
{
    var _w = _r.wr;
    if (i_ex(_w.mk))
    {
        with (_w.mk)
            instance_destroy();
    }
    _w.mk = noone;
    with (obj_knight_enemy)
        visible = 1;
    _w.dfl = true;
    _w.done = true;
    _w.st = 9;
    if (variable_global_exists("batmusic") && is_array(global.batmusic))
        mus_volume(global.batmusic[1], 1, 45);
    global.battlemsg[0] = "* " + knight_charname(_w.vic) + " stands alone.&* The fight goes on.";
    with (obj_knight_enemy)
        scr_mnendturn();
}

function knight_wr_finish(_r)
{
    var _w = _r.wr;
    if (i_ex(_w.mk))
    {
        with (_w.mk)
            instance_destroy();
    }
    _w.mk = noone;
    with (obj_knight_enemy)
        visible = 1;
    _w.mult = 1.25;
    _w.done = true;
    _w.st = 9;
    var _who = knight_charname(_w.vic);
    if (variable_global_exists("batmusic") && is_array(global.batmusic))
        mus_volume(global.batmusic[1], 1, 45);
    global.battlemsg[0] = stringsetsub("* ~1 was completely obliterated.&* The enemy became stronger.", _who);
    with (obj_knight_enemy)
        scr_mnendturn();
}
