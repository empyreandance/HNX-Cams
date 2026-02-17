import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import re

# 1. Config & Auto-Refresh (Updates every 5 mins for radar sync)
st.set_page_config(layout="wide", page_title="HNX Live Feeds", page_icon="📡")
st_autorefresh(interval=5 * 60 * 1000, key="radar_refresh")

# Use your GitHub Raw Link
DATA_SOURCE = "https://raw.githubusercontent.com/empyreandance/HNX-Cams/main/cctv_hnx.csv"

@st.cache_data(ttl=300)
def load_data():
    return pd.read_csv(DATA_SOURCE)

# Helper: Extract District and ID directly from the data
def get_video_info(row):
    # 1. Clean the name to create the player ID (e.g., '35ebsr140mariposa')
    cam_id = re.sub(r'[^a-zA-Z0-9]', '', str(row['name'])).lower()
    
    # 2. Extract District from the existing URL
    # Example URL: https://cwwp2.dot.ca.gov/data/d10/cctv/...
    # We look for the 'd' followed by numbers between slashes
    try:
        match = re.search(r'/data/(d\d+)/', str(row['url']))
        dist = match.group(1) if match else "d06" 
    except:
        dist = "d06" # Default fallback
        
    return f"https://cwwp2.dot.ca.gov/vm/loc/{dist}/{cam_id}.htm"

try:
    df = load_data()
    st.sidebar.title("🛠️ Dashboard Controls")
    
    # Search and Elevation Filters
    search_query = st.sidebar.text_input("Search Camera Name", placeholder="e.g. Mariposa")
    min_elev = int(df['elevation'].min())
    max_elev = int(df['elevation'].max())
    elev_range = st.sidebar.slider("Elevation Filter (ft)", min_elev, max_elev, (min_elev, max_elev))

    # Apply Filters
    filtered_df = df[
        (df['elevation'].between(elev_range[0], elev_range[1])) & 
        (df['name'].str.contains(search_query, case=False))
    ]

    # 2. Map Interface Header
    st.title(f"📡 Hanford CWA Live Feeds ({len(filtered_df)} Cameras)")
    
    # Display UTC Scan Time for Radar
    scan_time = datetime.utcnow().strftime('%H:%M UTC')
    st.caption(f"Radar Auto-Refresh Active | Current UTC: {scan_time}")

    m = folium.Map(location=[36.32, -119.64], zoom_start=8, tiles="OpenTopoMap")

    # 3. Live Radar Layer (NWS Reflectivity)
    folium.WmsTileLayer(
        url="https://mesonet.agron.iastate.edu/cgi-bin/wms/nexrad/n0q.cgi",
        layers="nexrad-n0q-900913",
        name="Live Radar",
        fmt="image/png",
        transparent=True,
        opacity=0.55,
        control=True
    ).add_to(m)

    # 4. Markers & Integrated Video Players
    for _, row in filtered_df.iterrows():
        # Get the targeted player URL
        player_url = get_video_info(row)
        
        # HTML Popup with IFrame and fallback link
        html = f'''
            <div style="width:320px; font-family: sans-serif;">
                <h4 style="margin:0; color: #d62828;">{row['name']}</h4>
                <p style="margin:5px 0; font-size: 11px;">Elevation: <b>{row['elevation']} ft</b></p>
                
                <iframe src="{player_url}" width="320" height="260" 
                        frameborder="0" scrolling="no" style="border-radius:8px; border:1px solid #ccc;">
                </iframe>
                
                <div style="margin-top: 10px; text-align: center;">
                    <a href="{player_url}" target="_blank" 
                       style="color: #d62828; font-size: 11px; font-weight: bold; text-decoration: none;">
                       🔗 Open Full Player
                    </a>
                    <span style="color: #ccc; margin: 0 5px;">|</span>
                    <a href="https://quickmap.dot.ca.gov/" target="_blank" 
                       style="color: #666; font-size: 11px; text-decoration: none;">
                       🌍 QuickMap
                    </a>
                </div>
            </div>
        '''
        
        # Red CircleMarkers for high contrast
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=6,
            color="#d62828",
            fill=True,
            fill_color="#d62828",
            fill_opacity=0.8,
            popup=folium.Popup(html, max_width=350),
            tooltip=f"{row['name']} ({row['elevation']} ft)"
        ).add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, width=1400, height=800)

except Exception as e:
    st.error(f"⚠️ Dashboard error: {e}")
