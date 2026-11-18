"""
WiFi Interface Monitor and Signal Scanner.
Queries Windows WLAN interface for active connection, SSID, RSSI, channel, link rates.
"""

from dataclasses import dataclass
import os
import platform
import re
import socket
import subprocess
from typing import Optional


@dataclass
class WiFiInterfaceInfo:
    """Stores current Wi-Fi adapter and connection state."""
    connected: bool = False
    name: str = "Wi-Fi"
    ssid: str = ""
    bssid: str = ""
    state: str = "disconnected"
    signal_percent: int = 0
    rssi_dbm: int = -100
    radio_type: str = "Unknown"
    band: str = "Unknown"
    channel: int = 0
    rx_rate_mbps: float = 0.0
    tx_rate_mbps: float = 0.0
    description: str = ""
    gateway_ip: str = "192.168.1.1"
    ip_address: str = ""
    error_message: str = ""

    def summary(self) -> str:
        if not self.connected:
            return "Wi-Fi Disconnected"
        return f"{self.ssid} ({self.band}, Ch {self.channel}) | Signal: {self.signal_percent}% ({self.rssi_dbm} dBm)"


def get_default_gateway() -> str:
    """
    Retrieves default gateway IP address from Windows routing table.
    """
    if platform.system() != "Windows":
        return "192.168.1.1"

    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        proc = subprocess.run(
            ['route', 'print', '0.0.0.0'],
            capture_output=True,
            text=True,
            timeout=2,
            startupinfo=startupinfo
        )
        for line in proc.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) >= 5 and parts[0] == '0.0.0.0' and parts[1] == '0.0.0.0':
                gw = parts[2]
                if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', gw) and gw != '0.0.0.0':
                    return gw
    except Exception:
        pass
    return "192.168.1.1"


def get_local_ip_for_gateway(gateway_ip: str = "8.8.8.8") -> str:
    """Finds the local IP address assigned to the interface reaching the gateway."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # Does not actually transmit packets, just determines routing table choice
        s.connect((gateway_ip, 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


class WiFiMonitor:
    """
    Monitors Wi-Fi connection state and signal parameters on Windows.
    """

    def __init__(self, simulate: bool = False):
        self.simulate = simulate
        self._last_info = WiFiInterfaceInfo()

    def query(self) -> WiFiInterfaceInfo:
        """
        Polls the Wi-Fi interface and returns current WiFiInterfaceInfo.
        """
        if self.simulate:
            return self._simulate_query()

        if platform.system() != "Windows":
            return WiFiInterfaceInfo(
                connected=False,
                state="unsupported_os",
                error_message="Non-Windows OS detected (simulated mode available with --simulate)"
            )

        info = WiFiInterfaceInfo()
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            proc = subprocess.run(
                ['netsh', 'wlan', 'show', 'interfaces'],
                capture_output=True,
                text=True,
                timeout=2.5,
                startupinfo=startupinfo
            )
            raw_output = proc.stdout

            parsed = self.parse_netsh_output(raw_output)
            parsed.gateway_ip = get_default_gateway()
            parsed.ip_address = get_local_ip_for_gateway(parsed.gateway_ip)

            self._last_info = parsed
            return parsed

        except subprocess.TimeoutExpired:
            info.error_message = "Wi-Fi query timed out"
            return info
        except Exception as e:
            info.error_message = str(e)
            return info

    @staticmethod
    def parse_netsh_output(output: str) -> WiFiInterfaceInfo:
        """
        Parses raw text from 'netsh wlan show interfaces'.
        """
        info = WiFiInterfaceInfo()
        data = {}

        for line in output.splitlines():
            if ':' in line:
                key, val = line.split(':', 1)
                data[key.strip().lower()] = val.strip()

        # Extract name & description
        info.name = data.get("name", "Wi-Fi")
        info.description = data.get("description", "")

        # State check
        state = data.get("state", "").lower()
        info.state = state

        # SSID & AP BSSID
        info.ssid = data.get("ssid", "")
        info.bssid = data.get("ap bssid", data.get("bssid", ""))

        # Only consider connected if state is connected and SSID is not empty
        info.connected = (state == "connected" and bool(info.ssid))

        # Radio, Band, Channel
        info.radio_type = data.get("radio type", "Unknown")
        info.band = data.get("band", "Unknown")

        ch_str = data.get("channel", "0")
        try:
            info.channel = int(re.findall(r'\d+', ch_str)[0]) if re.findall(r'\d+', ch_str) else 0
        except Exception:
            info.channel = 0

        # Receive / Transmit link rates
        rx_str = data.get("receive rate (mbps)", "0")
        tx_str = data.get("transmit rate (mbps)", "0")
        try:
            info.rx_rate_mbps = float(re.findall(r'[\d.]+', rx_str)[0]) if re.findall(r'[\d.]+', rx_str) else 0.0
        except Exception:
            info.rx_rate_mbps = 0.0

        try:
            info.tx_rate_mbps = float(re.findall(r'[\d.]+', tx_str)[0]) if re.findall(r'[\d.]+', tx_str) else 0.0
        except Exception:
            info.tx_rate_mbps = 0.0

        # Signal percentage (e.g. "82%")
        sig_str = data.get("signal", "0%")
        sig_match = re.search(r'(\d+)', sig_str)
        signal_pct = int(sig_match.group(1)) if sig_match else 0
        info.signal_percent = max(0, min(100, signal_pct))

        # RSSI in dBm
        # Windows 11 provides 'Rssi' line directly (e.g., -52)
        rssi_str = data.get("rssi", "")
        if rssi_str:
            rssi_match = re.search(r'(-?\d+)', rssi_str)
            if rssi_match:
                info.rssi_dbm = int(rssi_match.group(1))
            else:
                info.rssi_dbm = int(round((info.signal_percent / 2.0) - 100.0))
        else:
            # Fallback estimation: 100% = -50 dBm, 0% = -100 dBm
            info.rssi_dbm = int(round((info.signal_percent / 2.0) - 100.0))

        if not info.connected:
            info.rssi_dbm = -100
            info.signal_percent = 0

        return info

    def _simulate_query(self) -> WiFiInterfaceInfo:
        """Generates realistic simulated data for testing or demo purposes."""
        import random
        base_signal = 82 + random.randint(-4, 4)
        base_signal = max(10, min(100, base_signal))
        rssi = int(round((base_signal / 2.0) - 100.0)) + random.randint(-2, 2)

        return WiFiInterfaceInfo(
            connected=True,
            name="Wi-Fi (Simulated)",
            ssid="Demo-WiFi-5G",
            bssid="34:60:f9:88:ab:cd",
            state="connected",
            signal_percent=base_signal,
            rssi_dbm=rssi,
            radio_type="802.11ax",
            band="5 GHz",
            channel=36,
            rx_rate_mbps=866.7,
            tx_rate_mbps=866.7,
            description="Virtual Wi-Fi 6 Adapter",
            gateway_ip="192.168.1.1",
            ip_address="192.168.1.150"
        )
