"""DEPRECATED: Use `pygwin.lib.lazyasd` instead of `pygwin.lazyasd`."""

import warnings

warnings.warn(
    "Use `pygwin.api.subprocess` instead of `pygwin.lib.subprocess`.",
    DeprecationWarning,
    stacklevel=2,
)

from pygwin.api.subprocess import *  # noqa
