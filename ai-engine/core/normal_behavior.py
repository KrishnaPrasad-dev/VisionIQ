import json
from datetime import datetime
from pathlib import Path
import os


AI_ENGINE_ROOT = Path(__file__).resolve().parent.parent


METRIC_KEYS = [
    "people_count",
    "motion_ratio",
    "avg_velocity",
    "running_count",
    "loitering_count",
]


class NormalBehaviorModel:
    """Learns time-bucketed normal behavior and outputs anomaly score."""

    def __init__(self, storage_dir="alerts/baseline_profiles", min_samples=60):
        self.storage_dir = (AI_ENGINE_ROOT / storage_dir).resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.min_samples = int(os.getenv("QUANTUMEYE_BASELINE_MIN_SAMPLES", str(min_samples)))
        self.min_hour_samples = int(os.getenv("QUANTUMEYE_BASELINE_MIN_HOUR_SAMPLES", "18"))
        self.min_segment_hour_samples = int(os.getenv("QUANTUMEYE_BASELINE_MIN_SEGMENT_HOUR_SAMPLES", "14"))
        self.min_week_hour_samples = int(os.getenv("QUANTUMEYE_BASELINE_MIN_WEEK_HOUR_SAMPLES", "10"))
        self.min_week_segment_hour_samples = int(os.getenv("QUANTUMEYE_BASELINE_MIN_WEEK_SEGMENT_HOUR_SAMPLES", "7"))
        self.min_ready_total_samples = int(os.getenv("QUANTUMEYE_BASELINE_MIN_READY_TOTAL", "120"))
        self.day_start_hour = int(os.getenv("QUANTUMEYE_DAY_START_HOUR", "6")) % 24
        self.day_end_hour = int(os.getenv("QUANTUMEYE_DAY_END_HOUR", "18")) % 24
        self.night_start_hour = int(os.getenv("QUANTUMEYE_NIGHT_START_HOUR", "20")) % 24
        self.night_end_hour = int(os.getenv("QUANTUMEYE_NIGHT_END_HOUR", "5")) % 24
        self._profiles = {}

    def _profile_path(self, camera_id):
        return self.storage_dir / f"{camera_id}.json"

    def _new_bucket(self):
        return {
            "samples": 0,
            "last_update": None,
            "metrics": {
                key: {
                    "mean": 0.0,
                    "m2": 0.0,
                }
                for key in METRIC_KEYS
            },
        }

    def _new_hours_map(self):
        return {str(h): self._new_bucket() for h in range(24)}

    def _new_weekday_hours_map(self):
        return {str(d): self._new_hours_map() for d in range(7)}

    def _in_hour_range(self, hour, start, end):
        """Check if hour is in [start, end) with midnight wrap support."""
        if start == end:
            return True
        if start < end:
            return start <= hour < end
        return hour >= start or hour < end

    def _segment_for_time(self, when):
        hour = int(when.hour) % 24
        if self._in_hour_range(hour, self.day_start_hour, self.day_end_hour):
            return "day"
        if self._in_hour_range(hour, self.night_start_hour, self.night_end_hour):
            return "night"
        return "twilight"

    def _load(self, camera_id):
        if camera_id in self._profiles:
            return self._profiles[camera_id]

        path = self._profile_path(camera_id)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = None
        else:
            data = None

        if not data:
            data = {
                "camera_id": camera_id,
                "updated_at": datetime.utcnow().isoformat(),
                "created_at": datetime.utcnow().isoformat(),
                "total_samples": 0,
                "days_seen": [],
                "hour_buckets": self._new_hours_map(),
                "weekday_hour_buckets": self._new_weekday_hours_map(),
                "segment_hour_buckets": {
                    "day": self._new_hours_map(),
                    "night": self._new_hours_map(),
                    "twilight": self._new_hours_map(),
                },
                "weekday_segment_hour_buckets": {
                    "day": self._new_weekday_hours_map(),
                    "night": self._new_weekday_hours_map(),
                    "twilight": self._new_weekday_hours_map(),
                },
            }

        # Backward-compatible migration from legacy "buckets" schema.
        if "hour_buckets" not in data:
            legacy = data.get("buckets", {})
            data["hour_buckets"] = {str(h): legacy.get(str(h), self._new_bucket()) for h in range(24)}
        if "weekday_hour_buckets" not in data:
            data["weekday_hour_buckets"] = self._new_weekday_hours_map()
        if "segment_hour_buckets" not in data:
            data["segment_hour_buckets"] = {
                "day": self._new_hours_map(),
                "night": self._new_hours_map(),
                "twilight": self._new_hours_map(),
            }
        if "weekday_segment_hour_buckets" not in data:
            data["weekday_segment_hour_buckets"] = {
                "day": self._new_weekday_hours_map(),
                "night": self._new_weekday_hours_map(),
                "twilight": self._new_weekday_hours_map(),
            }
        data.setdefault("total_samples", 0)
        data.setdefault("days_seen", [])

        self._profiles[camera_id] = data
        return data

    def _save(self, camera_id):
        profile = self._profiles.get(camera_id)
        if not profile:
            return
        profile["updated_at"] = datetime.utcnow().isoformat()
        path = self._profile_path(camera_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)

    def _hour_bucket(self, camera_id, hour):
        profile = self._load(camera_id)
        buckets = profile.setdefault("hour_buckets", {})
        key = str(int(hour) % 24)
        if key not in buckets:
            buckets[key] = self._new_bucket()
        return buckets[key]

    def _weekday_hour_bucket(self, camera_id, weekday, hour):
        profile = self._load(camera_id)
        weekday_buckets = profile.setdefault("weekday_hour_buckets", {})
        wd_key = str(int(weekday) % 7)
        if wd_key not in weekday_buckets:
            weekday_buckets[wd_key] = {str(h): self._new_bucket() for h in range(24)}
        hour_map = weekday_buckets[wd_key]
        hr_key = str(int(hour) % 24)
        if hr_key not in hour_map:
            hour_map[hr_key] = self._new_bucket()
        return hour_map[hr_key]

    def _segment_hour_bucket(self, camera_id, segment, hour):
        profile = self._load(camera_id)
        segment_buckets = profile.setdefault("segment_hour_buckets", {})
        segment = str(segment)
        if segment not in segment_buckets:
            segment_buckets[segment] = self._new_hours_map()
        hour_map = segment_buckets[segment]
        hr_key = str(int(hour) % 24)
        if hr_key not in hour_map:
            hour_map[hr_key] = self._new_bucket()
        return hour_map[hr_key]

    def _weekday_segment_hour_bucket(self, camera_id, segment, weekday, hour):
        profile = self._load(camera_id)
        ws_buckets = profile.setdefault("weekday_segment_hour_buckets", {})
        segment = str(segment)
        if segment not in ws_buckets:
            ws_buckets[segment] = self._new_weekday_hours_map()

        weekday_map = ws_buckets[segment]
        wd_key = str(int(weekday) % 7)
        if wd_key not in weekday_map:
            weekday_map[wd_key] = self._new_hours_map()

        hour_map = weekday_map[wd_key]
        hr_key = str(int(hour) % 24)
        if hr_key not in hour_map:
            hour_map[hr_key] = self._new_bucket()
        return hour_map[hr_key]

    def _std(self, n, m2):
        if n < 2:
            return 0.0
        return (m2 / (n - 1)) ** 0.5

    def _update_bucket(self, bucket, metrics, when):
        bucket["samples"] = int(bucket.get("samples", 0)) + 1
        bucket["last_update"] = when.isoformat()
        n = int(bucket["samples"])

        metric_map = bucket.setdefault("metrics", {})
        for key in METRIC_KEYS:
            value = float(metrics.get(key, 0.0))
            state = metric_map.setdefault(key, {"mean": 0.0, "m2": 0.0})
            mean = float(state.get("mean", 0.0))
            m2 = float(state.get("m2", 0.0))

            delta = value - mean
            mean = mean + delta / n
            delta2 = value - mean
            m2 = m2 + delta * delta2

            state["mean"] = mean
            state["m2"] = m2

    def _score_bucket(self, bucket, metrics):
        n = int(bucket.get("samples", 0))
        if n < 2:
            return None

        weights = {
            "people_count": 0.31,
            "motion_ratio": 0.22,
            "avg_velocity": 0.20,
            "running_count": 0.15,
            "loitering_count": 0.12,
        }
        std_floor = {
            "people_count": 0.6,
            "motion_ratio": 0.01,
            "avg_velocity": 0.45,
            "running_count": 0.35,
            "loitering_count": 0.35,
        }

        weighted = 0.0
        for key, w in weights.items():
            value = float(metrics.get(key, 0.0))
            state = bucket.get("metrics", {}).get(key, {"mean": 0.0, "m2": 0.0})
            mean = float(state.get("mean", 0.0))
            std_raw = self._std(n, float(state.get("m2", 0.0)))

            # Keep sigma realistic so tiny variance does not explode anomaly.
            std = max(std_raw, std_floor.get(key, 1e-3), abs(mean) * 0.12)
            z = abs(value - mean) / std
            contribution = min(z / 3.0, 1.0)
            weighted += w * contribution

        return float(min(max(weighted, 0.0), 1.0))

    def update(self, camera_id, metrics, ts=None, allow_learning=True):
        if not allow_learning:
            return

        when = ts or datetime.now()
        segment = self._segment_for_time(when)
        profile = self._load(camera_id)
        profile["total_samples"] = int(profile.get("total_samples", 0)) + 1

        day_key = when.date().isoformat()
        days_seen = profile.setdefault("days_seen", [])
        if day_key not in days_seen:
            days_seen.append(day_key)
            if len(days_seen) > 30:
                del days_seen[:-30]

        hour_bucket = self._hour_bucket(camera_id, when.hour)
        week_hour_bucket = self._weekday_hour_bucket(camera_id, when.weekday(), when.hour)
        segment_hour_bucket = self._segment_hour_bucket(camera_id, segment, when.hour)
        week_segment_hour_bucket = self._weekday_segment_hour_bucket(
            camera_id,
            segment,
            when.weekday(),
            when.hour,
        )
        self._update_bucket(hour_bucket, metrics, when)
        self._update_bucket(week_hour_bucket, metrics, when)
        self._update_bucket(segment_hour_bucket, metrics, when)
        self._update_bucket(week_segment_hour_bucket, metrics, when)

        if int(profile.get("total_samples", 0)) % 10 == 0:
            self._save(camera_id)

    def flush(self, camera_id=None):
        """Persist profile(s) to disk immediately."""
        if camera_id is not None:
            if camera_id in self._profiles:
                self._save(camera_id)
            return

        for cid in list(self._profiles.keys()):
            self._save(cid)

    def score(self, camera_id, metrics, ts=None):
        when = ts or datetime.now()
        segment = self._segment_for_time(when)
        profile = self._load(camera_id)
        total_samples = int(profile.get("total_samples", 0))
        hour_bucket = self._hour_bucket(camera_id, when.hour)
        week_hour_bucket = self._weekday_hour_bucket(camera_id, when.weekday(), when.hour)
        segment_hour_bucket = self._segment_hour_bucket(camera_id, segment, when.hour)
        week_segment_hour_bucket = self._weekday_segment_hour_bucket(
            camera_id,
            segment,
            when.weekday(),
            when.hour,
        )

        n_hour = int(hour_bucket.get("samples", 0))
        n_week_hour = int(week_hour_bucket.get("samples", 0))
        n_segment_hour = int(segment_hour_bucket.get("samples", 0))
        n_week_segment_hour = int(week_segment_hour_bucket.get("samples", 0))

        if total_samples < self.min_samples:
            return {
                "anomaly_score": 0.0,
                "baseline_ready": False,
                "baseline_samples": total_samples,
            }

        hour_score = self._score_bucket(hour_bucket, metrics)
        week_hour_score = self._score_bucket(week_hour_bucket, metrics)
        segment_hour_score = self._score_bucket(segment_hour_bucket, metrics)
        week_segment_hour_score = self._score_bucket(week_segment_hour_bucket, metrics)

        candidates = []
        if week_segment_hour_score is not None and n_week_segment_hour >= self.min_week_segment_hour_samples:
            candidates.append(("week_segment_hour", week_segment_hour_score, min(1.0, n_week_segment_hour / 45.0)))
        if week_hour_score is not None and n_week_hour >= self.min_week_hour_samples:
            candidates.append(("week_hour", week_hour_score, min(1.0, n_week_hour / 80.0)))
        if segment_hour_score is not None and n_segment_hour >= self.min_segment_hour_samples:
            candidates.append(("segment_hour", segment_hour_score, min(1.0, n_segment_hour / 90.0)))
        if hour_score is not None and n_hour >= self.min_hour_samples:
            candidates.append(("hour", hour_score, min(1.0, n_hour / 120.0)))

        if not candidates:
            return {
                "anomaly_score": 0.0,
                "baseline_ready": total_samples >= self.min_ready_total_samples,
                "baseline_samples": total_samples,
                "baseline_segment": segment,
            }

        specificity = {
            "week_segment_hour": 1.35,
            "week_hour": 1.18,
            "segment_hour": 1.08,
            "hour": 1.0,
        }

        weighted_sum = 0.0
        total_weight = 0.0
        for name, score, conf in candidates:
            w = conf * specificity.get(name, 1.0)
            weighted_sum += score * w
            total_weight += w

        anomaly = weighted_sum / max(total_weight, 1e-6)

        return {
            "anomaly_score": float(min(max(anomaly, 0.0), 1.0)),
            "baseline_ready": total_samples >= self.min_ready_total_samples,
            "baseline_samples": total_samples,
            "baseline_segment": segment,
        }


normal_behavior_model = NormalBehaviorModel()
