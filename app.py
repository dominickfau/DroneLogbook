import traceback
import os
import webbrowser
import logging
from typing import List
from PyQt5 import QtCore, QtGui, QtWidgets
from sqlalchemy.orm import Session

from dronelogbook import enums, errors, config, models, dialogs
from dronelogbook.mainwindow import Ui_MainWindow
from dronelogbook.dymo import DymoLabelPrinter
from dronelogbook.customwidgets import SearchWidget
from dronelogbook.database import DBContext
from dronelogbook.defaultdata import load_default_data
from dronelogbook.updater import check_for_updates


logger = logging.getLogger("frontend")


class MainWindow(Ui_MainWindow):
    initialized = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(f"{config.PROGRAM_NAME} v{config.PROGRAM_VERSION}")

        self.drone_info_tabwidget.setEnabled(False)
        self.batteries_info_groupbox.setEnabled(False)
        self.equipment_info_groupbox.setEnabled(False)
        self.flights_info_tabwidget.setEnabled(False)

        self.settings = QtCore.QSettings(config.COMPANY_NAME, config.PROGRAM_NAME)
        self.load_settings()

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

        self.label_printer = None

        if config.LABEL_PRINTING_ENABLED:
            try:
                self.label_printer = DymoLabelPrinter()
            except errors.MissingRequiredSoftwareError:
                pass
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
        self.inventory_label_file_path = self.settings.value("inventory_label_file_path", os.path.join(config.LABEL_TEMPLATE_FOLDER, config.INVENTORY_BARCODE_TEMPLATE["FileName"]))
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
        self._populate_combobox(self.search_drone_status_combobox, enums.Airworthyness.all(), add_blank=True)
        self._populate_combobox(self.search_battery_status_combobox, enums.Airworthyness.all(), add_blank=True)
        self._populate_combobox(self.search_flight_controller_status_combobox, enums.Airworthyness.all(), add_blank=True)
        self._populate_combobox(self.battery_status_combobox, enums.Airworthyness.all())
        self._populate_combobox(self.drone_battery_status_combobox, enums.Airworthyness.all())
        self._populate_combobox(self.drone_status_combobox, enums.Airworthyness.all())
        self._populate_combobox(self.flight_controller_status_combobox, enums.Airworthyness.all())
        
        with DBContext() as session:
            drones = session.query(models.Drone).all()
            self._populate_combobox(self.search_flight_drone_combobox, [d.combobox_name for d in drones], add_blank=True)
            self._populate_combobox(self.flight_drone_combobox, [d.combobox_name for d in drones])

            batteries = session.query(models.Battery).all()
            self._populate_combobox(self.flight_battery_combobox, [b.combobox_name for b in batteries])

            flight_types = session.query(models.FlightType).all()
            self._populate_combobox(self.search_flight_type_combobox, [flight_type.name for flight_type in flight_types], add_blank=True)
            self._populate_combobox(self.flight_type_combbox, [flight_type.name for flight_type in flight_types])

            flight_statues = session.query(models.FlightStatus).order_by(models.FlightStatus.id).all()
            self._populate_combobox(self.search_flight_status_combobox, [flight_status.name for flight_status in flight_statues], add_blank=True)

            flight_operation_types = session.query(models.FlightOperationType).all()
            self._populate_combobox(self.flight_operation_type_combobox, [flight_operation_type.name for flight_operation_type in flight_operation_types])

            flight_operation_aprovals = session.query(models.FlightOperationApproval).all()
            self._populate_combobox(self.flight_operation_aproval_type_combobox, [flight_operation_approval.name for flight_operation_approval in flight_operation_aprovals])

            legal_rules = session.query(models.LegalRule).all()
            self._populate_combobox(self.flight_legal_rule_combobox, [legal_rule.name for legal_rule in legal_rules])

            battery_chemistries = session.query(models.BatteryChemistry).all()
            self._populate_combobox(self.search_battery_chemistry_combobox, [battery_chemistry.combobox_name for battery_chemistry in battery_chemistries], add_blank=True)
            self._populate_combobox(self.battery_chemistry_combobox, [battery_chemistry.combobox_name for battery_chemistry in battery_chemistries])

            self._populate_combobox(self.search_equipment_status_combobox, enums.Airworthyness.all(), add_blank=True)
            self._populate_combobox(self.equipment_status_combobox, enums.Airworthyness.all())

            equipment_types = session.query(models.EquipmentType).all()
            self._populate_combobox(self.search_equipment_type_combobox, [equipment_type.name for equipment_type in equipment_types], add_blank=True)
            self._populate_combobox(self.equipment_type_combobox, [equipment_type.name for equipment_type in equipment_types])

            flight_controllers = models.Equipment.find_by_type(session, models.EquipmentType.find_by_name(session, "Remote Controller"))
            self._populate_combobox(self.drone_flight_controller_combobox, [flight_controller.combobox_name for flight_controller in flight_controllers])
            
            self.drone_geometry_combobox.addItems([geometry.name for geometry in models.DroneGeometry.find_all(session)])

            session.expunge_all()

        self.reload_all_search_tables()

    def reload_all_search_tables(self) -> None:
        """Reloads all search tables."""

        with DBContext() as session:
            # Inventory tab.
            self.reload_drone_search_table(session)
            self.reload_battery_search_table(session)

            # Flight tab.
            self.reload_flight_search_table(session)

            # Equipment tab.
            self.reload_equipment_search_table(session)

            # Flight Controller tab.
            self.reload_flight_controller_search_table(session)
    
    def reload_drone_search_table(self, session: Session, search_criteria=None) -> None:
        """Reloads the drone search table."""
        self.drone_search_results = [] # type: list[models.Drone]

        # TODO: Implement search criteria.
        if search_criteria:
            self.drone_search_results = session.query(models.Drone).all()
        else:
            self.drone_search_results = session.query(models.Drone).all()
        
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
        session.expunge_all()
    
    def reload_battery_search_table(self, session: Session, search_criteria=None) -> None:
        """Reloads the battery search table."""

        # TODO: Implement search criteria.
        self.battery_search_results = [] # type: List[models.Battery]

        if search_criteria:
            self.battery_search_results = session.query(models.Battery).all()
        else:
            self.battery_search_results = session.query(models.Battery).all()
        
        data = []
        for battery in self.battery_search_results:
            row = []
            row.append(battery.serial_number)
            row.append(battery.name)
            row.append(battery.chemistry.name)
            row.append(battery.status)
            data.append(row)

        self.battery_search_widget.set_record_data(data)
        session.expunge_all()
    
    def reload_flight_search_table(self, session: Session, search_criteria=None) -> None:
        """Reloads the flight search table."""
        self.flight_search_results = [] # type: List[models.Flight]

        # TODO: Implement search criteria.
        if search_criteria:
            self.flight_search_results = session.query(models.Flight).all()
        else:
            self.flight_search_results = session.query(models.Flight).filter(models.Flight.active == True).all()
        
        data = []
        for flight in self.flight_search_results:
            row = []
            row.append(flight.uuid)
            row.append(flight.drone.combobox_name)
            row.append(flight.type_.name)
            row.append(flight.status.name)
            data.append(row)

        self.flight_search_widget.set_record_data(data)
        session.expunge_all()
    
    def reload_equipment_search_table(self, session: Session, search_criteria=None) -> None:
        """Reloads the equipment search table."""
        self.equipment_search_results = [] # type: List[models.Equipment]

        # TODO: Implement search criteria.
        if search_criteria:
            self.equipment_search_results = session.query(models.Equipment).all()
        else:
            self.equipment_search_results = session.query(models.Equipment).all()
        
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
        session.expunge_all()
    
    def reload_flight_controller_search_table(self, session: Session, search_criteria=None) -> None:
        """Reloads the flight controller search table."""
        self.flight_controller_search_results = []

        # TODO: Implement search criteria.
        if search_criteria:
            self.flight_controller_search_results = models.Equipment.find_by_type(session, models.EquipmentType.find_by_name(session, "Remote Controller"))
        else:
            self.flight_controller_search_results = models.Equipment.find_by_type(session, models.EquipmentType.find_by_name(session, "Remote Controller"))
        
        data = []
        for flight_controller in self.flight_controller_search_results:
            row = []
            row.append(flight_controller.serial_number)
            row.append(flight_controller.name)
            row.append(flight_controller.status)
            data.append(row)
        
        self.flight_controller_search_widget.set_record_data(data)
        session.expunge_all()
    
    def reload_flight_equipment_table(self, session: Session, flight: models.Flight):
        """Reloads the flight equipment table."""
        self.flight_equipment_table.setRowCount(0)
        flight = session.query(models.Flight).filter_by(id=flight.id).first()

        for equipment in flight.used_equipment:
            self.flight_equipment_table.insertRow(self.flight_equipment_table.rowCount())
            self.flight_equipment_table.setItem(self.flight_equipment_table.rowCount() - 1, 0, QtWidgets.QTableWidgetItem(equipment.serial_number))
            self.flight_equipment_table.setItem(self.flight_equipment_table.rowCount() - 1, 1, QtWidgets.QTableWidgetItem(equipment.name))
            self.flight_equipment_table.setItem(self.flight_equipment_table.rowCount() - 1, 2, QtWidgets.QTableWidgetItem(equipment.description))
            self.flight_equipment_table.setItem(self.flight_equipment_table.rowCount() - 1, 3, QtWidgets.QTableWidgetItem(equipment.type_.name))
            self.flight_equipment_table.setItem(self.flight_equipment_table.rowCount() - 1, 4, QtWidgets.QTableWidgetItem(equipment.status))

        # self.flight_equipment_table.resizeColumnsToContents()

        if len(self.selected_flight.used_equipment) == 0:
            self.flight_equipment_edit_button.setEnabled(False)
            self.flight_equipment_remove_button.setEnabled(False)
        else:
            self.flight_equipment_edit_button.setEnabled(True)
            self.flight_equipment_remove_button.setEnabled(True)
        session.expunge_all()
    
    def reload_drone_batteries_table(self, session: Session, drone: models.Drone):
        """Reloads the drone linked batteries table"""
        self.drone_batteries_table.setRowCount(0)
        drone = session.query(models.Drone).filter_by(id=drone.id)

        for battery in drone.batteries:
            self.drone_batteries_table.insertRow(self.drone_batteries_table.rowCount())
            self.drone_batteries_table.setItem(self.drone_batteries_table.rowCount() - 1, 0, QtWidgets.QTableWidgetItem(battery.serial_number))
            self.drone_batteries_table.setItem(self.drone_batteries_table.rowCount() - 1, 1, QtWidgets.QTableWidgetItem(battery.name))
            self.drone_batteries_table.setItem(self.drone_batteries_table.rowCount() - 1, 2, QtWidgets.QTableWidgetItem(battery.purchase_date.strftime(config.DATE_FORMAT)))
            self.drone_batteries_table.setItem(self.drone_batteries_table.rowCount() - 1, 3, QtWidgets.QTableWidgetItem(battery.status))

        if len(drone.batteries) == 0:
            self.drone_battery_edit_button.setEnabled(False)
            self.drone_battery_remove_button.setEnabled(False)
        else:
            self.drone_battery_edit_button.setEnabled(True)
            self.drone_battery_remove_button.setEnabled(True)
        session.expunge_all()

    def _populate_combobox(self, combo_box: QtWidgets.QComboBox, data_list: list, add_blank=False) -> None:
        """Populates a combo box with data from a list."""
        combo_box.clear()
        if add_blank:
            combo_box.addItem("")
        for data in data_list:
            combo_box.addItem(data)
        
    def backup_database(self) -> None:
        """Backs up the database."""
        # TODO: Implement this.
        raise NotImplementedError()
        self.statusBar().showMessage("Backing up database...")
        database.backup_database(config.DATABASE_DUMPS_FOLDER)
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

        # self.drone_name_line_edit.editingFinished.connect(lambda: self.selected_drone.set_attribute(models.Drone.name, self.drone_name_line_edit.text()))
        # self.drone_status_combobox.currentIndexChanged.connect(lambda: self.selected_drone.set_attribute(models.Drone.status, self.drone_status_combobox.currentText()))
        # self.drone_description_line_edit.editingFinished.connect(lambda: self.selected_drone.set_attribute(models.Drone.description, self.drone_description_line_edit.text()))
        # self.drone_serial_number_line_edit.editingFinished.connect(lambda: self.selected_drone.set_attribute(models.Drone.serial_number, self.drone_serial_number_line_edit.text()))
        # self.drone_model_line_edit.editingFinished.connect(lambda: self.selected_drone.set_attribute(models.Drone.model, self.drone_model_line_edit.text()))
        # self.drone_flight_controller_combobox.currentIndexChanged.connect(lambda: self.selected_drone.set_attribute(models.Drone.flight_controller_id, models.FlightController.find_by_combobox_name(self.drone_flight_controller_combobox.currentText()).id))
        # self.drone_color_line_edit.editingFinished.connect(lambda: self.selected_drone.set_attribute(models.Drone.color, self.drone_color_line_edit.text()))
        # self.drone_item_value_spinbox.valueChanged.connect(lambda: self.selected_drone.set_attribute(models.Drone.item_value, self.drone_item_value_spinbox.value()))
        # self.drone_date_purchased_date_edit.editingFinished.connect(lambda: self.selected_drone.set_attribute(models.Drone.purchase_date, self.drone_date_purchased_date_edit.date().toPyDate()))
        # self.drone_max_speed_spinbox.editingFinished.connect(lambda: self.selected_drone.set_attribute(models.Drone.max_speed, self.drone_max_speed_spinbox.value()))
        # self.drone_max_vertical_speed_spinbox.editingFinished.connect(lambda: self.selected_drone.set_attribute(models.Drone.max_vertical_speed, self.drone_max_vertical_speed_spinbox.value()))
        # self.drone_max_payload_weight_spinbox.editingFinished.connect(lambda: self.selected_drone.set_attribute(models.Drone.max_payload_weight, self.drone_max_payload_weight_spinbox.value()))
        # self.drone_weight_spinbox.editingFinished.connect(lambda: self.selected_drone.set_attribute(models.Drone.weight, self.drone_weight_spinbox.value()))
        # self.drone_max_service_interval_spinbox.editingFinished.connect(lambda: self.selected_drone.set_attribute(models.Drone.max_service_interval, self.drone_max_service_interval_spinbox.value()))
        # self.drone_geometry_combobox.currentIndexChanged.connect(lambda: self.selected_drone.set_attribute(models.Drone.geometry_id, models.DroneGeometry.find_by_name(self.drone_geometry_combobox.currentText()).id))
        # self.drone_battery_notes_plain_text_edit.textChanged.connect(lambda: self.selected_drone_battery.set_attribute(models.Battery.notes, self.drone_battery_notes_plain_text_edit.toPlainText()))
        # self.drone_battery_status_combobox.currentIndexChanged.connect(lambda: self.selected_drone_battery.set_attribute(models.Battery.status, self.drone_battery_status_combobox.currentText()))
        # self.drone_battery_capacity_spinbox.editingFinished.connect(lambda: self.selected_drone_battery.set_attribute(models.Battery.capacity, self.drone_battery_capacity_spinbox.value()))
        # self.drone_battery_cell_count_spinbox.editingFinished.connect(lambda: self.selected_drone_battery.set_attribute(models.Battery.cell_count, self.drone_battery_cell_count_spinbox.value()))
        # self.drone_battery_max_flight_time_spinbox.editingFinished.connect(lambda: self.selected_drone_battery.set_attribute(models.Battery.max_flight_time, self.drone_battery_max_flight_time_spinbox.value()))
        # self.drone_battery_max_charge_cycles_spinbox.editingFinished.connect(lambda: self.selected_drone_battery.set_attribute(models.Battery.max_charge_cycles, self.drone_battery_max_charge_cycles_spinbox.value()))
        # self.drone_battery_max_flight_spinbox.editingFinished.connect(lambda: self.selected_drone_battery.set_attribute(models.Battery.max_flight, self.drone_battery_max_flight_spinbox.value()))
        # self.drone_battery_weight_spinbox.editingFinished.connect(lambda: self.selected_drone_battery.set_attribute(models.Battery.weight, self.drone_battery_weight_spinbox.value()))
        # self.drone_battery_item_value_spinbox.editingFinished.connect(lambda: self.selected_drone_battery.set_attribute(models.Battery.item_value, self.drone_battery_item_value_spinbox.value()))
        # self.drone_battery_date_purchased_date_edit.editingFinished.connect(lambda: self.selected_drone_battery.set_attribute(models.Battery.purchase_date, self.drone_battery_date_purchased_date_edit.date().toPyDate()))
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

        # self.battery_status_combobox.currentIndexChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.status, self.battery_status_combobox.currentText()))
        # self.battery_capacity_spinbox.valueChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.capacity, self.battery_capacity_spinbox.value()))
        # self.battery_cell_count_spinbox.valueChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.cell_count, self.battery_cell_count_spinbox.value()))
        # self.battery_max_flight_time_spinbox.valueChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.max_flight_time, self.battery_max_flight_time_spinbox.value()))
        # self.battery_max_charge_cycles_spinbox.valueChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.max_charge_cycles, self.battery_max_charge_cycles_spinbox.value()))
        # self.battery_max_flight_spinbox.valueChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.max_flights, self.battery_max_flight_spinbox.value()))
        # self.battery_weight_spinbox.valueChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.weight, self.battery_weight_spinbox.value()))
        # self.battery_serial_number_line_edit.editingFinished.connect(lambda: self.selected_battery.set_attribute(database.Battery.serial_number, self.battery_serial_number_line_edit.text()))
        # self.battery_chemistry_combobox.currentIndexChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.chemistry_id, database.BatteryChemistry.find_by_combobox_name(self.battery_chemistry_combobox.currentText()).id))
        # self.battery_name_line_edit.editingFinished.connect(lambda: self.selected_battery.set_attribute(database.Battery.name, self.battery_name_line_edit.text()))
        # self.battery_item_value_spinbox.valueChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.item_value, self.battery_item_value_spinbox.value()))
        # self.battery_date_purchased_date_edit.dateChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.purchase_date, self.battery_date_purchased_date_edit.date().toPyDate()))
        # self.battery_notes_plain_text_edit.textChanged.connect(lambda: self.selected_battery.set_attribute(database.Battery.notes, self.battery_notes_plain_text_edit.toPlainText()))

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

        # self.equipment_serial_number_line_edit.editingFinished.connect(lambda: self.selected_equipment.set_attribute(database.Equipment.serial_number, self.equipment_serial_number_line_edit.text()))
        # self.equipment_name_line_edit.editingFinished.connect(lambda: self.selected_equipment.set_attribute(database.Equipment.name, self.equipment_name_line_edit.text()))
        # self.equipment_description_line_edit.editingFinished.connect(lambda: self.selected_equipment.set_attribute(database.Equipment.description, self.equipment_description_line_edit.text()))
        # self.equipment_type_combobox.currentIndexChanged.connect(lambda: self.selected_equipment.set_attribute(database.Equipment.type_id, database.EquipmentType.find_by_name(self.equipment_type_combobox.currentText()).id))
        # self.equipment_status_combobox.currentIndexChanged.connect(lambda: self.selected_equipment.set_attribute(database.Equipment.status, self.equipment_status_combobox.currentText()))
        # self.equipment_weight_spinbox.valueChanged.connect(lambda: self.selected_equipment.set_attribute(database.Equipment.weight, self.equipment_weight_spinbox.value()))
        # self.equipment_date_purchased_date_edit.dateChanged.connect(lambda: self.selected_equipment.set_attribute(database.Equipment.purchase_date, self.equipment_date_purchased_date_edit.date().toPyDate()))
        # self.equipment_item_value_spinbox.valueChanged.connect(lambda: self.selected_equipment.set_attribute(database.Equipment.item_value, self.equipment_item_value_spinbox.value()))

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

        # self.flight_controller_serial_number_line_edit.editingFinished.connect(lambda: self.selected_flight_controller.set_attribute(database.FlightController.serial_number, self.flight_controller_serial_number_line_edit.text()))
        # self.flight_controller_name_line_edit.editingFinished.connect(lambda: self.selected_flight_controller.set_attribute(database.FlightController.name, self.flight_controller_name_line_edit.text()))
        # self.flight_controller_status_combobox.currentIndexChanged.connect(lambda: self.selected_flight_controller.set_attribute(database.FlightController.status, self.flight_controller_status_combobox.currentText()))
        # self.flight_controller_date_purchased_date_edit.dateChanged.connect(lambda: self.selected_flight_controller.set_attribute(database.FlightController.purchase_date, self.flight_controller_date_purchased_date_edit.date().toPyDate()))
        # self.flight_controller_item_value_spinbox.valueChanged.connect(lambda: self.selected_flight_controller.set_attribute(database.FlightController.item_value, self.flight_controller_item_value_spinbox.value()))


        # Flight tab
        self.flight_search_widget.search_button.clicked.connect(self.on_search_flight_button_clicked)
        self.flight_search_widget.advanced_search_button.clicked.connect(self.on_search_flight_advanced_button_clicked)
        self.flight_search_widget.results_table.itemDoubleClicked.connect(self.on_flight_search_result_table_item_double_clicked)
        self.flight_search_widget.view_button.clicked.connect(self.on_search_flight_view_item_button_clicked)
        self.flight_print_inventory_label_button.clicked.connect(self.on_flight_print_inventory_label_button_clicked)
        self.flight_print_inventory_label_button.setEnabled(False)
        self.flight_add_button.clicked.connect(self.add_flight)
        self.flight_delete_button.clicked.connect(self.delete_flight)

        # self.flight_name_line_edit.editingFinished.connect(lambda: self.selected_flight.set_attribute(database.Flight.name, self.flight_name_line_edit.text()))
        # self.flight_external_case_id_line_edit.editingFinished.connect(lambda: self.selected_flight.set_attribute(database.Flight.external_case_id, self.flight_external_case_id_line_edit.text()))
        # self.night_flight_checkbox.stateChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.night_flight, self.night_flight_checkbox.isChecked()))
        # self.flight_active_checkbox.stateChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.active, self.flight_active_checkbox.isChecked()))
        self.flight_active_checkbox.setToolTip(models.Flight.active.doc)
        # self.flight_date_datetimeedit.dateTimeChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.date, self.flight_date_datetimeedit.dateTime().toPyDateTime()))
        # self.flight_duration_spinbox.valueChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.duration, self.flight_duration_spinbox.value()))
        # self.flight_type_combbox.currentIndexChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.type_id, database.FlightType.find_by_name(self.flight_type_combbox.currentText()).id))
        # self.flight_notes_plaintextedit.textChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.notes, self.flight_notes_plaintextedit.toPlainText()))
        # self.flight_battery_notes_plaintextedit.textChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.battery_notes, self.flight_battery_notes_plaintextedit.toPlainText()))
        # self.flight_in_flight_notes_plaintextedit.textChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.in_flight_notes, self.flight_in_flight_notes_plaintextedit.toPlainText()))
        # self.flight_post_flight_notes_plaintextedit.textChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.post_flight_notes, self.flight_post_flight_notes_plaintextedit.toPlainText()))
        # self.flight_operation_type_combobox.currentIndexChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.operation_type_id, database.FlightOperationType.find_by_name(self.flight_operation_type_combobox.currentText()).id))
        # self.flight_utm_authorization_line_edit.editingFinished.connect(lambda: self.selected_flight.set_attribute(database.Flight.utm_authorization, self.flight_utm_authorization_line_edit.text()))
        # self.flight_operation_aproval_type_combobox.currentIndexChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.operation_approval_id, database.FlightOperationApproval.find_by_name(self.flight_operation_aproval_type_combobox.currentText()).id))
        # self.flight_legal_rule_combobox.currentIndexChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.legal_rule_id, database.LegalRule.find_by_name(self.flight_legal_rule_combobox.currentText()).id))
        # self.flight_legal_rule_details_line_edit.editingFinished.connect(lambda: self.selected_flight.set_attribute(database.Flight.legal_rule_details, self.flight_legal_rule_details_line_edit.text()))
        # self.flight_max_altitude_spinbox.valueChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.max_altitude, self.flight_max_altitude_spinbox.value()))
        # self.flight_distance_traveled_spinbox.valueChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.distance_traveled, self.flight_distance_traveled_spinbox.value()))
        # self.flight_drone_combobox.currentIndexChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.drone_id, database.Drone.find_by_combobox_name(self.flight_drone_combobox.currentText()).id))
        # self.flight_battery_combobox.currentIndexChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.battery_id, database.Battery.find_by_combobox_name(self.flight_battery_combobox.currentText()).id))
        self.flight_equipment_add_button.clicked.connect(self.on_flight_equipment_add_button_clicked)
        self.flight_equipment_edit_button.clicked.connect(self.on_flight_equipment_edit_button_clicked)
        self.flight_equipment_remove_button.clicked.connect(self.on_flight_equipment_remove_button_clicked)


        # self.flight_encounter_with_law_checkbox.stateChanged.connect(lambda: self.selected_flight.set_attribute(database.Flight.encounter_with_law, self.flight_encounter_with_law_checkbox.isChecked()))

        # self.flight_weather_cloud_cover_spinbox.valueChanged.connect(lambda: self.selected_flight.weather.set_attribute(database.Weather.cloud_cover, self.flight_weather_cloud_cover_spinbox.value()))
        # self.flight_weather_humidity_spinbox.valueChanged.connect(lambda: self.selected_flight.weather.set_attribute(database.Weather.humidity, self.flight_weather_humidity_spinbox.value()))
        # self.flight_weather_temperature_spinbox.valueChanged.connect(lambda: self.selected_flight.weather.set_attribute(database.Weather.temperature, self.flight_weather_temperature_spinbox.value()))
        # self.flight_weather_wind_speed_spinbox.valueChanged.connect(lambda: self.selected_flight.weather.set_attribute(database.Weather.wind_speed, self.flight_weather_wind_speed_spinbox.value()))
        # self.flight_weather_wind_direction_spinbox.valueChanged.connect(lambda: self.selected_flight.weather.set_attribute(database.Weather.wind_direction, self.flight_weather_wind_direction_spinbox.value()))
        # self.flight_weather_notes_plaintextedit.textChanged.connect(lambda: self.selected_flight.weather.set_attribute(database.Weather.notes, self.flight_weather_notes_plaintextedit.toPlainText()))
    
    def on_splitter_moved(self, pos, index):
        splitter = self.sender()
        name = splitter.objectName()
        self.settings.beginGroup("GUI Properties")
        self.settings.setValue(name, splitter.saveState())
        self.settings.endGroup()

    def on_drone_geometry_combobox_changed(self, index: int) -> None:
        with DBContext() as session:
            name = self.drone_geometry_combobox.itemText(index)
            self.geometry = models.DroneGeometry.find_by_name(session, name) # type: models.DroneGeometry
            if self.geometry is None: return
            image = self.geometry.image
            qimage = image.to_QImage()
            qimage = qimage.scaled(config.THUMBNAIL_WIDTH, config.THUMBNAIL_HEIGHT, QtCore.Qt.KeepAspectRatio) # Scale the image
            pixmap = QtGui.QPixmap.fromImage(qimage)
            self.drone_geometry_image.setPixmap(pixmap)
            session.expunge_all()

    def on_drone_battery_create_new_button_clicked(self) -> None:
        drone_battery_dialog = dialogs.CreateBatteryDialog(self)
        drone_battery_dialog.exec()
        battery = drone_battery_dialog.battery
        if battery is not None:
            self.selected_drone.add_battery(battery)
            self.reload_drone_form(self.selected_drone)
    
    def on_drone_battery_add_button_clicked(self) -> None:
        dialog = dialogs.SelectBatteryDialog(current_batteries=self.selected_drone.batteries, parent=self)
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
        selected_battery = self.selected_drone.batteries[index]
        try:
            self.selected_drone.remove_battery(selected_battery)
        except errors.BatteryRemoveError as e:
            self.show_error(e)
        self.reload_drone_batteries_table(self.selected_drone)

    def on_drone_batteries_table_item_double_clicked(self, item: QtWidgets.QTableWidgetItem) -> None:
        index = self.drone_batteries_table.currentRow()
        if index < 0: return
        selected_battery = self.selected_drone.batteries[index]
        self.reload_drone_battery_form(selected_battery)

    def on_flight_equipment_add_button_clicked(self) -> None:
        equipment_dialog = dialogs.SelectFlightEquipmentDialog(flight=self.selected_flight)
        equipment_dialog.exec()
        self.reload_flight_equipment_table(self.selected_flight)
    
    def on_flight_equipment_edit_button_clicked(self) -> None:
        selected_equipment = self.selected_flight.used_equipment[self.flight_equipment_table.currentRow()]
        equipment_dialog = dialogs.SelectFlightEquipmentDialog(flight=self.selected_flight, equipment=selected_equipment)
        equipment_dialog.exec()
        self.reload_flight_equipment_table(self.selected_flight)
    
    def on_flight_equipment_remove_button_clicked(self) -> None:
        index = self.flight_equipment_table.currentRow()
        if index < 0: return
        selected_equipment = self.selected_flight.used_equipment[index]
        self.selected_flight.remove_equipment(selected_equipment)

        if len(self.selected_flight.used_equipment) == 0:
            self.flight_equipment_edit_button.setEnabled(False)
            self.flight_equipment_remove_button.setEnabled(False)

        self.reload_flight_equipment_table(self.selected_flight)

    def print_inventory_label(self, label_name: str, label_value: str):
        """Prints a label with the given name and value."""

        try:
            self.label_printer.register_label_file(self.inventory_label_file_path)
        except errors.SetLabelFileError as error:
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

    def reload_drone_form(self, drone: models.Drone):
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

        if config.LABEL_PRINTING_ENABLED:
            self.drone_print_inventory_label_button.setEnabled(True)

        self.selected_drone_battery = drone.batteries[0]

        # General tab
        self.drone_name_line_edit.setText(drone.name)
        self.drone_status_combobox.setCurrentText(drone.status)
        self.drone_description_line_edit.setText(drone.description)
        self.drone_serial_number_line_edit.setText(drone.serial_number)
        self.drone_model_line_edit.setText(drone.model)
        self.drone_flight_controller_combobox.setCurrentText(drone.flight_controller.combobox_name)

        # Details tab
        # self.drone_date_created_value.setText(drone.date_created.strftime("%Y-%m-%d"))
        # self.drone_date_modified_value.setText(drone.date_modified.strftime("%Y-%m-%d"))
        self.drone_color_line_edit.setText(drone.color)
        self.drone_item_value_spinbox.setValue(drone.price)
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

    def reload_drone_battery_form(self, battery: models.Battery):
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
        self.drone_battery_item_value_spinbox.setValue(battery.price)
        self.drone_battery_date_purchased_date_edit.setDate(QtCore.QDate.fromString(battery.purchase_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))

    def reload_battery_form(self, battery: models.Battery):
        """Reloads the battery form with the given battery."""
        self.selected_battery = battery

        if not battery:
            self.batteries_info_groupbox.setEnabled(False)
            self.battery_print_inventory_label_button.setEnabled(False)
            self.battery_delete_button.setEnabled(False)
            return
            
        self.batteries_info_groupbox.setEnabled(True)
        self.battery_delete_button.setEnabled(True)

        if config.LABEL_PRINTING_ENABLED:
            self.battery_print_inventory_label_button.setEnabled(True)

        # self.battery_date_created_value.setText(battery.date_created.strftime("%Y-%m-%d"))
        # self.battery_date_modified_value.setText(battery.date_modified.strftime("%Y-%m-%d"))
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
        self.battery_item_value_spinbox.setValue(battery.price)
        self.battery_date_purchased_date_edit.setDate(QtCore.QDate.fromString(battery.purchase_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))

        if battery.notes:
            self.battery_notes_plain_text_edit.setPlainText(battery.notes)
        else:
            self.battery_notes_plain_text_edit.setPlainText("")
    
    def reload_equipment_form(self, equipment: models.Equipment):
        """Reloads the equipment form with the given equipment."""
        self.selected_equipment = equipment

        if not equipment:
            self.equipment_info_groupbox.setEnabled(False)
            self.equipment_print_inventory_label_button.setEnabled(False)
            self.equipment_delete_button.setEnabled(False)
            return

        self.equipment_info_groupbox.setEnabled(True)

        if config.LABEL_PRINTING_ENABLED:
            self.equipment_print_inventory_label_button.setEnabled(True)
        
        # self.equipment_date_created_value.setText(equipment.date_created.strftime("%Y-%m-%d"))
        # self.equipment_date_modified_value.setText(equipment.date_modified.strftime("%Y-%m-%d"))

        self.equipment_serial_number_line_edit.setText(equipment.serial_number)
        self.equipment_name_line_edit.setText(equipment.name)
        self.equipment_description_line_edit.setText(equipment.description)
        self.equipment_type_combobox.setCurrentText(equipment.type_.name)
        self.equipment_status_combobox.setCurrentText(equipment.status)
        self.equipment_weight_spinbox.setValue(equipment.weight)
        self.equipment_date_purchased_date_edit.setDate(QtCore.QDate.fromString(equipment.purchase_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))
        self.equipment_item_value_spinbox.setValue(equipment.price)
        self.equipmen_total_flights_value.setText(str(equipment.total_flights))
        self.equipmen_total_flight_time_value.setText(str(round(equipment.total_flight_time / 60, 2))) # Show in hours
    
    def reload_flight_controller_form(self, flight_controller: models.Equipment):
        """Reloads the flight controller for with the given flight controller."""
        self.selected_flight_controller = flight_controller

        if not flight_controller:
            self.flight_controller_info_groupbox.setEnabled(False)
            self.flight_controller_print_inventory_label_button.setEnabled(False)
            self.flight_controller_delete_button.setEnabled(False)
            return

        self.flight_controller_info_groupbox.setEnabled(True)
        self.flight_controller_delete_button.setEnabled(True)

        if config.LABEL_PRINTING_ENABLED:
            self.flight_controller_print_inventory_label_button.setEnabled(True)

        # self.flight_controller_date_created_value.setText(flight_controller.date_created.strftime("%Y-%m-%d"))
        # self.flight_controller_date_modified_value.setText(flight_controller.date_modified.strftime("%Y-%m-%d"))
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
        self.flight_controller_item_value_spinbox.setValue(flight_controller.price)
    
    def reload_flight_form(self, flight: models.Flight):
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

        if config.LABEL_PRINTING_ENABLED:
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
        message_box.setText(f"{config.PROGRAM_NAME} - Version {config.PROGRAM_VERSION}")
        message_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        message_box.exec_()
    
    def add_drone(self) -> None:
        """Opens a dialog box to add a new drone."""
        with DBContext() as session:
            dialog = dialogs.CreateDroneDialog(session, self)
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
        except errors.Error as e:
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
        except errors.Error as e:
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
        except errors.Error as e:
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
        except errors.Error as e:
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
        except errors.Error as e:
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
        self.splash.closing.connect(lambda: self.main_window.show())
        # self.splash.closing.connect(lambda: self.main_window.showMaximized())
        self.splash.show()
        self.splash.loading()
        

def show_new_release_dialog(version: str, html_url: str):
    dialog = QtWidgets.QMessageBox()
    dialog.setWindowTitle("New release available")
    dialog.setText(f"New release available: {version}")
    dialog.setInformativeText("Would you like to open the download page?")
    dialog.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
    dialog.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Yes)
    dialog.setIcon(QtWidgets.QMessageBox.Icon.Information)
    if dialog.exec() == QtWidgets.QMessageBox.StandardButton.No:
        return

    # Open an internet browser to download the release
    try:
        webbrowser.open(html_url)
    except Exception as e:
        logger.exception(f"Failed to open browser to download release.")
        QtWidgets.QMessageBox.critical(None, "Error", f"Could not open browser: {e}")


def prompt_user(skip_check: bool=False):
        if not skip_check and not (config.DATABASE_USER.value == ""\
            or config.DATABASE_PASSWORD.value == ""\
            or config.DATABASE_HOST.value == ""\
            or config.DATABASE_PORT.value == ""):
            return

        logger.warning("Missing required registry key values. Prompting user to enter data.")
        
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Missing Required Data")
        v_layout = QtWidgets.QVBoxLayout()
        dialog.setLayout(v_layout)
        username_lineEdit = QtWidgets.QLineEdit()
        password_lineEdit = QtWidgets.QLineEdit()
        host_lineEdit = QtWidgets.QLineEdit()
        port_spinBox = QtWidgets.QSpinBox()

        password_lineEdit.setEchoMode(QtWidgets.QLineEdit.EchoMode.PasswordEchoOnEdit)
        port_spinBox.setButtonSymbols(QtWidgets.QSpinBox.ButtonSymbols.NoButtons)
        port_spinBox.setMinimum(1024)
        port_spinBox.setMaximum(65535)

        username_lineEdit.editingFinished.connect(lambda: username_lineEdit.setText(username_lineEdit.text().strip()))
        password_lineEdit.editingFinished.connect(lambda: password_lineEdit.setText(password_lineEdit.text().strip()))
        host_lineEdit.editingFinished.connect(lambda: host_lineEdit.setText(host_lineEdit.text().strip()))

        info_label = QtWidgets.QLabel(f"Please fill in the missing MySQL database authentication info.\n\nAll settings are stored in the registry at: '{config.DATABASE_USER.base_hive_location}'")

        v_layout.addWidget(info_label)
        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow(QtWidgets.QLabel("Username:"), username_lineEdit)
        form_layout.addRow(QtWidgets.QLabel("Password:"), password_lineEdit)
        form_layout.addRow(QtWidgets.QLabel("Host:"), host_lineEdit)
        form_layout.addRow(QtWidgets.QLabel("Port:"), port_spinBox)
        v_layout.addSpacing(10)
        v_layout.addLayout(form_layout)
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Save | QtWidgets.QDialogButtonBox.StandardButton.Close)
        v_layout.addWidget(button_box)

        username_lineEdit.setText(config.DATABASE_USER.value)
        password_lineEdit.setText(config.DATABASE_PASSWORD.value)
        host_lineEdit.setText(config.DATABASE_HOST.value)
        port_spinBox.setValue(int(config.DATABASE_PORT.value))

        def on_accept():
            config.DATABASE_USER.value = username_lineEdit.text()
            config.DATABASE_PASSWORD.value = password_lineEdit.text()
            config.DATABASE_HOST.value = host_lineEdit.text()
            config.DATABASE_PORT.value = str(port_spinBox.text())

            config.DATABASE_USER.save()
            config.DATABASE_PASSWORD.save()
            config.DATABASE_HOST.save()
            config.DATABASE_PORT.save()

            if config.DATABASE_USER.value == ""\
                or config.DATABASE_PASSWORD.value == ""\
                or config.DATABASE_HOST.value == ""\
                or config.DATABASE_PORT.value == "":
                QtWidgets.QMessageBox.warning(dialog, "Warning", "Please fill in all blank fields.")
                return

            dialog.accept()

        def on_reject():
            dialog.reject()

        button_box.accepted.connect(on_accept)
        button_box.rejected.connect(on_reject)

        result = dialog.exec()
        if result == 0:
            logger.warning("User did not set missing required database info. The program can not continue.")
            QtWidgets.QMessageBox.warning(dialog, "Error", "Missing required database info. The program can not continue.")
            exit(0)
        else:
            logger.info("Missing required database info saved. Application restart required to apply changes.")
            QtWidgets.QMessageBox.warning(dialog, "Error", "Missing required database info saved. Application restart required to apply changes.\n\nProgram will close after this dialog closes.")
            exit(0)




if __name__ == "__main__":
    newer, version, url = check_for_updates()
    if newer:
        show_new_release_dialog(version, url)

    prompt_user()

    try:
        models.create_database()
    except Exception as error:
        logger.exception("Could not create database.")
        QtWidgets.QMessageBox.warning(None, "Error", "There was an issue connecting to the database. Check database authentication settings.")
        prompt_user(skip_check=True)
        exit(0)

    models.create_database()
    load_default_data()
    app = Application([])
    app.exec_()