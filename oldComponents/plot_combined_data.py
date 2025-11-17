import json
import pandas as pd
from dash import Dash, dcc, html
import plotly.express as px

def load_combined_json(path='data/combined.json'):
    with open(path) as f:
        combined = json.load(f)
    
    rows = []
    for date, data in combined.items():
        # Add general Fitbit metrics
        row = {
            "date": pd.to_datetime(date),
            "steps": data.get("steps"),
            "distance": data.get("distance"),
            "calories_burned": data.get("calories_burned"),
            "sleep_hours": data.get("sleep_hours"),
            "sleep_score": data.get("sleep_score")
        }
        
        # Workout summary: total sets, total reps, total weight lifted
        exercises = data.get("exercises", [])
        row["workout_title"] = data.get("workout_title")
        row["total_sets"] = len(exercises)
        total_reps = sum(e["reps"] or 0 for e in exercises)
        total_weight = sum((float(e["weight_lbs"] or 0) * (e["reps"] or 0)) for e in exercises)
        row["total_reps"] = total_reps
        row["total_weight_lifted"] = total_weight
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.sort_values("date", inplace=True)
    return df

def create_dashboard(df):
    app = Dash(__name__)

    ### STEPS
    # ----------------------
    # Calculate average line
    # ----------------------
    average_steps = df["steps"].mean()
    df["average_steps"] = average_steps

    df['steps_rolling'] = df['steps'].rolling(window=7, min_periods=1).mean()
    df['distance_rolling'] = df['distance'].rolling(window=7, min_periods=1).mean()

    # ----------------------
    # Create the figure
    # ----------------------
    color = avg_steps_to_color(average_steps)
    steps_fig = px.bar(df, x="date", y="steps", title="Steps Over Time")
    steps_fig.add_scatter(x=df["date"], y=df["steps_rolling"], mode="lines+markers",
                    name="Average Steps", line=dict(dash="dot", color=color))
    steps_fig.add_scatter(x=df["date"], y=df["average_steps"], mode="lines",
                    name="Average Steps", line=dict(dash="solid", color="white"))
    steps_fig = autoscale_x(steps_fig, df, "steps")

    # Time series plots
    # steps_fig = px.line(df, x='date', y='steps', title='Steps over Time')
    # distance_fig = px.bar(df, x='date', y='distance', title='Distance (miles) over Time')
    # distance_fig.add_scatter(x=df["date"], y=df["distance_rolling"], mode="lines",
    #                 name="Average Distance", line=dict(dash="dot", color="black"))

    ### SLEEP 
    average_sleep = df["sleep_hours"].mean()
    df["average_sleep"] = average_sleep

    df['sleep_rolling'] = df['sleep_hours'].rolling(window=7, min_periods=1).mean()
    
    sleep_fig = px.line(df, x='date', y='sleep_hours', title='Sleep Hours over Time')
    sleep_fig.add_scatter(x=df["date"], y=df["sleep_rolling"], mode="lines+markers",
                    name="Average Sleep", line=dict(dash="dot", color=color))
    sleep_fig.add_scatter(x=df["date"], y=df["average_sleep"], mode="lines",
                    name="Average Sleep", line=dict(dash="solid", color="white"))
    sleep_fig = autoscale_x(sleep_fig, df, "sleep_hours")


    calories_fig = px.line(df, x='date', y='calories_burned', title='Calories Burned over Time')

    # Workout metrics
    sets_fig = px.bar(df, x='date', y='total_sets', title='Total Workout Sets per Day')
    reps_fig = px.bar(df, x='date', y='total_reps', title='Total Reps per Day')
    weight_fig = px.bar(df, x='date', y='total_weight_lifted', title='Total Weight Lifted per Day')

    # Layout
    app.layout = html.Div([
        html.H1("Fitness Dashboard"),
        dcc.Graph(figure=steps_fig),
        # dcc.Graph(figure=distance_fig),
        dcc.Graph(figure=sleep_fig),
        dcc.Graph(figure=calories_fig),
        html.H2("Workout Stats"),
        dcc.Graph(figure=sets_fig),
        dcc.Graph(figure=reps_fig),
        dcc.Graph(figure=weight_fig),
    ])
    
    return app

def avg_steps_to_color(average_steps):
    if average_steps >= 10000:
        return "green"
    elif average_steps >= 5000:
        return "orange"
    else:
        return "red"

def autoscale_x(fig, df, field):
    # Filter rows with steps data
    df_steps = df[df[str(field)].notna()]

    # Get min/max of the date column
    min_date = df_steps['date'].min()
    max_date = df_steps['date'].max()

    # Set x-axis range
    fig.update_layout(xaxis=dict(range=[min_date, max_date]))
    return fig

def main(): 
    df = load_combined_json('data/combined.json')
    
    px.defaults.template = "plotly_dark"
    px.defaults.color_continuous_scale = px.colors.sequential.Viridis  # optional: nicer default color scale

    app = create_dashboard(df)
    app.run(debug=True)

if __name__ == "__main__":
    main()