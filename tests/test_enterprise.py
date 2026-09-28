from app.security import validate_external_url


def test_public_url_is_accepted():
    assert validate_external_url("https://example.com/video") == "https://example.com/video"


def test_localhost_is_rejected():
    try:
        validate_external_url("http://127.0.0.1:8080/x")
    except ValueError:
        return
    raise AssertionError("private URL must be rejected")
