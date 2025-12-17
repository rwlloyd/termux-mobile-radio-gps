#!/data/data/com.termux/files/usr/bin/bash

OUTFILE="radio_log.csv"

# Create CSV header if file doesn't exist
if [ ! -f "$OUTFILE" ]; then
  echo "timestamp,lat,lon,accuracy,wifi_ssid,wifi_bssid,wifi_rssi,cell_type,cell_rssi,cell_id" >> "$OUTFILE"
fi

while true; do
  TIMESTAMP=$(date -Iseconds)

  # -------- GPS --------
  LOC=$(termux-location -p gps -r last)
  LAT=$(echo "$LOC" | jq -r '.latitude')
  LON=$(echo "$LOC" | jq -r '.longitude')
  ACC=$(echo "$LOC" | jq -r '.accuracy')

  # -------- WIFI --------
  WIFI=$(termux-wifi-connectioninfo)
  WIFI_SSID=$(echo "$WIFI" | jq -r '.ssid')
  WIFI_BSSID=$(echo "$WIFI" | jq -r '.bssid')
  WIFI_RSSI=$(echo "$WIFI" | jq -r '.rssi')

  # -------- CELL --------
  CELL=$(termux-telephony-cellinfo | jq '.[] | select(.registered==true)')

  CELL_TYPE=$(echo "$CELL" | jq -r '.type')
  CELL_DBM=$(echo "$CELL" | jq -r '.dbm')
  CELL_RSRP=$(echo "$CELL" | jq -r '.rsrp')
  CELL_RSRQ=$(echo "$CELL" | jq -r '.rsrq')
  CELL_RSSI=$(echo "$CELL" | jq -r '.rssi')
  CELL_CI=$(echo "$CELL" | jq -r '.ci')
  CELL_PCI=$(echo "$CELL" | jq -r '.pci')
  CELL_BAND=$(echo "$CELL" | jq -r '.bands[0]') 
  # -------- WRITE CSV --------
  echo "$TIMESTAMP,$LAT,$LON,$ACC,$WIFI_SSID,$WIFI_BSSID,$WIFI_RSSI,$CELL_TYPE,$CELL_RSSI,$CELL_CI" >> "$OUTFILE"

  # -------- TERMINAL FEEDBACK --------
  printf "[%s] GPS: %s,%s ±%sm | WiFi: %sdBm | Cell: %sdBm\r\n" \
  "$(date +%H:%M:%S)" \
  "${LAT:-NA}" "${LON:-NA}" "${ACC:-NA}" \
  "${WIFI_RSSI:-NA}" \
  "${CELL_RSSI:-NA}"
  sleep 1
done
