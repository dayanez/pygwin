import platform

import pytest


@pytest.fixture
def uname(xession, load_pgtrib):
    load_pgtrib("coreutils")
    return xession.aliases["uname"]


def test_uname_without_args(uname):
    out = uname(["-a"])

    assert out.startswith(platform.uname().system)
