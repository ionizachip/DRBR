
// ===== Build 45: skills (the UNDERTALE ENDLESS way, for the Knight) =====
// The TP bar is the skill GAUGE (kbr_me_tick fills it). Hold CHARGE (C) to charge it: the use-bar climbs 1.5 a frame up to
// your gauge; let go past the draw cost (60 at 100% SKILL COST) to draw one skill, at the full cost (100) to draw two - the
// charge is spent. Drawn skills spin for 30 frames, then wait in your slots. Build 46: TAP USE (Z) to pick the next of your
// skills (the picked one has the yellow frame), HOLD USE for 12 frames to use the picked one; HOLD SLOT (A) puts the picked
// skill in the hold slot, or brings the held one back (swapped with the picked one when the slots are full). The keys are
// the player's own (MORE OPTIONS > KEYBINDS). RED skills land on every rival's screen, around THEIR SOUL (each game spawns
// them itself from the seed the host gives); GREEN skills help you. Everyone starts with FULL HEAL (when the room allows
// it). After a skill there is a cooldown. Sudden death: the Annoying Dog eats every green skill and no more can be drawn
// (unless the room keeps them). No menu sounds: picking, holding and drawing are silent (only a skill used or landing is
// heard).

// build 50: ids 1-21 (16 FULL HEAL is never drawn; 17-21 are the knights' own attacks, drawn only when their knight is
// in the match's knight pool)
// build 52: 22-25 added (DARKNESS, LOCK, LIFESTEAL, DETERMINATION)
// build 52: 26-31 JEVIL's (his own Chapter 1 pieces): SPADE RING, DIAMOND RAIN, CLUB SPIRAL, HEART CAROUSEL, DEVILSKNIFE, CHAOS BOMBS
// DRBR: 32-37 GERSON's (his own Chapter 4 pieces): HAMMER TOSS, SHELL PINBALL, SWING DOWN, SPEAR VOLLEY, BELL OF JUSTICE, GIGA HAMMER
// DRBR: 38-44 FLOWERY's (his own Chapter 5 pieces, on the target's orange board): JARONA, BAMBOO RUSH, AQUA'S KNIVES, SETH'S
// BOOKS, ORANGE & GREEN, BLUE & YELLOW, LAST JARONA
// DRBR: 45-50 SPAMTON NEO's (his own Chapter 2 pieces): PIPIS, FLYING HEADS, HEART ATTACK, KROMER RAIN, MAIL WALL, BIG SHOT
// DRBR: 51-56 PINK's (her own Chapter 5 pieces): KITTY PARADE, KITTY RAIN, HEART SHOTS, FUSE BOMBS, MEGA BOMB, ENCORE
function kbr_skill_count()
{
    return 57;
}

// [name, short, red?, pool (0 low, 1 mid, 2 full, 9 never drawn)]
function kbr_skill_info(_id)
{
    switch (_id)
    {
        case 1: return ["Sword", "SWORD", true, 0];
        case 2: return ["Flurry", "FLURRY", true, 0];
        case 3: return ["Diamond Storm", "DIAMND", true, 1];
        case 4: return ["Streamline", "STREAM", true, 1];
        case 5: return ["Ring", "RING", true, 1];
        case 6: return ["Star Burst", "STARS", true, 1];
        case 7: return ["Weird Circle", "WEIRD", true, 1];
        case 8: return ["Slow", "SLOW", true, 1];
        case 9: return ["Confuse", "CONFUS", true, 2];
        case 10: return ["Knightmare", "KNGHTM", true, 2];
        case 11: return ["Heal 40", "HEAL40", false, 0];
        case 12: return ["Heal 80", "HEAL80", false, 1];
        case 13: return ["Shield", "SHIELD", false, 1];
        case 14: return ["Regeneration", "REGEN", false, 1];
        case 15: return ["Reflection", "REFLCT", false, 2];
        case 16: return ["Full Heal", "FULLHP", false, 9];
        case 17: return ["Crescent Slash", "CRESNT", true, 1];
        case 18: return ["Sword Rain", "SWRAIN", true, 1];
        case 19: return ["Thunder Lines", "THUNDR", true, 1];
        case 20: return ["Fountain Split", "FOUNTN", true, 1];
        case 21: return ["Diamond Eruption", "ERUPT", true, 2];
        case 22: return ["Darkness", "DARK", true, 1];
        case 23: return ["Lock", "LOCK", true, 2];
        case 24: return ["Lifesteal", "LSTEAL", false, 1];
        case 25: return ["Determination", "DETERM", false, 2];
        case 26: return ["Spade Ring", "SPADES", true, 0];
        case 27: return ["Diamond Rain", "DIAMRN", true, 1];
        case 28: return ["Club Spiral", "CLUBS", true, 1];
        case 29: return ["Heart Carousel", "CAROSL", true, 2];
        case 30: return ["Devilsknife", "DVKNIF", true, 2];
        case 31: return ["Chaos Bombs", "BOMBS", true, 2];
        case 32: return ["Hammer Toss", "HAMMER", true, 0];
        case 33: return ["Shell Pinball", "SHELL", true, 1];
        case 34: return ["Swing Down", "SWING", true, 1];
        case 35: return ["Spear Volley", "SPEARS", true, 2];
        case 36: return ["Bell of Justice", "BELLS", true, 2];
        case 37: return ["Giga Hammer", "GIGA", true, 1];
        case 38: return ["Jarona", "JARONA", true, 0];
        case 39: return ["Bamboo Rush", "BAMBOO", true, 0];
        case 40: return ["Aqua's Knives", "KNIVES", true, 1];
        case 41: return ["Seth's Books", "BOOKS", true, 1];
        case 42: return ["Orange & Green", "TAGTEM", true, 1];
        case 43: return ["Blue & Yellow", "BLOOM", true, 2];
        case 44: return ["Last Jarona", "LASTJR", true, 2];
        case 45: return ["Pipis", "PIPIS", true, 0];
        case 46: return ["Flying Heads", "HEADS", true, 0];
        case 47: return ["Heart Attack", "HEART", true, 1];
        case 48: return ["Kromer Rain", "KROMER", true, 1];
        case 49: return ["Mail Wall", "MAIL", true, 2];
        case 50: return ["BIG SHOT", "BIGSHT", true, 2];
        case 51: return ["Kitty Parade", "KITTYS", true, 0];
        case 52: return ["Kitty Rain", "KRAIN", true, 0];
        case 53: return ["Heart Shots", "LANES", true, 1];
        case 54: return ["Fuse Bombs", "BOMBS", true, 1];
        case 55: return ["Mega Bomb", "MEGAB", true, 2];
        case 56: return ["Encore", "ENCORE", true, 2];
    }
    return ["?", "?", false, 9];
}

// build 51: a skill's name in the feed (FULL HEAL is MAX there, as on its diamond)
function kbr_skill_fname(_id)
{
    return (_id == 16) ? "MAX" : kbr_skill_name(_id);
}

function kbr_skill_desc(_id)
{
    switch (_id)
    {
        case 1: return "RED, low pool: a tracking sword follows the#rival's SOUL, flashes, then slashes.";
        case 2: return "RED, low pool: five tracking swords from#alternating sides.";
        case 3: return "RED, mid pool: Kaizo's diagonal diamond rows#sweep the box.";
        case 4: return "RED, mid pool: the Splitters' teeth stream#across the box.";
        case 5: return "RED, mid pool: a ring of stars closes in and#bursts.";
        case 6: return "RED, mid pool: three stars burst near the#rival's SOUL.";
        case 7: return "RED, mid pool: Kaizo's Rising Abyss - weird#circles fire up from the floor.";
        case 8: return "RED, mid pool: rivals' SOULs move slower#for 5 seconds.";
        case 9: return "RED, full pool: rivals' controls turn around#for 4 seconds.";
        case 10: return "RED, full pool: the Spinning Slashes - three#rounds of slashes, a black flash.";
        case 11: return "GREEN, low pool: heal 40 HP.";
        case 12: return "GREEN, mid pool: heal 80 HP.";
        case 13: return "GREEN, mid pool: the next hits (SHIELD HITS)#are taken for 10 seconds.";
        case 14: return "GREEN, mid pool: +3 HP every second for 10#seconds.";
        case 15: return "GREEN, full pool: attack skills sent to you#go back to their sender (REFLECT TIME).";
        case 17: return "RED, mid pool, KAIZO in the pool: pairs of#crescents split and speed across.";
        case 18: return "RED, mid pool, KAIZO in the pool: five swords#flip in above and dive.";
        case 19: return "RED, mid pool, ELECKNIGHT in the pool: four#lightning lines cross the box.";
        case 20: return "RED, mid pool, THORN in the pool: the seam#splits and fountains burst out.";
        case 21: return "RED, full pool, VIOLET in the pool: a violet#circle erupts in diamonds.";
        case 22: return "RED, mid pool: their screen goes dark for 5#seconds - only a circle of light around their#SOUL. More CRYSTALS: a smaller circle.";
        case 23: return "RED, full pool: one of their skills is#padlocked for 6 seconds.";
        case 24: return "GREEN, mid pool: for 10 seconds, the damage#your sends deal heals you (a quarter of it).";
        case 25: return "GREEN, full pool, once a match: for 15 seconds,#a hit that would put you OUT leaves you at 1 HP.";
        case 26: return "RED, low pool, JEVIL: a ring of spades closes#in, then they fly off one by one.";
        case 27: return "RED, mid pool, JEVIL: diamonds rise up through#the box under the rival's SOUL.";
        case 28: return "RED, mid pool, JEVIL: dark clubs dive in from#the corners and burst into club balls.";
        case 29: return "RED, full pool, JEVIL: a row of carousel horses#spins round the box.";
        case 30: return "RED, full pool, JEVIL: four Devilsknives swing#round the box's middle.";
        case 31: return "RED, full pool, JEVIL: three suit bombs fall in#and burst - spades, diamonds, hearts, clubs.";
        case 32: return "RED, low pool, GERSON: six of his hammers arc#in over the box around the rival's SOUL.";
        case 33: return "RED, mid pool, GERSON: a shell kicked at the#rival bounces off the box, then bursts.";
        case 34: return "RED, mid pool, GERSON: he swings down along#the rival's row and column, three times.";
        case 35: return "RED, full pool, GERSON: the rival's SOUL turns#GREEN - eight spears to block with a shield.";
        case 36: return "RED, full pool, GERSON: two bells ring - arcs of#notes rain into the rival's box.";
        case 37: return "RED, mid pool, GERSON: a giant hammer hangs#over the box, then crashes down.";
        case 38: return "ORANGE, low pool, FLOWERY: a Jarona copy runs#onto the rival's board - 3 lunges to parry.";
        case 39: return "ORANGE, low pool, FLOWERY: bamboo stalks with#blue joints - dash through, or get hit.";
        case 40: return "ORANGE, mid pool, FLOWERY: Aqua's lilypads, and#knife chains between them to jump over.";
        case 41: return "ORANGE, mid pool, FLOWERY: Seth's books stream#his words across the rival's board.";
        case 42: return "ORANGE, mid pool, FLOWERY: Orange and Flowery#tag-team, with Green's JUST KIDDING.";
        case 43: return "ORANGE, full pool, FLOWERY: Blue's flower bombs -#Yellow's beam and spiralling butterflies.";
        case 44: return "ORANGE, full pool, FLOWERY: LAST JARONA - a#rainbow charge, then four rushes at 24.";
        case 45: return "RED, low pool, SPAMTON: two pipis eggs drop in#and hatch - a spray of heads at the rival.";
        case 46: return "RED, low pool, SPAMTON: his flying heads swoop#past the box, spitting heads at the rival.";
        case 47: return "RED, mid pool, SPAMTON: a wire heart darts in#front of the box, firing at the rival.";
        case 48: return "RED, mid pool, SPAMTON: [[KROMER]] - dollar bills#stream across the rival's box.";
        case 49: return "RED, full pool, SPAMTON: two RECREW mail walls#rush across - each leaves a gap.";
        case 50: return "RED, full pool, SPAMTON: [[BIG SHOT]] - a beam#along the rival's row, then cannon shots.";
        case 51: return "RED, low pool, PINK: six cats race through the#rival's row and the rows beside it.";
        case 52: return "RED, low pool, PINK: cats fall and rise through#the rival's column.";
        case 53: return "RED, mid pool, PINK: lane bullets shoot through#the rival's SOUL from all four sides.";
        case 54: return "RED, mid pool, PINK: three fuse bombs land round#the rival and blow along their lines.";
        case 55: return "RED, full pool, PINK: one big bomb lands on the#rival - a wide blast down its row and column.";
        case 56: return "RED, full pool, PINK: ENCORE! Fans pop out round#the box and throw their hearts.";
    }
    return "";
}

// the parts of kbr_skill_info (GameMaker's compiler for this game cannot index a function's result directly)
function kbr_skill_name(_id)
{
    var _i = kbr_skill_info(_id);
    return _i[0];
}

function kbr_skill_short(_id)
{
    var _i = kbr_skill_info(_id);
    return _i[1];
}

function kbr_skill_pool(_id)
{
    var _i = kbr_skill_info(_id);
    return _i[3];
}

function kbr_skill_red(_id)
{
    var _i = kbr_skill_info(_id);
    return _i[2];
}

function kbr_skills_new(_e)
{
    var _sl = [];
    if (_e.fullheal && _e.skills)
        array_push(_sl, { sid: 16, rev: 0 });
    return { slots: _sl, hold: undefined, sel: 0, cd: 0, charge: 0, charging: false, zh: 0, zdone: false, zlock: false, seq: 0,
        shield: 0, shield_t: 0, regen_t: 0, reflect_t: 0, slow_t: 0, conf_t: 0, fullheal_t: -1, sent: 0, got: 0, dog_t: 0,
        pend: [], need: -1, mad0: false, used: 0, fh_used: 0, pop_t: 0, pop_n: 0, drawn: 0,
        dark_t: 0, dark_max: 0, dark_r: 64, dark_w: false, ls_t: 0, det_t: 0, det_n: 0, saved_t: 0 };
}

// is skill _id allowed in this match (the room's settings: skills on, the skill's own switch, sudden death)
function kbr_skill_ok(_id)
{
    var _M = kbr_match();
    if (is_undefined(_M))
        return true;
    var _e = _M.eff;
    if (!_e.skills)
        return false;
    if (_id == 16)
        return _e.fullheal && !(_M.sd_on && !_e.sdgreen);
    // build 50: a knight's own attack only while that knight is in the match's pool
    if (kbr_skill_knight(_id) >= 0 && !kbr_kn_has(kbr_skill_knight(_id)))
        return false;
    // build 52: SKILL FAMILIES (the knights' attacks, Jevil's, or both)
    if (!kbr_skfam_has(_e, kbr_skill_family(_id)))
        return false;
    for (var _i = 0; _i < array_length(_e.skoff); _i++)
    {
        if (_e.skoff[_i] == _id)
            return false;
    }
    if (_M.sd_on && !_e.sdgreen && !kbr_skill_red(_id))
        return false;
    return true;
}

// the charge one draw needs (60 at 100% SKILL COST; RANDOM SKILL COSTS: a new one between 40 and 100 after every draw)
function kbr_skill_need()
{
    var _M = kbr_match();
    var _e = _M.eff;
    var _S = _M.sk;
    if (_e.rcost)
    {
        if (_S.need < 0)
            _S.need = 40 + irandom(60);
        return _S.need;
    }
    return clamp(round((60 * _e.scost) / 100), 10, 100);
}

// the charge for two skills at once
function kbr_skill_need2()
{
    var _M = kbr_match();
    return clamp(round((100 * _M.eff.scost) / 100), kbr_skill_need(), 100);
}

// a draw from the pool for a charge of _amt (low under the middle of the two costs, mid above it, the full pool for two)
function kbr_skill_draw(_amt)
{
    var _M = kbr_match();
    var _n1 = kbr_skill_need();
    var _n2 = kbr_skill_need2();
    var _maxp = (_amt >= _n2) ? 2 : ((_amt >= ((_n1 + _n2) / 2)) ? 1 : 0);
    // SHIELD MADNESS: half of all draws are Shields
    if (_M.eff.shieldmad && kbr_skill_ok(13) && irandom(1) == 0)
        return 13;
    var _ok = [];
    for (var _id = 1; _id < kbr_skill_count(); _id++)
    {
        var _p = kbr_skill_pool(_id);
        if (_p <= _maxp && kbr_skill_ok(_id) && !(_id == 25 && kbr_det_had()))
            array_push(_ok, _id);
    }
    if (array_length(_ok) == 0)
    {
        for (var _id = 1; _id < kbr_skill_count(); _id++)
        {
            if (_id != 16 && _id != 25 && kbr_skill_ok(_id))
                array_push(_ok, _id);
        }
    }
    if (array_length(_ok) == 0)
        return -1;
    return _ok[irandom(array_length(_ok) - 1)];
}

// build 52: DETERMINATION is once a match - drawn, held or used already (the bots keep their own count)
function kbr_det_had()
{
    var _M = kbr_match();
    if (is_undefined(_M))
        return false;
    var _S = _M.sk;
    if (_S.det_n > 0)
        return true;
    for (var _i = 0; _i < array_length(_S.slots); _i++)
    {
        if (_S.slots[_i].sid == 25)
            return true;
    }
    return !is_undefined(_S.hold) && _S.hold.sid == 25;
}

// every step (from kbr_me_tick): the keys, the timers of the buffs on you
function kbr_skills_tick()
{
    var _M = kbr_match();
    var _S = _M.sk;
    var _e = _M.eff;
    var _c = kbr_char();
    if (_S.cd > 0)
        _S.cd--;
    if (_S.dog_t > 0)
        _S.dog_t--;
    for (var _i = 0; _i < array_length(_S.slots); _i++)
    {
        if (_S.slots[_i].rev > 0)
            _S.slots[_i].rev--;
        // build 52: LOCK's padlock
        if (variable_struct_exists(_S.slots[_i], "lk") && _S.slots[_i].lk > 0)
            _S.slots[_i].lk--;
    }
    if (!is_undefined(_S.hold) && variable_struct_exists(_S.hold, "lk") && _S.hold.lk > 0)
        _S.hold.lk--;
    if (_S.dark_t > 0)
        _S.dark_t--;
    if (_S.ls_t > 0)
        _S.ls_t--;
    if (_S.det_t > 0)
        _S.det_t--;
    if (_S.saved_t > 0)
        _S.saved_t--;
    // buffs
    if (_S.shield_t > 0)
    {
        _S.shield_t--;
        if (_S.shield_t <= 0)
            _S.shield = 0;
    }
    if (_S.regen_t > 0)
    {
        _S.regen_t--;
        if ((_S.regen_t mod 30) == 0)
            kbr_heal(3, false);
    }
    if (_S.reflect_t > 0)
        _S.reflect_t--;
    if (_S.slow_t > 0)
        _S.slow_t--;
    if (_S.conf_t > 0)
        _S.conf_t--;
    if (_S.fullheal_t > 0)
    {
        _S.fullheal_t--;
        if (_S.fullheal_t == 0)
        {
            kbr_heal(global.maxhp[_c], true, true);
            _S.fullheal_t = -1;
        }
    }
    // incoming skills that wait for an attack to be running
    kbr_skill_pending();
    kbr_skill_sel_fix();
    var _can = (_M.R.ph == "run" || _M.R.ph == "arm" || _M.R.ph == "idle") && !global.knight_frozen && !instance_exists(obj_knight_prompt) && _e.skills;
    if (!_can)
    {
        _S.charging = false;
        _S.charge = 0;
        _S.zh = 0;
        _S.zdone = false;
        // USE still down from a box or the countdown: it only counts once it was let go
        _S.zlock = kbr_key_held("use");
        return 0;
    }
    // CHARGE (C unless changed in KEYBINDS)
    if (kbr_key_held("charge"))
    {
        if (!_S.charging)
        {
            _S.charging = true;
            _S.charge = 0;
        }
        _S.charge = min(_M.g, _S.charge + 1.5);
    }
    else if (_S.charging)
    {
        _S.charging = false;
        var _amt = floor(_S.charge);
        _S.charge = 0;
        var _n1 = kbr_skill_need();
        if (_amt >= _n1)
        {
            var _n = (_amt >= kbr_skill_need2()) ? 2 : 1;
            var _room = clamp(_e.slots, 1, 4) - array_length(_S.slots);
            if (_room <= 0)
                kbr_log("* Your skill slots are full.", c_gray);
            else
            {
                _M.g = max(0, _M.g - _amt);
                var _got = 0;
                for (var _i = 0; _i < min(_n, _room); _i++)
                {
                    var _id = kbr_skill_draw(_amt);
                    if (_id < 0)
                        break;
                    array_push(_S.slots, { sid: _id, rev: 30 + (_i * 10) });
                    _got++;
                }
                _S.need = -1;
                // build 50: YOU DREW A SKILL! pops beside the TP bar
                _S.pop_t = (_got > 0) ? 50 : 0;
                _S.pop_n = _got;
                kbr_log((_got > 1) ? "* You drew two skills!" : "* You drew a skill!", c_white);
                // build 51: counted for HOW TO PLAY's charge lesson
                _S.drawn = (variable_struct_exists(_S, "drawn") ? _S.drawn : 0) + _got;
            }
        }
        else if (_amt > 10)
            kbr_log("* Not enough charge (" + string(_amt) + " of " + string(_n1) + ").", c_gray);
    }
    // USE (Z unless changed): a tap (let go before 12 frames) picks the next skill, held 12 frames it uses the picked one -
    // once per hold; still cooling down (or still spinning in) when the 12 frames are up, it goes off as soon as it can while
    // the key stays down
    // DRBR: the orange SOUL coming or going moves USE to another key (kbr_key_now): a key already down then counts only once
    // let go (a dash's Z, or HOLD BREATH's key, never fires a skill on the swap)
    var _orn = kbr_orange_on();
    if (!variable_struct_exists(_S, "orw"))
        _S.orw = _orn;
    if (_orn != _S.orw)
    {
        _S.orw = _orn;
        _S.zlock = true;
        _S.zh = 0;
        _S.zdone = false;
    }
    if (_S.zlock)
    {
        if (!kbr_key_held("use"))
            _S.zlock = false;
    }
    else if (kbr_key_held("use"))
    {
        _S.zh++;
        if (_S.zh >= 12 && !_S.zdone && kbr_skill_use() != 0)
            _S.zdone = true;
    }
    else
    {
        if (_S.zh > 0 && _S.zh < 12)
            kbr_skill_next();
        _S.zh = 0;
        _S.zdone = false;
    }
    // HOLD SLOT (A unless changed): the picked skill to the hold slot, or the held one back
    if (kbr_key_pressed("hold"))
        kbr_skill_stash();
    return 1;
}

// the picked slot stays on a skill (slots used, eaten or drawn move it)
function kbr_skill_sel_fix()
{
    var _M = kbr_match();
    var _S = _M.sk;
    var _n = array_length(_S.slots);
    _S.sel = (_n <= 0) ? 0 : clamp(floor(_S.sel), 0, _n - 1);
    return _S.sel;
}

// a tap of USE: the next skill (around to the first)
function kbr_skill_next()
{
    var _M = kbr_match();
    var _S = _M.sk;
    var _n = array_length(_S.slots);
    if (_n < 2)
        return 0;
    _S.sel = (kbr_skill_sel_fix() + 1) mod _n;
    return 1;
}

// HOLD SLOT: the picked skill into the hold slot; with a skill already held, that one comes back where the picked one is
// (the two swap places when the slots are full)
function kbr_skill_stash()
{
    var _M = kbr_match();
    var _S = _M.sk;
    var _sel = kbr_skill_sel_fix();
    var _n = array_length(_S.slots);
    if (is_undefined(_S.hold))
    {
        if (_n == 0 || _S.slots[_sel].rev > 0 || kbr_slot_locked(_S.slots[_sel]))
            return 0;
        _S.hold = _S.slots[_sel];
        array_delete(_S.slots, _sel, 1);
        kbr_skill_sel_fix();
        kbr_log("* " + kbr_skill_name(_S.hold.sid) + " held.", c_white);
        return 1;
    }
    var _back = _S.hold;
    if (kbr_slot_locked(_back))
        return 0;
    if (_n < clamp(_M.eff.slots, 1, 4))
    {
        array_insert(_S.slots, _sel, _back);
        _S.hold = undefined;
    }
    else
    {
        if (_S.slots[_sel].rev > 0 || kbr_slot_locked(_S.slots[_sel]) || kbr_slot_locked(_back))
            return 0;
        _S.hold = _S.slots[_sel];
        _S.slots[_sel] = _back;
    }
    _S.sel = _sel;
    kbr_log("* " + kbr_skill_name(_back.sid) + " is back." + (is_undefined(_S.hold) ? "" : (" " + kbr_skill_name(_S.hold.sid) + " held.")), c_white);
    return 1;
}

// the picked skill: 1 used, 0 not yet (cooldown, still spinning in, no skill), -1 refused (the room does not allow it now)
function kbr_skill_use()
{
    var _M = kbr_match();
    var _S = _M.sk;
    var _sel = kbr_skill_sel_fix();
    if (_S.cd > 0 || array_length(_S.slots) == 0 || _S.slots[_sel].rev > 0 || _M.out)
        return 0;
    var _id = _S.slots[_sel].sid;
    // build 52: padlocked by a rival's LOCK
    if (kbr_slot_locked(_S.slots[_sel]))
    {
        snd_play(snd_error);
        kbr_log("* It's locked tight. (" + string(ceil(_S.slots[_sel].lk / 30)) + "s)", c_gray);
        return -1;
    }
    if (!kbr_skill_ok(_id))
    {
        snd_play(snd_error);
        kbr_log("* " + kbr_skill_name(_id) + " can't be used now.", c_gray);
        return -1;
    }
    array_delete(_S.slots, _sel, 1);
    kbr_skill_sel_fix();
    _S.cd = round(90 * (_M.eff.cdm / 100));
    _S.used++;
    var _nm = kbr_skill_name(_id);
    _S.seq++;
    if (kbr_skill_red(_id))
    {
        _S.sent++;
        kfo_up({ k: "sk", mid: _M.mid, sid: _id, seq: _S.seq });
        snd_play(snd_bell);
        return 1;
    }
    // green: on you, here (the host is told for the feed and its checks)
    switch (_id)
    {
        case 11: kbr_heal(40, true); break;
        case 12: kbr_heal(80, true); break;
        case 13: _S.shield = _M.eff.shp; _S.shield_t = 300; break;
        case 14: _S.regen_t = 300; break;
        case 15: _S.reflect_t = _M.eff.rsec * 30; break;
        case 16: _S.fullheal_t = 20; _S.fh_used++; break;
        case 24: _S.ls_t = 300; break;
        case 25: _S.det_t = 450; _S.det_n++; break;
    }
    kfo_up({ k: "sg", mid: _M.mid, sid: _id, seq: _S.seq });
    snd_play(snd_power);
    return 1;
}

function kbr_slot_locked(_sl)
{
    return is_struct(_sl) && variable_struct_exists(_sl, "lk") && _sl.lk > 0;
}

// build 52: LIFESTEAL - the host says one of my sends hurt someone (_d HP): a quarter of it back while it lasts
function kbr_on_lsh(_m)
{
    var _M = kbr_match();
    if (is_undefined(_M) || _M.out || !_M.me || _M.sk.ls_t <= 0)
        return 0;
    var _d = kfo_jn(_m, "d", 0);
    if (!is_numeric(_d) || _d <= 0)
        return 0;
    return kbr_heal(max(1, round(_d * 0.25)), true);
}

// build 52: DETERMINATION - a hit that would put you OUT while it lasts leaves you at 1 HP instead (once)
function kbr_det_save(_M)
{
    var _S = _M.sk;
    if (_S.det_t <= 0)
        return false;
    _S.det_t = 0;
    _S.saved_t = 60;
    _M.flash = 6;
    snd_play(snd_power);
    kbr_bn_show("DETERMINATION", "* But it refused.", make_color_rgb(255, 60, 60));
    kfo_up({ k: "dsv", mid: _M.mid });
    return true;
}

function kbr_heal(_n, _fx, _full)
{
    var _M = kbr_match();
    if (is_undefined(_M) || _M.out)
        return 0;
    var _c = kbr_char();
    // build 51: MAX (FULL HEAL) fills to the match's real max HP whatever HEAL POWER is (a 50% HEAL POWER room only halves the
    // other heals); the max HP is the room's online one (Kaizo's own HP rules are off online since build 47)
    var _amt = (!is_undefined(_full) && _full) ? max(0, global.maxhp[_c] - global.hp[_c])
        : max(0, min(round(_n * (_M.eff.hmul / 100)), global.maxhp[_c] - global.hp[_c]));
    global.hp[_c] += _amt;
    _M.healed += _amt;
    if (_fx && _amt > 0 && instance_exists(global.charinstance[0]))
    {
        var _ci = global.charinstance[0];
        var _w = instance_create(_ci.x, (_ci.y + _ci.myheight) - 24, obj_dmgwriter);
        _w.delay = 1;
        _w.type = 3;
        _w.damage = _amt;
        with (_ci)
            instance_create(x, y, obj_healanim);
    }
    return _amt;
}

// a hit while SHIELD holds: it takes it
function kbr_skill_absorb(_d)
{
    var _M = kbr_match();
    var _S = _M.sk;
    if (_S.shield > 0 && _d > 0)
    {
        _S.shield--;
        if (_S.shield <= 0)
            _S.shield_t = 0;
        snd_play(snd_bell);
        return 0;
    }
    return _d;
}

// what the others see of you: 1 shield, 2 regeneration, 4 reflection, 8 holding breath
function kbr_skill_flags()
{
    var _M = kbr_match();
    if (is_undefined(_M))
        return 0;
    var _S = _M.sk;
    return ((_S.shield > 0) ? 1 : 0) + ((_S.regen_t > 0) ? 2 : 0) + ((_S.reflect_t > 0) ? 4 : 0) + (_M.hold ? 8 : 0) + ((_S.ls_t > 0) ? 16 : 0) + ((_S.det_t > 0) ? 32 : 0);
}

// ---------- a rival's skill lands on you ----------
// from the host: { k: "ska", from, fname, id, seq, sd (seed of the pattern), rf (reflected back) }
function kbr_on_ska(_m)
{
    var _M = kbr_match();
    if (is_undefined(_M) || !kbr_on())
        return 0;
    var _S = _M.sk;
    var _id = kfo_jn(_m, "sid", 0);
    var _from = kfo_jn(_m, "from", -1);
    var _fn = kfo_js(_m, "fname", "Someone");
    if (!kbr_skill_red(_id))
        return 0;
    // build 48: a targeted room - every game starts the pattern around each target (the bullets hurt whoever they touch)
    if (is_array(kfo_jv(_m, "tg")))
        return kbr_on_ska_tg(_M, _m, _id, _from, _fn);
    if (_M.out || !_M.me)
        return 0;
    if (_S.reflect_t > 0 && kfo_jn(_m, "rf", 0) == 0)
    {
        kfo_up({ k: "rf", mid: _M.mid, to: _from, sid: _id, seq: kfo_jn(_m, "seq", 0) });
        return 1;
    }
    _S.got++;
    array_push(_S.pend, { sid: _id, from: _from, fn: _fn, sd: kfo_jn(_m, "sd", 1), t: 0, rf: kfo_jn(_m, "rf", 0), sh: kfo_jn(_m, "sh", 0) });
    // build 51: no line of its own - the host's feed says it (it was the second copy of every send)
    return 1;
}

// build 48: the targeted send - one pattern per target, in every game (the sender's own game too: its bullets cannot hurt it)
function kbr_on_ska_tg(_M, _m, _id, _from, _fn)
{
    var _S = _M.sk;
    var _tg = kfo_ja(_m, "tg");
    var _tm = kfo_ja(_m, "tm");
    var _sd = kfo_jn(_m, "sd", 1);
    var _my = global.kfo.my;
    var _onme = 0;
    // build 52: a watcher builds the sends at the player they follow (and keeps the rest a moment for a switch)
    var _wp = kbr_spec_pid(_M);
    for (var _i = 0; _i < array_length(_tg) && _i < 8; _i++)
    {
        if (!is_numeric(_tg[_i]))
            continue;
        var _mul = (_i < array_length(_tm) && is_numeric(_tm[_i])) ? clamp(_tm[_i], 0.1, 4) : 1;
        var _back = (_tg[_i] == _from);
        if (_M.out || !_M.me)
        {
            var _we = { sid: _id, from: _from, fn: _fn, sd: _sd + (_i * 7919), t: 0, rf: _back ? 1 : 0, tg: _tg[_i], mul: _mul, sh: kfo_jn(_m, "sh", 0), w: 1 };
            kbr_spec_log(_M, _we);
            if (_wp >= 0 && _tg[_i] == _wp && _tg[_i] != _my)
            {
                array_push(_S.pend, _we);
                continue;
            }
        }
        // build 49: a game only makes the sends aimed at its own SOUL (no one sees the bullets sent to other players); the
        // host's game also makes the ones aimed at its bots (hidden and harmless there: they only hit the bots)
        var _mine = (_tg[_i] == _my && _M.me && !_M.out);
        var _tb = kfo_is_host() && is_struct(global.kfo.H) && !is_undefined(kfo_host_player(_tg[_i])) && kfo_host_player(_tg[_i]).bot;
        if (!_mine && !_tb)
            continue;
        array_push(_S.pend, { sid: _id, from: _from, fn: _fn, sd: _sd + (_i * 7919), t: 0, rf: _back ? 1 : 0, tg: _tg[_i], mul: _mul, sh: kfo_jn(_m, "sh", 0) });
        if (_tg[_i] == _my && _M.me && !_M.out)
            _onme++;
    }
    // at most 40 waiting (a watcher whose box is gone a while)
    if (array_length(_S.pend) > 40)
        array_delete(_S.pend, 0, array_length(_S.pend) - 40);
    // build 51: no line of its own - the host's feed line for this send is the one line (it used to be written twice)
    if (_onme > 0 && _from != _my)
        _S.got++;
    return 1;
}

// skills wait for a box and a SOUL (between two attacks the box may be gone)
function kbr_skill_pending()
{
    var _M = kbr_match();
    var _S = _M.sk;
    if (array_length(_S.pend) == 0 || _M.R.ph != "run" || !instance_exists(obj_heart) || !instance_exists(obj_growtangle))
        return 0;
    // build 50: a box-splitting attack moved the box away: the sends wait for it (they use the box's real place and size)
    if (instance_find(obj_growtangle, 0).x < -1000)
        return 0;

    // at most two patterns start per step, the rest the next steps
    // DRBR: Flowery's sends (his orange board's pieces) wait in the list for his board - 40 seconds at most, then they wither;
    // the others land in order past them
    var _n = 0;
    var _i = 0;
    while (_i < array_length(_S.pend) && _n < 2)
    {
        var _s = _S.pend[_i];
        var _forme = !(variable_struct_exists(_s, "w") && _s.w) && (!variable_struct_exists(_s, "tg") || _s.tg == global.kfo.my);
        if (kbr_fl_is_send(_s.sid) && _forme && !kbr_fl_sa_ready())
        {
            if (!variable_struct_exists(_s, "w0"))
                _s.w0 = current_time;
            if (current_time - _s.w0 > 40000)
            {
                array_delete(_S.pend, _i, 1);
                kbr_log("* " + string_upper(kbr_skill_name(_s.sid)) + " withered: no orange board came.", c_gray);
                continue;
            }
            _i++;
            continue;
        }
        array_delete(_S.pend, _i, 1);
        kbr_skill_land(_s);
        _n++;
    }
    return 1;
}

function kbr_skill_shot(_x, _y, _spr, _wait, _ldir, _lspd, _dmg)
{
    var _b = instance_create_depth(_x, _y, -10, obj_knight_twin_bullet);
    _b.sprite_index = _spr;
    _b.image_blend = c_white;
    // build 48: a targeted send - the sender's colour, its strength, who sent it and whose SOUL it goes for
    var _cx = variable_global_exists("kbr_shot_ctx") ? global.kbr_shot_ctx : undefined;
    // build 52: an untargeted send knows its sender too (LIFESTEAL and the knockout credit)
    if (variable_global_exists("kbr_shot_from") && global.kbr_shot_from >= 0)
        _b.kbrf = global.kbr_shot_from;
    if (is_struct(_cx))
    {
        _b.image_blend = _cx.col;
        _dmg *= _cx.mul;
        _b.kbrf = _cx.from;
        _b.kbrt = _cx.tg;
        if (_cx.from == global.kfo.my)
        {
            _b.grazepoints = 0;
            _b.grazed = 1;
        }
        // build 52: built for a watcher: shown, never a hit
        if (variable_struct_exists(_cx, "w") && _cx.w)
        {
            _b.kbrw = 1;
            _b.grazepoints = 0;
            _b.grazed = 1;
        }
        // build 49: aimed at someone else (only the host's game makes these: the ones at its bots) - hidden and harmless
        // from the very first frame (they used to show for one frame before their Step hid them)
        else if (_cx.tg != global.kfo.my)
        {
            _b.visible = false;
            _b.active = 0;
            _b.image_alpha = 0;
            _b.grazepoints = 0;
            _b.grazed = 1;
        }
    }
    _b.wait = _wait;
    _b.ldir = _ldir;
    _b.lspd = _lspd;
    _b.image_angle = _ldir + _b.angoff;
    _b.kbr = 1;
    _b.kbrd = _dmg;
    _b.life = 200;
    return _b;
}

// the pattern of skill _s.id, around this game's own SOUL (the pattern's own numbers come from its seed)
function kbr_skill_land(_s)
{
    var _h = instance_find(obj_heart, 0);
    var _hx = (_h.bbox_left + _h.bbox_right) / 2;
    var _hy = (_h.bbox_top + _h.bbox_bottom) / 2;
    var _bx = instance_find(obj_growtangle, 0);
    var _art = knight_twin_art();
    var _g = kbr_rng(_s.sd);
    var _M = kbr_match();
    var _S = _M.sk;
    // build 48: a targeted send starts around its target's SOUL (where this game sees it; the box's middle when it cannot)
    global.kbr_shot_ctx = undefined;
    global.kbr_shot_from = variable_struct_exists(_s, "from") ? _s.from : -1;
    var _me = true;
    // build 52: built for a watcher - shown as the followed player sees it, never a hit
    var _watch = variable_struct_exists(_s, "w") && _s.w && variable_struct_exists(_s, "tg") && _s.tg == kbr_spec_pid(_M);
    if (variable_struct_exists(_s, "w") && _s.w && !_watch)
    {
        global.kbr_shot_from = -1;
        return 0;
    }
    if (_watch)
    {
        // the watcher's hidden SOUL is on theirs (kbr_spec_follow): the patterns start around it, the sender's colour
        global.kbr_shot_ctx = { col: kbr_pcol(kbr_pslot(_s.from)), mul: variable_struct_exists(_s, "mul") ? _s.mul : 1, from: _s.from, tg: _s.tg, w: true };
        if (kbr_sa_has(_s.sid))
        {
            global.kbr_shot_ctx = undefined;
            global.kbr_shot_from = -1;
            kbr_sa_start(_s, _hx, _hy, _s.tg);
            return 1;
        }
        if (_s.sid == 22)
        {
            _S.dark_t = round(150 * kbr_tg_fx_mul(_s));
            _S.dark_max = _S.dark_t;
            _S.dark_r = clamp(64 - (kbr_tg_shard_step(_M.eff.shards ? (variable_struct_exists(_s, "sh") ? _s.sh : 0) : 0) * 7), 36, 64);
            _S.dark_w = true;
        }
        if (_s.sid == 10)
            _M.flash = 12;
        global.kbr_shot_ctx = undefined;
        global.kbr_shot_from = -1;
        return 1;
    }
    if (variable_struct_exists(_s, "tg"))
    {
        _me = (_s.tg == global.kfo.my) && _M.me && !_M.out;
        var _pos = kbr_tg_pos(_s.tg);
        if (!_me)
        {
            if (is_undefined(_pos))
                _pos = [_bx.x, _bx.y];
            _hx = _pos[0];
            _hy = _pos[1];
        }
        global.kbr_shot_ctx = { col: kbr_pcol(kbr_pslot(_s.from)), mul: _s.mul, from: _s.from, tg: _s.tg };
    }
    // build 50: aimed at my own SOUL - the Knights' real attack objects (online_sent50.gml); the host's hidden copies for its
    // bots stay twin bullets (the bots dodge those)
    if (_me && kbr_sa_has(_s.sid))
    {
        global.kbr_shot_ctx = undefined;
        global.kbr_shot_from = -1;
        kbr_sa_start(_s, _hx, _hy);
        return 1;
    }
    // build 52: the effect skills on a bot (the host's game: its hidden copy of a targeted send)
    if (!_me && (_s.sid == 8 || _s.sid == 9 || _s.sid == 22 || _s.sid == 23) && variable_struct_exists(_s, "tg") && kfo_is_host() && is_struct(global.kfo.H))
    {
        var _bt = kfo_host_player(_s.tg);
        if (!is_undefined(_bt) && _bt.bot)
            kfo_bot_fx(_bt, _s.sid, kbr_tg_fx_mul(_s));
        global.kbr_shot_ctx = undefined;
        global.kbr_shot_from = -1;
        return 1;
    }
    if ((_s.sid >= 17 && _s.sid <= 21) || (_s.sid >= 26 && _s.sid <= 56))
    {
        kbr_sa_bot(_s, _hx, _hy, _bx, _g, _art);
        global.kbr_shot_ctx = undefined;
        global.kbr_shot_from = -1;
        return 1;
    }
    switch (_s.sid)
    {
        case 1:
            // one big slash: a sword from a random side, aimed, slow to come
            var _a = kbr_rng_int(_g, 360);
            var _sh = kbr_skill_shot(_hx + lengthdir_x(190, _a), _hy + lengthdir_y(190, _a), _art.sword, 26, _a + 180, 12, 24);
            _sh.aim = true;
            _sh.image_xscale = 1.5;
            _sh.image_yscale = 1.5;
            break;
        case 2:
            // a flurry: five swords from alternating sides
            for (var _i = 0; _i < 5; _i++)
            {
                var _side = ((_i mod 2) == 0) ? 0 : 180;
                var _ang = _side + (kbr_rng_int(_g, 50) - 25);
                var _sh2 = kbr_skill_shot(_hx + lengthdir_x(180, _ang), _hy + lengthdir_y(180, _ang), _art.sword, 18 + (_i * 8), _ang + 180, 11, 20);
                _sh2.aim = true;
            }
            break;
        case 3:
            // diamonds falling across the box
            for (var _i = 0; _i < 12; _i++)
            {
                var _x = (_bx.x - 70) + kbr_rng_int(_g, 140);
                kbr_skill_shot(_x, _bx.y - 150 - (_i * 14), _art.small, 10 + (_i * 4), 270, 5, 14);
            }
            break;
        case 4:
            // a stream sweeping in from one side
            var _fl = kbr_rng_int(_g, 2);
            for (var _i = 0; _i < 9; _i++)
            {
                var _yy = (_bx.y - 64) + (_i * 16);
                kbr_skill_shot(_fl ? (_bx.x + 190) : (_bx.x - 190), _yy, _art.small, 12 + (_i * 5), _fl ? 180 : 0, 6, 14);
            }
            break;
        case 5:
            // a ring closing in
            for (var _i = 0; _i < 12; _i++)
            {
                var _ra = _i * 30;
                kbr_skill_shot(_hx + lengthdir_x(150, _ra), _hy + lengthdir_y(150, _ra), _art.star, 30, _ra + 180, 3, 14);
            }
            break;
        case 6:
            // three star bursts around the SOUL
            for (var _j = 0; _j < 3; _j++)
            {
                var _ba = kbr_rng_int(_g, 360);
                var _px = _hx + lengthdir_x(150, _ba);
                var _py = _hy + lengthdir_y(150, _ba);
                var _aim = point_direction(_px, _py, _hx, _hy);
                for (var _k = 0; _k < 6; _k++)
                    kbr_skill_shot(_px, _py, _art.small, 16 + (_j * 30), _aim + (_k * 60), 3.8, 14);
            }
            break;
        case 7:
            // two rings, one turned half a step
            for (var _i = 0; _i < 16; _i++)
            {
                var _wa = _i * 22.5;
                var _r = ((_i mod 2) == 0) ? 160 : 120;
                kbr_skill_shot(_hx + lengthdir_x(_r, _wa), _hy + lengthdir_y(_r, _wa), _art.small, 24 + ((_i mod 2) * 12), _wa + 180 + 20, 2.6, 12);
            }
            break;
        case 8:
            if (_me)
            {
                _S.slow_t = round(150 * kbr_tg_fx_mul(_s));
                snd_play(snd_bell);
            }
            break;
        case 9:
            if (_me)
            {
                _S.conf_t = round(120 * kbr_tg_fx_mul(_s));
                snd_play(snd_error);
            }
            break;
        case 22:
            // DARKNESS: the screen goes dark but a circle around the SOUL (smaller for a sender with more CRYSTALS)
            if (_me)
            {
                var _sh = variable_struct_exists(_s, "sh") ? _s.sh : 0;
                _S.dark_t = round(150 * kbr_tg_fx_mul(_s));
                _S.dark_max = _S.dark_t;
                _S.dark_r = clamp(64 - (kbr_tg_shard_step(_M.eff.shards ? _sh : 0) * 7), 36, 64);
                snd_play(snd_knight_jump_quick);
            }
            break;
        case 23:
            // LOCK: one of my skills (the slots and the held one) padlocked for 6 seconds
            if (_me)
            {
                var _can = [];
                for (var _i = 0; _i < array_length(_S.slots); _i++)
                {
                    if (!kbr_slot_locked(_S.slots[_i]))
                        array_push(_can, _S.slots[_i]);
                }
                if (!is_undefined(_S.hold) && !kbr_slot_locked(_S.hold))
                    array_push(_can, _S.hold);
                if (array_length(_can) > 0)
                {
                    var _lk = _can[irandom(array_length(_can) - 1)];
                    _lk.lk = round(180 * kbr_tg_fx_mul(_s));
                    _lk.lk0 = _lk.lk;
                    kbr_log("* Your " + kbr_skill_name(_lk.sid) + " got padlocked!", c_red);
                }
                else
                    kbr_log("* A padlock found nothing to lock.", c_gray);
                snd_play(snd_error);
            }
            break;
        case 10:
            // KNIGHTMARE: eight aimed swords and two star bursts, a black flash and the sting
            for (var _i = 0; _i < 8; _i++)
            {
                var _na = kbr_rng_int(_g, 360);
                var _sh3 = kbr_skill_shot(_hx + lengthdir_x(185, _na), _hy + lengthdir_y(185, _na), _art.sword, 16 + (_i * 12), _na + 180, 12, 32);
                _sh3.aim = true;
            }
            for (var _j = 0; _j < 2; _j++)
            {
                var _qa = kbr_rng_int(_g, 360);
                for (var _k = 0; _k < 8; _k++)
                    kbr_skill_shot(_hx + lengthdir_x(160, _qa), _hy + lengthdir_y(160, _qa), _art.small, 30 + (_j * 40), _qa + 180 + (_k * 45), 4, 32);
            }
            if (_me)
            {
                _M.flash = 12;
                snd_play(snd_knight_jump_quick);
            }
            break;
    }
    global.kbr_shot_ctx = undefined;
    global.kbr_shot_from = -1;
    return 1;
}

// SLOW / CONFUSE: longer with a stronger send (never past the balance's cap), shorter for a part of a split send
function kbr_tg_fx_mul(_s)
{
    if (!variable_struct_exists(_s, "mul"))
        return 1;
    var _B = kbr_tg_bal();
    return clamp(_s.mul, 0.4, _B.fx_max);
}

// the hub controller's End Step: Confuse and MIRROR CONTROLS turn this step's own SOUL movement around (after the SOUL
// moved itself; kept inside the box)
function kbr_end_step()
{
    var _M = kbr_match();
    // build 52: a watcher's hidden SOUL back on the followed one's after this step's moves
    if (!is_undefined(_M) && kbr_on() && kbr_spec_pid(_M) >= 0)
        return kbr_spec_place(_M, kbr_spec_pid(_M));
    if (is_undefined(_M) || !kbr_on() || _M.out || !_M.me || !instance_exists(obj_heart) || !instance_exists(obj_growtangle))
        return 0;
    // build 47: QUICK SETTINGS open: the SOUL's own move of this step is taken back (it stays where it is)
    if ((variable_struct_exists(_M, "vw") && _M.vw.qs) || kfo_chat_typing())
        return kbr_qs_hold_soul(_M);
    var _inv = (_M.sk.conf_t > 0) != (_M.eff.mirror == 1);
    if (!_inv)
        return 0;
    var _b = instance_find(obj_growtangle, 0);
    with (obj_heart)
    {
        if (canmove)
        {
            var _dx = x - xprevious;
            var _dy = y - yprevious;
            x = xprevious - _dx;
            y = yprevious - _dy;
            var _w = bbox_right - bbox_left;
            var _hh = bbox_bottom - bbox_top;
            x = clamp(x, _b.bbox_left + 2, max(_b.bbox_left + 2, _b.bbox_right - _w - 2));
            y = clamp(y, _b.bbox_top + 2, max(_b.bbox_top + 2, _b.bbox_bottom - _hh - 2));
        }
    }
    return 1;
}

// sudden death: the Annoying Dog runs across and eats every green skill
function kbr_dog_eats()
{
    var _M = kbr_match();
    var _S = _M.sk;
    var _n = 0;
    if (_M.eff.sdgreen)
        return 0;
    for (var _i = array_length(_S.slots) - 1; _i >= 0; _i--)
    {
        if (!kbr_skill_red(_S.slots[_i].sid))
        {
            array_delete(_S.slots, _i, 1);
            _n++;
        }
    }
    if (!is_undefined(_S.hold) && !kbr_skill_red(_S.hold.sid))
    {
        _S.hold = undefined;
        _n++;
    }
    kbr_skill_sel_fix();
    _S.shield = 0;
    _S.shield_t = 0;
    _S.regen_t = 0;
    _S.ls_t = 0;
    _S.dog_t = 120;
    return _n;
}

function kbr_sudden_death()
{
    var _n = kbr_dog_eats();
    var _M = kbr_match();
    // build 51: the big announcement
    if (_M.eff.sdgreen || _n == 0)
        kbr_bn_show("SUDDEN DEATH", "* The ground shakes. Your max HP starts slipping away.", make_color_rgb(255, 60, 60));
    else
        kbr_bn_show("SUDDEN DEATH", "* The Annoying Dog ate your green skills. It looks very proud.", make_color_rgb(255, 60, 60));
    return 1;
}

function kbr_final_two_fx()
{
    var _M = kbr_match();
    // build 51: the big announcement
    kbr_bn_show("FINAL TWO", "* Only two SOULs left. The Roaring is coming.", make_color_rgb(255, 60, 60));
    _M.flash = 8;
    if (_M.eff.ftmus)
        kfo_mus_situ("lms");
    return 1;
}

// build 52: which family an attack skill belongs to: 1 the knights' (their swords, stars, slashes...), 2 Jevil's; 0 the ones of
// every family (the effects - SLOW, CONFUSE, DARKNESS, LOCK - and every green skill)
function kbr_skill_family(_id)
{
    // DRBR: the table of kbr_skill_fams (drbr53.gml): the knights' attack skills and each boss's "sends"
    var _t = kbr_skill_fams();
    return (is_numeric(_id) && _id >= 0 && _id < array_length(_t)) ? _t[_id] : 0;
}

// SENDS (the skfam setting, build 52's SKILL FAMILIES): 0 MATCH CURRENT BOSS - the family of the boss on stage now (the
// knights' while a knight is out, Jevil's while Jevil is ...); 3 ALL ENABLED - every family of the match's encounters;
// otherwise one fixed family (its fid: 1 KNIGHT, 2 JEVIL, 4 SPAMTON, 5 GERSON, 6 PINK, 7 FLOWERY). Effects and green skills
// (family 0) are always there.
function kbr_skfam_has(_e, _fam)
{
    if (_fam == 0)
        return true;
    var _kn = variable_struct_exists(_e, "kn") ? _e.kn : [0];
    // DRBR: Flowery's sends are pieces of his orange board: only in a match he is in (elsewhere they would wait for nothing)
    if (_fam == KBR_FAM_FLOWERY)
    {
        var _fl = false;
        for (var _j = 0; _j < array_length(_kn); _j++)
        {
            if (kbr_fam_of_ok(_kn[_j]) == KBR_FAM_FLOWERY)
                _fl = true;
        }
        if (!_fl)
            return false;
    }
    var _m = variable_struct_exists(_e, "skfam") ? _e.skfam : 0;
    if (_m == 0)
        return _fam == kbr_fam_now(_e);
    if (_m != KBR_FAM_ALL)
        return _fam == _m;
    for (var _i = 0; _i < array_length(_kn); _i++)
    {
        if (kbr_fam_of_ok(_kn[_i]) == _fam)
            return true;
    }
    return false;
}
