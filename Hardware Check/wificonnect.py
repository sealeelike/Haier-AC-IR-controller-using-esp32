import network
import time
from machine import Pin

# Configure LED indicator (if available)
led = Pin(2, Pin.OUT)  # ESP32 dev board typically has a built-in LED on GPIO2

# Security type mapping dictionary
security_types = {
    0: "Open",
    1: "WEP",
    2: "WPA-PSK",
    3: "WPA2-PSK",
    4: "WPA/WPA2-PSK",
    5: "WPA2-Enterprise",
    6: "WPA3-PSK",
    7: "WPA2/WPA3-PSK"
}

def test_wifi():
    # Create WLAN interface instance
    wlan = network.WLAN(network.STA_IF)
    
    # Activate interface
    wlan.active(True)
    print("WiFi interface activated")
    
    # Scan available networks
    print("Scanning WiFi networks...")
    networks = wlan.scan()
    
    # Sort by signal strength (strongest to weakest)
    sorted_networks = sorted(networks, key=lambda x: x[3], reverse=True)
    
    # Display sorted scan results
    if sorted_networks:
        print("Found the following WiFi networks (sorted by signal strength):")
        # Header
        print(f"{'No.':<4} {'SSID':<32} {'Signal':<10} {'Security':<20}")
        print("-" * 66)
        # Data
        for i, network_info in enumerate(sorted_networks):
            ssid = network_info[0].decode('utf-8')  # Network name
            signal_strength = network_info[3]       # Signal strength
            security = network_info[4]              # Security type
            security_type = security_types.get(security, "Unknown")
            print(f"{i+1:<4} {ssid:<32} {signal_strength:<10} {security_type:<20}")
        
        # WiFi module is functioning properly
        print("WiFi module is working properly!")
        # Blink LED to indicate success
        for _ in range(5):
            led.value(1)
            time.sleep(0.2)
            led.value(0)
            time.sleep(0.2)
    else:
        print("No WiFi networks found. Please check if the WiFi module is working.")
        # Keep LED on to indicate error
        led.value(1)
        return None, None
    
    return sorted_networks, wlan

def draw_progress_bar(progress, total, width=50):
    """Draw a progress bar in the console."""
    percent = (progress / total) * 100
    filled = int(width * progress // total)
    bar = '█' * filled + '-' * (width - filled)
    print(f'\rConnecting: |{bar}| {percent:.1f}%', end='')
    if progress == total:
        print()  # New line after completion

def connect_to_wifi(sorted_networks, wlan):
    # Check current connection status
    if wlan.isconnected():
        print(f"Currently connected to: {wlan.config('ssid')} (IP: {wlan.ifconfig()[0]})")
        user_input = input("Do you want to disconnect from the current network? (y/n): ").strip().lower()
        if user_input == 'y':
            wlan.disconnect()
            print("Disconnected from the current network.")
            time.sleep(1)  # Wait briefly to ensure disconnection
        else:
            print("Keeping the current connection.")
            # Blink LED slowly to indicate connection retained
            for _ in range(3):
                led.value(1)
                time.sleep(0.5)
                led.value(0)
                time.sleep(0.5)
            return True
    
    # Ask user to select a network to connect to
    while True:
        try:
            choice = int(input("Enter the number of the WiFi network to connect to (e.g., 1): "))
            if 1 <= choice <= len(sorted_networks):
                selected_network = sorted_networks[choice - 1]
                ssid = selected_network[0].decode('utf-8')
                security = selected_network[4]
                security_type = security_types.get(security, "Unknown")
                print(f"Selected network: {ssid} (Security: {security_type})")
                break
            else:
                print(f"Please enter a number between 1 and {len(sorted_networks)}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")
    
    # If the network is not "Open", prompt for password
    password = ""
    if security != 0:  # 0 means "Open"
        password = input(f"Enter password for {ssid}: ")
        print("Password received. Attempting to connect...")
    
    # Attempt to connect to the selected network
    wlan.connect(ssid, password)
    print(f"Connecting to {ssid}...")
    
    # Wait for connection with a timeout of 10 seconds, showing progress bar
    timeout = 10
    start_time = time.time()
    while not wlan.isconnected():
        elapsed = time.time() - start_time
        if elapsed > timeout:
            print("\nConnection timeout. Failed to connect.")
            # Keep LED on to indicate failure
            led.value(1)
            return False
        # Update progress bar every 0.1 seconds
        draw_progress_bar(elapsed, timeout)
        time.sleep(0.1)
    
    # Connection successful
    print("Connected successfully!")
    print(f"IP Address: {wlan.ifconfig()[0]}")
    # Blink LED rapidly to indicate successful connection
    for _ in range(10):
        led.value(1)
        time.sleep(0.1)
        led.value(0)
        time.sleep(0.1)
    return True

if __name__ == "__main__":
    print("Starting ESP32 WiFi module test...")
    sorted_networks, wlan = test_wifi()
    if sorted_networks:
        connect_to_wifi(sorted_networks, wlan)

