
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import itables as show
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm

# Load Under Fives and Malaria Deaths datasets
malaria_df = pd.read_csv("data/malaria_deaths_per_100000_reported.csv").melt(
    id_vars=["country"], var_name="year", value_name="malaria_deaths"
)
u5_total_pop_df = pd.read_csv(
    "data/u5pop.csv"
).melt(id_vars=["country"], var_name="year", value_name="total_pop_under5")

malaria_df

u5_total_pop_df

# Replacing 'k' and 'M' in the Under 5 total population dataset with numeric values
def convert_to_numeric(value):
    if isinstance(value, str):  # Check if the value is a string
        if value.endswith("k"):
            return float(value.replace("k", "")) * 1_000  # Convert 'k' to thousands
        elif value.endswith("M"):
            return float(value.replace("M", "")) * 1_000_000  # Convert 'M' to millions
    return float(value)  # Return as is if no 'k' or 'M'


# Apply the function to the 'total_pop_under5' column
u5_total_pop_df["total_pop_under5"] = u5_total_pop_df["total_pop_under5"].apply(
    convert_to_numeric
)

# Verify the changes
print(u5_total_pop_df.head())

# Cleaning datasets
malaria_df["year"] = pd.to_numeric(malaria_df["year"], errors="coerce")
u5_total_pop_df["year"] = pd.to_numeric(u5_total_pop_df["year"], errors="coerce")
malaria_df["malaria_deaths"] = pd.to_numeric(
    malaria_df["malaria_deaths"], errors="coerce"
)
u5_total_pop_df["total_pop_under5"] = pd.to_numeric(
    u5_total_pop_df["total_pop_under5"], errors="coerce"
)

# Viz 1_Under Five Population Percent Trend

# Selected countries
selected_countries = ["Zambia", "Namibia", "Lao", "Vanuatu", "Cambodia"]
select_countries_under5_pop_df = u5_total_pop_df[
    u5_total_pop_df["country"].isin(selected_countries)
]

# Create a new column to flag projected data (year > 2024)
select_countries_under5_pop_df["is_projected"] = (
    select_countries_under5_pop_df["year"] > 2024
)

# Simulate uncertainty bounds for visualization
select_countries_under5_pop_df["upper_bound"] = select_countries_under5_pop_df[
    "total_pop_under5"
] + np.random.uniform(0.3, 0.7, len(select_countries_under5_pop_df))
select_countries_under5_pop_df["lower_bound"] = select_countries_under5_pop_df[
    "total_pop_under5"
] - np.random.uniform(0.3, 0.7, len(select_countries_under5_pop_df))

# Split historical and projected data
historical_data = select_countries_under5_pop_df[
    ~select_countries_under5_pop_df["is_projected"]
]
projected_data = select_countries_under5_pop_df[
    select_countries_under5_pop_df["is_projected"]
]

# Initialize figure
fig = go.Figure()

# Color palette
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]  # Colors for countries

# Add data for each country
for i, country in enumerate(selected_countries):
    # Filter historical and projected data
    hist_data = historical_data[historical_data["country"] == country]
    proj_data = projected_data[projected_data["country"] == country]

    # Add historical line with ribbon (uncertainty bounds)
    fig.add_trace(
        go.Scatter(
            x=hist_data["year"],
            y=hist_data["total_pop_under5"],
            mode="lines",
            name=f"{country} (Historical)",
            line=dict(color=colors[i], width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=hist_data["year"].tolist() + hist_data["year"].tolist()[::-1],
            y=hist_data["upper_bound"].tolist()
            + hist_data["lower_bound"].tolist()[::-1],
            fill="toself",
            fillcolor=f"rgba{tuple(int(colors[i][j:j+2], 16) for j in (1, 3, 5)) + (0.1,)}",  # Transparent fill
            line=dict(color="rgba(255,255,255,0)"),
            showlegend=False,
        )
    )

    # Add projected trend as a dotted line
    fig.add_trace(
        go.Scatter(
            x=proj_data["year"],
            y=proj_data["total_pop_under5"],
            mode="lines",
            name=f"{country} (Projected)",
            line=dict(color=colors[i], dash="dot", width=3),
        )
    )

# Update layout for aesthetics and adjustments
fig.update_layout(
    title=dict(
        text="Population Under Five Trend with Projections and Uncertainty Bounds",
        font=dict(size=22, color="#2E3B4E"),
        x=0.5,
    ),
    xaxis=dict(
        title="Year",
        tickmode="linear",  # Show years at fixed intervals
        dtick=10,  # Intervals of 10 years
        showgrid=True,
        gridcolor="lightgrey",
    ),
    yaxis=dict(
        title="Percent Population Aged 0-4", showgrid=True, gridcolor="lightgrey"
    ),
    plot_bgcolor="white",
    legend=dict(
        title="Data Type",
        orientation="h",  # Horizontal legend
        x=0.5,  # Center the legend horizontally
        xanchor="center",
        y=-0.35,  # Push legend lower
    ),
    margin=dict(t=80, l=50, r=50, b=120),  # Increased bottom margin for space
)

fig.show()

# Top ten countries based on Under Five population

# Filter for the most recent year with data
latest_year = 2006
latest_data = u5_total_pop_df[u5_total_pop_df["year"] == latest_year]

# Sort and select the top 10 countries by under-five population
top_10_countries = latest_data.nlargest(10, "total_pop_under5")

# Ensure the country order is sorted by total_pop_under5 in descending order
top_10_countries = top_10_countries.sort_values(by="total_pop_under5", ascending=True)

# Format the population values for display
top_10_countries["formatted_population"] = top_10_countries["total_pop_under5"].apply(
    lambda x: f"{x/1e6:.1f}M" if x >= 1e6 else f"{x/1e3:.1f}K"
)

# Create a horizontal bar chart
fig_tp10 = px.bar(
    top_10_countries,
    x="total_pop_under5",
    y="country",
    orientation="h",  # Horizontal orientation
    title=f"Top 10 Countries by Under-Five Population in {latest_year}",
    labels={"total_pop_under5": "Under-Five Population", "country": "Country"},
    text="formatted_population",  # Display values on bars
    color="total_pop_under5",  # Color by population
    color_continuous_scale="Blues",
)

# Update layout for aesthetics
fig_tp10.update_layout(
    xaxis_title="Under-Five Population",
    yaxis_title="Country",
    plot_bgcolor="white",
    title_font=dict(size=20),
    xaxis=dict(showgrid=True, gridcolor="lightgrey"),
    yaxis=dict(showgrid=False),
    margin=dict(t=60, l=150, r=50, b=50),  # Adjust for long country names
)

# Show the chart
fig_tp10.show()

# Value Box Metrics (Under 5 Population)

# Filter for 2006
data_2006 = u5_total_pop_df[u5_total_pop_df["year"] == 2006]

# Global Total Under-Fives in 2006
global_total_under5_2006 = data_2006["total_pop_under5"].sum()

# Country with Highest Under-Fives in 2006
highest_under5_country_2006 = data_2006.sort_values(
    by="total_pop_under5", ascending=False
).iloc[0]
highest_under5_country_name = highest_under5_country_2006["country"]
highest_under5_country_value = highest_under5_country_2006["total_pop_under5"]

# Average Under-Fives Across Countries in 2006
average_under5_2006 = data_2006["total_pop_under5"].mean()

f"{global_total_under5_2006/1e6:.1f}M"
print(highest_under5_country_name)
f"{highest_under5_country_value/1e6:.1f}M"
f"{average_under5_2006/1e6:.1f}M"

# Viz 2_Malaria Mortality Trend

# Selected countries
selected_countries = ["Zambia", "Namibia", "Lao", "Vanuatu", "Cambodia"]
select_countries_malaria_deaths = malaria_df[
    malaria_df["country"].isin(selected_countries)
]

# Stacked Area Chart
malaria_trend_area = px.area(
    select_countries_malaria_deaths,
    x="year",
    y="malaria_deaths",
    color="country",
    title="Malaria Deaths Trend Over Years for Selected Countries",
    line_group="country",
    markers=True,
)

# Update layout for aesthetics
malaria_trend_area.update_layout(
    title=dict(font=dict(size=20, color="#2E3B4E"), x=0.5),
    xaxis=dict(title="Year", tickangle=-45, gridcolor="lightgrey"),
    yaxis=dict(title="Malaria Deaths", gridcolor="lightgrey"),
    plot_bgcolor="#FAFAFA",
    paper_bgcolor="white",
    legend=dict(
        title="Country",
        orientation="h",  # Horizontal legend
        x=0.5,  # Center legend horizontally
        xanchor="center",
        y=-0.35,  # Move legend further down
    ),
    margin=dict(t=70, l=50, r=50, b=100),  # Increased bottom margin to create space
)

malaria_trend_area.show()

# Geographical distribution of Malaria Mortality

# Create an animated choropleth map
malaria_choropleth_animated = px.choropleth(
    malaria_df,
    locations="country",
    locationmode="country names",
    color="malaria_deaths",
    hover_name="country",
    animation_frame="year",  # Add animation by year
    title="Global Malaria Deaths by Country Over Time",
    color_continuous_scale="Blues",
    labels={"malaria_deaths": "Malaria Deaths"},
)

# Update layout for aesthetics
malaria_choropleth_animated.update_layout(
    title=dict(font=dict(size=20, color="#2E3B4E"), x=0.5),
    geo=dict(
        showframe=False,  # Hide map frame
        showcoastlines=True,  # Show coastlines
        coastlinecolor="lightgrey",
        projection_type="natural earth",  # Natural Earth projection
    ),
    margin=dict(t=70, l=50, r=50, b=50),  # Adjust margins for better appearance
)

# Show the map
malaria_choropleth_animated.show()

# Value Box Metrics (Malaria Mortality)

# Country with Highest Malaria Deaths
highest_malaria_country = malaria_df.sort_values(
    by="malaria_deaths", ascending=False
).iloc[0]

# Country with Lowest Malaria Deaths
# Filter out countries with zero malaria deaths
non_zero_malaria_deaths = malaria_df[malaria_df["malaria_deaths"] > 0]

# Find the country with the lowest non-zero malaria deaths
lowest_malaria_country = non_zero_malaria_deaths.sort_values(by="malaria_deaths", ascending=True).iloc[0]

# Extract relevant information
lowest_malaria_country_name = lowest_malaria_country["country"]
lowest_malaria_country_value = lowest_malaria_country["malaria_deaths"]

print(highest_malaria_country)
print(lowest_malaria_country)

# Viz 3_Under Fives vs Malaria Mortality

# Merge datasets on "country" and "year"
merged_df = pd.merge(malaria_df, u5_total_pop_df, on=["country", "year"], how="inner")

# Drop rows with missing values
merged_df = merged_df.dropna(subset=["malaria_deaths", "total_pop_under5"])

# Filter for the range between 1990 and 2006
filtered_df = merged_df[(merged_df["year"] >= 1990) & (merged_df["year"] <= 2006)]

# Calculate 'population_size' for bubble size and scale for visibility
bubble_scaling_factor = 300  # Increase this factor to make bubbles larger
filtered_df["population_size"] = (
    filtered_df["total_pop_under5"] / 1e6 * bubble_scaling_factor
)

# Determine the minimum value for malaria deaths
y_min = filtered_df["malaria_deaths"].min() * 0.9

# Create an animated scatter plot
fig_animated = px.scatter(
    filtered_df,
    x="total_pop_under5",  # X-axis: Total under-five population
    y="malaria_deaths",  # Y-axis: Malaria deaths
    size="population_size",  # Larger bubble sizes
    color="country",  # Unique color for each country
    hover_name="country",  # Show country name on hover
    animation_frame="year",  # Animate by year
    animation_group="country",  # Group by country for smooth transitions
    title="Under-Five Population vs Malaria Deaths (1990-2006)",
    labels={
        "total_pop_under5": "Total Population Under-Five",
        "malaria_deaths": "Malaria Deaths",
        "population_size": "Bubble Size (Scaled)",
    },
    template="plotly_white",
)

# Slow down the animation speed
fig_animated.layout.updatemenus[0].buttons[0].args[1]["frame"][
    "duration"
] = 1500  # 1.5 seconds per frame

# Update layout for improved scaling and readability
fig_animated.update_layout(
    xaxis=dict(
        title="Total Population Under-Five",
        gridcolor="lightgrey",
        range=[
            filtered_df["total_pop_under5"].min() * 0.9,
            filtered_df["total_pop_under5"].max() * 1.1,
        ],
        tickformat=".1s",  # Use shortened notation (e.g., 10M for 10,000,000)
    ),
    yaxis=dict(
        title="Malaria Deaths",
        gridcolor="lightgrey",
        range=[y_min, 100],  # Set maximum to 100
        tickformat=".1s",  # Use shortened notation (e.g., 1K for 1,000)
    ),
    legend=dict(title="Country", orientation="v", y=0.5, x=1.1, xanchor="left"),
    margin=dict(t=70, l=50, r=50, b=50),
    plot_bgcolor="white",
    font=dict(family="Arial", size=12),
)

# Add breaks visually to indicate non-zero start
fig_animated.update_xaxes(
    zeroline=False,  # Remove the zero line
    showspikes=True,
    spikemode="across",
    spikecolor="black",
    spikesnap="cursor",
)
fig_animated.update_yaxes(
    zeroline=False,  # Remove the zero line
    showspikes=True,
    spikemode="across",
    spikecolor="black",
    spikesnap="cursor",
)

# Show the animated chart
fig_animated.show()

# Value Box Metrics (Under 5 Pop vs Malaria Mortality)

# Country with the Highest Malaria Deaths Ratio:
merged_df["malaria_deaths_ratio"] = (
    merged_df["malaria_deaths"] / merged_df["total_pop_under5"]
)
highest_malaria_deaths_ratio = merged_df.loc[merged_df["malaria_deaths_ratio"].idxmax()]
print(highest_malaria_deaths_ratio)

fig.show()

malaria_trend_area.show()

fig_animated.show()