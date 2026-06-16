import hashlib
import hmac
import json

from app.core.security import sign_webhook_payload


def test_webhook_hmac_signature():
    secret = "test-secret"
    body = json.dumps({"event": "test"}).encode()
    timestamp = "1234567890"
    sig = sign_webhook_payload(secret, timestamp, body)
    expected = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    assert sig == expected
