import requests
from skyfield.api import load

url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle"

# The header tells the server we are a normal browser, not a bot
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("Reading local orbital data snapshot...")
with open("celestrak_data.txt", "r", encoding="utf-8") as f:
    raw_data = f.read()

# Save the local snapshot directly to the file Skyfield expects
with open("data/oneweb.tle", "w", encoding="utf-8") as f:
    f.write(raw_data)
    
print("Local data loaded successfully.")

satellites = load.tle_file("data/oneweb.tle")
print(f"Loaded {len(satellites)} objects")

if len(satellites) > 0:
    sat = satellites[0]
    print(sat.name, sat.model.satnum)
else:
    print("Still empty. Open the oneweb.tle file to see the exact error text.")

import numpy as np
import itertools

# --- STEP 4: PROPAGATION ---
print("Setting up time window...")
ts = load.timescale()
t0 = ts.now()

# Create an array of times: 0 to 3 days, stepping by 1/1440th of a day (1 minute)
times = ts.tt_jd(t0.tt + np.arange(0, 3, 1/1440))
print("Propagating orbits for 3 days at 1 minute intervals...")

positions = {}
for sat in satellites:
    # Calculate the satellite's position at all time steps
    geocentric = sat.at(times)
    # Store the 3D position vectors in kilometers
    positions[sat.model.satnum] = geocentric.position.km

print(f"Propagation complete! Stored data for {len(positions)} satellites.")

# --- STEP 5: DISTANCE CALCULATION ---
print("Computing pairwise distances to find close approaches. This will take a moment...")
results = []
sat_ids = list(positions.keys())

# Check every possible unique pair of satellites
for id_a, id_b in itertools.combinations(sat_ids, 2):
    pos_a = positions[id_a]
    pos_b = positions[id_b]
    
    # Calculate the distance between them at every minute
    dist = np.linalg.norm(pos_a - pos_b, axis=0)
    
    # Find the moment they are closest
    min_idx = np.argmin(dist)
    min_dist = dist[min_idx]
    
    results.append({
        "object_a": id_a,
        "object_b": id_b,
        "min_distance_km": min_dist,
        "tca_index": min_idx
    })

print(f"Screened {len(results)} unique pairs.")

import pandas as pd

# *** STEP 6: FLAG HIGH RISK PAIRS ***
print("\n*** STEP 6: Flagging High Risk Pairs ***")
# Convert the raw results into a clean pandas data table
df = pd.DataFrame(results)

# Define our risk boundary
THRESHOLD_KM = 5.0 

# Filter for danger and sort so the closest approaches are at the top
flagged = df[df["min_distance_km"] < THRESHOLD_KM].sort_values("min_distance_km")

print(f"Found {len(flagged)} pairs that cross the {THRESHOLD_KM}km threshold.")

# *** STEP 7: CONVERT INDEX TO READABLE DATE ***
print("\n*** STEP 7: Converting Timestamps ***")
if len(flagged) > 0:
    # Translate the index number back into a real UTC time string
    flagged["tca_utc"] = flagged["tca_index"].apply(lambda i: times[i].utc_iso())
    
    # Print a clean table of the top 10 riskiest pairs
    print("Top 10 Closest Approaches:")
    print(flagged[["object_a", "object_b", "min_distance_km", "tca_utc"]].head(10))
else:
    print("No close approaches found under this threshold!")

import plotly.graph_objects as go
import plotly.express as px

# *** STEP 8: 3D VISUALIZATION ***
print("\n*** STEP 8: Generating 3D Visualization ***")

involved_sats = list(set(flagged["object_a"]).union(set(flagged["object_b"])))
fig = go.Figure()

# 1. Draw a sleek dark Earth
u = np.linspace(0, 2 * np.pi, 50)
v = np.linspace(0, np.pi, 50)
x = 6371 * np.outer(np.cos(u), np.sin(v))
y = 6371 * np.outer(np.sin(u), np.sin(v))
z = 6371 * np.outer(np.ones(np.size(u)), np.cos(v))

fig.add_trace(go.Surface(
    x=x, y=y, z=z, 
    colorscale=[[0, '#0d1117'], [1, '#0d1117']], 
    opacity=1.0, 
    showscale=False, 
    name="Earth",
    hoverinfo="skip"
))

# 2. Plot orbits with distinct colors and satellite markers
print(f"Plotting orbits for the {len(involved_sats)} at risk satellites...")
colors = px.colors.qualitative.Alphabet 

for i, sat_id in enumerate(involved_sats):
    pos = positions[sat_id]
    color = colors[i % len(colors)]
    
    # The orbital path line
    fig.add_trace(go.Scatter3d(
        x=pos[0], y=pos[1], z=pos[2],
        mode="lines",
        line=dict(color=color, width=3),
        name=f"Sat {sat_id} Path"
    ))
    
    # The satellite's position marker (a glowing dot)
    fig.add_trace(go.Scatter3d(
        x=[pos[0][0]], y=[pos[1][0]], z=[pos[2][0]],
        mode="markers",
        marker=dict(color=color, size=6, symbol="circle"),
        name=f"Sat {sat_id} Position",
        showlegend=False
    ))

# Create a subtle, dark-themed style for the axes
axis_style = dict(
    showgrid=True,
    gridcolor="#30363d",     # Faint grey grid lines
    zeroline=False,
    showbackground=False,    # Keeps the space background transparent
    color="#8b949e",         # Subtle grey text for the numbers
    title_font=dict(color="#8b949e")
)

fig.update_layout(
    scene=dict(
        aspectmode="data",
        bgcolor="#161b22",
        xaxis=axis_style,
        yaxis=axis_style,
        zaxis=axis_style
    ),
    paper_bgcolor="#161b22",
    plot_bgcolor="#161b22",
    title=dict(text="Flagged Orbits | Close Approaches", font=dict(color="#e6edf3")),
    margin=dict(l=0, r=0, b=0, t=40),
    legend=dict(font=dict(color="#e6edf3"), bgcolor="rgba(0,0,0,0)")
)

# 3. Save the interactive plot
fig.write_html("app/orbits_3d.html")
print("Success! 3D plot saved to app/orbits_3d.html")

import streamlit as st
import streamlit.components.v1 as components

# *** STEP 9: STREAMLIT DASHBOARD ***
print("\n*** STEP 9: Launching Dashboard ***")

# We use Streamlit to build the web app interface
st.set_page_config(layout="wide", page_title="SSA Risk Dashboard")

# Hide default Streamlit branding
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Apply custom CSS to match your NewSpace aesthetic
custom_css = """
<style>
/* Global Typography */
html, body, [class*="css"]  {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
}

/* Style the Metric Cards */
[data-testid="stMetric"] {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px;
}

/* Style the DataFrame Container */
[data-testid="stDataFrame"] {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 15px;
}

/* Adjust the main container layout */
.block-container {
    padding-top: 3rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.title("Orbital Conjunction Risk Dashboard")

# Adding the required business context from the project guide
st.markdown("""
**Context:** As the density of objects in Low Earth Orbit increases, collisions become more likely, potentially triggering Kessler Syndrome. 
This dashboard is a small scale model of the conjunction screening pipelines run operationally by Space Situational Awareness teams at Vyoma and DLR GSOC.
""")

# Display high level metrics
col1, col2 = st.columns(2)
col1.metric("Objects Tracked", len(sat_ids))
col2.metric("Flagged Close Approaches", len(flagged))

# Display the sortable data table
st.subheader("Risky Approaches (Under 5km threshold)")
st.dataframe(
    flagged[["object_a", "object_b", "min_distance_km", "tca_utc"]], 
    width='stretch'
)

# Embed the 3D Plotly visualization we generated in Step 8
st.subheader("3D Interactive Orbit Visualization")
with open("app/orbits_3d.html", "r", encoding="utf-8") as f:
    html_data = f.read()

st.components.v1.html(html_data, height=600)