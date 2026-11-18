"""
Unit tests for WiFiMonitor and netsh parser.
"""

import unittest
from wifi_analyzer.wifi_monitor import WiFiMonitor, WiFiInterfaceInfo


SAMPLE_NETSH_WIN11 = """
There is 1 interface on the system: 

    Name                   : Wi-Fi
    Description            : MediaTek Wi-Fi 6 MT7921 Wireless LAN Card
    GUID                   : 66023442-d4aa-41b5-83a9-0408b8ae5a28
    Physical address       : ec:2e:98:d4:ad:69
    Interface type         : Primary
    State                  : connected
    SSID                   : Office_5GHz
    AP BSSID               : 4a:b2:5d:88:30:c0
    Band                   : 5 GHz
    Channel                : 36
    Network type           : Infrastructure
    Radio type             : 802.11ax
    Authentication         : WPA2-Personal
    Cipher                 : CCMP
    Connection mode        : Auto Connect
    Receive rate (Mbps)    : 866.7
    Transmit rate (Mbps)   : 866.7
    Signal                 : 86% 
    Rssi                   : -48
    Profile                : Office_5GHz
"""

SAMPLE_NETSH_WIN10_NO_RSSI_FIELD = """
There is 1 interface on the system: 

    Name                   : Wi-Fi
    Description            : Intel(R) Wi-Fi 6 AX200 160MHz
    State                  : connected
    SSID                   : Home_Network
    BSSID                  : 00:11:22:33:44:55
    Network type           : Infrastructure
    Radio type             : 802.11ac
    Band                   : 2.4 GHz
    Channel                : 6
    Receive rate (Mbps)    : 300
    Transmit rate (Mbps)   : 300
    Signal                 : 80% 
"""

SAMPLE_NETSH_DISCONNECTED = """
There is 1 interface on the system: 

    Name                   : Wi-Fi
    Description            : MediaTek Wi-Fi 6 MT7921 Wireless LAN Card
    State                  : disconnected
    Radio status           : Hardware On, Software On
"""


class TestWiFiMonitor(unittest.TestCase):

    def test_parse_windows_11_connected(self):
        info = WiFiMonitor.parse_netsh_output(SAMPLE_NETSH_WIN11)
        self.assertTrue(info.connected)
        self.assertEqual(info.ssid, "Office_5GHz")
        self.assertEqual(info.bssid, "4a:b2:5d:88:30:c0")
        self.assertEqual(info.state, "connected")
        self.assertEqual(info.channel, 36)
        self.assertEqual(info.band, "5 GHz")
        self.assertEqual(info.radio_type, "802.11ax")
        self.assertEqual(info.rx_rate_mbps, 866.7)
        self.assertEqual(info.tx_rate_mbps, 866.7)
        self.assertEqual(info.signal_percent, 86)
        self.assertEqual(info.rssi_dbm, -48)

    def test_parse_windows_10_fallback_rssi(self):
        info = WiFiMonitor.parse_netsh_output(SAMPLE_NETSH_WIN10_NO_RSSI_FIELD)
        self.assertTrue(info.connected)
        self.assertEqual(info.ssid, "Home_Network")
        self.assertEqual(info.signal_percent, 80)
        # Fallback formula: (80 / 2) - 100 = 40 - 100 = -60 dBm
        self.assertEqual(info.rssi_dbm, -60)

    def test_parse_disconnected(self):
        info = WiFiMonitor.parse_netsh_output(SAMPLE_NETSH_DISCONNECTED)
        self.assertFalse(info.connected)
        self.assertEqual(info.state, "disconnected")
        self.assertEqual(info.ssid, "")
        self.assertEqual(info.rssi_dbm, -100)
        self.assertEqual(info.signal_percent, 0)

    def test_simulation_query(self):
        monitor = WiFiMonitor(simulate=True)
        info = monitor.query()
        self.assertTrue(info.connected)
        self.assertTrue(len(info.ssid) > 0)
        self.assertGreaterEqual(info.signal_percent, 10)
        self.assertLessEqual(info.signal_percent, 100)
        self.assertLess(info.rssi_dbm, 0)


if __name__ == '__main__':
    unittest.main()
