"""Imports every builtin library so DEFAULT_BUILTINS is populated."""
from . import lib_core, lib_engine, lib_input, lib_io, lib_mocks, lib_extra  # noqa: F401
from . import lib_net  # noqa: F401  (after lib_mocks: real buffers / sockets replace the recording stubs)
