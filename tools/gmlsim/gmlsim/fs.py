"""Sandboxed real-file layer with write-fault injection."""
import os
import shutil

from .errors import GMError, SimCrash


class Fault:
    """Write faults. Pass one to sim.fs.inject(fault, match=None, once=True).

    Every file write the sim performs (ini_close, file_text_close, file_copy, ...) goes through FS.write(),
    which consults the armed fault.  A fault maps (path, bytes) -> bytes actually written (or raises).
    """

    def __init__(self, fn, desc):
        self.fn = fn
        self.desc = desc

    def __repr__(self):
        return "<Fault %s>" % self.desc

    @staticmethod
    def truncate(n):
        """Silently write only the first n bytes (e.g. disk full)."""
        return Fault(lambda path, data: data[:n], "truncate(%d)" % n)

    @staticmethod
    def interrupt(n=0):
        """Write the first n bytes, then the process dies (SimCrash raised, nothing after runs)."""
        def fn(path, data):
            raise _Partial(data[:n])
        return Fault(fn, "interrupt(%d)" % n)

    @staticmethod
    def zero():
        """File ends up empty."""
        return Fault(lambda path, data: b"", "zero")

    @staticmethod
    def corrupt(seed=1, nbytes=4):
        """Flip nbytes pseudo-random bytes."""
        import random

        def fn(path, data):
            r = random.Random(seed)
            b = bytearray(data)
            for _ in range(min(nbytes, len(b))):
                b[r.randrange(len(b))] ^= 0xFF
            return bytes(b)
        return Fault(fn, "corrupt(seed=%d)" % seed)

    @staticmethod
    def garbage(payload=b"\x00\xff\x00garbage"):
        return Fault(lambda path, data: payload, "garbage")

    @staticmethod
    def fail():
        """The open/write fails before touching the file (IOError -> GMError); old content survives."""
        def fn(path, data):
            raise IOError("injected write failure")
        return Fault(fn, "fail")

    @staticmethod
    def custom(fn, desc="custom"):
        return Fault(fn, desc)


class _Partial(Exception):
    def __init__(self, data):
        self.data = data


class FS:
    def __init__(self, root):
        self.root = os.path.realpath(root)
        self.faults = []        # [(fault, match_fn, once)]
        self.write_log = []     # (relpath, nbytes_written, fault_desc|None)
        # DRBR: GameMaker's read-only BUNDLE (the folder of data.win - "Included Files"). A relative name is looked for in
        # the save area first, then here; every write, delete and rename stays in the save area. None = no bundle.
        self.bundle = None

    def bundle_path(self, name):
        if not self.bundle:
            return None
        n = name.replace("\\", "/").lstrip("/")
        b = os.path.realpath(self.bundle)
        full = os.path.realpath(os.path.join(b, n))
        if full != b and not full.startswith(b + os.sep):
            raise GMError("sandbox escape refused: %r" % name, "sandbox")
        return full

    # ---- paths
    def path(self, name):
        if not isinstance(name, str):
            raise GMError("file name must be a string", "type")
        n = name.replace("\\", "/")
        if n.startswith(self.root):
            n = n[len(self.root):]
        n = n.lstrip("/")
        full = os.path.realpath(os.path.join(self.root, n))
        if full != self.root and not full.startswith(self.root + os.sep):
            raise GMError("sandbox escape refused: %r" % name, "sandbox")
        return full

    def rel(self, full):
        return os.path.relpath(full, self.root)

    # ---- faults
    def inject(self, fault, match=None, once=True):
        """Arm a fault for the next write (match: substring of relpath or callable(relpath)->bool)."""
        if isinstance(match, str):
            sub = match
            match = lambda rel, sub=sub: sub in rel
        self.faults.append([fault, match, once])

    def clear_faults(self):
        self.faults.clear()

    # ---- operations
    def exists(self, name):
        if os.path.isfile(self.path(name)):
            return True
        bp = self.bundle_path(name)
        return bool(bp) and os.path.isfile(bp)

    def read(self, name):
        full = self.path(name)
        if not os.path.isfile(full):
            bp = self.bundle_path(name)
            if bp and os.path.isfile(bp):
                full = bp
        with open(full, "rb") as fh:
            return fh.read()

    def write(self, name, data):
        """Write bytes, honoring injected faults. May raise SimCrash (interrupt) or GMError."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        full = self.path(name)
        rel = self.rel(full)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        fault = None
        for item in self.faults:
            fl, match, once = item
            if match is None or match(rel):
                fault = fl
                if once:
                    self.faults.remove(item)
                break
        if fault is None:
            out = data
        else:
            try:
                out = fault.fn(full, data)
            except _Partial as p:
                with open(full, "wb") as fh:
                    fh.write(p.data)
                self.write_log.append((rel, len(p.data), fault.desc))
                raise SimCrash("process killed mid-write of %s after %d/%d bytes" % (rel, len(p.data), len(data)))
            except IOError as e:
                self.write_log.append((rel, 0, fault.desc))
                raise GMError("file write failed: %s (%s)" % (rel, e), "io")
        with open(full, "wb") as fh:
            fh.write(out)
        self.write_log.append((rel, len(out), fault.desc if fault else None))

    def delete(self, name):
        try:
            os.remove(self.path(name))
            return True
        except OSError:
            return False

    def copy(self, src, dst):
        self.write(dst, self.read(src))

    def rename(self, src, dst):
        os.replace(self.path(src), self.path(dst))

    # ---- snapshot support
    def dump(self):
        out = {}
        for dp, _, fns in os.walk(self.root):
            for fn in fns:
                full = os.path.join(dp, fn)
                with open(full, "rb") as fh:
                    out[os.path.relpath(full, self.root)] = fh.read()
        return out

    def load(self, files):
        for dp, dns, fns in os.walk(self.root, topdown=False):
            for fn in fns:
                os.remove(os.path.join(dp, fn))
            for dn in dns:
                try:
                    os.rmdir(os.path.join(dp, dn))
                except OSError:
                    pass
        for rel, data in files.items():
            full = os.path.join(self.root, rel)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "wb") as fh:
                fh.write(data)
