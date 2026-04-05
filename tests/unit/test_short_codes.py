from app.services.short_codes import CHARS, generate_short_code


def test_generate_short_code_uses_requested_length():
    code = generate_short_code(6)
    assert len(code) == 6


def test_generate_short_code_is_base62():
    code = generate_short_code(32)
    assert set(code) <= set(CHARS)
