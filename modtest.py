
"""
modtest.py

Entry point for Ash's Modbus RTU Tester GUI.

"""

import sys
from PyQt5 import QtWidgets

from modules.gui import ModbusGui # type: ignore


def main() -> None:
    """
    Create the QApplication and show the main Modbus GUI window.
    """
    app = QtWidgets.QApplication(sys.argv)
    window = ModbusGui()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
