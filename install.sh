#!/bin/bash
set -e

# --- AetherDB Install Script ---
# 1. Creates an executable for AetherDB using PyInstaller.
# 2. Sets up AetherDB as a systemd service.

# Determine the absolute path of the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to create an executable using PyInstaller
create_executable() {
    # Activate the virtual environment
    source "$SCRIPT_DIR/.venv/bin/activate"

    # Install PyInstaller if not already installed
    pip show pyinstaller >/dev/null 2>&1 || pip install pyinstaller

    # Create an executable using PyInstaller
    pyinstaller --onefile --name aetherdb "$SCRIPT_DIR/aetherdb/__main__.py"

    # Move the executable to /usr/local/bin
    sudo mv "$SCRIPT_DIR/dist/aetherdb" /usr/local/bin/aetherdb
    sudo chown root:root /usr/local/bin/aetherdb
    sudo chmod 755 /usr/local/bin/aetherdb

    echo "Created executable: aetherdb (run it from anywhere)"
}

# Function to set up systemd service
setup_systemd_service() {
    # Create systemd service file for AetherDB
    SERVICE_FILE="/etc/systemd/system/aetherdb.service"
    SERVICE_CONTENT="[Unit]
Description=AetherDB Service
After=network.target

[Service]
ExecStart=/usr/local/bin/aetherdb
WorkingDirectory=$SCRIPT_DIR
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
}

# Main script execution
create_executable
setup_systemd_service