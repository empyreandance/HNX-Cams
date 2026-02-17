import pandas as pd

# 1. Define Precise Hanford CWA Boundaries
# These coordinates cover the HNX footprint from Yosemite to the Tehachapis
LAT_MIN, LAT_MAX = 34.75, 38.20
LON_MIN, LON_MAX = -121.20, -117.60

# 2. Load your already-fetched data
try:
    df = pd.read_csv("cctv_final.csv")
    print(f"📖 Loaded {len(df)} total California cameras.")
except FileNotFoundError:
    print("❌ Error: Could not find 'cctv_final.csv' in this folder.")
    exit()

# 3. Apply the Hanford Filter
hnx_df = df[
    (df['lat'].between(LAT_MIN, LAT_MAX)) & 
    (df['lon'].between(LON_MIN, LON_MAX))
].copy()

# 4. Save the new, lightweight file
hnx_df.to_csv("cctv_hnx.csv", index=False)

print(f"✅ Success! Filtered down to {len(hnx_df)} Hanford CWA cameras.")
print("🚀 Next: Upload 'cctv_hnx.csv' to GitHub.")