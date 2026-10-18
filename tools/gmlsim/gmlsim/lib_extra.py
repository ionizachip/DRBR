"""Less common builtins: ds_priority, string_split, more recording stubs (video, layers, platform SDKs)."""
from . import ops
from .errors import GMError
from .lib_mocks import rec
from .registry import builtin
from .rt import share
from .values import GMArray, from_py


def _prio(sim, i):
    q = sim.sys_state.setdefault("ds_priority", {})
    try:
        return q[int(i)]
    except (KeyError, TypeError, ValueError):
        raise GMError("Data structure with index %s does not exist (ds_priority)" % (i,), "ds")


@builtin()
def ds_priority_create(sim):
    q = sim.sys_state.setdefault("ds_priority", {})
    i = sim.next_ds
    sim.next_ds += 1
    q[i] = []
    return i


@builtin()
def ds_priority_destroy(sim, i):
    _prio(sim, i)
    del sim.sys_state["ds_priority"][int(i)]
    return 0


@builtin()
def ds_priority_add(sim, i, v, p):
    _prio(sim, i).append([p, share(v)])
    return 0


@builtin()
def ds_priority_clear(sim, i):
    _prio(sim, i).clear()
    return 0


@builtin()
def ds_priority_size(sim, i):
    return len(_prio(sim, i))


@builtin()
def ds_priority_empty(sim, i):
    return not _prio(sim, i)


@builtin()
def ds_priority_delete_min(sim, i):
    q = _prio(sim, i)
    if not q:
        return None
    k = min(range(len(q)), key=lambda j: q[j][0])
    return q.pop(k)[1]


@builtin()
def ds_priority_delete_max(sim, i):
    q = _prio(sim, i)
    if not q:
        return None
    k = max(range(len(q)), key=lambda j: q[j][0])
    return q.pop(k)[1]


@builtin()
def ds_priority_find_min(sim, i):
    q = _prio(sim, i)
    return min(q, key=lambda e: e[0])[1] if q else None


@builtin()
def ds_priority_find_max(sim, i):
    q = _prio(sim, i)
    return max(q, key=lambda e: e[0])[1] if q else None


@builtin()
def ds_map_keys_to_array(sim, m, arr=None):
    keys = list(sim.ds_map(m).keys())
    if arr is not None:
        arr.data[:] = keys
        return len(keys)
    return GMArray(keys)


@builtin()
def ds_map_values_to_array(sim, m, arr=None):
    vals = [share(v) for v in sim.ds_map(m).values()]
    if arr is not None:
        arr.data[:] = vals
        return len(vals)
    return GMArray(vals)


@builtin("string_split", "gml_std_string_split")
def string_split(sim, s, delim, remove_empty=False, max_splits=None):
    if s.__class__ is not str or delim.__class__ is not str:
        raise GMError("string_split(): arguments must be strings", "type")
    parts = s.split(delim) if max_splits is None else s.split(delim, int(max_splits))
    if ops.truth(remove_empty):
        parts = [p for p in parts if p != ""]
    return GMArray(parts)


@builtin()
def string_byte_length(sim, s):
    return len(s.encode("utf-8"))


@builtin()
def randomise(sim):
    sim.rng.seed(sim.rng.random())
    return 0


@builtin()
def point_distance_3d(sim, x1, y1, z1, x2, y2, z2):
    import math
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)


@builtin()
def parameter_count(sim):
    return 0


@builtin()
def parameter_string(sim, i):
    return ""


@builtin()
def object_get_sprite(sim, i):
    n = sim.obj_by_index.get(int(i))
    return sim.objects[n].sprite if n else -1


@builtin()
def object_set_persistent(sim, i, flag):
    n = sim.obj_by_index.get(int(i))
    if n is None:
        raise GMError("object_set_persistent(): unknown object %r" % (i,), "no_object")
    sim.objects[n].persistent = ops.truth(flag)
    return 0


@builtin()
def instance_id_get(sim, i):
    return -4


for _a, _b in (("circle", "circle_color"), ("ellipse", "ellipse_color"), ("line", "line_color")):
    pass

rec("""draw_circle_colour draw_ellipse_color draw_ellipse_colour draw_line_colour draw_line_width_colour
draw_point_color draw_point_colour draw_roundrect_color draw_roundrect_colour draw_roundrect_ext
draw_roundrect_color_ext draw_roundrect_colour_ext draw_triangle_colour draw_surface_general draw_path
draw_tilemap draw_handler draw_rectangle_colour_dummy
set_screen_color set_screen_con set_screen_image_index set_screen_sprite set_screen_offset set_screen_timer
set_screen
video_set_volume video_close video_draw video_pause video_resume video_enable_loop video_open
gif_add_surface gif_save
screen_save screen_save_part
layer_background_get_index layer_background_get_htiled layer_background_get_vtiled layer_background_get_xscale
layer_background_get_yscale layer_background_xscale layer_background_yscale layer_background_get_stretch
layer_background_change layer_background_sprite layer_sprite_get_xscale layer_sprite_get_yscale
layer_sprite_get_speed layer_sprite_get_index layer_tile_x layer_tile_y layer_tile_get_x layer_tile_get_y
layer_tile_alpha layer_tilemap_get_id layer_force_draw_depth layer_script_begin layer_script_end
camera_set_view_border camera_get_view_border_x camera_get_view_border_y camera_set_view_speed
camera_get_view_speed_x camera_get_view_speed_y camera_set_view_angle camera_set_view_target
camera_get_view_target
gpu_get_blendmode texture_prefetch texture_is_ready texturegroup_get_textures
sprite_prefetch sprite_set_bbox sprite_add surface_getpixel surface_get_target
audio_emitter_exists audio_emitter_create audio_group_is_loaded audio_play_sound_on audio_create_stream
audio_destroy_stream
mp_grid_create path_add os_is_paused gamepad_test_mapping
video_get_format video_get_status video_get_duration video_get_position
buffer_load buffer_load_async buffer_save_async ds_list_read ds_list_write ds_map_set_post
ini_open_from_string vertex_format_add_position_3d
switch_controller_support_get_selected_id switch_controller_support_set_defaults
switch_controller_support_set_singleplayer_only switch_controller_set_supported_styles
switch_controller_support_show switch_accounts_select_account switch_accounts_open_user
switch_accounts_is_user_open switch_save_data_commit switch_save_data_mount
switch_language_get_desired_language
psn_load_modules psn_init_np_libs psn_init_trophy psn_get_trophy_unlock_state psn_unlock_trophy
psn_post_uds_event psn_tick
json_encode json_decode
""", 0)


# ------------------------------------------------------------------ base64 (GameMaker: UTF-8 text <-> base64 text)
@builtin()
def base64_encode(sim, s):
    import base64 as _b64
    from .values import gml_str
    return _b64.b64encode(gml_str(s).encode('utf-8')).decode('ascii')


@builtin()
def base64_decode(sim, s):
    import base64 as _b64
    from .values import gml_str
    t = gml_str(s).strip()
    t = t + '=' * (-len(t) % 4)
    try:
        return _b64.b64decode(t.encode('ascii'), validate=False).decode('utf-8', errors='replace')
    except Exception:
        # GameMaker decodes what it can and never throws: an empty string for garbage
        return ''


# ------------------------------------------------------------------ the clipboard (one text, per emulated game)
@builtin()
def clipboard_set_text(sim, s):
    from .values import gml_str
    sim.clipboard = gml_str(s)
    return 0


@builtin()
def clipboard_get_text(sim):
    return getattr(sim, 'clipboard', '')


@builtin()
def clipboard_has_text(sim):
    return bool(getattr(sim, 'clipboard', ''))


# DRBR 1.0.3: the GPU state queries as the runner answers them with nothing set: no shader (-1), fog off
@builtin()
def shader_current(sim):
    return -1


@builtin()
def gpu_get_fog(sim):
    return GMArray([False, 0, 0, 1])
