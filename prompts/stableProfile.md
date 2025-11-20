{
  "trainee": {
    "age": 25,
    "height": "5'5",
    "weight_lbs": 160,
    "experience_years": 2.5,
    "goals": {
      "bodyfat_target": "10-14%",
      "performance": [
        "10 pull ups",
        "5 weighted pull ups",
        "225 bench",
        "300 squat",
        "400 deadlift",
        "front lever progression",
        "handstand progression",
        "Muscle up progression",
        "Hyrox/Spartan readiness",
        "8 minute mile time (Currently 12:00)",
        "better posture",
        "improve grip endurance for pullups/deadlifts"
      ],
      "aesthetic": {
        "back_to_waist_ratio": 1.6,
        "boulder_shoulders": true,
        "visible_muscle_tone": true,
        "lean_body_type": true
      },
      "goal_hierarchy": {
        "priority_order": [
          "Compound Strength Lifts (Bench, Deadlift Alternatives)",
          "Pull-up/Calisthenics Progression",
          "Cardio Performance (8-min mile/10k Endurance)",
          "Aesthetic Volume (Shoulders/Back-to-Waist)"
        ],
        "running_principle": "Focus on CONSISTENCY and speed work (Intervals) over sheer weekly VOLUME."
      }
    },
    "constraints": {
      "sessions_per_week": "3-4",
      "sleep_pattern": "avg 6 hours w/ disruptions",
      "weekend_behavior": "late nights (Friday/Saturday), alcohol 4-6 shots",
      "equipment": "Crunch gym standard setup",
      "weekday_behavior": "software engineer, primarily desk job 10-6",
      "preferences": {
        "dislike": [
          "squats",
          "leg movements",
          "long isolation-only sessions"
        ],
        "like": [
          "weightlifting",
          "swimming",
          "compound lifts",
          "efficient 1-hour sessions"
        ]
      },
      "weightlifting_plan": {
        "likes": [
          "compound lifts",
          "fewer total exercises",
          "incline over flat bench",
          "focus on boulder shoulders each session"
        ],
        "dislikes": [
          "complicated setup",
          "single side movements (eg split squats)",
          "repeated deadlifts",
          "too much CNS fatigue"
        ]
      },
      "recovery_notes": {
        "typical_soreness": "moderate after upper body push/pull days",
        "injuries": [
          "mild forearm tendon strain historically",
          "occasional lower back tightness"
        ],
        "mobility_issues": [
          "shoulder external rotation weakness",
          "tight hamstrings"
        ],
        "stretching_preference": "dynamic warmups > long static stretching during sessions"
      },
      "nutrition_considerations": {
        "protein_target_g": 140,
        "protein_priority": true,
        "typical_weekday_intake": "high adherence (ground beef, shakes, veggies)",
        "typical_weekend_intake": "inconsistent, treats, high-carb meals",
        "hydration_target_oz": 80
      },
      "cardio_plan": {
        "cardio_preferences": [
          "short interval work mandatory",
          "no more than 3 runs per week"
        ],
        "baseline_performance": ["unable to run 3 miles continuosly without stopping", "running 12 min mile is RPE 7"],
        "cardio_targets": {
          "8_minute_mile_pace": "Target 8:00/mile (Currently 12:00/mile)",
          "endurance_target": "10k distance ASAP",
          "ideal_training_pace_ranges": {
            "easy_recovery": "10:00-11:30/mile",
            "tempo_threshold": "8:30-9:30/mile",
            "interval_speed": "7:00-7:45/mile"
          },
          "session_templates": {
            "speed_interval": "Max 45 min. Purpose: VO2max/Pace Familiarity. Structure: 4-6 sets of 400m-800m @ interval pace with equal rest.",
            "tempo_threshold": "Max 50 min. Purpose: Lactate Tolerance/Sustained Speed. Structure: 20-30 min sustained effort at tempo pace.",
            "easy_recovery": "Max 30 min. Purpose: Aerobic Base/Active Recovery. Structure: Sustained effort at easy pace (RPE 5-6)."
          }
        }
      },
      "progress_tracking": {
        "metrics": [
          "pullups max reps",
          "weighted pullups",
          "bench/row/deadlift incline/flat weights",
          "body weight",
          "waist/back measurements",
          "sleep quality",
          "RPE per lift",
          "step count",
          "mile time (current/best)",
          "run distance/time per session"
        ],
        "frequency": [
          "weekly weigh-in",
          "daily training log",
          "weekly performance check (lift/run)"
        ]
      },
      "AI_daily_optimizer_inputs": {
        "current_fatigue_level": "moderate (self-reported)",
        "recent_workouts_summary": "last 3 days sets/reps/weights/RPE",
        "recent_nutrition_summary": "calories/protein adherence last 3 days",
        "recent_sleep_summary": "average last 3 nights",
        "injury_alerts": "forearm/back soreness, shoulder tightness",
        "mobility_alerts": "shoulder, hamstrings",
        "run_baseline": {
          "current_mile_time": "12:00",
          "max_weekly_run_volume_miles": 4
        }
      },
      "movement_rules": {
        "bench": "Incline Barbell preferred; no dumbbell substitution",
        "overhead_press": "Only on push + dips days; skip if incline bench is done",
        "pullups": "Use bodyweight, assisted, or negatives - whatever builds pull up strength quickest",
        "avoid": [
          "excessive isolation",
          "CNS-overfatigue exercises",
          "split-squats",
          "repeated deadlifts"
        ],
        "prioritize": [
          "building strength to get to 10 pullups",
          "least amount of work for max strength gains",
          "aesthetics"
        ],
        "conditional_run_scheduling": [
          "Total training must not exceed 4 sessions/week (3 strength max, 3 run max). Strength days take priority.",
          "Running days must be scheduled on non-strength days or separated by >8 hours.",
          "IF Injury_Alerts include 'lower back tightness' AND a strength session is scheduled TOMORROW: THEN swap TEMPO or SPEED run for an EASY/RECOVERY run to conserve CNS/low-back recovery.",
          "IF current_fatigue_level is HIGH OR recent_sleep_summary is <6 hours: THEN only schedule an EASY/RECOVERY run. DELAY planned Speed/Tempo until recovery improves.",
          "IF running volume is high (>4 miles total), reduce total strength-focused leg sets to 1/2 the baseline plan (running serves as primary functional leg stimulus)."
        ]
      }
    }
  }
}