
"""
modules/gui.py

PyQt5 GUI for the Modbus RTU Tester.

This module contains:

- ModbusGui (QtWidgets.QMainWindow)

Tabs:
    * "Modbus Tester" tab:
        - choose COM port and serial parameters
        - select register type (holding, input, coils, discrete inputs)
        - select address range and scaling
        - read a block of values (single-shot or live polling)
        - write a single holding register or coil
        - view raw Modbus RTU frames (TX/RX) and decoded exceptions
    * "Device Scanner" tab:
        - choose COM port and serial parameters
        - choose a slave ID range
        - scan the RS485 bus for responding devices

All actual Modbus operations are delegated to ModbusClient, which lives
in modules/modbus.py and is imported here.
"""

from __future__ import annotations

from typing import List, Union
import time

import serial
import serial.tools.list_ports
from PyQt5 import QtCore, QtGui, QtWidgets

from modules.modbus import ModbusClient


class ModbusGui(QtWidgets.QMainWindow):
    """
    Main window for the Modbus RTU Test GUI.

    This class focuses on UI concerns:
    - Widgets, layout, and theming
    - Collecting user inputs and displaying results
    - Delegating Modbus operations to ModbusClient
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ash's Modbus Tester")
        self.resize(1000, 720)

        # Internal state
        self._poll_timer = QtCore.QTimer(self)
        self._poll_timer.timeout.connect(self._on_poll_timer)
        self._poll_in_progress = False

        self._create_widgets()
        self._create_layouts()
        self._create_connections()
        self._apply_dark_theme()

        # Initialise defaults and ports AFTER widgets/layouts exist
        self._populate_serial_defaults()
        self._populate_scan_defaults()
        self._refresh_ports()
        self._refresh_scan_ports()

    # ------------------------------------------------------------------
    # UI creation
    # ------------------------------------------------------------------
    def _create_widgets(self) -> None:
        """Create all widgets for both tabs and shared elements."""

        # =========================
        # Main tester tab widgets
        # =========================

        # --- Connection widgets ---
        self.port_label = QtWidgets.QLabel("COM Port:")
        self.port_combo = QtWidgets.QComboBox()
        self.refresh_ports_btn = QtWidgets.QPushButton("Refresh")

        self.slave_id_label = QtWidgets.QLabel("Slave ID:")
        self.slave_id_spin = QtWidgets.QSpinBox()
        self.slave_id_spin.setRange(1, 247)
        self.slave_id_spin.setValue(1)  # Reasonable default

        # --- Serial settings widgets ---
        self.baud_label = QtWidgets.QLabel("Baud:")
        self.baud_combo = QtWidgets.QComboBox()

        self.parity_label = QtWidgets.QLabel("Parity:")
        self.parity_combo = QtWidgets.QComboBox()

        self.databits_label = QtWidgets.QLabel("Data bits:")
        self.databits_combo = QtWidgets.QComboBox()

        self.stopbits_label = QtWidgets.QLabel("Stop bits:")
        self.stopbits_combo = QtWidgets.QComboBox()

        # --- Register settings widgets ---
        self.register_type_label = QtWidgets.QLabel("Register type:")
        self.register_type_combo = QtWidgets.QComboBox()

        self.reg_start_label = QtWidgets.QLabel("Start address:")
        self.reg_start_spin = QtWidgets.QSpinBox()
        self.reg_start_spin.setRange(0, 65535)

        self.reg_count_label = QtWidgets.QLabel("Number of points:")
        self.reg_count_spin = QtWidgets.QSpinBox()
        self.reg_count_spin.setRange(1, 125)

        self.decimals_label = QtWidgets.QLabel("Decimals (for registers):")
        self.decimals_spin = QtWidgets.QSpinBox()
        self.decimals_spin.setRange(0, 6)
        self.decimals_spin.setValue(0)

        self.signed_checkbox = QtWidgets.QCheckBox("Signed values (for registers)")

        # --- Polling controls ---
        self.poll_enable_checkbox = QtWidgets.QCheckBox("Enable live polling")
        self.poll_interval_label = QtWidgets.QLabel("Poll interval (ms):")
        self.poll_interval_spin = QtWidgets.QSpinBox()
        self.poll_interval_spin.setRange(100, 10000)
        self.poll_interval_spin.setSingleStep(100)
        self.poll_interval_spin.setValue(1000)

        # --- Read action & status ---
        self.fetch_btn = QtWidgets.QPushButton("Fetch Data (single read)")
        self.fetch_btn.setFixedHeight(40)

        self.status_label = QtWidgets.QLabel("Ready.")
        self.status_label.setWordWrap(True)

        # --- Write widgets ---
        self.write_addr_label = QtWidgets.QLabel("Address:")
        self.write_addr_spin = QtWidgets.QSpinBox()
        self.write_addr_spin.setRange(0, 65535)

        self.write_value_label = QtWidgets.QLabel("Value:")
        self.write_value_edit = QtWidgets.QLineEdit()
        self.write_value_edit.setPlaceholderText("e.g. 123 or 1/0 or true/false")

        self.write_btn = QtWidgets.QPushButton("Write Value")

        write_group_title = "Write single value (coils / holding registers only)"
        self.write_group = QtWidgets.QGroupBox(write_group_title)

        # --- Table for results ---
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Address", "Raw", "Scaled"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)

        # --- Operation log (shared between tabs) ---
        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(220)
        self.log_view.setPlaceholderText(
            "Operation log will appear here.\n"
            "Each read/write/scan will be summarised.\n"
            "Raw RTU frames (TX/RX) and Modbus exceptions will also be shown."
        )

        # =========================
        # Device scanner tab widgets
        # =========================

        # Scanner connection widgets
        self.scan_port_label = QtWidgets.QLabel("COM Port:")
        self.scan_port_combo = QtWidgets.QComboBox()
        self.scan_refresh_btn = QtWidgets.QPushButton("Refresh")

        self.scan_baud_label = QtWidgets.QLabel("Baud:")
        self.scan_baud_combo = QtWidgets.QComboBox()

        self.scan_parity_label = QtWidgets.QLabel("Parity:")
        self.scan_parity_combo = QtWidgets.QComboBox()

        self.scan_databits_label = QtWidgets.QLabel("Data bits:")
        self.scan_databits_combo = QtWidgets.QComboBox()

        self.scan_stopbits_label = QtWidgets.QLabel("Stop bits:")
        self.scan_stopbits_combo = QtWidgets.QComboBox()

        # Scanner settings
        self.scan_id_start_label = QtWidgets.QLabel("Slave ID start:")
        self.scan_id_start_spin = QtWidgets.QSpinBox()
        self.scan_id_start_spin.setRange(1, 247)

        self.scan_id_end_label = QtWidgets.QLabel("Slave ID end:")
        self.scan_id_end_spin = QtWidgets.QSpinBox()
        self.scan_id_end_spin.setRange(1, 247)

        self.scan_timeout_label = QtWidgets.QLabel("Timeout (s):")
        self.scan_timeout_spin = QtWidgets.QDoubleSpinBox()
        self.scan_timeout_spin.setRange(0.05, 5.0)
        self.scan_timeout_spin.setSingleStep(0.05)
        self.scan_timeout_spin.setDecimals(2)

        self.scan_btn = QtWidgets.QPushButton("Scan bus for devices")
        self.scan_btn.setFixedHeight(40)

        self.scan_status_label = QtWidgets.QLabel(
            "Set parameters and click 'Scan bus for devices'."
        )
        self.scan_status_label.setWordWrap(True)

        # Scanner results table
        self.scan_table = QtWidgets.QTableWidget()
        self.scan_table.setColumnCount(3)
        self.scan_table.setHorizontalHeaderLabels(["Slave ID", "Status", "Details"])
        self.scan_table.verticalHeader().setVisible(False)
        self.scan_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.scan_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.scan_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.scan_table.horizontalHeader().setStretchLastSection(True)

        # =========================
        # Tab widget
        # =========================
        self.tabs = QtWidgets.QTabWidget()

    def _create_layouts(self) -> None:
        """Layout both tabs and add them to the QTabWidget."""

        # --------------------------------------------------------------
        # Main tester tab layout
        # --------------------------------------------------------------
        conn_layout = QtWidgets.QGridLayout()
        conn_layout.addWidget(self.port_label, 0, 0)
        conn_layout.addWidget(self.port_combo, 0, 1)
        conn_layout.addWidget(self.refresh_ports_btn, 0, 2)

        conn_layout.addWidget(self.slave_id_label, 1, 0)
        conn_layout.addWidget(self.slave_id_spin, 1, 1)

        conn_group = QtWidgets.QGroupBox("Connection")
        conn_group.setLayout(conn_layout)

        serial_layout = QtWidgets.QGridLayout()
        serial_layout.addWidget(self.baud_label, 0, 0)
        serial_layout.addWidget(self.baud_combo, 0, 1)

        serial_layout.addWidget(self.parity_label, 1, 0)
        serial_layout.addWidget(self.parity_combo, 1, 1)

        serial_layout.addWidget(self.databits_label, 2, 0)
        serial_layout.addWidget(self.databits_combo, 2, 1)

        serial_layout.addWidget(self.stopbits_label, 3, 0)
        serial_layout.addWidget(self.stopbits_combo, 3, 1)

        serial_group = QtWidgets.QGroupBox("Serial settings")
        serial_group.setLayout(serial_layout)

        reg_layout = QtWidgets.QGridLayout()
        reg_layout.addWidget(self.register_type_label, 0, 0)
        reg_layout.addWidget(self.register_type_combo, 0, 1)

        reg_layout.addWidget(self.reg_start_label, 1, 0)
        reg_layout.addWidget(self.reg_start_spin, 1, 1)

        reg_layout.addWidget(self.reg_count_label, 2, 0)
        reg_layout.addWidget(self.reg_count_spin, 2, 1)

        reg_layout.addWidget(self.decimals_label, 3, 0)
        reg_layout.addWidget(self.decimals_spin, 3, 1)

        reg_layout.addWidget(self.signed_checkbox, 4, 0, 1, 2)

        reg_group = QtWidgets.QGroupBox("Register settings")
        reg_group.setLayout(reg_layout)

        write_layout = QtWidgets.QGridLayout()
        write_layout.addWidget(self.write_addr_label, 0, 0)
        write_layout.addWidget(self.write_addr_spin, 0, 1)

        write_layout.addWidget(self.write_value_label, 1, 0)
        write_layout.addWidget(self.write_value_edit, 1, 1)

        write_layout.addWidget(self.write_btn, 2, 0, 1, 2)
        self.write_group.setLayout(write_layout)

        # Polling controls
        poll_layout = QtWidgets.QHBoxLayout()
        poll_layout.addWidget(self.poll_interval_label)
        poll_layout.addWidget(self.poll_interval_spin)
        poll_widget = QtWidgets.QWidget()
        poll_widget.setLayout(poll_layout)

        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(conn_group)
        left_layout.addWidget(serial_group)
        left_layout.addWidget(reg_group)
        left_layout.addWidget(self.write_group)
        left_layout.addStretch()
        left_layout.addWidget(self.poll_enable_checkbox)
        left_layout.addWidget(poll_widget)
        left_layout.addWidget(self.fetch_btn)
        left_layout.addWidget(self.status_label)

        left_widget = QtWidgets.QWidget()
        left_widget.setLayout(left_layout)

        log_group = QtWidgets.QGroupBox("Operation log")
        log_layout = QtWidgets.QVBoxLayout()
        log_layout.addWidget(self.log_view)
        log_group.setLayout(log_layout)

        right_layout = QtWidgets.QVBoxLayout()
        right_layout.addWidget(self.table, 1)
        right_layout.addWidget(log_group, 0)

        right_widget = QtWidgets.QWidget()
        right_widget.setLayout(right_layout)

        main_tab_layout = QtWidgets.QHBoxLayout()
        main_tab_layout.addWidget(left_widget, 0)
        main_tab_layout.addWidget(right_widget, 1)

        main_tab = QtWidgets.QWidget()
        main_tab.setLayout(main_tab_layout)

        # --------------------------------------------------------------
        # Device scanner tab layout
        # --------------------------------------------------------------
        scan_conn_layout = QtWidgets.QGridLayout()
        scan_conn_layout.addWidget(self.scan_port_label, 0, 0)
        scan_conn_layout.addWidget(self.scan_port_combo, 0, 1)
        scan_conn_layout.addWidget(self.scan_refresh_btn, 0, 2)

        scan_conn_layout.addWidget(self.scan_baud_label, 1, 0)
        scan_conn_layout.addWidget(self.scan_baud_combo, 1, 1)

        scan_conn_layout.addWidget(self.scan_parity_label, 2, 0)
        scan_conn_layout.addWidget(self.scan_parity_combo, 2, 1)

        scan_conn_layout.addWidget(self.scan_databits_label, 3, 0)
        scan_conn_layout.addWidget(self.scan_databits_combo, 3, 1)

        scan_conn_layout.addWidget(self.scan_stopbits_label, 4, 0)
        scan_conn_layout.addWidget(self.scan_stopbits_combo, 4, 1)

        scan_conn_group = QtWidgets.QGroupBox("Scan connection settings")
        scan_conn_group.setLayout(scan_conn_layout)

        scan_settings_layout = QtWidgets.QGridLayout()
        scan_settings_layout.addWidget(self.scan_id_start_label, 0, 0)
        scan_settings_layout.addWidget(self.scan_id_start_spin, 0, 1)

        scan_settings_layout.addWidget(self.scan_id_end_label, 1, 0)
        scan_settings_layout.addWidget(self.scan_id_end_spin, 1, 1)

        scan_settings_layout.addWidget(self.scan_timeout_label, 2, 0)
        scan_settings_layout.addWidget(self.scan_timeout_spin, 2, 1)

        scan_settings_group = QtWidgets.QGroupBox("Scan settings")
        scan_settings_group.setLayout(scan_settings_layout)

        scan_controls_layout = QtWidgets.QVBoxLayout()
        scan_controls_layout.addWidget(scan_conn_group)
        scan_controls_layout.addWidget(scan_settings_group)
        scan_controls_layout.addStretch()
        scan_controls_layout.addWidget(self.scan_btn)
        scan_controls_layout.addWidget(self.scan_status_label)

        scan_controls_widget = QtWidgets.QWidget()
        scan_controls_widget.setLayout(scan_controls_layout)

        scan_right_layout = QtWidgets.QVBoxLayout()
        scan_right_layout.addWidget(self.scan_table)

        scan_right_widget = QtWidgets.QWidget()
        scan_right_widget.setLayout(scan_right_layout)

        scan_tab_layout = QtWidgets.QHBoxLayout()
        scan_tab_layout.addWidget(scan_controls_widget, 0)
        scan_tab_layout.addWidget(scan_right_widget, 1)

        scan_tab = QtWidgets.QWidget()
        scan_tab.setLayout(scan_tab_layout)

        # --------------------------------------------------------------
        # Tab widget as central widget
        # --------------------------------------------------------------
        self.tabs.addTab(main_tab, "Modbus Tester")
        self.tabs.addTab(scan_tab, "Device Scanner")

        self.setCentralWidget(self.tabs)

    def _create_connections(self) -> None:
        """Wire up button signals and tab logic."""
        self.refresh_ports_btn.clicked.connect(self._refresh_ports)
        self.fetch_btn.clicked.connect(self._on_fetch_clicked)
        self.write_btn.clicked.connect(self._on_write_single_clicked)
        self.register_type_combo.currentIndexChanged.connect(self._on_register_type_changed)

        self.poll_enable_checkbox.toggled.connect(self._on_poll_toggled)

        self.scan_refresh_btn.clicked.connect(self._refresh_scan_ports)
        self.scan_btn.clicked.connect(self._on_scan_clicked)

    # ------------------------------------------------------------------
    # Theming / defaults
    # ------------------------------------------------------------------
    def _apply_dark_theme(self) -> None:
        """
        Apply a high-contrast dark blue theme with bright text.
        """

        # Backgrounds
        base_bg = QtGui.QColor(20, 26, 48)    # deep navy blue
        panel_bg = QtGui.QColor(28, 34, 56)   # slightly lighter navy
        field_bg = QtGui.QColor(36, 42, 64)   # input fields, tables
        alt_bg = QtGui.QColor(50, 58, 84)

        # Text colours
        text_main = QtGui.QColor(230, 235, 245)   # bright near-white
        text_disabled = QtGui.QColor(130, 135, 150)

        # Accent / highlight
        accent = QtGui.QColor(80, 140, 255)       # electric blue highlight
        accent_text = QtGui.QColor(0, 0, 0)

        palette = QtGui.QPalette()

        palette.setColor(QtGui.QPalette.Window, base_bg)
        palette.setColor(QtGui.QPalette.WindowText, text_main)
        palette.setColor(QtGui.QPalette.Base, field_bg)
        palette.setColor(QtGui.QPalette.AlternateBase, alt_bg)
        palette.setColor(QtGui.QPalette.ToolTipBase, panel_bg)
        palette.setColor(QtGui.QPalette.ToolTipText, text_main)
        palette.setColor(QtGui.QPalette.Text, text_main)
        palette.setColor(QtGui.QPalette.Button, panel_bg)
        palette.setColor(QtGui.QPalette.ButtonText, text_main)
        palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
        palette.setColor(QtGui.QPalette.Highlight, accent)
        palette.setColor(QtGui.QPalette.HighlightedText, accent_text)

        palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, text_disabled)
        palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, text_disabled)

        self.setPalette(palette)

        self.setStyleSheet(f"""
            QWidget {{
                font-size: 14px;
                color: rgb({text_main.red()}, {text_main.green()}, {text_main.blue()});
                background-color: rgb({base_bg.red()}, {base_bg.green()}, {base_bg.blue()});
            }}

            QGroupBox {{
                margin-top: 10px;
                padding: 8px;
                border: 1px solid #3A4371;
                border-radius: 6px;
                background-color: rgb({panel_bg.red()}, {panel_bg.green()}, {panel_bg.blue()});
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2px 6px;
            }}

            QPushButton {{
                background-color: rgb(40, 90, 160);
                color: white;
                padding: 6px 12px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: rgb(60, 120, 200);
            }}
            QPushButton:pressed {{
                background-color: rgb(30, 70, 130);
            }}

            QComboBox, QSpinBox, QLineEdit, QPlainTextEdit {{
                background-color: rgb({field_bg.red()}, {field_bg.green()}, {field_bg.blue()});
                color: rgb({text_main.red()}, {text_main.green()}, {text_main.blue()});
                border: 1px solid #5060A0;
                border-radius: 4px;
                padding: 2px 6px;
            }}

            QComboBox QAbstractItemView {{
                background-color: rgb({field_bg.red()}, {field_bg.green()}, {field_bg.blue()});
                color: rgb({text_main.red()}, {text_main.green()}, {text_main.blue()});
                selection-background-color: rgb({accent.red()}, {accent.green()}, {accent.blue()});
            }}

            QTableWidget {{
                background-color: rgb({field_bg.red()}, {field_bg.green()}, {field_bg.blue()});
                alternate-background-color: rgb({alt_bg.red()}, {alt_bg.green()}, {alt_bg.blue()});
                gridline-color: #7080B0;
                border-radius: 4px;
            }}
            QHeaderView::section {{
                background-color: rgb(40, 48, 72);
                color: rgb({text_main.red()}, {text_main.green()}, {text_main.blue()});
                padding: 4px;
                border: none;
                border-right: 1px solid #5560A0;
            }}

            QScrollBar:vertical {{
                background: rgb(30, 36, 54);
                width: 12px;
                margin: 0px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: rgb(80, 120, 200);
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgb(100, 150, 240);
            }}

            /* Tabs */
            QTabWidget::pane {{
                border: 1px solid #3A4371;
                background-color: rgb({base_bg.red()}, {base_bg.green()}, {base_bg.blue()});
            }}

            QTabBar::tab {{
                background-color: rgb({panel_bg.red()}, {panel_bg.green()}, {panel_bg.blue()});
                color: rgb({text_main.red()}, {text_main.green()}, {text_main.blue()});
                padding: 6px 16px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border: 1px solid #3A4371;
                margin-right: 2px;
            }}

            QTabBar::tab:selected {{
                background-color: rgb(40, 90, 160);
                color: white;
            }}

            QTabBar::tab:hover {{
                background-color: rgb(60, 120, 200);
            }}
        """)

    def _populate_serial_defaults(self) -> None:
        """
        Fill the serial-parameter dropdowns and default register settings
        for the main tester tab.
        """
        # Baud rates
        for baud in [9600, 19200, 38400, 57600, 115200]:
            self.baud_combo.addItem(str(baud))
        self.baud_combo.setCurrentText("9600")

        # Parity
        self.parity_combo.addItems(["None", "Even", "Odd"])
        self.parity_combo.setCurrentText("None")

        # Data bits
        self.databits_combo.addItems(["8", "7"])
        self.databits_combo.setCurrentText("8")

        # Stop bits
        self.stopbits_combo.addItems(["1", "2"])
        self.stopbits_combo.setCurrentText("1")

        # Register types
        self.register_type_combo.addItems([
            "Holding Registers (4xxxx)",
            "Input Registers (3xxxx)",
            "Coils (0xxxx)",
            "Discrete Inputs (1xxxx)",
        ])
        self.register_type_combo.setCurrentIndex(0)

        # Default register range
        self.reg_start_spin.setValue(0)
        self.reg_count_spin.setValue(4)
        self.decimals_spin.setValue(0)
        self.signed_checkbox.setChecked(False)

        self._on_register_type_changed(self.register_type_combo.currentIndex())

    def _populate_scan_defaults(self) -> None:
        """
        Fill the serial-parameter dropdowns and scan defaults
        for the Device Scanner tab.
        """
        # Baud rates
        for baud in [9600, 19200, 38400, 57600, 115200]:
            self.scan_baud_combo.addItem(str(baud))
        self.scan_baud_combo.setCurrentText("9600")

        # Parity
        self.scan_parity_combo.addItems(["None", "Even", "Odd"])
        self.scan_parity_combo.setCurrentText("None")

        # Data bits
        self.scan_databits_combo.addItems(["8", "7"])
        self.scan_databits_combo.setCurrentText("8")

        # Stop bits
        self.scan_stopbits_combo.addItems(["1", "2"])
        self.scan_stopbits_combo.setCurrentText("1")

        # Scan ID range
        self.scan_id_start_spin.setValue(1)
        self.scan_id_end_spin.setValue(10)

        # Timeout
        self.scan_timeout_spin.setValue(0.3)

    # ------------------------------------------------------------------
    # Port enumeration
    # ------------------------------------------------------------------
    def _refresh_ports(self) -> None:
        """
        Scan available serial ports and populate COM port dropdown
        for the main tester tab.
        """
        current = self.port_combo.currentText()
        self.port_combo.clear()

        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            self.port_combo.addItem(p.device)

        if current and current in [p.device for p in ports]:
            idx = self.port_combo.findText(current)
            if idx >= 0:
                self.port_combo.setCurrentIndex(idx)

        if self.port_combo.count() == 0:
            self.status_label.setText(
                "No serial ports found. Plug in your USB-RS485 adapter and click Refresh."
            )
        else:
            self.status_label.setText(
                "Ready. Select a COM port, set the parameters, and click 'Fetch Data'."
            )

    def _refresh_scan_ports(self) -> None:
        """
        Scan available serial ports and populate COM port dropdown
        for the Device Scanner tab.
        """
        current = self.scan_port_combo.currentText()
        self.scan_port_combo.clear()

        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            self.scan_port_combo.addItem(p.device)

        if current and current in [p.device for p in ports]:
            idx = self.scan_port_combo.findText(current)
            if idx >= 0:
                self.scan_port_combo.setCurrentIndex(idx)

        if self.scan_port_combo.count() == 0:
            self.scan_status_label.setText(
                "No serial ports found. Plug in your USB-RS485 adapter and click Refresh."
            )
        else:
            self.scan_status_label.setText(
                "Set slave ID range and click 'Scan bus for devices'."
            )

    # ------------------------------------------------------------------
    # Register type handling
    # ------------------------------------------------------------------
    def _on_register_type_changed(self, index: int) -> None:
        """
        Enable/disable scaling options depending on whether we're dealing with
        register values (analog) or bits (coils/inputs).
        """
        reg_type = self.register_type_combo.currentText()
        is_bit_type = reg_type.startswith("Coils") or reg_type.startswith("Discrete Inputs")

        self.decimals_spin.setEnabled(not is_bit_type)
        self.signed_checkbox.setEnabled(not is_bit_type)

        if is_bit_type:
            self.decimals_spin.setValue(0)
            self.signed_checkbox.setChecked(False)

    # ------------------------------------------------------------------
    # Helpers to build ModbusClient from UI (main tab)
    # ------------------------------------------------------------------
    def _build_client_from_ui(self) -> ModbusClient:
        """
        Build a ModbusClient from the current UI settings (main tester tab).
        """
        port = self.port_combo.currentText()
        if not port:
            raise RuntimeError("No COM port selected.")

        slave_id = self.slave_id_spin.value()
        baud = int(self.baud_combo.currentText())

        parity_text = self.parity_combo.currentText()
        if parity_text == "None":
            parity = serial.PARITY_NONE
        elif parity_text == "Even":
            parity = serial.PARITY_EVEN
        else:
            parity = serial.PARITY_ODD

        databits = int(self.databits_combo.currentText())
        stopbits = int(self.stopbits_combo.currentText())

        client = ModbusClient(
            port=port,
            slave_id=slave_id,
            baudrate=baud,
            parity=parity,
            databits=databits,
            stopbits=stopbits,
            timeout=0.5,
            frame_logger=self._frame_logger,
        )
        return client

    # ------------------------------------------------------------------
    # Live polling
    # ------------------------------------------------------------------
    def _on_poll_toggled(self, enabled: bool) -> None:
        """
        Enable or disable live polling mode.
        """
        if enabled:
            interval_ms = self.poll_interval_spin.value()
            self._poll_timer.start(interval_ms)
            self.fetch_btn.setEnabled(False)
            self._append_log(
                f"LIVE POLLING enabled → interval {interval_ms} ms "
                f"using current Modbus settings."
            )
            self.status_label.setText(
                f"Live polling enabled ({interval_ms} ms)."
            )
        else:
            self._poll_timer.stop()
            self.fetch_btn.setEnabled(True)
            self._append_log("LIVE POLLING disabled.")
            self.status_label.setText("Live polling disabled. Ready.")

    def _on_poll_timer(self) -> None:
        """
        Called periodically when live polling is enabled.
        """
        if self._poll_in_progress:
            # Skip this tick if the previous read is still running
            return
        self._poll_in_progress = True
        try:
            self._perform_read(from_poll=True)
        finally:
            self._poll_in_progress = False

    # ------------------------------------------------------------------
    # Fetch (read) logic
    # ------------------------------------------------------------------
    def _on_fetch_clicked(self) -> None:
        """
        Handle click on the "Fetch Data" button (single-shot read).
        """
        self._perform_read(from_poll=False)

    def _perform_read(self, from_poll: bool) -> None:
        """
        Core read logic used by both single-shot fetch and live polling.

        If from_poll=True, we avoid modal error popups and just log.
        """
        try:
            client = self._build_client_from_ui()
        except Exception as exc:
            if from_poll:
                self._append_log(f"ERROR building client during poll: {exc}")
                self.status_label.setText(f"Poll error: {exc}")
            else:
                self._show_error(str(exc))
            return

        start_addr = self.reg_start_spin.value()
        count = self.reg_count_spin.value()
        decimals = self.decimals_spin.value()
        signed = self.signed_checkbox.isChecked()
        reg_type = self.register_type_combo.currentText()

        if not from_poll:
            self.status_label.setText(
                f"Reading {count} point(s) starting at address {start_addr} "
                f"from slave {client.slave_id} on {client.port}..."
            )
            QtWidgets.QApplication.processEvents()

        self._append_log(
            f"{'POLL' if from_poll else 'READ'} request → "
            f"Type: {reg_type}, Slave: {client.slave_id}, "
            f"Start address: {start_addr}, Count: {count}, "
            f"Decimals: {decimals if not reg_type.startswith(('Coils', 'Discrete Inputs')) else 'n/a'}, "
            f"Signed: {signed if not reg_type.startswith(('Coils', 'Discrete Inputs')) else 'n/a'}"
        )

        try:
            if reg_type.startswith("Holding Registers"):
                # FC3
                values = client.read_holding_registers(
                    start_address=start_addr,
                    count=count,
                    signed=signed,
                )
                fc = 3
            elif reg_type.startswith("Input Registers"):
                # FC4
                values = client.read_input_registers(
                    start_address=start_addr,
                    count=count,
                    signed=signed,
                )
                fc = 4
            elif reg_type.startswith("Coils"):
                # FC1
                values = client.read_coils(
                    start_address=start_addr,
                    count=count,
                )
                fc = 1
            elif reg_type.startswith("Discrete Inputs"):
                # FC2
                values = client.read_discrete_inputs(
                    start_address=start_addr,
                    count=count,
                )
                fc = 2
            else:
                raise ValueError(f"Unsupported register type: {reg_type}")
        except Exception as exc:
            msg = f"Error reading: {exc}"
            self._append_log(f"ERROR during {'POLL' if from_poll else 'READ'}: {exc}")
            if from_poll:
                # Don't spam popups, just update status
                self.status_label.setText(msg)
            else:
                self._show_error(msg)
            return

        self._populate_table(start_addr, values, decimals)

        if from_poll:
            self.status_label.setText(
                f"Live polling OK. Last read returned {len(values)} value(s)."
            )
        else:
            self.status_label.setText("Read OK.")

        self._append_log(
            f"{'POLL' if from_poll else 'READ'} OK (FC{fc}) → "
            f"Received {len(values)} value(s) starting at address {start_addr}."
        )

    # ------------------------------------------------------------------
    # Write logic
    # ------------------------------------------------------------------
    def _on_write_single_clicked(self) -> None:
        """
        Handle click on the "Write Value" button (main tester tab).
        """
        try:
            client = self._build_client_from_ui()
        except Exception as exc:
            self._show_error(str(exc))
            return

        addr = self.write_addr_spin.value()
        value_text = self.write_value_edit.text().strip()
        if not value_text:
            self._show_error("Please enter a value to write.")
            return

        reg_type = self.register_type_combo.currentText()
        decimals = self.decimals_spin.value()
        signed = self.signed_checkbox.isChecked()

        self.status_label.setText(
            f"Writing value to {reg_type} at address {addr} for slave "
            f"{client.slave_id} on {client.port}..."
        )
        QtWidgets.QApplication.processEvents()

        self._append_log(
            f"WRITE request → Type: {reg_type}, Slave: {client.slave_id}, "
            f"Address: {addr}, Raw value: {value_text}, "
            f"Decimals: {decimals if reg_type.startswith('Holding') else 'n/a'}, "
            f"Signed: {signed if reg_type.startswith('Holding') else 'n/a'}"
        )

        try:
            if reg_type.startswith("Holding Registers"):
                # Numeric value with scaling
                numeric = float(value_text)
                client.write_holding_register(
                    address=addr,
                    value=numeric,
                    decimals=decimals,
                    signed=signed,
                )
                fc = 16  # we use FC16 in ModbusClient

            elif reg_type.startswith("Coils"):
                lowered = value_text.lower()
                if lowered in ("1", "on", "true", "high"):
                    bit_value = 1
                elif lowered in ("0", "off", "false", "low"):
                    bit_value = 0
                else:
                    bit_value = int(value_text)
                    if bit_value not in (0, 1):
                        raise ValueError("For coils, only 0 or 1 is allowed.")

                client.write_coil(
                    address=addr,
                    value=bit_value,
                )
                fc = 5

            else:
                raise ValueError("Selected register type is read-only and cannot be written.")

        except Exception as exc:
            self._append_log(f"ERROR during WRITE: {exc}")
            self._show_error(f"Error writing: {exc}")
            return

        self.status_label.setText("Write OK.")
        self._append_log(
            f"WRITE OK (FC{fc}) → {reg_type} at address {addr} updated successfully."
        )

    # ------------------------------------------------------------------
    # Device Scanner logic (second tab)
    # ------------------------------------------------------------------
    def _build_scan_client_for_slave(self, slave_id: int) -> ModbusClient:
        """
        Build a ModbusClient using the scanner tab settings, for a given slave ID.
        """
        port = self.scan_port_combo.currentText()
        if not port:
            raise RuntimeError("No COM port selected for scanning.")

        baud = int(self.scan_baud_combo.currentText())

        parity_text = self.scan_parity_combo.currentText()
        if parity_text == "None":
            parity = serial.PARITY_NONE
        elif parity_text == "Even":
            parity = serial.PARITY_EVEN
        else:
            parity = serial.PARITY_ODD

        databits = int(self.scan_databits_combo.currentText())
        stopbits = int(self.scan_stopbits_combo.currentText())
        timeout = float(self.scan_timeout_spin.value())

        client = ModbusClient(
            port=port,
            slave_id=slave_id,
            baudrate=baud,
            parity=parity,
            databits=databits,
            stopbits=stopbits,
            timeout=timeout,
            frame_logger=self._frame_logger,
        )
        return client

    def _on_scan_clicked(self) -> None:
        """
        Scan a range of slave IDs on the selected port and list responsive devices.
        """
        port = self.scan_port_combo.currentText()
        if not port:
            self._append_log("ERROR: Scan requested but no COM port selected on scanner tab.")
            self.scan_status_label.setText("Please select a COM port before scanning.")
            return

        start_id = self.scan_id_start_spin.value()
        end_id = self.scan_id_end_spin.value()

        if start_id > end_id:
            # Swap to be nice
            start_id, end_id = end_id, start_id
            self.scan_id_start_spin.setValue(start_id)
            self.scan_id_end_spin.setValue(end_id)

        self.scan_table.setRowCount(0)
        total_ids = end_id - start_id + 1

        self.scan_status_label.setText(
            f"Scanning slave IDs {start_id}–{end_id} on {port}..."
        )
        QtWidgets.QApplication.processEvents()

        self._append_log(
            f"SCAN start → Port: {port}, ID range: {start_id}–{end_id}, "
            f"Baud: {self.scan_baud_combo.currentText()}, "
            f"Parity: {self.scan_parity_combo.currentText()}, "
            f"Data bits: {self.scan_databits_combo.currentText()}, "
            f"Stop bits: {self.scan_stopbits_combo.currentText()}, "
            f"Timeout: {self.scan_timeout_spin.value():.2f}s"
        )

        responsive_ids: List[int] = []
        for idx, slave_id in enumerate(range(start_id, end_id + 1), start=1):
            try:
                client = self._build_scan_client_for_slave(slave_id)
            except Exception as exc:
                self._append_log(f"ERROR building client for slave {slave_id}: {exc}")
                self.scan_status_label.setText(f"Error building client: {exc}")
                return

            self.scan_status_label.setText(
                f"Scanning slave ID {slave_id} ({idx}/{total_ids})..."
            )
            QtWidgets.QApplication.processEvents()

            try:
                # Generic probe: try reading holding register 0 (FC3)
                values = client.read_holding_registers(
                    start_address=0,
                    count=1,
                    signed=False,
                )
                detail = f"Responded to FC3 at address 0, value={values[0]}"
                self._add_scan_result_row(slave_id, "Online", detail)
                responsive_ids.append(slave_id)
                self._append_log(
                    f"SCAN: Slave {slave_id} ONLINE → FC3, address 0, value={values[0]}"
                )
            except Exception:
                # No response or error -> ignore silently (can be noisy otherwise)
                pass

        if responsive_ids:
            self.scan_status_label.setText(
                f"Scan complete. Found {len(responsive_ids)} device(s): {responsive_ids}."
            )
            self._append_log(
                f"SCAN complete → Found {len(responsive_ids)} device(s): {responsive_ids}"
            )
        else:
            self.scan_status_label.setText(
                "Scan complete. No devices responded in the selected ID range."
            )
            self._append_log("SCAN complete → No responding devices in this range.")

    def _add_scan_result_row(self, slave_id: int, status: str, details: str) -> None:
        """
        Add a row to the scanner results table for a responding device.
        """
        row = self.scan_table.rowCount()
        self.scan_table.insertRow(row)

        id_item = QtWidgets.QTableWidgetItem(str(slave_id))
        id_item.setTextAlignment(QtCore.Qt.AlignCenter)

        status_item = QtWidgets.QTableWidgetItem(status)
        status_item.setTextAlignment(QtCore.Qt.AlignCenter)

        details_item = QtWidgets.QTableWidgetItem(details)
        details_item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        self.scan_table.setItem(row, 0, id_item)
        self.scan_table.setItem(row, 1, status_item)
        self.scan_table.setItem(row, 2, details_item)

        self.scan_table.resizeColumnsToContents()

    # ------------------------------------------------------------------
    # Table display (main tab)
    # ------------------------------------------------------------------
    def _populate_table(
        self,
        start_address: int,
        values: List[Union[int, float]],
        decimals: int
    ) -> None:
        """
        Fill the QTableWidget with values (main tester tab).
        """
        self.table.setRowCount(len(values))

        scale = 10 ** decimals if decimals > 0 else 1

        for row, raw in enumerate(values):
            addr_item = QtWidgets.QTableWidgetItem(str(start_address + row))
            addr_item.setTextAlignment(QtCore.Qt.AlignCenter)

            raw_item = QtWidgets.QTableWidgetItem(str(raw))
            raw_item.setTextAlignment(QtCore.Qt.AlignCenter)

            if isinstance(raw, (int, float)) and scale != 1:
                scaled_val = float(raw) / float(scale)
                scaled_str = f"{scaled_val:.{decimals}f}"
            else:
                scaled_str = str(raw)

            scaled_item = QtWidgets.QTableWidgetItem(scaled_str)
            scaled_item.setTextAlignment(QtCore.Qt.AlignCenter)

            self.table.setItem(row, 0, addr_item)
            self.table.setItem(row, 1, raw_item)
            self.table.setItem(row, 2, scaled_item)

        self.table.resizeColumnsToContents()

    # ------------------------------------------------------------------
    # Raw frame logger + exception decoder
    # ------------------------------------------------------------------
    def _frame_logger(self, request: bytes, response: bytes) -> None:
        """
        Called by ModbusClient's LoggingInstrument for every transaction.

        Logs raw TX/RX frames and decodes Modbus exceptions if present.
        """
        req_hex = " ".join(f"{b:02X}" for b in request)
        res_hex = " ".join(f"{b:02X}" for b in response)

        self._append_log(f"TX (raw): {req_hex}")
        self._append_log(f"RX (raw): {res_hex}")

        # Detect Modbus exception:
        # Response function code = request FC + 0x80, and third byte is exception code
        if len(response) >= 3:
            func_code = response[1]
            if func_code & 0x80:
                exc_code = response[2]
                desc = self._decode_exception_code(exc_code)
                self._append_log(
                    f"MODBUS EXCEPTION → Code {exc_code}: {desc}"
                )

    @staticmethod
    def _decode_exception_code(code: int) -> str:
        """
        Translate standard Modbus exception codes into human-readable text.
        """
        mapping = {
            1: "Illegal function (the function code is not supported by this device).",
            2: "Illegal data address (you’re asking for a register/coil the device doesn’t implement).",
            3: "Illegal data value (value is outside allowed range or invalid).",
            4: "Slave device failure (internal error in the slave).",
            5: "Acknowledge (request accepted, processing will take place but is not complete).",
            6: "Slave device busy (try again later).",
            8: "Memory parity error (error in device memory).",
            10: "Gateway path unavailable.",
            11: "Gateway target device failed to respond.",
        }
        return mapping.get(code, "Unknown exception code (non-standard or vendor-specific).")

    # ------------------------------------------------------------------
    # Log + error helpers
    # ------------------------------------------------------------------
    def _append_log(self, message: str) -> None:
        """
        Append a timestamped line to the operation log.

        This helps non-experts see, in plain language, what Modbus
        operation was just attempted or completed.
        """
        timestamp = time.strftime("%H:%M:%S")
        self.log_view.appendPlainText(f"[{timestamp}] {message}")
        # Auto-scroll to the bottom
        self.log_view.verticalScrollBar().setValue(
            self.log_view.verticalScrollBar().maximum()
        )

    def _show_error(self, message: str) -> None:
        """
        Show an error in both the status label and a popup message box.
        """
        self.status_label.setText(message)
        QtWidgets.QMessageBox.critical(self, "Error", message)
        self._append_log(f"ERROR: {message}")
