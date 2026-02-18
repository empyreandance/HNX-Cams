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
    if os.path.exists(FILES["Caltrans"]):
        df_cal = pd.read_csv(FILES["Caltrans"])
        df_cal["source"] = "Caltrans"
        dfs.append(df_cal)
    
    if os.path.exists(FILES["ALERTCalifornia"]):
        df_alert = pd.read_csv(FILES["ALERTCalifornia"])
        dfs.append(df_alert)
        
    if not dfs: return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)

def generate_popup_html(group):
    """
    Creates a single HTML popup containing ALL cameras at this location.
    """
    html_content = f'<div style="width:340px; max-height:400px; overflow-y:auto; font-family:sans-serif;">'
    
    # Title (use the first camera's location name generally)
    first_row = group.iloc[0]
    location_title = first_row['name'].split(":")[1].strip() if ":" in first_row['name'] else first_row['name']
    
    html_content += f'<h4 style="margin:0; position:sticky; top:0; background:white; padding:5px 0; border-bottom:2px solid #ccc;">📍 {location_title}</h4>'

    for _, row in group.iterrows():
        name = row['name']
        elev = row['elevation']
        source = row.get('source', 'Caltrans')
        url = str(row['url'])
        
        html_content += f'<div style="margin-top:15px; border-bottom:1px solid #eee; padding-bottom:10px;">'
        html_content += f'<div style="font-weight:bold; color:#005f73; font-size:13px;">📷 {name}</div>'
        html_content += f'<div style="font-size:10px; color:#666; margin-bottom:4px;">Elev: {elev} ft | Src: {source}</div>'

        if source == "Caltrans":
            cam_id = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
            try:
                match = re.search(r'/data/(d\d+)/', url)
                dist = match.group(1) if match else "d06"
            except: dist = "d06"
            player_url = f"https://cwwp2.dot.ca.gov/vm/loc/{dist}/{cam_id}.htm"
            html_content += f'<iframe src="{player_url}" width="100%" height="200" frameborder="0" scrolling="no" style="border-radius:4px; border:1px solid #ccc;"></iframe>'
            html_content += f'<a href="{player_url}" target="_blank" style="display:block; text-align:right; font-size:10px; margin-top:2px;">🔗 Full Player</a>'

        elif source == "ALERTCalifornia":
            html_content += f'<img src="{url}" width="100%" style="border-radius:4px; border:1px solid #ccc;" onerror="this.src=\'https://via.placeholder.com/320x200?text=Feed+Offline\';">'
            html_content += f'<a href="{url}" target="_blank" style="display:block; text-align:right; font-size:10px; margin-top:2px;">🔗 Full Image</a>'
        
        html_content += '</div>'

    html_content += '</div>'
    return html_content

try:
    df = load_data()
    if df.empty:
        st.error("⚠️ No data files found.")
        st.stop()

    st.sidebar.title("🛠️ Dashboard Controls")
    
    # Filters
    st.sidebar.subheader("Filters")
    all_sources = df['source'].unique().tolist()
    selected_sources = st.sidebar.multiselect("Networks", all_sources, default=all_sources)
    
    if 'elev_slider' not in st.session_state:
        st.session_state.elev_slider = (int(df['elevation'].min()), int(df['elevation'].max()))

    elev_range = st.sidebar.slider("Elevation (ft)", int(df['elevation'].min()), int(df['elevation'].max()), key="elev_slider")

    # Filter Data
    filtered_df = df[
        (df['elevation'].between(elev_range[0], elev_range[1])) &
        (df['source'].isin(selected_sources))
    ]

    # --- Map Interface ---
    st.title(f"📡 Hanford CWA Live Feeds")
    st.caption(f"Showing {len(filtered_df)} cameras grouped by location")

    m = folium.Map(location=[36.32, -119.64], zoom_start=7, tiles="OpenTopoMap")
    
    folium.WmsTileLayer(
        url="https://mesonet.agron.iastate.edu/cgi-bin/wms/nexrad/n0q.cgi",
        layers="nexrad-n0q-900913",
        name="Live Radar",
        fmt="image/png",
        transparent=True,
        opacity=0.55
    ).add_to(m)

    # --- GROUPING LOGIC ---
    # Group by Lat/Lon to handle stacked cameras
    # We round to 4 decimals to catch "very close" cameras that should be grouped
    filtered_df['lat_round'] = filtered_df['lat'].round(4)
    filtered_df['lon_round'] = filtered_df['lon'].round(4)
    
    grouped = filtered_df.groupby(['lat_round', 'lon_round'])

    for (lat, lon), group in grouped:
        # Determine marker color (if mixed group, use Purple, otherwise source color)
        sources = group['source'].unique()
        if len(sources) > 1:
            color = "purple" # Mixed location
        elif "Caltrans" in sources:
            color = "#d62828"
        else:
            color = "#005f73"

        # Generate the multi-camera popup
        popup_html = generate_popup_html(group)
        
        # Tooltip shows count if > 1
        count = len(group)
        tooltip_text = f"{group.iloc[0]['name']} ({count} Cams)" if count > 1 else group.iloc[0]['name']

        folium.CircleMarker(
            location=[lat, lon],
            radius=7 if count > 1 else 5,  # Make multi-cam markers slightly bigger
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=360),
            tooltip=tooltip_text
        ).add_to(m)

    st_folium(m, width=1400, height=800)

except Exception as e:
    st.error(f"⚠️ Dashboard error: {e}")
