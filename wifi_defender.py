#!/usr/bin/env python3

import os
import sys
import time
import subprocess
import signal
import re
from datetime import datetime

# ---------------------------
# CONFIGURATIONS
# ---------------------------

WIFI_INTERFACE = "wlan0"  # Replace with your Wi-Fi interface
MONITOR_INTERFACE = WIFI_INTERFACE  # By default, the same interface is used in monitor mode
LOCAL_SUBNET = "192.168.1.0/24"     # Change to match your local subnet
AIRODUMP_PREFIX = "airodump_out"    # Prefix for airodump-ng output files
NETDISCOVER_INTERVAL = 60           # Seconds between netdiscover scans
NMAP_FULL_SCAN_INTERVAL = 300       # Seconds between optional Nmap scans

# Known Devices (MAC: Friendly Name) for quick recognition
KNOWN_DEVICES = {
    "AA:BB:CC:DD:EE:11": "My Laptop",
    "AA:BB:CC:DD:EE:22": "My Phone",
}

# Directory for logs
LOG_DIR = "./wifi_logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Log rotation
MAX_LOG_FILES = 10  # Keep only the 10 newest logs to prevent growth

# ---------------------------
# HELPER FUNCTIONS
# ---------------------------

def check_root():
    """Ensure we are running as root."""
    if os.geteuid() != 0:
        print("[!] Please run this script with sudo or as root.")
        sys.exit(1)

def rotate_logs(directory):
    """Keep only the newest logs up to MAX_LOG_FILES."""
    files = sorted(os.listdir(directory), key=lambda x: os.path.getmtime(os.path.join(directory, x)))
    while len(files) > MAX_LOG_FILES:
        oldest = files.pop(0)
        os.remove(os.path.join(directory, oldest))

def log_message(message):
    """Write a log entry to file and also print to console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file_path = os.path.join(LOG_DIR, "wifi_defender.log")
    with open(log_file_path, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def set_monitor_mode(interface):
    """Set the specified interface into monitor mode."""
    log_message(f"Setting {interface} to monitor mode...")
    subprocess.run(["ifconfig", interface, "down"], check=True)
    subprocess.run(["iwconfig", interface, "mode", "monitor"], check=True)
    subprocess.run(["ifconfig", interface, "up"], check=True)

def set_managed_mode(interface):
    """Set the specified interface back to managed mode."""
    log_message(f"Setting {interface} back to managed mode...")
    subprocess.run(["ifconfig", interface, "down"], check=True)
    subprocess.run(["iwconfig", interface, "mode", "managed"], check=True)
    subprocess.run(["ifconfig", interface, "up"], check=True)

def launch_airodump(interface):
    """
    Launch airodump-ng in a background process.  
    We'll run it on all channels unless you only want to monitor one.  
    Output is stored in AIRODUMP_PREFIX files.
    """
    log_message("Launching airodump-ng for continuous Wi-Fi monitoring...")
    log_path = os.path.join(LOG_DIR, AIRODUMP_PREFIX)
    cmd = [
        "airodump-ng",
        interface,
        "--write", log_path,
        "--write-interval", "30",  # Writes CSV every 30 seconds
        "--beacons"               # Capture beacon frames for more info
    ]
    # Example: to limit to one channel or BSSID, you could add:
    # cmd += ["--channel", "6", "--bssid", "<Your_BSSID>"]

    # Launch in the background
    # We can store the Popen object if we need to kill it later
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc

def run_netdiscover(subnet):
    """
    Run netdiscover in passive/active hybrid mode to detect hosts.  
    We'll parse the output for new devices.
    """
    log_message(f"Running netdiscover on {subnet}...")
    cmd = ["netdiscover", "-r", subnet]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log_message("[!] netdiscover command failed. Check if netdiscover is installed.")
        return

    lines = result.stdout.strip().split('\n')
    discovered_devices = []
    # Typical netdiscover line example:
    # 192.168.1.10   00:11:22:33:44:55   1      60   Intel Corporate
    for line in lines:
        if re.match(r"^\d+\.\d+\.\d+\.\d+", line):
            parts = line.split()
            if len(parts) >= 2:
                ip = parts[0]
                mac = parts[1].upper()
                discovered_devices.append((ip, mac))

    return discovered_devices

def run_nmap_scan(target_ip):
    """
    Run an Nmap scan for open ports or vulnerabilities on a single target IP.
    This can be modified for deeper scans (e.g., -sV, -O, --script).
    """
    log_message(f"Running Nmap scan on {target_ip}...")
    cmd = ["nmap", "-sS", "-T4", "-Pn", target_ip]  # Stealth SYN scan, no ping
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def handle_new_device(ip, mac):
    """
    Logic to handle new or unknown devices.
    Possibly alert, log heavily, or run a deeper Nmap scan.
    """
    friendly_name = KNOWN_DEVICES.get(mac, "Unknown Device")
    log_message(f"Detected new or unknown device: MAC={mac}, IP={ip}, Label={friendly_name}")

    # Optionally run an Nmap scan
    nmap_output = run_nmap_scan(ip)
    # Save the Nmap output to a file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nmap_log_file = os.path.join(LOG_DIR, f"nmap_{ip}_{timestamp}.log")
    with open(nmap_log_file, "w") as f:
        f.write(nmap_output)

    # If you suspect a rogue device, you could incorporate iptables blocks or further investigations

# ---------------------------
# MAIN ROUTINE
# ---------------------------

def main():
    check_root()
    rotate_logs(LOG_DIR)

    # Put interface into monitor mode
    set_monitor_mode(WIFI_INTERFACE)

    # Launch airodump-ng in the background
    airodump_proc = launch_airodump(MONITOR_INTERFACE)

    # Track devices we have seen to avoid repeated alerts
    known_macs = set(m.upper() for m in KNOWN_DEVICES.keys())
    seen_macs = set(known_macs)  # start with known devices

    # Capture Ctrl+C to restore managed mode before exit
    def signal_handler(sig, frame):
        log_message("Caught interrupt signal. Cleaning up...")
        if airodump_proc:
            airodump_proc.terminate()
            airodump_proc.wait()
        set_managed_mode(WIFI_INTERFACE)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # MAIN LOOP
    last_nmap_time = 0
    while True:
        # 1. Run netdiscover to see who is on the subnet
        discovered = run_netdiscover(LOCAL_SUBNET)
        if discovered:
            for ip, mac in discovered:
                # If it's not in seen_macs, handle it as a new device
                if mac not in seen_macs:
                    handle_new_device(ip, mac)
                    seen_macs.add(mac)

        # 2. Optionally run a full nmap scan across entire subnet every NMAP_FULL_SCAN_INTERVAL
        current_time = time.time()
        if current_time - last_nmap_time > NMAP_FULL_SCAN_INTERVAL:
            log_message("Running full Nmap scan across subnet...")
            # Example: Quick scan with -sn to see which hosts are up
            subprocess.run(["nmap", "-sn", LOCAL_SUBNET], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # You might parse results or do a deeper scan here
            last_nmap_time = current_time

        rotate_logs(LOG_DIR)

        # Wait before next netdiscover iteration
        time.sleep(NETDISCOVER_INTERVAL)

if __name__ == "__main__":
    main()
