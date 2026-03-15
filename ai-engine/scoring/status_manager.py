import time

_last_status = "SAFE"
_hold_until = 0
HOLD_SECONDS = 3


def get_status(score):

    global _last_status, _hold_until

    now = time.time()

    if score >= 55:
        new_status = "CRITICAL"
    elif score >= 25:
        new_status = "SUSPICIOUS"
    else:
        new_status = "SAFE"

    severity = {
        "SAFE": 0,
        "SUSPICIOUS": 1,
        "CRITICAL": 2
    }

    # prevent status flickering
    if severity[new_status] < severity[_last_status]:
        if now < _hold_until:
            return _last_status

    if new_status != _last_status:
        _hold_until = now + HOLD_SECONDS

    _last_status = new_status

    return new_status