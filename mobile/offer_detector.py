def is_offer_screen(parsed: dict) -> bool:
    return parsed.get("screen_type") == "offer"
