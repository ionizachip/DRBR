// ===== Build 52: watching a player = seeing their battle =====
// A watcher (out, or in the room but not in the match) sees what the player they follow sees:
//  - the watcher's own SOUL (hidden, never hurt: global.inv) sits on the followed player's SOUL every frame (where the
//    host's position stream puts it), so the Knight's attacks that home in on "the SOUL" go for the followed player, as
//    they do in that player's own game;
//  - every send aimed at the followed player is built in the watcher's game too: the same message from the host (every
//    game gets each targeted send), the same seed, the same attack objects (kbr_sa_start), started the same way when an
//    attack is running - so the swords, stars, crescents... are the ones the followed player is dodging. They are shown,
//    never hurt the watcher (an out SOUL takes no damage) and are never sent back or counted;
//  - DARKNESS on the followed player darkens the watcher's view around them;
//  - switching to someone else drops what was being built for the last one (their sends, their DARKNESS) and starts the
//    sends the new one got in the last 2.5 seconds (from their start: see the note in kbr_spec_switch).
// Watching never sends anything, never moves anyone's SOUL but the watcher's own hidden one, never changes a target or
// uses a skill.

// the player a watcher follows (-1: not watching, or nobody to follow)
function kbr_spec_pid(_M)
{
    if (is_undefined(_M) || !(_M.out || !_M.me) || !variable_struct_exists(_M, "spect"))
        return -1;
    return (is_numeric(_M.spect) && _M.spect >= 0) ? _M.spect : -1;
}

// every frame while watching (kbr_me_tick): the hidden SOUL on the followed one's, a switch noticed, the sends started
function kbr_spec_follow(_M)
{
    if (!variable_struct_exists(_M, "w_last"))
    {
        _M.w_last = -1;
        _M.wlog = [];
    }
    var _wp = kbr_spec_pid(_M);
    if (_wp != _M.w_last)
    {
        kbr_spec_switch(_M, _M.w_last, _wp);
        _M.w_last = _wp;
    }
    if (_wp < 0)
        return 0;
    kbr_spec_place(_M, _wp);
    // the sends that came for them start once an attack is running (as in their game); their DARKNESS runs down
    kbr_skill_pending();
    if (_M.sk.dark_w && _M.sk.dark_t > 0)
        _M.sk.dark_t--;
    return 1;
}

// the watcher's hidden SOUL onto the followed one's (here and again in the End Step, after everything else moved it)
function kbr_spec_place(_M, _wp)
{
    if (_wp < 0)
        return 0;
    var _id = string(_wp);
    if (instance_exists(obj_heart) && variable_struct_exists(_M.ps, _id))
    {
        var _q = variable_struct_get(_M.ps, _id);
        var _tx = kbr_ps_x(_q) + 10;
        var _ty = kbr_ps_y(_q) + 10;
        with (obj_heart)
        {
            var _cx = (bbox_right > bbox_left) ? ((bbox_left + bbox_right) / 2) : (x + 10);
            var _cy = (bbox_bottom > bbox_top) ? ((bbox_top + bbox_bottom) / 2) : (y + 10);
            x += _tx - _cx;
            y += _ty - _cy;
            visible = false;
            canmove = 0;
        }
        // DRBR: Flowery's board - the watcher's orange SOUL is a puppet of the followed one's: its height, its dash, and the
        // board's dash speed (the course is the room's; the board then scrolls as theirs does)
        kbr_fl_puppet(_q, _ty);
        // DRBR: Pink's lanes - the watcher's purple SOUL on the followed one's lane
        kbr_pk_puppet(_tx, _ty);
        // DRBR 1.0.1: Gerson's green shield - the watcher's turns as the followed one's (a bot's too)
        kbr_hj_puppet(_q);
    }
    return 1;
}

// the last few sends aimed at anyone (a watcher keeps them for a switch): { ms, e } with e a pending send
function kbr_spec_log(_M, _e)
{
    if (!variable_struct_exists(_M, "wlog"))
        _M.wlog = [];
    array_push(_M.wlog, { ms: current_time, e: _e });
    while (array_length(_M.wlog) > 0 && (array_length(_M.wlog) > 40 || current_time - _M.wlog[0].ms > 3000))
        array_delete(_M.wlog, 0, 1);
    return 1;
}

// following someone else: the last one's sends and DARKNESS go; the new one's recent sends start
function kbr_spec_switch(_M, _old, _new)
{
    var _S = _M.sk;
    // their sends being built here (real attack objects and pattern bullets), and the ones still waiting
    for (var _i = array_length(global.kbr_sa) - 1; _i >= 0; _i--)
    {
        var _G = global.kbr_sa[_i];
        if (!_G.twin && variable_struct_exists(_G, "watch") && _G.watch)
        {
            kbr_sa_kill(_G.gx);
            if (_G.loop >= 0)
                audio_stop_sound(_G.loop);
            array_delete(global.kbr_sa, _i, 1);
        }
    }
    with (obj_knight_twin_bullet)
    {
        if (variable_instance_exists(id, "kbrw") && kbrw)
            instance_destroy();
    }
    for (var _i = array_length(_S.pend) - 1; _i >= 0; _i--)
    {
        if (variable_struct_exists(_S.pend[_i], "w") && _S.pend[_i].w)
            array_delete(_S.pend, _i, 1);
    }
    _S.dark_t = 0;
    _S.dark_w = false;
    if (_new < 0 || !variable_struct_exists(_M, "wlog"))
        return 1;
    // what the new one got in the last 2.5 seconds. These start from their beginning: a send is built from its seed frame
    // by frame by the Knight's own objects, so its middle cannot be rebuilt without running those frames.
    for (var _i = 0; _i < array_length(_M.wlog); _i++)
    {
        var _w = _M.wlog[_i];
        if (current_time - _w.ms <= 2500 && _w.e.tg == _new)
        {
            var _e = { sid: _w.e.sid, from: _w.e.from, fn: _w.e.fn, sd: _w.e.sd, t: 0, rf: _w.e.rf, tg: _w.e.tg, mul: _w.e.mul, sh: _w.e.sh, w: 1 };
            array_push(_S.pend, _e);
        }
    }
    return 1;
}
