
// ===== DRBR REAL-RUNNER AUTOTEST HOOK (tests/realrunner: patched into a private TEST build only - never in a release) =====
// Active only when chapter3_windows/drbr_data/autotest.cfg exists. Lines "key=value":
//   kn=6                      the knight / boss of the practice match (its lineup id: 6 = Jevil, 7 Gerson, 8 Flowery, ...)
//   seq=3,11,3,11             the attacks forced in order (one per cycle), then the game ends
//   shots=0,10,20             frames of each attack (af) saved as kat_<n>_<attack>_<af>.png (screen_save)
//   set=mhp:999,skills:1      room settings (numbers) over the defaults
//   send=30@40                a skill sent at this game (sid) on frame af of the first attack (as a bot named LANCER)
//   detail=1                  a line every frame of an attack (the Devilsknives, the box, the SOUL)
function kat_note(_s)
{
    var _f = file_text_open_append("kat_log.txt");
    file_text_write_string(_f, _s);
    file_text_writeln(_f);
    file_text_close(_f);
    return 0;
}

function kat_csv(_s)
{
    var _o = [];
    var _cur = "";
    for (var _i = 1; _i <= string_length(_s); _i++)
    {
        var _ch = string_char_at(_s, _i);
        if (_ch == ",")
        {
            if (_cur != "")
                array_push(_o, _cur);
            _cur = "";
        }
        else if (_ch != " " && _ch != "\r")
            _cur += _ch;
    }
    if (_cur != "")
        array_push(_o, _cur);
    return _o;
}

function kat_has(_a, _v)
{
    for (var _i = 0; _i < array_length(_a); _i++)
    {
        if (_a[_i] == _v)
            return true;
    }
    return false;
}

function kat_load()
{
    var _K = { st: 0, t: 0, rt: 0, kn: 6, seq: [3], shots: [], set: [], send: -1, send_af: 0, sent: 0, detail: 0, fgo: 0, natk: 0,
        lastph: "", atk: -1, okn: 0, a_frames: 0, a_far: 0, a_farobj: "", a_max: 0, a_maxd: 0, idle_t: 0 };
    var _f = file_text_open_read("drbr_data/autotest.cfg");
    var _n = 0;
    while (!file_text_eof(_f) && _n < 50)
    {
        var _l = file_text_read_string(_f);
        file_text_readln(_f);
        _n++;
        var _p = string_pos("=", _l);
        if (_p <= 1)
            continue;
        var _k = string_copy(_l, 1, _p - 1);
        var _v = string_replace_all(string_copy(_l, _p + 1, string_length(_l) - _p), "\r", "");
        if (_k == "kn")
            _K.kn = real(_v);
        else if (_k == "seq" || _k == "shots")
        {
            var _a = kat_csv(_v);
            var _r = [];
            for (var _i = 0; _i < array_length(_a); _i++)
                array_push(_r, real(_a[_i]));
            variable_struct_set(_K, _k, _r);
        }
        else if (_k == "set")
            _K.set = kat_csv(_v);
        else if (_k == "send")
        {
            var _q = string_pos("@", _v);
            _K.send = real(string_copy(_v, 1, _q - 1));
            _K.send_af = real(string_copy(_v, _q + 1, string_length(_v) - _q));
        }
        else if (_k == "detail")
            _K.detail = real(_v);
    }
    file_text_close(_f);
    return _K;
}

// the attack's pieces: how many, and the ones far outside the screen (more than 1000 px past its edges)
function kat_pieces(_K)
{
    var _cx = camera_get_view_x(view_camera[0]);
    var _cy = camera_get_view_y(view_camera[0]);
    var _n = 0;
    with (all)
    {
        var _nm = object_get_name(object_index);
        var _piece = object_is_ancestor(object_index, obj_bulletparent) || object_index == obj_bulletparent
            || string_pos("obj_jv_", _nm) == 1 || string_pos("obj_hj_", _nm) == 1 || string_pos("obj_fl_", _nm) == 1
            || string_pos("obj_sn_", _nm) == 1 || string_pos("obj_pk_", _nm) == 1;
        if (!_piece || _nm == "obj_jv_joker" || _nm == "obj_jv_body" || _nm == "obj_jv_bg" || _nm == "obj_jv_dbc")
            continue;
        _n++;
        var _dx = max(0, _cx - x, x - (_cx + 640));
        var _dy = max(0, _cy - y, y - (_cy + 480));
        var _d = max(_dx, _dy);
        if (!is_numeric(x) || !is_numeric(y) || is_nan(x) || is_nan(y))
            _d = 999999;
        if (_d > _K.a_maxd)
            _K.a_maxd = _d;
        if (_d > 1000 && visible)
        {
            _K.a_far++;
            if (string_pos(_nm, _K.a_farobj) == 0 && string_length(_K.a_farobj) < 300)
                _K.a_farobj += _nm + "@" + string(round(x - _cx)) + "," + string(round(y - _cy)) + " ";
        }
    }
    _K.a_max = max(_K.a_max, _n);
    return _n;
}

function kat_tick()
{
    if (!variable_global_exists("kat"))
    {
        global.kat = 0;
        if (file_exists("drbr_data/autotest.cfg"))
        {
            global.kat = kat_load();
            kat_note("KAT begin kn " + string(global.kat.kn) + " seq " + string(array_length(global.kat.seq)) + " build " + string(kfo_version()));
        }
    }
    if (!is_struct(global.kat))
        return 0;
    var _K = global.kat;
    _K.t++;
    if (_K.t > 30 * 60 * 20)
    {
        kat_note("KAT timeout");
        game_end();
        return 0;
    }
    if (_K.st == 0)
    {
        if (room_get_name(room) == "room_dw_snow_zone" && instance_exists(obj_mainchara))
        {
            _K.rt++;
            if (_K.rt == 120)
            {
                kfo_get();
                global.kfo.name = "Kris";
                var _s = kfo_set_clean({ kn: [_K.kn], open: _K.kn, bots: 0 });
                _s.mhp = 999;
                _s.skills = 0;
                for (var _i = 0; _i < array_length(_K.set); _i++)
                {
                    var _kv = _K.set[_i];
                    var _p = string_pos(":", _kv);
                    if (_p > 1)
                        variable_struct_set(_s, string_copy(_kv, 1, _p - 1), real(string_copy(_kv, _p + 1, string_length(_kv) - _p)));
                }
                global.kfo.set = kfo_set_clean(_s);
                kfo_practice_start();
                kfo_host_set(global.kfo.set);
                var _why = kfo_host_start();
                kat_note("KAT practice start: '" + string(_why) + "'");
                _K.st = 1;
            }
        }
        return 0;
    }
    var _M = kfo_match();
    if (is_undefined(_M))
        return 0;
    if (_M.go)
        _K.fgo++;
    var _c = kbr_char();
    if (!_M.out)
    {
        if (global.hp[_c] < global.maxhp[_c])
            kat_note("HIT F" + string(_K.t) + " af " + string(_M.R.af) + " lost " + string(global.maxhp[_c] - global.hp[_c]));
        global.hp[_c] = global.maxhp[_c];
    }
    var _R = _M.R;
    var _ph = _R.ph;
    if (_ph != _K.lastph)
    {
        if (_K.lastph == "run")
            kat_note("ATK " + string(_K.natk) + " ai " + string(_K.atk) + " " + kbr_atk_name(_K.okn, _K.atk) + " | frames " + string(_K.a_frames) + " pieces max " + string(_K.a_max)
                + " far frames " + string(_K.a_far) + " max off-screen " + string(round(_K.a_maxd)) + " | " + _K.a_farobj);
        kat_note("PH F" + string(_K.t) + " " + _K.lastph + " -> " + _ph + " k " + string(_R.k) + " af " + string(_R.af) + " tt " + string(global.turntimer) + " cut " + string(_R.cut_why));
        if (_ph == "run")
        {
            _K.natk++;
            // the attack this cycle really is (the timeline's own: a boss's finale can take a cycle's place - the Roaring)
            var _cyc = kbr_tl_get(_M.tl, _R.k);
            _K.atk = _cyc.ai;
            _K.okn = _cyc.ok;
            _K.a_frames = 0;
            _K.a_far = 0;
            _K.a_farobj = "";
            _K.a_max = 0;
            _K.a_maxd = 0;
        }
        _K.lastph = _ph;
    }
    if (_ph == "run")
    {
        _K.a_frames++;
        kat_pieces(_K);
        if (_K.send >= 0 && _K.sent == 0 && _R.af == _K.send_af)
        {
            _K.sent = 1;
            array_push(_M.sk.pend, { sid: _K.send, from: 2, fn: "LANCER", sd: 777, t: 0, rf: 0, sh: 0 });
            kat_note("SEND F" + string(_K.t) + " sid " + string(_K.send) + " af " + string(_R.af));
        }
    }
    if ((_ph == "run" || _ph == "arm") && _K.detail)
    {
        var _l = "F" + string(_K.t) + " " + _ph + " af " + string(_R.af) + " tt " + string(global.turntimer);
        with (obj_jv_joker)
        {
            if (instance_exists(body))
                _l += " | body c" + string(body.condition) + " t" + string(body.timer);
        }
        with (obj_jv_cscythe)
            _l += " | S " + string(round(x)) + "," + string(round(y)) + " a" + string(image_alpha) + " r" + string(round(image_angle)) + " d" + string(depth) + " k" + string(king)
                + " ty" + string(type) + " kx" + string((variable_instance_exists(id, "kbrx") ? kbrx : 0)) + " c " + (variable_instance_exists(id, "jv_centerx") ? (string(round(jv_centerx)) + "," + string(round(jv_centery))) : "none");
        with (obj_collidebullet)
        {
            if (object_index == obj_collidebullet)
                _l += " | RB " + string(round(x)) + "," + string(round(y)) + " a" + string(image_alpha) + " " + sprite_get_name(sprite_index);
        }
        with (obj_growtangle)
            _l += " | BOX " + string(round(x)) + "," + string(round(y)) + " s" + string(image_xscale);
        with (obj_heart)
            _l += " | H " + string(round(x)) + "," + string(round(y));
        _l += " | cam " + string(camera_get_view_x(view_camera[0])) + "," + string(camera_get_view_y(view_camera[0])) + " fps " + string(fps);
        kat_note(_l);
    }
    if (_ph == "run" && kat_has(_K.shots, _R.af))
        screen_save("kat_" + string(_K.natk) + "_" + string(_K.atk) + "_" + string(_R.af) + ".png");
    if (_K.natk >= array_length(_K.seq) && _ph != "run" && _K.lastph != "run" && _K.natk > 0)
    {
        _K.idle_t++;
        if (_K.idle_t > 5)
        {
            kat_note("KAT done F" + string(_K.t));
            game_end();
        }
    }
    return 1;
}
