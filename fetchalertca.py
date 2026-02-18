import requests
import pandas as pd
import json

# Configuration
API_URL = "https://services8.arcgis.com/X84q166Srnyl4JMV/ArcGIS/rest/services/ALERTCalifornia_Camera_Feed/FeatureServer/0/query"

# Your requested bounds
LAT_MIN, LAT_MAX = 34.75, 38.20
LON_MIN, LON_MAX = -121.20, -117.60

def fetch_alertca_cams():
    print(f"📡 Querying ALERTCalifornia API for bounds: {LAT_MIN},{LON_MIN} to {LAT_MAX},{LON_MAX}...")
    
    params = {
        "f": "json",
        "where": "1=1",
        "outFields": "*",
        "geometry": f"{LON_MIN},{LAT_MIN},{LON_MAX},{LAT_MAX}",
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects",
        "inSR": "4326",
        "outSR": "4326",
        "returnGeometry": "true",
        "resultType": "standard"
    }

    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if "features" not in data or len(data["features"]) == 0:
            print("⚠️ No features found.")
            return

        cams = []
        for feature in data["features"]:
            attr = feature["attributes"]
            geom = feature["geometry"]
            
            # NO JITTER: Use exact coordinates so we can group them later
            row = {
                "lon": geom["x"],
                "lat": geom["y"],
                "name": f"ALERTCA: {attr.get('cameraName') or attr.get('name') or 'Unknown'}",
                "url": attr.get("imageURL") or attr.get("networkURL") or "",
                "elevation": 0, # Will be fixed by clean.py
                "source": "ALERTCalifornia"
            }
            cams.append(row)

        df = pd.DataFrame(cams)
        
        # Save to CSV
        output_file = "cctv_alertca.csv"
        df.to_csv(output_file, index=False)
        print(f"✅ Success! Found {len(df)} cameras. Saved to {output_file} (No Jitter).")
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")

if __name__ == "__main__":
    fetch_alertca_cams()