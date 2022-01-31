from __future__ import annotations
from abc import abstractmethod
from dataclasses import dataclass, field
from PyQt5 import QtCore, QtGui, QtWidgets


import utilities
from database import global_session, generate_random_string, Battery, Drone, DroneGeometry, Flight, FlightController, BatteryChemistry, Equipment, EquipmentType, Equipment
from customwidgets import CustomQTableWidget
from app import THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT


@dataclass
class ValidationResult:
    is_valid: bool = True
    messages: list[str] = field(default_factory=list)

    def add_error(self, error_message: str) -> None:
        self.is_valid = False
        self.messages.append(error_message)


class Dialog(QtWidgets.QDialog):

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setWindowTitle('Dialog')
        self.setSizeGripEnabled(True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.setModal(True)

        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)
    
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        super().closeEvent(event)

    @abstractmethod
    def generate_serial_number(self) -> None:
        """Generate a serial number for the current dialog."""
        pass

    @abstractmethod
    def serial_number_valid(self, serial_number: str) -> bool:
        """Check if the serial number is valid."""
        pass
    
    @abstractmethod
    def validate_form(self) -> ValidationResult:
        """Validate user input for the current dialog."""
        pass
    
    @abstractmethod
    def save(self) -> None:
        """Save the current dialog object to database."""
        pass


class SelectBatteryDialog(QtWidgets.QDialog):
    def __init__(self, current_batteries: Battery=None, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        self.battery = None # type: Battery
        self.batteries = current_batteries

        self.setWindowTitle("Select Battery")
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(QtWidgets.QLabel("Select a battery to add to the drone."))
        self.form_layout = QtWidgets.QFormLayout()
        self.battery_combobox = QtWidgets.QComboBox()
        batteries = [battery for battery in Battery.find_all()]
        current_batteries = [battery for battery in self.batteries]
        self.battery_combobox_items = [battery.combobox_name for battery in batteries if battery not in current_batteries]
        self.battery_combobox.addItems(self.battery_combobox_items)
        self.form_layout.addRow(QtWidgets.QLabel("Battery:"), self.battery_combobox)
        self.layout().addLayout(self.form_layout)
        button_layout = QtWidgets.QHBoxLayout()
        add_button = QtWidgets.QPushButton("Add")
        add_button.clicked.connect(self.add_battery)
        add_button.clicked.connect(self.close)
        button_layout.addWidget(add_button)
        self.layout().addLayout(button_layout)

    def add_battery(self):
        self.battery = Battery.find_by_combobox_name(self.battery_combobox.currentText())
        self.close()


class AddDroneDialog(Dialog):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        self.drone = None # type: Drone
        self.geometry = None # type: DroneGeometry
        self.batteries = [] # type: list[Battery]
        self.flight_controller = None # type: FlightController
        
        self.setWindowTitle("Add Drone")
        self.resize(700, 600)

        self.drone_name_label = QtWidgets.QLabel("Drone Name:")
        self.drone_name_input = QtWidgets.QLineEdit()
        self.drone_name_input.editingFinished.connect(lambda: utilities.clean_text_input(self.drone_name_input))

        self.drone_serial_number_label = QtWidgets.QLabel("Drone Serial Number:")
        self.drone_serial_number_input = QtWidgets.QLineEdit()
        self.drone_serial_number_input.editingFinished.connect(lambda: utilities.clean_text_input(self.drone_serial_number_input))
        self.generate_battery_serial_number_button = QtWidgets.QPushButton("Generate")
        self.generate_battery_serial_number_button.clicked.connect(self.generate_serial_number)
        self.generate_battery_serial_number_button.setFixedWidth(75)

        self.drone_flight_controller_label = QtWidgets.QLabel("Flight Controller:")
        self.drone_flight_controller_combobox = QtWidgets.QComboBox()
        self.drone_flight_controller_combobox.addItem("")
        self.drone_flight_controller_combobox.addItems([flight_controller.combobox_name for flight_controller in FlightController.find_all()])
        self.drone_flight_controller_combobox.setCurrentIndex(0)
        self.drone_flight_controller_combobox.currentTextChanged.connect(self.set_flight_controller)
        self.drone_add_flight_controller_button = QtWidgets.QPushButton("Add")
        self.drone_add_flight_controller_button.setFixedWidth(75)
        self.drone_add_flight_controller_button.clicked.connect(self.add_flight_controller)
        
        self.drone_batteries_table = CustomQTableWidget(self)
        columns = [
            "[Serial Number] - Name",
            "Capacity (mAh)",
            "Status"
        ]
        self.drone_batteries_table.set_table_headers(columns)
        self.drone_batteries_table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.drone_batteries_table.setColumnWidth(0, 250)
        self.drone_batteries_table.setColumnWidth(1, 150)
        self.drone_batteries_table.setColumnWidth(2, 150)
        self.drone_add_new_battery_button = QtWidgets.QPushButton("Create New")
        self.drone_add_new_battery_button.clicked.connect(self.add_new_battery)
        self.drone_add_new_battery_button.setFixedWidth(75)
        self.drone_add_battery_button = QtWidgets.QPushButton("Add")
        self.drone_add_battery_button.clicked.connect(self.add_battery)
        self.drone_add_battery_button.setFixedWidth(75)
        self.drone_remove_battery_button = QtWidgets.QPushButton("Remove")
        self.drone_remove_battery_button.setEnabled(False)
        self.drone_remove_battery_button.clicked.connect(self.remove_battery)
        self.drone_remove_battery_button.setFixedWidth(75)

        self.drone_geometry_label = QtWidgets.QLabel("Geometry:")
        self.drone_geometry_combobox = QtWidgets.QComboBox()
        self.drone_geometry_combobox.addItems([geometry.name for geometry in DroneGeometry.find_all()])
        self.drone_geometry_combobox.setCurrentIndex(1)
        self.drone_geometry_combobox.currentIndexChanged.connect(self.on_drone_geometry_combobox_changed)
        self.drone_geometry_image = QtWidgets.QLabel()

        self.drone_add_button = QtWidgets.QPushButton("Add Drone")
        self.drone_add_button.clicked.connect(self.add_drone)

        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow(self.drone_name_label, self.drone_name_input)
        h_box = QtWidgets.QHBoxLayout()
        h_box.addWidget(self.drone_serial_number_input, stretch=1)
        h_box.addWidget(self.generate_battery_serial_number_button)
        form_layout.addRow(self.drone_serial_number_label, h_box)
        h_box = QtWidgets.QHBoxLayout()
        h_box.addWidget(self.drone_flight_controller_combobox, stretch=1)
        h_box.addWidget(self.drone_add_flight_controller_button)
        form_layout.addRow(self.drone_flight_controller_label, h_box)

        self.main_layout.addLayout(form_layout)

        self.drone_battery_button_layout = QtWidgets.QVBoxLayout()
        self.drone_battery_button_layout.addWidget(self.drone_add_new_battery_button)
        self.drone_battery_button_layout.addWidget(self.drone_add_battery_button)
        self.drone_battery_button_layout.addWidget(self.drone_remove_battery_button)
        self.drone_battery_button_layout.addStretch(1)

        self.drone_battery_layout = QtWidgets.QHBoxLayout()
        self.drone_battery_layout.addWidget(self.drone_batteries_table, stretch=1)
        self.drone_battery_layout.addLayout(self.drone_battery_button_layout)

        self.main_layout.addSpacing(10)
        self.main_layout.addLayout(self.drone_battery_layout)

        self.drone_geometry_layout = QtWidgets.QHBoxLayout()
        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow(self.drone_geometry_label, self.drone_geometry_combobox)
        self.drone_geometry_layout.addLayout(form_layout)

        self.main_layout.addLayout(self.drone_geometry_layout)
        self.main_layout.addWidget(self.drone_geometry_image, alignment=QtCore.Qt.AlignHCenter)
        self.main_layout.addWidget(self.drone_add_button)

        self.drone_geometry_combobox.setCurrentIndex(0)
    
    def set_flight_controller(self, combobox_text: str) -> None:
        self.flight_controller = FlightController.find_by_combobox_name(combobox_text)

    def generate_serial_number(self) -> None:
        serial_number = generate_random_string(Drone)
        self.drone_serial_number_input.setText(serial_number)
    
    def reload_drone_batteries_table(self) -> None:
        self.drone_batteries_table.setRowCount(0)
        for battery in self.batteries:
            row = self.drone_batteries_table.rowCount()
            self.drone_batteries_table.insertRow(row)
            self.drone_batteries_table.setItem(row, 0, QtWidgets.QTableWidgetItem(battery.combobox_name))
            self.drone_batteries_table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(battery.capacity)))
            self.drone_batteries_table.setItem(row, 2, QtWidgets.QTableWidgetItem(battery.status))
    
    def add_flight_controller(self) -> None:
        dialog = CreateFlightControllerDialog(self)
        dialog.exec()
        flight_controller = dialog.flight_controller
        if flight_controller is None: return
        self.flight_controller = flight_controller

    def add_new_battery(self) -> None:
        drone_battery_dialog = CreateBatteryDialog(self)
        drone_battery_dialog.exec()
        battery = drone_battery_dialog.battery
        if battery is None: return
        if battery not in self.batteries:
            self.batteries.append(battery)
            self.reload_drone_batteries_table()
            self.drone_remove_battery_button.setEnabled(True)

    def add_battery(self) -> None:
        dialog = SelectBatteryDialog(current_batteries=self.batteries, parent=self)
        dialog.exec()
        battery = dialog.battery
        if len(dialog.battery_combobox_items) == 1:
            self.drone_add_battery_button.setEnabled(False)

        if battery is None: return
        self.add_battery_to_drone(battery)

    def remove_battery(self) -> None:
        rows = self.drone_batteries_table.selectionModel().selectedRows()
        row_indexes = [row.row() for row in rows]
        batteries = self.batteries
        for row_index in reversed(row_indexes):
            battery = batteries[row_index]
            self.batteries.remove(battery)
            self.drone_add_battery_button.setEnabled(True)
            
        self.reload_drone_batteries_table()
        if len(self.batteries) == 0:
            self.drone_remove_battery_button.setEnabled(False)

    def add_battery_to_drone(self, battery: Battery) -> None:
        if battery is None: return
        if battery not in self.batteries:
            self.batteries.append(battery)
            self.reload_drone_batteries_table()
            self.drone_remove_battery_button.setEnabled(True)
    
    def on_drone_geometry_combobox_changed(self, index: int) -> None:
        name = self.drone_geometry_combobox.itemText(index)
        self.geometry = DroneGeometry.find_by_name(name) # type: DroneGeometry
        if self.geometry is None: return
        image = self.geometry.image
        qimage = image.to_QImage()
        qimage = qimage.scaled(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT, QtCore.Qt.KeepAspectRatio) # Scale the image
        pixmap = QtGui.QPixmap.fromImage(qimage)
        self.drone_geometry_image.setPixmap(pixmap)
    
    def serial_number_valid(self, serial_number: str) -> bool:
        x = global_session.query(Drone).filter_by(serial_number=serial_number).first()
        if x is None: return True
        return False
    
    def validate_form(self) -> ValidationResult:
        validation_result = ValidationResult()

        serial_number = self.drone_serial_number_input.text()
        drone_name = self.drone_name_input.text()
        if serial_number == "":
            validation_result.add_error("Serial number cannot be empty.")
        elif not self.serial_number_valid(serial_number):
            validation_result.add_error("Serial number already exists.")

        if drone_name == "":
            validation_result.add_error("Drone name cannot be empty.")
        if self.flight_controller is None:
            validation_result.add_error("Flight controller must be selected.")
        if self.geometry is None:
            validation_result.add_error("Geometry must be selected.")
        if len(self.batteries) == 0:
            validation_result.add_error("Drone must have at least one battery.")

        return validation_result

    def add_drone(self) -> None:
        validation_result = self.validate_form()

        if not validation_result.is_valid:
            message_box = QtWidgets.QMessageBox()
            message_box.setWindowTitle("Error")
            message_box.setIcon(QtWidgets.QMessageBox.Warning)
            message_box.setText("There were errors in the form.")
            message_box.setInformativeText("\n".join(validation_result.messages))
            message_box.exec()
            return

        serial_number = self.drone_serial_number_input.text()
        flight_controller = self.flight_controller
        geometry = self.geometry
        batteries = self.batteries
        self.drone = Drone.create(
            serial_number=serial_number,
            flight_controller=flight_controller,
            geometry=geometry,
            batteries=batteries,
            name=self.drone_name_input.text()
        )
        self.close()


class CreateBatteryDialog(Dialog):
    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        self.battery = None # type: Battery
        
        self.setWindowTitle("Add Battery")

        self.battery_name_label = QtWidgets.QLabel("Battery Name:")
        self.battery_name_input = QtWidgets.QLineEdit()
        self.battery_name_input.editingFinished.connect(lambda: utilities.clean_text_input(self.battery_name_input))
        
        self.battery_serial_number_label = QtWidgets.QLabel("Battery Serial Number:")
        self.battery_serial_number_input = QtWidgets.QLineEdit()
        self.battery_serial_number_input.editingFinished.connect(lambda: utilities.clean_text_input(self.battery_serial_number_input))
        self.generate_serial_number_button = QtWidgets.QPushButton("Generate")
        self.generate_serial_number_button.clicked.connect(self.generate_serial_number)
        self.generate_serial_number_button.setFixedWidth(75)

        self.battery_chemistry_label = QtWidgets.QLabel("Battery Chemistry:")
        self.battery_chemistry_combobox = QtWidgets.QComboBox()
        battery_chemistries = global_session.query(BatteryChemistry).all()
        self.battery_chemistry_combobox.addItems([battery_chemistry.name for battery_chemistry in battery_chemistries])

        self.battery_capacity_label = QtWidgets.QLabel("Capacity:")
        self.battery_capacity_input = QtWidgets.QSpinBox()
        self.battery_capacity_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.battery_capacity_input.setRange(0, 1000000)
        self.battery_capacity_input.setValue(0)
        self.battery_capacity_input.setSuffix(" mAh")

        self.battery_cell_count_label = QtWidgets.QLabel("Cell Count:")
        self.battery_cell_count_input = QtWidgets.QSpinBox()
        self.battery_cell_count_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.battery_cell_count_input.setRange(0, 100)
        self.battery_cell_count_input.setValue(0)

        self.battery_max_flight_time_label = QtWidgets.QLabel("Max Flight Time:")
        self.battery_max_flight_time_input = QtWidgets.QSpinBox()
        self.battery_max_flight_time_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.battery_max_flight_time_input.setRange(0, 1000000)
        self.battery_max_flight_time_input.setValue(Battery.max_flight_time.default.arg)
        self.battery_max_flight_time_input.setSuffix(" minutes")

        self.battery_max_charge_cycles_label = QtWidgets.QLabel("Max Charge Cycles:")
        self.battery_max_charge_cycles_input = QtWidgets.QSpinBox()
        self.battery_max_charge_cycles_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.battery_max_charge_cycles_input.setRange(0, 1000000)
        self.battery_max_charge_cycles_input.setValue(Battery.max_charge_cycles.default.arg)

        self.battery_max_flights_label = QtWidgets.QLabel("Max Flights:")
        self.battery_max_flights_input = QtWidgets.QSpinBox()
        self.battery_max_flights_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.battery_max_flights_input.setRange(0, 1000000)
        self.battery_max_flights_input.setValue(Battery.max_flights.default.arg)

        self.battery_purchase_date_label = QtWidgets.QLabel("Purchase Date:")
        self.battery_purchase_date_input = QtWidgets.QDateEdit()
        self.battery_purchase_date_input.setDate(QtCore.QDate.currentDate())
        self.battery_purchase_date_input.setCalendarPopup(True)

        self.battery_purchase_price_label = QtWidgets.QLabel("Purchase Price:")
        self.battery_purchase_price_input = QtWidgets.QDoubleSpinBox()
        self.battery_purchase_price_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.battery_purchase_price_input.setRange(0, 1000000)
        self.battery_purchase_price_input.setValue(0)
        self.battery_purchase_price_input.setPrefix("$ ")

        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save)

        self.init_layout()

    def init_layout(self):
        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow(self.battery_name_label, self.battery_name_input)
        h_box = QtWidgets.QHBoxLayout()
        h_box.addWidget(self.battery_serial_number_input, stretch=1)
        h_box.addWidget(self.generate_serial_number_button)
        form_layout.addRow(self.battery_serial_number_label, h_box)
        form_layout.addRow(self.battery_chemistry_label, self.battery_chemistry_combobox)
        form_layout.addRow(self.battery_capacity_label, self.battery_capacity_input)
        form_layout.addRow(self.battery_cell_count_label, self.battery_cell_count_input)
        form_layout.addRow(self.battery_max_flight_time_label, self.battery_max_flight_time_input)
        form_layout.addRow(self.battery_max_charge_cycles_label, self.battery_max_charge_cycles_input)
        form_layout.addRow(self.battery_max_flights_label, self.battery_max_flights_input)
        form_layout.addRow(self.battery_purchase_date_label, self.battery_purchase_date_input)
        form_layout.addRow(self.battery_purchase_price_label, self.battery_purchase_price_input)
        self.main_layout.addLayout(form_layout)
        self.main_layout.addWidget(self.save_button)

    def generate_serial_number(self) -> None:
        serial_number = generate_random_string(Battery)
        self.battery_serial_number_input.setText(serial_number)
    
    def serial_number_valid(self, serial_number: str) -> bool:
        x = global_session.query(Battery).filter_by(serial_number=serial_number).first()
        if x is None: return True
        return False
    
    def validate_form(self) -> ValidationResult:
        validation_result = ValidationResult()

        if self.battery_name_input.text() == "":
            validation_result.add_error("Battery Name is required")
        if self.battery_serial_number_input.text() == "":
            validation_result.add_error("Battery Serial Number is required")
        else:
            if not self.serial_number_valid(self.battery_serial_number_input.text()):
                validation_result.add_error("Battery Serial Number already exists")
        if self.battery_chemistry_combobox.currentText() == "":
            validation_result.add_error("Battery Chemistry is required")
        
        return validation_result
        
    def save(self) -> None:
        validation_result = self.validate_form()

        if not validation_result.is_valid:
            message_box = QtWidgets.QMessageBox()
            message_box.setWindowTitle("Error")
            message_box.setIcon(QtWidgets.QMessageBox.Warning)
            message_box.setText("There were errors in the form.")
            message_box.setInformativeText("\n".join(validation_result.messages))
            message_box.exec()
            return
        
        battery_name = self.battery_name_input.text()
        battery_serial_number = self.battery_serial_number_input.text()
        battery_chemistry = self.battery_chemistry_combobox.currentText()
        battery_capacity = self.battery_capacity_input.value()
        battery_cell_count = self.battery_cell_count_input.value()
        battery_max_flight_time = self.battery_max_flight_time_input.value()
        battery_max_charge_cycles = self.battery_max_charge_cycles_input.value()
        battery_max_flights = self.battery_max_flights_input.value()
        battery_purchase_date = self.battery_purchase_date_input.date().toPyDate()
        battery_purchase_price = self.battery_purchase_price_input.value()

        battery_chemistry_object = global_session.query(BatteryChemistry).filter_by(name=battery_chemistry).first()
        self.battery = Battery(
            name=battery_name,
            serial_number=battery_serial_number,
            chemistry_id=battery_chemistry_object.id,
            capacity=battery_capacity,
            cell_count=battery_cell_count,
            max_flight_time=battery_max_flight_time,
            max_charge_cycles=battery_max_charge_cycles,
            max_flights=battery_max_flights,
            purchase_date=battery_purchase_date,
            item_value=battery_purchase_price
        )
        global_session.add(self.battery)
        global_session.commit()
        self.close()
    

class CreateEquipmentDialog(Dialog):
    def __init__(self, parent=None):
        super(CreateEquipmentDialog, self).__init__(parent)
        self.setWindowTitle("Add Equipment")

        self.equipment = None # type: Equipment

        self.equipment_name_label = QtWidgets.QLabel("Name:")
        self.equipment_name_input = QtWidgets.QLineEdit()
        self.equipment_name_input.editingFinished.connect(lambda: utilities.clean_text_input(self.equipment_name_input))

        self.equipment_serial_number_label = QtWidgets.QLabel("Serial Number:")
        self.equipment_serial_number_input = QtWidgets.QLineEdit()
        self.equipment_serial_number_input.editingFinished.connect(lambda: utilities.clean_text_input(self.equipment_serial_number_input))
        self.generate_equipment_serial_number_button = QtWidgets.QPushButton("Generate")
        self.generate_equipment_serial_number_button.clicked.connect(self.generate_equipment_serial_number)
        self.generate_equipment_serial_number_button.setFixedWidth(75)

        self.equipment_type_label = QtWidgets.QLabel("Type:")
        self.equipment_type_combobox = QtWidgets.QComboBox()
        items = [item.name for item in global_session.query(EquipmentType).order_by(EquipmentType.name).all()]
        self.equipment_type_combobox.addItems(items)

        self.equipment_purchase_date_label = QtWidgets.QLabel("Purchase Date:")
        self.equipment_purchase_date_input = QtWidgets.QDateEdit()
        self.equipment_purchase_date_input.setDate(QtCore.QDate.currentDate())
        self.equipment_purchase_date_input.setCalendarPopup(True)

        self.equipment_purchase_price_label = QtWidgets.QLabel("Purchase Price:")
        self.equipment_purchase_price_input = QtWidgets.QDoubleSpinBox()
        self.equipment_purchase_price_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.equipment_purchase_price_input.setRange(0, 1000000)
        self.equipment_purchase_price_input.setValue(0)
        self.equipment_purchase_price_input.setPrefix("$ ")

        self.equipment_description_label = QtWidgets.QLabel("Description:")
        self.equipment_description_input = QtWidgets.QTextEdit()

        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save)

        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow(self.equipment_name_label, self.equipment_name_input)
        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addWidget(self.equipment_serial_number_input, stretch=1)
        h_layout.addWidget(self.generate_equipment_serial_number_button)
        form_layout.addRow(self.equipment_serial_number_label, h_layout)
        form_layout.addRow(self.equipment_type_label, self.equipment_type_combobox)
        form_layout.addRow(self.equipment_purchase_date_label, self.equipment_purchase_date_input)
        form_layout.addRow(self.equipment_purchase_price_label, self.equipment_purchase_price_input)
        form_layout.addRow(self.equipment_description_label, self.equipment_description_input)
        self.main_layout.addLayout(form_layout)
        self.main_layout.addWidget(self.save_button)

    def generate_serial_number(self) -> None:
        serial_number = generate_random_string(Equipment)
        self.equipment_serial_number_input.setText(serial_number)

    def serial_number_valid(self, serial_number: str) -> bool:
        x = global_session.query(Equipment).filter_by(serial_number=serial_number).first()
        if x is None: return True
        return False

    def validate_form(self) -> ValidationResult:
        validation_result = ValidationResult()

        if self.equipment_name_input.text() == "":
            validation_result.add_error("Equipment name is required.")
        if self.equipment_serial_number_input.text() == "":
            validation_result.add_error("Equipment serial number is required.")
        elif not self.serial_number_valid(self.equipment_serial_number_input.text()):
            validation_result.add_error("Equipment serial number already exists.")
        if self.equipment_type_combobox.currentText() == "":
            validation_result.add_error("Equipment type is required.")
        
        return validation_result

    def save(self) -> None:
        validation_result = self.validate_form()

        if not validation_result.is_valid:
            message_box = QtWidgets.QMessageBox()
            message_box.setWindowTitle("Error")
            message_box.setIcon(QtWidgets.QMessageBox.Warning)
            message_box.setText("There were errors in the form.")
            message_box.setInformativeText("\n".join(validation_result.messages))
            message_box.exec()
            return
        
        self.equipment = Equipment.create(
            name=self.equipment_name_input.text(),
            serial_number=self.equipment_serial_number_input.text(),
            type_=global_session.query(EquipmentType).filter_by(name=self.equipment_type_combobox.currentText()).first(),
            purchase_date=self.equipment_purchase_date_input.date().toPyDate(),
            item_value=self.equipment_purchase_price_input.value(),
            description=self.equipment_description_input.toPlainText()
        )
        self.close()


class CreateFlightControllerDialog(Dialog):
    def __init__(self, parent=None):
        super(CreateFlightControllerDialog, self).__init__(parent)
        self.setWindowTitle("Add Flight Controller")

        self.flight_controller = None # type: FlightController

        self.flight_controller_name_label = QtWidgets.QLabel("Name:")
        self.flight_controller_name_input = QtWidgets.QLineEdit()
        self.flight_controller_name_input.editingFinished.connect(lambda: utilities.clean_text_input(self.flight_controller_name_input))

        self.flight_controller_serial_number_label = QtWidgets.QLabel("Serial Number:")
        self.flight_controller_serial_number_input = QtWidgets.QLineEdit()
        self.flight_controller_serial_number_input.editingFinished.connect(lambda: utilities.clean_text_input(self.flight_controller_serial_number_input))
        self.generate_flight_controller_serial_number_button = QtWidgets.QPushButton("Generate")
        self.generate_flight_controller_serial_number_button.clicked.connect(self.generate_serial_number)
        self.generate_flight_controller_serial_number_button.setFixedWidth(75)

        self.flight_controller_purchase_date_label = QtWidgets.QLabel("Purchase Date:")
        self.flight_controller_purchase_date_input = QtWidgets.QDateEdit()
        self.flight_controller_purchase_date_input.setDate(QtCore.QDate.currentDate())
        self.flight_controller_purchase_date_input.setCalendarPopup(True)

        self.flight_controller_purchase_price_label = QtWidgets.QLabel("Purchase Price:")
        self.flight_controller_purchase_price_input = QtWidgets.QDoubleSpinBox()
        self.flight_controller_purchase_price_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.flight_controller_purchase_price_input.setRange(0, 1000000)
        self.flight_controller_purchase_price_input.setValue(0)
        self.flight_controller_purchase_price_input.setPrefix("$ ")

        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save)

        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow(self.flight_controller_name_label, self.flight_controller_name_input)
        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addWidget(self.flight_controller_serial_number_input, stretch=1)
        h_layout.addWidget(self.generate_flight_controller_serial_number_button)
        form_layout.addRow(self.flight_controller_serial_number_label, h_layout)
        form_layout.addRow(self.flight_controller_purchase_date_label, self.flight_controller_purchase_date_input)
        form_layout.addRow(self.flight_controller_purchase_price_label, self.flight_controller_purchase_price_input)
        self.main_layout.addLayout(form_layout)
        self.main_layout.addWidget(self.save_button)
    
    def generate_serial_number(self) -> None:
        serial_number = generate_random_string(FlightController)
        self.flight_controller_serial_number_input.setText(serial_number)
    
    def serial_number_valid(self, serial_number: str) -> bool:
        x = global_session.query(FlightController).filter_by(serial_number=serial_number).first()
        if x is None: return True
        return False

    def validate_form(self) -> ValidationResult:
        validation_result = ValidationResult()

        if self.flight_controller_name_input.text() == "":
            validation_result.add_error("Flight controller name is required.")
        if self.flight_controller_serial_number_input.text() == "":
            validation_result.add_error("Flight controller serial number is required.")
        elif not self.serial_number_valid(self.flight_controller_serial_number_input.text()):
            validation_result.add_error("Flight controller serial number already exists.")

        return validation_result

    def save(self) -> None:
        validation_result = self.validate_form()

        if not validation_result.is_valid:
            message_box = QtWidgets.QMessageBox()
            message_box.setWindowTitle("Error")
            message_box.setIcon(QtWidgets.QMessageBox.Warning)
            message_box.setText("There were errors in the form.")
            message_box.setInformativeText("\n".join(validation_result.messages))
            message_box.exec()
            return
        
        self.flight_controller = FlightController.create(
            name=self.flight_controller_name_input.text(),
            serial_number=self.flight_controller_serial_number_input.text(),
            purchase_date=self.flight_controller_purchase_date_input.date().toPyDate(),
            item_value=self.flight_controller_purchase_price_input.value()
        )
        self.close()


class SelectFlightEquipmentDialog(QtWidgets.QDialog):
    def __init__(self, flight: Flight, equipment: Equipment=None, parent=None):
        super(SelectFlightEquipmentDialog, self).__init__(parent)
        
        self.flight = flight
        self.equipment = equipment

        self.setWindowTitle("Add Equipment")
        if self.equipment:
            self.setWindowTitle("Select Equipment")
        # self.resize(400, 75)

        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)

        label = QtWidgets.QLabel("Select Equipment to add.")
        if self.equipment:
            label.setText("Select Equipment replacement.")
        self.main_layout.addWidget(label)
        label = QtWidgets.QLabel(f"Flight: {self.flight.name}")
        self.main_layout.addWidget(label)

        self.form_layout = QtWidgets.QFormLayout()
        self.main_layout.addLayout(self.form_layout)

        self.equipment_name_label = QtWidgets.QLabel("Equipment:")
        self.equipment_name_combobox = QtWidgets.QComboBox()

        equipment = global_session.query(Equipment).all() # type: list[Equipment]
        self.equipment_name_combobox.addItems([item.combobox_name for item in equipment])

        if self.equipment:
            self.equipment_name_combobox.setCurrentText(self.equipment.combobox_name)
        
        self.form_layout.addRow(self.equipment_name_label, self.equipment_name_combobox)
        self.save_button = QtWidgets.QPushButton("Add")
        if self.equipment:
            self.save_button.setText("Replace")
        self.main_layout.addWidget(self.save_button)
        self.save_button.clicked.connect(self.save)

    def save(self):
        value = self.equipment_name_combobox.currentText()
        new_equipment = Equipment.find_by_combobox_name(value)
        if self.equipment and self.equipment.id != new_equipment.id:
            self.flight.remove_equipment(self.equipment)
        self.flight.add_equipment(new_equipment)
        self.close()