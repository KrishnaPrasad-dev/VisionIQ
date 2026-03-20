class RulesEngine:
    def __init__(self, config):
        self.config = config

    def evaluate(self, data):

        events = []
        people_count = data["people_count"]

        max_people = self.config.get("maxPeople")

        if max_people and people_count > max_people:
            events.append({
                "type": "overcrowding",
                "count": people_count
            })

        if self.config.get("restrictedAccess"):
            if people_count > 0:
                events.append({
                    "type": "restricted_access"
                })

        return events