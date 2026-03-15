ZONE_THREAT_SCORES = {
    "low": 10,
    "medium": 20,
    "high": 35,
    "critical": 50
}

def calculate_threat_score(
    person_count,
    zone_results,
    loitering_count,
    motion
):

    score = 0

    # People should not be dangerous by default
    score += person_count * 5

    zone_hits = 0

    for zone_name, triggered, threat_level in zone_results:

        if triggered:
            score += ZONE_THREAT_SCORES.get(threat_level, 20)
            zone_hits += 1

    # Loitering
    score += loitering_count * 10

    # Motion behaviour
    if motion.get("running"):
        score += 15

    if motion.get("panic"):
        score += 20

    if motion.get("abandoned"):
        score += 25

    return min(score, 100)