#!/usr/bin/env python3
"""Create an interactive heatmap HTML from a radio log CSV.

Reads `radio_log.csv` (or any CSV with the same header) and creates
an interactive Leaflet map saved as HTML using Folium + HeatMap.

Usage examples in README.
"""
import argparse
import os
import webbrowser
import math
import http.server
import socketserver
import pandas as pd
import folium
from folium.plugins import HeatMap


def rssi_to_weight(rssi):
    if pd.isna(rssi):
        return None
    try:
        r = float(rssi)
    except Exception:
        return None
    # Typical RSSI is negative dBm (e.g. -30 good, -120 bad).
    # Map [-120, -30] -> [0.0, 1.0]
    # If value is outside, clamp it.
    w = (r + 120.0) / 90.0
    return max(0.0, min(1.0, w))


def _pick_rssi_columns(df):
    # Return (wifi_col, cell_col) names or (None,None)
    cols = [c.lower() for c in df.columns]
    wifi_col = None
    cell_col = None

    # heuristics for wifi
    for name in df.columns:
        n = name.lower()
        if 'wifi' in n and ('rssi' in n or 'dbm' in n):
            wifi_col = name
            break
    # fallback to any rssi-like column that isn't clearly cell
    if wifi_col is None:
        for name in df.columns:
            n = name.lower()
            if 'rssi' in n and 'cell' not in n:
                wifi_col = name
                break

    # heuristics for cell
    for pref in ('cell_rsrp', 'cell_dbm', 'cell_rssi', 'cell_rssicell_ci', 'cell_rsrq'):
        for name in df.columns:
            if pref in name.lower():
                cell_col = name
                break
        if cell_col:
            break

    # last resort: any numeric column with dBm-like range
    if not wifi_col or not cell_col:
        for name in df.columns:
            if (not wifi_col) and 'wifi' in name.lower():
                wifi_col = wifi_col or name
            if (not cell_col) and 'cell' in name.lower():
                cell_col = cell_col or name

    return wifi_col, cell_col


def _detect_latlon(df):
    # Try common cases, then heuristics.
    # 1) explicit columns
    if 'lat' in df.columns and 'lon' in df.columns:
        lat = pd.to_numeric(df['lat'], errors='coerce')
        lon = pd.to_numeric(df['lon'], errors='coerce')
        if lat.notna().sum() and lon.notna().sum():
            return lat, lon

    # 2) MultiIndex index (timestamp, lat) case observed in radio_log2.csv
    if isinstance(df.index, pd.MultiIndex):
        # try to find a numeric level that looks like latitude
        for lvl in range(df.index.nlevels):
            vals = pd.to_numeric(df.index.get_level_values(lvl), errors='coerce')
            vals_s = pd.Series(vals)
            if vals_s.notna().sum() > 0 and (vals_s.between(-90, 90).mean() > 0.5):
                lat = vals_s
                # find lon in columns: prefer 'lon', else numeric column in -180..180
                if 'lon' in df.columns:
                    num = pd.to_numeric(df['lon'], errors='coerce')
                    num_s = pd.Series(num)
                    if num_s.notna().sum() and (num_s.between(-180, 180).mean() > 0.5):
                        lon = num_s
                    else:
                        lon = None
                elif 'timestamp' in df.columns:
                    maybe = pd.to_numeric(df['timestamp'], errors='coerce')
                    maybe_s = pd.Series(maybe)
                    if maybe_s.notna().sum() and (maybe_s.between(-180, 180).mean() > 0.5):
                        lon = maybe_s
                    else:
                        lon = None
                else:
                    lon = None

                if lon is None:
                    # search for numeric column likely to be lon
                    for name in df.columns:
                        num = pd.to_numeric(df[name], errors='coerce')
                        num_s = pd.Series(num)
                        if num_s.notna().sum() and (num_s.between(-180, 180).mean() > 0.5):
                            lon = num_s
                            break

                if lon is not None:
                    return lat, lon

    # 3) heuristic scan columns for lat/lon ranges
    lat_candidate = None
    lon_candidate = None
    for name in df.columns:
        num = pd.to_numeric(df[name], errors='coerce')
        num_s = pd.Series(num)
        if num_s.notna().sum() == 0:
            continue
        frac_lat = num_s.between(-90, 90).mean()
        frac_lon = num_s.between(-180, 180).mean()
        if frac_lat > 0.6 and lat_candidate is None:
            lat_candidate = num_s
        if frac_lon > 0.6 and lon_candidate is None:
            lon_candidate = num_s
    if lat_candidate is not None and lon_candidate is not None:
        return lat_candidate, lon_candidate

    return None, None


def build_points(df, weight_source):
    # detect lat/lon
    lat_series, lon_series = _detect_latlon(df)
    if lat_series is None or lon_series is None:
        # try simple fallback to columns named 'lat' and 'lon' coerced
        raise RuntimeError("Unable to detect latitude and longitude columns automatically")

    wifi_col, cell_col = _pick_rssi_columns(df)

    points = []
    for i in range(len(df)):
        try:
            lat = float(lat_series.iloc[i])
            lon = float(lon_series.iloc[i])
        except Exception:
            continue
        if math.isnan(lat) or math.isnan(lon):
            continue

        weight = None
        if weight_source == 'wifi':
            if wifi_col in df.columns:
                weight = rssi_to_weight(df[wifi_col].iloc[i])
            if weight is None and cell_col in df.columns:
                weight = rssi_to_weight(df[cell_col].iloc[i])
        elif weight_source == 'cell':
            if cell_col in df.columns:
                weight = rssi_to_weight(df[cell_col].iloc[i])
            if weight is None and wifi_col in df.columns:
                weight = rssi_to_weight(df[wifi_col].iloc[i])
        else:
            weight = 1.0

        if weight is None:
            weight = 0.2

        points.append([lat, lon, float(weight)])

    return points


def create_map(points, out_html, radius=15, blur=15, min_opacity=0.2):
    if not points:
        raise RuntimeError("No valid points to plot")

    # center map on median
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    center = [sum(lats) / len(lats), sum(lons) / len(lons)]

    m = folium.Map(location=center, tiles="OpenStreetMap", zoom_start=15)
    HeatMap(points, radius=radius, blur=blur, min_opacity=min_opacity).add_to(m)
    folium.LayerControl().add_to(m)
    m.save(out_html)


def serve_file(path, port=8000):
    # Serve the directory containing path and open in browser
    directory = os.path.abspath(os.path.dirname(path))
    os.chdir(directory)

    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}/{os.path.basename(path)}"
        print(f"Serving {path} at {url}")
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Stopped server")


def main():
    parser = argparse.ArgumentParser(description="Plot radio_log CSV as a heatmap (interactive HTML)")
    parser.add_argument("--input", "-i", default="radio_log.csv", help="Input CSV file")
    parser.add_argument("--output", "-o", default="radio_heatmap.html", help="Output HTML file")
    parser.add_argument("--weight", "-w", choices=["wifi", "cell", "count"], default="wifi",
                        help="Weight points by 'wifi' RSSI, 'cell' RSSI, or 'count' (uniform)")
    parser.add_argument("--radius", type=int, default=15, help="Heat map radius (pixels)")
    parser.add_argument("--blur", type=int, default=15, help="Heat map blur")
    parser.add_argument("--min-opacity", type=float, default=0.2, help="Heat map min opacity")
    parser.add_argument("--serve", action="store_true", help="Start a local HTTP server and open the map in a browser")
    parser.add_argument("--port", type=int, default=8000, help="Port to serve on when using --serve")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        raise SystemExit(f"Input file not found: {args.input}")

    df = pd.read_csv(args.input)

    points = build_points(df, args.weight)
    create_map(points, args.output, radius=args.radius, blur=args.blur, min_opacity=args.min_opacity)

    print(f"Saved heatmap to {args.output}")

    if args.serve:
        serve_file(args.output, port=args.port)


if __name__ == "__main__":
    main()
