"""DEPRECATED: Use `pygwin.lib.lazyasd` instead of `pygwin.lazyasd`."""

import warnings

warnings.warn(
    "Use `pygwin.lib.lazyasd` instead of `pygwin.lazyasd`.",
    DeprecationWarning,
    stacklevel=2,
)

from pygwin.lib.lazyasd import *  # noqa
