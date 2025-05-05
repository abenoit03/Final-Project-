"""
Name:       Amelia Benoit
CS230:      CS230-4
Data:       ny housing data
URL:        Link to your web application on Streamlit Cloud (if posted)

Description: This page provides interactive visual analysis of NYC housing data using charts and statistical summaries. Users can explore patterns in price, size, borough, and more using Seaborn and other visualization tools.
"""

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import pydeck as pdk
import seaborn as sns
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import os

# [PY3] Error checking with try/except
@st.cache_data
def load_data(file_path="C:/Users/Amelia/OneDrive - Bentley University/Spring 2025 Classes/CS 230/Final Project/nyhouse.csv"):
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return pd.DataFrame()

    df.columns = df.columns.str.strip().str.lower()
    df = df.dropna(subset=["latitude", "longitude", "price", "locality", "beds", "bath", "propertysqft"])

    mask_us = df["locality"].str.strip().str.lower() == "united states"
    city_from_address = df.loc[mask_us, "formatted_address"].str.split(",").str[1].str.strip().str.lower()
    df.loc[mask_us, "locality"] = city_from_address

    df["locality"] = df["locality"].str.strip().str.lower().replace({
        "the bronx": "bronx county",
        "bronx": "bronx county",
        "new york": "new york county",
        "nyc": "new york county",
        "queens": "queens county",
        "brooklyn": "brooklyn county",
        "flatbush": "brooklyn county",
        "jamaica": "queens county",
        "staten island": "richmond county"
    })

    df["locality"] = df["locality"].str.title()
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["propertysqft"] = pd.to_numeric(df["propertysqft"], errors="coerce")
    df = df.dropna(subset=["price", "beds", "bath", "propertysqft"])
    df = df[(df["price"] > 1000) & (df["price"] <= 500_000_000)]

    df["price"] = df["price"].astype(int)
    df["beds"] = df["beds"].astype(int)
    df["bath"] = df["bath"].astype(int)
    df["propertysqft"] = df["propertysqft"].astype(int)

    return df

# Load data
st.set_page_config(page_title="NYC Housing Market Explorer", layout="wide")
df = load_data()

# Sidebar filters
st.sidebar.markdown("## \U0001F3E0 Filter Listings")
selected_area = st.sidebar.selectbox("Choose County", df["locality"].unique())
price_min = int(df["price"].min())
price_max = int(df["price"].max())
price_range = st.sidebar.slider("Price Range ($)", price_min, price_max, (price_min, 5_000_000))
property_keyword = st.sidebar.text_input("Property type (Condo, Townhouse, Co-op)", "Condo")

filtered_df = df[
    (df["locality"] == selected_area) &
    (df["price"] >= price_range[0]) &
    (df["price"] <= price_range[1]) &
    (df["type"].str.lower().str.contains(property_keyword.lower()))
]

filtered_df["category"] = ["Luxury" if p > 1_000_000 else "Standard" for p in filtered_df["price"]]

st.title("\U0001F5FD NYC Housing Market Explorer")
st.markdown(f"### {len(filtered_df)} listings in **{selected_area}** for **{property_keyword.title()}**")
st.divider()

# [CHART1] Histogram
st.markdown("#### \U0001F4C8 Price Distribution")
fig1, ax1 = plt.subplots()
ax1.hist(filtered_df["price"] / 1_000_000, bins=30, color="#5DADE2", edgecolor="white")
ax1.set_title("Price Distribution")
ax1.set_xlabel("Price $ (millions)")
ax1.set_ylabel("Count")
ax1.ticklabel_format(style='plain', axis='both')  # Turn off scientific notation
st.pyplot(fig1)
st.divider()

# [SEA1] barplot
st.markdown("#### \U0001F4CA Average Price by Borough")
avg_price_by_area = filtered_df.groupby("sublocality")["price"].mean().reset_index()
fig3, ax3 = plt.subplots()
sns.barplot(data=avg_price_by_area, x="sublocality", y="price", ax=ax3, palette="coolwarm")
ax3.set_title("Average Price by Borough")
ax3.set_ylabel("Average Price $ (millions)")
ax3.set_xlabel("Borough")
plt.xticks(rotation=45)
st.pyplot(fig3)
st.divider()

# Property Type Pie Chart
if property_keyword.strip() == "":
    st.markdown("#### \U0001F3E2 Property Type Distribution")
    type_counts = filtered_df["type"].value_counts()
    type_total = type_counts.sum()
    grouped_types = {}
    other_count = 0
    for property_type, count in type_counts.items():
        percent = (count / type_total) * 100
        if percent >= 3:
            grouped_types[property_type] = count
        else:
            other_count += count
    if other_count > 0:
        grouped_types["Other"] = other_count

    with st.expander("📋 Listings per Property Type"):
        for k, v in grouped_types.items():
            st.write(f"{k}: {v} listings")

    colors = plt.cm.Set3(range(len(grouped_types)))
    fig4, ax4 = plt.subplots()
    ax4.pie(grouped_types.values(), labels=grouped_types.keys(), autopct='%1.1f%%', startangle=90, colors=colors)
    ax4.set_title("Property Type Distribution")
    ax4.axis('equal')
    st.pyplot(fig4)
else:
    st.markdown("🔍 **Pie chart is hidden when filtering by keyword.**")
st.divider()

# Summary statistics
st.markdown("#### \U0001F4B5 Summary Statistics")
def price_stats(df):
    return df["price"].min(), df["price"].max(), df["price"].mean()
min_price, max_price, avg_price = price_stats(filtered_df)
st.write(f"Min Price: ${min_price:,}")
st.write(f"Max Price: ${max_price:,}")
st.write(f"Average Price: ${int(avg_price):,}")
st.divider()

# Listings per Borough
borough_counts = {area: len(df[df["locality"] == area]) for area in df["locality"].unique()}
with st.expander("📋 Listings per Borough"):
    for area, count in borough_counts.items():
        st.write(f"{area}: {count} listings")
st.divider()

# [FOLIUM1] Clustered Map
st.markdown("#### \U0001F5FA Clustered Listing Map")
map2 = folium.Map(location=[filtered_df["latitude"].mean(), filtered_df["longitude"].mean()], zoom_start=11)
marker_cluster = MarkerCluster().add_to(map2)
for idx, row in filtered_df.iterrows():
    color = "darkred" if row["category"] == "Luxury" else "green"
    folium.Marker(
        location=[row["latitude"], row["longitude"]],
        popup=f"{row['formatted_address']}<br>Price: ${row['price']:,}",
        icon=folium.Icon(color=color, icon="home")
    ).add_to(marker_cluster)
st_folium(map2, width=700, height=450)
