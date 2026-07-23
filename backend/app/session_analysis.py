import statistics
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

SESSION_GAP_MINUTES = 5
BRADY_THRESHOLD = 60
TACHY_THRESHOLD = 100
ARRHYTHMIA_BPM_DELTA = 30
CONSECUTIVE_FOR_EPISODE = 3


def group_sessions(readings: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    if not readings:
        return []

    sorted_r = sorted(readings, key=lambda r: r.get("timestamp", ""))
    sessions = []
    current = [sorted_r[0]]

    for r in sorted_r[1:]:
        prev_ts = _parse_ts(current[-1].get("timestamp", ""))
        curr_ts = _parse_ts(r.get("timestamp", ""))
        if prev_ts and curr_ts and (curr_ts - prev_ts) > timedelta(minutes=SESSION_GAP_MINUTES):
            sessions.append(current)
            current = [r]
        else:
            current.append(r)

    if current:
        sessions.append(current)

    return sessions


def analyze_session(readings: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not readings:
        return {}

    timestamps = [_parse_ts(r.get("timestamp", "")) for r in readings]
    timestamps = [ts for ts in timestamps if ts is not None]
    bpms = [r["bpm"] for r in readings if "bpm" in r]

    if not bpms:
        return {}

    start_time = timestamps[0]
    end_time = timestamps[-1]
    duration_seconds = (end_time - start_time).total_seconds() if end_time > start_time else 0

    avg_bpm = round(statistics.mean(bpms), 1)
    min_bpm = min(bpms)
    max_bpm = max(bpms)
    std_dev = round(statistics.stdev(bpms), 1) if len(bpms) > 1 else 0.0

    total = len(bpms)
    bajo_count = sum(1 for b in bpms if b < BRADY_THRESHOLD)
    normal_count = sum(1 for b in bpms if BRADY_THRESHOLD <= b <= TACHY_THRESHOLD)
    elevado_count = sum(1 for b in bpms if b > TACHY_THRESHOLD)

    zone_pct = {
        "bajo": round(bajo_count / total * 100, 1) if total else 0,
        "normal": round(normal_count / total * 100, 1) if total else 0,
        "elevado": round(elevado_count / total * 100, 1) if total else 0,
    }

    arrhythmia_events = _detect_arrhythmias(bpms)
    brady_episodes = _detect_episodes(bpms, BRADY_THRESHOLD, "bradicardia")
    tachy_episodes = _detect_episodes(bpms, TACHY_THRESHOLD, "taquicardia", above=True)

    classification = _classify_session(arrhythmia_events, brady_episodes, tachy_episodes, avg_bpm)

    return {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": int(duration_seconds),
        "reading_count": total,
        "avg_bpm": avg_bpm,
        "min_bpm": min_bpm,
        "max_bpm": max_bpm,
        "std_dev_bpm": std_dev,
        "zone_distribution_pct": zone_pct,
        "arrhythmia_events": arrhythmia_events,
        "bradycardia_episodes": brady_episodes,
        "tachycardia_episodes": tachy_episodes,
        "classification": classification,
    }


def _parse_ts(ts_str: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None


def _detect_arrhythmias(bpms: List[int]) -> List[Dict[str, Any]]:
    events = []
    for i in range(1, len(bpms)):
        delta = abs(bpms[i] - bpms[i - 1])
        if delta >= ARRHYTHMIA_BPM_DELTA:
            events.append({
                "index": i,
                "from_bpm": bpms[i - 1],
                "to_bpm": bpms[i],
                "delta": delta,
            })
    return events


def _detect_episodes(
    bpms: List[int], threshold: int, label: str, above: bool = False
) -> List[Dict[str, Any]]:
    episodes = []
    i = 0
    while i <= len(bpms) - CONSECUTIVE_FOR_EPISODE:
        segment = bpms[i:i + CONSECUTIVE_FOR_EPISODE]
        if all(b > threshold if above else b < threshold for b in segment):
            end = i + CONSECUTIVE_FOR_EPISODE
            while end < len(bpms) and (bpms[end] > threshold if above else bpms[end] < threshold):
                end += 1
            episodes.append({
                "type": label,
                "start_index": i,
                "end_index": end - 1,
                "duration_readings": end - i,
                "avg_bpm": round(statistics.mean(bpms[i:end]), 1),
            })
            i = end
        else:
            i += 1
    return episodes


def _classify_session(
    arrhythmias: List[Dict],
    brady_episodes: List[Dict],
    tachy_episodes: List[Dict],
    avg_bpm: float,
) -> str:
    total_episodes = len(brady_episodes) + len(tachy_episodes)
    if total_episodes >= 3 or len(arrhythmias) >= 5:
        return "critico"
    if total_episodes >= 1 or len(arrhythmias) >= 1 or avg_bpm > TACHY_THRESHOLD or avg_bpm < BRADY_THRESHOLD:
        return "atencion"
    return "normal"
