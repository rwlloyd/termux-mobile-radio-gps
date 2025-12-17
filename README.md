# Termux Mobile Radio + GPS — Heatmap

This small project converts Termux radio/GPS CSV logs into interactive heatmaps (Leaflet via Folium).

What this repo contains
- `plot_heatmap.py` — Python script that reads CSV logs and writes an interactive HTML heatmap.
- `requirements.txt` — Python dependencies (`pandas`, `folium`).
- `radio_log.csv`, `radio_log2.csv` — example logs collected from Termux (different layouts).
- `radio_heatmap.html`, `radio2_heatmap.html`, `radio_heatmap_check1.html`, `radio_heatmap_check2.html` — example outputs generated during testing.
- `android-setup.md` — instructions for setting up Termux on Android.
- `make-heatmaps-setup.md` — quick usage notes and examples for generating heatmaps.

Key features
- Automatic detection of latitude/longitude columns, including CSVs where lat or lon appear in the index (as in `radio_log2.csv`).
- Heuristic detection of RSSI-like columns (wifi and cell) and mapping RSSI dBm to heatmap weights.
- CLI options to tune radius, blur, weighting mode, and to serve the output locally.

Quick start (send this to a friend)

1) Create a Python virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Generate a heatmap from the default log (`radio_log.csv`):

```bash
python plot_heatmap.py
# -> radio_heatmap.html
```

3) Generate a heatmap from a second-layout log (`radio_log2.csv`):

```bash
python plot_heatmap.py --input radio_log2.csv --output radio2_heatmap.html
```

4) Serve the generated HTML and open it in the browser:

```bash
python plot_heatmap.py --serve
```

Options of interest
- `--weight wifi|cell|count` — weight by wifi RSSI (default), cell RSSI, or uniform counts.
- `--radius`, `--blur`, `--min-opacity` — visual tuning for the heatmap.
- `--serve --port <n>` — serve the output HTML on localhost and open it automatically.

Links to project notes
- Android / Termux setup: `android-setup.md`
- Heatmap usage and examples: `make-heatmaps-setup.md`

Troubleshooting notes
- If the script fails to detect lat/lon, check the CSV header or attachment format. Logs produced by Termux sometimes shift columns; the script has heuristics but you can open the CSV and confirm the `lat`/`lon` fields.
- If RSSI values are absent, use `--weight count` to plot sample density instead.

If you want, I can add a short `test.sh` that runs the two example commands and produces both HTML files for easy sharing.
