
"""
modules/gui.py

PyQt5 GUI for the Modbus RTU Tester.

This module contains:

- ModbusGui (QtWidgets.QMainWindow)
    The GUI that lets the user:
        * choose COM port and serial parameters
        * select register type (holding, input, coils, discrete inputs)
        * select address range and scaling
        * read a block of values
        * write a single holding register or coil

All actual Modbus operations are delegated to ModbusClient, which lives
in modules/modbus.py and is imported here.
"""

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
        self.resize(950, 650)

        self._create_widgets()
        self._create_layouts()
        self._create_connections()
        self._apply_dark_theme()

        self._populate_serial_defaults()
        self._refresh_ports()

    # ------------------------------------------------------------------
    # UI creation
    # ------------------------------------------------------------------
    def _create_widgets(self) -> None:
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

        # --- Read action & status ---
        self.fetch_btn = QtWidgets.QPushButton("Fetch Data")
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

        # --- Operation log (for non-experts) ---
        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(180)
        self.log_view.setPlaceholderText(
            "Operation log will appear here.\n"
            "Each read/write will be summarised with function code, addresses and values."
        )

    def _create_layouts(self) -> None:
        # Connection group
        conn_layout = QtWidgets.QGridLayout()
        conn_layout.addWidget(self.port_label, 0, 0)
        conn_layout.addWidget(self.port_combo, 0, 1)
        conn_layout.addWidget(self.refresh_ports_btn, 0, 2)

        conn_layout.addWidget(self.slave_id_label, 1, 0)
        conn_layout.addWidget(self.slave_id_spin, 1, 1)

        conn_group = QtWidgets.QGroupBox("Connection")
        conn_group.setLayout(conn_layout)

        # Serial settings group
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

        # Register settings group
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

        # Write group layout
        write_layout = QtWidgets.QGridLayout()
        write_layout.addWidget(self.write_addr_label, 0, 0)
        write_layout.addWidget(self.write_addr_spin, 0, 1)

        write_layout.addWidget(self.write_value_label, 1, 0)
        write_layout.addWidget(self.write_value_edit, 1, 1)

        write_layout.addWidget(self.write_btn, 2, 0, 1, 2)
        self.write_group.setLayout(write_layout)

        # Left panel layout (controls)
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(conn_group)
        left_layout.addWidget(serial_group)
        left_layout.addWidget(reg_group)
        left_layout.addWidget(self.write_group)
        left_layout.addStretch()
        left_layout.addWidget(self.fetch_btn)
        left_layout.addWidget(self.status_label)

        left_widget = QtWidgets.QWidget()
        left_widget.setLayout(left_layout)

        # Right side: table + log
        log_group = QtWidgets.QGroupBox("Operation log")
        log_layout = QtWidgets.QVBoxLayout()
        log_layout.addWidget(self.log_view)
        log_group.setLayout(log_layout)

        right_layout = QtWidgets.QVBoxLayout()
        right_layout.addWidget(self.table, 1)
        right_layout.addWidget(log_group, 0)

        right_widget = QtWidgets.QWidget()
        right_widget.setLayout(right_layout)

        # Main layout: left panel + right (table + log)
        main_layout = QtWidgets.QHBoxLayout()
        main_layout.addWidget(left_widget, 0)
        main_layout.addWidget(right_widget, 1)

        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def _create_connections(self) -> None:
        self.refresh_ports_btn.clicked.connect(self._refresh_ports)
        self.fetch_btn.clicked.connect(self._on_fetch_clicked)
        self.write_btn.clicked.connect(self._on_write_single_clicked)
        self.register_type_combo.currentIndexChanged.connect(self._on_register_type_changed)

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
        """)

    def _populate_serial_defaults(self) -> None:
        """
        Fill the serial-parameter dropdowns and default register settings.
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

    # ------------------------------------------------------------------
    # Port enumeration
    # ------------------------------------------------------------------
    def _refresh_ports(self) -> None:
        """
        Scan available serial ports and populate COM port dropdown.
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
            self.status_label.setText("No serial ports found. Plug in your USB-RS485 adapter and click Refresh.")
        else:
            self.status_label.setText("Ready. Select a COM port and click 'Fetch Data'.")

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
    # Helpers to build ModbusClient from UI
    # ------------------------------------------------------------------
    def _build_client_from_ui(self) -> ModbusClient:
        """
        Build a ModbusClient from the current UI settings.
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
        )
        return client

    # ------------------------------------------------------------------
    # Fetch (read) logic
    # ------------------------------------------------------------------
    def _on_fetch_clicked(self) -> None:
        """
        Handle click on the "Fetch Data" button.
        """
        try:
            client = self._build_client_from_ui()
        except Exception as exc:
            self._show_error(str(exc))
            return

        start_addr = self.reg_start_spin.value()
        count = self.reg_count_spin.value()
        decimals = self.decimals_spin.value()
        signed = self.signed_checkbox.isChecked()
        reg_type = self.register_type_combo.currentText()

        self.status_label.setText(
            f"Reading {count} point(s) starting at address {start_addr} from slave {client.slave_id} on {client.port}..."
        )
        QtWidgets.QApplication.processEvents()

        self._append_log(
            f"READ request → Type: {reg_type}, Slave: {client.slave_id}, "
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
            self._append_log(f"ERROR during READ: {exc}")
            self._show_error(f"Error reading: {exc}")
            return

        self._populate_table(start_addr, values, decimals)
        self.status_label.setText("Read OK.")
        self._append_log(
            f"READ OK (FC{fc}) → Received {len(values)} value(s) starting at address {start_addr}."
        )

    # ------------------------------------------------------------------
    # Write logic
    # ------------------------------------------------------------------
    def _on_write_single_clicked(self) -> None:
        """
        Handle click on the "Write Value" button.
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
            f"Writing value to {reg_type} at address {addr} for slave {client.slave_id} on {client.port}..."
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
    # Table display
    # ------------------------------------------------------------------
    def _populate_table(self, start_address: int, values: List[Union[int, float]], decimals: int) -> None:
        """
        Fill the QTableWidget with values.
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

