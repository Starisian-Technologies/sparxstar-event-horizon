"""
SPARXSTAR Event Horizon - Attack Simulation Tests
Tests use Python requests + pytest.
A `ConnectionError` on a blocked endpoint is a PASS (return 444 ghosts the connection).
A 200/404 on a blocked endpoint is a FAIL.
"""
import pytest
import requests
from requests.exceptions import ConnectionError

BASE_URL = "http://localhost"


def test_homepage_load():
    """Ensure the site loads normally for legitimate traffic."""
    try:
        r = requests.get(BASE_URL, timeout=2)
        assert r.status_code in [200, 404]  # 404 is fine if no index.html exists
    except ConnectionError:
        pytest.fail("Normal traffic was blocked — firewall is too aggressive!")


def test_honey_pot():
    """Ensure the bot trap /spx-trap ghosts the connection (return 444)."""
    with pytest.raises(ConnectionError):
        requests.get(f"{BASE_URL}/spx-trap", timeout=2)


def test_sql_injection_block():
    """Ensure SQL Injection query strings are ghosted (return 444)."""
    with pytest.raises(ConnectionError):
        requests.get(f"{BASE_URL}/?id=1' UNION SELECT user,password", timeout=2)


def test_bad_bot_block():
    """Ensure known bad User-Agents are ghosted (return 444)."""
    headers = {"User-Agent": "masscan"}
    with pytest.raises(ConnectionError):
        requests.get(BASE_URL, headers=headers, timeout=2)


def test_sensitive_file_block():
    """Ensure requests for wp-config.php are ghosted (return 444)."""
    with pytest.raises(ConnectionError):
        requests.get(f"{BASE_URL}/wp-config.php", timeout=2)


def test_env_file_block():
    """Ensure requests for .env files are ghosted (return 444)."""
    with pytest.raises(ConnectionError):
        requests.get(f"{BASE_URL}/.env", timeout=2)


def test_emergency_bypass():
    """Ensure the X-SPX-Bypass header overrides the firewall for admins."""
    headers = {"X-SPX-Bypass": "true"}
    try:
        r = requests.get(
            f"{BASE_URL}/?id=1' UNION SELECT user,password",
            headers=headers,
            timeout=2,
        )
        assert r.status_code in [200, 404]
    except ConnectionError:
        pytest.fail("Emergency Bypass failed — malicious payload was still blocked.")


def test_static_asset_bypass():
    """Ensure static images bypass the firewall and are served (not ghosted)."""
    try:
        r = requests.get(f"{BASE_URL}/logo.png", timeout=2)
        assert r.status_code != 444
    except ConnectionError:
        pytest.fail("Static asset connection was dropped — should be allowed.")
