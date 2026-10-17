"""Recording mocks for graphics / audio / surface / window / layer ... APIs.

Every call is appended to sim.log as Call(frame, name, args); inspect with sim.calls('draw_text').
"""
from .registry import DEFAULT_BUILTINS, gvar
from .values import GMArray

_RECORDING = {}


def _make(name, ret):
    from .sim_log import record

    def fn(sim, *args):
        record(sim, name, args)
        return ret(sim, args) if callable(ret) else ret
    return fn


def rec(names, ret=0):
    for n in names.split():
        DEFAULT_BUILTINS[n] = (_make(n, ret), False)
        _RECORDING[n] = ret


# ---- drawing (return 0)
rec("""draw_sprite draw_sprite_ext draw_sprite_part draw_sprite_part_ext draw_sprite_stretched
draw_sprite_stretched_ext draw_sprite_pos draw_sprite_tiled draw_sprite_tiled_ext draw_sprite_general draw_self
draw_text draw_text_ext draw_text_transformed draw_text_color draw_text_colour draw_text_ext_color
draw_text_ext_transformed draw_text_transformed_color draw_text_ext_transformed_color
draw_rectangle draw_rectangle_color draw_rectangle_colour draw_roundrect draw_line draw_line_width
draw_line_color draw_line_width_color draw_circle draw_circle_color draw_ellipse draw_triangle
draw_triangle_color draw_point draw_arrow draw_healthbar draw_clear draw_clear_alpha draw_surface
draw_surface_ext draw_surface_part draw_surface_part_ext draw_surface_stretched draw_primitive_begin
draw_primitive_end draw_primitive_begin_texture draw_vertex draw_vertex_color draw_vertex_texture
draw_vertex_texture_color draw_set_font draw_set_halign draw_set_valign draw_set_circle_precision
draw_enable_alphablend draw_set_color draw_set_colour draw_set_alpha""")
rec("""gpu_set_blendmode gpu_set_blendmode_ext gpu_set_blendmode_ext_sepalpha gpu_set_blendenable
gpu_set_alphatestenable gpu_set_alphatestref gpu_set_colorwriteenable gpu_set_fog gpu_set_texfilter
gpu_set_texrepeat gpu_set_ztestenable gpu_set_zwriteenable gpu_set_cullmode gpu_set_texfilter_ext
shader_set shader_reset shader_set_uniform_f shader_set_uniform_i shader_set_uniform_f_array
shader_set_uniform_matrix texture_set_stage texture_set_interpolation
surface_set_target surface_reset_target surface_copy surface_copy_part surface_resize surface_free_dummy
surface_save
view_set_wport view_set_hport view_set_xport view_set_yport view_set_surface_id view_set_visible
view_set_camera view_set_wport camera_set_view_pos camera_set_view_size camera_set_view_mat
camera_set_proj_mat camera_apply camera_destroy
window_set_size window_set_caption window_set_fullscreen window_set_cursor window_set_position
window_center window_set_min_width window_set_min_height window_enable_borderless_fullscreen
window_set_showborder window_mouse_set display_set_gui_size display_set_gui_maximise
display_reset display_set_timing_method application_surface_enable application_surface_draw_enable
display_set_ui_visibility
layer_set_visible layer_depth layer_x layer_y layer_hspeed layer_vspeed layer_destroy layer_background_destroy
layer_background_htiled layer_background_vtiled layer_background_stretch layer_background_blend
layer_background_alpha layer_background_speed layer_background_visible layer_background_index
layer_sprite_destroy layer_sprite_x layer_sprite_y layer_sprite_alpha layer_sprite_blend layer_set_target_room
audio_stop_sound audio_stop_all audio_pause_sound audio_pause_all audio_resume_sound audio_resume_all
audio_sound_gain audio_sound_pitch audio_sound_set_track_position audio_set_master_gain audio_group_set_gain
audio_group_load audio_group_stop_all audio_stop_sync_group audio_listener_position audio_emitter_position
audio_emitter_gain audio_emitter_pitch audio_emitter_free audio_falloff_set_model
mp_grid_clear_cell mp_grid_add_cell mp_grid_add_rectangle mp_grid_clear_all mp_grid_destroy mp_grid_draw
path_start path_end path_delete path_add_point path_set_closed path_set_kind path_set_precision path_clear_points
path_speed_dummy move_towards_point move_snap move_bounce_solid motion_set motion_add
sprite_delete sprite_set_offset sprite_set_alpha_from_sprite sprite_save
font_enable_effects font_delete
instance_deactivate_dummy
buffer_delete buffer_seek buffer_write buffer_async_group_option buffer_async_group_begin
buffer_async_group_end buffer_async_group_enable
vertex_begin vertex_end vertex_position vertex_position_3d vertex_colour vertex_color vertex_texcoord
vertex_normal vertex_submit vertex_delete_buffer vertex_format_begin vertex_format_add_position
vertex_format_add_colour vertex_format_add_texcoord vertex_format_add_normal vertex_freeze
audio_group_set_gain_dummy
gamepad_set_vibration gamepad_set_axis_deadzone gamepad_set_color gamepad_set_colour
event_show_debug_message_dummy
trigger_event_dummy
switch_controller_support_show
network_dummy
steam_dummy
""")
rec("surface_exists_dummy", False)

# ---- queries with fixed defaults
rec("""place_meeting position_meeting place_free place_empty position_empty point_in_circle instance_place_dummy
mp_grid_path path_exists layer_exists layer_background_exists is_animated_dummy
audio_is_playing audio_is_paused sprite_exists_dummy keyboard_virtual_status""", False)
# (the collision_* functions answer an instance or noone, as instance_place does: a loop "until (c < 0)" ends on noone - it
# would never end on false, 0)
rec("""instance_place instance_position instance_nearest instance_furthest collision_rectangle_list_dummy
instance_find_dummy collision_rectangle collision_circle collision_line collision_point collision_ellipse""", -4)
rec("""distance_to_object distance_to_point""", 1000000)
rec("collision_rectangle_list collision_circle_list collision_point_list collision_line_list instance_place_list", 0)
rec("""path_get_x path_get_y path_get_length path_get_number path_get_point_x path_get_point_y
window_get_width window_get_height window_get_x window_get_y display_get_width display_get_height
display_get_gui_width display_get_gui_height display_get_dpi_x window_get_fullscreen window_has_focus
audio_sound_get_gain audio_sound_get_pitch audio_sound_get_track_position audio_sound_length audio_get_master_gain
camera_get_view_x camera_get_view_y camera_get_view_width camera_get_view_height camera_get_view_angle
view_get_camera view_get_wport view_get_hport view_get_xport view_get_yport view_get_surface_id view_get_visible
layer_get_x layer_get_y layer_get_depth layer_get_hspeed layer_get_vspeed layer_get_visible layer_get_id
layer_get_all layer_get_all_elements layer_get_element_type layer_get_name layer_background_get_id
layer_background_get_blend layer_background_get_alpha layer_background_get_sprite layer_sprite_get_sprite
layer_sprite_get_x layer_sprite_get_y layer_get_id_at_depth layer_create layer_background_create
layer_sprite_create layer_get_target_room
camera_create_view camera_create
shader_get_uniform shader_get_sampler_index shader_is_compiled
texture_get_texel_width texture_get_texel_height surface_get_texture sprite_get_texture sprite_get_uvs
sprite_get_bbox_left sprite_get_bbox_top sprite_get_bbox_right sprite_get_bbox_bottom sprite_get_speed
sprite_get_xoffset sprite_get_yoffset sprite_get_number font_get_size audio_get_type
gamepad_get_guid gamepad_get_device_count application_get_position
vertex_create_buffer vertex_format_end buffer_create buffer_read buffer_get_size buffer_peek
os_get_info_dummy
get_open_filename get_save_filename""", 0)
rec("get_string", "")
rec("get_integer get_integer_async get_string_async show_question show_message_async", 0)
rec("show_message", 0)
rec("""get_open_filename_ext""", "")
rec("audio_get_name sprite_get_name font_get_name layer_get_name_dummy path_get_name script_get_name room_get_name_dummy", "")

# ---- stateful draw state
_DRAW_DEFAULTS = {"color": 16777215, "alpha": 1, "font": -1, "halign": 0, "valign": 0}


def _draw_state(sim):
    return sim.sys_state.setdefault("draw", dict(_DRAW_DEFAULTS))


def _mk_setter(name, key):
    from .sim_log import record

    def fn(sim, v, *a):
        record(sim, name, (v,) + a)
        _draw_state(sim)[key] = v
        return 0
    return fn


def _mk_getter(name, key):
    def fn(sim):
        return _draw_state(sim)[key]
    return fn


for _n, _k in (("draw_set_color", "color"), ("draw_set_colour", "color"), ("draw_set_alpha", "alpha"),
               ("draw_set_font", "font"), ("draw_set_halign", "halign"), ("draw_set_valign", "valign")):
    DEFAULT_BUILTINS[_n] = (_mk_setter(_n, _k), False)
for _n, _k in (("draw_get_color", "color"), ("draw_get_colour", "color"), ("draw_get_alpha", "alpha"),
               ("draw_get_font", "font"), ("draw_get_halign", "halign"), ("draw_get_valign", "valign")):
    DEFAULT_BUILTINS[_n] = (_mk_getter(_n, _k), False)

# ---- text metrics (crude, deterministic): 8px per char, 16px per line
def _lines(s):
    return str(s).split("\n")


DEFAULT_BUILTINS["string_width"] = (lambda sim, s: 8 * max(len(l) for l in _lines(s)), False)
DEFAULT_BUILTINS["string_height"] = (lambda sim, s: 16 * len(_lines(s)), False)
DEFAULT_BUILTINS["string_width_ext"] = (lambda sim, s, sep, w: 8 * max(len(l) for l in _lines(s)), False)
DEFAULT_BUILTINS["string_height_ext"] = (lambda sim, s, sep, w: 16 * len(_lines(s)), False)

# ---- sprites: sizes configurable via sim.sys_state['sprite_sizes'] = {idx: (w, h)}
def _spr_dim(i, sim):
    return sim.sys_state.get("sprite_sizes", {}).get(i, (16, 16))


def _rec_fn(name, fn):
    from .sim_log import record

    def w(sim, *a):
        record(sim, name, a)
        return fn(sim, *a)
    DEFAULT_BUILTINS[name] = (w, False)


_rec_fn("sprite_get_width", lambda sim, i: _spr_dim(i, sim)[0])
_rec_fn("sprite_get_height", lambda sim, i: _spr_dim(i, sim)[1])
_rec_fn("sprite_exists", lambda sim, i: i in sim.assets.values() or i in sim.sys_state.get("sprite_sizes", {}))
_rec_fn("font_exists", lambda sim, i: True)
_rec_fn("sprite_create_from_surface", lambda sim, *a: sim.define_asset("__spr_%d" % sim.next_asset))
_rec_fn("sprite_duplicate", lambda sim, *a: sim.define_asset("__spr_%d" % sim.next_asset))
_rec_fn("font_add_sprite_ext", lambda sim, *a: sim.define_asset("__fnt_%d" % sim.next_asset))

# ---- surfaces
def _surf_create(sim, w, h, *a):
    i = sim.next_surface
    sim.next_surface += 1
    sim.surfaces[i] = (int(w), int(h))
    return i


_rec_fn("surface_create", _surf_create)
_rec_fn("surface_exists", lambda sim, i: i.__class__ in (int, float) and int(i) in sim.surfaces)
_rec_fn("surface_free", lambda sim, i: sim.surfaces.pop(int(i), None) and 0)
_rec_fn("surface_get_width", lambda sim, i: sim.surfaces.get(int(i), (0, 0))[0])
_rec_fn("surface_get_height", lambda sim, i: sim.surfaces.get(int(i), (0, 0))[1])

# ---- audio
def _audio_play(sim, snd, *a):
    sim.audio_next += 1
    return sim.audio_next


_rec_fn("audio_play_sound", _audio_play)
_rec_fn("audio_play_sound_at", _audio_play)
_rec_fn("audio_exists", lambda sim, i: True)


# ---- misc
@__import__("gmlsim.registry", fromlist=["builtin"]).builtin("trigger_event")
def trigger_event(sim, *a):
    from .sim_log import record
    record(sim, "trigger_event", a)
    return 0


gvar("gamepad_dummy", 0)

# DRBR: the window title (drbr53.gml names the window)
rec("window_get_caption", "")
