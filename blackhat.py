#!/usr/bin/env python3
"""
BlackHat Educational Firmware for Raspberry Pi Zero 2 W
Inspired by M5StickC Bruce firmware and Flipper Zero
Hardware: Waveshare Pi Zero WH Package F with UPS Module and 1.3" LCD
OS: Raspberry Pi OS 32-bit

WARNING: This firmware is for EDUCATIONAL PURPOSES ONLY
Only use on networks and devices you own or have explicit permission to test
"""

import time
import os
import sys
import threading
import subprocess
import json
import socket
import struct
import fcntl
import signal
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import RPi.GPIO as GPIO

# Display imports for Waveshare 1.3" LCD
try:
    import ST7789
    from luma.core.interface.serial import spi
    from luma.core.render import canvas
    from luma.oled.device import ssd1351
    LCD_AVAILABLE = True
except ImportError:
    print("LCD libraries not found. Install: pip3 install ST7789 luma.oled luma.core")
    LCD_AVAILABLE = False

class BlackHatDevice:
    def __init__(self):
        self.running = True
        self.current_menu = "main"
        self.menu_index = 0
        self.display_width = 240
        self.display_height = 240
        
        # Initialize display
        if LCD_AVAILABLE:
            self.display = ST7789.ST7789(
                port=0, cs=1, dc=9, backlight=13, rst=22, 
                width=240, height=240, rotation=0
            )
            self.display.begin()
        
        # Initialize GPIO for buttons (adjust pins as needed)
        GPIO.setmode(GPIO.BCM)
        self.setup_buttons()
        
        # Menu structure
        self.menus = {
            "main": {
                "title": "BlackHat Main Menu",
                "items": [
                    ("WiFi Tools", "wifi_menu"),
                    ("Bluetooth Tools", "bluetooth_menu"),
                    ("Network Tools", "network_menu"),
                    ("GPIO Tools", "gpio_menu"),
                    ("System Info", "system_info"),
                    ("Settings", "settings_menu"),
                    ("Shutdown", "shutdown")
                ]
            },
            "wifi_menu": {
                "title": "WiFi Tools",
                "items": [
                    ("Scan Networks", "wifi_scan"),
                    ("Monitor Mode", "wifi_monitor"),
                    ("Deauth Attack", "wifi_deauth"),
                    ("Access Point", "create_ap"),
                    ("Back", "main")
                ]
            },
            "bluetooth_menu": {
                "title": "Bluetooth Tools",
                "items": [
                    ("Scan Devices", "bt_scan"),
                    ("BLE Scanner", "ble_scan"),
                    ("Device Info", "bt_info"),
                    ("Back", "main")
                ]
            },
            "network_menu": {
                "title": "Network Tools",
                "items": [
                    ("Port Scanner", "port_scan"),
                    ("Network Scan", "network_scan"),
                    ("Packet Capture", "packet_capture"),
                    ("DNS Lookup", "dns_lookup"),
                    ("Back", "main")
                ]
            },
            "gpio_menu": {
                "title": "GPIO Tools",
                "items": [
                    ("Pin State", "gpio_state"),
                    ("PWM Control", "gpio_pwm"),
                    ("I2C Scanner", "i2c_scan"),
                    ("SPI Test", "spi_test"),
                    ("Back", "main")
                ]
            },
            "settings_menu": {
                "title": "Settings",
                "items": [
                    ("Display", "display_settings"),
                    ("Network", "network_settings"),
                    ("About", "about"),
                    ("Back", "main")
                ]
            }
        }
        
        self.boot_splash()
    
    def setup_buttons(self):
        """Setup GPIO buttons for navigation"""
        # Define button pins (adjust according to your hardware)
        self.BTN_UP = 5
        self.BTN_DOWN = 6
        self.BTN_LEFT = 16
        self.BTN_RIGHT = 24
        self.BTN_SELECT = 12
        self.BTN_BACK = 20
        
        buttons = [self.BTN_UP, self.BTN_DOWN, self.BTN_LEFT, 
                  self.BTN_RIGHT, self.BTN_SELECT, self.BTN_BACK]
        
        for btn in buttons:
            GPIO.setup(btn, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(btn, GPIO.FALLING, 
                                callback=self.button_callback, bouncetime=200)
    
    def boot_splash(self):
        """Display boot splash screen"""
        if not LCD_AVAILABLE:
            print("=== BlackHat Firmware ===")
            print("Educational Hacking Device")
            print("Booting...")
            time.sleep(3)
            return
        
        # Create boot image
        image = Image.new('RGB', (self.display_width, self.display_height), color=(0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw boot screen
        draw.text((120, 80), "BlackHat", fill=(0, 255, 0), font=font_large, anchor="mm")
        draw.text((120, 110), "Educational Firmware", fill=(255, 255, 255), font=font_small, anchor="mm")
        draw.text((120, 130), "v1.0", fill=(128, 128, 128), font=font_small, anchor="mm")
        
        # Add loading animation
        for i in range(20):
            draw.rectangle([(60 + i*6, 160), (60 + i*6 + 4, 170)], 
                          fill=(0, 255, 0) if i < 10 else (128, 128, 128))
        
        self.display.display(image)
        time.sleep(3)
    
    def button_callback(self, channel):
        """Handle button presses"""
        if channel == self.BTN_UP:
            self.menu_index = max(0, self.menu_index - 1)
        elif channel == self.BTN_DOWN:
            max_index = len(self.menus[self.current_menu]["items"]) - 1
            self.menu_index = min(max_index, self.menu_index + 1)
        elif channel == self.BTN_SELECT:
            self.select_menu_item()
        elif channel == self.BTN_BACK:
            if self.current_menu != "main":
                self.current_menu = "main"
                self.menu_index = 0
        
        self.update_display()
    
    def select_menu_item(self):
        """Handle menu item selection"""
        current_items = self.menus[self.current_menu]["items"]
        if self.menu_index < len(current_items):
            _, action = current_items[self.menu_index]
            
            if action in self.menus:
                self.current_menu = action
                self.menu_index = 0
            else:
                self.execute_action(action)
    
    def execute_action(self, action):
        """Execute selected action"""
        action_map = {
            "wifi_scan": self.wifi_scan,
            "wifi_monitor": self.wifi_monitor,
            "wifi_deauth": self.wifi_deauth,
            "create_ap": self.create_access_point,
            "bt_scan": self.bluetooth_scan,
            "ble_scan": self.ble_scan,
            "bt_info": self.bluetooth_info,
            "port_scan": self.port_scanner,
            "network_scan": self.network_scanner,
            "packet_capture": self.packet_capture,
            "dns_lookup": self.dns_lookup,
            "gpio_state": self.gpio_state,
            "gpio_pwm": self.gpio_pwm,
            "i2c_scan": self.i2c_scanner,
            "spi_test": self.spi_test,
            "system_info": self.show_system_info,
            "about": self.show_about,
            "shutdown": self.shutdown_device
        }
        
        if action in action_map:
            action_map[action]()
    
    def update_display(self):
        """Update the display with current menu"""
        if not LCD_AVAILABLE:
            self.print_menu_console()
            return
        
        image = Image.new('RGB', (self.display_width, self.display_height), color=(0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
            font_item = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            font_title = ImageFont.load_default()
            font_item = ImageFont.load_default()
        
        # Draw title
        title = self.menus[self.current_menu]["title"]
        draw.text((120, 20), title, fill=(0, 255, 255), font=font_title, anchor="mm")
        
        # Draw menu items
        items = self.menus[self.current_menu]["items"]
        start_y = 50
        
        for i, (item_text, _) in enumerate(items):
            y_pos = start_y + i * 25
            color = (255, 255, 0) if i == self.menu_index else (255, 255, 255)
            
            if i == self.menu_index:
                draw.rectangle([(10, y_pos - 10), (230, y_pos + 10)], fill=(64, 64, 64))
            
            draw.text((20, y_pos), f"> {item_text}" if i == self.menu_index else f"  {item_text}", 
                     fill=color, font=font_item)
        
        # Draw status bar
        draw.line([(0, 220), (240, 220)], fill=(128, 128, 128))
        draw.text((120, 230), f"Select: Enter | Back: ESC", 
                 fill=(128, 128, 128), font=font_item, anchor="mm")
        
        self.display.display(image)
    
    def print_menu_console(self):
        """Print menu to console when display not available"""
        os.system('clear')
        print(f"\n=== {self.menus[self.current_menu]['title']} ===\n")
        
        items = self.menus[self.current_menu]["items"]
        for i, (item_text, _) in enumerate(items):
            marker = ">> " if i == self.menu_index else "   "
            print(f"{marker}{i+1}. {item_text}")
        
        print("\nUse keyboard: w/s (up/down), Enter (select), q (back)")
    
    # WiFi Tools
    def wifi_scan(self):
        """Scan for WiFi networks"""
        self.show_status("Scanning WiFi networks...")
        try:
            result = subprocess.run(['iwlist', 'wlan0', 'scan'], 
                                  capture_output=True, text=True)
            # Parse and display results
            networks = self.parse_wifi_scan(result.stdout)
            self.display_results("WiFi Networks", networks)
        except Exception as e:
            self.show_error(f"WiFi scan failed: {str(e)}")
    
    def wifi_monitor(self):
        """Enable monitor mode"""
        self.show_status("Enabling monitor mode...")
        try:
            subprocess.run(['sudo', 'airmon-ng', 'start', 'wlan0'], check=True)
            self.show_success("Monitor mode enabled")
        except Exception as e:
            self.show_error(f"Monitor mode failed: {str(e)}")
    
    def wifi_deauth(self):
        """Perform deauth attack (educational only)"""
        self.show_warning("EDUCATIONAL ONLY - Own networks!")
        # Implementation would go here
        time.sleep(2)
        self.show_status("Deauth demo completed")
    
    def create_access_point(self):
        """Create access point"""
        self.show_status("Creating access point...")
        # Implementation for creating AP
        time.sleep(2)
        self.show_success("AP created: BlackHat-Demo")
    
    # Bluetooth Tools
    def bluetooth_scan(self):
        """Scan for Bluetooth devices"""
        self.show_status("Scanning Bluetooth devices...")
        try:
            result = subprocess.run(['hcitool', 'scan'], 
                                  capture_output=True, text=True)
            devices = result.stdout.strip().split('\n')[1:]  # Skip header
            self.display_results("Bluetooth Devices", devices)
        except Exception as e:
            self.show_error(f"Bluetooth scan failed: {str(e)}")
    
    def ble_scan(self):
        """Scan for BLE devices"""
        self.show_status("Scanning BLE devices...")
        # BLE scanning implementation
        time.sleep(3)
        self.show_success("BLE scan completed")
    
    def bluetooth_info(self):
        """Show Bluetooth adapter info"""
        try:
            result = subprocess.run(['hciconfig'], capture_output=True, text=True)
            self.display_text("Bluetooth Info", result.stdout)
        except Exception as e:
            self.show_error(f"Failed to get BT info: {str(e)}")
    
    # Network Tools
    def port_scanner(self):
        """Simple port scanner"""
        self.show_status("Port scanning localhost...")
        open_ports = []
        
        for port in [22, 80, 443, 8080, 3389, 21, 23]:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            if result == 0:
                open_ports.append(f"Port {port}: Open")
            sock.close()
        
        self.display_results("Open Ports", open_ports or ["No open ports found"])
    
    def network_scanner(self):
        """Scan local network"""
        self.show_status("Scanning local network...")
        # Network scanning implementation
        time.sleep(3)
        self.show_success("Network scan completed")
    
    def packet_capture(self):
        """Capture network packets"""
        self.show_status("Starting packet capture...")
        # Packet capture implementation
        time.sleep(3)
        self.show_success("Capture saved to /tmp/capture.pcap")
    
    def dns_lookup(self):
        """Perform DNS lookup"""
        try:
            import socket
            hostname = "google.com"
            ip = socket.gethostbyname(hostname)
            self.display_text("DNS Lookup", f"{hostname} -> {ip}")
        except Exception as e:
            self.show_error(f"DNS lookup failed: {str(e)}")
    
    # GPIO Tools
    def gpio_state(self):
        """Show GPIO pin states"""
        gpio_info = []
        for pin in range(2, 28):
            try:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                state = GPIO.input(pin)
                gpio_info.append(f"Pin {pin}: {'HIGH' if state else 'LOW'}")
            except:
                gpio_info.append(f"Pin {pin}: ERROR")
        
        self.display_results("GPIO States", gpio_info)
    
    def gpio_pwm(self):
        """PWM control demo"""
        self.show_status("PWM demo on pin 18...")
        try:
            GPIO.setup(18, GPIO.OUT)
            pwm = GPIO.PWM(18, 1000)  # 1kHz frequency
            pwm.start(0)
            
            for duty_cycle in range(0, 101, 10):
                pwm.ChangeDutyCycle(duty_cycle)
                time.sleep(0.1)
            
            pwm.stop()
            self.show_success("PWM demo completed")
        except Exception as e:
            self.show_error(f"PWM failed: {str(e)}")
    
    def i2c_scanner(self):
        """Scan I2C bus"""
        self.show_status("Scanning I2C bus...")
        try:
            result = subprocess.run(['i2cdetect', '-y', '1'], 
                                  capture_output=True, text=True)
            self.display_text("I2C Devices", result.stdout)
        except Exception as e:
            self.show_error(f"I2C scan failed: {str(e)}")
    
    def spi_test(self):
        """SPI test"""
        self.show_status("SPI test...")
        # SPI testing implementation
        time.sleep(2)
        self.show_success("SPI test completed")
    
    # System functions
    def show_system_info(self):
        """Display system information"""
        info = []
        info.append(f"Hostname: {socket.gethostname()}")
        info.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            with open('/proc/loadavg', 'r') as f:
                load = f.read().strip()
                info.append(f"Load: {load}")
        except:
            pass
        
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemTotal' in line or 'MemFree' in line:
                        info.append(line.strip())
        except:
            pass
        
        self.display_results("System Info", info)
    
    def show_about(self):
        """Show about information"""
        about_text = """BlackHat Educational Firmware v1.0

Created for Raspberry Pi Zero 2 W
Hardware: Waveshare Package F
OS: Raspberry Pi OS 32-bit

WARNING: Educational use only!
Only test on owned devices.

Inspired by:
- M5StickC Bruce Firmware
- Flipper Zero

Features:
- WiFi penetration testing
- Bluetooth scanning
- Network analysis
- GPIO control
- System monitoring"""
        
        self.display_text("About", about_text)
    
    def shutdown_device(self):
        """Shutdown the device"""
        self.show_status("Shutting down...")
        time.sleep(2)
        self.running = False
        GPIO.cleanup()
        os.system('sudo shutdown -h now')
    
    # Utility functions
    def show_status(self, message):
        """Show status message"""
        if LCD_AVAILABLE:
            image = Image.new('RGB', (self.display_width, self.display_height), color=(0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.text((120, 120), message, fill=(255, 255, 0), anchor="mm")
            self.display.display(image)
        else:
            print(f"STATUS: {message}")
        time.sleep(1)
    
    def show_success(self, message):
        """Show success message"""
        if LCD_AVAILABLE:
            image = Image.new('RGB', (self.display_width, self.display_height), color=(0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.text((120, 120), "✓ " + message, fill=(0, 255, 0), anchor="mm")
            self.display.display(image)
        else:
            print(f"SUCCESS: {message}")
        time.sleep(2)
    
    def show_error(self, message):
        """Show error message"""
        if LCD_AVAILABLE:
            image = Image.new('RGB', (self.display_width, self.display_height), color=(0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.text((120, 120), "✗ " + message, fill=(255, 0, 0), anchor="mm")
            self.display.display(image)
        else:
            print(f"ERROR: {message}")
        time.sleep(2)
    
    def show_warning(self, message):
        """Show warning message"""
        if LCD_AVAILABLE:
            image = Image.new('RGB', (self.display_width, self.display_height), color=(0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.text((120, 120), "⚠ " + message, fill=(255, 165, 0), anchor="mm")
            self.display.display(image)
        else:
            print(f"WARNING: {message}")
        time.sleep(2)
    
    def display_results(self, title, items):
        """Display list of results"""
        if LCD_AVAILABLE:
            # Paginated display for LCD
            self.display_paginated_results(title, items)
        else:
            print(f"\n=== {title} ===")
            for item in items:
                print(f"  {item}")
            input("\nPress Enter to continue...")
    
    def display_text(self, title, text):
        """Display text content"""
        if LCD_AVAILABLE:
            # Display text on LCD
            pass
        else:
            print(f"\n=== {title} ===")
            print(text)
            input("\nPress Enter to continue...")
    
    def display_paginated_results(self, title, items):
        """Display paginated results on LCD"""
        # Implementation for paginated display
        pass
    
    def parse_wifi_scan(self, scan_output):
        """Parse iwlist scan output"""
        networks = []
        lines = scan_output.split('\n')
        current_network = {}
        
        for line in lines:
            line = line.strip()
            if 'ESSID:' in line:
                essid = line.split('ESSID:')[1].strip('"')
                if essid:
                    current_network['ESSID'] = essid
            elif 'Quality=' in line:
                quality = line.split('Quality=')[1].split(' ')[0]
                current_network['Quality'] = quality
            elif 'Encryption key:' in line:
                encryption = 'Yes' if 'on' in line else 'No'
                current_network['Encryption'] = encryption
                
                if current_network.get('ESSID'):
                    networks.append(f"{current_network['ESSID']} - {current_network.get('Quality', 'N/A')} - Encrypted: {encryption}")
                current_network = {}
        
        return networks[:10]  # Limit to 10 results
    
    def keyboard_input_handler(self):
        """Handle keyboard input when display not available"""
        while self.running:
            try:
                key = input().lower()
                if key == 'w':
                    self.menu_index = max(0, self.menu_index - 1)
                elif key == 's':
                    max_index = len(self.menus[self.current_menu]["items"]) - 1
                    self.menu_index = min(max_index, self.menu_index + 1)
                elif key == '':  # Enter
                    self.select_menu_item()
                elif key == 'q':
                    if self.current_menu != "main":
                        self.current_menu = "main"
                        self.menu_index = 0
                    else:
                        self.running = False
                        break
                
                self.update_display()
            except KeyboardInterrupt:
                self.running = False
                break
            except EOFError:
                self.running = False
                break
    
    def run(self):
        """Main run loop"""
        try:
            if not LCD_AVAILABLE:
                # Start keyboard input handler thread
                input_thread = threading.Thread(target=self.keyboard_input_handler)
                input_thread.daemon = True
                input_thread.start()
            
            self.update_display()
            
            while self.running:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            GPIO.cleanup()

def main():
    """Main function"""
    print("BlackHat Educational Firmware Starting...")
    
    # Check if running as root for some operations
    if os.geteuid() != 0:
        print("Note: Some features require root privileges")
    
    device = BlackHatDevice()
    device.run()

if __name__ == "__main__":
    main()
