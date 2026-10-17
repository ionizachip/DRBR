"""Keyboard / mouse / gamepad scripted-input mocks."""
from .registry import builtin, const
from .errors import GMError

VK = dict(vk_nokey=0, vk_anykey=1, vk_backspace=8, vk_tab=9, vk_enter=13, vk_return=13, vk_shift=16,
          vk_control=17, vk_alt=18, vk_pause=19, vk_escape=27, vk_space=32, vk_pageup=33, vk_pagedown=34,
          vk_end=35, vk_home=36, vk_left=37, vk_up=38, vk_right=39, vk_down=40, vk_printscreen=44,
          vk_insert=45, vk_delete=46, vk_lshift=160, vk_rshift=161, vk_lcontrol=162, vk_rcontrol=163,
          vk_lalt=164, vk_ralt=165, vk_numpad0=96, vk_numpad1=97, vk_numpad2=98, vk_numpad3=99,
          vk_numpad4=100, vk_numpad5=101, vk_numpad6=102, vk_numpad7=103, vk_numpad8=104, vk_numpad9=105,
          vk_multiply=106, vk_add=107, vk_subtract=109, vk_decimal=110, vk_divide=111,
          vk_f1=112, vk_f2=113, vk_f3=114, vk_f4=115, vk_f5=116, vk_f6=117, vk_f7=118, vk_f8=119,
          vk_f9=120, vk_f10=121, vk_f11=122, vk_f12=123)
const(**VK)
const(mb_left=1, mb_right=2, mb_middle=3, mb_any=-1, mb_none=0)
GP = dict(gp_face1=32769, gp_face2=32770, gp_face3=32771, gp_face4=32772, gp_shoulderl=32773, gp_shoulderr=32774,
          gp_shoulderlb=32775, gp_shoulderrb=32776, gp_select=32777, gp_start=32778, gp_stickl=32779,
          gp_stickr=32780, gp_padu=32781, gp_padd=32782, gp_padl=32783, gp_padr=32784,
          gp_axislh=32785, gp_axislv=32786, gp_axisrh=32787, gp_axisrv=32788)
const(**GP)


def key_code(k):
    if isinstance(k, str):
        if k.lower() in VK:
            return VK[k.lower()]
        if k.lower() in GP:
            return GP[k.lower()]
        if ("vk_" + k.lower()) in VK:
            return VK["vk_" + k.lower()]
        if len(k) == 1:
            return ord(k.upper())
        raise ValueError("unknown key %r" % k)
    return int(k)


def _num(k):
    try:
        return int(k)
    except (TypeError, ValueError):
        raise GMError("keyboard function expects a key code, got %r" % (k,), "type")


PAD0 = 32769   # gp_* codes: scripted like keys, read only by the gamepad functions (vk_anykey never sees them)


@builtin()
def keyboard_check_pressed(sim, k):
    i = sim.input
    k = _num(k)
    if k == 1:
        return i.any_pressed()
    return k < PAD0 and k in i.pressed and k not in i.cleared


@builtin()
def keyboard_check(sim, k):
    i = sim.input
    k = _num(k)
    if k == 1:
        return any(x < PAD0 for x in i.held - i.cleared)
    return k < PAD0 and k in i.held and k not in i.cleared


@builtin()
def keyboard_check_direct(sim, k):
    return keyboard_check(sim, k)


@builtin()
def keyboard_check_released(sim, k):
    return _num(k) in sim.input.released


@builtin()
def keyboard_clear(sim, k):
    sim.input.cleared.add(_num(k))
    return 0


@builtin()
def io_clear(sim):
    sim.input.cleared |= set(sim.input.pressed | sim.input.held)
    return 0


@builtin()
def keyboard_key_press(sim, k):
    sim.input.pressed.add(_num(k)); sim.input.held.add(_num(k)); return 0


@builtin()
def keyboard_key_release(sim, k):
    sim.input.held.discard(_num(k)); return 0


@builtin("keyboard_set_map", "keyboard_unset_map", "keyboard_virtual_show", "keyboard_virtual_hide")
def _kb_noop(sim, *a):
    return 0


@builtin()
def mouse_check_button(sim, b):
    return False


@builtin()
def mouse_check_button_pressed(sim, b):
    return False


@builtin()
def mouse_check_button_released(sim, b):
    return False


@builtin()
def mouse_clear(sim, b):
    return 0


# a scripted controller: gp_* codes pressed / held with sim.press / sim.hold (or put in sim.input.pressed / held) count as
# the buttons of any connected pad; gamepad_is_connected is true once a test sets sim.input.pad = True
@builtin()
def gamepad_is_connected(sim, dev):
    return bool(getattr(sim.input, 'pad', False))


@builtin()
def gamepad_button_check(sim, dev, b):
    b = _num(b)
    return b >= PAD0 and b in sim.input.held and b not in sim.input.cleared


@builtin()
def gamepad_button_check_pressed(sim, dev, b):
    b = _num(b)
    return b >= PAD0 and b in sim.input.pressed and b not in sim.input.cleared


@builtin()
def gamepad_button_check_released(sim, dev, b):
    b = _num(b)
    return b >= PAD0 and b in sim.input.released


@builtin("gamepad_axis_value", "gamepad_get_device_count", "gamepad_button_value")
def _gp_zero(sim, *a):
    return 0


@builtin("gamepad_get_description")
def _gp_desc(sim, *a):
    return ""


@builtin()
def mouse_wheel_up(sim):
    return bool(getattr(sim.input, 'wheel_up', 0))


@builtin()
def mouse_wheel_down(sim):
    return bool(getattr(sim.input, 'wheel_down', 0))
