// build 50: the players' sent attacks (the Knights' real attack objects) - their timelines and cleanup
kbr_sa_frame();
knight_run_tick();
knight_backspace_check();

knight_kspell_tick();
// build 50: the fight song's lyrics (Flower Man, Raise Up Your Bat)
knight_lyr_step();
// build 50: the custom characters in a fight (Flowery: his turn-long effects; their heroes keep their look)
knight_cc_tick();
knight_mus_tick();
// build 43: Knight Fights Online (messages, timers, the host's room); build 45: a game started from a Steam invite joins it
kfo_launch_check();
kfo_tick();
// build 47: the online room's overworld (the party asleep, the wall before the original encounter); every frame, so leaving
// a room always wakes the party
kfo_world_room_tick();
// build 48: the room's chat (T / ENTER in a match opens it)
kfo_chat_tick();
// build 49: F3 - the DEBUG OVERLAY (and its log)
kh_dbg_tick();
