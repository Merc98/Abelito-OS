from shared.agent_modes import (
    build_decepticon_engagement_package,
    get_mode,
    list_modes,
)


def test_list_modes_contains_decepticon_with_capabilities():
    by_name = {item["name"]: item for item in list_modes()}
    assert "default" in by_name
    assert "decepticon" in by_name
    assert "phase_based_execution" in by_name["decepticon"]["capabilities"]


def test_get_mode_errors_on_unknown():
    try:
        get_mode("unknown")
        assert False, "expected KeyError"
    except KeyError:
        assert True


def test_decepticon_engagement_package_shape():
    package = build_decepticon_engagement_package(
        objective="Validate segmentation",
        authorized_scope=["10.0.0.0/24"],
        constraints=["No DoS"],
    )
    assert package["roe"]["authorized_scope"] == ["10.0.0.0/24"]
    assert "kill_chain" in package["conops"]
    assert package["deconfliction"]["window_required"] is True
