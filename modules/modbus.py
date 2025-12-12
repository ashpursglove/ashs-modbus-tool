"""
modules/modbus.py

Thin wrapper around minimalmodbus for use by the PyQt5 GUI.

Provides:
- LoggingInstrument: subclass of minimalmodbus.Instrument that can call a
  frame_logger callback with raw RTU request/response frames.
- ModbusClient: high-level helper that exposes simple methods:
    * read_holding_registers
    * read_input_registers
    * read_coils
    * read_discrete_inputs
    * write_holding_register
    * write_coil

The GUI passes in a frame_logger callable so it can display raw TX/RX frames.
"""

from __future__ import annotations

from typing import Callable, List, Optional

import minimalmodbus
import serial


FrameLogger = Callable[[bytes, bytes], None]


class LoggingInstrument(minimalmodbus.Instrument):
    """
    minimalmodbus.Instrument subclass that can report raw RTU frames.

    If frame_logger is provided, it will be called with:
        frame_logger(request_bytes, response_bytes)
    for every Modbus transaction.
    """

    def __init__(
        self,
        portname: str,
        slaveaddress: int,
        frame_logger: Optional[FrameLogger] = None,
    ) -> None:
        super().__init__(portname, slaveaddress)
        self._frame_logger: Optional[FrameLogger] = frame_logger

    def _communicate(self, request: bytes, *args, **kwargs) -> bytes:  # type: ignore[override]
        """
        Wrap the parent _communicate to capture raw request/response frames.

        We don't modify the behaviour at all, only tap into the bytes.
        """
        response = super()._communicate(request, *args, **kwargs)
        if self._frame_logger is not None:
            try:
                self._frame_logger(request, response)
            except Exception:
                # Never let logging break Modbus comms
                pass
        return response


class ModbusClient:
    """
    High-level Modbus RTU client built on minimalmodbus.

    This class is intentionally GUI-agnostic and only deals with:
    - Serial port & slave configuration
    - Simple read/write operations
    - Optional frame logging via a callback

    Parameters
    ----------
    port : str
        Serial port name, e.g. "COM3" on Windows or "/dev/ttyUSB0" on Linux.
    slave_id : int
        Modbus slave address (1..247).
    baudrate : int
        Serial baudrate (default 9600).
    parity : str
        serial.PARITY_NONE / PARITY_EVEN / PARITY_ODD.
    databits : int
        Typically 8 or 7.
    stopbits : int
        1 or 2.
    timeout : float
        Serial read timeout in seconds.
    frame_logger : callable, optional
        If given, it will be called with (request_bytes, response_bytes)
        for each Modbus transaction.
    """

    def __init__(
        self,
        port: str,
        slave_id: int,
        baudrate: int = 9600,
        parity: str = serial.PARITY_NONE,
        databits: int = 8,
        stopbits: int = 1,
        timeout: float = 0.5,
        frame_logger: Optional[FrameLogger] = None,
    ) -> None:
        self.port = port
        self.slave_id = slave_id

        # Create our logging instrument
        instrument = LoggingInstrument(port, slave_id, frame_logger=frame_logger)

        # RTU mode
        instrument.mode = minimalmodbus.MODE_RTU
        instrument.clear_buffers_before_each_transaction = True

        # Serial config
        instrument.serial.baudrate = baudrate
        instrument.serial.bytesize = databits
        instrument.serial.parity = parity
        instrument.serial.stopbits = stopbits
        instrument.serial.timeout = timeout

        # You can flip this on for console debug if needed
        instrument.debug = False

        self._instrument = instrument

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _to_signed_16(value: int) -> int:
        """
        Convert an unsigned 16-bit integer to signed (two's complement).
        """
        if value > 0x7FFF:
            return value - 0x10000
        return value

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------
    def read_holding_registers(
        self,
        start_address: int,
        count: int,
        signed: bool = False,
    ) -> List[int]:
        """
        Read a block of holding registers (FC3).

        Returns a list of raw 16-bit integers. If signed=True, values are
        converted to Python signed ints using two's complement logic.
        """
        # minimalmodbus.read_registers: functioncode defaults to 3
        values = self._instrument.read_registers(
            registeraddress=start_address,
            number_of_registers=count,
        )
        if signed:
            return [self._to_signed_16(v) for v in values]
        return values

    def read_input_registers(
        self,
        start_address: int,
        count: int,
        signed: bool = False,
    ) -> List[int]:
        """
        Read a block of input registers (FC4).

        Returns a list of raw 16-bit integers. If signed=True, values are
        converted to Python signed ints using two's complement logic.
        """
        values = self._instrument.read_registers(
            registeraddress=start_address,
            number_of_registers=count,
            functioncode=4,
        )
        if signed:
            return [self._to_signed_16(v) for v in values]
        return values

    def read_coils(
        self,
        start_address: int,
        count: int,
    ) -> List[int]:
        """
        Read a block of coils (FC1).

        Returns a list of bits (0 or 1).
        """
        return self._instrument.read_bits(
            address=start_address,
            number_of_bits=count,
            functioncode=1,
        )

    def read_discrete_inputs(
        self,
        start_address: int,
        count: int,
    ) -> List[int]:
        """
        Read a block of discrete inputs (FC2).

        Returns a list of bits (0 or 1).
        """
        return self._instrument.read_bits(
            address=start_address,
            number_of_bits=count,
            functioncode=2,
        )

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------
    def write_holding_register(
        self,
        address: int,
        value: float,
        decimals: int = 0,
        signed: bool = False,
    ) -> None:
        """
        Write a single holding register.

        We force functioncode=16 (Write Multiple Registers) so that scaled
        values (decimals > 0) are always handled consistently.
        """
        self._instrument.write_register(
            registeraddress=address,
            value=value,
            number_of_decimals=decimals,
            functioncode=16,
            signed=signed,
        )

    def write_coil(
        self,
        address: int,
        value: int,
    ) -> None:
        """
        Write a single coil (FC5).

        value must be 0 or 1.
        """
        self._instrument.write_bit(
            address=address,
            value=value,
            functioncode=5,
        )
