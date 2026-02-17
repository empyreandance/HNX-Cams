import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import re

# 1. Config & Auto-Refresh
st.set_page_config(layout="wide", page_title="HNX Live Feeds", page_icon="📡")
st_autorefresh(interval=5 * 60 * 1000, key="radar_refresh")

DATA_SOURCE = "https://raw.githubusercontent.com/empyreandance/HNX-Cams/main/cctv_hnx.csv"

@st.cache_data(ttl=300)
def load_data():
    return pd.read_csv(DATA_SOURCE)

def get_video_info(row):
    cam_id = re.sub(r'[^a-zA-Z0-9]', '', str(row['name'])).lower()
    try:
        match = re.search(r'/data/(d\d+)/', str(row['url']))
        dist = match.group(1) if match else "d06" 
    except:
        dist = "d06"
    return f"https://cwwp2.dot.ca.gov/vm/loc/{dist}/{cam_id}.htm"

try:
    df = load_data()
    st.sidebar.title("🛠️ Dashboard Controls")
    
    # --- Quick Elevation Presets (Modified for Force Refresh) ---
    st.sidebar.subheader("Quick Elevation Filter")
    
    if 'elev_slider' not in st.session_state:
        st.session_state.elev_slider = (int(df['elevation'].min()), int(df['elevation'].max()))

    col1, col2 = st.sidebar.columns(2)
    # Using a list of tuples to be absolutely explicit with the labels
    presets = [
        (1000, "> 1000 ft"), (2000, "> 2000 ft"), 
        (3000, "> 3000 ft"), (4000, "> 4000 ft"), 
        (5000, "> 5000 ft"), (6000, "> 6000 ft"), 
        (7000, "> 7000 ft"), (8000, "> 8000 ft")
    ]
    
    for i, (val, label) in enumerate(presets):
        target_col = col1 if i % 2 == 0 else col2
        # Adding 'v2' to the key forces Streamlit to treat this as a brand-new UI element
        if target_col.button(label, key=f"btn_v2_{val}"):
            st.session_state.elev_slider = (val, int(df['elevation'].max()))

    if st.sidebar.button("🔄 Reset to All", key="btn_v2_reset"):
        st.session_state.elev_slider = (int(df['elevation'].min()), int(df['elevation'].max()))

    st.sidebar.markdown("---")

    elev_range = st.sidebar.slider(
        "Manual Elevation Filter (ft)", 
        int(df['elevation'].min()), 
        int(df['elevation'].max()), 
        key="elev_slider"
    )

    filtered_df = df[df['elevation'].between(elev_range[0], elev_range[1])]

    # --- Map Interface ---
    st.title(f"📡 Hanford CWA Live Feeds ({len(filtered_df)} Cameras)")
    scan_time = datetime.utcnow().strftime('%H:%M UTC')
    st.caption(f"Radar Auto-Refresh Active | Current UTC: {scan_time}")

    m = folium.Map(location=[36.32, -119.64], zoom_start=8, tiles="OpenTopoMap")

    # Radar Layer
    folium.WmsTileLayer(
        url="https://mesonet.agron.iastate.edu/cgi-bin/wms/nexrad/n0q.cgi",
        layers="nexrad-n0q-900913",
        name="Live Radar",
        fmt="image/png",
        transparent=True,
        opacity=0.55,
        control=True
    ).add_to(m)

    for _, row in filtered_df.iterrows():
        player_url = get_video_info(row)
        html = f'''
            <div style="width:320px; font-family: sans-serif;">
                <h4 style="margin:0; color: #d62828;">{row['name']}</h4>
                <p style="margin:5px 0; font-size: 11px;">Elevation: <b>{row['elevation']} ft</b></p>
                <iframe src="{player_url}" width="320" height="260" frameborder="0" scrolling="no" style="border-radius:8px; border:1px solid #ccc;"></iframe>
                <div style="margin-top: 10px; text-align: center;">
                    <a href="{player_url}" target="_blank" style="color: #d62828; font-size: 11px; font-weight: bold; text-decoration: none;">🔗 Open Full Player</a>
                </div>
            </div>
        '''
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=6, color="#d62828", fill=True, fill_color="#d62828", fill_opacity=0.8,
            popup=folium.Popup(html, max_width=350),
            tooltip=f"{row['name']} ({row['elevation']} ft)"
        ).add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, width=1400, height=800)

except Exception as e:
    st.error(f"⚠️ Dashboard error: {e}")
