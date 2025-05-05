"""
Name:       Amelia Benoit
CS230:      CS230-4
Data:       ny housing data
URL:        Link to your web application on Streamlit Cloud (if posted)

Description: This page enables users to filter and search for properties based on specific criteria like price, borough, and room count. A Folium map displays matching properties, and summary statistics offer quick insights.
"""

import streamlit as st
import pandas as pd
import pydeck as pdk
import matplotlib.pyplot as plt

# [ST4] Customized page layout with sidebar and emoji title
st.set_page_config(page_title="Find a Home", page_icon="🏠")


# [PY1] A function with two+ parameters (with default), called twice
@st.cache_data
def load_data(
        file_path="C:/Users/Amelia/OneDrive - Bentley University/Spring 2025 Classes/CS 230/Final Project/nyhouse.csv"):
    try:  # [PY3] Error checking with try/except
        df = pd.read_csv(file_path)
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return pd.DataFrame()

    # [DA1] Clean the data
    df.columns = df.columns.str.strip().str.lower()
    df = df.dropna(subset=["latitude", "longitude", "price", "locality", "beds", "bath", "propertysqft"])

    # Fix united states by pulling city from formatted_address
    mask_us = df["locality"].str.strip().str.lower() == "united states"
    city_from_address = df.loc[mask_us, "formatted_address"].str.split(",").str[1].str.strip().str.lower()
    df.loc[mask_us, "locality"] = city_from_address

    # Standardize locality names and fixing the data
    df["locality"] = df["locality"].str.strip().str.lower()
    df["locality"] = df["locality"].replace({
        "the bronx": "bronx county",
        "bronx": "bronx county",
        "new york": "new york county",
        "nyc": "new york county",
        "queens": "queens county",
        "brooklyn": "brooklyn county",
        "flatbush":"brooklyn county",
        "jamaica": "queens county",
        "staten island": "richmond county"
    })

    # Capitalize locality for display
    df["locality"] = df["locality"].str.title()

    # Convert other columns
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["propertysqft"] = pd.to_numeric(df["propertysqft"], errors="coerce")
    df = df.dropna(subset=["price", "beds", "bath", "propertysqft"])
    df = df[(df["price"] > 1000) & (df["price"] <= 500_000_000)]

    # [DA9] Add new calculated/cleaned columns
    df["price"] = df["price"].astype(int)
    df["beds"] = df["beds"].astype(int)
    df["bath"] = df["bath"].astype(int)
    df["propertysqft"] = df["propertysqft"].astype(int)

    return df

# [PY1] Call with default value
df = load_data()

st.title("🏠 Find Your Ideal Home")

# [ST1], [ST2], [ST3] Three Streamlit widgets: dropdown, sliders
st.sidebar.header("Search Filters")

# [ST1] Dropdown to select area with "Any" option
localities = ["Any"] + sorted(df["locality"].unique())
selected_locality = st.sidebar.selectbox("Select Location (county)", localities)

# Filtering by selected locality
if selected_locality != "Any":
    df = df[df["locality"] == selected_locality]

# [ST3] Text input for keyword (property type)
property_keyword = st.sidebar.text_input("Enter Property Type (Condo, Townhouse, Co-op)", "")

# Bedrooms slider
min_beds = int(df["beds"].min())
max_beds = int(df["beds"].max())

if min_beds < max_beds:
    bedroom = st.sidebar.slider("Minimum Bedrooms", min_value=min_beds, max_value=max_beds, value=min_beds)
else:
    st.sidebar.write(f"Only {min_beds} bedroom(s) available.")
    bedroom = min_beds

# Bathrooms slider
min_bath = int(df["bath"].min())
max_bath = int(df["bath"].max())

if min_bath < max_bath:
    bathroom = st.sidebar.slider("Minimum Bathrooms", min_value=min_bath, max_value=max_bath, value=min_bath)
else:
    st.sidebar.write(f"Only {min_bath} bathroom(s) available.")
    bathroom = min_bath

price_min = int(df["price"].min())
price_max = int(df["price"].max())
price_range = st.sidebar.slider("Price Range ($)", price_min, price_max, (price_min, 5_000_000))

sqft_min = int(df["propertysqft"].min())
sqft_max = int(df["propertysqft"].max())
sqft_range = st.sidebar.slider("Square Footage Range", sqft_min, sqft_max, (sqft_min, 2000))

# [DA5] Filter data using multiple conditions
results = df[
    ((selected_locality == "Any") | (df["locality"] == selected_locality)) &
    (df["beds"] >= bedroom) &
    (df["bath"] >= bathroom) &
    (df["price"] >= price_range[0]) & (df["price"] <= price_range[1]) &
    (df["propertysqft"] >= sqft_range[0]) & (df["propertysqft"] <= sqft_range[1]) &
    ((property_keyword.strip() == "") | (df["type"].str.lower().str.contains(property_keyword.strip().lower())))
]

# [DA2] Sort data by price
results = results.sort_values(by="price")

# [DA3] Show top 5 most expensive listings
top_5 = results.nlargest(5, "price")

# [PY2] Function returning multiple values
def get_top_and_count(df):
    return df.head(5), len(df)

top_rows, count = get_top_and_count(results)

# [PY5] Dictionary usage with keys/values
info = {
    "Total Listings": count,
    "Top Listing Address": top_rows.iloc[0]["formatted_address"] if not top_rows.empty else "N/A",
    "Top Price": top_rows.iloc[0]["price"] if not top_rows.empty else "N/A"
}
for k, v in info.items():
    st.write(f"**{k}**: {v}")

# [DA4] Filter by one condition (already shown: by borough)
st.markdown(f"### 🔍 {count} Matching Listings in {selected_locality}")
st.dataframe(results[["formatted_address", "price", "beds", "bath", "propertysqft", "type"]])

if selected_locality == "Any":
    locality_filter = df["locality"].notnull()  # Accept all valid localities
else:
    locality_filter = df["locality"] == selected_locality

# [DA4], [DA5] Filtering by multiple conditions
filtered_df = df[
    locality_filter &
    (df["price"] >= price_range[0]) &
    (df["price"] <= price_range[1]) &
    (df["type"].str.lower().str.contains(property_keyword.lower()))
]

# [PY4] Categorize listings by price
filtered_df["category"] = ["Luxury" if p > 1_000_000 else "Standard" for p in filtered_df["price"]]

# [CHART2] Scatter Plot (Matplotlib)
st.markdown("### \U0001F50D Property Size vs. Price")
fig2, ax2 = plt.subplots()
# Divide price by 1,000,000 to convert to millions
ax2.scatter(filtered_df["propertysqft"], filtered_df["price"] / 1_000_000, alpha=0.6, color="teal")
ax2.set_title("Property Size vs. Price")
ax2.set_xlabel("Size (sqft)")
ax2.set_ylabel("Price (Millions $)")
ax2.ticklabel_format(style='plain', axis='both')  # Turn off scientific notation
st.pyplot(fig2)


# [MAP] Detailed map with tooltips using PyDeck
if not results.empty:
    st.markdown("### 📍 Map of your Ideal Listings")
    layer = pdk.Layer(
        type="ScatterplotLayer",
        data=results,
        get_position='[longitude, latitude]',
        get_color='[0, 128, 255, 160]',
        get_radius=200,
        pickable=True
    )
    view_state = pdk.ViewState(
        latitude=results["latitude"].mean(),
        longitude=results["longitude"].mean(),
        zoom=10,
        pitch=0
    )
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=view_state,
        layers=[layer],
        tooltip={"text": "{formatted_address}\nPrice: ${price}"}
    ))
else:
    st.warning("No matching properties found. Try adjusting your filters.")

# [PY4] List comprehension example
low_sqft_addresses = [addr for addr in df[df["propertysqft"] < 800]["formatted_address"].head(3)]