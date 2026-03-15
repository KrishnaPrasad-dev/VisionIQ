import config.config as config


ZONE_THREAT_SCORES = {
    "low": 10,
    "medium": 20,
    "high": 35,
    "critical": 50
}


MODE_WEIGHTS = {

    "SHOP": {
        "person": 3,
        "loitering": 8,
        "running": 12,
        "panic": 18,
        "abandoned": 25
    },

    "OFFICE": {
        "person": 6,
        "loitering": 15,
        "running": 18,
        "panic": 22,
        "abandoned": 25
    },

    "WAREHOUSE": {
        "person": 10,
        "loitering": 10,
        "running": 20,
        "panic": 25,
        "abandoned": 30
    }
}


def calculate_threat_score(
    person_count,
    zone_results,
    loitering_count,
    motion
):

    mode = config.mode
    weights = MODE_WEIGHTS.get(mode, MODE_WEIGHTS["SHOP"])

    score = 0

    # people presence
    score += person_count * weights["person"]

    # zone intrusion
    for zone_name, triggered, threat_level in zone_results:

        if triggered:
            score += ZONE_THREAT_SCORES.get(threat_level, 20)

    # loitering
    score += loitering_count * weights["loitering"]

    # motion behaviour
    if motion.get("running"):
        score += weights["running"]

    if motion.get("panic"):
        score += weights["panic"]

    if motion.get("abandoned"):
        score += weights["abandoned"]

    return min(score, 100)