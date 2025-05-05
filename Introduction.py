"""
Name:       Amelia Benoit
CS230:      CS230-4
Data:       ny housing data
URL:        Link to your web application on Streamlit Cloud (if posted)

Description: This home page introduces the NYC Housing Market Explorer app, outlining its purpose and features. It provides an overview of the dataset and includes general insights into the NYC housing market.
"""

import streamlit as st
import pydeck as pdk

st.set_page_config(
    page_title="NYC Housing Market Explorer",
    page_icon="🏠",
)

st.write("# Welcome to the NYC Housing Market Data! 🏙️")

st.sidebar.success("Select a page above.")

st.markdown(
    """
This interactive app allows you to explore residential real estate listings across New York City's five boroughs using real-world housing market data.

Whether you're a curious resident, potential homebuyer, or data enthusiast, this tool helps you:

🔍 Filter listings by borough, price range, and property type

📊 Visualize trends like price distribution and property type composition

🌆 View maps showing property locations, prices, and density

🧮 Compare average prices across neighborhoods and boroughs

The goal is to make NYC's complex housing data more accessible, visual, and interactive. This will help you uncover insights about real estate in one of the world's most dynamic markets.
    """
)
# [PY3] [DA1] Error checking with try/except
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
df = load_data()

# [Map] 3D
st.markdown("#### 🗺️ 3D Map of Property Prices")
column_layer = pdk.Layer(
    "ColumnLayer",
    data=df,
    get_position='[longitude, latitude]',
    get_elevation='price',
    elevation_scale=0.0005,
    radius=100,
    get_fill_color='[180, 0, 200, 140]',
    pickable=True,
    auto_highlight=True,
)
view_state = pdk.ViewState(
    latitude=df["latitude"].mean(),
    longitude=df["longitude"].mean(),
    zoom=10,
    pitch=50,
    bearing=0
)
st.pydeck_chart(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state=view_state,
    layers=[column_layer],
    tooltip={"text": "{formatted_address}\nPrice: ${price}"}
))
