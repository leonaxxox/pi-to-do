#!/bin/bash
# Sets Pi To-Do to start automatically. Run once: bash install.sh
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
chmod +x "$DIR/start-kiosk.sh"

sudo tee /etc/systemd/system/pi-todo.service >/dev/null <<EOF
[Unit]
Description=Pi To-Do server
After=network-online.target
Wants=network-online.target

[Service]
User=$USER
WorkingDirectory=$DIR
ExecStart=/usr/bin/python3 $DIR/server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now pi-todo.service

mkdir -p "$HOME/.config/autostart"
cat > "$HOME/.config/autostart/pi-todo.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Pi To-Do
Exec=$DIR/start-kiosk.sh
EOF

echo ""
echo "All set ♡  Restart the Pi with:  sudo reboot"
