import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import re
import os

# 1. Config & Auto-Refresh
st.set_page_config(layout="wide", page_title="HNX Live Feeds", page_icon="📡")
st_autorefresh(interval=5 * 60 * 1000, key="radar_refresh")

# File Paths
FILES = {
    "Caltrans": "cctv_hnx.csv",
    "ALERTCalifornia": "cctv_alertca.csv"
}

@st.cache_data(ttl=300)
def load_data():
    dfs = []
    
    # Load Caltrans Data (Original)
    if os.path.exists(FILES["Caltrans"]):
        df_cal = pd.read_csv(FILES["Caltrans"])
        df_cal["source"] = "Caltrans" # Tag original data
        dfs.append(df_cal)
    
    # Load ALERTCalifornia Data (New)
    if os.path.exists(FILES["ALERTCalifornia"]):
        df_alert = pd.read_csv(FILES["ALERTCalifornia"])
        dfs.append(df_alert)
        
    if not dfs:
        return pd.DataFrame()
        
    return pd.concat(dfs, ignore_index=True)

def get_player_html(row):
    """
    Generates the HTML for the popup based on the camera source.
    """
    name = row['name']
    elev = row['elevation']
    source = row.get('source', 'Caltrans')
    url = str(row['url'])

    # --- Caltrans Logic (Iframe Player) ---
    if source == "Caltrans":
        cam_id = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
        try:
            match = re.search(r'/data/(d\d+)/', url)
            dist = match.group(1) if match else "d06"
        except:
            dist = "d06"
        
        player_url = f"https://cwwp2.dot.ca.gov/vm/loc/{dist}/{cam_id}.htm"
        
        return f'''
            <div style="width:320px; font-family: sans-serif;">
                <h4 style="margin:0; color: #d62828;">{name}</h4>
                <p style="margin:5px 0; font-size: 11px;">Source: Caltrans | Elev: <b>{elev} ft</b></p>
                <iframe src="{player_url}" width="320" height="260" frameborder="0" scrolling="no" style="border-radius:8px; border:1px solid #ccc;"></iframe>
                <div style="margin-top: 10px; text-align: center;">
                    <a href="{player_url}" target="_blank" style="color: #d62828; font-size: 11px; font-weight: bold; text-decoration: none;">🔗 Open Full Player</a>
                </div>
            </div>
        '''

    # --- ALERTCalifornia Logic (Direct Image/Stream) ---
    elif source == "ALERTCalifornia":
        # ALERTCalifornia URLs in the API are often direct images or m3u8 streams.
        # For simplicity in Folium popups, we usually display the latest image.
        # If the URL implies a stream (rare in the public CSV output), we link to it.
        
        return f'''
            <div style="width:320px; font-family: sans-serif;">
                <h4 style="margin:0; color: #005f73;">{name}</h4>
                <p style="margin:5px 0; font-size: 11px;">Source: ALERTCalifornia | Elev: <b>{elev} ft</b></p>
                <img src="{url}" width="320" style="border-radius:8px; border:1px solid #ccc;" onerror="this.onerror=null; this.src='https://via.placeholder.com/320x200?text=Feed+Offline';">
                <div style="margin-top: 10px; text-align: center;">
                    <a href="{url}" target="_blank" style="color: #005f73; font-size: 11px; font-weight: bold; text-decoration: none;">🔗 Open Full Feed</a>
                </div>
                <p style="font-size:9px; color:#666; margin-top:5px;"><i>Data Courtesy: ALERTCalifornia & UCSD</i></p>
            </div>
        '''
    return ""

try:
    df = load_data()
    
    if df.empty:
        st.error("⚠️ No data files found. Please ensure 'cctv_hnx.csv' and 'cctv_alertca.csv' are in the directory.")
        st.stop()

    st.sidebar.title("🛠️ Dashboard Controls")
    
    # Source Filter
    st.sidebar.subheader("Filter by Source")
    all_sources = df['source'].unique().tolist()
    selected_sources = st.sidebar.multiselect("Select Networks", all_sources, default=all_sources)
    
    # Elevation Filter
    st.sidebar.subheader("Elevation Filter")
    if 'elev_slider' not in st.session_state:
        st.session_state.elev_slider = (int(df['elevation'].min()), int(df['elevation'].max()))

    col1, col2 = st.sidebar.columns(2)
    presets = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000]
    for i, p in enumerate(presets):
        target_col = col1 if i % 2 == 0 else col2
        if target_col.button(f"{p:,}+ ft", key=f"fixed_btn_{p}"):
            st.session_state.elev_slider = (p, int(df['elevation'].max()))

    if st.sidebar.button("🔄 Reset to All", key="fixed_btn_reset"):
        st.session_state.elev_slider = (int(df['elevation'].min()), int(df['elevation'].max()))

    elev_range = st.sidebar.slider(
        "Range (ft)", 
        int(df['elevation'].min()), 
        int(df['elevation'].max()), 
        key="elev_slider"
    )

    # Apply Filters
    filtered_df = df[
        (df['elevation'].between(elev_range[0], elev_range[1])) &
        (df['source'].isin(selected_sources))
    ]

    # --- Map Interface ---
    st.title(f"📡 Hanford CWA Live Feeds ({len(filtered_df)} Cameras)")
    scan_time = datetime.utcnow().strftime('%H:%M UTC')
    st.caption(f"Sources: {', '.join(selected_sources)} | Radar Active | UTC: {scan_time}")

    m = folium.Map(location=[36.32, -119.64], zoom_start=7, tiles="OpenTopoMap")

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

    # Add Markers
    for _, row in filtered_df.iterrows():
        html = get_player_html(row)
        
        # Color code markers by source
        marker_color = "#d62828" if row['source'] == "Caltrans" else "#005f73"
        
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=6, 
            color=marker_color, 
            fill=True, 
            fill_color=marker_color, 
            fill_opacity=0.8,
            popup=folium.Popup(html, max_width=350),
            tooltip=f"{row['name']} ({row['elevation']} ft)"
        ).add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, width=1400, height=800)

except Exception as e:
    st.error(f"⚠️ Dashboard error: {e}")
