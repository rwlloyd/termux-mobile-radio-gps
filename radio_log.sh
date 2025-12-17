#!/data/data/com.termux/files/usr/bin/bash

OUTFILE="$HOME/storage/downloads/radio_log.csv"
INTERVAL=2   # seconds

# Create CSV header once
if [ ! -f "$OUTFILE" ]; then
  echo "timestamp,lat,lon,accuracy,wifi_rssi,cell_type,cell_dbm,cell_rsrp,cell_rsrq,cell_rssicell_ci,cell_pci,cell_band" >> "$OUTFILE"
fi

echo "[starting logger]"
echo "[warming GPS — this may take up to a minute]"

# --- GPS warm-up ---
until termux-location -p gps -r updates >/dev/null 2>&1; do
  sleep 2
done

while true; do
  TIMESTAMP=$(date -Iseconds)

  # --- GPS: read cached, validated JSON ---
  LOC=$(termux-location -p gps -r last 2>/dev/null)

  if ! echo "$LOC" | jq -e . >/dev/null 2>&1; then
    echo "[waiting for GPS fix]"
    sleep $INTERVAL
    continue
  fi

  LAT=$(echo "$LOC" | jq -r '.latitude')
  LON=$(echo "$LOC" | jq -r '.longitude')
  ACC=$(echo "$LOC" | jq -r '.accuracy')

  # Skip until accuracy is reasonable
  if [ "$ACC" = "null" ] || (( $(echo "$ACC > 100" | bc -l) )); then
    echo "[GPS not locked yet ±${ACC}m]"
    sleep $INTERVAL
    continue
  fi

  # --- Wi-Fi (current connection) ---
  WIFI=$(termux-wifi-connectioninfo 2>/dev/null)
  WIFI_BSSID=$(echo "$WIFI" | jq -r '.bssid')
  WIFI_RSSI=$(echo "$WIFI" | jq -r '.rssi // "NA"')

  # --- Cellular: serving cell only ---
  CELL=$(termux-telephony-cellinfo | jq '.[] | select(.registered==true)' 2>/dev/null)

  CELL_TYPE=$(echo "$CELL" | jq -r '.type // "NA"')
  CELL_DBM=$(echo "$CELL" | jq -r '.dbm // "NA"')
  CELL_RSRP=$(echo "$CELL" | jq -r '.rsrp // "NA"')
  CELL_RSRQ=$(echo "$CELL" | jq -r '.rsrq // "NA"')
  CELL_RSSI=$(echo "$CELL" | jq -r '.rssi')
  CELL_CI=$(echo "$CELL" | jq -r '.ci // "NA"')
  CELL_PCI=$(echo "$CELL" | jq -r '.pci // "NA"')
  CELL_BAND=$(echo "$CELL" | jq -r '.bands[0] // "NA"')

  # --- Write CSV ---
  echo "$TIMESTAMP,$LAT,$LON,$ACC,$WIFI_BSSID,$WIFI_RSSI,$CELL_TYPE,$CELL_DBM,$CELL_RSRP,$CELL_RSRQ,$CELL_RSSI,$CELL_CI,$CELL_PCI,$CELL_BAND" >> "$OUTFILE"

  # --- Terminal feedback ---
  printf "[%s] GPS %.5f,%.5f ±%sm | WiFi %sdBm | LTE RSRP %sdBm (B%s)\n" \
    "$(date +%H:%M:%S)" \
    "$LAT" "$LON" "$ACC" \
    "$WIFI_RSSI" \
    "$CELL_RSRP" \
    "$CELL_BAND"

  sleep $INTERVAL
done
