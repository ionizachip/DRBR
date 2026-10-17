"""Exception types for the GML simulator."""


class GMError(Exception):
    """A runtime error that real GameMaker would report as a fatal error.

    Attributes: kind (short machine-readable tag), message, entry (code entry name),
    line (1-based line of the failing statement), stack (list of function names).
    """

    def __init__(self, message, kind="error"):
        super().__init__(message)
        self.message = message
        self.kind = kind
        self.entry = None
        self.line = None
        self.stack = []
        self.event = None     # "obj_name.Step_0" when raised inside an event
        self.frame = None     # sim frame number when raised from Sim.step

    def __str__(self):
        loc = ""
        if self.entry is not None or self.line is not None:
            loc = " [at %s line %s]" % (self.entry or "?", self.line if self.line is not None else "?")
        return self.message + loc


class GMParseError(GMError):
    def __init__(self, message, entry=None, line=None, col=None):
        super().__init__(message, "parse")
        self.entry = entry
        self.line = line
        self.col = col

    def __str__(self):
        return "%s:%s:%s: %s" % (self.entry or "<src>", self.line, self.col, self.message)


class GMThrow(GMError):
    """`throw expr;` carrying an arbitrary GML value."""

    def __init__(self, value, text=None):
        super().__init__(text if text is not None else "Unhandled exception: %r" % (value,), "throw")
        self.value = value


class SimCrash(Exception):
    """The simulated process died (fault injection / game_end during a write).
    Deliberately NOT a GMError so GML try/catch cannot swallow it."""


class SimGameEnd(Exception):
    """Raised out of Sim.step when game_end() was called and sim.raise_on_game_end is set."""
