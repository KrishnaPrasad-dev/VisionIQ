from scoring.score_smoother import apply_score_decay


ZONE_LEVEL_SCORE = {
    "low": 8,
    "medium": 16,
    "high": 26,
    "critical": 40,
}


def calculate_threat_score(
    people_count,
    zone_hits,
    loitering,
    rules,
    loitering_count=0,
    running_count=0,
    vandalism=False,
    vandalism_confidence=0.0,
    anomaly_score=0.0,
    baseline_ready=True,
    track_stability=1.0,
    avg_velocity=0.0,
):
    """
    Enhanced threat scoring with better accuracy
    
    Args:
        people_count: Number of people detected
        zone_hits: List of zone violations
        loitering: Boolean for loitering detection
        rules: Camera rules (maxPeople, restrictedAccess, etc)
        loitering_count: Number of loitering people
    """
    score = 0

    # Get mode (default to SHOP if not in rules)
    mode = rules.get("mode", "SHOP")
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
    mode_weights = MODE_WEIGHTS.get(mode, MODE_WEIGHTS["SHOP"])

    # ========================================
    # BASE SCORE: people presence
    person_weight = mode_weights.get("person", 3)
    score += people_count * person_weight

    # ========================================
    # CROWD DENSITY THREAT
    max_people = rules.get("maxPeopleAllowed", rules.get("maxPeople", 5))

    if people_count > max_people:
        overflow = people_count - max_people
        overflow_threat = min((overflow ** 1.35) * 18, 55)
        score += overflow_threat

    # Hard overcrowding escalation for high overflow ratio
    if max_people > 0 and people_count >= int(max_people * 1.7):
        score += 18

    # ========================================
    # RESTRICTED AREA VIOLATION
    restricted_zone = bool(rules.get("restrictedZoneMonitoring") or rules.get("restrictedAccess"))
    after_hours = bool(rules.get("afterHours"))

    if restricted_zone and people_count > 0:
        score += 60

    if after_hours and people_count > 0:
        score += 22

    # ========================================
    # ZONE-BASED THREATS
    zone_threat_total = 0
    for hit in zone_hits:
        threat_level = str(hit.get("threat", "low")).lower()
        zone_threat_total += ZONE_LEVEL_SCORE.get(threat_level, 8)

    score += min(zone_threat_total, 50)

    # ========================================
    # LOITERING DETECTION
    if loitering:
        loiter_weight = mode_weights.get("loitering", 8)
        loiter_score = loiter_weight * (1 + loitering_count * 0.5)
        score += min(loiter_score, 40)

    # RUNNING BEHAVIOR
    if running_count > 0:
        run_weight = mode_weights.get("running", 12)
        score += min(run_weight * running_count, 45)

    # Asset damage / vandalism behavior
    if vandalism:
        vandal_weight = mode_weights.get("abandoned", 25)
        score += vandal_weight + min(20, 25 * float(max(0.0, min(vandalism_confidence, 1.0))))

    # Fast global movement indicates panic-like behavior
    if avg_velocity >= 18:
        score += mode_weights.get("panic", 18)

    # Baseline anomaly contributes once profile is ready.
    if baseline_ready:
        score += min(24, max(0.0, anomaly_score) * 28)
    else:
        # During warm-up, avoid aggressive scores unless there are strong explicit signals.
        score *= 0.88
        strong_signals = (
            int(vandalism)
            + int(running_count > 0)
            + int(people_count > max_people)
            + int(len(zone_hits) > 0)
            + int(restricted_zone and people_count > 0)
            + int(after_hours and people_count > 0)
        )
        if strong_signals == 0:
            score *= 0.75

    # ========================================
    # THREAT LEVEL ESCALATION
    threat_indicators = sum([
        people_count > max_people,
        restricted_zone,
        after_hours,
        len(zone_hits) > 0,
        loitering,
        running_count > 0,
        vandalism,
    ])

    if threat_indicators >= 2:
        score += 12
    if threat_indicators >= 3:
        score += 10

    # ========================================
    # Lower confidence tracking slightly reduces raw score.
    confidence_factor = 0.85 + 0.15 * max(0.0, min(track_stability, 1.0))
    score *= confidence_factor

    # Penalize weak, low-stability single-person signals to cut false positives.
    if people_count <= 2 and track_stability < 0.35:
        score *= 0.75

    weak_signal_only = (
        people_count <= 1
        and len(zone_hits) == 0
        and not loitering
        and running_count == 0
        and not vandalism
    )
    if weak_signal_only:
        score *= 0.8

    score = min(max(score, 0), 100)
    return int(round(apply_score_decay(score)))


def get_status(score):
    """
    Enhanced status determination with better granularity
    """
    if score >= 75:
        return "CRITICAL"
    elif score >= 60:
        return "DANGER"
    elif score >= 40:
        return "WARNING"
    elif score >= 20:
        return "ALERT"
    else:
        return "SAFE"