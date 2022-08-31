import logging
from typing import Any
from . import errors, config
try:
    from win32com.client import Dispatch
except ImportError:
    config.LABEL_PRINTING_ENABLED = False


logger = logging.getLogger("backend")


class DymoLabelPrinter:
    def __init__(self) -> object:
        self.printer_name = None
        self.label_file_path = None
        self.is_open = False
        try:
            self.printer_engine = Dispatch('Dymo.DymoAddIn')
            self.label_engine = Dispatch('Dymo.DymoLabels')
        except Exception as error:
            if error.strerror == "Invalid class string":
                config.LABEL_PRINTING_ENABLED = False
                raise errors.MissingRequiredSoftwareError("Missing required software program. Please install DLS8Setup.8.7.exe.")

        printers = self.printer_engine.GetDymoPrinters()
        self.PRINTERS = [printer for printer in printers.split('|') if printer]

    def __enter__(self):
        self.printer_engine.StartPrintJob()
        return self.printer_engine

    def __exit__(self, exc_type, exc_val, exc_tb):
        # TODO: Log the exception if one was raised.
        self.printer_engine.EndPrintJob()

    def set_printer(self, printer_name: str):
        if printer_name not in self.PRINTERS:
            raise Exception('Printer not found')
        self.printer_engine.SelectPrinter(printer_name)

    def print_labels(self, copies: int = 1):
        with self as label_engine:
            label_engine.Print(copies, False)

    def set_field(self, field_name: str, field_value: Any):
        self.label_engine.SetField(field_name, field_value)

    def register_label_file(self, label_file_path: str) -> object:
        self.label_file_path = label_file_path
        self.is_open = self.printer_engine.Open(label_file_path)
        if not self.is_open:
            raise errors.SetLabelFileError('Could not open label file.')