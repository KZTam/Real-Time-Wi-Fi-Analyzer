"""
Unit tests for SpeedMonitor and DataBuffer.
"""

import os
import tempfile
import unittest
from wifi_analyzer.speed_monitor import SpeedMonitor
from wifi_analyzer.data_buffer import DataBuffer


class TestSpeedMonitor(unittest.TestCase):

    def test_simulation_speed_sampling(self):
        monitor = SpeedMonitor(simulate=True)
        sample = monitor.sample()
        self.assertGreaterEqual(sample.download_mbps, 0.0)
        self.assertGreaterEqual(sample.upload_mbps, 0.0)
        self.assertIn("Simulated", sample.interface_name)

        stats = monitor.get_stats()
        self.assertGreater(stats["peak_download_mbps"], 0.0)
        self.assertGreater(stats["avg_download_mbps"], 0.0)
        self.assertEqual(stats["samples_count"], 1)


class TestDataBuffer(unittest.TestCase):

    def setUp(self):
        self.buffer = DataBuffer(max_points=50)

    def test_append_and_count(self):
        self.assertEqual(self.buffer.count(), 0)
        self.buffer.append(
            download_mbps=45.5,
            upload_mbps=12.2,
            ping_ms=5.0,
            rssi_dbm=-52,
            signal_percent=82,
            ssid="TestNet",
            channel=6,
            band="2.4 GHz"
        )
        self.assertEqual(self.buffer.count(), 1)

    def test_get_time_series_arrays(self):
        for i in range(10):
            self.buffer.append(
                download_mbps=float(i * 5),
                upload_mbps=float(i * 2),
                ping_ms=4.0 + (i * 0.5),
                rssi_dbm=-50 - i,
                signal_percent=80 - i,
                ssid="TestNet",
                channel=6,
                band="2.4 GHz"
            )

        ts = self.buffer.get_time_series(window_seconds=5)
        self.assertEqual(len(ts["time"]), 5)
        self.assertEqual(len(ts["download"]), 5)
        self.assertEqual(len(ts["upload"]), 5)
        self.assertEqual(len(ts["ping"]), 5)
        self.assertEqual(len(ts["rssi"]), 5)

    def test_csv_export(self):
        self.buffer.append(
            download_mbps=25.0,
            upload_mbps=10.0,
            ping_ms=6.0,
            rssi_dbm=-55,
            signal_percent=78,
            ssid="TestNet",
            channel=11,
            band="2.4 GHz"
        )
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_path = f.name

        try:
            self.buffer.export_csv(temp_path)
            self.assertTrue(os.path.exists(temp_path))
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("Download_Mbps", content)
                self.assertIn("25.0", content)
                self.assertIn("TestNet", content)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_json_export(self):
        self.buffer.append(
            download_mbps=30.0,
            upload_mbps=15.0,
            ping_ms=3.5,
            rssi_dbm=-50,
            signal_percent=85,
            ssid="TestNet5G",
            channel=36,
            band="5 GHz"
        )
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            self.buffer.export_json(temp_path)
            self.assertTrue(os.path.exists(temp_path))
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("TestNet5G", content)
                self.assertIn("30.0", content)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == '__main__':
    unittest.main()
