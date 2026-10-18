
// ===== build 38: the Weird Route by party order, the survivors' talk and the moves they learn, the last member's parry,
// HoldBreath for everyone when Kris is not there, and the INFINITE HP option =====

// ---------- party order ----------
// The member on top of the party (slot 1) stays to the end: the Knight never takes them (in the Violet Knight's Side B they
// finish the fight; Kris on top plays the mod's own Kris story). The Knight goes for the bottom member first, then the next up.
function knight_wr_slain(_c)
{
    if (!knight_active() || _c < 1 || _c > knight_wr_maxc())
        return false;
    var _r = global.krun;
    if (!variable_struct_exists(_r, "wr") || !is_struct(_r.wr))
        return false;
    return _r.wr.slain[_c];
}

// still in the fight: in a party slot and not taken by the Knight (knocked down still counts)
// the highest character id the party logic looks at: the game's four and the custom characters (build 50: Flowery, 5)
function knight_wr_maxc()
{
    return min(5, max(4, knight_cc_max_id()));
}

function knight_wr_here(_c)
{
    if (_c < 1 || _c > knight_wr_maxc())
        return false;
    return scr_havechar(_c) && !knight_wr_slain(_c);
}

// the lowest member in the party (bottom slot first) the Knight can take: still here and not the top member
function knight_wr_bottom(_top)
{
    for (var _s = 2; _s >= 0; _s--)
    {
        var _c = global.char[_s];
        if (_c == _top || !knight_wr_here(_c))
            continue;
        return _c;
    }
    return 0;
}

// different members still here (clones of one member count once)
function knight_wr_here_count()
{
    var _n = 0;
    for (var _c = 1; _c <= knight_wr_maxc(); _c++)
    {
        if (knight_wr_here(_c))
            _n++;
    }
    return _n;
}

// the only member left (0 while more than one is here)
function knight_wr_lone()
{
    if (knight_wr_here_count() != 1)
        return 0;
    for (var _c = 1; _c <= knight_wr_maxc(); _c++)
    {
        if (knight_wr_here(_c))
            return _c;
    }
    return 0;
}

// Kris is in the fight (in the party and not taken by the Knight on a Weird Route)
function knight_kris_here()
{
    return scr_havechar(1) && !knight_wr_slain(1);
}

// can the Knight still take _c in this fight (here, and not the top member)
function knight_wr_can_take(_c)
{
    return knight_wr_here(_c) && _c != knight_wr_fin_of_party();
}

// ---------- the survivors' talk after the Knight takes someone ----------
// Susie always speaks first; the others follow in party order once she is done (Kris never speaks). First everyone's shock,
// then what they will do about it: Susie's fury, Ralsei's resolve, Noelle's courage. Susie gets back up to answer if she was down.
function knight_talk_can(_c)
{
    if (!knight_wr_here(_c))
        return false;
    return (_c == 2) || (global.hp[_c] > 0);
}

function knight_talk_speakers(_v)
{
    var _o = [];
    if (_v != 2 && knight_talk_can(2))
        array_push(_o, 2);
    for (var _s = 0; _s < 3; _s++)
    {
        var _c = global.char[_s];
        if (_c != 3 && _c != 4 && !knight_cc_ok(_c))
            continue;
        if (_c == _v || !knight_talk_can(_c))
            continue;
        var _dup = false;
        for (var _j = 0; _j < array_length(_o); _j++)
        {
            if (_o[_j] == _c)
                _dup = true;
        }
        if (!_dup)
            array_push(_o, _c);
    }
    return _o;
}

// round one: the shock (_again: they already lost someone in this fight)
function knight_talk_shock(_c, _v, _again)
{
    if (_c >= 5)
    {
        // build 50: Flowery - the smile goes
        var _fl = [];
        array_push(_fl, "..^2.&" + knight_taunt_name(_v) + "?/%");
        if (_again)
            array_push(_fl, "Hey..^2. hey.^2&Not cool.^2&Not cool at all./%");
        else
            array_push(_fl, "Hey..^2. get up..^2.&That's not funny./%");
        return _fl;
    }
    if (_c == 2)
    {
        var _l = [];
        if (_v == 1)
            array_push(_l, "K^3-Kris...?/%");
        else if (_v == 3)
            array_push(_l, "R^3-Ralsei...?/%");
        else if (_v >= 5)
            array_push(_l, "F^3-Flowery...?/%");
        else
            array_push(_l, "N^3-Noelle...?/%");
        if (_again)
            array_push(_l, "...^2. Not..^2.&not you too.../%");
        return _l;
    }
    if (_c == 3)
    {
        if (_v == 1)
            return ["K^2-Kris...?!&No..^2. not you...!/%"];
        if (_v == 2)
            return ["S^2-Susie...?!&No..^2. no no no.../%"];
        return ["N^2-no..^2. this wasn't&in the prophecy..!/%"];
    }
    if (_v == 1)
        return ["K^2-Kris...?!/%"];
    if (_v == 2)
        return ["S^2-Susie...?/%"];
    if (_v >= 5)
        return ["F^2-Flowery...?!/%", "N-no..^2. get up..^2.&please get up...!/%"];
    return ["R^2-Ralsei...?!/%", "N-no..^2. get up..^2.&please get up...!/%"];
}

// round two: what they will do about it
function knight_talk_resolve(_c, _v, _again)
{
    if (_c >= 5)
    {
        if (_again)
            return ["...^2. That's two.^2&You're done&smiling, pal./%"];
        return ["...Hey.^2&Nobody hurts&my team on&my watch./%"];
    }
    if (_c == 2)
    {
        if (_again)
            return ["YOU..^2.&I'M GONNA..^2.&END YOU!!!/%"];
        if (_v == 1)
            return ["Y^2-You.../%", "I'LL..^2. MAKE..^2.&YOU..^2. PAY!!!/%"];
        if (_v == 3)
            return ["Y^2-You.../%", "I'll..^2. make..^2.&YOU..^2. SUFFER!/%"];
        return ["Y^2-You.../%", "I'LL..^2. TEAR..^2.&YOU..^2. APART!!!/%"];
    }
    if (_c == 3)
    {
        if (_again)
            return ["...^2. Then I'll..^2.&end this myself./%"];
        return ["I..^2. I won't let you&hurt anyone else...!/%"];
    }
    if (_v == 2)
        return ["...^2.&I'll make you&pay for that./%"];
    if (_v == 3)
        return ["...^2.&Then I..^2. I have to&do it myself./%"];
    return ["...^2.&I'm..^2. I'm not scared&of you anymore./%"];
}

// the whole talk: [member, line, text speed, stance change]
function knight_talk_build(_v, _again)
{
    var _sp = knight_talk_speakers(_v);
    var _q = [];
    for (var _i = 0; _i < array_length(_sp); _i++)
    {
        var _c = _sp[_i];
        var _l = knight_talk_shock(_c, _v, _again);
        for (var _j = 0; _j < array_length(_l); _j++)
            array_push(_q, [_c, _l[_j], 3, (_j == 0) ? "shock" : ""]);
    }
    for (var _i = 0; _i < array_length(_sp); _i++)
    {
        var _c = _sp[_i];
        var _l = knight_talk_resolve(_c, _v, _again);
        var _n = array_length(_l);
        for (var _j = 0; _j < _n; _j++)
        {
            var _fx = "";
            if (_j == 0)
                _fx = (_n == 1) ? "resolve_final" : "resolve";
            else if (_j == _n - 1)
                _fx = "final";
            array_push(_q, [_c, _l[_j], (_c == 2) ? 3 : 2, _fx]);
        }
    }
    return _q;
}

// Violet Knight Side B hides Susie behind her fear sprite while the blade comes back (the mod's own marker)
function knight_talk_susmarker()
{
    var _ke = instance_find(obj_knight_enemy, 0);
    if (_ke == noone || !variable_instance_exists(_ke, "_susshock"))
        return noone;
    var _m = _ke._susshock;
    if (!i_ex(_m) || !_m.visible)
        return noone;
    return _m;
}

function knight_talk_saved()
{
    if (!variable_global_exists("knight_tk_save") || !is_array(global.knight_tk_save))
        global.knight_tk_save = [-1, -1, -1, -1, -1, -1];
    return global.knight_tk_save;
}

// a member's normal stance for the rest of the fight
function knight_talk_idle(_c)
{
    if (_c == 2)
        return (global.charweapon[2] == 0) ? spr_susieb_idle_unarmed_unhappy : spr_susieb_idle_serious;
    if (_c == 3)
        return spr_ralsei_idle;
    if (_c == 4 || knight_cc_ok(_c))
        return knight_vb_idle_sprite(_c);
    return spr_krisb_idle;
}

// stance changes on a talk line: shock (hurt pose, face), resolve (stands back up / Noelle readies a spell), Susie's fury
function knight_talk_fx(_c, _fx)
{
    if (_fx == "")
        return 0;
    knight_talk_saved();
    var _h = knight_hero_inst(_c);
    var _s = knight_slot_of(_c);
    if (_c == 2)
    {
        var _mk = knight_talk_susmarker();
        if (_fx == "shock")
        {
            if (global.hp[2] <= 0 && _s >= 0)
            {
                // she was down: she gets back up to answer
                global.hp[2] = 1;
                scr_revive(_s);
                snd_play(snd_wing);
                snd_play(snd_power);
                if (_h != noone)
                {
                    var _ha = instance_create(_h.x, _h.y, obj_healanim);
                    _ha.target = _h;
                }
            }
            if (_mk == noone && _h != noone)
            {
                with (_h)
                    scr_shakeobj();
                snd_play(snd_sussurprise);
            }
            return 1;
        }
        if (_fx == "resolve" || _fx == "resolve_final")
        {
            if (_mk != noone)
            {
                _mk.sprite_index = spr_susie_anger_yell;
                if (_h != noone)
                {
                    _mk.x = _h.x + 8;
                    _mk.y = _h.y - 10;
                }
                with (_mk)
                    scr_minishakeobj();
            }
        }
        if (_fx == "final" || _fx == "resolve_final")
        {
            if (_mk != noone)
                _mk.visible = 0;
            if (_h != noone)
            {
                with (_h)
                {
                    visible = 1;
                    idlesprite = spr_susieb_attackready_unhappy;
                    scr_shakeobj();
                }
            }
            snd_play(snd_noise);
        }
        return 1;
    }
    if (_fx == "shock")
    {
        if (_h != noone && global.knight_tk_save[_c] == -1)
            global.knight_tk_save[_c] = _h.idlesprite;
        if (_c == 3)
        {
            if (_h != noone)
            {
                with (_h)
                {
                    idlesprite = spr_ralsei_hurt_fixed;
                    scr_shakeobj();
                }
            }
            snd_play(snd_txtral);
        }
        if (_c == 4 || _c >= 5)
        {
            if (_h != noone)
            {
                with (_h)
                {
                    idlesprite = variable_instance_exists(id, "hurtsprite") ? hurtsprite : spr_noelleb_hurt;
                    scr_shakeobj();
                }
            }
            if (_c == 4)
                snd_play(snd_noelle_scared);
        }
        if (_s >= 0)
            global.faceaction[_s] = 5;
        return 1;
    }
    if (_fx == "resolve" || _fx == "resolve_final")
    {
        if (_c == 3)
        {
            knight_talk_calm(3);
            if (_h != noone)
            {
                with (_h)
                    scr_minishakeobj();
            }
        }
        if (_c == 4 || _c >= 5)
        {
            if (_h != noone)
            {
                with (_h)
                {
                    idlesprite = variable_instance_exists(id, "spellreadysprite") ? spellreadysprite : spr_noelleb_spellready;
                    scr_shakeobj();
                }
            }
            if (_s >= 0 && global.faceaction[_s] == 5)
                global.faceaction[_s] = 0;
        }
    }
    return 1;
}

// back to their own stance (the one they had before the shock) and their normal face
function knight_talk_calm(_c)
{
    knight_talk_saved();
    var _h = knight_hero_inst(_c);
    var _was = global.knight_tk_save[_c];
    global.knight_tk_save[_c] = -1;
    if (_h != noone)
    {
        if (_was != -1 && _was != spr_ralsei_hurt_fixed && _was != spr_noelleb_hurt && !(knight_cc_ok(_c) && _was == knight_cc(_c).poses.hurt))
            _h.idlesprite = _was;
        else
            _h.idlesprite = knight_talk_idle(_c);
    }
    var _s = knight_slot_of(_c);
    if (_s >= 0 && global.faceaction[_s] == 5)
        global.faceaction[_s] = 0;
    return 1;
}

// after the talk: everyone who spoke stands normally again (Susie keeps her serious stance)
function knight_talk_end(_sp)
{
    for (var _i = 0; _i < array_length(_sp); _i++)
    {
        var _c = _sp[_i];
        if (_c == 2)
        {
            var _mk = knight_talk_susmarker();
            if (_mk != noone)
                _mk.visible = 0;
            var _h = knight_hero_inst(2);
            if (_h != noone)
            {
                _h.visible = 1;
                _h.idlesprite = knight_talk_idle(2);
            }
        }
        else
            knight_talk_calm(_c);
    }
    return 1;
}

// ---------- the knight's ACT lists (run in the knight's scope: myself = its monster slot) ----------
function knight_act_can(_c, _i)
{
    if (_i < 0 || _i > 5)
        return 0;
    if (_c == 2)
        return global.canactsus[myself][_i];
    if (_c == 3)
        return global.canactral[myself][_i];
    if (_c == 4)
        return global.canactnoe[myself][_i];
    return global.canact[myself][_i];
}

function knight_act_name(_c, _i)
{
    if (_i < 0 || _i > 5)
        return "";
    if (_c == 2)
        return global.actnamesus[myself][_i];
    if (_c == 3)
        return global.actnameral[myself][_i];
    if (_c == 4)
        return global.actnamenoe[myself][_i];
    return global.actname[myself][_i];
}

function knight_act_first_free(_c)
{
    for (var _i = 0; _i < 6; _i++)
    {
        if (knight_act_can(_c, _i) != 1)
            return _i;
    }
    return -1;
}

function knight_act_find(_c, _name)
{
    for (var _i = 0; _i < 6; _i++)
    {
        if (knight_act_can(_c, _i) == 1 && knight_act_name(_c, _i) == _name)
            return _i;
    }
    return -1;
}

function knight_act_put(_c, _i, _name, _desc, _cost)
{
    if (_i < 0 || _i > 5)
        return 0;
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
    return 1;
}

function knight_act_clear(_c, _i)
{
    if (_i < 0 || _i > 5)
        return 0;
    if (_c == 2)
    {
        global.canactsus[myself][_i] = 0;
        global.actnamesus[myself][_i] = "";
        global.actcostsus[myself][_i] = 0;
    }
    if (_c == 3)
    {
        global.canactral[myself][_i] = 0;
        global.actnameral[myself][_i] = "";
        global.actcostral[myself][_i] = 0;
    }
    if (_c == 4)
    {
        global.canactnoe[myself][_i] = 0;
        global.actnamenoe[myself][_i] = "";
        global.actcostnoe[myself][_i] = 0;
    }
    return 1;
}

// ---------- HoldBreath for everyone when Kris is not there ----------
// Only Kris had HoldBreath (the SOUL moves faster). Without Kris each other member gets it in their own S / R / N-Action list
// (the first free row, after their own ACT), like the Kaizo Knight mod does. The Violet Knight keeps its HoldBreath / DeepBreath toggle.
// Battle start (the end of the knight's own setup); also clears what was learned in the last fight.
function knight_hb_setup(_key)
{
    hb_key = _key;
    hb_turn = -2;
    knight_learn_init(true);
    knight_dbl_clear();
    if (scr_havechar(1))
        return 0;
    return knight_hb_give();
}

// give HoldBreath to every other member who does not have it yet (also when the Knight has taken Kris)
function knight_hb_give()
{
    var _nm = "HoldBreath";
    if (variable_instance_exists(id, "hb_key") && hb_key == "violet" && variable_instance_exists(id, "holdbreathcount") && holdbreathcount > 0)
        _nm = "DeepBreath";
    var _n = 0;
    for (var _c = 2; _c <= 4; _c++)
    {
        if (!scr_havechar(_c))
            continue;
        if (knight_act_find(_c, "HoldBreath") >= 0 || knight_act_find(_c, "DeepBreath") >= 0)
            continue;
        var _i = knight_act_first_free(_c);
        if (_i < 0)
            continue;
        knight_act_put(_c, _i, _nm, "", 0);
        _n++;
    }
    if (_n > 0)
        knight_actcount_fix();
    return _n;
}

// Susie's (and the Cyan Knight's Ralsei's) talk ACT removes itself after use: in the fights where nothing else ever reuses that
// row, HoldBreath moves up into it so the magic menu has no empty first cell. Only while the bullets fly (nobody is choosing).
function knight_hb_compact()
{
    if (!variable_instance_exists(id, "hb_key") || (hb_key != "base" && hb_key != "thorn" && hb_key != "cyan"))
        return 0;
    if (!variable_global_exists("mnfight") || global.mnfight != 2)
        return 0;
    var _moved = false;
    for (var _c = 2; _c <= 4; _c++)
    {
        var _i = knight_act_find(_c, "HoldBreath");
        if (_i <= 0)
            continue;
        var _j = knight_act_first_free(_c);
        if (_j < 0 || _j >= _i)
            continue;
        knight_act_clear(_c, _i);
        knight_act_put(_c, _j, "HoldBreath", "", 0);
        _moved = true;
    }
    if (_moved)
    {
        knight_actcount_fix();
        scr_spellmenu_setup();
    }
    return _moved;
}

function knight_hb_rename(_name)
{
    for (var _c = 2; _c <= 4; _c++)
    {
        var _i = knight_act_find(_c, "HoldBreath");
        if (_i < 0)
            _i = knight_act_find(_c, "DeepBreath");
        if (_i >= 0)
        {
            if (_c == 2)
                global.actnamesus[myself][_i] = _name;
            if (_c == 3)
                global.actnameral[myself][_i] = _name;
            if (_c == 4)
                global.actnamenoe[myself][_i] = _name;
        }
    }
    knight_actcount_fix();
    scr_spellmenu_setup();
}

function knight_hb_do(_c, _nm)
{
    var _who = knight_charname(_c);
    var _how = " held her breath in panic..^1.";
    if (_c == 2)
        _how = " kept her breath held in focus..^1.";
    if (_c == 3)
        _how = " held his breath to stay calm..^1.";
    var _tog = (variable_instance_exists(id, "hb_key") && hb_key == "violet");
    var _turn = knight_active() ? global.krun.eturns : -1;
    var _t = "";
    if (_tog && _turn >= 0 && variable_instance_exists(id, "hb_turn") && hb_turn == _turn)
    {
        // somebody already changed the SOUL's speed this turn
        _t = "* " + _who + _how + "&* Nothing else happened./%";
    }
    else if (_tog && _nm == "DeepBreath")
    {
        hb_turn = _turn;
        holdbreathcount = 0;
        knight_hb_rename("HoldBreath");
        _t = "* " + _who + " took a deep breath...&* The SOUL now moves slower./%";
    }
    else if (holdbreathcount <= 0)
    {
        hb_turn = _turn;
        holdbreathcount = 1;
        if (_tog)
            knight_hb_rename("DeepBreath");
        _t = "* " + _who + _how + "&* The SOUL now moves faster./%";
    }
    else
        _t = "* " + _who + _how + "&* But nothing seemed to happen./%";
    scr_speaker("noone");
    msgset(0, _t);
    scr_battletext_default();
    actcon = 1;
    return 1;
}

// ---------- the moves the survivors learn ----------
// Susie: RUDER BUSTER (two Rude Busters, X-Slash's timing) when the Knight takes Ralsei, or after the first loss she sees when it
// cannot take Ralsei in this fight. Noelle finds her courage: ICESTORM (two Ice Shocks; SnowGrave too). Ralsei: FIRESTORM (two
// FireShocks). Learned once per fight, on the knight's ACT list (60% TP for Ruder Buster, 30% for the storms).
function knight_learn_init(_force)
{
    if (_force || !variable_global_exists("knight_lrn") || !is_array(global.knight_lrn))
    {
        global.knight_lrn = [false, false, false, false, false, false];
        global.knight_fl_lrn = false;
    }
}

function knight_learned(_c)
{
    knight_learn_init(false);
    return (_c >= 1 && _c <= 4 && global.knight_lrn[_c]);
}

function knight_learn_act(_c, _name, _desc, _cost)
{
    var _k = instance_find(obj_knight_enemy, 0);
    if (_k == noone)
        return -1;
    var _i = -1;
    with (_k)
    {
        _i = knight_act_find(_c, _name);
        if (_i < 0)
            _i = knight_act_first_free(_c);
        if (_i >= 0)
            knight_act_put(_c, _i, _name, _desc, _cost);
        knight_actcount_fix();
        scr_spellmenu_setup();
    }
    return _i;
}

// what the survivors learn after _v was taken: returns the battle text ("" = nothing). _quiet: a member whose message a later
// scene gives instead (the Violet finisher's power-up). _more: the Knight may still take someone later in this fight (Susie
// waits for Ralsei only while he can still be taken)
function knight_learn_after(_v, _quiet, _more)
{
    knight_learn_init(false);
    var _pages = [];
    if (_v != 2 && knight_wr_here(2) && !global.knight_lrn[2] && (_v == 3 || !(_more && knight_wr_can_take(3))))
    {
        global.knight_lrn[2] = true;
        knight_learn_act(2, "RuderBuster", "Rude x2#Damage", 150);
        if (_quiet != 2)
            array_push(_pages, "* (" + knight_charname(2) + " learned \\cYRUDER BUSTER\\cW!)");
    }
    for (var _s = 0; _s < 3; _s++)
    {
        var _c = global.char[_s];
        if (_c != 3 && _c != 4 && _c != 5)
            continue;
        if (_c == 5)
        {
            // build 50: Flowery (his own character) learns nothing of theirs - he stops smiling, once
            if (!global.knight_fl_lrn && _v != 5)
            {
                global.knight_fl_lrn = true;
                array_push(_pages, "* (" + knight_charname(5) + " stopped smiling.)");
            }
            continue;
        }
        if (_c == _v || !knight_wr_here(_c) || global.knight_lrn[_c])
            continue;
        global.knight_lrn[_c] = true;
        var _nm = knight_charname(_c);
        if (_c == 4)
        {
            knight_learn_act(4, "IceStorm", "Ice x2#Damage", 75);
            // one line per page: with a long name ("The Angel") two of them already fill the box
            var _p = "* (" + _nm + " found her courage!)/* (" + _nm + " learned \\cYICESTORM\\cW!)";
            if (!knight_has_spell(4, 10))
            {
                scr_spellget(4, 10);
                scr_spellmenu_setup();
                _p += "/* (" + _nm + " can now use \\cYSNOWGRAVE\\cW.)";
            }
            with (obj_knight_enemy)
                noe_learned = 1;
            if (_quiet != 4)
                array_push(_pages, _p);
        }
        else
        {
            knight_learn_act(3, "FireStorm", "Fire x2#Damage", 75);
            if (_quiet != 3)
                array_push(_pages, "* (" + _nm + " learned \\cYFIRESTORM\\cW!)");
        }
    }
    if (array_length(_pages) > 0)
        snd_play(snd_power);
    var _t = "";
    for (var _i = 0; _i < array_length(_pages); _i++)
        _t += _pages[_i] + ((_i == (array_length(_pages) - 1)) ? "/%" : "/");
    return _t;
}

// battle text with several pages ("page/page/%"): every page gets its own box. A "/" inside ONE message only waits for a key and
// then carries on in the same box, so the learned-moves text (build 38-40) ran on and out of the bottom of the box.
function knight_msg_pages(_t)
{
    var _pages = [];
    var _cur = "";
    var _n = string_length(_t);
    for (var _i = 1; _i <= _n; _i++)
    {
        var _ch = string_char_at(_t, _i);
        if (_ch == "/")
        {
            array_push(_pages, _cur);
            _cur = "";
            if (_i < _n && string_char_at(_t, _i + 1) == "%")
                break;
            continue;
        }
        _cur += _ch;
    }
    if (_cur != "" && _cur != "%")
        array_push(_pages, _cur);
    var _k = array_length(_pages);
    for (var _i = 0; _i < _k; _i++)
    {
        var _s = _pages[_i] + ((_i == (_k - 1)) ? "/%" : "/");
        if (_i == 0)
            msgset(0, _s);
        else
            msgnext(_s);
    }
    return _k;
}

// the slot a member acts from right now (a clone in another slot does not steal it)
function knight_act_slot(_c)
{
    var _cc = variable_global_exists("currentactingchar") ? global.currentactingchar : -1;
    if (_cc >= 0 && _cc < 3 && global.char[_cc] == _c && global.hp[_c] > 0)
        return _cc;
    return knight_soul_slot(_c);
}

// a learned move: the member casts their own spell in the spell phase, twice (the spell phase's cast reads the flag)
function knight_storm_do(_c, _nm)
{
    var _s = knight_act_slot(_c);
    var _sp = 9;
    if (_c == 2)
        _sp = 4;
    if (_c == 3)
        _sp = 13;
    if (_s >= 0)
    {
        global.faceaction[_s] = 2;
        global.charaction[_s] = 2;
        global.charspecial[_s] = _sp;
        global.chartarget[_s] = 0;
        global.acting[_s] = 0;
        knight_dbl_set(_s, _sp);
    }
    var _who = knight_charname(_c);
    scr_speaker("noone");
    if (_c == 2)
        msgset(0, "* " + _who + "'s fury boiled over!/%");
    else if (_c == 3)
        msgset(0, "* " + _who + "'s resolve burned bright!/%");
    else
        msgset(0, "* " + _who + " steadied her breath!/%");
    scr_battletext_default();
    snd_play(snd_boost);
    var _h = knight_hero_inst(_c);
    if (_h != noone)
    {
        with (_h)
            scr_oflash();
    }
    actcon = 1;
    return 1;
}

// the S / R / N-Actions the hub adds (HoldBreath without Kris, the learned moves). Runs first in the ACT phase and uses the
// action up, so the fight's own ACT code never sees it.
function knight_member_acts()
{
    if (!variable_instance_exists(id, "actingsus"))
        return false;
    var _did = false;
    for (var _c = 2; _c <= 4; _c++)
    {
        var _a = 0;
        var _f = 0;
        if (_c == 2)
        {
            _a = actingsus;
            _f = actconsus;
        }
        if (_c == 3)
        {
            _a = actingral;
            _f = actconral;
        }
        if (_c == 4)
        {
            _a = variable_instance_exists(id, "actingnoe") ? actingnoe : 0;
            _f = variable_instance_exists(id, "actconnoe") ? actconnoe : 0;
        }
        if (_f != 1 || _a < 1 || _a > 6)
            continue;
        var _nm = knight_act_name(_c, _a - 1);
        if (!is_string(_nm))
            continue;
        var _hb = (_nm == "HoldBreath" || _nm == "DeepBreath");
        var _st = (_nm == "RuderBuster" || _nm == "IceStorm" || _nm == "FireStorm");
        if (!_hb && !_st)
            continue;
        if (_c == 2)
            actconsus = 0;
        if (_c == 3)
            actconral = 0;
        if (_c == 4)
            actconnoe = 0;
        if (_hb)
            knight_hb_do(_c, _nm);
        else
            knight_storm_do(_c, _nm);
        _did = true;
    }
    return _did;
}

// ---------- the double casts (X-Slash's timing: the second one 15 frames after the first) ----------
function knight_dbl_clear()
{
    global.knight_dbl = [0, 0, 0];
}

function knight_dbl_set(_s, _sp)
{
    if (!variable_global_exists("knight_dbl") || !is_array(global.knight_dbl))
        knight_dbl_clear();
    if (_s >= 0 && _s < 3)
        global.knight_dbl[_s] = _sp;
}

// the spell phase casts spell _sp for party slot _s: true (once) when it is the learned double version
function knight_dbl_take(_s, _sp)
{
    if (!variable_global_exists("knight_dbl") || !is_array(global.knight_dbl) || _s < 0 || _s > 2)
        return false;
    if (global.knight_dbl[_s] != _sp)
        return false;
    global.knight_dbl[_s] = 0;
    return true;
}

// the spell phase's line names the learned move
function knight_dbl_text(_s)
{
    if (!variable_global_exists("knight_dbl") || !is_array(global.knight_dbl) || _s < 0 || _s > 2)
        return 0;
    var _sp = global.knight_dbl[_s];
    if (_sp == 0 || global.charspecial[_s] != _sp)
        return 0;
    var _who = knight_charname(global.char[_s]);
    if (_sp == 4)
        global.msg[0] = "* " + _who + " used RUDER BUSTER!/%";
    if (_sp == 9)
        global.msg[0] = "* " + _who + " cast ICESTORM!/%";
    if (_sp == 13)
        global.msg[0] = "* " + _who + " cast FIRESTORM!/%";
    return 1;
}

// ---------- the last member's parry ----------
// When the Knight comes for someone and only one member is left, it charges them and they knock the blade back: nobody dies.
function knight_dfl_name(_c)
{
    if (_c == 2)
        return "susie";
    if (_c == 3)
        return "ralsei";
    if (_c == 4)
        return "noelle";
    return "kris";
}

function knight_dfl_pose(_c, _on)
{
    // the game's act-sprite helper keeps its markers on the caller (the knight, or the hub's controller)
    if (!variable_instance_exists(id, "_charactsprite"))
    {
        for (var _ci = 0; _ci < 10; _ci++)
            _charactsprite[_ci] = noone;
    }
    if (!_on)
    {
        scr_act_charsprite_end();
        knight_cc_pose_marker_end();
        return 0;
    }
    var _h = knight_hero_inst(_c);
    if (_h == noone)
        return 0;
    if (knight_cc_ok(_c))
        return knight_cc_pose_marker(_h, _h.attacksprite, 0.5);
    var _spr = variable_instance_exists(_h, "attacksprite") ? _h.attacksprite : spr_krisb_attack;
    var _a = scr_act_charsprite(knight_dfl_name(_c), _spr, 0.5, 2);
    if (i_ex(_a))
        _a.depth = _h.depth - 1;
    return 1;
}

// the parry itself: the blade bounces off (the shadow flies back past the Knight), flash, shake
function knight_dfl_hit(_c, _mk, _bx, _by)
{
    var _h = knight_hero_inst(_c);
    if (_h != noone)
    {
        with (_h)
            scr_shakeobj();
    }
    knight_dfl_pose(_c, true);
    snd_play(snd_impact);
    snd_play_x(snd_knight_cut, 0.8, 0.6);
    snd_play_x(snd_bell, 0.7, 1.4);
    if (!i_ex(obj_shake))
        instance_create(0, 0, obj_shake);
    if (i_ex(_mk))
    {
        _mk.image_index = 3;
        with (_mk)
        {
            scr_lerpvar("x", x, _bx + 70, 14, 2, "out");
            scr_lerpvar("y", y, _by - 24, 14, 2, "out");
        }
    }
    return 1;
}

function knight_dfl_text(_c)
{
    return "* " + knight_charname(_c) + " knocked the Knight's blade back!/%";
}

// ---------- INFINITE HP (CONFIG page) ----------
// Party HP never goes down in a hub fight: every hit still lands (damage numbers, the hurt flash, No-Hit) but takes nothing,
// drains (ThornRing, Kaizo's GLOOM) take nothing and the Thorn Knight wears no max HP down. The story still takes members
// (Weird Route, Violet Side B). Runs with it are not recorded.
function knight_infhp()
{
    if (!knight_active())
        return false;
    var _r = global.krun;
    return (_r.state == "battle" && knight_cfg_flag(_r.cfg, "infhp"));
}

// HP a hit or a drain takes: none with INFINITE HP
// DRBR 1.0.3: online, none for a hit the room's rules took nothing from (kbr_dmg_taken answered 0 - you are OUT and watching,
// a SHIELD took it, HOW TO PLAY, the last 1 HP of an OUT): Chapter 3's damage scripts make every hit at least 1 after that
// answer, so an OUT player's hidden SOUL lost its last HP to a later hit and the party-down check took them out of the match
function knight_infhp_cut(_d)
{
    if (knight_infhp())
        return 0;
    if (kbr_nohurt_take())
        return 0;
    return _d;
}

// every battle frame: anything else that took HP (or GLOOM) is put back for members who are still up
function knight_infhp_tick(_r)
{
    if (!knight_infhp())
        return 0;
    for (var _s = 0; _s < 3; _s++)
    {
        var _c = global.char[_s];
        if (_c < 1 || _c > 4 || knight_wr_slain(_c))
            continue;
        if (global.hp[_c] > 0 && global.hp[_c] < global.maxhp[_c])
            global.hp[_c] = global.maxhp[_c];
    }
    with (obj_knight_enemy)
    {
        if (variable_instance_exists(id, "k_gloom") && is_array(k_gloom))
        {
            for (var _g = 0; _g < array_length(k_gloom); _g++)
                k_gloom[_g] = 0;
        }
    }
    return 1;
}
