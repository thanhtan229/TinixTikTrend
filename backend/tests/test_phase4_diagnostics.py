import json
from fastapi.testclient import TestClient

from app.main import app
from app.api.diagnostics import get_system_diagnostics, run_deep_diagnostics
from app.services.backup_service import BackupService


def test_p4_ac_25_diagnostics_allowlist_and_sensitive_redaction():
    """
    P4-AC-25: Cheap diagnostics expose only the documented allowlist and do not
    return cookies, localStorage, raw session JSON, credentials, auth headers or
    arbitrary filesystem listings.
    - tiktok_session.status is strictly an enum (available/missing/invalid).
    """
    client = TestClient(app)
    resp = client.get("/api/diagnostics")
    assert resp.status_code == 200
    data = resp.json()

    # Structural allowlist checks
    assert "system" in data
    assert "database" in data
    assert "crawler" in data
    assert "scheduler" in data
    assert "tiktok_session" in data

    # Database section
    assert "size_bytes" in data["database"]
    assert "table_counts" in data["database"]
    assert "products" in data["database"]["table_counts"]

    # Verify cheap diagnostics does NOT run deep checks
    assert "integrity_check" not in data["database"]
    assert "foreign_key_check" not in data["database"]

    # Session redaction checks
    session_info = data["tiktok_session"]
    assert session_info["status"] in ("available", "missing", "invalid")
    assert session_info["redacted"] is True
    assert "cookie" not in session_info
    assert "session" not in session_info or isinstance(session_info.get("session"), str) is False

    # Deep scan the entire response text for sensitive leak patterns
    raw_text = resp.text.lower()
    forbidden_terms = [
        "sessionid",
        "sid_guard",
        "passport_csrf_token",
        "authorization",
        "bearer ",
        "password",
        "secret",
        "private_key",
    ]
    for term in forbidden_terms:
        assert term not in raw_text, f"Potential sensitive leak detected: '{term}' found in /api/diagnostics response"


def test_p4_ac_26_deep_diagnostics_explicit_verification():
    """
    P4-AC-26: `integrity_check` and `foreign_key_check` run only through the explicit
    deep-diagnostics action, not normal UI reads/modal opening.
    """
    client = TestClient(app)
    resp = client.get("/api/diagnostics/deep")
    assert resp.status_code == 200
    data = resp.json()

    assert "status" in data
    assert "integrity_check" in data
    assert "foreign_key_check" in data
    assert "checked_at" in data

    # On a healthy SQLite database, both checks pass cleanly
    assert data["status"] == "ok"
    assert data["integrity_check"] == "ok"
    assert data["foreign_key_check"] == "ok"

