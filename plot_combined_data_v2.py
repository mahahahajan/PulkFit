import json
import pandas as pd
from dash import Dash, dcc, html
import plotly.express as px
import plotly.io as pio
import numpy as np

from oldComponents.combine_datasets_v2 import EXERCISE_TO_MET 

# --- Helper: Estimate workout calories if missing ---
def estimate_workout_calories(exercises, body_weight_kg=72):  # ~158 lb
    total_calories = 0
    for e in exercises:
        exercise = e.get("exercise")
        reps = e.get("reps") or 0
        met = EXERCISE_TO_MET.get(exercise, 5)
        duration_min = max(0.3, reps / 20)
        calories = (met * 3.5 * body_weight_kg / 200) * duration_min
        total_calories += calories
    return round(total_calories, 1)

# --- Load and flatten combined data ---
def load_combined_json(path='data/combined.json'):
    with open(path) as f:
        combined = json.load(f)

    rows = []
    for date, data in combined.items():
        exercises = data.get("exercises", [])
        total_reps = sum(e.get("reps") or 0 for e in exercises)
        total_weight = sum((float(e.get("weight_lbs") or 0) * (e.get("reps") or 0)) for e in exercises)
        total_sets = len(exercises)

        # Workout calories fallback
        workout_cals = data.get("calories_burned_from_workout") or estimate_workout_calories(exercises)

        rows.append({
            "date": pd.to_datetime(date),
            "steps": data.get("steps"),
            "distance": data.get("distance"),
            "fitbit_calories": data.get("calories_burned_from_steps"),
            "workout_calories": workout_cals,
            "total_calories": data.get("total_calories_burned"),
            "sleep_hours": data.get("sleep_hours"),
            "sleep_score": data.get("sleep_score"),
            "workout_title": data.get("workout_title"),
            "total_sets": total_sets,
            "total_reps": total_reps,
            "total_weight_lifted": total_weight,
            "exercises": data.get("exercises", []) 
        })

    df = pd.DataFrame(rows)
    df.sort_values("date", inplace=True)
    return df

# --- Visualization ---
def create_dashboard(df):
    app = Dash(__name__)

    px.defaults.template = "plotly_dark"
    px.defaults.color_continuous_scale = px.colors.qualitative.Dark2
    px.defaults.color_discrete_sequence = px.colors.qualitative.Dark2
    # plotly_template = pio.templates["plotly_dark"]
    # plotly_template.data["colorway"][0] = '#00cc96'
    # print (plotly_template)

    # print(px.defaults.template)

    # Rolling averages
    for col in ["steps", "sleep_hours", "total_calories"]:
        df[f"{col}_rolling"] = df[col].rolling(window=7, min_periods=1).mean()

    for col in ["steps", "sleep_hours", "total_calories"]:
        df[f"{col}_total_average"] = df[col].mean(skipna=True)

    # --- Calories Plot ---
    calories_fig = px.line(df, x="date", y="total_calories", title="Calories Burned (Fitbit + Workouts)",
                           labels={"total_calories": "Calories"})
    calories_fig.add_scatter(x=df["date"], y=df["total_calories_rolling"], mode="lines", name="7-Day Avg (Total)", line=dict(color="white", width=3))
    # calories_fig.add_scatter(x=df["date"], y=df["fitbit_calories"], mode="lines", name="Calories from Steps", line=dict(dash="dash"))
    # calories_fig.add_scatter(x=df["date"], y=df["workout_calories"], mode="lines", name="Calories from Workout", line=dict(dash="dot"))
    calories_series = df["total_calories"].replace(0, pd.NA)
    avg_calories = calories_series.mean(skipna=True)
    calories_fig.add_hline(y=avg_calories, line_dash="dot", annotation_text=f"Avg Calories: {int(avg_calories)}", annotation_position="top left")
    # calories_fig.add_scatter(x=df["date"], y=df["total_calories_total_average"], mode="lines", name="Total Average Calories Burned in a Day", line=dict(dash="dot"))
    calories_fig = autoscale_x(calories_fig, df, "total_calories")

    # --- Steps Plot ---
    steps_fig = px.bar(df, x="date", y="steps", title="Daily Steps")
    steps_fig.add_scatter(x=df["date"], y=df["steps_rolling"], mode="lines", name="7-Day Avg", line=dict(color="white"))
    step_series = df["steps"].replace(0, pd.NA)
    avg_steps = step_series.mean(skipna=True)
    steps_fig.add_hline(y=avg_steps, line_dash="dot", annotation_text=f"Avg Steps: {int(avg_steps)}", annotation_position="top left")
    steps_fig = autoscale_x(steps_fig, df, "steps")

    # --- Sleep Plot ---
    sleep_fig = px.line(df, x="date", y="sleep_hours", title="Sleep Hours")
    sleep_fig.add_scatter(x=df["date"], y=df["sleep_hours_rolling"], mode="lines", name="7-Day Avg", line=dict(color="white"))
    sleep_series = df["sleep_hours"].replace(0, pd.NA)
    avg_sleep = sleep_series.mean(skipna=True)
    sleep_fig.add_hline(y=avg_sleep, line_dash="dot", annotation_text=f"Avg Sleep: {avg_sleep:.1f}h", annotation_position="top left")
    sleep_fig = autoscale_x(sleep_fig, df, "sleep_hours")

    muscle_group_trends_fig = plot_muscle_group_sets_trends(df)
    muscle_groups_trends_monthly_fig = plot_muscle_group_sets_last_month(df)

    muscle_group_weight_trend_fig = plot_muscle_group_weight_trends_ranked(df)

    plot_progress_fig = plot_progress_tracking(df)

    # --- Workout Metrics ---
    sets_fig = px.bar(df, x="date", y="total_sets", title="Workout Sets per Day")
    reps_fig = px.bar(df, x="date", y="total_reps", title="Reps per Day")
    weight_fig = px.bar(df, x="date", y="total_weight_lifted", title="Total Weight Lifted per Day (lbs)")

    # --- Layout ---
    app.layout = html.Div([
        html.H1("Fitness Dashboard", style={"textAlign": "center", "marginBottom": "20px"}),
        html.Div([
            dcc.Graph(figure=calories_fig),
            dcc.Graph(figure=steps_fig),
            dcc.Graph(figure=sleep_fig),
            html.H2("Workout Stats", style={"marginTop": "30px", "textAlign": "center"}),
            dcc.Graph(figure=muscle_groups_trends_monthly_fig),
            dcc.Graph(figure=muscle_group_trends_fig),
            dcc.Graph(figure=muscle_group_weight_trend_fig),
            dcc.Graph(figure=plot_progress_fig),
            dcc.Graph(figure=sets_fig),
            dcc.Graph(figure=reps_fig),
            dcc.Graph(figure=weight_fig),
        ], style={"padding": "10px"})
    ], style={"maxWidth": "900px", "margin": "auto", "padding": "10px"})
    return app

def plot_muscle_group_sets_trends(df):
    """
    Create a grouped bar chart showing weekly total sets per muscle group.
    """
    rows = []
    for _, row in df.iterrows():
        date = row.get("date")
        exercises = row.get("exercises", [])
        for ex in exercises:
            if not ex or "exercise" not in ex:
                continue
            exercise_name = ex.get("exercise")
            # Get the muscle groups from the central mapping
            muscle_groups = ex.get("muscle_groups")
            for mg in muscle_groups:
                rows.append({
                    "date": pd.to_datetime(date),
                    "muscle_group": mg,
                    "sets": 1
                })

    if not rows:
        print("⚠️ No exercise data found for plotting.")
        return None

    df_sets = pd.DataFrame(rows)
    # Aggregate sets per muscle group per week
    df_sets["week"] = df_sets["date"].dt.to_period("W").apply(lambda r: r.start_time)
    df_weekly = df_sets.groupby(["week", "muscle_group"], as_index=False).agg({"sets": "sum"})

    # Grouped bar chart
    fig = px.bar(
        df_weekly,
        x="week",
        y="sets",
        color="muscle_group",
        barmode="group",
        title="💪 Weekly Sets per Muscle Group",
        labels={"week": "Week", "sets": "Total Sets"},
    )

    fig.update_layout(
        xaxis_title="Week",
        yaxis_title="Total Sets",
        legend_title="Muscle Group",
        hovermode="x unified",
    )

    return fig

def plot_muscle_group_sets_last_month(df):
    """
    Create a grouped bar chart showing weekly total sets per muscle group
    for only the last month.
    """
    rows = []
    for _, row in df.iterrows():
        date = row.get("date")
        exercises = row.get("exercises", [])
        for ex in exercises:
            if not ex or "exercise" not in ex:
                continue
            muscle_groups = ex.get("muscle_groups")
            if not muscle_groups:
                continue
            for mg in muscle_groups:
                rows.append({
                    "date": pd.to_datetime(date),
                    "muscle_group": mg,
                    "sets": 1
                })

    if not rows:
        print("⚠️ No exercise data found for plotting.")
        return None

    df_sets = pd.DataFrame(rows)

    # Filter to only last month
    last_month = df_sets["date"].max() - pd.DateOffset(days=30)
    df_sets = df_sets[df_sets["date"] >= last_month]

    # Aggregate sets per muscle group per week
    df_sets["week"] = df_sets["date"].dt.to_period("W").apply(lambda r: r.start_time)
    df_weekly = df_sets.groupby(["week", "muscle_group"], as_index=False).agg({"sets": "sum"})

    # Grouped bar chart
    fig = px.bar(
        df_weekly,
        x="week",
        y="sets",
        color="muscle_group",
        barmode="group",
        title="💪 Weekly Sets per Muscle Group (Last 30 Days)",
        labels={"week": "Week", "sets": "Total Sets"},
    )

    fig.update_layout(
        xaxis_title="Week",
        yaxis_title="Total Sets",
        legend_title="Muscle Group",
        hovermode="x unified",
    )

    return fig

def plot_muscle_group_weight_trends_ranked(df):
    """
    Create a grouped bar chart showing weekly total weight lifted per muscle group,
    with weights adjusted based on exercise type and ranked per week.
    """
    rows = []
    for _, row in df.iterrows():
        date = row.get("date")
        exercises = row.get("exercises", [])
        for ex in exercises:
            if not ex or "muscle_groups" not in ex:
                continue

            weight = ex.get("weight_lbs") or 0
            reps = ex.get("reps") or 0
            exercise_name = ex.get("exercise", "").lower()
            notes = ex.get("notes", "").lower()

            # --- Adjust weight based on exercise type ---
            actual_weight = weight

            # if "barbell" in exercise_name:
            #     actual_weight = 2 * weight + 45
            # elif "assisted" in exercise_name:
            #     # Bodyweight assumed ~158 lbs (adjustable)
            #     bodyweight = 158
            #     actual_weight = bodyweight - weight
            # elif "smith" in exercise_name or "smith" in notes:
            #     actual_weight = 2 * weight

            total_weight = actual_weight * reps

            for mg in ex.get("muscle_groups", []):
                rows.append({
                    "date": pd.to_datetime(date),
                    "muscle_group": mg,
                    "total_weight": total_weight
                })

    if not rows:
        print("⚠️ No exercise data found for plotting.")
        return None

    df_weights = pd.DataFrame(rows)

    # Aggregate per week
    df_weights["week"] = df_weights["date"].dt.to_period("W").apply(lambda r: r.start_time)
    df_weekly = df_weights.groupby(["week", "muscle_group"], as_index=False).agg({"total_weight": "sum"})

    # Keep only last 4 weeks
    latest_week = df_weekly["week"].max()
    df_weekly = df_weekly[df_weekly["week"] >= (latest_week - pd.Timedelta(weeks=4))]

    # --- Rank muscle groups per week ---
    df_weekly["rank"] = df_weekly.groupby("week")["total_weight"].rank(method="first", ascending=False)
    df_weekly.sort_values(["week", "rank"], inplace=True)

    # Grouped bar chart
    fig = px.bar(
        df_weekly,
        x="week",
        y="total_weight",
        color="muscle_group",
        title="🏋️ Weekly Total Weight by Muscle Group (Ranked, Adjusted Weights)",
        labels={"week": "Week", "total_weight": "Total Weight (lbs × reps)"},
    )

    fig.update_layout(
        xaxis_title="Week",
        yaxis_title="Total Weight Lifted",
        legend_title="Muscle Group",
        hovermode="x unified",
        barmode="group",
    )

    return fig

def plot_progress_tracking(df):
    """
    Track weekly progress for Back, Chest, and Quads.
    Shows total weekly training volume (weight x reps) per muscle group.
    Adds 3-week rolling trend lines for each muscle group with matching colors.
    """
    import plotly.express as px

    target_muscle_groups = ["Back", "Chest", "Quads"]
    rows = []

    for _, row in df.iterrows():
        date = row.get("date")
        exercises = row.get("exercises", [])
        for ex in exercises:
            if not ex or "muscle_groups" not in ex:
                continue

            weight = ex.get("weight_lbs") or 0
            reps = ex.get("reps") or 0
            exercise_name = ex.get("exercise", "").lower()
            notes = ex.get("notes", "").lower()

            # Adjust weight
            # actual_weight = weight
            # if "barbell" in exercise_name:
            #     actual_weight = 2 * weight + 45
            # elif "assisted" in exercise_name:
            #     bodyweight = 158
            #     actual_weight = bodyweight - weight
            # elif "smith" in exercise_name or "smith" in notes:
            #     actual_weight = 2 * weight

            total_weight = weight * reps

            for mg in ex.get("muscle_groups", []):
                if mg in target_muscle_groups:
                    rows.append({
                        "date": pd.to_datetime(date),
                        "muscle_group": mg,
                        "volume": total_weight
                    })

    if not rows:
        print("⚠️ No target muscle group data found for plotting.")
        return None

    df_volume = pd.DataFrame(rows)

    # Aggregate weekly
    df_volume["week"] = df_volume["date"].dt.to_period("W").apply(lambda r: r.start_time)
    df_weekly = df_volume.groupby(["week", "muscle_group"], as_index=False).agg({"volume": "sum"})

    # Add rolling trend
    df_weekly = df_weekly.sort_values("week")
    df_weekly["volume_rolling"] = df_weekly.groupby("muscle_group")["volume"].rolling(window=3, min_periods=1).mean().reset_index(level=0, drop=True)

    # --- Plotly Express grouped bar chart ---
    fig = px.bar(
        df_weekly,
        x="week",
        y="volume",
        color="muscle_group",
        barmode="group",
        title="📈 Progress Tracking: Back, Chest, Quads",
        labels={"week": "Week", "volume": "Total Weight × Reps", "muscle_group": "Muscle Group"},
    )

    # Extract bar colors from the figure to use for trend lines
    color_map = {d.name: d.marker.color for d in fig.data if hasattr(d, "marker") and hasattr(d, "name")}

    # Add trend lines with matching colors
    for mg in target_muscle_groups:
        trend_df = df_weekly[df_weekly["muscle_group"] == mg]
        fig.add_scatter(
            x=trend_df["week"],
            y=trend_df["volume_rolling"],
            mode="lines",
            line=dict(dash="dot", width=3, color=color_map.get(mg, "white")),
            name=f"{mg} Trend"
        )

    return fig

def autoscale_x(fig, df, field):
    df_valid = df[(df[field].notna()) & (df[field] != 0)]
    if(field == 'total_calories'):
        df_valid = df[df[field] > 100]
    
    if not df_valid.empty:
        fig.update_layout(xaxis=dict(range=[df_valid["date"].min(), df_valid["date"].max()]))
    return fig

def main():
    df = load_combined_json('data/combined_v5.json')
    app = create_dashboard(df)
    app.run(debug=True)

if __name__ == "__main__":
    main()
