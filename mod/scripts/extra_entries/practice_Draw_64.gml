if (practicemode)
{
    var f_dotum = 5;
    var f_main = 7;
    if (!variable_instance_exists(id, "practicedraw"))
    {
        practicedraw = 1;
        practicey = -16;
        practicemove = 0;
        practiceatk = 0;
        practicestart = 0;
        practicebuff = 0;
        practicekill = 0;
        global.turntimer = 0;
    }
    var _pt = 80;
    if (practicekill > 0)
    {
        practicekill--;
        global.turntimer = 0;
    }
    if (global.turntimer > 0)
    {
        _pt = -48;
        practicestart = 1;
    }
    else if (global.myfight == 0)
    {
        if (practicebuff > 0)
            practicebuff--;
        var _maxatk = array_length(prac_list) - 1;
        var _move = 0;
        if (left_p())
        {
            _move = 1;
            practiceatk--;
            practicemove = -24;
        }
        if (right_p())
        {
            _move = 1;
            practiceatk++;
            practicemove = 24;
        }
        if (practiceatk < 0)
            practiceatk = _maxatk;
        if (practiceatk > _maxatk)
            practiceatk = 0;
        if (_move)
            snd_play(snd_menumove);
        if (button1_p())
        {
            practicebuff = 15;
            global.tension = 0;
            prac_sel = practiceatk;
            if (!variable_instance_exists(id, "tempitem"))
            {
                for (var _ti = 0; _ti < 12; _ti++)
                {
                    for (var _tj = 0; _tj < 3; _tj++)
                        tempitem[_ti][_tj] = global.item[_ti];
                }
            }
            scr_endturn();
        }
        if (button3_p() && practicebuff <= 0)
        {
            holdbreathcount = 1 - holdbreathcount;
            if (holdbreathcount > 0)
                snd_play(snd_mercyadd);
            else
                snd_play(snd_swing);
        }
    }
    if (practicey != _pt)
    {
        practicey = mean(practicey, practicey, _pt);
        if (abs(practicey - _pt) < 1)
            practicey = _pt;
    }
    if (practicemove != 0)
    {
        practicemove = mean(practicemove, 0);
        if (abs(practicemove) < 1)
            practicemove = 0;
    }
    var _alpha = min(1, practicey / 48);
    var _fn = draw_get_font();
    var _ha = draw_get_halign();
    var _va = draw_get_valign();
    var _co = draw_get_color();
    var _al = draw_get_alpha();
    draw_set_alpha(0.2 * _alpha);
    draw_set_color(c_black);
    for (var i = 1; i <= 12; i++)
        draw_rectangle(0, -1, 640, round((practicey / 12) * i), 0);
    var _cur = prac_list[clamp(practiceatk, 0, array_length(prac_list) - 1)];
    var _attackname = _cur[2];
    draw_set_alpha(_alpha);
    draw_set_font(f_dotum);
    draw_set_halign(fa_center);
    draw_set_valign(fa_top);
    draw_set_color(-1);
    var _atkY = round(practicey * 0.5);
    if (practicestart)
    {
        _atkY = max(_atkY, 8);
        if (global.turntimer > 0)
            draw_set_color(c_yellow);
        draw_set_alpha(max(_alpha, 0.5));
    }
    var _am = ((current_time % 800) >= 400) * 2;
    var _aw = max(120, string_width(_attackname) * 0.5 + 24);
    draw_text_outline(320, _atkY, _attackname, 0);
    draw_set_color(-1);
    if (global.turntimer > 0)
    {
        if (practicebuff > 0)
            practicebuff--;
        else
        {
            draw_set_font(f_main);
            draw_set_alpha(0.35);
            draw_text_outline(320, _atkY + 16, "[MENU] End Attack");
            if (button3_p())
            {
                practicebuff = 15;
                scr_kaizo_killobjs_prac();
                global.turntimer = 0;
                visible = true;
                image_alpha = 1;
            }
        }
    }
    if (global.turntimer <= 0)
    {
        draw_text_outline(320 - _aw - _am - min(practicemove, 0), _atkY, "<");
        draw_text_outline(320 + _aw + _am + max(practicemove, 0), _atkY, ">");
    }
    if (practicestart)
        draw_set_alpha(_alpha);
    draw_set_font(f_main);
    draw_set_color(c_ltgray);
    draw_text_outline(320, _atkY - 20, "Phase " + string(_cur[0]) + "  -  Turn " + string(_cur[1]));
    draw_set_halign(fa_left);
    var _hbtext = "HoldBreath: OFF";
    draw_set_color(c_red);
    if (holdbreathcount > 0)
    {
        _hbtext = "HoldBreath: ON";
        draw_set_color(c_lime);
    }
    draw_text_outline(8, practicey - 74, _hbtext, 0, 3);
    draw_set_color(c_ltgray);
    draw_text_outline(8, practicey - 74, "\n([MENU] to toggle)");
    var _exit_text = "(Press BACKSPACE to leave.)";
    draw_text_outline(632 - string_width(_exit_text), practicey - 74, _exit_text);
    draw_set_font(_fn);
    draw_set_halign(_ha);
    draw_set_valign(_va);
    draw_set_color(_co);
    draw_set_alpha(_al);
}
