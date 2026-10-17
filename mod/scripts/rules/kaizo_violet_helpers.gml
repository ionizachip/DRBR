// Extra helpers required by kaizo_violet_rules.json (global scripts)
// knight_canon_xy(name, axis): canonical PTB02 con==8 positions. name "kris"|"susie"|"ralsei", axis "x"|"y".
function knight_canon_xy(_n, _a)
{
    if (_n == "kris") return (_a == "x") ? 2356 : 104;
    if (_n == "susie") return (_a == "x") ? 2310 : 142;
    return (_a == "x") ? 2288 : 190;
}
// knight_friends_down(): true iff no PRESENT member among ids 1,3,4 has hp > 0.
function knight_friends_down()
{
    var _ids = [1, 3, 4];
    for (var _i = 0; _i < 3; _i++)
        if (scr_havechar(_ids[_i]) && global.hp[_ids[_i]] > 0) return false;
    return true;
}
// knight_susie_line(orig): Susie's balloon text. F = present ids among 1,3,4 (order Kris, Ralsei, Noelle),
// names Kris/Ralsei/Noelle, pronouns them/him/her. Returns orig when F == [Kris, Ralsei].
function knight_susie_line(_o)
{
    var _f = [], _nm = [], _pn = [];
    if (scr_havechar(1)) { array_push(_f, 1); array_push(_nm, "Kris"); array_push(_pn, "them"); }
    if (scr_havechar(3)) { array_push(_f, 3); array_push(_nm, "Ralsei"); array_push(_pn, "him"); }
    if (scr_havechar(4)) { array_push(_f, 4); array_push(_nm, "Noelle"); array_push(_pn, "her"); }
    var _n = array_length(_f);
    if (_n == 2 && _f[0] == 1 && _f[1] == 3) return _o;
    var _p = (_n == 1) ? _pn[0] : "them";
    if (_o == "Me? I got...&Kris and Ralsei&behind me./%")
    { if (_n == 0) return "Me? I've...&got friends I KNOW&would back me up./%"; if (_n == 1) return "Me? I got...&" + _nm[0] + " here&behind me./%"; return "Me? I got...&" + _nm[0] + " and " + _nm[1] + "&behind me./%"; }
    if (_o == "As long as Kris,&Ralsei, are here.../%")
    { if (_n == 0) return "But as long as&I keep standing.../%"; if (_n == 1) return "As long as " + _nm[0] + "&is right here.../%"; return "As long as " + _nm[0] + ",&" + _nm[1] + ", are here.../%"; }
    if (_o == "Even... even if&you knock them down.../%")
    { if (_n == 0) return "You... you can&hit me all you like.../%"; return "Even... even if&you knock " + _p + " down.../%"; }
    if (_o == "As long as Kris has got&a hand to lift me up with.../%")
    { if (_n == 0) return "As long as I can&still stand up.../%"; if (_n == 1) return "As long as " + _nm[0] + " has got&a hand to lift me up with.../%"; return "As long as my friends have got&a hand to lift me up with.../%"; }
    if (_o == "As long as I'm here to&lift them back up.../%")
    { if (_n == 0) return "As long as I'm still&standing.../%"; return "As long as I'm here to&lift " + _p + " back up.../%"; }
    return _o;
}
