"""Tests for the tiny DoS protection helper."""

from streamlit_extension.utils.dos_protection import DoSProtectionSystem


def test_attack_detection():
    dos = DoSProtectionSystem(threshold=3, window=60)
    ip = "1.2.3.4"
    assert dos.record_request(ip)
    assert dos.record_request(ip)
    assert dos.record_request(ip)
    assert not dos.record_request(ip)
    assert dos.detect_attack(ip)