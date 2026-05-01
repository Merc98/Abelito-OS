from mobile.mobile_agent import MobileScreenAgentService


def test_contract_no_tap_and_ceo_flow_surrogate():
    svc = MobileScreenAgentService(rules={"mobile_offer_rules": {"min_fare":12.0,"min_fare_absolute":6.0,"min_pay_per_mile":2.5,"max_pickup_minutes":10}})
    sid = svc.start_mobile_session("d1", "android", mode="recommend_only")
    parsed = svc.parse_current_offer(sid, "$18 6 miles 4 min")
    rec = svc.recommend_action(sid, parsed)
    assert rec["action"].startswith("RECOMMEND_")
