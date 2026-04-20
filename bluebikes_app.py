"""
Name: Joao Pereira
Class: CS230-2
Data: Blue Bikes Boston Trips from September 2020
URL: "https://cs230-final-project-bluebikes.streamlit.app/"

Description:
This program looks at Blue Bikes trip data from September 2020 in Boston.
I wanted to show how people were using the bike-share system during the
pandemic, and whether commuters and casual riders behaved differently.
The app lets users filter trips by rider type and duration, see which
stations are the busiest, check out an interactive map of ride locations,
and explore when during the day people tend to ride.

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

# Google Drive file ID for the dataset (202009-bluebikes-tripdata.csv)
DRIVE_FILE_ID = "1fUkI9iB7Q-5SyB5XaEnZuI8VtHqD-Wor"

# Days in correct order for charts
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


#  DATA LOADING

@st.cache_data
def load_data(file_id):
    """Load the Blue Bikes CSV from Google Drive and add useful columns."""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"

    # Read CSV with latin-1 encoding to handle special characters in station names
    df = pd.read_csv(url, encoding="latin-1")

    # Convert trip duration from seconds to minutes  #[COLUMNS]
    df["duration_min"] = df["tripduration"] / 60

    # Parse the starttime column – format="mixed" handles slight variations in the timestamps  #[COLUMNS]
    df["starttime"] = pd.to_datetime(df["starttime"], errors="coerce")
    df = df.dropna(subset=["starttime"])

    # Pull out day of week and hour so we can group by them later  #[COLUMNS]
    df["day_of_week"] = df["starttime"].dt.day_name()
    df["hour"] = df["starttime"].dt.hour

    # Drop the original seconds column since we now have duration_min  #[COLUMNS]
    df = df.drop(columns=["tripduration"])

    return df


#  HELPER FUNCTIONS

# #[FUNC2P] – two parameters, max_duration has a default value
def filter_trips(df, user_type="All", max_duration=60):
    """
    Filter the dataframe by user type and max trip duration.
    user_type: 'All', 'Subscriber', or 'Customer'
    max_duration: longest trip to include, in minutes (default 60)
    """
    # #[FILTER1] – single condition: filter out trips longer than the slider value
    filtered = df[df["duration_min"] <= max_duration]

    # #[FILTER2] – two conditions combined with AND: duration AND user type
    if user_type != "All":
        filtered = filtered[
            (filtered["duration_min"] <= max_duration) &
            (filtered["usertype"] == user_type)
        ]
    return filtered


# #[FUNCRETURN2] – this function returns two separate values at once
def get_top_stations(df, n=10):
    """Return the top-n busiest start stations and end stations."""
    top_start = df["start station name"].value_counts().head(n)
    top_end   = df["end station name"].value_counts().head(n)
    return top_start, top_end


# #[FUNCCALL2] – get_station_summary() gets called on the Station page and the Map page
def get_station_summary(df):
    """
    Build a pivot table of trips and average duration per start station.
    Returns a dictionary with the full pivot and the top 10 stations.
    """
    summary = {}

    # #[PIVOTTABLE] – pivot table showing mean duration and trip count per station
    pivot = df.pivot_table(
        index="start station name",
        values=["duration_min"],
        aggfunc={"duration_min": ["mean", "count"]}
    )
    pivot.columns = ["avg_duration_min", "trip_count"]
    pivot = pivot.reset_index()

    # #[DICTMETHOD] – using two dict methods: direct assignment and .update()
    summary["pivot"] = pivot
    summary.update({"top10": pivot.nlargest(10, "trip_count")})
    return summary


# #[LAMBDA] – quick lambda to turn a number of minutes into a readable string
format_duration = lambda mins: f"{int(mins // 60)}h {int(mins % 60)}m" if mins >= 60 else f"{int(mins)}m"


#  PAGE FUNCTIONS

def show_overview(df):
    """Show the Overview page with cards and a bar chart by day of week."""
    st.title("Blue Bikes Trips Data Explorer")
    st.write(
        "Blue Bikes is Boston's public bike-share program. "
        "This app looks at rides taken during September 2020, when the city was still "
        "figuring out how to get around during the pandemic. "
        "You can use the sidebar to filter by rider type and trip length."
    )

    # Four summary numbers at the top
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Trips", f"{len(df):,}")
    col2.metric("Avg Duration", format_duration(df["duration_min"].mean()))
    col3.metric("Subscribers", f"{(df['usertype'] == 'Subscriber').sum():,}")
    col4.metric("Casual Riders", f"{(df['usertype'] == 'Customer').sum():,}")

    st.markdown("---")

    # #[CHART1] – vertical bar chart with custom colors, labels, and legend
    st.subheader("Trips by Day of the Week")
    st.write("I wanted to know if people would ride more on weekdays or weekends. The following graph shows the results I found.")

    # #[SORT] – reindex by DAY_ORDER to get Mon-Sun left to right
    day_counts = df["day_of_week"].value_counts().reindex(DAY_ORDER).fillna(0)

    fig1, ax1 = plt.subplots(figsize=(9, 4))
    colors = ["#2196F3" if d not in ["Saturday", "Sunday"] else "#0D47A1" for d in DAY_ORDER]
    bars = ax1.bar(DAY_ORDER, day_counts.values, color=colors, edgecolor="white", width=0.6)

    for bar in bars:
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 200,
            f"{int(bar.get_height()):,}",
            ha="center", va="bottom", fontsize=8
        )

    ax1.set_xlabel("Day of Week")
    ax1.set_ylabel("Number of Trips")
    ax1.set_title("Blue Bikes – Trips by Day of Week (Sept 2020)", fontweight="bold")
    ax1.legend(handles=[
        plt.Rectangle((0, 0), 1, 1, color="#2196F3", label="Weekday"),
        plt.Rectangle((0, 0), 1, 1, color="#0D47A1", label="Weekend"),
    ], loc="upper right")
    ax1.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig1)

    st.write(
        "On average, people tended to ride more during the weekend than on weekdays, which surprised me since a big portion of riders must need to  "
        "bike to commute to work or school."
    )

    st.markdown("---")

    # #[CHART2] Pie chart: Subscriber vs Customer split
    st.subheader("Rider Type Split")
    st.write("How does the overall split between subscribers and casual riders look?")

    subscriber_count = (df["usertype"] == "Subscriber").sum()
    customer_count = (df["usertype"] == "Customer").sum()

    fig5, ax5 = plt.subplots(figsize=(3.5, 3.5))
    ax5.pie(
        [subscriber_count, customer_count],
        labels=["Subscriber", "Customer"],
        colors=["#1565C0", "#E65100"],
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 2},
    )
    ax5.set_title("Subscriber vs. Customer Split – Sept 2020", fontweight="bold")
    st.pyplot(fig5)

    st.write(
        f"Out of {len(df):,} trips, {subscriber_count:,} were made by subscribers "
        f"and {customer_count:,} by casual customers. "
        "Subscribers make up the large majority of rides."
    )
    
    st.markdown("---")

    # #[CHART3] – Grouped bar chart: Subscriber vs Customer trips by day of week
    st.subheader("Subscribers vs. Casual Riders by Day of Week")
    st.write("I wanted to see whether the weekday vs weekend pattern was different for commuters and casual riders.")

    sub_counts = df[df["usertype"] == "Subscriber"]["day_of_week"].value_counts().reindex(DAY_ORDER).fillna(0)
    cus_counts = df[df["usertype"] == "Customer"]["day_of_week"].value_counts().reindex(DAY_ORDER).fillna(0)

    x = range(len(DAY_ORDER))
    width = 0.4

    fig4, ax4 = plt.subplots(figsize=(10, 4))
    bars1 = ax4.bar([i - width/2 for i in x], sub_counts.values, width=width, label="Subscriber", color="#1565C0", edgecolor="white")
    bars2 = ax4.bar([i + width/2 for i in x], cus_counts.values, width=width, label="Customer", color="#E65100", edgecolor="white")

    ax4.set_xticks(list(x))
    ax4.set_xticklabels(DAY_ORDER)
    ax4.set_xlabel("Day of Week")
    ax4.set_ylabel("Number of Trips")
    ax4.set_title("Subscriber vs. Customer Trips by Day – Sept 2020", fontweight="bold")
    ax4.legend(title="Rider Type")
    ax4.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig4)

    st.write(
    "Subscribers ride more heavily on weekdays, which confirms commuter behavior. "
    "Casual customers peak on weekends, therefore suggesting recreational use."
)


def show_stations(df):
    """Show the Station Analysis page with charts and a pivot table."""
    st.title("Station Analysis")
    st.write("Which stations do people start and end their rides at the most?")

    # #[FUNCCALL2] – first call to get_station_summary
    summary = get_station_summary(df)

    # #[MAXMIN] – find the busiest and quietest stations
    trip_counts = df["start station name"].value_counts()
    busiest  = trip_counts.idxmax()
    quietest = trip_counts.idxmin()

    col1, col2 = st.columns(2)
    col1.success(f"Busiest: {busiest}")
    col2.info(f"Least busy: {quietest}")

    n = st.slider("Select how many stations you want the graph to show:", min_value=5, max_value=20, value=10)

    # #[FUNCCALL2] – calling get_top_stations here
    top_start, top_end = get_top_stations(df, n=n)

    # #[ITERLOOP] – loop through station names to shorten them for the chart
    # #[DICTMETHOD] – .items() lets us get both key and value from the Series
    station_labels = []
    for station, count in top_start.items():
        short = station[:35] + "..." if len(station) > 35 else station
        station_labels.append(short)

    # #[CHART2] – horizontal bar chart
    st.subheader(f"Top {n} Start Stations")
    fig2, ax2 = plt.subplots(figsize=(9, n * 0.5 + 1))
    y_pos = range(len(top_start))
    ax2.barh(y_pos, top_start.values, color="#1565C0", edgecolor="white")
    ax2.set_yticks(list(y_pos))
    ax2.set_yticklabels(station_labels, fontsize=9)
    ax2.invert_yaxis()
    ax2.set_xlabel("Number of Trips")
    ax2.set_title(f"Top {n} Busiest Start Stations – Sept 2020", fontweight="bold")
    ax2.spines[["top", "right"]].set_visible(False)
    for i, v in enumerate(top_start.values):
        ax2.text(v + 10, i, f"{v:,}", va="center", fontsize=8)
    plt.tight_layout()
    st.pyplot(fig2)


def show_map(df):
    """Show the PyDeck map of station locations."""
    st.title("Map of Ride Start Locations")
    st.write(
        "Each dot is a Blue Bikes station. "
        "Scroll around to see the station name and trip count."
    )

    # #[FUNCCALL2] – calling get_top_stations again (map page)
    top_start, _ = get_top_stations(df, n=300)

    # Get unique stations with their coordinates
    station_df = (
        df[["start station name", "start station latitude", "start station longitude"]]
        .drop_duplicates("start station name")
    )

    # Count trips per station and merge with coordinates
    trip_counts = df["start station name"].value_counts().reset_index()
    trip_counts.columns = ["start station name", "trip_count"]
    map_df = station_df.merge(trip_counts, on="start station name")

    # #[SORT] – sort by trip count so busiest stations render on top
    map_df = map_df.sort_values("trip_count", ascending=False)

    # Scale dot size based on trip volume
    map_df["radius"] = map_df["trip_count"] / map_df["trip_count"].max() * 2000 + 500

    # #[MAP] – PyDeck ScatterplotLayer, pickable so tooltip shows on hover
    # #[MAP] – PyDeck ScatterplotLayer with tooltip
    map_df = map_df.dropna(subset=["start station latitude", "start station longitude"])

    st.pydeck_chart(pdk.Deck(
        map_style="road",
        initial_view_state=pdk.ViewState(
            latitude=42.358,
            longitude=-71.095,
            zoom=11,
            pitch=45,
        ),
        layers=[
            pdk.Layer(
                "ColumnLayer",
                data=map_df,
                get_position=["start station longitude", "start station latitude"],
                get_elevation="trip_count",
                elevation_scale=0.5,
                radius=100,
                get_fill_color=[21, 101, 192, 200],
                pickable=True,
                auto_highlight=True,
            )
        ],
        tooltip={"text": "{start station name}\nTrips: {trip_count}"},
    ))

def show_patterns(df):
    """Show hourly ride patterns split by user type."""
    st.title("When Do People Ride?")
    st.write(
        "This page breaks down rides by hour of the day for subscribers vs. casual customers. "
        "I expected subscribers to show commute peaks and customers to be more spread out."
    )

    hourly = (
        df.groupby(["hour", "usertype"])
        .size()
        .reset_index(name="trip_count")
    )

    fig3, ax3 = plt.subplots(figsize=(10, 4))
    color_map = {"Subscriber": "#1565C0", "Customer": "#E65100"}

    # #[ITERLOOP] – loop through each user type to draw its line on the chart
    for utype, group in hourly.groupby("usertype"):
        ax3.plot(
            group["hour"],
            group["trip_count"],
            marker="o",
            label=utype,
            color=color_map.get(utype, "gray"),
            linewidth=2,
            markersize=4,
        )

    ax3.set_xticks(range(0, 24))
    ax3.set_xticklabels([f"{h}:00" for h in range(0, 24)], rotation=45, fontsize=8)
    ax3.set_xlabel("Hour of Day")
    ax3.set_ylabel("Number of Trips")
    ax3.set_title("Trips by Hour of Day – Subscribers vs. Customers", fontweight="bold")
    ax3.legend(title="Rider Type")
    ax3.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig3)

    st.write(
        "Subscribers have clear spikes around 8 AM and 5-6 PM, which are common commute times. "
        "Customers are more active in the afternoon with no real commute pattern, "
        "which lines up with them being recreational or tourist riders."
    )

    # Stats table per user type
    st.subheader("Trip Duration by Rider Type")

    # #[DICTMETHOD] – building a dict and using .keys() and .items() to loop through it
    stats_dict = {}
    for utype in df["usertype"].unique():
        subset = df[df["usertype"] == utype]["duration_min"]
        stats_dict[utype] = {
            "Mean (min)": round(subset.mean(), 1),
            "Median (min)": round(subset.median(), 1),
            "Max (min)": round(subset.max(), 1),
            "Total Rides": f"{len(subset):,}",
        }

    cols = st.columns(len(stats_dict.keys()))
    for col, (utype, stats) in zip(cols, stats_dict.items()):
        col.markdown(f"**{utype}**")
        for label, val in stats.items():
            col.metric(label, val)

    # #[MAXMIN]
    peak_hour = hourly.loc[hourly["trip_count"].idxmax(), "hour"]
    st.info(f"Peak hour overall: {peak_hour}:00 – {peak_hour + 1}:00")


def show_data_explorer(df):
    """Data Explorer page with a pivot table of stations and their average trip duration."""
    st.title("Data Explorer")
    st.write(
        "This page shows every Blue Bikes station along with the average trip duration "
        "for rides that started there, sorted alphabetically. "
        "You may use the sidebar filters to explore how different riders' types or trip lengths "
        "affect the averages."
    )

    # #[PIVOTTABLE] – pivot table of average duration per station from raw data
    st.subheader("Average Trip Duration per Station")
    st.write("Stations are listed in alphabetical order.")

    pivot = df.groupby("start station name")["duration_min"].mean().reset_index()
    pivot.columns = ["Station", "Avg Duration (min)"]

    # #[SORT] – sort alphabetically by station name
    pivot = pivot.sort_values("Station", ascending=True).reset_index(drop=True)

    # #[LISTCOMP] – format the duration column using list comprehension
    pivot["Avg Duration"] = [format_duration(m) for m in pivot["Avg Duration (min)"]]

    # Drop the raw minutes column, only show formatted duration
    pivot = pivot.drop(columns=["Avg Duration (min)"])

    # Set index to start at 1
    pivot.index = range(1, len(pivot) + 1)

    st.dataframe(pivot, use_container_width=True, height=500)

    st.markdown(f"Showing **{len(pivot)}** stations total.")


def main():
    """Main function – sets up the page, sidebar, loads data, and routes to pages."""

    st.set_page_config(
        page_title="Blue Bikes Explorer",
        page_icon="🚲",
        layout="wide",
    )

    # #[ST3] – sidebar with logo, navigation radio buttons, and global filters
    st.sidebar.markdown("""
        <div style='text-align: center; padding: 10px;'>
            <h1 style='color: #1565C0; font-size: 28px;'>🚲 Blue Bikes</h1>
            <p style='color: #555; font-size: 14px;'>Boston Bike Share Explorer</p>
        </div>
    """, unsafe_allow_html=True)
    st.sidebar.write("September 2020 ride data from Boston.")

    page = st.sidebar.radio(
        "Navigate to:",
        ["Overview", "Station Analysis", "Map", "Ride Patterns", "Data Explorer"],
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Filters**")

    # #[ST1] – dropdown to filter by rider type
    user_type_choice = st.sidebar.selectbox(
        "Rider Type",
        options=["All", "Subscriber", "Customer"],
        help="Subscribers have annual memberships. Customers are one-time or casual riders.",
    )

    # #[ST2] – slider to filter by max trip length
    max_dur = st.sidebar.slider(
        "Max Trip Duration (minutes)",
        min_value=5,
        max_value=120,
        value=60,
        step=5,
    )

    # Load data and apply filters
    df_all = load_data(DRIVE_FILE_ID)
    df = filter_trips(df_all, user_type=user_type_choice, max_duration=max_dur)

    st.sidebar.markdown(f"Showing **{len(df):,}** trips")

    # Route to the correct page based on sidebar selection
    if page == "Overview":
        show_overview(df)
    elif page == "Station Analysis":
        show_stations(df)
    elif page == "Map":
        show_map(df)
    elif page == "Ride Patterns":
        show_patterns(df)
    elif page == "Data Explorer":
        show_data_explorer(df)

if __name__ == "__main__":
    main()
