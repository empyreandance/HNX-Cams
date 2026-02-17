import pandas as pd
import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# 1. Load Data
df = pd.read_csv("cctv.csv")
df.columns = ['lon', 'lat', 'name', 'description']
total = len(df)

def get_elevation(row):
    try:
        url = f"https://epqs.nationalmap.gov/v1/json?x={row['lon']}&y={row['lat']}&units=Feet&output=json"
        res = requests.get(url, timeout=10).json()
        elev = int(res['value'])
    except:
        elev = 0
    
    # Extract URL using regex
    match = re.search(r'src="([^"]+)"', str(row['description']))
    cam_url = match.group(1) if match else None
    
    return {"index": row.name, "elevation": elev, "cam_url": cam_url}

print(f"🚀 Starting PARALLEL cleanup for {total} locations...")

results = []
# 2. Run in Parallel (10 workers is usually safe for govt APIs)
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(get_elevation, row) for _, row in df.iterrows()]
    
    count = 0
    for future in as_completed(futures):
        results.append(future.result())
        count += 1
        if count % 5 == 0:
            print(f"✅ Processed {count}/{total}...")

# 3. Merge and Save
results_df = pd.DataFrame(results).sort_values("index")
df['elevation'] = results_df['elevation'].values
df['cam_url'] = results_df['cam_url'].values

df.to_csv("cctv_final.csv", index=False)
print("\n🔥 Done! 'cctv_final.csv' is ready. Upload this to Google Sheets now.")