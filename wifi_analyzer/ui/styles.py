"""
Modern Dark Theme stylesheets and color palette for the Wi-Fi Analyzer.
"""

PALETTE = {
    "bg_main": "#0f131a",
    "bg_panel": "#171c26",
    "bg_card": "#1d2331",
    "bg_card_hover": "#252d3e",
    "border": "#283347",
    "border_highlight": "#3b4863",
    "text_primary": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    
    # Accent colors for curves and telemetry
    "download_cyan": "#00e5ff",
    "download_cyan_fill": "#00e5ff22",
    "upload_green": "#00e676",
    "upload_green_fill": "#00e67622",
    "ping_amber": "#ffb300",
    "ping_amber_fill": "#ffb30022",
    "rssi_magenta": "#e040fb",
    "rssi_magenta_fill": "#e040fb22",
    
    # State colors
    "connected_green": "#10b981",
    "disconnected_red": "#ef4444",
    "warning_orange": "#f59e0b",
}

MAIN_STYLE_SHEET = f"""
QMainWindow {{
    background-color: {PALETTE['bg_main']};
}}

QWidget {{
    color: {PALETTE['text_primary']};
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}}

/* Top Banner */
QFrame#bannerFrame {{
    background-color: {PALETTE['bg_panel']};
    border-bottom: 1px solid {PALETTE['border']};
    padding: 6px;
}}

QFrame#controlToolbar {{
    background-color: {PALETTE['bg_panel']};
    border-radius: 8px;
    border: 1px solid {PALETTE['border']};
    padding: 8px;
}}

/* Buttons */
QPushButton {{
    background-color: #263248;
    color: #f8fafc;
    border: 1px solid {PALETTE['border_highlight']};
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 600;
    font-size: 13px;
}}

QPushButton:hover {{
    background-color: #334155;
    border-color: #64748b;
}}

QPushButton:pressed {{
    background-color: #1e293b;
}}

QPushButton:disabled {{
    background-color: #1e2430;
    color: #475569;
    border-color: #27303f;
}}

/* Primary Run Button */
QPushButton#btnRun {{
    background-color: #059669;
    border: 1px solid #10b981;
    color: #ffffff;
    font-weight: bold;
    font-size: 13px;
}}

QPushButton#btnRun:hover {{
    background-color: #10b981;
}}

QPushButton#btnRun:pressed {{
    background-color: #047857;
}}

QPushButton#btnRun:disabled {{
    background-color: #1c2e28;
    border-color: #284439;
    color: #4b6b5d;
}}

/* Stop Button */
QPushButton#btnStop {{
    background-color: #dc2626;
    border: 1px solid #ef4444;
    color: #ffffff;
    font-weight: bold;
}}

QPushButton#btnStop:hover {{
    background-color: #ef4444;
}}

QPushButton#btnStop:pressed {{
    background-color: #b91c1c;
}}

/* Combo Box & Spin Box */
QComboBox {{
    background-color: {PALETTE['bg_card']};
    border: 1px solid {PALETTE['border']};
    border-radius: 6px;
    padding: 5px 12px;
    color: {PALETTE['text_primary']};
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {PALETTE['border_highlight']};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid {PALETTE['border']};
}}

QComboBox QAbstractItemView {{
    background-color: {PALETTE['bg_card']};
    color: {PALETTE['text_primary']};
    selection-background-color: #334155;
    border: 1px solid {PALETTE['border']};
}}

/* Checkbox */
QCheckBox {{
    spacing: 8px;
    color: {PALETTE['text_secondary']};
    font-weight: 500;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid {PALETTE['border_highlight']};
    background-color: {PALETTE['bg_card']};
}}

QCheckBox::indicator:checked {{
    background-color: #0ea5e9;
    border-color: #38bdf8;
}}

/* Card Frame */
QFrame.metricCard {{
    background-color: {PALETTE['bg_card']};
    border: 1px solid {PALETTE['border']};
    border-radius: 10px;
    padding: 12px;
}}

QFrame.metricCard:hover {{
    border-color: {PALETTE['border_highlight']};
    background-color: {PALETTE['bg_card_hover']};
}}

/* Splitter */
QSplitter::handle {{
    background-color: {PALETTE['border']};
    width: 2px;
    height: 2px;
}}

/* Status Bar */
QStatusBar {{
    background-color: {PALETTE['bg_panel']};
    color: {PALETTE['text_secondary']};
    border-top: 1px solid {PALETTE['border']};
}}

/* Dialogs & Message Boxes */
QDialog, QMessageBox {{
    background-color: {PALETTE['bg_panel']};
    color: {PALETTE['text_primary']};
}}

QMessageBox QLabel {{
    color: #f8fafc;
    background-color: transparent;
    font-size: 13px;
}}

QMessageBox QLabel#qt_msgbox_label {{
    color: #f8fafc;
}}

QMessageBox QLabel#qt_msgboxex_icon_label {{
    background-color: transparent;
}}

QMessageBox QPushButton {{
    background-color: #263248;
    color: #ffffff;
    border: 1px solid {PALETTE['border_highlight']};
    border-radius: 6px;
    padding: 7px 22px;
    min-width: 75px;
    font-weight: 600;
    font-size: 13px;
}}

QMessageBox QPushButton:hover {{
    background-color: #334155;
    border-color: #64748b;
}}

QMessageBox QPushButton:pressed {{
    background-color: #1e293b;
}}

QMessageBox QPushButton:focus {{
    border-color: #38bdf8;
}}
"""
