#!/bin/bash
# Waits for the to-do server, then opens the display full-screen.
for i in $(seq 1 60); do
  curl -s http://localhost:8080/api/state >/dev/null && break
  sleep 1
done
BROWSER=$(command -v chromium-browser || command -v chromium)
exec "$BROWSER" --kiosk --noerrdialogs --disable-infobars --no-first-run \
  --disable-session-crashed-bubble --disable-translate --password-store=basic \
  http://localhost:8080/
