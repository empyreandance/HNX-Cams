import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration & Auto-Refresh (Updates every 10 mins)
st.set_page_config(layout="wide", page_title="Hanford CWA Webcam Dashboard", page_icon="🏔️")
st_autorefresh(interval=10 * 60 * 1000, key="cctv_refresh")

# 2. Data Connection (Your Google Sheet CSV)
DATA_SOURCE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRAewePdABLXrhPZPwsQUqPh6GjHZ8_kgaZM4x367YL5QNv0-w1TViJPWoag4j0sWzCM7VMK-Leuf6A/pub?output=csv"

@st.cache_data(ttl=600)
def load_data():
    # Reading your clean columns: lon, lat, name, url, elevation
    return pd.read_csv(DATA_SOURCE)

# 3. Sidebar Setup (Filters & Search)
st.sidebar.title("🛠️ Dashboard Controls")

try:
    df = load_data()
    
    # Text Search
    search_query = st.sidebar.text_input("Search Camera Name", placeholder="e.g. SR-20")

    # Elevation Slider
    min_e, max_e = int(df['elevation'].min()), int(df['elevation'].max())
    elev_range = st.sidebar.slider("Elevation Filter (ft)", min_e, max_e, (min_e, max_e))

    # 4. Filter Logic
    filtered_df = df[
        (df['elevation'] >= elev_range[0]) & 
        (df['elevation'] <= elev_range[1]) &
        (df['name'].str.contains(search_query, case=False))
    ]

    # 5. Main Map Interface
    st.title(f"📡 Hanford CWA Live Feeds ({len(filtered_df)} active)")
    
    # Centers map based on your actual data points
    m = folium.Map(
        location=[filtered_df['lat'].mean(), filtered_df['lon'].mean()], 
        zoom_start=8, 
        tiles="OpenTopoMap"
    )

    for _, row in filtered_df.iterrows():
        # Using the clean 'url' column for the live image preview
        popup_html = f'''
            <div style="width:300px">
                <h4 style="margin-bottom:5px;">{row['name']}</h4>
                <p style="margin-top:0;">Elevation: <b>{row['elevation']} ft</b></p>
                <img src="{row['url']}" width="100%" style="border-radius:5px;">
                <br><a href="{row['url']}" target="_blank">Open Full Image</a>
            </div>
        '''
        folium.Marker(
            [row['lat'], row['lon']], 
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=row['name']
        ).add_to(m)

    st_folium(m, width=1400, height=800)

except Exception as e:
    st.error(f"⚠️ Unable to load data. Please check your Google Sheet link. Error: {e}")
