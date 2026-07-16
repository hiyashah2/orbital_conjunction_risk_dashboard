# Orbital Conjunction Risk Dashboard

An interactive Space Situational Awareness (SSA) tool that tracks real satellites in orbit, predicts their future positions, and flags close-approach ("conjunction") events between them — a small-scale model of the collision-risk screening pipelines run operationally by companies and agencies like Vyoma and DLR's GSOC.

**Live dashboard:** https://orbitalconjunctionriskdashboard.streamlit.app/

---

## Context

As the number of active satellites and debris fragments in Low Earth Orbit grows — driven largely by mega-constellations — the risk of in-orbit collisions rises with it, a compounding effect known as **Kessler Syndrome**. Operators and SSA teams continuously screen tracked objects against each other to catch dangerous close approaches before they happen.

This project builds a compact, from-scratch version of that same screening pipeline: real orbital data in, flagged risk pairs and a visual 3D orbit view out.

## What it does

- Loads real orbital data (Two-Line Element sets) for the **OneWeb constellation** (~650 active satellites)
- Propagates every object's position over a **3-day window at 1-minute resolution** using the SGP4 propagation model
- Screens **every unique pair of tracked objects** for their closest approach distance and time (Time of Closest Approach)
- Flags any pair passing within **5 km** of each other as a risky close approach
- Renders an **interactive 3D visualization** of the flagged objects' orbital paths around Earth
- Presents everything in a live, sortable **Streamlit dashboard**

## How it works

1. **Data ingestion** — TLE data for the OneWeb constellation is loaded from a saved local snapshot (`celestrak_data.txt`), originally sourced from [Celestrak](https://celestrak.org)
2. **Propagation** — each object's position is computed at 1-minute intervals over a 3-day window using `skyfield`'s SGP4 implementation, returning 3D position vectors (km) for every object at every timestep
3. **Conjunction screening** — for every pair of objects, the Euclidean distance between their position vectors is computed across the full time window; the minimum distance and its timestamp become that pair's candidate risk event
4. **Risk flagging** — pairs with a minimum distance under 5 km are flagged and sorted by closest approach
5. **Visualization** — flagged objects' full orbital paths are rendered in an interactive 3D Plotly scene, styled to match the dashboard's dark theme
6. **Dashboard** — Streamlit ties it together: summary metrics, a sortable table of flagged risk pairs, and the embedded 3D view

## Tech stack

| Tool | Purpose |
|---|---|
| [skyfield](https://rhodesmill.org/skyfield/) | TLE parsing and SGP4 orbit propagation |
| numpy | Vector math for position/distance calculations |
| pandas | Organizing and filtering conjunction results |
| plotly | Interactive 3D orbit visualization |
| streamlit | Dashboard interface and deployment |
| requests | (Live TLE fetching support — see Data Source below) |

## Data source

Orbital data covers the OneWeb constellation, originally retrieved from [Celestrak's public TLE feed](https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle). The dashboard currently reads from a saved local snapshot (`celestrak_data.txt`) for reliability rather than fetching live on every run — see **Future Improvements** below for adding a scheduled live refresh.

## Project structure

```
orbital_conjunction_risk_dashboard/
├── src/
│   └── build_model.py      # Full pipeline: data load → propagation → screening → viz → dashboard
├── data/
│   └── oneweb.tle           # Working TLE data used by the pipeline
├── app/
│   └── orbits_3d.html       # Generated 3D visualization, embedded in the dashboard
├── celestrak_data.txt        # Local snapshot of OneWeb TLE data
├── .streamlit/
│   └── config.toml           # Dashboard theme configuration
└── requirements.txt
```

## Running it locally

```bash
git clone https://github.com/hiyashah2/orbital_conjunction_risk_dashboard.git
cd orbital_conjunction_risk_dashboard
pip install -r requirements.txt
streamlit run src/build_model.py
```

## Scope and limitations

This is a portfolio/educational-scale implementation, and it's worth being upfront about what that means:

- **Miss-distance screening only** — risk is assessed purely on minimum separation distance, not a full Probability of Collision (Pc) calculation, which would require position-uncertainty (covariance) data not available in public TLEs. This is the standard first-pass method taught before Pc, and matches how real screening pipelines gate their first pass.
- **Single constellation** — currently screens OneWeb against itself; doesn't yet cross-screen against other constellations or debris catalogs.
- **TLE accuracy window** — TLE-based predictions are most reliable within a few days of their epoch; the 3-day propagation window is chosen deliberately to stay within that reliable range.

## Future improvements

- Live TLE refresh on a schedule, rather than a static snapshot
- Cross-screen OneWeb against Starlink and known debris clusters for a more realistic multi-constellation picture
- Add relative velocity at closest approach as a second risk factor alongside distance
- Validate flagged events against publicly documented real conjunction cases


## Author

Hiya Shah — [GitHub](https://github.com/hiyashah2)
