# Real-Time Wi-Fi Analyzer 📡

A native desktop application built with **Python**, **PyQt5**, and **PyQtGraph** for real-time monitoring, throughput analysis, latency tracking, and signal strength (RSSI) diagnostics of your Wi-Fi connection.

---

## 🌟 Key Features

1. **Wi-Fi Connection Enforcement**
   - The analyzer **can only be run when your laptop is connected to Wi-Fi**.
   - If Wi-Fi is disconnected, the **Run Analyzer** button is automatically disabled and locked, and a status banner prompts you to connect to a Wi-Fi network.
   - Auto-detects Wi-Fi connection in real-time — as soon as you connect, the **Run** button unlocks.
   - If the Wi-Fi connection drops while analyzing, the software automatically pauses and displays a warning dialog.

2. **Graph 1: Real-Time Throughput Graph (1Hz Updates)**
   - Visualizes **Download Speed (Mbps)** (Electric Cyan curve) and **Upload Speed (Mbps)** (Emerald Green curve).
   - Dynamically sampled and redrawn at **1Hz** (exactly 1 update per second).
   - Smooth translucent area fills below each curve for instant visual readability.
   - Dynamic auto-scaling Y-axis with live readout legends.

3. **Graph 2: Real-Time Ping Latency Graph (1Hz Updates)**
   - **Real-Time Ping (in ms)**: Measures round-trip latency to your Wi-Fi default gateway (router) or public DNS (Cloudflare `1.1.1.1` / Google `8.8.8.8`). Features an Amber curve with translucent area fill, dynamic auto-scaling, jitter calculation (RFC 1889 standard), and packet loss detection.

4. **Active Speed Probing Mode (Optional)**
   - Toggle **Active Speed Prober** to burst test traffic and benchmark your connection's maximum achievable bandwidth.
   - Leave disabled for standard **Passive Traffic Monitoring** (monitors actual background and foreground network consumption).

5. **Telemetry Metric Cards**
   - High-visibility dashboard cards displaying:
     - **Download Speed**: Current, Peak, and Average (in Mbps)
     - **Upload Speed**: Current, Peak, and Average (in Mbps)
     - **Ping Latency**: Current, Min, Max, Jitter (in ms), and Packet Loss (%)
     - **Signal RSSI**: Current RSSI (in dBm), Signal Quality (%), Channel, and Band

6. **Wi-Fi Hardware & Network Details**
   - Live strip showing SSID, BSSID (Access Point MAC), Wi-Fi Standard (e.g. `802.11ax Wi-Fi 6`, `802.11ac`), Link Transmit/Receive rates, Local IP, and Gateway IP.

7. **Data Export**
   - Export captured session data to **CSV** or **JSON** for reports, network site surveys, or speed troubleshooting.

8. **Simulation Mode**
   - Run with `--simulate` or toggle **Simulation Mode** in the UI to evaluate all features and graphs without requiring an active physical Wi-Fi connection.

---

## 📁 Project Structure

```
realtimewifianalyzer/
├── wifi_analyzer/
│   ├── __init__.py
│   ├── wifi_monitor.py       # Queries Windows WLAN interface for SSID, RSSI, channel, link rates
│   ├── ping_monitor.py       # Asynchronous non-blocking ping & jitter monitor
│   ├── speed_monitor.py      # Real-time 1Hz I/O delta speed calculator (in Mbps)
│   ├── active_probe.py       # Lightweight HTTP burst stream generator for active speed testing
│   ├── data_buffer.py        # Circular time-series buffer and CSV/JSON exporter
│   └── ui/
│       ├── __init__.py
│       ├── main_window.py    # Main PyQt5 dashboard window and 1Hz loop coordinator
│       ├── speed_graph.py    # PyQtGraph widget for Upload & Download speed (Mbps)
│       ├── signal_graph.py   # PyQtGraph widget for Real-Time Ping Latency (ms)
│       ├── connected_axis.py # Custom connected axis item ensuring seamless corner alignment
│       ├── stats_card.py     # Custom telemetry metric card widgets
│       └── styles.py         # Modern Dark Theme QSS stylesheets and color palettes
├── tests/
│   ├── test_wifi_monitor.py  # Unit tests for WLAN parsing and connection state
│   ├── test_ping_monitor.py  # Unit tests for ping latency and jitter calculations
│   ├── test_speed_monitor.py # Unit tests for speed calculation and data buffering
│   └── test_connected_axes.py# Unit tests for axis connection and resize resilience
├── main.py                   # Application launch script
├── requirements.txt          # Python dependencies
└── README.md                 # Documentation and guide
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Operating System**: Windows 10 or Windows 11 (uses native `netsh wlan` and IP Helper routing).
- **Python**: Version 3.8 or higher (tested on Python 3.11).

### 2. Installation
Open a terminal (PowerShell or Command Prompt) in the project directory and install the required dependencies:

```powershell
pip install -r requirements.txt
```

The required dependencies are:
- `PyQt5`: Desktop GUI application framework.
- `pyqtgraph`: Fast, hardware-accelerated 2D real-time plotting library.
- `psutil`: High-precision system network interface I/O monitoring.
- `numpy`: Fast vectorized numerical arrays for time-series buffer handling.

### 3. Running the Analyzer

To start the analyzer:

```powershell
python main.py
```

If you are developing or testing in an environment without physical Wi-Fi hardware:

```powershell
python main.py --simulate
```

---

## 🎮 How to Use

1. **Check Connection Status**:
   - Look at the top-right banner.
   - If you are connected to Wi-Fi, it will show a **green badge** with your Wi-Fi SSID and channel.
   - If not connected, it will show a **red badge** stating `Disconnected from Wi-Fi — Connect to Wi-Fi to Run`, and the **Run** button will remain locked.

2. **Start Analysis**:
   - Click the green **▶ Run Analyzer** button.
   - The button will toggle to **⏸ Pause** and the analyzer will begin updating both graphs and metric cards at **1Hz**.

3. **Select Ping Destination**:
   - Use the **Ping Target** dropdown:
     - `Wi-Fi Gateway (Router)`: Pings your local router IP (e.g. `192.168.1.1` or `192.168.100.1`), measuring pure over-the-air Wi-Fi latency.
     - `Cloudflare (1.1.1.1)` or `Google DNS (8.8.8.8)`: Measures end-to-end internet latency.

4. **Enable Active Speed Test (Optional)**:
   - Check the **Active Speed Prober** checkbox to burst test streams every second and observe the maximum bandwidth capacity of your Wi-Fi link.
   - Uncheck it to return to passive monitoring mode.

5. **Adjust Time Window**:
   - Change the **Window** dropdown (`30 seconds`, `60 seconds`, `120 seconds`, `300 seconds`) to zoom in on recent spikes or observe broader trends.

6. **Export Data**:
   - Click **📥 Export Data** to save the recorded telemetry session as a `.csv` or `.json` file.

---

## ⚡ Active Speed Prober vs. Passive Traffic Monitoring

The **Active Speed Prober** checkbox in the toolbar controls *how* your upload and download speeds are evaluated on the real-time throughput graph:

### 1. Unchecked (Default: Passive Traffic Monitoring)
* **How it works**: The software passively observes your active Wi-Fi network interface using `psutil`. It calculates the exact amount of data currently passing through the Wi-Fi card per second.
* **Expected graph output**:
  * If you are streaming high-definition video, playing an online game, or downloading files, the graph reflects your real current consumption (e.g., 20–100+ Mbps).
  * If your computer is sitting idle without web activity, the graph will naturally hover around **0.0–0.5 Mbps** (small background system telemetry and keep-alive packets).
* **Network impact**: Zero extra data consumed (0 bytes overhead).

### 2. Checked (Active Speed Prober Mode)
* **How it works**: A dedicated background worker thread generates lightweight, continuous 1-second burst traffic (downloading small stream chunks from fast CDN test endpoints like Cloudflare and uploading small burst packets).
* **Expected graph output**:
  * The graph measures and displays your **maximum available throughput capacity** live at 1Hz, even when you aren't doing any browsing or file downloading.
  * You can walk around your room or office and watch how physical obstacles, walls, and distance dynamically affect your available Wi-Fi link speed in real-time.
* **Network impact**: Consumes small bursts of test data (~1–2 MB per second while active).

### Summary Comparison

| Mode | When to Use | Data Usage | Graph Representation |
| :--- | :--- | :--- | :--- |
| **Passive Monitoring** *(Unchecked)* | To observe actual ongoing background and application network traffic. | None (0 extra bytes) | Actual live bandwidth consumption. |
| **Active Speed Prober** *(Checked)* | To benchmark and diagnose the maximum speed your Wi-Fi link can currently achieve. | Minimal test bursts (~1–2 MB/s) | Maximum achievable Wi-Fi capacity. |

---

## 🧪 Running Unit Tests

Run the complete test suite:

```powershell
python -m unittest discover tests
```

---

## ⚙️ Technical Architecture Details

| Metric | Source / Method | Unit | Description |
| :--- | :--- | :--- | :--- |
| **Download Speed** | `psutil.net_io_counters(pernic=True)` | `Mbps` | Sampled every 1.0 second: `(delta_bytes_recv * 8) / (dt * 1_000_000)` |
| **Upload Speed** | `psutil.net_io_counters(pernic=True)` | `Mbps` | Sampled every 1.0 second: `(delta_bytes_sent * 8) / (dt * 1_000_000)` |
| **Ping Latency** | Non-blocking background worker (`ping -n 1 -w 800 <host>`) | `ms` | Round-trip time to access point gateway or DNS |
| **Jitter** | RFC 1889 / RFC 3550 statistical variance | `ms` | Running jitter smoothed over successive ping measurements |
| **RSSI** | `netsh wlan show interfaces` | `dBm` / `dB` | Exact signal strength reported by Windows WLAN API |
| **Signal Quality** | Windows Native WLAN | `%` | Percentage signal quality (0% to 100%) |

---

## 📜 License

This project is licensed under the MIT License.
