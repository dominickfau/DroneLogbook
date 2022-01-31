from __future__ import annotations
import traceback
import os
from typing import Any
from win32com.client import Dispatch
from PyQt5 import QtCore, QtGui, QtWidgets

from mainwindow import Ui_MainWindow
import database
import utilities
import label_template_data
from errors import *

from customwidgets import SearchWidget

COMPANY_NAME = "DF-Software"
PROGRAM_NAME = "Drone Logbook"
VERSION = "0.1.0"

USER_HOME_FOLDER = os.path.expanduser('~')
COMPANY_FOLDER = os.path.join(USER_HOME_FOLDER, "Documents", COMPANY_NAME)
PROGRAM_FOLDER = os.path.join(COMPANY_FOLDER, PROGRAM_NAME)
LOG_FOLDER = os.path.join(PROGRAM_FOLDER, 'Logs')
LABEL_TEMPLATE_FOLDER = os.path.join(PROGRAM_FOLDER, 'Label Templates')


DUMPS_FOLDER = os.path.join(PROGRAM_FOLDER, 'Dumps')
DATABASE_DUMPS_FOLDER = os.path.join(DUMPS_FOLDER, 'Database')

THUMBNAIL_WIDTH = 400
THUMBNAIL_HEIGHT = 250

import dialogs

if not os.path.exists(COMPANY_FOLDER):
    os.mkdir(COMPANY_FOLDER)

if not os.path.exists(PROGRAM_FOLDER):
    os.makedirs(PROGRAM_FOLDER)

if not os.path.exists(LABEL_TEMPLATE_FOLDER):
    os.makedirs(LABEL_TEMPLATE_FOLDER)
    with open(os.path.join(LABEL_TEMPLATE_FOLDER, label_template_data.INVENTORY_BARCODE_TEMPLATE["FileName"]), 'w') as f:
        f.write(label_template_data.INVENTORY_BARCODE_TEMPLATE["Data"])

if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

if not os.path.exists(DUMPS_FOLDER):
    os.makedirs(DUMPS_FOLDER)

if not os.path.exists(DATABASE_DUMPS_FOLDER):
    os.makedirs(DATABASE_DUMPS_FOLDER)


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
                raise MissingRequiredSoftwareError("Missing required software program. Please install DLS8Setup.8.7.exe.")

        printers = self.printer_engine.GetDymoPrinters()
        self.PRINTERS = [printer for printer in printers.split('|') if printer]

    def __enter__(self):
        self.printer_engine.StartPrintJob()
        return self.printer_engine

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Log the exception if one was raised
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
            raise SetLabelFileError('Could not open label file.')


class MainWindow(Ui_MainWindow):
    initialized = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(f"{PROGRAM_NAME} v{VERSION}")

        self.drone_info_tabwidget.setEnabled(False)
        self.batteries_info_groupbox.setEnabled(False)
        self.equipment_info_groupbox.setEnabled(False)
        self.flights_info_tabwidget.setEnabled(False)

        self.settings = QtCore.QSettings(COMPANY_NAME, PROGRAM_NAME)
        self.load_settings()

        self.label_printing_enabled = True

        columns = [
            "Serial Number",
            "Name",
            "Color",
            "Brand",
            "Status"
        ]
        self.drone_search_widget = SearchWidget(columns, parent=self)
        self.drone_search_layout.addWidget(self.drone_search_widget)
        self.search_drone_serial_number_line_edit = QtWidgets.QLineEdit()
        self.search_drone_name_line_edit = QtWidgets.QLineEdit()
        self.search_drone_description_line_edit = QtWidgets.QLineEdit()
        self.search_drone_status_combobox = QtWidgets.QComboBox()
        self.drone_search_widget.add_search_form_field("Serial Number:", self.search_drone_serial_number_line_edit)
        self.drone_search_widget.add_search_form_field("Name:", self.search_drone_name_line_edit)
        self.drone_search_widget.add_search_form_field("Description:", self.search_drone_description_line_edit)
        self.drone_search_widget.add_search_form_field("Status:", self.search_drone_status_combobox)

        columns = [
            "Serial Number",
            "Name",
            "Chemistry",
            "Status"
        ]
        self.battery_search_widget = SearchWidget(columns)
        self.battery_search_layout.addWidget(self.battery_search_widget)
        self.search_battery_serial_number_line_edit = QtWidgets.QLineEdit()
        self.search_battery_chemistry_combobox = QtWidgets.QComboBox()
        self.search_battery_status_combobox = QtWidgets.QComboBox()
        self.battery_search_widget.add_search_form_field("Serial Number:", self.search_battery_serial_number_line_edit)
        self.battery_search_widget.add_search_form_field("Chemistry:", self.search_battery_chemistry_combobox)
        self.battery_search_widget.add_search_form_field("Status:", self.search_battery_status_combobox)

        columns = [
            "Serial Number",
            "Name",
            "Description",
            "Type",
            "Status"
        ]
        self.equipment_search_widget = SearchWidget(columns)
        self.equipment_search_layout.addWidget(self.equipment_search_widget)
        self.search_equipment_serial_number_line_edit = QtWidgets.QLineEdit()
        self.search_equipment_name_line_edit = QtWidgets.QLineEdit()
        self.search_equipment_description_line_edit = QtWidgets.QLineEdit()
        self.search_equipment_type_combobox = QtWidgets.QComboBox()
        self.search_equipment_status_combobox = QtWidgets.QComboBox()
        self.equipment_search_widget.add_search_form_field("Serial Number:", self.search_equipment_serial_number_line_edit)
        self.equipment_search_widget.add_search_form_field("Name:", self.search_equipment_name_line_edit)
        self.equipment_search_widget.add_search_form_field("Description:", self.search_equipment_description_line_edit)
        self.equipment_search_widget.add_search_form_field("Type:", self.search_equipment_type_combobox)
        self.equipment_search_widget.add_search_form_field("Status:", self.search_equipment_status_combobox)

        columns = [
            "Unique Id",
            "Drone",
            "Type",
            "Status"
        ]
        self.flight_search_widget = SearchWidget(columns)
        self.flight_search_layout.addWidget(self.flight_search_widget)
        self.search_flight_uuid_line_edit = QtWidgets.QLineEdit()
        self.search_flight_drone_combobox = QtWidgets.QComboBox()
        self.search_flight_status_combobox = QtWidgets.QComboBox()
        self.search_flight_type_combobox = QtWidgets.QComboBox()
        self.search_flight_show_inactive_checkbox = QtWidgets.QCheckBox("Show Inactive")
        self.flight_search_widget.add_search_form_field("Unique ID:", self.search_flight_uuid_line_edit)
        self.flight_search_widget.add_search_form_field("Drone:", self.search_flight_drone_combobox)
        self.flight_search_widget.add_search_form_field("Status:", self.search_flight_status_combobox)
        self.flight_search_widget.add_search_form_field("Type:", self.search_flight_type_combobox)
        self.flight_search_widget.add_search_field(self.search_flight_show_inactive_checkbox)

        columns = [
            "Serial Number",
            "Name",
            "Status"
        ]
        self.flight_controller_search_widget = SearchWidget(columns)
        self.flight_controller_search_layout.addWidget(self.flight_controller_search_widget)
        self.search_flight_controller_serial_number_line_edit = QtWidgets.QLineEdit()
        self.search_flight_controller_name_line_edit = QtWidgets.QLineEdit()
        self.search_flight_controller_status_combobox = QtWidgets.QComboBox()
        self.flight_controller_search_widget.add_search_form_field("Serial Number:", self.search_flight_controller_serial_number_line_edit)
        self.flight_controller_search_widget.add_search_form_field("Name:", self.search_flight_controller_name_line_edit)
        self.flight_controller_search_widget.add_search_form_field("Status:", self.search_flight_controller_status_combobox)

        try:
            self.label_printer = DymoLabelPrinter()
        except MissingRequiredSoftwareError as error:
            self.label_printing_enabled = False
            self.label_printer = None
            print(error)

        if self.label_printing_enabled:
            if self.default_printer == "":
                if len(self.label_printer.PRINTERS) == 1:
                    self.default_printer = self.label_printer.PRINTERS[0]
                    self.label_printer.set_printer(self.default_printer)
                    self.settings.setValue("default_printer", self.default_printer)
                else:
                    self.ask_for_default_printer()
            self.label_printer.set_printer(self.default_printer)

        
        self.init_form_data()
        self.connect_signals()
        self.initialized.emit()
    
    def load_settings(self) -> None:
        self.load_label_file_settings()
        self.default_printer = self.settings.value("default_printer", "")
        self._restore_splitter_states()
    
    def load_label_file_settings(self) -> None:
        self.settings.beginGroup("Label Files")
        self.inventory_label_file_path = self.settings.value("inventory_label_file_path", os.path.join(LABEL_TEMPLATE_FOLDER, label_template_data.INVENTORY_BARCODE_TEMPLATE["FileName"]))
        self.settings.endGroup()
    
    def save_settings(self) -> None:
        self.settings.beginGroup("Label Files")
        self.settings.setValue("inventory_label_file_path", self.inventory_label_file_path)
        self.settings.endGroup()
    
    def closeEvent(self, event=None) -> None:
        """Closes the application."""
        self.save_settings()
        self.close()
    
    def _restore_splitter_states(self) -> None:
        self.settings.beginGroup("GUI Properties")
        self.drone_splitter.restoreState(self.settings.value(self.drone_splitter.objectName(), self.drone_splitter.saveState()))
        self.battery_splitter.restoreState(self.settings.value(self.battery_splitter.objectName(), self.battery_splitter.saveState()))
        self.equipment_splitter.restoreState(self.settings.value(self.equipment_splitter.objectName(), self.equipment_splitter.saveState()))
        self.flight_controller_splitter.restoreState(self.settings.value(self.flight_controller_splitter.objectName(), self.flight_controller_splitter.saveState()))
        self.flights_splitter.restoreState(self.settings.value(self.flights_splitter.objectName(), self.flights_splitter.saveState()))
        self.settings.endGroup()
    
    def show_error(self, error: Exception):
        message_box = QtWidgets.QMessageBox()
        message_box.setWindowTitle("Error")
        message_box.setText("An error occurred.")
        message_box.setInformativeText(str(error))
        message_box.setDetailedText(traceback.format_exc())
        message_box.setIcon(QtWidgets.QMessageBox.Critical)
        message_box.exec_()
    
    def ask_for_default_printer(self):
        def on_default_printer_index_changed(index: int):
            self.settings.setValue("default_printer", combo_box.currentText())
                
        message_box = QtWidgets.QDialog(self)
        message_box.setWindowTitle("Select Default Printer")
        message_box.setFixedSize(400, 200)
        message_box.setStyleSheet("background-color: white;")
        message_box.setLayout(QtWidgets.QVBoxLayout())
        message_box.layout().addWidget(QtWidgets.QLabel("Please select the default printer for printing labels."))
        message_box.layout().addWidget(QtWidgets.QLabel("This will be used for all future label printing."))
        message_box.layout().addWidget(QtWidgets.QLabel("If you do not select a printer, labels will not be printed."))
        form_layout = QtWidgets.QFormLayout()
        combo_box = QtWidgets.QComboBox()
        combo_box.addItem("")
        if len(self.label_printer.PRINTERS) > 0:
            combo_box.addItems(self.label_printer.PRINTERS)
        combo_box.currentIndexChanged.connect(on_default_printer_index_changed)
        form_layout.addRow("Printer:", combo_box)
        message_box.layout().addLayout(form_layout)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        ok_button = QtWidgets.QPushButton("OK")
        ok_button.clicked.connect(message_box.accept)
        button_layout.addWidget(ok_button)
        message_box.layout().addLayout(button_layout)
        message_box.exec_()

    def init_form_data(self):
        """Initializes the form data."""
        self._populate_combobox(self.search_drone_status_combobox, database.Airworthyness.all(), add_blank=True)
        self._populate_combobox(self.search_battery_status_combobox, database.Airworthyness.all(), add_blank=True)
        self._populate_combobox(self.search_flight_controller_status_combobox, database.Airworthyness.all(), add_blank=True)
        self._populate_combobox(self.battery_status_combobox, database.Airworthyness.all())
        self._populate_combobox(self.drone_battery_status_combobox, database.Airworthyness.all())
        self._populate_combobox(self.drone_status_combobox, database.Airworthyness.all())
        self._populate_combobox(self.flight_controller_status_combobox, database.Airworthyness.all())
        
        
        drones = database.global_session.query(database.Drone).all()
        self._populate_combobox(self.search_flight_drone_combobox, [d.combobox_name for d in drones], add_blank=True)
        self._populate_combobox(self.flight_drone_combobox, [d.combobox_name for d in drones])

        batteries = database.global_session.query(database.Battery).all()
        self._populate_combobox(self.flight_battery_combobox, [b.combobox_name for b in batteries])

        flight_types = database.global_session.query(database.FlightType).all()
        self._populate_combobox(self.search_flight_type_combobox, [flight_type.name for flight_type in flight_types], add_blank=True)
        self._populate_combobox(self.flight_type_combbox, [flight_type.name for flight_type in flight_types])

        flight_statues = database.global_session.query(database.FlightStatus).order_by(database.FlightStatus.id).all()
        self._populate_combobox(self.search_flight_status_combobox, [flight_status.name for flight_status in flight_statues], add_blank=True)

        flight_operation_types = database.global_session.query(database.FlightOperationType).all()
        self._populate_combobox(self.flight_operation_type_combobox, [flight_operation_type.name for flight_operation_type in flight_operation_types])

        flight_operation_aprovals = database.global_session.query(database.FlightOperationApproval).all()
        self._populate_combobox(self.flight_operation_aproval_type_combobox, [flight_operation_approval.name for flight_operation_approval in flight_operation_aprovals])

        legal_rules = database.global_session.query(database.LegalRule).all()
        self._populate_combobox(self.flight_legal_rule_combobox, [legal_rule.name for legal_rule in legal_rules])

        battery_chemistries = database.global_session.query(database.BatteryChemistry).all()
        self._populate_combobox(self.search_battery_chemistry_combobox, [battery_chemistry.combobox_name for battery_chemistry in battery_chemistries], add_blank=True)
        self._populate_combobox(self.battery_chemistry_combobox, [battery_chemistry.combobox_name for battery_chemistry in battery_chemistries])

        self._populate_combobox(self.search_equipment_status_combobox, database.Airworthyness.all(), add_blank=True)
        self._populate_combobox(self.equipment_status_combobox, database.Airworthyness.all())

        equipment_types = database.global_session.query(database.EquipmentType).all()
        self._populate_combobox(self.search_equipment_type_combobox, [equipment_type.name for equipment_type in equipment_types], add_blank=True)
        self._populate_combobox(self.equipment_type_combobox, [equipment_type.name for equipment_type in equipment_types])

        flight_controllers = database.global_session.query(database.FlightController).all()
        self._populate_combobox(self.drone_flight_controller_combobox, [flight_controller.combobox_name for flight_controller in flight_controllers])
        
        self.drone_geometry_combobox.addItems([geometry.name for geometry in database.DroneGeometry.find_all()])

        self.reload_all_search_tables()

    def reload_all_search_tables(self) -> None:
        """Reloads all search tables."""

        # Inventory tab.
        self.reload_drone_search_table()
        self.reload_battery_search_table()

        # Flight tab.
        self.reload_flight_search_table()

        # Equipment tab.
        self.reload_equipment_search_table()

        # Flight Controller tab.
        self.reload_flight_controller_search_table()
    
    def reload_drone_search_table(self, search_criteria=None) -> None:
        """Reloads the drone search table."""
        self.drone_search_results = [] # type: list[database.Drone]

        # TODO: Implement search criteria.
        if search_criteria:
            self.drone_search_results = database.global_session.query(database.Drone).all()
        else:
            self.drone_search_results = database.global_session.query(database.Drone).all()
        
        data = []
        for drone in self.drone_search_results:
            row = []
            row.append(drone.serial_number)
            row.append(drone.name)
            row.append(drone.color)
            row.append(drone.brand)
            row.append(drone.status)
            data.append(row)

        self.drone_search_widget.set_record_data(data)
    
    def reload_battery_search_table(self, search_criteria=None) -> None:
        """Reloads the battery search table."""

        # TODO: Implement search criteria.
        self.battery_search_results = [] # type: list[database.Battery]

        if search_criteria:
            self.battery_search_results = database.global_session.query(database.Battery).all()
        else:
            self.battery_search_results = database.global_session.query(database.Battery).all()
        
        data = []
        for battery in self.battery_search_results:
            row = []
            row.append(battery.serial_number)
            row.append(battery.name)
            row.append(battery.chemistry.name)
            row.append(battery.status)
            data.append(row)

        self.battery_search_widget.set_record_data(data)
    
    def reload_flight_search_table(self, search_criteria=None) -> None:
        """Reloads the flight search table."""
        self.flight_search_results = [] # type: list[database.Flight]

        # TODO: Implement search criteria.
        if search_criteria:
            self.flight_search_results = database.global_session.query(database.Flight).all()
        else:
            self.flight_search_results = database.global_session.query(database.Flight).filter(database.Flight.active == True).all()
        
        data = []
        for flight in self.flight_search_results:
            row = []
            row.append(flight.uuid)
            row.append(flight.drone.combobox_name)
            row.append(flight.type_.name)
            row.append(flight.status.name)
            data.append(row)

        self.flight_search_widget.set_record_data(data)
    
    def reload_equipment_search_table(self, search_criteria=None) -> None:
        """Reloads the equipment search table."""
        self.equipment_search_results = [] # type: list[database.Equipment]

        # TODO: Implement search criteria.
        if search_criteria:
            self.equipment_search_results = database.global_session.query(database.Equipment).all()
        else:
            self.equipment_search_results = database.global_session.query(database.Equipment).all()
        
        data = []
        for item in self.equipment_search_results:
            row = []
            row.append(item.serial_number)
            row.append(item.name)
            row.append(item.description)
            row.append(item.type_.name)
            row.append(item.status)
            data.append(row)
        
        self.equipment_search_widget.set_record_data(data)
    
    def reload_flight_controller_search_table(self, search_criteria=None) -> None:
        """Reloads the flight controller search table."""
        self.flight_controller_search_results = []

        # TODO: Implement search criteria.
        if search_criteria:
            self.flight_controller_search_results = database.global_session.query(database.FlightController).all()
        else:
            self.flight_controller_search_results = database.global_session.query(database.FlightController).all()
        
        data = []
        for flight_controller in self.flight_controller_search_results:
            row = []
            row.append(flight_controller.serial_number)
            row.append(flight_controller.name)
            row.append(flight_controller.status)
            data.append(row)
        
        self.flight_controller_search_widget.set_record_data(data)
    
    def reload_flight_equipment_table(self, flight: database.Flight):
        """Reloads the flight equipment table."""
        self.flight_equipment_table.setRowCount(0)
        for equipment_to_flight in flight.used_equipment:
            self.flight_equipment_table.insertRow(self.flight_equipment_table.rowCount())
            self.flight_equipment_table.setItem(self.flight_equipment_table.rowCount() - 1, 0, QtWidgets.QTableWidgetItem(equipment_to_flight.equipment.serial_number))
            self.flight_equipment_table.setItem(self.flight_equipment_table.rowCount() - 1, 1, QtWidgets.QTableWidgetItem(equipment_to_flight.equipment.name))
            self.flight_equipment_table.setItem(self.flight_equipment_table.rowCount() - 1, 2, QtWidgets.QTableWidgetItem(equipment_to_flight.equipment.description))
            self.flight_equipment_table.setItem(self.flight_equipment_table.rowCount() - 1, 3, QtWidgets.QTableWidgetItem(equipment_to_flight.equipment.type_.name))
            self.flight_equipment_table.setItem(self.flight_equipment_table.rowCount() - 1, 4, QtWidgets.QTableWidgetItem(equipment_to_flight.equipment.status))

        # self.flight_equipment_table.resizeColumnsToContents()

        if len(self.selected_flight.used_equipment) == 0:
            self.flight_equipment_edit_button.setEnabled(False)
            self.flight_equipment_remove_button.setEnabled(False)
        else:
            self.flight_equipment_edit_button.setEnabled(True)
            self.flight_equipment_remove_button.setEnabled(True)
    
    def reload_drone_batteries_table(self, drone: database.Drone):
        """Reloads the drone linked batteries table"""
        self.drone_batteries_table.setRowCount(0)
        for battery_to_drone in drone.batteries:
            battery = battery_to_drone.battery
            self.drone_batteries_table.insertRow(self.drone_batteries_table.rowCount())
            self.drone_batteries_table.setItem(self.drone_batteries_table.rowCount() - 1, 0, QtWidgets.QTableWidgetItem(battery.serial_number))
            self.drone_batteries_table.setItem(self.drone_batteries_table.rowCount() - 1, 1, QtWidgets.QTableWidgetItem(battery.name))
            self.drone_batteries_table.setItem(self.drone_batteries_table.rowCount() - 1, 2, QtWidgets.QTableWidgetItem(battery.purchase_date.strftime("%Y-%m-%d")))
            self.drone_batteries_table.setItem(self.drone_batteries_table.rowCount() - 1, 3, QtWidgets.QTableWidgetItem(battery.status))

        if len(drone.batteries) == 0:
            self.drone_battery_edit_button.setEnabled(False)
            self.drone_battery_remove_button.setEnabled(False)
        else:
            self.drone_battery_edit_button.setEnabled(True)
            self.drone_battery_remove_button.setEnabled(True)

    def _populate_combobox(self, combo_box: QtWidgets.QComboBox, data_list: list, add_blank=False) -> None:
        """Populates a combo box with data from a list."""
        combo_box.clear()
        if add_blank:
            combo_box.addItem("")
        for data in data_list:
            combo_box.addItem(data)
        
    def backup_database(self) -> None:
        """Backs up the database."""
        self.statusBar().showMessage("Backing up database...")
        database.backup_database(DATABASE_DUMPS_FOLDER)
        self.statusBar().showMessage("Database backup complete.", 5000)

    def connect_signals(self):
        # Window Widgets
        self.drone_splitter.splitterMoved.connect(self.on_splitter_moved)
        self.battery_splitter.splitterMoved.connect(self.on_splitter_moved)
        self.equipment_splitter.splitterMoved.connect(self.on_splitter_moved)
        self.flight_controller_splitter.splitterMoved.connect(self.on_splitter_moved)
        self.flights_splitter.splitterMoved.connect(self.on_splitter_moved)


        # File menu
        self.actionAbout.triggered.connect(self.about)
        self.actionExit.triggered.connect(self.closeEvent)
        self.actionExit.setShortcut("Ctrl+Q")
        self.actionBackup_Database.triggered.connect(self.backup_database)

        # Inventory menu
        self.actionAdd_Drone.triggered.connect(self.add_drone)
        self.actionAdd_Battery.triggered.connect(self.add_battery)
        self.actionAdd_Equipment.triggered.connect(self.add_equipment)

        # Maintenance menu
        self.actionAdd_Maintenance.triggered.connect(self.add_maintenance)

        # Flight menu
        self.actionAdd_Flight.triggered.connect(self.add_flight)

        # Drone tab
        self.drone_search_widget.search_button.clicked.connect(self.on_search_drone_button_clicked)
        self.drone_search_widget.advanced_search_button.clicked.connect(self.on_search_drone_advanced_button_clicked)
        self.drone_search_widget.results_table.itemDoubleClicked.connect(self.on_drone_search_result_table_item_double_clicked)
        self.drone_search_widget.view_button.clicked.connect(self.on_search_drone_view_item_button_clicked)
        self.drone_add_button.clicked.connect(self.add_drone)
        self.drone_geometry_combobox.setCurrentIndex(1)
        self.drone_geometry_combobox.currentIndexChanged.connect(self.on_drone_geometry_combobox_changed)
        self.drone_geometry_combobox.setCurrentIndex(0)
        self.drone_print_inventory_label_button.clicked.connect(self.on_drone_print_inventory_label_button_clicked)
        self.drone_print_inventory_label_button.setEnabled(False)
        self.drone_delete_button.clicked.connect(self.delete_drone)
        self.drone_delete_button.setEnabled(False)

        self.drone_name_line_edit.editingFinished.connect(lambda: self.selected_drone.set_attribute(database.Drone.name, self.drone_name_line_edit.text()))
        self.drone_status_combobox.currentIndexChanged.connect(lambda: self.selected_drone.set_attribute(database.Drone.status, self.drone_status_combobox.currentText()))
        self.drone_description_line_edit.editingFinished.connect(lambda: self.selected_drone.set_attribute(database.Drone.description, self.drone_description_line_edit.text()))
        self.drone_serial_number_line_edit.editingFinished.connect(lambda: self.selected_drone.set_attribute(database.Drone.serial_number, self.drone_serial_number_line_edit.text()))
        self.drone_model_line_edit.editingFinished.connect(lambda: self.selected_drone.set_attribute(database.Drone.model, self.drone_model_line_edit.text()))
        self.drone_flight_controller_combobox.currentIndexChanged.connect(lambda: self.selected_drone.set_attribute(database.Drone.flight_controller_id, database.FlightController.find_by_combobox_name(self.drone_flight_controller_combobox.currentText()).id))
        self.drone_color_line_edit.editingFinished.connect(lambda: self.selected_drone.set_attribute(database.Drone.color, self.drone_color_line_edit.text()))
        self.drone_item_value_spinbox.valueChanged.connect(lambda: self.selected_drone.set_attribute(database.Drone.item_value, self.drone_item_value_spinbox.value()))
        self.drone_date_purchased_date_edit.editingFinished.connect(lambda: self.selected_drone.set_attribute(database.Drone.purchase_date, self.drone_date_purchased_date_edit.date().toPyDate()))
        self.drone_max_speed_spinbox.editingFinished.connect(lambda: self.selected_drone.set_attribute(database.Drone.max_speed, self.drone_max_speed_spinbox.value()))
        self.drone_max_vertical_speed_spinbox.editingFinished.connect(lambda: self.selected_drone.set_attribute(database.Drone.max_vertical_speed, self.drone_max_vertical_speed_spinbox.value()))
        self.drone_max_payload_weight_spinbox.editingFinished.connect(lambda: self.selected_drone.set_attribute(database.Drone.max_payload_weight, self.drone_max_payload_weight_spinbox.value()))
        self.drone_weight_spinbox.editingFinished.connect(lambda: self.selected_drone.set_attribute(database.Drone.weight, self.drone_weight_spinbox.value()))
        self.drone_max_service_interval_spinbox.editingFinished.connect(lambda: self.selected_drone.set_attribute(database.Drone.max_service_interval, self.drone_max_service_interval_spinbox.value()))
        self.drone_geometry_combobox.currentIndexChanged.connect(lambda: self.selected_drone.set_attribute(database.Drone.geometry_id, database.DroneGeometry.find_by_name(self.drone_geometry_combobox.currentText()).id))
        self.drone_battery_notes_plain_text_edit.textChanged.connect(lambda: self.selected_drone_battery.set_attribute(database.Battery.notes, self.drone_battery_notes_plain_text_edit.toPlainText()))
        self.drone_battery_status_combobox.currentIndexChanged.connect(lambda: self.selected_drone_battery.set_attribute(database.Battery.status, self.drone_battery_status_combobox.currentText()))
        self.drone_battery_capacity_spinbox.editingFinished.connect(lambda: self.selected_drone_battery.set_attribute(database.Battery.capacity, self.drone_battery_capacity_spinbox.value()))
        self.drone_battery_cell_count_spinbox.editingFinished.connect(lambda: self.selected_drone_battery.set_attribute(database.Battery.cell_count, self.drone_battery_cell_count_spinbox.value()))
        self.drone_battery_max_flight_time_spinbox.editingFinished.connect(lambda: self.selected_drone_battery.set_attribute(database.Battery.max_flight_time, self.drone_battery_max_flight_time_spinbox.value()))
        self.drone_battery_max_charge_cycles_spinbox.editingFinished.connect(lambda: self.selected_drone_battery.set_attribute(database.Battery.max_charge_cycles, self.drone_battery_max_charge_cycles_spinbox.value()))
        self.drone_battery_max_flight_spinbox.editingFinished.connect(lambda: self.selected_drone_battery.set_attribute(database.Battery.max_flight, self.drone_battery_max_flight_spinbox.value()))
        self.drone_battery_weight_spinbox.editingFinished.connect(lambda: self.selected_drone_battery.set_attribute(database.Battery.weight, self.drone_battery_weight_spinbox.value()))
        self.drone_battery_item_value_spinbox.editingFinished.connect(lambda: self.selected_drone_battery.set_attribute(database.Battery.item_value, self.drone_battery_item_value_spinbox.value()))
        self.drone_battery_date_purchased_date_edit.editingFinished.connect(lambda: self.selected_drone_battery.set_attribute(database.Battery.purchase_date, self.drone_battery_date_purchased_date_edit.date().toPyDate()))
        self.drone_batteries_table.itemDoubleClicked.connect(self.on_drone_batteries_table_item_double_clicked)
        self.drone_battery_create_new_button.clicked.connect(self.on_drone_battery_create_new_button_clicked)
        self.drone_battery_add_button.clicked.connect(self.on_drone_battery_add_button_clicked)
        self.drone_battery_edit_button.clicked.connect(self.on_drone_battery_edit_button_clicked)
        self.drone_battery_remove_button.clicked.connect(self.on_drone_battery_remove_button_clicked)

        # Batteries tab
        self.battery_search_widget.search_button.clicked.connect(self.on_search_battery_button_clicked)
        self.battery_search_widget.advanced_search_button.clicked.connect(self.on_search_battery_advanced_button_clicked)
        self.battery_search_widget.results_table.itemDoubleClicked.connect(self.on_battery_search_result_table_item_double_clicked)
        self.battery_print_inventory_label_button.clicked.connect(self.on_battery_print_inventory_label_button_clicked)
        self.battery_print_inventory_label_button.setEnabled(False)
        self.battery_add_button.clicked.connect(self.add_battery)
        self.battery_delete_button.clicked.connect(self.delete_battery)
        self.battery_delete_button.setEnabled(False)

        self.battery_status_combobox.currentIndexChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.status, self.battery_status_combobox.currentText()))
        self.battery_capacity_spinbox.valueChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.capacity, self.battery_capacity_spinbox.value()))
        self.battery_cell_count_spinbox.valueChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.cell_count, self.battery_cell_count_spinbox.value()))
        self.battery_max_flight_time_spinbox.valueChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.max_flight_time, self.battery_max_flight_time_spinbox.value()))
        self.battery_max_charge_cycles_spinbox.valueChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.max_charge_cycles, self.battery_max_charge_cycles_spinbox.value()))
        self.battery_max_flight_spinbox.valueChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.max_flights, self.battery_max_flight_spinbox.value()))
        self.battery_weight_spinbox.valueChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.weight, self.battery_weight_spinbox.value()))
        self.battery_serial_number_line_edit.editingFinished.connect(lambda: self.selected_battery.set_attribute(database.Battery.serial_number, self.battery_serial_number_line_edit.text()))
        self.battery_chemistry_combobox.currentIndexChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.chemistry_id, database.BatteryChemistry.find_by_combobox_name(self.battery_chemistry_combobox.currentText()).id))
        self.battery_name_line_edit.editingFinished.connect(lambda: self.selected_battery.set_attribute(database.Battery.name, self.battery_name_line_edit.text()))
        self.battery_item_value_spinbox.valueChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.item_value, self.battery_item_value_spinbox.value()))
        self.battery_date_purchased_date_edit.dateChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.purchase_date, self.battery_date_purchased_date_edit.date().toPyDate()))
        self.battery_notes_plain_text_edit.textChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.notes, self.battery_notes_plain_text_edit.toPlainText()))

        # Equipment tab
        self.equipment_search_widget.search_button.clicked.connect(self.on_search_equipment_button_clicked)
        self.equipment_search_widget.advanced_search_button.clicked.connect(self.on_search_equipment_advanced_button_clicked)
        self.equipment_search_widget.results_table.itemDoubleClicked.connect(self.on_equipment_search_result_table_item_double_clicked)
        self.equipment_search_widget.view_button.clicked.connect(self.on_search_equipment_view_item_button_clicked)
        self.equipment_print_inventory_label_button.clicked.connect(self.on_equipment_print_inventory_label_button_clicked)
        self.equipment_print_inventory_label_button.setEnabled(False)
        self.equipment_add_button.clicked.connect(self.add_equipment)
        self.equipment_delete_button.clicked.connect(self.delete_equipment)
        self.equipment_delete_button.setEnabled(False)

        self.equipment_serial_number_line_edit.editingFinished.connect(lambda: self.selected_equipment.set_attribute(database.Equipment.serial_number, self.equipment_serial_number_line_edit.text()))
        self.equipment_name_line_edit.editingFinished.connect(lambda: self.selected_equipment.set_attribute(database.Equipment.name, self.equipment_name_line_edit.text()))
        self.equipment_description_line_edit.editingFinished.connect(lambda: self.selected_equipment.set_attribute(database.Equipment.description, self.equipment_description_line_edit.text()))
        self.equipment_type_combobox.currentIndexChanged.connect(lambda: self.selected_equipment.set_attribute(database.Equipment.type_id, database.EquipmentType.find_by_name(self.equipment_type_combobox.currentText()).id))
        self.equipment_status_combobox.currentIndexChanged.connect(lambda: self.selected_equipment.set_attribute(database.Equipment.status, self.equipment_status_combobox.currentText()))
        self.equipment_weight_spinbox.valueChanged.connect(lambda: self.selected_equipment.set_attribute(database.Equipment.weight, self.equipment_weight_spinbox.value()))
        self.equipment_date_purchased_date_edit.dateChanged.connect(lambda: self.selected_equipment.set_attribute(database.Equipment.purchase_date, self.equipment_date_purchased_date_edit.date().toPyDate()))
        self.equipment_item_value_spinbox.valueChanged.connect(lambda: self.selected_equipment.set_attribute(database.Equipment.item_value, self.equipment_item_value_spinbox.value()))

        # Flight Contoller tab
        self.flight_controller_search_widget.search_button.clicked.connect(self.on_search_flight_controller_button_clicked)
        self.flight_controller_search_widget.advanced_search_button.clicked.connect(self.on_search_flight_controller_advanced_button_clicked)
        self.flight_controller_search_widget.results_table.itemDoubleClicked.connect(self.on_flight_controller_search_result_table_item_double_clicked)
        self.flight_controller_search_widget.view_button.clicked.connect(self.on_search_flight_controller_view_item_button_clicked)
        self.flight_controller_print_inventory_label_button.clicked.connect(self.on_flight_controller_print_inventory_label_button_clicked)
        self.flight_controller_print_inventory_label_button.setEnabled(False)
        self.flight_controller_add_button.clicked.connect(self.add_flight_controller)
        self.flight_controller_delete_button.clicked.connect(self.delete_flight_controller)
        self.flight_controller_delete_button.setEnabled(False)

        self.flight_controller_serial_number_line_edit.editingFinished.connect(lambda: self.selected_flight_controller.set_attribute(database.FlightController.serial_number, self.flight_controller_serial_number_line_edit.text()))
        self.flight_controller_name_line_edit.editingFinished.connect(lambda: self.selected_flight_controller.set_attribute(database.FlightController.name, self.flight_controller_name_line_edit.text()))
        self.flight_controller_status_combobox.currentIndexChanged.connect(lambda: self.selected_flight_controller.set_attribute(database.FlightController.status, self.flight_controller_status_combobox.currentText()))
        self.flight_controller_date_purchased_date_edit.dateChanged.connect(lambda: self.selected_flight_controller.set_attribute(database.FlightController.purchase_date, self.flight_controller_date_purchased_date_edit.date().toPyDate()))
        self.flight_controller_item_value_spinbox.valueChanged.connect(lambda: self.selected_flight_controller.set_attribute(database.FlightController.item_value, self.flight_controller_item_value_spinbox.value()))


        # Flight tab
        self.flight_search_widget.search_button.clicked.connect(self.on_search_flight_button_clicked)
        self.flight_search_widget.advanced_search_button.clicked.connect(self.on_search_flight_advanced_button_clicked)
        self.flight_search_widget.results_table.itemDoubleClicked.connect(self.on_flight_search_result_table_item_double_clicked)
        self.flight_search_widget.view_button.clicked.connect(self.on_search_flight_view_item_button_clicked)
        self.flight_print_inventory_label_button.clicked.connect(self.on_flight_print_inventory_label_button_clicked)
        self.flight_print_inventory_label_button.setEnabled(False)
        self.flight_add_button.clicked.connect(self.add_flight)
        self.flight_delete_button.clicked.connect(self.delete_flight)

        self.flight_name_line_edit.editingFinished.connect(lambda: self.selected_flight.set_attribute(database.Flight.name, self.flight_name_line_edit.text()))
        self.flight_external_case_id_line_edit.editingFinished.connect(lambda: self.selected_flight.set_attribute(database.Flight.external_case_id, self.flight_external_case_id_line_edit.text()))
        self.night_flight_checkbox.stateChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.night_flight, self.night_flight_checkbox.isChecked()))
        self.flight_active_checkbox.stateChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.active, self.flight_active_checkbox.isChecked()))
        self.flight_active_checkbox.setToolTip(database.Flight.active.doc)
        self.flight_date_datetimeedit.dateTimeChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.date, self.flight_date_datetimeedit.dateTime().toPyDateTime()))
        self.flight_duration_spinbox.valueChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.duration, self.flight_duration_spinbox.value()))
        self.flight_type_combbox.currentIndexChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.type_id, database.FlightType.find_by_name(self.flight_type_combbox.currentText()).id))
        self.flight_notes_plaintextedit.textChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.notes, self.flight_notes_plaintextedit.toPlainText()))
        self.flight_battery_notes_plaintextedit.textChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.battery_notes, self.flight_battery_notes_plaintextedit.toPlainText()))
        self.flight_in_flight_notes_plaintextedit.textChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.in_flight_notes, self.flight_in_flight_notes_plaintextedit.toPlainText()))
        self.flight_post_flight_notes_plaintextedit.textChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.post_flight_notes, self.flight_post_flight_notes_plaintextedit.toPlainText()))
        self.flight_operation_type_combobox.currentIndexChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.operation_type_id, database.FlightOperationType.find_by_name(self.flight_operation_type_combobox.currentText()).id))
        self.flight_utm_authorization_line_edit.editingFinished.connect(lambda: self.selected_flight.set_attribute(database.Flight.utm_authorization, self.flight_utm_authorization_line_edit.text()))
        self.flight_operation_aproval_type_combobox.currentIndexChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.operation_approval_id, database.FlightOperationApproval.find_by_name(self.flight_operation_aproval_type_combobox.currentText()).id))
        self.flight_legal_rule_combobox.currentIndexChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.legal_rule_id, database.LegalRule.find_by_name(self.flight_legal_rule_combobox.currentText()).id))
        self.flight_legal_rule_details_line_edit.editingFinished.connect(lambda: self.selected_flight.set_attribute(database.Flight.legal_rule_details, self.flight_legal_rule_details_line_edit.text()))
        self.flight_max_altitude_spinbox.valueChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.max_altitude, self.flight_max_altitude_spinbox.value()))
        self.flight_distance_traveled_spinbox.valueChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.distance_traveled, self.flight_distance_traveled_spinbox.value()))
        self.flight_drone_combobox.currentIndexChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.drone_id, database.Drone.find_by_combobox_name(self.flight_drone_combobox.currentText()).id))
        self.flight_battery_combobox.currentIndexChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.battery_id, database.Battery.find_by_combobox_name(self.flight_battery_combobox.currentText()).id))
        self.flight_equipment_add_button.clicked.connect(self.on_flight_equipment_add_button_clicked)
        self.flight_equipment_edit_button.clicked.connect(self.on_flight_equipment_edit_button_clicked)
        self.flight_equipment_remove_button.clicked.connect(self.on_flight_equipment_remove_button_clicked)


        self.flight_encounter_with_law_checkbox.stateChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.encounter_with_law, self.flight_encounter_with_law_checkbox.isChecked()))

        self.flight_weather_cloud_cover_spinbox.valueChanged.connect(lambda: self.selected_flight.weather.set_attribute(database.Weather.cloud_cover, self.flight_weather_cloud_cover_spinbox.value()))
        self.flight_weather_humidity_spinbox.valueChanged.connect(lambda: self.selected_flight.weather.set_attribute(database.Weather.humidity, self.flight_weather_humidity_spinbox.value()))
        self.flight_weather_temperature_spinbox.valueChanged.connect(lambda: self.selected_flight.weather.set_attribute(database.Weather.temperature, self.flight_weather_temperature_spinbox.value()))
        self.flight_weather_wind_speed_spinbox.valueChanged.connect(lambda: self.selected_flight.weather.set_attribute(database.Weather.wind_speed, self.flight_weather_wind_speed_spinbox.value()))
        self.flight_weather_wind_direction_spinbox.valueChanged.connect(lambda: self.selected_flight.weather.set_attribute(database.Weather.wind_direction, self.flight_weather_wind_direction_spinbox.value()))
        self.flight_weather_notes_plaintextedit.textChanged.connect(lambda: self.selected_flight.weather.set_attribute(database.Weather.notes, self.flight_weather_notes_plaintextedit.toPlainText()))
    
    def on_splitter_moved(self, pos, index):
        splitter = self.sender()
        name = splitter.objectName()
        self.settings.beginGroup("GUI Properties")
        self.settings.setValue(name, splitter.saveState())
        self.settings.endGroup()

    def on_drone_geometry_combobox_changed(self, index: int) -> None:
        name = self.drone_geometry_combobox.itemText(index)
        self.geometry = database.DroneGeometry.find_by_name(name) # type: database.DroneGeometry
        if self.geometry is None: return
        image = self.geometry.image
        qimage = image.to_QImage()
        qimage = qimage.scaled(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT, QtCore.Qt.KeepAspectRatio) # Scale the image
        pixmap = QtGui.QPixmap.fromImage(qimage)
        self.drone_geometry_image.setPixmap(pixmap)

    def on_drone_battery_create_new_button_clicked(self) -> None:
        drone_battery_dialog = dialogs.CreateBatteryDialog(self)
        drone_battery_dialog.exec()
        battery = drone_battery_dialog.battery
        if battery is not None:
            self.selected_drone.add_battery(battery)
            self.reload_drone_form(self.selected_drone)
    
    def on_drone_battery_add_button_clicked(self) -> None:
        batteries = [battery_to_drone.battery for battery_to_drone in self.selected_drone.batteries]
        dialog = dialogs.SelectBatteryDialog(current_batteries=batteries, parent=self)
        dialog.exec()
        battery = dialog.battery
        if battery is not None:
            self.selected_drone.add_battery(battery)
            self.reload_drone_form(self.selected_drone)
    
    def on_drone_battery_edit_button_clicked(self) -> None:
        index = self.drone_batteries_table.currentRow()
        if index < 0: return
        selected_battery = self.selected_drone.batteries[index].battery
        self.reload_drone_battery_form(selected_battery)
    
    def on_drone_battery_remove_button_clicked(self) -> None:
        index = self.drone_batteries_table.currentRow()
        if index < 0: return
        selected_battery = self.selected_drone.batteries[index].battery
        try:
            self.selected_drone.remove_battery(selected_battery)
        except database.BatteryRemoveError as e:
            self.show_error(e)
        self.reload_drone_batteries_table(self.selected_drone)

    def on_drone_batteries_table_item_double_clicked(self, item: QtWidgets.QTableWidgetItem) -> None:
        index = self.drone_batteries_table.currentRow()
        if index < 0: return
        selected_battery = self.selected_drone.batteries[index].battery
        self.reload_drone_battery_form(selected_battery)

    def on_flight_equipment_add_button_clicked(self) -> None:
        equipment_dialog = dialogs.SelectFlightEquipmentDialog(flight=self.selected_flight)
        equipment_dialog.exec()
        self.reload_flight_equipment_table(self.selected_flight)
    
    def on_flight_equipment_edit_button_clicked(self) -> None:
        selected_equipment = self.selected_flight.used_equipment[self.flight_equipment_table.currentRow()].equipment
        equipment_dialog = dialogs.SelectFlightEquipmentDialog(flight=self.selected_flight, equipment=selected_equipment)
        equipment_dialog.exec()
        self.reload_flight_equipment_table(self.selected_flight)
    
    def on_flight_equipment_remove_button_clicked(self) -> None:
        index = self.flight_equipment_table.currentRow()
        if index < 0: return
        selected_equipment = self.selected_flight.used_equipment[index].equipment
        self.selected_flight.remove_equipment(selected_equipment)

        if len(self.selected_flight.used_equipment) == 0:
            self.flight_equipment_edit_button.setEnabled(False)
            self.flight_equipment_remove_button.setEnabled(False)

        self.reload_flight_equipment_table(self.selected_flight)

    def print_inventory_label(self, label_name: str, label_value: str):
        """Prints a label with the given name and value."""

        try:
            self.label_printer.register_label_file(self.inventory_label_file_path)
        except SetLabelFileError as error:
            self.show_error(error)
            return
        self.label_printer.set_field("barcode_upper_left", label_value)
        self.label_printer.set_field("barcode_upper_right", label_value)
        self.label_printer.set_field("barcode_lower_left", label_value)
        self.label_printer.set_field("barcode_lower_right", label_value)
        self.label_printer.set_field("center_waste_text", label_name)
        self.label_printer.print_labels()

    def on_drone_print_inventory_label_button_clicked(self):
        """Open the dialog to print the inventory labels."""
        label_name = self.drone_name_line_edit.text()
        label_value = self.drone_serial_number_line_edit.text()
        self.print_inventory_label(label_name, label_value)

    def on_battery_print_inventory_label_button_clicked(self):
        """Open the dialog to print the inventory labels."""
        label_name = self.battery_name_line_edit.text()
        label_value = self.battery_serial_number_line_edit.text()
        self.print_inventory_label(label_name, label_value)
    
    def on_equipment_print_inventory_label_button_clicked(self):
        """Open the dialog to print the inventory labels."""
        label_name = self.equipment_name_line_edit.text()
        label_value = self.equipment_serial_number_line_edit.text()
        self.print_inventory_label(label_name, label_value)
    
    def on_flight_controller_print_inventory_label_button_clicked(self):
        """Open the dialog to print the inventory labels."""
        label_name = self.flight_controller_name_line_edit.text()
        label_value = self.flight_controller_serial_number_line_edit.text()
        self.print_inventory_label(label_name, label_value)
    
    def on_flight_print_inventory_label_button_clicked(self):
        """Open the dialog to print the inventory labels."""
        label_name = self.flight_name_line_edit.text()
        label_value = self.flight_uuid_value.text()
        self.print_inventory_label(label_name, label_value)

    def on_search_drone_button_clicked(self):
        """Searches for drones based on the search criteria."""
        self.reload_drone_search_table() # TODO: Add search criteria
    
    def on_search_drone_advanced_button_clicked(self):
        """Opens the advanced search dialog."""
        # TODO: Add advanced search
        pass

    def on_drone_search_result_table_item_double_clicked(self, item: QtWidgets.QTableWidgetItem):
        """Populates form with the selected drone."""
        row = self.drone_search_widget.results_table.row(item)
        drone = self.drone_search_results[row]
        self.reload_drone_form(drone)

    def on_search_drone_view_item_button_clicked(self):
        """Populates form with the selected drone."""
        item = self.drone_search_widget.results_table.currentItem()
        if not item: return
        row = self.drone_search_widget.results_table.row(item)
        drone = self.drone_search_results[row]
        self.reload_drone_form(drone)

    def on_search_battery_button_clicked(self):
        """Searches for batteries based on the search criteria."""
        self.reload_battery_search_table() # TODO: Add search criteria

    def on_search_battery_advanced_button_clicked(self):
        """Opens the advanced search dialog."""
        # TODO: Add advanced search
        pass

    def on_battery_search_result_table_item_double_clicked(self, item: QtWidgets.QTableWidgetItem):
        """Populates form with the selected battery."""
        row = self.battery_search_widget.results_table.row(item)
        battery = self.battery_search_results[row]
        self.reload_battery_form(battery)
        
    def on_search_battery_view_item_button_clicked(self):
        """Populates form with the selected battery."""
        item = self.battery_search_widget.results_table.currentItem()
        if not item: return
        row = self.battery_search_widget.results_table.row(item)
        battery = self.battery_search_results[row]
        self.reload_battery_form(battery)

    def on_search_equipment_button_clicked(self):
        """Searches for equipment based on the search criteria."""
        self.reload_equipment_search_table() # TODO: Add search criteria

    def on_search_equipment_advanced_button_clicked(self):
        """Opens the advanced search dialog."""
        # TODO: Create advanced search dialog for equipment
        pass

    def on_equipment_search_result_table_item_double_clicked(self, item: QtWidgets.QTableWidgetItem):
        """Populates form with the selected equipment."""
        row = self.equipment_search_widget.results_table.row(item)
        equipment = self.equipment_search_results[row]
        self.reload_equipment_form(equipment)

    def on_search_equipment_view_item_button_clicked(self):
        """Populates form with the selected equipment."""
        item = self.equipment_search_widget.results_table.currentItem()
        if not item: return
        row = self.equipment_search_widget.results_table.row(item)
        equipment = self.equipment_search_results[row]
        self.reload_equipment_form(equipment)
    
    def on_search_flight_controller_button_clicked(self):
        """Searches for flights based on the search criteria."""
        self.reload_flight_controller_search_table()
    
    def on_search_flight_controller_advanced_button_clicked(self):
        """Opens the advanced search dialog."""
        # TODO: Create advanced search dialog for flight controllers
        pass

    def on_flight_controller_search_result_table_item_double_clicked(self, item: QtWidgets.QTableWidgetItem):
        """Populates form with the selected flight."""
        item = self.flight_controller_search_widget.results_table.currentItem()
        if not item: return
        row = self.flight_controller_search_widget.results_table.row(item)
        flight_controller = self.flight_controller_search_results[row]
        self.reload_flight_controller_form(flight_controller)
    
    def on_search_flight_controller_view_item_button_clicked(self):
        """Populates form with the selected flight."""
        item = self.flight_controller_search_widget.results_table.currentItem()
        if not item: return
        row = self.flight_controller_search_widget.results_table.row(item)
        flight_controller = self.flight_controller_search_results[row]
        self.reload_flight_controller_form(flight_controller)

    def on_search_flight_button_clicked(self):
        """Searches for flights based on the search criteria."""
        self.reload_flight_search_table() # TODO: Add search criteria

    def on_search_flight_advanced_button_clicked(self):
        """Opens the advanced search dialog."""
        # TODO: Add advanced search
        pass

    def on_flight_search_result_table_item_double_clicked(self, item: QtWidgets.QTableWidgetItem):
        """Populates form with the selected flight."""
        row = self.flight_search_widget.results_table.row(item)
        flight = self.flight_search_results[row]
        self.reload_flight_form(flight)

    def on_search_flight_view_item_button_clicked(self):
        """Populates form with the selected flight."""
        item = self.flight_search_widget.results_table.currentItem()
        if not item: return
        row = self.flight_search_widget.results_table.row(item)
        flight = self.flight_search_results[row]
        self.reload_flight_form(flight)

    def reload_drone_form(self, drone: database.Drone):
        """Reloads the drone form with the ginven drone."""
        self.selected_drone = drone

        if not drone:
            self.drone_info_tabwidget.setCurrentIndex(0)
            self.drone_info_tabwidget.setEnabled(False)
            self.drone_print_inventory_label_button.setEnabled(False)
            self.drone_delete_button.setEnabled(False)
            return

        self.drone_info_tabwidget.setEnabled(True)
        self.drone_delete_button.setEnabled(True)

        if self.label_printing_enabled:
            self.drone_print_inventory_label_button.setEnabled(True)

        self.selected_drone_battery = drone.batteries[0].battery

        # General tab
        self.drone_name_line_edit.setText(drone.name)
        self.drone_status_combobox.setCurrentText(drone.status)
        self.drone_description_line_edit.setText(drone.description)
        self.drone_serial_number_line_edit.setText(drone.serial_number)
        self.drone_model_line_edit.setText(drone.model)
        self.drone_flight_controller_combobox.setCurrentText(drone.flight_controller.combobox_name)

        # Details tab
        self.drone_date_created_value.setText(drone.date_created.strftime("%Y-%m-%d"))
        self.drone_date_modified_value.setText(drone.date_modified.strftime("%Y-%m-%d"))
        self.drone_color_line_edit.setText(drone.color)
        self.drone_item_value_spinbox.setValue(drone.item_value)
        self.drone_date_purchased_date_edit.setDate(QtCore.QDate.fromString(drone.purchase_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))
        self.drone_max_speed_spinbox.setValue(drone.max_speed)
        self.drone_max_vertical_speed_spinbox.setValue(drone.max_vertical_speed)
        self.drone_max_payload_weight_spinbox.setValue(drone.max_payload_weight)
        self.drone_weight_spinbox.setValue(drone.weight)
        self.drone_max_service_interval_spinbox.setValue(drone.max_service_interval)
        self.drone_geometry_combobox.setCurrentText(drone.geometry.name)

        # Linked Batteries tab
        self.reload_drone_batteries_table(drone)
        self.reload_drone_battery_form(self.selected_drone_battery)

    def reload_drone_battery_form(self, battery: database.Battery):
        """Reloads the drone battery form with the given battery"""
        self.selected_drone_battery = battery

        self.drone_battery_notes_plain_text_edit.setPlainText(battery.notes)
        self.drone_battery_age_value.setText(str(battery.age))
        self.drone_battery_total_flights_value.setText(str(battery.total_flights))
        self.drone_battery_total_flight_time_value.setText(str(battery.total_flight_time))
        self.drone_battery_lifespan_flight_progressbar.setValue(battery.total_flights)
        self.drone_battery_lifespan_cycles_progressbar.setValue(battery.charge_cycle_count)
        self.drone_battery_status_combobox.setCurrentText(battery.status)
        self.drone_battery_capacity_spinbox.setValue(battery.capacity)
        self.drone_battery_cell_count_spinbox.setValue(battery.cell_count)
        self.drone_battery_max_flight_time_spinbox.setValue(battery.max_flight_time)
        self.drone_battery_max_charge_cycles_spinbox.setValue(battery.max_charge_cycles)
        self.drone_battery_max_flight_spinbox.setValue(battery.max_flights)
        self.drone_battery_weight_spinbox.setValue(battery.weight)
        self.drone_battery_item_value_spinbox.setValue(battery.item_value)
        self.drone_battery_date_purchased_date_edit.setDate(QtCore.QDate.fromString(battery.purchase_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))

    def reload_battery_form(self, battery: database.Battery):
        """Reloads the battery form with the given battery."""
        self.selected_battery = battery

        if not battery:
            self.batteries_info_groupbox.setEnabled(False)
            self.battery_print_inventory_label_button.setEnabled(False)
            self.battery_delete_button.setEnabled(False)
            return
            
        self.batteries_info_groupbox.setEnabled(True)
        self.battery_delete_button.setEnabled(True)

        if self.label_printing_enabled:
            self.battery_print_inventory_label_button.setEnabled(True)

        self.battery_date_created_value.setText(battery.date_created.strftime("%Y-%m-%d"))
        self.battery_date_modified_value.setText(battery.date_modified.strftime("%Y-%m-%d"))
        self.battery_age_value.setText(str(battery.age) + " yrs")
        self.battery_total_flights_value.setText(str(battery.total_flights))
        self.battery_total_flight_time_value.setText(str(round(battery.total_flight_time / 60, 2))) # Show in hours

        self.battery_lifespan_flight_progressbar.setValue(battery.total_flights)
        self.battery_lifespan_flight_progressbar.setMaximum(battery.max_flights)
        self.battery_lifespan_flight_progressbar.setToolTip(f"Based on {battery.total_flights} flights. Max: {battery.max_flights}")

        self.battery_lifespan_cycles_progressbar.setValue(battery.charge_cycle_count)
        self.battery_lifespan_cycles_progressbar.setMaximum(battery.max_charge_cycles)
        self.battery_lifespan_cycles_progressbar.setToolTip(f"Based on {battery.charge_cycle_count} charge cycles. Max: {battery.max_charge_cycles}")

        self.battery_status_combobox.setCurrentText(battery.status)
        self.battery_capacity_spinbox.setValue(battery.capacity)
        self.battery_cell_count_spinbox.setValue(battery.cell_count)
        self.battery_max_flight_time_spinbox.setValue(battery.max_flight_time)
        self.battery_max_charge_cycles_spinbox.setValue(battery.max_charge_cycles)
        self.battery_max_flight_spinbox.setValue(battery.max_flights)
        self.battery_weight_spinbox.setValue(battery.weight)
        self.battery_serial_number_line_edit.setText(battery.serial_number)
        self.battery_name_line_edit.setText(battery.name)
        self.battery_chemistry_combobox.setCurrentText(battery.chemistry.combobox_name)
        self.battery_item_value_spinbox.setValue(battery.item_value)
        self.battery_date_purchased_date_edit.setDate(QtCore.QDate.fromString(battery.purchase_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))

        if battery.notes:
            self.battery_notes_plain_text_edit.setPlainText(battery.notes)
        else:
            self.battery_notes_plain_text_edit.setPlainText("")
    
    def reload_equipment_form(self, equipment: database.Equipment):
        """Reloads the equipment form with the given equipment."""
        self.selected_equipment = equipment

        if not equipment:
            self.equipment_info_groupbox.setEnabled(False)
            self.equipment_print_inventory_label_button.setEnabled(False)
            self.equipment_delete_button.setEnabled(False)
            return

        self.equipment_info_groupbox.setEnabled(True)

        if self.label_printing_enabled:
            self.equipment_print_inventory_label_button.setEnabled(True)
        
        self.equipment_date_created_value.setText(equipment.date_created.strftime("%Y-%m-%d"))
        self.equipment_date_modified_value.setText(equipment.date_modified.strftime("%Y-%m-%d"))

        self.equipment_serial_number_line_edit.setText(equipment.serial_number)
        self.equipment_name_line_edit.setText(equipment.name)
        self.equipment_description_line_edit.setText(equipment.description)
        self.equipment_type_combobox.setCurrentText(equipment.type_.name)
        self.equipment_status_combobox.setCurrentText(equipment.status)
        self.equipment_weight_spinbox.setValue(equipment.weight)
        self.equipment_date_purchased_date_edit.setDate(QtCore.QDate.fromString(equipment.purchase_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))
        self.equipment_item_value_spinbox.setValue(equipment.item_value)
        self.equipmen_total_flights_value.setText(str(equipment.total_flights))
        self.equipmen_total_flight_time_value.setText(str(round(equipment.total_flight_time / 60, 2))) # Show in hours
    
    def reload_flight_controller_form(self, flight_controller: database.FlightController):
        """Reloads the flight controller for with the given flight controller."""
        self.selected_flight_controller = flight_controller

        if not flight_controller:
            self.flight_controller_info_groupbox.setEnabled(False)
            self.flight_controller_print_inventory_label_button.setEnabled(False)
            self.flight_controller_delete_button.setEnabled(False)
            return

        self.flight_controller_info_groupbox.setEnabled(True)
        self.flight_controller_delete_button.setEnabled(True)

        if self.label_printing_enabled:
            self.flight_controller_print_inventory_label_button.setEnabled(True)

        self.flight_controller_date_created_value.setText(flight_controller.date_created.strftime("%Y-%m-%d"))
        self.flight_controller_date_modified_value.setText(flight_controller.date_modified.strftime("%Y-%m-%d"))
        self.flight_controller_age_value.setText(str(flight_controller.age) + " yrs")
        self.flight_controller_total_flights_value.setText(str(flight_controller.total_flights))
        self.flight_controller_total_flight_time_value.setText(str(round(flight_controller.total_flight_time / 60, 2)))
        if flight_controller.last_flight_date is None:
            self.flight_controller_last_flight_date_value.setText("None")
        else:
            self.flight_controller_last_flight_date_value.setText(flight_controller.last_flight_date.strftime("%Y-%m-%d"))
        if flight_controller.last_flight_duration is None:
            self.flight_controller_last_flight_time_value.setText("None")
        else:
            self.flight_controller_last_flight_time_value.setText(str(flight_controller.last_flight_duration))
        self.flight_controller_serial_number_line_edit.setText(flight_controller.serial_number)
        self.flight_controller_name_line_edit.setText(flight_controller.name)
        self.flight_controller_status_combobox.setCurrentText(flight_controller.status)
        self.flight_controller_date_purchased_date_edit.setDate(QtCore.QDate.fromString(flight_controller.purchase_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))
        self.flight_controller_item_value_spinbox.setValue(flight_controller.item_value)
    
    def reload_flight_form(self, flight: database.Flight):
        """Reloads the flight form with the given flight."""
        self.selected_flight = flight

        if not flight:
            self.flights_info_tabwidget.setCurrentIndex(0)
            self.flights_info_tabwidget.setEnabled(False)
            self.flight_print_inventory_label_button.setEnabled(False)
            self.flight_delete_button.setEnabled(False)
            return

        self.flights_info_tabwidget.setEnabled(True)
        self.flight_delete_button.setEnabled(True)

        if self.label_printing_enabled:
            self.flight_print_inventory_label_button.setEnabled(True)

        # General tab
        self.flight_uuid_value.setText(flight.uuid)
        self.flight_status_value.setText(flight.status.name)
        self.flight_take_off_weight_value.setText(str(flight.total_takeoff_weight))
        self.flight_name_line_edit.setText(flight.name)
        self.flight_external_case_id_line_edit.setText(flight.external_case_id)
        self.flight_active_checkbox.setChecked(flight.active)
        self.night_flight_checkbox.setChecked(flight.night_flight)
        self.flight_date_datetimeedit.setDateTime(QtCore.QDateTime.fromString(flight.date.strftime("%Y-%m-%d %H:%M:%S"), "yyyy-MM-dd hh:mm:ss"))
        self.flight_duration_spinbox.setValue(flight.duration)
        self.flight_type_combbox.setCurrentText(flight.type_.name)

        # Notes tab
        if flight.notes:
            self.flight_notes_plaintextedit.setPlainText(flight.notes)
        else:
            self.flight_notes_plaintextedit.setPlainText("")

        if flight.battery_notes:
            self.flight_battery_notes_plaintextedit.setPlainText(flight.battery_notes)
        else:
            self.flight_battery_notes_plaintextedit.setPlainText("")
        
        if flight.in_flight_notes:
            self.flight_in_flight_notes_plaintextedit.setPlainText(flight.in_flight_notes)
        else:
            self.flight_in_flight_notes_plaintextedit.setPlainText("")
        
        if flight.post_flight_notes:
            self.flight_post_flight_notes_plaintextedit.setPlainText(flight.post_flight_notes)
        else:
            self.flight_post_flight_notes_plaintextedit.setPlainText("")

        # Compliance tab
        self.flight_operation_type_combobox.setCurrentText(flight.operation_type.name)
        self.flight_utm_authorization_line_edit.setText(flight.utm_authorization)
        self.flight_operation_aproval_type_combobox.setCurrentText(flight.operation_approval.name)
        self.flight_legal_rule_combobox.setCurrentText(flight.legal_rule.name)
        self.flight_legal_rule_details_line_edit.setText(flight.legal_rule_details)
        self.flight_max_altitude_spinbox.setValue(flight.max_agl_altitude)
        self.flight_distance_traveled_spinbox.setValue(flight.distance_traveled)

        # Drone / Equipment tab
        self.flight_drone_combobox.setCurrentText(flight.drone.combobox_name)
        self.flight_drone_status_value.setText(flight.drone.status)
        self.flight_drone_serial_number_value.setText(flight.drone.serial_number)
        self.flight_battery_combobox.setCurrentText(flight.battery.combobox_name)
        self.reload_flight_equipment_table(flight)

        # Safety / Incidence tab
        self.flight_encounter_with_law_checkbox.setChecked(flight.encounter_with_law)

        # Weather tab
        if flight.weather:
            self.flight_weather_tab.setEnabled(True)
            self.flight_weather_date_value.setText(flight.weather.date.strftime("%Y-%m-%d"))
            self.flight_weather_location_value.setText(str(flight.location))
            self.flight_weather_cloud_cover_spinbox.setValue(flight.weather.cloud_cover)
            self.flight_weather_humidity_spinbox.setValue(flight.weather.humidity)
            self.flight_weather_temperature_spinbox.setValue(flight.weather.temperature)
            self.flight_weather_wind_speed_spinbox.setValue(flight.weather.wind_speed)
            self.flight_weather_wind_direction_spinbox.setValue(flight.weather.wind_direction)

            if flight.weather.notes:
                self.flight_weather_notes_plaintextedit.setPlainText(flight.weather.notes)
            else:
                self.flight_weather_notes_plaintextedit.setPlainText("")

        else:
            self.flight_weather_tab.setEnabled(False)
            self.flight_weather_date_value.setText("")
            self.flight_weather_location_value.setText("")
            self.flight_weather_cloud_cover_spinbox.setValue(0)
            self.flight_weather_humidity_spinbox.setValue(0)
            self.flight_weather_temperature_spinbox.setValue(0)
            self.flight_weather_wind_speed_spinbox.setValue(0)
            self.flight_weather_wind_direction_spinbox.setValue(0)
            self.flight_weather_notes_plaintextedit.setPlainText("")

    def about(self) -> None:
        """Opens a dialog box with information about the application."""
        message_box = QtWidgets.QMessageBox()
        message_box.setWindowTitle("About")
        message_box.setText(f"{PROGRAM_NAME} - Version {VERSION}")
        message_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        message_box.exec_()
    
    def add_drone(self) -> None:
        """Opens a dialog box to add a new drone."""
        dialog = dialogs.AddDroneDialog(self)
        dialog.exec()
        if dialog.drone is None: return
        self.reload_drone_search_table()
        self.reload_drone_form(dialog.drone)

    def add_battery(self) -> None:
        """Opens a dialog box to add a new battery."""
        dialog = dialogs.CreateBatteryDialog(self)
        dialog.exec()
        battery = dialog.battery
        if battery is None: return
        self.reload_battery_form(battery)
        self.reload_battery_search_table()

    def add_equipment(self) -> None:
        """Opens a dialog box to add a new equipment."""
        dialog = dialogs.CreateEquipmentDialog(self)
        dialog.exec()
        equipment = dialog.equipment
        if equipment is None: return
        self.reload_equipment_form(equipment)
        self.reload_equipment_search_table()
    
    def add_flight_controller(self) -> None:
        """Opens a dialog box to add a new flight controller."""
        dialog = dialogs.CreateFlightControllerDialog(self)
        dialog.exec()
        flight_controller = dialog.flight_controller
        if flight_controller is None: return
        self.reload_flight_controller_form(flight_controller)
        self.reload_flight_controller_search_table()
    
    def add_maintenance(self) -> None:
        """Opens a dialog box to add a new maintenance."""
        return
        dialog = dialogs.CreateMaintenanceDialog(self)
        dialog.exec()
        maintenance = dialog.maintenance
        if maintenance is None: return
        self.reload_maintenance_form(maintenance)
        self.reload_maintenance_search_table()
    
    def add_flight(self) -> None:
        """Opens a dialog box to add a new flight."""
        return
        dialog = dialogs.CreateFlightDialog(self)
        dialog.exec()
        flight = dialog.flight
        if flight is None: return
        self.reload_flight_form(flight)
        self.reload_flight_search_table()
    
    def delete_drone(self) -> None:
        """Deletes the selected drone."""
        if not self.selected_drone: return

        message_box = QtWidgets.QMessageBox()
        message_box.setIcon(QtWidgets.QMessageBox.Warning)
        message_box.setWindowTitle("Delete Equipment")
        message_box.setText(f"Are you sure you want to delete the drone {self.selected_drone.name}?")
        message_box.setInformativeText("This will not delete any batteries or flight controllers associated with this drone.")
        message_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        message_box.setDefaultButton(QtWidgets.QMessageBox.No)
        result = message_box.exec_()
        if result == QtWidgets.QMessageBox.No: return

        try:
            self.selected_drone.delete()
            self.reload_drone_form(None)
            self.reload_drone_search_table()
        except database.Error as e:
            self.show_error(e)
            return

    def delete_battery(self) -> None:
        """Deletes the selected battery."""
        if not self.selected_battery: return

        message_box = QtWidgets.QMessageBox()
        message_box.setIcon(QtWidgets.QMessageBox.Warning)
        message_box.setWindowTitle("Delete Battery")
        message_box.setText(f"Are you sure you want to delete the battery {self.selected_battery.name}?")
        message_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        message_box.setDefaultButton(QtWidgets.QMessageBox.No)
        result = message_box.exec_()
        if result == QtWidgets.QMessageBox.No: return

        try:
            self.selected_battery.delete()
            self.reload_battery_form(None)
            self.reload_battery_search_table()
        except database.Error as e:
            self.show_error(e)
            return

    def delete_equipment(self) -> None:
        if not self.selected_equipment: return

        message_box = QtWidgets.QMessageBox()
        message_box.setIcon(QtWidgets.QMessageBox.Warning)
        message_box.setWindowTitle("Delete Equipment")
        message_box.setText(f"Are you sure you want to delete the equipment {self.selected_equipment.name}?")
        message_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        message_box.setDefaultButton(QtWidgets.QMessageBox.No)
        result = message_box.exec_()
        if result == QtWidgets.QMessageBox.No: return

        try:
            self.selected_equipment.delete()
            self.reload_equipment_form(None)
            self.reload_equipment_search_table()
        except database.Error as e:
            self.show_error(e)
            return

    def delete_flight_controller(self) -> None:
        if not self.selected_flight_controller: return

        message_box = QtWidgets.QMessageBox()
        message_box.setIcon(QtWidgets.QMessageBox.Warning)
        message_box.setWindowTitle("Delete Equipment")
        message_box.setText(f"Are you sure you want to delete the flight controller {self.selected_flight_controller.name}?")
        message_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        message_box.setDefaultButton(QtWidgets.QMessageBox.No)
        result = message_box.exec_()
        if result == QtWidgets.QMessageBox.No: return

        try:
            self.selected_flight_controller.delete()
            self.reload_flight_controller_form(None)
            self.reload_flight_controller_search_table()
        except database.Error as e:
            self.show_error(e)
            return
    
    def delete_flight(self) -> None:
        if not self.selected_flight: return

        message_box = QtWidgets.QMessageBox()
        message_box.setIcon(QtWidgets.QMessageBox.Warning)
        message_box.setWindowTitle("Delete Equipment")
        message_box.setText(f"Are you sure you want to delete the flight {self.selected_flight.name}?")
        message_box.setInformativeText("Any equipment or batteries associated with this flight, will lose their association with the flight.")
        message_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        message_box.setDefaultButton(QtWidgets.QMessageBox.No)
        result = message_box.exec_()
        if result == QtWidgets.QMessageBox.No: return

        try:
            self.selected_flight.delete()
            self.reload_flight_form(None)
            self.reload_flight_search_table()
        except database.Error as e:
            self.show_error(e)
            return


class SplashScreen(QtWidgets.QWidget):
    closing = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Splash Screen Example')
        self.setFixedSize(600, 300)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.setStyleSheet('''
        #LabelTitle {
            font-size: 60px;
            color: #93deed;
        }

        #LabelDesc {
            font-size: 30px;
            color: #c2ced1;
        }

        #LabelLoading {
            font-size: 30px;
            color: #e8e8eb;
        }

        QFrame {
            background-color: #2F4454;
            color: rgb(220, 220, 220);
        }

        QProgressBar {
            background-color: #DA7B93;
            color: rgb(200, 200, 200);
            border-style: none;
            border-radius: 10px;
            text-align: center;
            font-size: 30px;
        }

        QProgressBar::chunk {
            border-radius: 10px;
            background-color: qlineargradient(spread:pad x1:0, x2:1, y1:0.511364, y2:0.523, stop:0 #1C3334, stop:1 #376E6F);
        }
    ''')

        self.initUI()

    def initUI(self):
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.frame = QtWidgets.QFrame()
        layout.addWidget(self.frame)
        v_layout = QtWidgets.QVBoxLayout()

        self.labelTitle = QtWidgets.QLabel(self.frame)
        self.labelTitle.setObjectName('LabelTitle')
        
        # center labels
        self.labelTitle.setText('Splash Screen')
        self.labelTitle.setAlignment(QtCore.Qt.AlignCenter)
        v_layout.addWidget(self.labelTitle)


        self.labelDescription = QtWidgets.QLabel(self.frame)
        self.labelDescription.setObjectName('LabelDesc')
        self.labelDescription.setText('<strong>Working on Task #1</strong>')
        self.labelDescription.setAlignment(QtCore.Qt.AlignCenter)
        v_layout.addWidget(self.labelDescription)

        self.progressBar = QtWidgets.QProgressBar(self.frame)
        self.progressBar.setAlignment(QtCore.Qt.AlignCenter)
        self.progressBar.setFormat('%p%')
        self.progressBar.setTextVisible(True)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(20)
        v_layout.addWidget(self.progressBar)

        self.labelLoading = QtWidgets.QLabel(self.frame)
        self.labelLoading.setObjectName('LabelLoading')
        self.labelLoading.setAlignment(QtCore.Qt.AlignCenter)
        self.labelLoading.setText('loading...')
        v_layout.addWidget(self.labelLoading)

        self.frame.setLayout(v_layout)

    def loading(self):
        self.progressBar.setValue(0)
        # database.force_recreate()
        self.closing.emit()
        self.close()


class Application(QtWidgets.QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.main_window = MainWindow()
        self.aboutToQuit.connect(self.main_window.closeEvent)

        # TODO: Work on splash screen
        self.splash = SplashScreen()
        # self.splash.closing.connect(lambda: self.main_window.show())
        self.splash.closing.connect(lambda: self.main_window.showMaximized())
        self.splash.show()
        self.splash.loading()
        


if __name__ == "__main__":
    app = Application([])
    app.exec_()