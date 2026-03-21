import json
from datetime import datetime
from pathlib import Path


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
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.min_samples = int(min_samples)
        self._profiles = {}

    def _profile_path(self, camera_id):
        return self.storage_dir / f"{camera_id}.json"

    def _new_bucket(self):
        return {
            "samples": 0,
            "metrics": {
                key: {
                    "mean": 0.0,
                    "m2": 0.0,
                }
                for key in METRIC_KEYS
            },
        }

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
                "buckets": {str(h): self._new_bucket() for h in range(24)},
            }

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

    def _bucket(self, camera_id, hour):
        profile = self._load(camera_id)
        buckets = profile.setdefault("buckets", {})
        key = str(int(hour) % 24)
        if key not in buckets:
            buckets[key] = self._new_bucket()
        return buckets[key]

    def _std(self, n, m2):
        if n < 2:
            return 0.0
        return (m2 / (n - 1)) ** 0.5

    def update(self, camera_id, metrics, ts=None, allow_learning=True):
        if not allow_learning:
            return

        when = ts or datetime.now()
        bucket = self._bucket(camera_id, when.hour)
        bucket["samples"] += 1
        n = bucket["samples"]

        for key in METRIC_KEYS:
            value = float(metrics.get(key, 0.0))
            state = bucket["metrics"][key]
            mean = float(state["mean"])
            m2 = float(state["m2"])

            delta = value - mean
            mean = mean + delta / n
            delta2 = value - mean
            m2 = m2 + delta * delta2

            state["mean"] = mean
            state["m2"] = m2

        if n % 10 == 0:
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
        bucket = self._bucket(camera_id, when.hour)
        n = int(bucket.get("samples", 0))

        if n < self.min_samples:
            return {
                "anomaly_score": 0.0,
                "baseline_ready": False,
                "baseline_samples": n,
            }

        # Weighted z-score blend; clamped to 0..1
        weights = {
            "people_count": 0.30,
            "motion_ratio": 0.22,
            "avg_velocity": 0.20,
            "running_count": 0.15,
            "loitering_count": 0.13,
        }

        weighted = 0.0
        for key, w in weights.items():
            value = float(metrics.get(key, 0.0))
            state = bucket["metrics"][key]
            mean = float(state["mean"])
            std = max(self._std(n, float(state["m2"])), 1e-3)
            z = abs(value - mean) / std
            contribution = min(z / 3.0, 1.0)  # 3 sigma ~= high anomaly
            weighted += w * contribution

        return {
            "anomaly_score": float(min(max(weighted, 0.0), 1.0)),
            "baseline_ready": True,
            "baseline_samples": n,
        }


normal_behavior_model = NormalBehaviorModel()
