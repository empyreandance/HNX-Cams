import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# 1. Config
INPUT_FILE = "cctv_alertca.csv"
OUTPUT_FILE = "cctv_alertca.csv"  # Overwrite with fixed data

# 2. Load Data
print(f"📂 Loading {INPUT_FILE}...")
df = pd.read_csv(INPUT_FILE)
total = len(df)

def get_elevation(row):
    """
    Fetches elevation (in Feet) from USGS National Map API.
    """
    try:
        # USGS EPQS API (Free, no key required)
        url = f"https://epqs.nationalmap.gov/v1/json?x={row['lon']}&y={row['lat']}&units=Feet&output=json"
        res = requests.get(url, timeout=5).json()
        
        # Valid response usually looks like: {'value': '123.45', ...}
        if 'value' in res and res['value'] is not None:
            return {"index": row.name, "elevation": int(float(res['value']))}
    except Exception as e:
        pass # If fail, keep original or 0
    
    return {"index": row.name, "elevation": 0}

print(f"🚀 Starting PARALLEL elevation lookup for {total} locations...")

results = []
# 3. Run in Parallel (10 workers is polite for this API)
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(get_elevation, row) for _, row in df.iterrows()]
    
    count = 0
    for future in as_completed(futures):
        res = future.result()
        results.append(res)
        count += 1
        if count % 10 == 0:
            print(f"   ✅ Processed {count}/{total}...")

# 4. Merge Updates
print("💾 Saving data...")
results_df = pd.DataFrame(results).set_index("index")

# Update only the elevation column in the original dataframe
df.update(results_df)

# 5. Save
df.to_csv(OUTPUT_FILE, index=False)
print(f"\n🔥 Done! Saved accurate elevations to '{OUTPUT_FILE}'.")