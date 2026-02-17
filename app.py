import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="Hanford CWA Webcam Dashboard", page_icon="🏔️")
st_autorefresh(interval=10 * 60 * 1000, key="cctv_refresh")

# 2. DATA SOURCE: Using your GitHub Raw Link
DATA_SOURCE = "https://raw.githubusercontent.com/empyreandance/HNX-Cams/main/cctv_final.csv"

@st.cache_data(ttl=600)
def load_data():
    return pd.read_csv(DATA_SOURCE)

try:
    df = load_data()
    
    # 3. Sidebar Search & Filter
    st.sidebar.title("🛠️ Dashboard Controls")
    search_query = st.sidebar.text_input("Search Camera Name", placeholder="e.g. SR-20")

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
        # Using your clean 'url' column for the live images
        html = f'''
            <div style="width:300px">
                <h4 style="margin-bottom:5px;">{row['name']}</h4>
                <p style="margin-top:0;">Elevation: <b>{row['elevation']} ft</b></p>
                <img src="{row['url']}" width="100%" style="border-radius:5px;">
                <br><a href="{row['url']}" target="_blank" style="font-size:12px;">Open Full Image</a>
            </div>
        '''
        folium.Marker(
            [row['lat'], row['lon']], 
            popup=folium.Popup(html, max_width=350),
            tooltip=row['name']
        ).add_to(m)

    st_folium(m, width=1400, height=800)

except Exception as e:
    st.error(f"Connecting to GitHub data... If this persists, verify cctv_final.csv is in your repo. Error: {e}")
