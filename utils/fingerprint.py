import hashlib
import json
from typing import Union


def generate_fingerprint(raw_payload: Union[dict, str]) -> str:
    """
    Generates a stable SHA-256 fingerprint for a device.

    - Accepts dict or string
    - Canonicalizes input
    - Returns hex digest (64 chars)

    This fingerprint is what gets stored and compared in DB.
    """

    if raw_payload is None:
        raise ValueError("FINGERPRINT_PAYLOAD_MISSING")

    # Normalize payload
    if isinstance(raw_payload, dict):
        normalized = json.dumps(
            raw_payload,
            sort_keys=True,
            separators=(",", ":"),
        )
    elif isinstance(raw_payload, str):
        normalized = raw_payload.strip()
    else:
        raise ValueError("INVALID_FINGERPRINT_PAYLOAD")

    if not normalized:
        raise ValueError("EMPTY_FINGERPRINT_PAYLOAD")

    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
