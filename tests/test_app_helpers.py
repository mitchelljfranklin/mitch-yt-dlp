from app import App


def test_format_speed():
    assert App._format_speed(None) == ""
    assert App._format_speed(0) == ""
    assert App._format_speed(999) == "999 B/s"
    assert App._format_speed(1_200) == "1 KB/s"
    assert App._format_speed(2_500_000) == "2.5 MB/s"


def test_format_eta():
    assert App._format_eta(None) == ""
    assert App._format_eta(0) == ""
    assert App._format_eta(-5) == ""
    assert App._format_eta(65) == "- ETA 1:05"
    assert App._format_eta(3661) == "- ETA 61:01"
