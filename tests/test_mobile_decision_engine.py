from abel_os.mobile.decision_engine import MobileDecisionEngine
from abel_os.schemas import DecisionOutcome, MobileMode, MobileOffer


def test_recommend_accept_in_recommend_only_mode() -> None:
    engine = MobileDecisionEngine()
    offer = MobileOffer(
        fare=12.0,
        pickup_eta_minutes=5,
        pickup_miles=1.0,
        trip_miles=4.0,
        source_confidence=0.9,
    )

    result = engine.evaluate(offer, mode=MobileMode.RECOMMEND_ONLY)

    assert result.decision == DecisionOutcome.RECOMMEND_ONLY
    assert result.recommended_action == "ACCEPT"
    assert result.execution_allowed is False


def test_reject_blocked_zone_in_auto_mode() -> None:
    engine = MobileDecisionEngine(blocked_zones={"zona roja"})
    offer = MobileOffer(
        fare=8.0,
        pickup_eta_minutes=4,
        pickup_miles=2.0,
        trip_miles=2.0,
        destination_zone="Zona Roja",
        source_confidence=0.9,
    )

    result = engine.evaluate(offer, mode=MobileMode.AUTO_DETERMINISTIC)

    assert result.decision == DecisionOutcome.REJECT
    assert result.execution_allowed is True


def test_escalate_when_accept_button_missing() -> None:
    engine = MobileDecisionEngine()
    offer = MobileOffer(
        fare=15.0,
        pickup_eta_minutes=3,
        pickup_miles=1.0,
        trip_miles=5.0,
        accept_button_visible=False,
    )

    result = engine.evaluate(offer, mode=MobileMode.AUTO_DETERMINISTIC)

    assert result.decision == DecisionOutcome.HUMAN
    assert result.recommended_action == "ESCALATE"
