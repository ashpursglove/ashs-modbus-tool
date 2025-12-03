"""
modules/modbus.py

Non-GUI Modbus helper logic for the Modbus RTU testing tool.

This module contains:

- ModbusClient
    A small helper class that wraps minimalmodbus.Instrument creation and
    read/write calls. It is GUI-agnostic and can be reused by scripts,
    services, tests, etc.

The GUI in modules/gui.py imports ModbusClient from here and uses it to
perform all Modbus operations.
"""

from typing import List

import minimalmodbus
import serial


class ModbusClient:
    """
    Thin wrapper around minimalmodbus.Instrument that encapsulates:

    - Instrument creation (Serial + Modbus RTU config)
    - Reading different Modbus data types:
        * Holding registers (4xxxx, FC3)
        * Input registers (3xxxx, FC4)
        * Coils (0xxxx, FC1)
        * Discrete inputs (1xxxx, FC2)
    - Writing:
        * Single holding register (FC16)
        * Single coil (FC5)

    This class is independent of any GUI framework.
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
    ) -> None:
        """
        Initialise a ModbusClient with the given serial and Modbus parameters.

        Parameters
        ----------
        port : str
            Serial port name (e.g. "COM3", "/dev/ttyUSB0").
        slave_id : int
            Modbus slave address (1..247).
        baudrate : int
            Serial baudrate (default 9600).
        parity : str
            Parity from pyserial (e.g. serial.PARITY_NONE).
        databits : int
            Number of data bits (7 or 8).
        stopbits : int
            Number of stop bits (1 or 2).
        timeout : float
            Serial timeout in seconds.
        """
        self.port = port
        self.slave_id = slave_id
        self.baudrate = baudrate
        self.parity = parity
        self.databits = databits
        self.stopbits = stopbits
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------
    def _create_instrument(self) -> minimalmodbus.Instrument:
        """
        Create and configure a minimalmodbus.Instrument object.

        A fresh instrument is created per operation
        (close_port_after_each_call=True) to avoid port-locking issues
        when sharing with other programs.
        """
        instrument = minimalmodbus.Instrument(self.port, self.slave_id)
        instrument.mode = minimalmodbus.MODE_RTU
        instrument.clear_buffers_before_each_transaction = True
        instrument.close_port_after_each_call = True

        instrument.serial.baudrate = self.baudrate
        instrument.serial.bytesize = self.databits
        instrument.serial.parity = self.parity
        instrument.serial.stopbits = self.stopbits
        instrument.serial.timeout = self.timeout

        return instrument

    # ------------------------------------------------------------------
    # Reading helpers
    # ------------------------------------------------------------------
    def read_holding_registers(
        self,
        start_address: int,
        count: int,
        signed: bool = False,
    ) -> List[int]:
        """
        Read a block of holding registers (function code 3).

        Returns
        -------
        List[int]
            Raw register values (0..65535 or signed if requested).
        """
        instrument = self._create_instrument()
        values = instrument.read_registers(
            registeraddress=start_address,
            number_of_registers=count,
            functioncode=3,
        )
        if signed:
            values = [self._to_signed_16(v) for v in values]
        return values

    def read_input_registers(
        self,
        start_address: int,
        count: int,
        signed: bool = False,
    ) -> List[int]:
        """
        Read a block of input registers (function code 4).

        Returns
        -------
        List[int]
            Raw register values (0..65535 or signed if requested).
        """
        instrument = self._create_instrument()
        values = instrument.read_registers(
            registeraddress=start_address,
            number_of_registers=count,
            functioncode=4,
        )
        if signed:
            values = [self._to_signed_16(v) for v in values]
        return values

    def read_coils(
        self,
        start_address: int,
        count: int,
    ) -> List[int]:
        """
        Read a block of coils (function code 1).

        Returns
        -------
        List[int]
            List of 0/1 integers.
        """
        instrument = self._create_instrument()
        bits = instrument.read_bits(
            registeraddress=start_address,
            number_of_bits=count,
            functioncode=1,
        )
        return [int(b) for b in bits]

    def read_discrete_inputs(
        self,
        start_address: int,
        count: int,
    ) -> List[int]:
        """
        Read a block of discrete inputs (function code 2).

        Returns
        -------
        List[int]
            List of 0/1 integers.
        """
        instrument = self._create_instrument()
        bits = instrument.read_bits(
            registeraddress=start_address,
            number_of_bits=count,
            functioncode=2,
        )
        return [int(b) for b in bits]

    # ------------------------------------------------------------------
    # Writing helpers
    # ------------------------------------------------------------------
    def write_holding_register(
        self,
        address: int,
        value: float,
        decimals: int = 0,
        signed: bool = False,
    ) -> None:
        """
        Write a single holding register (function code 16 / 6).

        minimalmodbus handles scaling when number_of_decimals > 0.

        Parameters
        ----------
        address : int
            Register address.
        value : float
            Value to write (unscaled).
        decimals : int
            Number of decimal places (e.g. 1 means value*10 goes on the wire).
        signed : bool
            Whether to treat the register as signed 16-bit.
        """
        instrument = self._create_instrument()
        instrument.write_register(
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
        Write a single coil (function code 5).

        Parameters
        ----------
        address : int
            Coil address.
        value : int
            0 or 1.
        """
        if value not in (0, 1):
            raise ValueError("Coil value must be 0 or 1.")
        instrument = self._create_instrument()
        instrument.write_bit(
            registeraddress=address,
            value=value,
            functioncode=5,
        )

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _to_signed_16(value: int) -> int:
        """
        Convert an unsigned 16-bit integer to a signed Python int.
        """
        if value >= 0x8000:
            return value - 0x10000
        return value
