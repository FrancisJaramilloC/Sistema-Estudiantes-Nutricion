from datetime import datetime, timezone, timedelta

from app.database import get_dynamodb_resource
from app.session_analysis import group_sessions, analyze_session


class TestSessionAnalysis:
    def _make_reading(self, bpm, minutes_ago=0):
        ts = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
        return {
            "device_id": "test-device",
            "bpm": bpm,
            "timestamp": ts.isoformat(),
            "student_id": "test-student",
            "reading_id": f"r-{minutes_ago}",
        }

    def test_group_sessions_single_group(self):
        readings = [self._make_reading(70, i) for i in range(30, 0, -1)]
        groups = group_sessions(readings)
        assert len(groups) == 1
        assert len(groups[0]) == 30

    def test_group_sessions_split_by_gap(self):
        r1 = self._make_reading(70, 15)
        r2 = self._make_reading(75, 13)
        r3 = self._make_reading(80, 3)
        r4 = self._make_reading(82, 2)
        r5 = self._make_reading(78, 1)
        readings = [r1, r2, r3, r4, r5]
        groups = group_sessions(readings)
        assert len(groups) == 2
        assert len(groups[0]) == 2
        assert len(groups[1]) == 3

    def test_group_sessions_empty(self):
        assert group_sessions([]) == []

    def test_analyze_session_basic(self):
        readings = [self._make_reading(75, i) for i in range(10, 0, -1)]
        analysis = analyze_session(readings)
        assert analysis["avg_bpm"] == 75.0
        assert analysis["min_bpm"] == 75
        assert analysis["max_bpm"] == 75
        assert analysis["reading_count"] == 10
        assert analysis["classification"] == "normal"

    def test_analyze_session_with_tachycardia(self):
        readings = [self._make_reading(110, i) for i in range(5, 0, -1)]
        analysis = analyze_session(readings)
        assert analysis["avg_bpm"] > 100
        assert len(analysis["tachycardia_episodes"]) >= 1
        assert analysis["classification"] == "atencion"

    def test_analyze_session_with_bradycardia(self):
        readings = [self._make_reading(50, i) for i in range(5, 0, -1)]
        analysis = analyze_session(readings)
        assert analysis["avg_bpm"] < 60
        assert len(analysis["bradycardia_episodes"]) >= 1
        assert analysis["classification"] == "atencion"

    def test_analyze_session_arrhythmia_detection(self):
        readings = [
            self._make_reading(70, 5),
            self._make_reading(72, 4),
            self._make_reading(110, 3),
            self._make_reading(75, 2),
            self._make_reading(70, 1),
        ]
        analysis = analyze_session(readings)
        assert len(analysis["arrhythmia_events"]) >= 1

    def test_analyze_session_zone_distribution(self):
        readings = [
            self._make_reading(50, 5),
            self._make_reading(75, 4),
            self._make_reading(110, 3),
            self._make_reading(80, 2),
            self._make_reading(120, 1),
        ]
        analysis = analyze_session(readings)
        zones = analysis["zone_distribution_pct"]
        assert "bajo" in zones
        assert "normal" in zones
        assert "elevado" in zones
        total = zones["bajo"] + zones["normal"] + zones["elevado"]
        assert abs(total - 100) < 0.2

    def test_critical_classification(self):
        readings = [self._make_reading(110, i) for i in range(10, 0, -1)]
        # Add arrhythmias
        for i in range(5):
            readings.append(self._make_reading(70 if i % 2 == 0 else 140, i))
        analysis = analyze_session(readings)
        assert analysis["classification"] in ("atencion", "critico")

    def test_empty_readings(self):
        assert analyze_session([]) == {}

    def test_avg_bpm_rounding(self):
        readings = [self._make_reading(73, 2), self._make_reading(74, 1)]
        analysis = analyze_session(readings)
        assert analysis["avg_bpm"] == 73.5
