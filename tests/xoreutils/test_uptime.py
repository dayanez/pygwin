import datetime

import pytest


@pytest.fixture
def uptime(xession, load_pgtrib):
    load_pgtrib("coreutils")
    return xession.aliases["uptime"]


def test_uptime(uptime):
    out = uptime([])
    delta = datetime.timedelta(seconds=float(out))
    # make sure that it returns a positive time lapse
    assert delta > datetime.timedelta(microseconds=1)
