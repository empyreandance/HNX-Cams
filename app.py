import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# 1. Config & Auto-Refresh (Updates every 5 mins for radar)
st.set_page_config(layout="wide", page_title="HNX Live Feeds", page_icon="📡")
st_autorefresh(interval=5 * 60 * 1000, key="radar_refresh")

DATA_SOURCE = "https://raw.githubusercontent.com/empyreandance/HNX-Cams/main/cctv_hnx.csv"

@st.cache_data(ttl=300)
def load_data():
    return pd.read_csv(DATA_SOURCE)

try:
    df = load_data()
    st.sidebar.title("🛠️ Controls")
    search_query = st.sidebar.text_input("Search Camera", placeholder="e.g. Tehachapi")
    elev_range = st.sidebar.slider("Elevation (ft)", int(df['elevation'].min()), int(df['elevation'].max()), (int(df['elevation'].min()), int(df['elevation'].max())))

    filtered_df = df[(df['elevation'].between(elev_range[0], elev_range[1])) & (df['name'].str.contains(search_query, case=False))]

    # 2. Map Setup
    st.title(f"📡 Hanford CWA Live Feeds ({len(filtered_df)} Cameras)")
    
    # Display Scan Time
    scan_time = datetime.utcnow().strftime('%H:%M UTC')
    st.caption(f"Radar Auto-Refresh Active | Latest Scan approx: {scan_time}")

    m = folium.Map(location=[36.32, -119.64], zoom_start=8, tiles="OpenTopoMap")

    # 3. Radar Layer
    folium.WmsTileLayer(
        url="https://mesonet.agron.iastate.edu/cgi-bin/wms/nexrad/n0q.cgi",
        layers="nexrad-n0q-900913",
        name="Live Radar",
        fmt="image/png",
        transparent=True,
        opacity=0.5,
        control=True
    ).add_to(m)

    for _, row in filtered_df.iterrows():
        # IMPROVED LINK: Direct query for QuickMap
        clean_name = row['name'].split(':')[0].strip() if ':' in row['name'] else row['name']
        live_link = f"https://quickmap.dot.ca.gov/?vcam={clean_name}"
        
        html = f'''
            <div style="width:280px; font-family: sans-serif;">
                <h4 style="margin:0; color: #d62828;">{row['name']}</h4>
                <p style="margin:5px 0; font-size: 12px;">Elev: {row['elevation']} ft</p>
                <img src="{row['url']}" width="100%" style="border-radius:5px;">
                <div style="margin-top: 10px; text-align: center;">
                    <a href="{live_link}" target="_blank" 
                       style="background-color: #d62828; color: white; padding: 6px 12px; 
                       text-decoration: none; border-radius: 15px; font-size: 11px; font-weight: bold;">
                       🎥 OPEN QUICKMAP LIVE
                    </a>
                </div>
            </div>
        '''
        
        # RED CircleMarkers
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=6,
            color="#d62828",  # Red border
            fill=True,
            fill_color="#d62828", # Red fill
            fill_opacity=0.7,
            popup=folium.Popup(html, max_width=300),
            tooltip=row['name']
        ).add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, width=1400, height=800)

except Exception as e:
    st.error(f"Error: {e}")
