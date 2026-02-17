import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration & Auto-Refresh (Every 10 mins)
st.set_page_config(layout="wide", page_title="Hanford CWA Webcam Dashboard", page_icon="📡")
st_autorefresh(interval=10 * 60 * 1000, key="cctv_refresh")

# 2. DATA SOURCE: Pointing to your new Hanford-only CSV
DATA_SOURCE = "https://raw.githubusercontent.com/empyreandance/HNX-Cams/main/cctv_hnx.csv"

@st.cache_data(ttl=600)
def load_data():
    return pd.read_csv(DATA_SOURCE)

try:
    df = load_data()
    
    # 3. Sidebar Search & Filter
    st.sidebar.title("🛠️ Dashboard Controls")
    search_query = st.sidebar.text_input("Search Camera Name", placeholder="e.g. Tehachapi")

    min_e, max_e = int(df['elevation'].min()), int(df['elevation'].max())
    elev_range = st.sidebar.slider("Elevation Filter (ft)", min_e, max_e, (min_e, max_e))

    # 4. Filter Logic
    filtered_df = df[
        (df['elevation'] >= elev_range[0]) & 
        (df['elevation'] <= elev_range[1]) &
        (df['name'].str.contains(search_query, case=False))
    ]

    # 5. Main Map Interface
    st.title(f"🌨️ Hanford CWA Live Feeds ({len(filtered_df)} Cameras)")
    
    # Centers map on the heart of the HNX CWA (Hanford/Visalia area)
    m = folium.Map(
        location=[36.32, -119.64], 
        zoom_start=8, 
        tiles="OpenTopoMap"
    )

    # 6. Add NWS Weather Radar Overlay
    folium.WmsTileLayer(
        url="https://mesonet.agron.iastate.edu/cgi-bin/wms/nexrad/n0q.cgi",
        layers="nexrad-n0q-900913",
        name="Live Radar (NEXRAD)",
        fmt="image/png",
        transparent=True,
        opacity=0.55,
        control=True
    ).add_to(m)

    # 7. Add Camera Markers
    for _, row in filtered_df.iterrows():
        # Dynamic link to the Caltrans Live Player
        live_link = f"https://quickmap.dot.ca.gov/?cms={row['name'].replace(' ', '')}"
        
        html = f'''
            <div style="width:280px; font-family: sans-serif;">
                <h4 style="margin:0 0 5px 0; color: #1f77b4;">{row['name']}</h4>
                <p style="margin:0 0 10px 0; font-size: 13px;">Elevation: <b>{row['elevation']} ft</b></p>
                <img src="{row['url']}" width="100%" style="border-radius:8px; border: 1px solid #ddd;">
                <div style="margin-top: 12px; text-align: center;">
                    <a href="{live_link}" target="_blank" 
                       style="background-color: #d62828; color: white; padding: 8px 15px; 
                       text-decoration: none; border-radius: 20px; font-size: 12px; font-weight: bold; display: inline-block;">
                       🎥 OPEN LIVE STREAM
                    </a>
                </div>
            </div>
        '''
        
        # Using smaller CircleMarkers for professional GIS look
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=6,
            color="#1f77b4",
            fill=True,
            fill_opacity=0.8,
            popup=folium.Popup(html, max_width=300),
            tooltip=f"{row['name']} ({row['elevation']} ft)"
        ).add_to(m)

    # Add Layer Control to toggle Radar on/off
    folium.LayerControl().add_to(m)

    st_folium(m, width=1400, height=800)

except Exception as e:
    st.error(f"⚠️ App is updating or data is missing. Error: {e}")
