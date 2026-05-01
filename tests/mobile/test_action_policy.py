from mobile.action_policy import evaluate_action_request


def base():
    return {"mode":"supervised_executor","session_permission":True,"ceo_delegation":True,"governance_approved":True,"kill_switch_active":True,"audit_log_enabled":True,"device_health_ok":True,"selector_validated":True,"min_action_confidence":0.9}


def test_block_cases_and_allow():
    c = base(); c["session_permission"] = False
    assert not evaluate_action_request({"confidence":1.0,"screen_type":"offer"}, c).allowed
    c = base(); c["kill_switch_active"] = False
    assert not evaluate_action_request({"confidence":1.0,"screen_type":"offer"}, c).allowed
    c = base()
    assert not evaluate_action_request({"confidence":0.5,"screen_type":"offer"}, c).allowed
    assert evaluate_action_request({"confidence":0.95,"screen_type":"offer"}, base()).allowed


def test_downgrade_on_drift():
    c = base(); c["selector_drift_detected"] = True
    d = evaluate_action_request({"confidence":0.95,"screen_type":"offer"}, c)
    assert d.downgrade_mode == "observer"
