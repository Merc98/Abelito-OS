from mobile.offer_scorer import OfferScorer

RULES = {"mobile_offer_rules": {"min_fare":12.0,"min_fare_absolute":6.0,"min_pay_per_mile":2.5,"max_pickup_minutes":10}}


def test_accept_high_pay_per_mile():
    s = OfferScorer(RULES).score({"fare":20,"pickup_minutes":5,"trip_miles":6})
    assert s.recommendation == "ACCEPT"


def test_reject_low_fare_and_long_pickup():
    assert OfferScorer(RULES).score({"fare":5,"pickup_minutes":5,"trip_miles":2}).recommendation == "REJECT"
    assert OfferScorer(RULES).score({"fare":20,"pickup_minutes":12,"trip_miles":2}).recommendation == "REJECT"


def test_human_review_missing_data():
    assert OfferScorer(RULES).score({"fare":None,"pickup_minutes":1,"trip_miles":1}).recommendation == "HUMAN_REVIEW"
