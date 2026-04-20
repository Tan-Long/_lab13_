from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_phone_vn() -> None:
    out = scrub_text("Call me at 0901234567")
    assert "0901234567" not in out
    assert "REDACTED_PHONE_VN" in out


def test_scrub_cccd() -> None:
    out = scrub_text("My CCCD is 036202001680")
    assert "036202001680" not in out
    assert "REDACTED_CCCD" in out


def test_scrub_passport() -> None:
    out = scrub_text("Passport: B1234567")
    assert "B1234567" not in out
    assert "REDACTED_PASSPORT" in out


def test_scrub_credit_card() -> None:
    out = scrub_text("Card: 4111 1111 1111 1111")
    assert "4111" not in out
    assert "REDACTED_CREDIT_CARD" in out


def test_no_false_positive() -> None:
    clean = "This is a normal message about observability and logging."
    assert scrub_text(clean) == clean
