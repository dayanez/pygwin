"""Custom tools for managing JSON serialization / deserialization of pygwin
objects.
"""

import functools

from pygwin.environ import EnvPath


@functools.singledispatch
def serialize_pygwin_json(val):
    """JSON serializer for pygwin custom data structures. This is only
    called when another normal JSON types are not found.
    """
    return str(val)


@serialize_pygwin_json.register(EnvPath)
def _serialize_pygwin_json_env_path(val):
    return val.paths
