# BlackHat Educational Firmware

An educational hacking firmware for Raspberry Pi Zero 2 W inspired by M5StickC's Bruce firmware and Flipper Zero. This firmware provides a comprehensive penetration testing and security research platform with an intuitive menu-driven interface.

**Optimized for Raspberry Pi OS 32-bit**

## ⚠️ IMPORTANT DISCLAIMER

**THIS FIRMWARE IS FOR EDUCATIONAL PURPOSES ONLY**

- Only use on networks and devices you own
- Always obtain explicit permission before testing
- Be aware of local laws regarding cybersecurity testing
- The authors are not responsible for misuse

## 🔧 Hardware Requirements

- **Raspberry Pi Zero 2 W** (primary board)
- **Waveshare Pi Zero WH Package F** with UPS Module
- **1.3-inch LCD Display** (240x240 resolution)
- **MicroSD Card** (16GB+ recommended)
- **Raspberry Pi OS 32-bit** (Legacy or current)
- **Optional**: External antenna for better wireless range

### GPIO Button Connections

Connect tactile buttons to these GPIO pins:

| Function | GPIO Pin | Physical Pin |
|----------|----------|--------------|
| UP       | GPIO 5   | Pin 29       |
| DOWN     | GPIO 6   | Pin 31       |
| LEFT     | GPIO 16  | Pin 36       |
| RIGHT    | GPIO 24  | Pin 18       |
| SELECT   | GPIO 12  | Pin 32       |
| BACK     | GPIO 20  | Pin 38       |

## 🚀 Features

### 📡 WiFi Tools
- **Network Scanner**: Detect nearby WiFi networks
- **Monitor Mode**: Enable wireless monitoring
- **Deauth Attack**: Educational demonstration (own networks only)
- **Access Point**: Create hotspot for testing (BlackHat-Educational)

### 📱 Bluetooth Tools
- **Device Scanner**: Discover Bluetooth devices
- **BLE Scanner**: Low Energy device detection
- **Device Information**: Detailed Bluetooth adapter info

### 🌐 Network Tools
- **Port Scanner**: Check for open ports
- **Network Discovery**: Find devices on local network
- **Packet Capture**: Monitor network traffic
- **DNS Lookup**: Resolve hostnames

### ⚡ GPIO Tools
- **Pin State Monitor**: Check GPIO pin status
- **PWM Control**: Generate PWM signals
- **I2C Scanner**: Detect I2C devices
- **SPI Testing**: Test SPI communication

### 🖥️ System Tools
- **System Information**: Hardware and OS details
- **Settings Configuration**: Customize behavior
- **About**: Firmware information

## 📦 Installation

### Step 1: Prepare Your Pi

1. Flash the latest **Raspberry Pi OS 32-bit** to your SD card
2. Enable SSH and configure WiFi if needed
3. Boot your Pi and update the system:

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2: Download and Install

```bash
# Clone or download the firmware files
git clone https://github.com/yourusername/blackhat-firmware.git
cd blackhat-firmware

# Ensure the main file is named correctly
ls blackhat.py  # Should exist

# Make the installation script executable
chmod +x install.sh

# Run the installation (requires root)
sudo ./install.sh
```

### Step 3: Hardware Setup

1. Connect your 1.3" LCD display according to Waveshare documentation
2. Wire the navigation buttons to the specified GPIO pins
3. Ensure the UPS module is properly connected

### Step 4: Custom Boot Splash (Optional)

Create a custom 240x240 PNG image and place it at:
```
/opt/blackhat/images/boot_splash.png
```

### Step 5: Reboot and Enjoy!

```bash
sudo reboot
```

The firmware will start automatically and display the boot splash, followed by the main menu.

## 🎮 Usage

### Navigation
- **UP/DOWN**: Navigate menu items
- **SELECT**: Choose menu item
- **BACK**: Return to previous menu
- **LEFT/RIGHT**: Reserved for future features

### Without Physical Buttons
If you don't have buttons connected, you can use keyboard input:
- **W/S**: Up/Down navigation
- **Enter**: Select item
- **Q**: Back/Quit

### Manual Execution
```bash
# Run BlackHat firmware manually
sudo python3 /opt/blackhat/blackhat.py

# Or with service
sudo systemctl start blackhat
```

## 🔧 Configuration

Edit the configuration file to customize behavior:
```bash
sudo nano /opt/blackhat/configs/blackhat.conf
```

### Key Configuration Options

```ini
[display]
width = 240
height = 240
rotation = 0

[gpio]
btn_up = 5
btn_down = 6
# ... other button mappings

[network]
default_interface = wlan0
ap_ssid = BlackHat-Educational
ap_password = educational123

[security]
enable_deauth = false  # Disable for safety
log_captures = true

[system]
arch = armv7l  # 32-bit ARM
```

## 🛠️ Advanced Features

### WiFi Monitor Mode

Enable monitor mode for packet capture and analysis:

```bash
sudo /opt/blackhat/enable_monitor.sh
```

Disable monitor mode and restore normal WiFi:

```bash
sudo /opt/blackhat/disable_monitor.sh
```

### Access Point Mode

Start educational access point:

```bash
sudo /opt/blackhat/start_ap.sh
```

Stop access point:

```bash
sudo /opt/blackhat/stop_ap.sh
```

### Service Management

```bash
# Check firmware status
sudo systemctl status blackhat

# Start/stop manually
sudo systemctl start blackhat
sudo systemctl stop blackhat

# View logs
sudo journalctl -u blackhat -f

# Disable auto-start
sudo systemctl disable blackhat
```

## 📁 File Structure

```
/opt/blackhat/
├── blackhat.py               # Main system file
├── configs/
│   └── blackhat.conf        # Configuration file
├── images/
│   └── boot_splash.png    # Custom boot image
├── logs/                  # Log files
├── captures/              # Packet captures
├── enable_monitor.sh      # Monitor mode script
├── disable_monitor.sh     # Disable monitor mode
├── start_ap.sh           # Start access point
├── stop_ap.sh            # Stop access point
└── uninstall.sh          # Uninstall script
```

## 🔍 Troubleshooting

### Display Issues

1. **Black screen**: Check SPI is enabled (`sudo raspi-config`)
2. **Wrong colors**: Verify display wiring and model
3. **No display library**: Install missing packages:
   ```bash
   sudo pip3 install ST7789 luma.core luma.oled
   ```

### WiFi Issues

1. **Monitor mode fails**: Install aircrack-ng suite:
   ```bash
   sudo apt install aircrack-ng
   ```
2. **No wireless interface**: Check WiFi adapter compatibility
3. **Permission denied**: Ensure running as root for wireless operations

### Bluetooth Issues

1. **No Bluetooth**: Enable Bluetooth service:
   ```bash
   sudo systemctl enable bluetooth
   sudo systemctl start bluetooth
   ```
2. **hcitool not found**: Install Bluetooth tools:
   ```bash
   sudo apt install bluez bluez-tools
   ```

### GPIO Issues

1. **Button not responding**: Check wiring and GPIO pin numbers
2. **Permission denied**: Ensure script runs with root privileges
3. **GPIO already in use**: Check for conflicting services

## 🔒 Security Considerations

### Ethical Usage
- **Own networks only**: Never test on networks you don't own
- **Get permission**: Always obtain written permission before testing
- **Legal compliance**: Be aware of local laws regarding security testing
- **Educational focus**: Use for learning, not malicious purposes

### Safety Features
- Deauth attacks disabled by default
- All captures logged for accountability
- Clear educational warnings throughout interface
- No automated attack modes

### Recommendations
- Use in isolated lab environments
- Document all testing activities
- Regular security updates
- Monitor usage logs

## 🔄 Updates and Maintenance

### Updating the Firmware

```bash
cd /opt/blackhat
sudo git pull  # If installed via git
sudo systemctl restart blackhat
```

### Log Rotation

Logs are automatically rotated daily. To manually check logs:

```bash
# View current logs
sudo tail -f /opt/blackhat/logs/blackhat.log

# View system logs
sudo journalctl -u blackhat -f
```

### Backup Configuration

```bash
# Backup your configuration
sudo cp /opt/blackhat/configs/blackhat.conf /home/pi/blackhat_backup.conf
```

## 🗑️ Uninstallation

To completely remove the firmware:

```bash
sudo /opt/blackhat/uninstall.sh
```

This will:
- Stop and disable the service
- Remove all firmware files
- Clean up configuration files
- Remove desktop shortcuts

## 📚 Educational Resources

### Recommended Learning Materials
- **WiFi Security**: Understanding WPA/WPA2/WPA3 protocols
- **Bluetooth Security**: BLE security concepts
- **Network Analysis**: Packet analysis with Wireshark
- **Ethical Hacking**: OSCP, CEH, and similar certifications

### Practice Environments
- Set up isolated test networks
- Use virtualized environments
- Practice with dedicated security labs
- Join ethical hacking communities

## 🤝 Contributing

We welcome contributions to improve this educational platform:

1. Fork the repository
2. Create a feature branch
3. Add educational value
4. Ensure ethical compliance
5. Submit a pull request

### Development Guidelines
- Maintain educational focus
- Add safety warnings for dangerous features
- Document all new features
- Test thoroughly on actual hardware

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **M5StickC Bruce Firmware**: Inspiration for interface design
- **Flipper Zero**: Reference for educational security tools
- **Raspberry Pi Foundation**: Amazing hardware platform
- **Waveshare**: Quality display modules
- **Security Community**: Tools and knowledge sharing

## 📞 Support

- **Issues**: Report bugs via GitHub issues
- **Questions**: Use GitHub discussions
- **Security**: Report vulnerabilities privately
- **Documentation**: Wiki contributions welcome

---

**Remember: With great power comes great responsibility. Use this firmware ethically and legally!**
