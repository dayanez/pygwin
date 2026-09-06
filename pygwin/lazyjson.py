"""DEPRECATED: Use `pygwin.lib.lazyjson` instead of `pygwin.lazyjson`."""

import warnings

warnings.warn(
    "Use `pygwin.lib.lazyjson` instead of `pygwin.lazyjson`.",
    DeprecationWarning,
    stacklevel=2,
)

from pygwin.lib.lazyjson import *  # noqa
