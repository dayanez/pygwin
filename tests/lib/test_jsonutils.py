"""Testing pygwin json hooks"""

import json

import pytest

from pygwin.environ import EnvPath
from pygwin.lib.jsonutils import serialize_pygwin_json


@pytest.mark.parametrize(
    "inp",
    [
        42,
        "yo",
        ["hello"],
        {"x": 65},
        EnvPath(["wakka", "jawaka"]),
        ["y", EnvPath(["wakka", "jawaka"])],
        {"z": EnvPath(["wakka", "jawaka"])},
    ],
)
def test_serialize_pygwin_json_roundtrip(inp):
    s = json.dumps(inp, default=serialize_pygwin_json)
    obs = json.loads(s)
    assert inp == obs
