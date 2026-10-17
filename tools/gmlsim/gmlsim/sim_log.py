from collections import namedtuple

Call = namedtuple("Call", "frame name args")


def record(sim, name, args):
    if sim.record_calls:
        sim.log.append(Call(sim.frame_no, name, args))
