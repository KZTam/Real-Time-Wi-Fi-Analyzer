# Real-Time Wi-Fi Suite 📡⚡

A native desktop application built with **Python**, **PyQt5**, and **PyQtGraph** for real-time Wi-Fi network analysis and active speed limit saturation benchmarking.

The software features a **Mode Selection Window** that allows users to choose between two specialized operating modes:
1. **Window 1: Real-Time Wi-Fi Analyzer** — Continuous 1Hz passive monitoring of throughput and router ping latency.
2. **Window 2: Speed Limit Test** — 20-second active multi-threaded saturation benchmark to measure peak achievable bandwidth (Download first, then Upload).

---

## 🌟 Modes Overview

### 1. Selection Window (Launcher)
When launched (`python main.py`), a modern dark-themed selection dashboard lets you choose your desired tool:
* **Launch Real-Time Analyzer**: Opens Window 1 for continuous, passive, non-intrusive monitoring.
* **Launch Speed Limit Test**: Opens Window 2 for a full-throttle 20-second bandwidth capacity benchmark.
* Easily switch between modes or return to the launcher at any time.

---

### 2. Window 1: Real-Time Wi-Fi Analyzer (Passive Monitoring)
* **Wi-Fi Connection Enforcement**: The analyzer only runs when connected to Wi-Fi. If disconnected, the **Run** button locks automatically and pauses if disconnected mid-run.
* **Graph 1: Live Throughput (1Hz)**: Electric Cyan (Download) and Emerald Green (Upload) curves with translucent area fills.
* **Graph 2: Real-Time Ping Latency (1Hz)**: Measures round-trip time to your router gateway or public DNS, computing RFC 1889 jitter and packet loss.
* **Active Speed Prober (Optional)**: Checkbox to toggle lightweight 1-second burst traffic to evaluate available bandwidth without continuous saturation.
* **Telemetry Metric Cards**: Live, Peak, and Average Download/Upload speeds, latency, and RSSI signal metrics.
* **Mode Navigation**: Features a **← Mode Selection** button to easily switch back to the launcher window.

---

### 3. Window 2: Speed Limit Test (Active 20-Second Saturation Benchmark)
* **20-Second Timed Benchmark**: Fixed 20-second total duration designed to measure true peak capacity without bogging down your network indefinitely.
* **Two-Phase Saturation Sequence**:
  * **Phase 1 (Seconds 1 to 10)**: **Multi-Threaded Download Saturation** — 8 concurrent worker streams download from high-speed CDNs to saturate downstream bandwidth.
  * **Phase 2 (Seconds 11 to 20)**: **Multi-Threaded Upload Saturation** — 8 concurrent worker streams upload burst payloads to saturate upstream bandwidth.
* **Separated Dedicated Graphs (10-Second Timelines)**:
  * **Top Graph**: Real-Time Download Saturation (Mbps) plotted over a 10s timeline (`0..10s`).
  * **Bottom Graph**: Real-Time Upload Saturation (Mbps) plotted over a 10s timeline (`0..10s`, starting from 0s at Phase 2).
  * Both graphs use custom `ConnectedAxisItem` to guarantee axes remain seamlessly attached at `(0, 0)` with zero gap on resize and maximize.
* **Streamlined Metric Cards**: Balanced two-card display (Download Speed & Upload Speed) mirroring the two graphs, with RSSI and progress phase widgets removed for maximum clarity.
* **Zero 'Active Speed Prober' Checkbox**: The toolbar is focused purely on the multi-threaded saturation test.
* **Zero Memory Accumulation**: Data packets are streamed and immediately discarded from memory buffers, keeping RAM usage below 40 MB.
* **Mode Navigation**: Features a **← Mode Selection** button to return to the launcher window.

---

## 📁 Project Structure

```
realtimewifianalyzer/
├── wifi_analyzer/
│   ├── __init__.py
│   ├── wifi_monitor.py          # Queries Windows WLAN interface for SSID, RSSI, channel, link rates
│   ├── ping_monitor.py          # Asynchronous non-blocking ping & jitter monitor
│   ├── speed_monitor.py         # Real-time 1Hz I/O delta speed calculator (in Mbps)
│   ├── active_probe.py          # Lightweight HTTP burst stream generator for active speed testing
│   ├── speed_test_engine.py     # 20-second multi-threaded saturation benchmark engine
│   ├── data_buffer.py           # Circular time-series buffer and CSV/JSON exporter
│   └── ui/
│       ├── __init__.py
│       ├── selection_window.py   # Mode Selection launcher window
│       ├── main_window.py       # Window 1: Real-Time Wi-Fi Analyzer dashboard
│       ├── speed_limit_window.py# Window 2: Speed Limit Test dashboard
│       ├── benchmark_graph.py   # Dedicated 10s separated Download & Upload graph widgets
│       ├── speed_graph.py       # 1Hz Real-Time Throughput graph widget
│       ├── signal_graph.py      # 1Hz Real-Time Ping Latency graph widget
│       ├── connected_axis.py    # Custom connected axis item ensuring seamless corner alignment
│       ├── stats_card.py        # Telemetry metric card widgets
│       └── styles.py            # Modern Dark Theme QSS stylesheets and color palettes
├── tests/
│   ├── test_wifi_monitor.py     # Unit tests for WLAN parsing and connection state
│   ├── test_ping_monitor.py     # Unit tests for ping latency and jitter calculations
│   ├── test_speed_monitor.py    # Unit tests for speed calculation and data buffering
│   ├── test_connected_axes.py   # Unit tests for axis connection and resize resilience
│   └── test_speed_limit.py      # Unit tests for Speed Limit Test and selection launcher
├── main.py                      # Application launch script
├── requirements.txt             # Python dependencies
└── README.md                    # Documentation and guide
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Operating System**: Windows 10 or Windows 11.
- **Python**: Version 3.8 or higher (tested on Python 3.11).

### 2. Installation
Open PowerShell in the project directory and install dependencies:

```powershell
pip install -r requirements.txt
```

Required dependencies:
- `PyQt5`: Desktop GUI application framework.
- `pyqtgraph`: Hardware-accelerated 2D real-time plotting.
- `psutil`: High-precision system network interface I/O monitoring.
- `numpy`: Vectorized numerical arrays for time-series buffer handling.

### 3. Running the Suite

**Standard Launch (Opens Selection Window)**:
```powershell
python main.py
```

**Simulation Mode (For offline testing or environments without Wi-Fi)**:
```powershell
python main.py --simulate
```

**Direct Mode Shortcuts**:
```powershell
# Directly launch Window 1 (Real-Time Wi-Fi Analyzer)
python main.py --analyzer

# Directly launch Window 2 (Speed Limit Test)
python main.py --speed-test
```

---

## 🎮 How to Use the Modes

### Using Window 1: Real-Time Wi-Fi Analyzer
1. Click **Launch Real-Time Analyzer →** in the selection window.
2. Confirm the top-right Wi-Fi connection badge is **green**.
3. Click **▶ Run** to monitor live network throughput and router ping latency updated at **1Hz**.
4. Select your preferred **Ping Target** (`Router Gateway`, `Cloudflare`, `Google DNS`).
5. (Optional) Check **Active Speed Prober** to burst 1s test traffic to assess pipeline responsiveness.
6. Export captured sessions anytime via **📥 Export Data**.
7. Click **← Mode Selection** anytime to return to the launcher window.

### Using Window 2: Speed Limit Test
1. Click **Launch Speed Limit Test →** in the selection window.
2. Click **▶ Run Speed Test**.
3. **Phase 1 (Seconds 1–10)**: The software launches 8 parallel download streams to saturate downstream bandwidth. Watch the top **Download Speed (Mbps)** graph plot real-time capacity.
4. **Phase 2 (Seconds 11–20)**: The software switches to 8 parallel upload streams. Watch the bottom **Upload Speed (Mbps)** graph plot real-time upload capacity.
5. **Results**: At second 20, the test finishes automatically and presents your **Peak Download** and **Peak Upload** achievable bandwidth.
6. Click **📁 Export Results** to save the benchmark to CSV or JSON.
7. Click **← Mode Selection** to return to the launcher window.

---

## 💡 Active Speed Prober vs. Speed Limit Test Explained

### Why Does Passive Monitoring Show 10–20 Mbps While Speed Tests Show 60–100+ Mbps?
* **Passive Throughput Monitoring (Window 1 default)**: Measures the actual network packets currently consumed by your active applications and operating system. If background programs and browsers only need 10–20 Mbps, that is what is measured. This does not mean your Wi-Fi cannot go faster—it simply means current demand is modest.
* **Active Speed Prober (Window 1 optional toggle)**: Generates small 1-second burst requests every second. This evaluates instantaneous link responsiveness without completely monopolizing your bandwidth.
* **Speed Limit Test (Window 2)**: Runs 8 concurrent worker streams designed to max out your downstream (Phase 1, 1–10s) and upstream (Phase 2, 11–20s) bandwidth. Like mobile and web speed test apps, this measures your connection's absolute physical ceiling. Chunks are discarded immediately upon arrival, maintaining RAM usage below 40 MB and low CPU load.

---

## 🧪 Running Unit Tests

Run the full test suite (29 tests):

```powershell
python -m unittest discover tests
```

---

## ⚙️ Technical Comparison

| Feature | Real-Time Wi-Fi Analyzer (Window 1) | Speed Limit Test (Window 2) |
| :--- | :--- | :--- |
| **Measurement Type** | **Passive 1Hz I/O Monitoring** | **Active Multi-Threaded Saturation** |
| **Primary Purpose** | Monitor current app/OS consumption & latency | Measure theoretical ceiling & peak bandwidth |
| **Test Duration** | Continuous (until paused by user) | Fixed 20 seconds (10s DL + 10s UL) |
| **Throughput Graphs** | Combined Download & Upload graph | **Separated** Download (Top) & Upload (Bottom) graphs |
| **Ping Latency** | Yes (real-time ping & jitter graph) | No (replaced by Upload graph) |
| **RSSI Section** | Yes (Signal dBm and quality) | Removed for clean benchmark layout |
| **Network Overhead** | 0 bytes (pure passive observation) | 20-second active burst |

---

## 📜 License

This project is licensed under the MIT License.
