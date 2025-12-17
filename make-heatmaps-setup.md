# Radio log heatmap

This repository contains a small script `plot_heatmap.py` that reads a Termux radio log CSV (header: `timestamp,lat,lon,accuracy,wifi_ssid,wifi_bssid,wifi_rssi,cell_type,cell_rssi,cell_id`) and produces an interactive heatmap saved as an HTML file using Folium.

Quick start

1. Install the requirements in a virtualenv (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Generate the heatmap HTML (defaults to `radio_log.csv` input and `radio_heatmap.html` output):

```bash
python plot_heatmap.py
```

3. Choose weight source (how point intensity is computed):

- `--weight wifi` (default) — weight by `wifi_rssi` (falls back to `cell_rssi`)
- `--weight cell` — weight by `cell_rssi` (falls back to `wifi_rssi`)
- `--weight count` — uniform weight for each sample

Example (use cell RSSI and custom radius):

```bash
python plot_heatmap.py --input radio_log.csv --output mymap.html --weight cell --radius 20
```

4. Serve the generated HTML and open it in a browser:

```bash
python plot_heatmap.py --serve
```

This starts a simple local HTTP server and opens the HTML in your default browser.

Notes

- The script maps RSSI (dBm) values to weights: -30 dBm becomes weight ~1.0, -120 dBm becomes ~0.0.
- Rows with missing or invalid lat/lon are skipped.
- The output HTML is fully interactive (Leaflet) and can be opened directly.
