# compress.py
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import datetime
import math
import json
import os

# ---- Helpers ----

def _norm_muscle(m: str) -> str:
    """Normalize muscle group strings to a consistent lower-case key."""
    if not m:
        return "other"
    return m.strip().lower()

def _is_weighted_set(s: Dict[str, Any]) -> bool:
    return s.get("weight_lbs") not in (None, 0)

# ---- Compression functions ----

def compress_single_workout(day_date: str, day_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compress one day's workout into a compact summary.

    Input day_data should include:
      - 'exercises': list of set-like dicts. Example for each set:
          {
            "exercise": "Pull Up (Assisted)",
            "set_type": "normal",
            "weight_lbs": 150.0,
            "reps": 5,
            "distance": None,
            "notes": "",
            "muscle_groups": ["Back"]
          }

    Returns a compact dict:
      {
        "date": "2025-11-12",
        "had_workout": True/False,
        "focus": "push/pull/legs/full/other",
        "volume_sets": {"back": 6, "biceps": 4, ...},
        "total_sets": 12,
        "total_reps": 78,
        "estimated_volume": 12345.0, # sum(weight*reps) where weight present
        "key_lifts": [
           {"exercise": "Pull Up (Assisted)", "sets": 3, "avg_weight": 150.0, "avg_reps": 5}
        ],
        "notes": "optional aggregated notes"
      }
    """
    exercises = day_data.get("exercises", []) or []
    if not exercises:
        return {
            "date": day_date,
            "had_workout": False,
            "focus": "none",
            "volume_sets": {},
            "total_sets": 0,
            "total_reps": 0,
            "estimated_volume": 0.0,
            "key_lifts": [],
            "notes": ""
        }

    # Group by exercise name
    ex_groups = defaultdict(list)
    for s in exercises:
        name = (s.get("exercise") or "unknown").strip()
        ex_groups[name].append(s)

    # Volume per muscle
    volume_sets = Counter()
    total_sets = 0
    total_reps = 0
    estimated_volume = 0.0  # weight * reps sum (None weight treated as 0)
    lift_scores = {}  # heuristic for picking key lifts

    # Accumulate notes
    notes_parts = []

    for name, sets in ex_groups.items():
        sets_count = 0
        reps_sum = 0
        weight_sum = 0.0
        weight_count = 0
        muscles_seen = set()
        for s in sets:
            reps = s.get("reps") or 0
            weight = s.get("weight_lbs") or 0.0
            # muscle groups is a list per set in your data
            mgroups = s.get("muscle_groups") or []
            for mg in mgroups:
                mg_norm = _norm_muscle(mg)
                volume_sets[mg_norm] += 1  # count a set toward that muscle
                muscles_seen.add(mg_norm)

            sets_count += 1
            total_sets += 1
            reps_sum += reps
            total_reps += reps
            if weight:
                estimated_volume += weight * reps
                weight_sum += weight
                weight_count += 1

            note = s.get("notes")
            if note:
                notes_parts.append(note.strip())

        avg_weight = (weight_sum / weight_count) if weight_count else None
        avg_reps = (reps_sum / sets_count) if sets_count else None

        # Score key lifts by estimated volume (weight*reps) and sets_count
        score = (avg_weight or 0) * (avg_reps or 0) * sets_count
        lift_scores[name] = {
            "name": name,
            "sets": sets_count,
            "reps_sum": reps_sum,
            "avg_reps": avg_reps,
            "avg_weight": avg_weight,
            "muscles": sorted(list(muscles_seen)),
            "score": score
        }

    # Decide focus: heuristically choose muscle with highest sets
    if volume_sets:
        top_muscle, top_sets = volume_sets.most_common(1)[0]
        # map to push/pull/legs/simple categories
        push = {"chest", "shoulder", "shoulders", "triceps", "front delts", "pec"}
        pull = {"back", "biceps", "rear delts", "lats"}
        legs = {"quads", "hamstrings", "glutes", "calves", "legs"}
        if top_muscle in push:
            focus = "push"
        elif top_muscle in pull:
            focus = "pull"
        elif top_muscle in legs:
            focus = "legs"
        else:
            focus = top_muscle  # fallback to specific muscle
    else:
        focus = "other"

    # Choose key lifts: top 2 by score, prefer compound names (heuristic)
    sorted_lifts = sorted(lift_scores.values(), key=lambda x: x["score"], reverse=True)
    key_lifts = []
    for l in sorted_lifts[:3]:
        key_lifts.append({
            "exercise": l["name"],
            "sets": l["sets"],
            "avg_weight": round(l["avg_weight"], 1) if l["avg_weight"] is not None else None,
            "avg_reps": round(l["avg_reps"], 1) if l["avg_reps"] is not None else None,
            "muscles": l["muscles"]
        })

    summary = {
        "date": day_date,
        "had_workout": True,
        "focus": focus,
        "volume_sets": dict(volume_sets),  # sets per muscle
        "total_sets": total_sets,
        "total_reps": total_reps,
        "estimated_volume": round(estimated_volume, 1),
        "key_lifts": key_lifts,
        "notes": " | ".join(notes_parts[:5])  # small snippet
    }
    return summary


def compress_recent_workouts(combined_metrics: Dict[str, Dict[str, Any]],
                             n: int = 5,
                             ordered_desc: bool = True) -> List[Dict[str, Any]]:
    """
    Find the last N days that have workouts and compress them.

    - combined_metrics: { "YYYY-MM-DD": {...}, ... }
    - n: number of recent workouts to return
    - ordered_desc: if True returns newest first
    """
    # list of date strings that had workouts
    # sort keys descending by date
    dates = sorted(combined_metrics.keys(), reverse=ordered_desc)
    compressed = []
    for d in dates:
        if len(compressed) >= n:
            break
        day = combined_metrics[d]
        exercises = day.get("exercises") or []
        if not exercises:
            continue
        compressed.append(compress_single_workout(d, day))
    return compressed


def compute_weekly_volume(combined_metrics: Dict[str, Dict[str, Any]],
                          ref_date: Optional[str] = None) -> Dict[str, int]:
    """
    Compute week-to-date sets per muscle group.

    - ref_date: ISO string (YYYY-MM-DD). If None, today is used.
    - Week is ISO week starting Monday through Sunday (consistent with datetime.isocalendar())
    """
    if ref_date:
        ref = datetime.date.fromisoformat(ref_date)
    else:
        ref = datetime.date.today()

    ref_iso = ref.isocalendar()  # (year, weeknum, weekday)
    target_year, target_week = ref_iso[0], ref_iso[1]

    week_volume = Counter()
    for dstr, day in combined_metrics.items():
        try:
            d = datetime.date.fromisoformat(dstr)
        except Exception:
            continue
        iso = d.isocalendar()
        if (iso[0], iso[1]) != (target_year, target_week):
            continue
        exs = day.get("exercises") or []
        if not exs:
            continue
        for s in exs:
            mgs = s.get("muscle_groups") or []
            for mg in mgs:
                mg_norm = _norm_muscle(mg)
                week_volume[mg_norm] += 1
    return dict(week_volume)


def build_llm_payload(combined_metrics: Dict[str, Dict[str, Any]],
                      date_today: Optional[str] = None,
                      recent_n: int = 3) -> Dict[str, Any]:
    """
    Build the compact LLM payload for today's plan generation.

    Payload includes:
      - sleep_last_night (hours, score)
      - resting_heart_rate
      - bodyweight
      - week_volume (sets per muscle)
      - recent_workouts (compressed last N workouts)
      - last_workout_detailed (compressed summary of the most recent workout)
      - simple fatigue flags (low_sleep boolean)
    """
    if not date_today:
        date_today = datetime.date.today().isoformat()

    # Sleep and biometrics for the most recent prior day if available
    # Use the day BEFORE date_today as "last night" - user can override by passing date_today correctly.
    prev_date = (datetime.date.fromisoformat(date_today) - datetime.timedelta(days=1)).isoformat()
    prev = combined_metrics.get(prev_date, {})

    sleep_last_night = {
        "hours": prev.get("sleep_hours"),
        "score": prev.get("sleep_score"),
        "resting_hr": prev.get("resting_heart_rate")
    }

    bodyweight = prev.get("bodyweight") or combined_metrics.get(date_today, {}).get("bodyweight")

    week_volume = compute_weekly_volume(combined_metrics, ref_date=date_today)
    recent = compress_recent_workouts(combined_metrics, n=recent_n, ordered_desc=True)
    last_workout = recent[0] if recent else {"had_workout": False}

    # simple fatigue heuristic
    low_sleep = False
    if sleep_last_night.get("hours") is not None:
        low_sleep = sleep_last_night["hours"] < 6.0

    payload = {
        "date_for_plan": date_today,
        "sleep_last_night": sleep_last_night,
        "bodyweight": bodyweight,
        "week_volume": week_volume,
        "recent_workouts": recent,
        "last_workout_summary": last_workout,
        "low_sleep_flag": low_sleep
    }
    return payload

def repo_path(*paths):
    """Return repo-relative path for GitHub Actions or local usage."""
    return os.path.join(os.getcwd(), *paths)

def run_create_llm_payload():
    combined_file = repo_path("data", "combined_v5.json")
    output_file = repo_path("data", "llm_payload.json")

    with open(combined_file, "r") as f:
        combined_data = json.load(f)
        
    print("Compressed recent:", compress_recent_workouts(combined_data, n=3))
    print("Week volume:", compute_weekly_volume(combined_data))

    llm_payload = build_llm_payload(combined_data, date_today="2025-11-16", recent_n=3)
    print("Payload:", llm_payload)

    with open(output_file, "w+") as f: 
        json.dump(llm_payload, f, indent=2)

# ---- Example usage ----
if __name__ == "__main__":
    combined_file = repo_path("data", "combined_v5.json")
    output_file = repo_path("data", "llm_payload.json")

    with open(combined_file, "r") as f:
        combined_data = json.load(f)
    
    print("Compressed recent:", compress_recent_workouts(combined_data, n=3))
    print("Week volume:", compute_weekly_volume(combined_data))

    llm_payload = build_llm_payload(combined_data, date_today="2025-11-16", recent_n=3)
    print("Payload:", llm_payload)

    with open(output_file, "w+") as f: 
        json.dump(llm_payload, f, indent=2)
