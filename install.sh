#!/bin/bash
# BlackHat Educational Firmware Installation Script
# For Raspberry Pi Zero 2 W with Waveshare 1.3" LCD
# Optimized for Raspberry Pi OS 32-bit

set -e

echo "=================================="
echo "BlackHat Educational Firmware Setup"
echo "=================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 
   exit 1
fi

# Detect architecture
ARCH=$(uname -m)
echo "Detected architecture: $ARCH"

if [[ "$ARCH" == "armv7l" || "$ARCH" == "armv6l" ]]; then
    echo "Optimizing for 32-bit ARM architecture..."
    ARM32=true
else
    echo "Warning: This script is optimized for 32-bit ARM (Pi Zero 2W)"
    ARM32=false
fi

# Update system
echo "Updating system packages..."
apt update && apt upgrade -y

# Install required system packages
echo "Installing system dependencies..."
apt install -y \
    python3-pip \
    python3-dev \
    python3-setuptools \
    python3-wheel \
    python3-numpy \
    python3-pil \
    git \
    i2c-tools \
    wireless-tools \
    aircrack-ng \
    bluetooth \
    bluez \
    bluez-tools \
    hostapd \
    dnsmasq \
    tcpdump \
    nmap \
    build-essential \
    cmake \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7 \
    libtiff6-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev

# Enable SPI and I2C
echo "Enabling SPI and I2C..."
raspi-config nonint do_spi 0
raspi-config nonint do_i2c 0

# Install Python packages
echo "Installing Python dependencies..."
pip3 install --upgrade pip

# Install display libraries
pip3 install \
    ST7789 \
    luma.core \
    luma.oled \
    RPi.GPIO \
    spidev \
    pillow \
    numpy

# Install wireless tools
pip3 install \
    scapy \
    wifi \
    bluetooth-utils

# Create project directory
PROJECT_DIR="/opt/blackhat"
echo "Creating project directory: $PROJECT_DIR"
mkdir -p $PROJECT_DIR
mkdir -p $PROJECT_DIR/logs
mkdir -p $PROJECT_DIR/captures
mkdir -p $PROJECT_DIR/configs

# Copy main firmware (assuming it's in current directory)
if [ -f "blackhat.py" ]; then
    cp blackhat.py $PROJECT_DIR/
    chmod +x $PROJECT_DIR/blackhat.py
else
    echo "Warning: blackhat.py not found in current directory"
    echo "Please ensure the main system file is named 'blackhat.py'"
fi

# Create systemd service
echo "Creating systemd service..."
cat > /etc/systemd/system/blackhat.service << 'EOF'
[Unit]
Description=BlackHat Educational Firmware
After=multi-user.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/blackhat
ExecStart=/usr/bin/python3 /opt/blackhat/blackhat.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/blackhat
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create configuration file
echo "Creating configuration file..."
cat > $PROJECT_DIR/configs/blackhat.conf << 'EOF'
# BlackHat Configuration File

[display]
width = 240
height = 240
rotation = 0
backlight = 13

[gpio]
btn_up = 5
btn_down = 6
btn_left = 16
btn_right = 24
btn_select = 12
btn_back = 20

[network]
default_interface = wlan0
monitor_interface = wlan0mon
ap_ssid = BlackHat-Educational
ap_password = educational123

[security]
enable_deauth = false
enable_jamming = false
log_captures = true

[system]
auto_start = true
boot_splash = true
splash_duration = 3
arch = armv7l
EOF

# Create boot splash image directory
mkdir -p $PROJECT_DIR/images
echo "Boot splash image directory created at $PROJECT_DIR/images"
echo "Place your custom boot image (240x240 PNG) as 'boot_splash.png' in this directory"

# Set permissions
chown -R root:root $PROJECT_DIR
chmod -R 755 $PROJECT_DIR

# Configure WiFi monitor mode support
echo "Configuring WiFi for monitor mode..."
# Add monitor mode script
cat > $PROJECT_DIR/enable_monitor.sh << 'EOF'
#!/bin/bash
# Enable monitor mode on wlan0
sudo airmon-ng check kill
sudo airmon-ng start wlan0
EOF
chmod +x $PROJECT_DIR/enable_monitor.sh

# Create disable monitor mode script
cat > $PROJECT_DIR/disable_monitor.sh << 'EOF'
#!/bin/bash
# Disable monitor mode
sudo airmon-ng stop wlan0mon
sudo systemctl start NetworkManager 2>/dev/null || true
sudo systemctl start wpa_supplicant 2>/dev/null || true
EOF
chmod +x $PROJECT_DIR/disable_monitor.sh

# Configure Bluetooth
echo "Configuring Bluetooth..."
systemctl enable bluetooth
systemctl start bluetooth

# Configure hostapd for AP mode
echo "Configuring hostapd..."
cat > /etc/hostapd/hostapd.conf << 'EOF'
interface=wlan0
driver=nl80211
ssid=BlackHat-Educational
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=educational123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Configure dnsmasq for AP mode
echo "Configuring dnsmasq..."
cat > /etc/dnsmasq.d/blackhat.conf << 'EOF'
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
EOF

# Create helper scripts
echo "Creating helper scripts..."

# WiFi AP start script
cat > $PROJECT_DIR/start_ap.sh << 'EOF'
#!/bin/bash
# Start Access Point mode
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq

sudo ifconfig wlan0 192.168.4.1 netmask 255.255.255.0
sudo systemctl start hostapd
sudo systemctl start dnsmasq

echo "Access Point started: BlackHat-Educational"
echo "Password: educational123"
echo "Gateway: 192.168.4.1"
EOF
chmod +x $PROJECT_DIR/start_ap.sh

# WiFi AP stop script
cat > $PROJECT_DIR/stop_ap.sh << 'EOF'
#!/bin/bash
# Stop Access Point mode
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
sudo dhcpcd wlan0
echo "Access Point stopped"
EOF
chmod +x $PROJECT_DIR/stop_ap.sh

# Create logs rotation
echo "Setting up log rotation..."
cat > /etc/logrotate.d/blackhat << 'EOF'
/opt/blackhat/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF

# Enable and start the service
echo "Enabling BlackHat service..."
systemctl daemon-reload
systemctl enable blackhat.service

# Create desktop shortcut (if desktop environment is present)
if [ -d "/home/pi/Desktop" ]; then
    echo "Creating desktop shortcut..."
    cat > /home/pi/Desktop/BlackHat.desktop << 'EOF'
[Desktop Entry]
Name=BlackHat Firmware
Comment=Educational Hacking Device Interface
Exec=sudo python3 /opt/blackhat/blackhat.py
Icon=/opt/blackhat/images/icon.png
Terminal=true
Type=Application
Categories=Education;Development;
EOF
    chmod +x /home/pi/Desktop/BlackHat.desktop
    chown pi:pi /home/pi/Desktop/BlackHat.desktop
fi

# Create uninstall script
cat > $PROJECT_DIR/uninstall.sh << 'EOF'
#!/bin/bash
# Uninstall BlackHat firmware
echo "Uninstalling BlackHat firmware..."
sudo systemctl stop blackhat.service 2>/dev/null || true
sudo systemctl disable blackhat.service 2>/dev/null || true
sudo rm -f /etc/systemd/system/blackhat.service
sudo systemctl daemon-reload
sudo rm -rf /opt/blackhat
sudo rm -f /etc/logrotate.d/blackhat
sudo rm -f /home/pi/Desktop/BlackHat.desktop
echo "BlackHat firmware uninstalled"
EOF
chmod +x $PROJECT_DIR/uninstall.sh

echo ""
echo "=================================="
echo "Installation Complete!"
echo "=================================="
echo ""
echo "BlackHat Educational Firmware has been installed to: $PROJECT_DIR"
echo "Main system file: $PROJECT_DIR/blackhat.py"
echo ""
echo "Configuration:"
echo "- Service: systemctl status blackhat"
echo "- Logs: journalctl -u blackhat -f"
echo "- Config: $PROJECT_DIR/configs/blackhat.conf"
echo "- Main file: $PROJECT_DIR/blackhat.py"
echo ""
echo "Important Notes:"
echo "1. Place your boot splash image (240x240 PNG) at:"
echo "   $PROJECT_DIR/images/boot_splash.png"
echo ""
echo "2. The firmware will start automatically on boot"
echo "   To start manually: sudo systemctl start blackhat"
echo ""
echo "3. For WiFi pentesting features:"
echo "   - Run: sudo $PROJECT_DIR/enable_monitor.sh"
echo "   - Use responsibly and only on owned networks!"
echo ""
echo "4. Hardware connections for buttons:"
echo "   - UP: GPIO 5     - DOWN: GPIO 6"
echo "   - LEFT: GPIO 16  - RIGHT: GPIO 24"
echo "   - SELECT: GPIO 12 - BACK: GPIO 20"
echo ""
echo "5. Default Access Point:"
echo "   - SSID: BlackHat-Educational"
echo "   - Password: educational123"
echo ""
echo "6. Architecture detected: $ARCH (32-bit ARM optimized)"
echo ""
echo "WARNING: This firmware is for EDUCATIONAL PURPOSES ONLY!"
echo "Only use on networks and devices you own or have permission to test."
echo ""
echo "Reboot to start the firmware automatically:"
echo "sudo reboot"
echo ""
EOF
