#!/usr/bin/env python3

import os
import sys
import re
import subprocess
import signal
import time
from datetime import datetime

# ---------------------------
# GLOBAL CONFIGURATION
# ---------------------------

# How often to run netdiscover (in seconds)
NETDISCOVER_INTERVAL = 60

# How often to run a full nmap scan across the subnet (in seconds)
NMAP_FULL_SCAN_INTERVAL = 300

# Prefix for airodump-ng logs
AIRODUMP_PREFIX = "airodump_out"

# Directory to store logs (airodump, netdiscover, nmap, etc.)
LOG_DIR = "./wifi_logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Limit the number of old log files to keep
MAX_LOG_FILES = 10

# Dictionary of known/trusted devices { MAC: Friendly Name }
KNOWN_DEVICES = {
    "AA:BB:CC:DD:EE:11": "My Laptop",
    "AA:BB:CC:DD:EE:22": "My Phone",
}

# ---------------------------
# HELPER FUNCTIONS
# ---------------------------

def check_root():
    """Ensure the script is run as root."""
    if os.geteuid() != 0:
        print("[!] Please run this script with sudo or as root.")
        sys.exit(1)

def rotate_logs(directory):
    """Keep only the newest logs up to MAX_LOG_FILES to prevent indefinite growth."""
    files = sorted(os.listdir(directory), key=lambda x: os.path.getmtime(os.path.join(directory, x)))
    while len(files) > MAX_LOG_FILES:
        oldest = files.pop(0)
        os.remove(os.path.join(directory, oldest))

def log_message(message):
    """Write a log entry to a central file and print to console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file_path = os.path.join(LOG_DIR, "wifi_defender.log")
    with open(log_file_path, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def run_command(cmd):
    """Run a shell command and return its stdout as text. Raises on error."""
    process = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return process.stdout.strip()

def get_connected_wifi_interface():
    """
    Attempt to find a wireless interface that's currently associated/connected 
    to a Wi-Fi network, by parsing 'iw dev'.
    Return the interface name if found, else None.
    """
    try:
        output = run_command(["iw", "dev"])
    except subprocess.CalledProcessError:
        log_message("[!] Failed to run 'iw dev' command.")
        return None

    # Example snippet from 'iw dev':
    # phy#0
    #   Interface wlan0
    #       ifindex 3
    #       wdev 0x1
    #       addr 00:11:22:33:44:55
    #       type managed
    #       ...
    # We need to check if the interface is in "type managed" and also "Connected".

    # We'll also cross-check with "iw <if> link" to see if it's connected or not.
    interfaces = re.findall(r"Interface\s+(\S+)", output)
    for iface in interfaces:
        try:
            link_info = run_command(["iw", iface, "link"])
            # If we're associated, link info might contain lines like:
            # Connected to aa:bb:cc:dd:ee:ff (on freq 2437)
            # SSID: MyHomeWiFi
            if "Connected to" in link_info:
                return iface
        except subprocess.CalledProcessError:
            continue
    return None

def get_current_wifi_info(interface):
    """
    Parse 'iw <interface> link' to find the BSSID, channel (frequency), and SSID. 
    Also parse 'ip -f inet address show dev <interface>' to find local IP and netmask.
    Returns a dict with keys: 'bssid', 'channel', 'ssid', 'ip_subnet'.
    """
    info = {
        "interface": interface,
        "bssid": None,
        "channel": None,
        "ssid": None,
        "ip_subnet": None
    }

    try:
        link_info = run_command(["iw", interface, "link"])
        # Example link_info lines:
        # Connected to aa:bb:cc:dd:ee:ff (on freq 2412)
        # SSID: MyHomeWiFi
        # ...
        m_connected = re.search(r"Connected to\s+([\da-fA-F:]+)\s+\(on\s+freq\s+(\d+)\)", link_info)
        if m_connected:
            info["bssid"] = m_connected.group(1).upper()
            freq = m_connected.group(2)
            # Convert freq to channel (rough approximation for 2.4 GHz)
            # For a robust approach, use a freq-to-channel mapping table.
            # Common 2.4 GHz frequencies: 2412 (ch1), 2417 (ch2), ... 2462 (ch11)
            # For 5 GHz, it's different. We'll do a minimal approach:
            freq_int = int(freq)
            if 2412 <= freq_int <= 2472:
                # (freq - 2412)/5 + 1
                channel = 1 + (freq_int - 2412)//5
                info["channel"] = str(channel)
            elif 5170 <= freq_int <= 5825:
                # 5GHz channels
                # This is more varied, but let's do a best guess or store freq
                info["channel"] = freq
            else:
                info["channel"] = freq  # fallback
        m_ssid = re.search(r"SSID:\s+(.+)", link_info)
        if m_ssid:
            info["ssid"] = m_ssid.group(1)

        # Next, get local IP and netmask
        # We'll parse 'ip -f inet address show dev <interface>'
        ip_info = run_command(["ip", "-f", "inet", "address", "show", "dev", interface])
        # Example output:
        # inet 192.168.1.101/24 brd 192.168.1.255 scope global dynamic wlan0
        m_ip = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+\/\d+)", ip_info)
        if m_ip:
            cidr = m_ip.group(1)  # e.g. "192.168.1.101/24"
            # We'll convert e.g. 192.168.1.101/24 to 192.168.1.0/24 for scanning
            ip, prefix = cidr.split("/")
            octets = ip.split(".")
            mask_int = int(prefix)
            # A very simple approach for /24:
            # If prefix=24, zero out last octet. For anything else, we do minimal approach.
            if mask_int == 24:
                net_addr = f"{octets[0]}.{octets[1]}.{octets[2]}.0/24"
                info["ip_subnet"] = net_addr
            else:
                # fallback
                info["ip_subnet"] = f"{ip}/{prefix}"
    except subprocess.CalledProcessError as e:
        log_message(f"[!] Error getting Wi-Fi info: {e}")
    
    return info

def set_monitor_mode(interface):
    """Set the specified interface to monitor mode."""
    log_message(f"Setting {interface} to monitor mode...")
    subprocess.run(["ifconfig", interface, "down"], check=True)
    subprocess.run(["iwconfig", interface, "mode", "monitor"], check=True)
    subprocess.run(["ifconfig", interface, "up"], check=True)

def set_managed_mode(interface):
    """Set the specified interface back to managed mode."""
    log_message(f"Reverting {interface} to managed mode...")
    subprocess.run(["ifconfig", interface, "down"], check=True)
    subprocess.run(["iwconfig", interface, "mode", "managed"], check=True)
    subprocess.run(["ifconfig", interface, "up"], check=True)

def launch_airodump(interface, bssid=None, channel=None):
    """
    Launch airodump-ng in background to capture data. 
    We'll store CSV logs in LOG_DIR with AIRODUMP_PREFIX.
    """
    log_message("Launching airodump-ng for continuous Wi-Fi monitoring...")
    out_path = os.path.join(LOG_DIR, AIRODUMP_PREFIX)
    cmd = [
        "airodump-ng", interface,
        "--write", out_path,
        "--write-interval", "30",
        "--beacons"
    ]
    if bssid:
        cmd += ["--bssid", bssid]
    if channel:
        cmd += ["--channel", channel]

    # Launch in background
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc

def run_netdiscover(subnet):
    """
    Run netdiscover on the given subnet and return a list of (ip, mac).
    """
    log_message(f"Running netdiscover on {subnet}...")
    try:
        result = subprocess.run(["netdiscover", "-r", subnet], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        log_message(f"[!] netdiscover error: {e}")
        return []

    discovered = []
    lines = result.stdout.strip().split('\n')
    for line in lines:
        # Typical netdiscover lines look like:
        # 192.168.1.10   00:11:22:33:44:55   1      60   SomeVendor
        if re.match(r"^\d+\.\d+\.\d+\.\d+", line):
            parts = line.split()
            if len(parts) >= 2:
                ip = parts[0]
                mac = parts[1].upper()
                discovered.append((ip, mac))
    return discovered

def run_nmap_scan(ip):
    """
    Perform a basic Nmap scan on a single IP. 
    Returns the stdout for logging.
    """
    log_message(f"Running Nmap scan on {ip}...")
    cmd = ["nmap", "-sS", "-T4", "-Pn", ip]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        log_message(f"[!] Nmap scan error on {ip}: {e}")
        return ""

def handle_new_device(ip, mac):
    """Logic for new or unknown devices: log, run nmap, etc."""
    friendly_name = KNOWN_DEVICES.get(mac, "Unknown Device")
    log_message(f"New device detected: IP={ip}, MAC={mac}, Name={friendly_name}")

    # Optional deeper scan
    nmap_result = run_nmap_scan(ip)
    if nmap_result:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nmap_log_file = os.path.join(LOG_DIR, f"nmap_{ip}_{timestamp}.log")
        with open(nmap_log_file, "w") as f:
            f.write(nmap_result)

# ---------------------------
# MAIN FUNCTION
# ---------------------------

def main():
    check_root()
    rotate_logs(LOG_DIR)

    # 1. Automatically detect which Wi-Fi interface is connected
    iface = get_connected_wifi_interface()
    if not iface:
        log_message("[!] No connected Wi-Fi interface found. Exiting.")
        sys.exit(1)
    else:
        log_message(f"[+] Found connected Wi-Fi interface: {iface}")

    # 2. Gather details about current Wi-Fi (BSSID, channel, IP subnet, etc.)
    wifi_info = get_current_wifi_info(iface)
    if not wifi_info["bssid"]:
        log_message("[!] Could not determine connected BSSID. Exiting.")
        sys.exit(1)
    else:
        log_message(f"[+] Connected BSSID: {wifi_info['bssid']}, Channel: {wifi_info['channel']}, SSID: {wifi_info['ssid']}")
    if not wifi_info["ip_subnet"]:
        log_message("[!] Could not determine local IP subnet. Exiting.")
        sys.exit(1)
    else:
        log_message(f"[+] Derived local subnet: {wifi_info['ip_subnet']}")

    # 3. Put interface into monitor mode
    set_monitor_mode(iface)

    # 4. Start airodump-ng in the background, focusing on the current BSSID & channel
    airodump_proc = launch_airodump(iface, bssid=wifi_info["bssid"], channel=wifi_info["channel"])

    # 5. Signal handler for Ctrl+C
    def signal_handler(sig, frame):
        log_message("Caught Ctrl+C, terminating script.")
        if airodump_proc:
            airodump_proc.terminate()
            airodump_proc.wait()
        set_managed_mode(iface)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    seen_macs = set(m.upper() for m in KNOWN_DEVICES.keys())
    last_nmap_time = 0

    # 6. Main loop: run netdiscover periodically, detect new devices, optional nmap scans
    while True:
        discovered = run_netdiscover(wifi_info["ip_subnet"])
        for ip, mac in discovered:
            if mac not in seen_macs:
                handle_new_device(ip, mac)
                seen_macs.add(mac)

        # full network scan every NMAP_FULL_SCAN_INTERVAL
        now = time.time()
        if now - last_nmap_time > NMAP_FULL_SCAN_INTERVAL:
            log_message("[+] Running quick Nmap ping sweep on entire subnet...")
            subprocess.run(["nmap", "-sn", wifi_info["ip_subnet"]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Could parse results or do a deeper scan if desired
            last_nmap_time = now

        rotate_logs(LOG_DIR)
        time.sleep(NETDISCOVER_INTERVAL)

if __name__ == "__main__":
    main()
