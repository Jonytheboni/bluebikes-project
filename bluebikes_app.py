"""
Name: Joao Pereira
CS230
Data: Blue Bikes Boston Trips from September 2020
URL: (Add your Streamlit Cloud link here after publishing)

Description:
    This program explores Blue Bikes trip data from September 2020 in Boston.
    Users can filter trips by user type and duration, explore the busiest
    stations, view trip patterns by day of the week, and see ride locations
    on an interactive map. The app provides summary statistics, bar charts,
    a scatter plot, and a PyDeck map to tell the story of how Boston commuters
    and recreational riders used the Blue Bikes system.

References:
    - Streamlit documentation: https://docs.streamlit.io
    - PyDeck documentation: https://deckgl.readthedocs.io
    - Pandas documentation: https://pandas.pydata.org/docs/
    - Blue Bikes system data: https://bluebikes.com/system-data
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pydeck as pdk

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="🚲 Blue Bikes Explorer",
    page_icon="🚲",
    layout="wide",
)

# ─────────────────────────────────────────────
#  LOAD & PREPARE DATA
# ─────────────────────────────────────────────

# #[FUNCCALL2] – load_data() is called once here (cached) and reused everywhere
@st.cache_data
def load_data(file_id):
    """Load the Blue Bikes Excel file and engineer useful columns."""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    df = pd.read_csv(url, encoding="latin-1")
    df["starttime"] = pd.to_datetime(df["starttime"], infer_datetime_format=True, errors="coerce")

    # Convert trip duration from seconds to minutes  #[COLUMNS]
    df["duration_min"] = df["tripduration"] / 60

    # Extract day-of-week and hour from the start time  #[COLUMNS]
    df["day_of_week"] = df["starttime"].dt.day_name()
    df["hour"] = df["starttime"].dt.hour

    # Drop the raw tripduration column since we have duration_min  #[COLUMNS]
    df = df.drop(columns=["tripduration"])

    return df


DRIVE_FILE_ID = "1DLcLOKrPavHxi-4raVqj5Hmjw50Vk19r"
df_all = load_data(DRIVE_FILE_ID)

# Ordered list of days for charts
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# ─────────────────────────────────────────────
#  HELPER FUNCTIONS
# ─────────────────────────────────────────────

# #[FUNC2P] – function with two parameters, one has a default value
def filter_trips(df, user_type="All", max_duration=60):
    """
    Return a filtered copy of df.
    user_type: 'All', 'Subscriber', or 'Customer'
    max_duration: upper limit on trip length in minutes
    """
    # #[FILTER1] – filter by duration
    filtered = df[df["duration_min"] <= max_duration]

    # #[FILTER2] – filter by user type AND duration (two conditions)
    if user_type != "All":
        filtered = filtered[(filtered["duration_min"] <= max_duration) &
                            (filtered["usertype"] == user_type)]
    return filtered


# #[FUNCRETURN2] – returns two values
def get_top_stations(df, n=10):
    """Return the top-n busiest start and end stations as two Series."""
    top_start = df["start station name"].value_counts().head(n)
    top_end   = df["end station name"].value_counts().head(n)
    return top_start, top_end   # returns TWO values


# #[FUNCCALL2] – get_station_summary() is called on Page 2 AND Page 3
def get_station_summary(df):
    """Build a dict summary for a station-level pivot."""
    # #[DICTMETHOD] – using dict .get() and .update() below
    summary = {}
    pivot = df.pivot_table(          # #[PIVOTTABLE]
        index="start station name",
        values=["duration_min"],
        aggfunc={"duration_min": ["mean", "count"]}
    )
    pivot.columns = ["avg_duration_min", "trip_count"]
    pivot = pivot.reset_index()

    # Store the pivot and top-10 in a dict using two dictionary methods
    summary["pivot"] = pivot
    summary.update({"top10": pivot.nlargest(10, "trip_count")})  # .update() is a dict method
    return summary


# #[LAMBDA] – lambda to format duration for display
format_duration = lambda mins: f"{int(mins // 60)}h {int(mins % 60)}m" if mins >= 60 else f"{int(mins)}m"

# ─────────────────────────────────────────────
#  SIDEBAR  #[ST3]
# ─────────────────────────────────────────────
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Bluebikes_logo.svg/320px-Bluebikes_logo.svg.png",
    use_container_width=True,
)
st.sidebar.title("🚲 Blue Bikes Explorer")
st.sidebar.markdown("Explore **September 2020** ride data across Boston.")

# Navigation
page = st.sidebar.radio(
    "Navigate to:",
    ["🏠 Overview", "📊 Station Analysis", "🗺️ Map", "📅 Ride Patterns"],
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Global Filters**")

# #[ST1] – Streamlit dropdown
user_type_choice = st.sidebar.selectbox(
    "User Type",
    options=["All", "Subscriber", "Customer"],
    help="Subscribers have annual memberships; Customers are casual riders.",
)

# #[ST2] – Streamlit slider
max_dur = st.sidebar.slider(
    "Max Trip Duration (minutes)",
    min_value=5,
    max_value=120,
    value=60,
    step=5,
)

# Apply global filters using our function  #[FUNCCALL2]
df = filter_trips(df_all, user_type=user_type_choice, max_duration=max_dur)

st.sidebar.markdown(f"**Showing:** {len(df):,} trips")

# ─────────────────────────────────────────────
#  PAGE 1 – OVERVIEW
# ─────────────────────────────────────────────
if page == "🏠 Overview":
    st.title("🚲 Blue Bikes Boston – September 2020")
    st.markdown(
        """
        Blue Bikes is Boston's public bike-share program. This app explores **307,853 rides**
        taken during September 2020 — a month when the city was still adapting to the pandemic.
        Use the **sidebar** to filter by rider type and trip length, then explore each page.
        """
    )

    # KPI cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Trips", f"{len(df):,}")
    col2.metric("Avg Duration", format_duration(df["duration_min"].mean()))
    col3.metric("Subscribers", f"{(df['usertype'] == 'Subscriber').sum():,}")
    col4.metric("Casual Riders", f"{(df['usertype'] == 'Customer').sum():,}")

    st.markdown("---")

    # #[CHART1] – Bar chart: trips by day of week, custom colors & labels
    st.subheader("📅 Total Trips by Day of Week")
    st.markdown("Which days are Boston cyclists most active?")

    # #[SORT] – sort by a defined day order
    day_counts = df["day_of_week"].value_counts().reindex(DAY_ORDER).fillna(0)

    fig1, ax1 = plt.subplots(figsize=(9, 4))
    colors = ["#1565C0" if d in ["Saturday", "Sunday"] else "#42A5F5" for d in DAY_ORDER]
    bars = ax1.bar(DAY_ORDER, day_counts.values, color=colors, edgecolor="white", linewidth=0.8)

    # Add value labels on top of each bar
    for bar in bars:
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 100,
            f"{int(bar.get_height()):,}",
            ha="center", va="bottom", fontsize=8, color="#333"
        )

    ax1.set_xlabel("Day of Week", fontsize=11)
    ax1.set_ylabel("Number of Trips", fontsize=11)
    ax1.set_title("Blue Bikes Trips by Day of Week – Sept 2020", fontsize=13, fontweight="bold")
    ax1.legend(
        handles=[
            plt.Rectangle((0,0),1,1, color="#42A5F5", label="Weekday"),
            plt.Rectangle((0,0),1,1, color="#1565C0", label="Weekend"),
        ],
        loc="upper right", framealpha=0.8
    )
    ax1.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig1)

    st.markdown(
        "💡 **Takeaway:** Weekday ridership is consistently higher, suggesting most Blue Bikes "
        "users commute to work or school."
    )

# ─────────────────────────────────────────────
#  PAGE 2 – STATION ANALYSIS
# ─────────────────────────────────────────────
elif page == "📊 Station Analysis":
    st.title("📊 Station Analysis")
    st.markdown("Which stations see the most action?")

    # #[FUNCCALL2] – second call to get_station_summary
    summary = get_station_summary(df)

    # #[MAXMIN] – find the station with the most and fewest trips
    busiest = summary["pivot"].loc[summary["pivot"]["trip_count"].idxmax(), "start station name"]
    quietest = summary["pivot"].loc[summary["pivot"]["trip_count"].idxmin(), "start station name"]

    col1, col2 = st.columns(2)
    col1.info(f"🏆 **Busiest start station:** {busiest}")
    col2.info(f"🔇 **Quietest start station:** {quietest}")

    # Top-N selector  #[ST1] already used in sidebar; this is extra UI richness
    n = st.slider("Show top N stations", min_value=5, max_value=20, value=10)

    # #[FUNCCALL2] – calling get_top_stations() here (also called in Map page)
    top_start, top_end = get_top_stations(df, n=n)

    # #[ITERLOOP] – loop through the top stations dict to build label list
    station_labels = []
    for station, count in top_start.items():   # .items() is a dict method  #[DICTMETHOD]
        short = station[:35] + "…" if len(station) > 35 else station
        station_labels.append(short)

    # #[CHART2] – Horizontal bar chart (different type from CHART1)
    st.subheader(f"Top {n} Busiest Start Stations")
    fig2, ax2 = plt.subplots(figsize=(9, n * 0.45 + 1))

    y_pos = range(len(top_start))
    ax2.barh(y_pos, top_start.values, color="#0288D1", edgecolor="white")
    ax2.set_yticks(list(y_pos))
    ax2.set_yticklabels(station_labels, fontsize=9)
    ax2.invert_yaxis()
    ax2.set_xlabel("Number of Trips", fontsize=11)
    ax2.set_title(f"Top {n} Start Stations – Blue Bikes Sept 2020", fontsize=13, fontweight="bold")
    ax2.spines[["top", "right"]].set_visible(False)

    for i, v in enumerate(top_start.values):
        ax2.text(v + 20, i, f"{v:,}", va="center", fontsize=8)

    plt.tight_layout()
    st.pyplot(fig2)

    # Pivot table view
    st.subheader("📋 Station Pivot Table")
    st.markdown("Average trip duration and ride count per start station (top 20 by trip count).")

    # #[LISTCOMP] – list comprehension to format average duration column
    top20 = summary["pivot"].nlargest(20, "trip_count").copy()
    top20["avg_duration_formatted"] = [format_duration(m) for m in top20["avg_duration_min"]]

    display_df = top20[["start station name", "trip_count", "avg_duration_formatted"]].rename(columns={
        "start station name": "Station",
        "trip_count": "Total Trips",
        "avg_duration_formatted": "Avg Duration",
    })
    st.dataframe(display_df.reset_index(drop=True), use_container_width=True)

# ─────────────────────────────────────────────
#  PAGE 3 – MAP
# ─────────────────────────────────────────────
elif page == "🗺️ Map":
    st.title("🗺️ Ride Start Locations")
    st.markdown(
        "Each dot represents a **bike station**. The dot size reflects trip volume; "
        "hover over a dot to see the station name and trip count."
    )

    # #[FUNCCALL2] – third call to get_top_stations (used here for map data)
    top_start, _ = get_top_stations(df, n=200)   # get up to 200 stations for map

    # Build station-level data with lat/lon  #[FILTER2]
    station_df = (
        df[["start station name", "start station latitude", "start station longitude"]]
        .drop_duplicates("start station name")
    )

    # Merge with trip counts
    trip_counts = df["start station name"].value_counts().reset_index()
    trip_counts.columns = ["start station name", "trip_count"]
    map_df = station_df.merge(trip_counts, on="start station name")

    # #[SORT] – sort stations by trip count descending
    map_df = map_df.sort_values("trip_count", ascending=False)

    # Scale radius for visual clarity
    map_df["radius"] = map_df["trip_count"] / map_df["trip_count"].max() * 300 + 50

    # #[MAP] – PyDeck ScatterplotLayer with tooltip
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position=["start station longitude", "start station latitude"],
        get_radius="radius",
        get_fill_color=[2, 136, 209, 180],   # Blue Bikes blue, semi-transparent
        get_line_color=[255, 255, 255],
        line_width_min_pixels=1,
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=42.358,
        longitude=-71.095,
        zoom=12.5,
        pitch=30,
    )

    tooltip = {
        "html": "<b>{start station name}</b><br/>Trips: {trip_count}",
        "style": {"backgroundColor": "steelblue", "color": "white", "padding": "8px"},
    }

    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="mapbox://styles/mapbox/light-v10",
    ))

    st.markdown("---")
    st.subheader("📍 Top 10 Stations Table")

    # #[ITERLOOP] – iterate through top stations to build a display list
    station_list = []
    for rank, (name, count) in enumerate(top_start.head(10).items(), start=1):
        station_list.append({"Rank": rank, "Station": name, "Trips": f"{count:,}"})

    st.table(pd.DataFrame(station_list))

# ─────────────────────────────────────────────
#  PAGE 4 – RIDE PATTERNS
# ─────────────────────────────────────────────
elif page == "📅 Ride Patterns":
    st.title("📅 Ride Patterns by Hour & User Type")
    st.markdown(
        "When do Subscribers (commuters) vs. Customers (casual riders) ride? "
        "Use the filters in the sidebar to explore."
    )

    # Hourly trip counts split by user type
    hourly = (
        df.groupby(["hour", "usertype"])
        .size()
        .reset_index(name="trip_count")
    )

    fig3, ax3 = plt.subplots(figsize=(10, 4))
    colors_map = {"Subscriber": "#1565C0", "Customer": "#EF6C00"}

    # #[ITERLOOP] – loop through user types to plot each line
    for utype, group in hourly.groupby("usertype"):
        ax3.plot(
            group["hour"],
            group["trip_count"],
            marker="o",
            label=utype,
            color=colors_map.get(utype, "gray"),
            linewidth=2,
            markersize=5,
        )

    ax3.set_xticks(range(0, 24))
    ax3.set_xticklabels([f"{h}:00" for h in range(0, 24)], rotation=45, fontsize=8)
    ax3.set_xlabel("Hour of Day", fontsize=11)
    ax3.set_ylabel("Number of Trips", fontsize=11)
    ax3.set_title("Blue Bikes Trips by Hour of Day – Sept 2020", fontsize=13, fontweight="bold")
    ax3.legend(title="User Type", framealpha=0.8)
    ax3.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig3)

    st.markdown(
        "💡 **Takeaway:** Subscribers show clear **rush-hour peaks** at 8 AM and 5–6 PM, "
        "confirming commuter behavior. Casual Customers peak in the afternoon and ride more "
        "evenly throughout the day."
    )

    # Summary stats by user type
    st.subheader("📊 Duration Statistics by User Type")

    # #[DICTMETHOD] – build and access a dict of stats
    stats_dict = {}
    for utype in df["usertype"].unique():
        subset = df[df["usertype"] == utype]["duration_min"]
        stats_dict[utype] = {
            "Mean (min)": round(subset.mean(), 1),
            "Median (min)": round(subset.median(), 1),
            "Max (min)": round(subset.max(), 1),
            "Count": f"{len(subset):,}",
        }

    # #[ITERLOOP] – loop through the stats dict to display  #[DICTMETHOD] – .keys() method
    cols = st.columns(len(stats_dict.keys()))
    for col, (utype, stats) in zip(cols, stats_dict.items()):
        col.markdown(f"**{utype}**")
        for label, val in stats.items():
            col.metric(label, val)

    # #[MAXMIN] – find hour with most rides
    peak_hour = hourly.loc[hourly["trip_count"].idxmax(), "hour"]
    st.info(f"🕐 **Peak hour overall:** {peak_hour}:00 – {peak_hour+1}:00")
