#!/bin/bash
set -e

# --- AetherDB Install Script ---
# 1. Creates virtual environment, installs requirements.
# 2. Installs system command 'aetherdb' (calls 'python -m aetherdb').
# 3. Sets up AetherDB as a systemd service.

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Please install Python 3." >&2
  exit 1
fi

if ! command -v pip3 >/dev/null 2>&1; then
  echo "pip3 is required. Please install pip for Python 3." >&2
  exit 1
fi

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo 'Installing global "aetherdb" command...'
CLI_SCRIPT="#!/bin/bash\nDIR=\"$(cd \"$(dirname \"$0\")\" && pwd)\"\nsource \"$DIR/.venv/bin/activate\"\npython -m aetherdb \"$@\"\n"
echo -e "$CLI_SCRIPT" > aetherdb_launcher_tmp.sh
chmod +x aetherdb_launcher_tmp.sh
if sudo cp aetherdb_launcher_tmp.sh /usr/local/bin/aetherdb 2>/dev/null; then
    echo "Created system command: aetherdb (run it from anywhere)"
else
    echo "Could not create /usr/local/bin/aetherdb (need sudo). Please copy 'aetherdb_launcher_tmp.sh' to a directory on your PATH."
fi
rm -f aetherdb_launcher_tmp.sh

# Create systemd service file for AetherDB
SERVICE_FILE="/etc/systemd/system/aetherdb.service"
SERVICE_CONTENT="[Unit]
Description=AetherDB Service
After=network.target

[Service]
ExecStart=/usr/local/bin/aetherdb
WorkingDirectory=/chemin/absolu/vers/aetherdb
StandardOutput=inherit
StandardError=inherit
Restart=always
User=$(whoami)

[Install]
WantedBy=multi-user.target"

echo "$SERVICE_CONTENT" | sudo tee $SERVICE_FILE > /dev/null

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the AetherDB service to start on boot
sudo systemctl enable aetherdb

# Start the AetherDB service
sudo systemctl start aetherdb

echo "\nInstall complete. AetherDB is now set up as a systemd service."
echo "You can manage the service with:"
echo "  sudo systemctl {start,stop,restart,status} aetherdb"
echo "Or, run AetherDB manually with:"
echo "  aetherdb"
echo "or, inside your project, you can always run:"
echo "  python -m aetherdb"