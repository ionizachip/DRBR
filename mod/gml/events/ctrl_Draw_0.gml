// build 50: the telegraphs and slashes of the players' sent attacks (under the HUD)
kbr_sa_draw();
knight_hud_draw();
// build 45: the cold place as the online room's lobby (the other players walking around)
kfo_world_draw();
// build 48: the room's chat in the cold place
kfo_chat_draw_world();
// build 49: the DEBUG OVERLAY (F3) over everything the hub draws
kfo_inv_draw();
kh_dbg_draw();
