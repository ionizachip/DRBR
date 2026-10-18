// a new room: the Tag Team / Remix knights that waited at the back in the last one are gone with it
global.knight_lu_inroom = false;
knight_mus_reset();
if (global.knight_reopen)
{
    global.knight_reopen = false;
    // (DRBR 1.0.1: back from an offline fight - the KNIGHT page; knight_ui_init)
    global.knight_ui_back = !(is_struct(global.kfo) && (global.kfo.reopen || kfo_in_room()));
    knight_menu_open(0);
}
