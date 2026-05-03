import bootstrap


def test_check_port_returns_bool():
    out = bootstrap.check_port('127.0.0.1', 9)
    assert isinstance(out, bool)
