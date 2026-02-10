from functools import wraps
from flask import request, jsonify

from services.license_service import verify_license_for_device


def license_device_required():
    """
    Global runtime enforcement decorator.

    RULES:
    - Runtime = VERIFY ONLY (NO device registration, NO activation)
    - Requires:
        - license_key
        - fingerprint
    - Source:
        - JSON body OR headers (X-License-Key, X-Device-Fingerprint)
    - On failure:
        - ALWAYS return 403
        - Unified error structure
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            data = request.get_json(silent=True) or {}

            license_key = (
                data.get("license_key")
                or request.headers.get("X-License-Key")
            )
            fingerprint = (
                data.get("fingerprint")
                or request.headers.get("X-Device-Fingerprint")
            )

            # Enforce strict presence + type
            if not isinstance(license_key, str) or not isinstance(fingerprint, str):
                return jsonify({
                    "status": "error",
                    "reason": "MISSING_LICENSE_OR_DEVICE",
                }), 403

            # Runtime verification (read-only)
            result = verify_license_for_device(
                license_key=license_key.strip(),
                fingerprint=fingerprint.strip(),
            )

            # Any runtime failure → FORBIDDEN
            if not result.get("allowed"):
                return jsonify({
                    "status": "error",
                    "reason": result.get("reason"),
                }), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator
