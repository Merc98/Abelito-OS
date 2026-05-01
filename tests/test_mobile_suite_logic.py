from suites.mobile.rideshare_accept_reject import decide_offer


def test_decide_offer_accept():
    src = 'Oferta $15 pickup 5 min 4 km'
    out = decide_offer(src)
    assert out['decision'] == 'ACCEPT'


def test_decide_offer_reject():
    src = 'Oferta $5 pickup 12 min 3 km'
    out = decide_offer(src)
    assert out['decision'] == 'REJECT'
