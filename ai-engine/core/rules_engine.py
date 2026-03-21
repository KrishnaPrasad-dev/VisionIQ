class RulesEngine:
    def __init__(self, config):
        self.config = config

    def evaluate(self, data):

        events = []
        people_count = data["people_count"]

        max_people = self.config.get("maxPeople")

        if max_people and people_count > max_people:
            overflow = people_count - max_people
            severity = "high" if overflow >= max(2, int(max_people * 0.3)) else "medium"
            events.append({
                "type": "overcrowding",
                "count": people_count,
                "severity": severity,
            })

            if max_people > 0 and people_count >= int(max_people * 1.7):
                events.append({
                    "type": "critical_overcrowding",
                    "count": people_count,
                    "severity": "critical",
                })

        if self.config.get("restrictedAccess"):
            if people_count > 0:
                events.append({
                    "type": "restricted_access",
                    "severity": "critical",
                })

        if data.get("loitering"):
            events.append({
                "type": "loitering",
                "count": len(data.get("loitering_ids", [])),
                "severity": "medium",
            })

        if data.get("running"):
            events.append({
                "type": "running",
                "count": len(data.get("running_ids", [])),
                "severity": "high",
            })

        if data.get("table_breakage"):
            events.append({
                "type": "asset_damage",
                "severity": "critical",
                "confidence": round(float(data.get("table_breakage_confidence", 0.0)), 2),
            })

        if data.get("status") == "CRITICAL":
            events.append({
                "type": "critical_threat",
                "severity": "critical",
                "score": data.get("score", 0),
            })

        return events