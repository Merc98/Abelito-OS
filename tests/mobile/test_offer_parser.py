from mobile.screen_parser import ScreenParser


def test_parse_fields_from_ui_tree():
    p = ScreenParser()
    r = p.parse("$18.50 7.2 miles pickup 5 min")
    assert r["fields"]["fare"] == 18.50
    assert r["fields"]["trip_miles"] == 7.2
    assert r["fields"]["pickup_minutes"] == 5


def test_missing_fields_and_ocr_fallback():
    p = ScreenParser()
    r = p.parse("", ocr_text="$9.00 3 miles 4 min")
    assert r["source"] == "ocr"
    assert r["fields"]["fare"] == 9.0


def test_malformed_ui_tree():
    p = ScreenParser()
    r = p.parse("<xml broken")
    assert r["screen_type"] in ("unknown", "offer")
