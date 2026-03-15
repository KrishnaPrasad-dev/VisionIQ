import time


class DwellTracker:
    """
    Tracks how long a person stays inside a zone.
    Used for loitering detection.
    """

    def __init__(self, threshold_seconds=30):
        self.threshold = threshold_seconds
        self.entry_times = {}
        self.loitering = {}

    def update(self, track_ids, zone_name, in_zone_flags):

        alerts = []
        now = time.time()

        for track_id, in_zone in zip(track_ids, in_zone_flags):

            key = (int(track_id), zone_name)

            if in_zone:

                if key not in self.entry_times:
                    self.entry_times[key] = now

                dwell_time = now - self.entry_times[key]

                if dwell_time >= self.threshold:
                    alerts.append((int(track_id), zone_name, round(dwell_time)))
                    self.loitering[int(track_id)] = zone_name

            else:

                if key in self.entry_times:
                    del self.entry_times[key]

                if int(track_id) in self.loitering:
                    del self.loitering[int(track_id)]

        return alerts

    def is_loitering(self, track_id):
        return int(track_id) in self.loitering


# global instance used by pipeline
dwell_tracker = DwellTracker()