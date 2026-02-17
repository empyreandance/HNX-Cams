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

DATA_SOURCE = "https://raw.githubusercontent.com/empyreandance/HNX-Cams/main/cctv_hnx.csv"

@st.cache_data(ttl=300)
def load_data():
    return pd.read_csv(DATA_SOURCE)

# Helper: Detect Caltrans District and clean ID for direct video player
def get_video_info(lat, lon, name):
    # Standardize the name into a video ID (strip spaces and special chars)
    cam_id = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
    
    # Logic to assign District based on Hanford CWA geography
    # D10: Merced, Mariposa
    # D06: Fresno, Madera, Kings, Tulare, Western Kern
    # D09: Eastern Kern (Mojave/Tehachapi areas)
    
    if lat > 37.3:
        dist = "d10" # Northern CWA (Mariposa/Merced)
    elif lon > -118.5 and lat < 35.8:
        dist = "d09" # Eastern Kern/Mojave area
    else:
        dist = "d06" # Central Valley core
        
    return f"https://cwwp2.dot.ca.gov/vm/loc/{dist}/{cam_id}.htm"

try:
    df = load_data()
    st.sidebar.title("🛠️ Dashboard Controls")
    search_query = st.sidebar.text_input("Search Camera Name", placeholder="e.g. Tehachapi")
    elev_range = st.sidebar.slider("Elevation Filter (ft)", int(df['elevation'].min()), int(df['elevation'].max()), (int(df['elevation'].min()), int(df['elevation'].max())))

    filtered_df = df[(df['elevation'].between(elev_range[0], elev_range[1])) & (df['name'].str.contains(search_query, case=False))]

    # 2. Map Interface
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

    # 4. Markers & Embedded Video Players
    for _, row in filtered_df.iterrows():
        player_url = get_video_info(row['lat'], row['lon'], row['name'])
        
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
                       🔗 Open Full Player in New Tab
                    </a>
                </div>
            </div>
        '''
        
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
    st.error(f"⚠️ Error: {e}")
