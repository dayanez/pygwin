"""DEPRECATED: Use `pygwin.lib.lazyasd` instead of `pygwin.lazyasd`."""

import warnings

warnings.warn(
    "Use `pygwin.api.os` instead of `pygwin.lib.os`.", DeprecationWarning, stacklevel=2
)

from pygwin.api.os import *  # noqa
