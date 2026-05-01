import pytest
from mobile.kill_switch import KillSwitch


def test_kill_switch_flow():
    ks = KillSwitch("s1")
    ks.enable()
    assert ks.is_active()
    ks.trigger()
    assert not ks.is_active()
    with pytest.raises(RuntimeError):
        ks.require_active_or_raise()
