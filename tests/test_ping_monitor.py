"""
Unit tests for PingMonitor latency calculations and statistics.
"""

import unittest
from wifi_analyzer.ping_monitor import PingMonitor, PingResult


class TestPingMonitor(unittest.TestCase):

    def test_simulation_ping(self):
        monitor = PingMonitor(simulate=True)
        # Run several probes
        for _ in range(5):
            res = monitor._simulate_ping("192.168.1.1")
            self.assertIsNotNone(res)
            if res.success:
                self.assertGreater(res.latency_ms, 0.0)

    def test_stats_aggregation(self):
        monitor = PingMonitor(simulate=True)
        # Inject known results into history
        monitor._history.append(PingResult("192.168.1.1", 10.0, 100.0, True))
        monitor._history.append(PingResult("192.168.1.1", 20.0, 101.0, True))
        monitor._history.append(PingResult("192.168.1.1", 30.0, 102.0, True))
        monitor._packets_sent = 3
        monitor._packets_lost = 0

        stats = monitor.get_stats()
        self.assertEqual(stats["min_ms"], 10.0)
        self.assertEqual(stats["max_ms"], 30.0)
        self.assertEqual(stats["avg_ms"], 20.0)
        self.assertEqual(stats["loss_percent"], 0.0)

    def test_packet_loss_calculation(self):
        monitor = PingMonitor(simulate=True)
        monitor._history.append(PingResult("192.168.1.1", 10.0, 100.0, True))
        monitor._history.append(PingResult("192.168.1.1", None, 101.0, False, "Timeout"))
        monitor._packets_sent = 2
        monitor._packets_lost = 1

        stats = monitor.get_stats()
        self.assertEqual(stats["loss_percent"], 50.0)
        self.assertEqual(stats["packets_lost"], 1)


if __name__ == '__main__':
    unittest.main()
