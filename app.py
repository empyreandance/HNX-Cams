import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
import requests
import re

# 1. Setup & Auto-Refresh (Every 5 mins)
st.set_page_config(layout="wide", page_title="Hanford CWA Dashboard")
st_autorefresh(interval=5 * 60 * 1000, key="datarefresh")

# 2. Helper: Get Elevation from USGS
def get_elevation(lat, lon):
    try:
        url = f"https://epqs.nationalmap.gov/v1/json?x={lon}&y={lat}&units=Feet&output=json"
        res = requests.get(url, timeout=5).json()
        return int(res['value'])
    except:
        return 0

# 3. Helper: Extract URL from Messy HTML
def extract_url(html):
    match = re.search(r'src="([^"]+)"', str(html))
    return match.group(1) if match else None

# 4. Load & Process Data
@st.cache_data
def load_and_clean_data():
    df = pd.read_csv("cctv.csv")
    # Identify columns from your screenshot
    df.columns = ['lon', 'lat', 'name', 'description']
    df['cam_url'] = df['description'].apply(extract_url)
    
    # Fetch elevation for each point (cached so it only runs once!)
    with st.spinner("Fetching altitudes for new cameras..."):
        df['elevation'] = df.apply(lambda x: get_elevation(x['lat'], x['lon']), axis=1)
    return df

df = load_and_clean_data()

# 5. Sidebar Filter
st.sidebar.header("Filter by Altitude")
min_e = int(df['elevation'].min())
max_e = int(df['elevation'].max())
elev_range = st.sidebar.slider("Elevation (ft)", min_e, max_e, (min_e, max_e))

# 6. Filter & Display Map
filtered = df[(df['elevation'] >= elev_range[0]) & (df['elevation'] <= elev_range[1])]

st.title(f"HNX CWA Live Feeds: {len(filtered)} active")
m = folium.Map(location=[36.32, -119.64], zoom_start=8, tiles="OpenTopoMap")

for _, row in filtered.iterrows():
    html = f"<b>{row['name']}</b><br>Elev: {row['elevation']}ft<br><img src='{row['cam_url']}' width='300px'>"
    folium.Marker([row['lat'], row['lon']], popup=folium.Popup(html, max_width=350)).add_to(m)

st_folium(m, width=1200, height=650)