
// ===== build 39: when Susie is not in the fight, Ralsei or Noelle speak where she would =====
// In the knights' talk phase Susie taunts the Knight (turns 6-14 of the fight, the game's own lines). Without her nobody spoke.
// Now the first of Ralsei / Noelle in party order who is still standing says the same beats in their own words (Kris never
// speaks), Noelle as the Angel on a Weird Route save. Susie's own lines name the friends who are really there (the Normal,
// Supercharged and Thorn Knights used to name Kris and Ralsei whoever was in the party). The narration before the Roaring
// ("* Susie grew pale.") names whoever is there.

// ---------- who speaks ----------
// the member who says the talk-phase lines this turn: Susie when she is here (and up); else the first of Ralsei / Noelle in
// party order who is here and up; 0 = nobody. In the Violet Knight's Side B the survivors' own talk takes over after a loss.
function knight_taunt_who()
{
    if (knight_wr_here(2))
        return (global.hp[2] > 0) ? 2 : 0;
    if (i_ex(obj_knight_enemy))
    {
        var _ke = instance_find(obj_knight_enemy, 0);
        if (variable_instance_exists(_ke, "vb_losses") && _ke.vb_losses > 0)
            return 0;
    }
    for (var _s = 0; _s < 3; _s++)
    {
        var _c = global.char[_s];
        if ((_c == 3 || _c == 4) && knight_wr_here(_c) && global.hp[_c] > 0)
            return _c;
    }
    return 0;
}

// start of the knight's talk phase (knight scope): _ok = the fight's own conditions (not practice, ...). Keeps the speaker for
// the whole turn (both balloons of a line).
function knight_taunt_begin(_ok)
{
    taunt_c = (_ok && !knight_taunt_practice()) ? knight_taunt_who() : 0;
    return (taunt_c > 0);
}

// no talk-phase lines in practice (the fight's own flag, or the hub's)
function knight_taunt_practice()
{
    return knight_active() && variable_struct_exists(global.krun, "practice") && global.krun.practice;
}

// Kaizo Knight: Susie talks under the mod's own condition (_sus: up, or frozen); without her the stand-in
function knight_taunt_begin_kz(_ok, _sus)
{
    taunt_c = 0;
    if (_ok && !knight_taunt_practice())
    {
        if (scr_havechar(2))
            taunt_c = _sus ? 2 : 0;
        else
            taunt_c = knight_taunt_who();
    }
    return (taunt_c > 0);
}

function knight_taunt_c()
{
    if (variable_instance_exists(id, "taunt_c") && taunt_c > 0)
        return taunt_c;
    return 2;
}

// the friends the speaker can name: members still here, other than the speaker, in party order (clones once)
function knight_taunt_friends(_sp)
{
    var _f = [];
    for (var _s = 0; _s < 3; _s++)
    {
        var _c = global.char[_s];
        if (_c < 1 || (_c > 4 && !knight_cc_ok(_c)) || _c == _sp || !knight_wr_here(_c))
            continue;
        var _dup = false;
        for (var _j = 0; _j < array_length(_f); _j++)
        {
            if (_f[_j] == _c)
                _dup = true;
        }
        if (!_dup)
            array_push(_f, _c);
    }
    return _f;
}

// every friend of the speaker is down (and there is at least one)
function knight_taunt_down()
{
    var _f = knight_taunt_friends(knight_taunt_c());
    if (array_length(_f) == 0)
        return false;
    for (var _i = 0; _i < array_length(_f); _i++)
    {
        if (global.hp[_f[_i]] > 0)
            return false;
    }
    return true;
}

function knight_taunt_name(_c)
{
    switch (_c)
    {
        case 1: return "Kris";
        case 2: return "Susie";
        case 3: return "Ralsei";
        case 4: return "Noelle";
    }
    if (_c >= 5 && knight_cc_ok(_c))
        return knight_char_proper(_c);
    return "";
}

// build 50: the Violet Knight's title for a member (The Cage, The Girl, The Prince, The Angel - and Flowery, The Flower Man);
// anywhere else, the member's own name
function knight_vtitle(_c)
{
    if (_c >= 5 && knight_cc_ok(_c) && variable_global_exists("knight_variant") && global.knight_variant == 3)
        return "The Flower Man";
    return knight_charname(_c);
}

// him / her / them for the friends who are down
function knight_taunt_pron(_f)
{
    if (array_length(_f) != 1)
        return "them";
    if (_f[0] == 3)
        return "him";
    if (_f[0] == 4)
        return "her";
    if (_f[0] == 5)
        return "him";
    return "them";
}

// ---------- the lines ----------
// _beat: which of Susie's lines this is (6a, 6b, ... 14c; c... in the Cyan Knight); _orig: her line as the fight has it.
// Susie keeps her own line (named friends fixed to the real party); Ralsei and Noelle say theirs.
function knight_taunt_line(_beat, _orig)
{
    var _c = knight_taunt_c();
    if (_c == 2)
        return knight_susie_line(_orig);
    return knight_taunt_stand(_c, _beat, _orig);
}

// the Kaizo Knight already fits Susie's lines to the party itself
function knight_taunt_line_kz(_beat, _orig)
{
    var _c = knight_taunt_c();
    if (_c == 2)
        return _orig;
    return knight_taunt_stand(_c, _beat, _orig);
}

function knight_taunt_stand(_c, _beat, _orig)
{
    var _f = knight_taunt_friends(_c);
    var _n = array_length(_f);
    var _a = (_n > 0) ? knight_taunt_name(_f[0]) : "";
    var _b = (_n > 1) ? knight_taunt_name(_f[1]) : "";
    var _dn = knight_taunt_down();
    var _p = knight_taunt_pron(_f);
    if (string_char_at(_beat, 1) == "c")
        return knight_taunt_cyan(_c, _beat, _orig, _n);
    if (_c == 3)
        return knight_taunt_ralsei(_beat, _n, _a, _b, _dn, _p);
    if (global.flag[456] > 0)
        return knight_taunt_angel(_beat, _n, _a, _b, _dn, _p, _f);
    return knight_taunt_noelle(_beat, _n, _a, _b, _dn, _p, _f);
}

// Ralsei: gentle even here. Where Susie taunts, he hopes, encourages his friends and pleads (his own lines in this fight:
// "Please... please, don't do this...", "We're not giving up! Kris, come on!"); where she gets angry, he apologizes and
// still means to stop the Knight. He never threatens or demands.
function knight_taunt_ralsei(_beat, _n, _a, _b, _dn, _p)
{
    switch (_beat)
    {
        case "6a": return "Haha.../%";
        case "6b": return (_n > 0) ? ("We're... still&standing! " + _a + ",&we're still standing!/%") : "I'm... still&standing...!&Haha... I did it!/%";
        case "7a": return "I don't think&you understand.../%";
        case "7b": return (_n > 0) ? "We're not going to&give up. Not when&we're together!/%" : "I'm not going to&give up. My friends&are counting on me!/%";
        case "8a": return "You're... all alone,&aren't you...?/%";
        case "8b":
            if (_n == 0)
                return "...I'm alone too.&But I know my&friends believe in me./%";
            if (_n == 1)
                return "...I'm not.&I have " + _a + "&right here./%";
            return "...I'm not.&I have " + _a + "&and " + _b + " here./%";
        case "9a":
            if (_n == 0)
                return "Even if you&hurt me.../%";
            if (_dn)
                return "Even if you&knock " + _p + " down.../%";
            return "Even if you&knock me down.../%";
        case "9b":
            if (_n == 0)
                return "I'll get back up.&...I promise!/%";
            if (_dn)
                return "I'll heal " + _p + ".&As many times&as it takes!/%";
            if (_n == 1)
                return "As long as " + _a + "&is here.../%";
            return "As long as " + _a + "&and " + _b + " are here.../%";
        case "10a":
            if (_n == 0)
                return "As long as I can&still stand.../%";
            if (_dn)
                return "As long as I'm&here to lift " + _p + "&back up.../%";
            if (_n == 1)
                return "As long as I have&magic left to&heal " + _a + ".../%";
            return "As long as I have&magic left to heal&my friends.../%";
        case "10b": return (_n > 0) ? "...we won't lose.&We won't!/%" : "...I won't lose.&I won't!/%";
        case "11": return "So... please...&stop this.../%";
        case "12": return "You can't win...&so please...&please, just stop!/%";
        case "13a": return "... You won't&even.../%";
        case "13b": return (_n > 0) ? "...tell us why&you're doing this...?/%" : "...tell me why&you're doing this...?/%";
        case "14a": return "...I see.../%";
        case "14b": return "Then... I won't&ask anymore./%";
        case "14c": return (_n > 0) ? "I'm sorry...&But we have to&stop you./%" : "I'm sorry...&But I have to&stop you./%";
    }
    return ".../%";
}

// Noelle: Susie's own steps, in Noelle's voice - stammering where Susie smirks, braver every turn, and the outburst at the
// end is her own ("Leave Susie ALONE!!" in Chapter 2)
function knight_taunt_noelle(_beat, _n, _a, _b, _dn, _p, _f)
{
    switch (_beat)
    {
        case "6a": return "Faha.../%";
        case "6b": return (_n > 0) ? "D-didn't think&we'd still be&standing, did you?/%" : "D-didn't think&I'd still be&standing, did you?/%";
        case "7a": return "Th-thing is,&you actually.../%";
        case "7b": return (_n > 0) ? "You actually messed&up, picking a fight&with... with US!/%" : "You actually messed&up, picking a fight&with... with ME!/%";
        case "8a": return "You? You're all&alone... aren't you?/%";
        case "8b":
            if (_n == 0)
                return "Me? I've got&friends... who'd&back me up!/%";
            if (_n == 1)
                return "Me? I've got...&" + _a + " right&behind me./%";
            return "Me? I've got...&" + _a + " and " + _b + "&behind me./%";
        case "9a":
            if (_n == 0)
                return "You... you can hit&me all you want.../%";
            if (_dn)
                return "Even... even if&you knock " + _p + " down.../%";
            return "Even... even if&you knock me down.../%";
        case "9b":
            if (_n == 0)
                return "...I'll just get&back up!/%";
            if (_dn)
                return "As long as&I'm here.../%";
            if (_n == 1)
                return "As long as " + _a + "&is here.../%";
            return "As long as " + _a + "&and " + _b + " are here.../%";
        case "10a":
            if (_n == 0)
                return "As long as I can&still stand.../%";
            if (_dn)
                return "As long as I'm here&to lift " + _p + "&back up.../%";
            if (_n == 1)
                return "As long as " + _a + "&has a hand to lift&me up with.../%";
            return "As long as my friends&have a hand to lift&me up with.../%";
        case "10b": return "Y-you're never gonna&win! You hear me?!/%";
        case "11": return "So... g-give up./%";
        case "12": return "You know you can't&win... so... give up!&...P-please?/%";
        case "13a": return "... You won't&even.../%";
        case "13b": return "...say anything?&...Gosh./%";
        case "14a": return "...Faha...&fahahaha.../%";
        case "14b": return "Gosh... I'm done&talking./%";
        case "14c": return (_n > 0) ? "People like you...&LEAVE MY FRIENDS&ALONE!!/%" : "People like you...&just... LEAVE US&ALONE!!/%";
    }
    return ".../%";
}

// Noelle on a Weird Route save (the Angel): Susie's steps again, but melodramatic - shaking laughter, power she is afraid of,
// Kris always behind her, and her own Snowgrave words ("Getting... stronger.", "it's... cold...")
function knight_taunt_angel(_beat, _n, _a, _b, _dn, _p, _f)
{
    var _kris = false;
    for (var _i = 0; _i < array_length(_f); _i++)
    {
        if (_f[_i] == 1)
            _kris = true;
    }
    switch (_beat)
    {
        case "6a": return "Haha... haha.../%";
        case "6b": return (_n > 0) ? "Didn't... think we'd&still be standing...?&...Me neither./%" : "Didn't... think I'd&still be standing...?&...Me neither./%";
        case "7a": return "Thing is...&you actually.../%";
        case "7b": return "You actually picked&a fight with ME.&...You shouldn't have./%";
        case "8a": return "You're... all alone,&aren't you...?/%";
        case "8b":
            if (_n == 0)
                return "Me? ...I don't&need anyone.&Not anymore./%";
            if (_kris)
                return "Me? I have Kris.&Kris is ALWAYS&behind me.../%";
            if (_n == 1)
                return "Me? I have " + _a + ".&I'll never be&alone again.../%";
            return "Me? I have " + _a + "&and " + _b + ". I'll never&be alone again.../%";
        case "9a":
            if (_n == 0)
                return "Go on. Hit me.&Hit me again.../%";
            if (_dn)
                return "Even if you&knock " + _p + " down.../%";
            return "Even... even if&you knock me down.../%";
        case "9b":
            if (_n == 0)
                return "...It doesn't hurt.&Nothing hurts&anymore.../%";
            if (_dn)
                return "...I'll stand alone.&I'm strong enough&now. Aren't I...?/%";
            return "I'll get back up.&I ALWAYS get&back up now.../%";
        case "10a":
            if (_n > 0 && _dn)
                return "As long as I'm&still... standing.../%";
            if (_kris)
                return "As long as Kris&tells me what&to do.../%";
            return "As long as I keep&getting stronger.../%";
        case "10b": return "You'll NEVER win!&Do you hear me?!&...Do you...?/%";
        case "11": return "So... give up.&...Please. I don't&want to do it again./%";
        case "12": return "You can't win...!&So give up...!&GIVE UP!!!/%";
        case "13a": return "... You won't&even.../%";
        case "13b": return _kris ? "...say a thing...&...Just like Kris./%" : "...say a thing...&...It's so quiet.&It's so cold.../%";
        case "14a": return "...Haha...&hahaha.../%";
        case "14b": return "I'm done talking...&I'm done being&scared.../%";
        case "14c": return "People like you...&make me want to&FREEZE it ALL!!/%";
    }
    return ".../%";
}

// the Cyan Knight (joke fight): its own joke lines, in their voices. The GOD speech stays the GOD speech.
function knight_taunt_cyan(_c, _beat, _orig, _n)
{
    var _r = (_c == 3);
    switch (_beat)
    {
        case "c6a": return "\\c5Um, so.../%";
        case "c6b": return _r ? "\\c5Is anyone else&worried about what&the Knight is doing?/%" : "\\c5Is anyone gonna&mention what the&HECK the Knight&is doing...?/%";
        case "c7a": return "\\c5W-well, it doesn't&matter!/%";
        case "c7b": return _r ? "\\c5I'm not scared!&No matter how many&settings you change!/%" : "\\c5I'm not scared!&Of the Knight, I mean.&Mice are different./%";
        case "c8a": return _r ? "\\c5Susie? She's not&even in this fight.../%" : "\\c5Susie? She's not&here... sadly.../%";
        case "c8b": return _r ? "\\c5Me? I'm... very&fluffy...!&(Is that good?)/%" : "\\c5Me? I'm Goated&With The Sauce!&(What does that mean?)/%";
        case "c9a": return "\\c5Even... even if&you set gravity&to 5.../%";
        case "c9b": return "\\c5Even if you rotate&the tracking swords&by 1 degree.../%";
        case "c9c": return _r ? "\\c5As long as Lancer&is behind me.../%" : "\\c5As long as Susie&is cheering for me&somewhere.../%";
        case "c10a": return "\\c5As long as a&Revivemint heals&half my HP.../%";
        case "c10b": return _r ? "\\c5And as long as I&never, EVER equip&the ThornRing.../%" : "\\c5And as long as I&don't learn any&weird spells.../%";
        case "c10c": return _r ? "\\c5You're never gonna&win! ...Probably!/%" : "\\c5Y-you're never gonna&win, you hear me?!/%";
        case "c11": return _r ? "\\c5So... um... a&$1000 gift for my&friends, please?/%" : "\\c5So... give me a&$1000 gift.&Fahaha! Kidding!/%";
        case "c12": return _r ? "\\c5W-what!? How is it&not defeated yet!?&That was the&final attack!/%" : "\\c5Wh-what!? How is it&not dead yet!? That&was the final attack!/%";
        case "c13a": return "\\c5... You won't&even say.../%";
        case "c14a": return _r ? "\\c5... hehe...&hehehe.../%" : "\\c5... faha...&fahahaha.../%";
        case "c14b": return _r ? "\\c5S-sorry, I think&I'm done talking./%" : "\\c5Gosh, I'm done&talking./%";
        case "c14c": return _r ? "\\c5... people like&you... are just&really r^5       ./%" : "\\c5... people like&you... just really&get on my n^5       ./%";
    }
    return _orig;
}

// the balloon for the line: the speaker's own voice and spot (knight scope, sets myblcon like scr_enemyblcon does)
function knight_taunt_balloon()
{
    var _c = knight_taunt_c();
    var _h = knight_hero_inst(_c);
    if (_h == noone)
    {
        _c = 2;
        _h = knight_hero_inst(2);
    }
    var _x = (_h != noone) ? _h.x : 0;
    var _y = (_h != noone) ? _h.y : 0;
    switch (_c)
    {
        case 3:
            global.typer = 74;
            scr_enemyblcon(_x + 85, _y + 45, 14);
            break;
        case 4:
            global.typer = 76;
            scr_enemyblcon(_x + 85, _y + 45, 14);
            break;
        default:
            global.typer = 75;
            scr_enemyblcon(_x + 92, _y + 38, 14);
            break;
    }
    if (_h != noone && (_c == 2 || _c == 3))
        scr_guardpeek(knight_hero_obj(_c));
    return myblcon;
}

// Kaizo Knight: a frozen speaker only shakes (the mod's own frozen Susie, any speaker now)
function knight_taunt_kz_frozen()
{
    var _c = knight_taunt_c();
    if (!variable_instance_exists(id, "k_freeze") || !is_array(k_freeze) || _c >= array_length(k_freeze) || !k_freeze[_c])
        return false;
    with (knight_hero_obj(_c))
    {
        if (variable_instance_exists(id, "herofrozen"))
        {
            with (herofrozen)
                scr_minishakeobj();
        }
    }
    return true;
}

// the Cyan Knight's joke narration after the first line ("Ralsei shakes his head. Kris doesn't respond.")
function knight_cyan_shake(_orig)
{
    var _c = knight_taunt_c();
    if (_c == 2 && knight_wr_here(1) && knight_wr_here(3) && !knight_wr_here(4))
        return _orig;
    var _f = knight_taunt_friends(_c);
    var _s = "";
    for (var _i = 0; _i < array_length(_f); _i++)
    {
        var _l = "";
        switch (_f[_i])
        {
            case 1: _l = "* Kris doesn't respond. They're dead."; break;
            case 2: _l = "* Susie pretends she didn't hear that."; break;
            case 3: _l = "* Ralsei shakes his head."; break;
            case 4: _l = "* Noelle shakes her head."; break;
        }
        if (_l != "")
            _s += ((_s == "") ? "" : "&") + _l;
    }
    if (_s == "")
        _s = "* Nobody responds.&* Nobody else is here.";
    return _s;
}

// ---------- the narration before the Roaring ----------
// "* Susie grew pale." / "* Susie struggled to give some kind of warning.": Susie when she is here, else the first of
// Ralsei / Noelle in party order, else Kris
function knight_pale_who()
{
    if (knight_wr_here(2))
        return 2;
    for (var _s = 0; _s < 3; _s++)
    {
        var _c = global.char[_s];
        if ((_c == 3 || _c == 4) && knight_wr_here(_c))
            return _c;
    }
    for (var _s = 0; _s < 3; _s++)
    {
        var _c = global.char[_s];
        if (_c >= 1 && (_c <= 4 || knight_cc_ok(_c)) && knight_wr_here(_c))
            return _c;
    }
    return 2;
}

function knight_pale_up()
{
    return (global.hp[knight_pale_who()] > 0);
}

// the name in the line (_def: what the fight itself would say for Susie, e.g. the Violet Knight's titles)
function knight_pale_name(_def)
{
    var _c = knight_pale_who();
    if (_c == 2)
        return _def;
    if (_c == 4 && global.flag[456] > 0)
        return "The Angel";
    if (_c >= 5 && global.knight_variant == 3)
        return knight_vtitle(_c);
    if (_c == 3 && variable_instance_exists(id, "ralseititle"))
        return ralseititle;
    if (_c == 1 && variable_instance_exists(id, "kristitle"))
        return kristitle;
    return knight_taunt_name(_c);
}

function knight_pale_text(_k, _def)
{
    var _nm = knight_pale_name(_def);
    if (_k == 0)
        return "* " + _nm + " grew pale.";
    return "* " + _nm + " struggled to give some kind of warning.";
}

// ---------- Noelle's N-Action ----------
// her talk to the Knight; on a Weird Route save she is the Angel (her own empty faces from Chapter 2's Snowgrave lines)
function knight_noe_act_text(_n)
{
    msgset(0, "* " + global.charname[4] + " tried talking.../");
    if (global.flag[456] > 0)
    {
        if (_n == 1)
        {
            scr_anyface_next("noelle", "e");
            msgnext("\\Ee* You're... scary, y'know./");
            scr_anyface_next("noelle", "d");
            msgnext("\\Ed* I used to like scary things.../");
            scr_anyface_next("noelle", "Z");
            msgnext("\\EZ* ...But now I'M the scary thing. Aren't I...?/");
        }
        else
        {
            scr_anyface_next("noelle", "e");
            msgnext("\\Ee* .../");
            scr_anyface_next("noelle", "Z");
            if (knight_wr_here(1))
                msgnext("\\EZ* It's so cold, Kris... Why is it so cold...?/");
            else
                msgnext("\\EZ* It's so cold... Why is it so cold...?/");
        }
    }
    else if (_n == 1)
    {
        scr_anyface_next("noelle", "B");
        msgnext("\\EB* U-um... h-hello? You d-don't have to do this...!/");
        scr_anyface_next("noelle", "Y");
        msgnext("\\EY* I don't know why you're so angry, but... p-please stop!/");
    }
    else
    {
        scr_anyface_next("noelle", "A");
        msgnext("\\EA* U-umm... c-can we just talk about it...?/");
    }
    scr_anyface_next("none", 0);
    msgnext("* (... but nothing happened.)/%");
    return 1;
}
