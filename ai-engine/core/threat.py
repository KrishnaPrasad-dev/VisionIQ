def calculate_threat_score(people_count, zone_hits, loitering, rules):

    score = 0

    # -------------------------------
    # CROWD DENSITY
    # -------------------------------
    max_people = rules.get("maxPeople", 5)

    if people_count > max_people:
        overflow = people_count - max_people
        score += min(overflow * 10, 40)

    # -------------------------------
    # RESTRICTED ACCESS
    # -------------------------------
    if rules.get("restrictedAccess"):
        if people_count > 0:
            score += 50

    # -------------------------------
    # ZONES
    # -------------------------------
    for hit in zone_hits:
        score += hit.get("threat", 1) * 10

    # -------------------------------
    # LOITERING
    # -------------------------------
    if loitering:
        score += 20

    return min(score, 100)


def get_status(score):

    if score >= 70:
        return "DANGER"
    elif score >= 30:
        return "WARNING"
    else:
        return "SAFE"