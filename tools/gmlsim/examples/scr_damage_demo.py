"""Run the real DELTARUNE scr_damage (decompiled) against mocked globals -- no game needed.

    python3 examples/scr_damage_demo.py [path/to/CodeEntries]

Shows: loading real scripts lazily across files (scr_damage -> scr_damage_cache -> scr_damage_calculation ->
scr_element_damage_reduction ...), mocking an engine-level script (instance_create), and faithful errors when
a global the real game would have initialised is missing.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from gmlsim import Sim, GMError  # noqa: E402

DEFAULT_DIR = "/home/claude/work/gml/base/CodeEntries"


def make_sim(code_dir):
    sim = Sim(seed=1)
    # scripts only: object events (hundreds of Create events needing the whole game) are not loaded, but the
    # object *names* are still defined so `obj_knight_enemy` etc. resolve.
    sim.load_dir(code_dir, kinds=("scripts",))
    sim.mock("instance_create", lambda s, x, y, obj: s.create_instance(obj, x, y).id)
    heroes = [sim.create("obj_hero_dummy" if "obj_hero_dummy" in sim.objects else _def(sim, "obj_hero_dummy"),
                         100 + i * 50, 200, myheight=40) for i in range(3)]
    sim.define_globals(inv=-1, invc=1, chapter=1, char=[1, 2, 3], hp=[0, 90, 110, 70], maxhp=[0, 90, 110, 70],
                       battledf=[0, 2, 1, 0], charaction=[0, 0, 0, 0], chararmor1=[0, 0, 0, 0],
                       chararmor2=[0, 0, 0, 0], charinstance=heroes)
    return sim


def _def(sim, name):
    sim.define_object(name)
    return name


def main(code_dir):
    sim = make_sim(code_dir)
    enemy = sim.create(_def(sim, "obj_battle_dummy"), target=0, damage=40)

    # 1. trivial: invulnerable (global.inv >= 0) -> nothing happens
    sim.globals["inv"] = 5
    sim.call("scr_damage", self_obj=enemy)
    print("inv=5  -> hp unchanged:", sim.py(sim.globals["hp"]))

    # 2. real path: party member 1 (target 0) takes 40 damage through the real scripts
    sim.globals["inv"] = -1
    sim.call("scr_damage", self_obj=enemy)
    print("inv=-1 -> hp:", sim.py(sim.globals["hp"]), " tdamage:", sim.get(enemy, "tdamage"),
          " new inv timer:", sim.globals["inv"])

    # 3. faithful error when the harness is missing state the game would have had
    del sim.globals["battledf"]
    sim.globals["inv"] = -1
    try:
        sim.call("scr_damage", self_obj=enemy)
    except GMError as e:
        print("missing global ->", e.message, "| stack:", e.stack, "| at", e.entry, "line", e.line)
    return sim


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DIR)
