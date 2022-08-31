from typing import Any, List, Optional
from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from PyQt5 import QtCore, QtGui, QtWidgets
from sqlalchemy.orm import Session
from dronelogbook import models
from . import utilities
from .customwidgets import CustomQTableWidget
from .config import THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT


@dataclass
class ValidationResult:
    is_valid: bool = True
    messages: list[str] = field(default_factory=list)

    def add_error(self, error_message: str) -> None:
        self.is_valid = False
        self.messages.append(error_message)
    
    def show_error(self) -> bool:
        """Shows validation errors to user if needed.
            Returns True if error shown."""
        if not self.is_valid:
            message_box = QtWidgets.QMessageBox()
            message_box.setWindowTitle("Validation Error")
            message_box.setIcon(QtWidgets.QMessageBox.Warning)
            message_box.setText("Please fix the errors below.")
            message_box.setInformativeText("\n".join(self.messages))
            message_box.exec()
            return True
        return False


class Dialog(ABC, QtWidgets.QDialog):
    """Base class for all dialogs."""

    def __init__(self, title: str, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setWindowTitle(title)
        self.setSizeGripEnabled(True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.setModal(True)

        self.main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.main_layout)
    
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        super().closeEvent(event)
    
    @abstractmethod
    def result(self) -> Any:
        """Used to retrieve result after dialog closed."""
        pass

    @abstractmethod
    def generate_serial_number(self) -> None:
        """Generate a serial number for the current dialog."""
        pass

    @abstractmethod
    def is_serial_number_valid(self, serial_number: str) -> bool:
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


class SelectBatteryDialog(Dialog):
    def __init__(self, session: Session, current_batteries: List[models.Battery]=None, usable_batteries: List[models.Battery]=None, parent: QtWidgets.QWidget = None):
        """Creates a battery select dialog. current_batteries and usable_batteries are used to
            limit battery selection.

        Args:
            current_batteries (List[models.Battery], optional): List of batteries currently in use. Defaults to None.
            usable_batteries (List[models.Battery], optional): List of all usable batteries. Defaults to None.
        """
        super().__init__(parent, title="Select Battery")
        self.session = session

        self.selected_battery = None # type: models.Battery
        self.current_batteries = current_batteries
        self.usable_batteries = usable_batteries
        batteries = self.session.query(models.Battery).all() # type: List[models.Battery]

        self.main_layout.addWidget(QtWidgets.QLabel("Select a battery."))
        self.form_layout = QtWidgets.QFormLayout()

        self.battery_combobox = QtWidgets.QComboBox()

        if self.current_batteries and self.usable_batteries:
            battery_combobox_items = [battery.combobox_name for battery in self.usable_batteries if battery not in self.current_batteries]
        else:
            battery_combobox_items = [battery.combobox_name for battery in batteries]

        self.battery_combobox.addItems(battery_combobox_items)

        self.form_layout.addRow(QtWidgets.QLabel("Battery:"), self.battery_combobox)
        self.main_layout.addLayout(self.form_layout)

        button_layout = QtWidgets.QHBoxLayout()
        select_button = QtWidgets.QPushButton("Select")
        select_button.clicked.connect(self.select_battery)
        select_button.clicked.connect(self.close)
        button_layout.addWidget(select_button)
        self.main_layout.addLayout(button_layout)

    def select_battery(self):
        self.selected_battery = models.Battery.find_by_combobox_name(self.session, self.battery_combobox.currentText())
        self.accepted()
        self.close()
    
    def result(self) -> Optional[models.Battery]:
        return self.selected_battery
    
    # def generate_serial_number(self) -> None:
    #     """Generate a serial number for the current dialog."""
    #     raise NotImplementedError(f"generate_serial_number not implimented yet.")

    # def is_serial_number_valid(self, serial_number: str) -> bool:
    #     """Check if the serial number is valid."""
    #     raise NotImplementedError(f"is_serial_number_valid not implimented yet.")
    
    # def validate_form(self) -> ValidationResult:
    #     """Validate user input for the current dialog."""
    #     raise NotImplementedError(f"validate_form not implimented yet.")
    
    # def save(self) -> None:
    #     """Save the current dialog object to database."""
    #     raise NotImplementedError(f"save not implimented yet.")


class CreateBatteryDialog(Dialog):
    def __init__(self, session: Session, parent: QtWidgets.QWidget = None):
        super().__init__(title="Create New Battery", parent=parent)

        self.battery = None # type: models.Battery
        self.session = session

        self.name_label = QtWidgets.QLabel("Name:")
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.editingFinished.connect(lambda: utilities.clean_text_input(self.name_input))
        
        self.serial_number_label = QtWidgets.QLabel("Serial Number:")
        self.serial_number_input = QtWidgets.QLineEdit()
        self.serial_number_input.editingFinished.connect(lambda: utilities.clean_text_input(self.serial_number_input))
        self.generate_serial_number_button = QtWidgets.QPushButton("Generate")
        self.generate_serial_number_button.clicked.connect(self.generate_serial_number)
        self.generate_serial_number_button.setFixedWidth(75)

        self.chemistry_label = QtWidgets.QLabel("Battery Chemistry:")
        self.chemistry_combobox = QtWidgets.QComboBox()
        battery_chemistries = self.session.query(models.BatteryChemistry).all() # type: List[models.BatteryChemistry]
        self.chemistry_combobox.addItems([battery_chemistry.name for battery_chemistry in battery_chemistries])

        self.capacity_label = QtWidgets.QLabel("Capacity:")
        self.capacity_input = QtWidgets.QSpinBox()
        self.capacity_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.capacity_input.setRange(0, 1000000)
        self.capacity_input.setValue(0)
        self.capacity_input.setSuffix(" mAh")

        self.cell_count_label = QtWidgets.QLabel("Cell Count:")
        self.cell_count_input = QtWidgets.QSpinBox()
        self.cell_count_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.cell_count_input.setRange(0, 100)
        self.cell_count_input.setValue(0)

        self.max_flight_time_label = QtWidgets.QLabel("Max Flight Time:")
        self.max_flight_time_input = QtWidgets.QSpinBox()
        self.max_flight_time_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.max_flight_time_input.setRange(0, 1000000)
        self.max_flight_time_input.setValue(models.Battery.max_flight_time.default.arg)
        self.max_flight_time_input.setSuffix(" minutes")

        self.max_charge_cycles_label = QtWidgets.QLabel("Max Charge Cycles:")
        self.max_charge_cycles_input = QtWidgets.QSpinBox()
        self.max_charge_cycles_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.max_charge_cycles_input.setRange(0, 1000000)
        self.max_charge_cycles_input.setValue(models.Battery.max_charge_cycles.default.arg)

        self.max_flights_label = QtWidgets.QLabel("Max Flights:")
        self.max_flights_input = QtWidgets.QSpinBox()
        self.max_flights_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.max_flights_input.setRange(0, 1000000)
        self.max_flights_input.setValue(models.Battery.max_flights.default.arg)

        self.purchase_date_label = QtWidgets.QLabel("Purchase Date:")
        self.purchase_date_input = QtWidgets.QDateEdit()
        self.purchase_date_input.setDate(QtCore.QDate.currentDate())
        self.purchase_date_input.setCalendarPopup(True)

        self.purchase_price_label = QtWidgets.QLabel("Purchase Price:")
        self.purchase_price_input = QtWidgets.QDoubleSpinBox()
        self.purchase_price_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.purchase_price_input.setRange(0, 1000000)
        self.purchase_price_input.setValue(0)
        self.purchase_price_input.setPrefix("$ ")

        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save)

        self.init_layout()

    def init_layout(self):
        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow(self.name_label, self.name_input)

        h_box = QtWidgets.QHBoxLayout()
        h_box.addWidget(self.serial_number_input, stretch=1)
        h_box.addWidget(self.generate_serial_number_button)

        form_layout.addRow(self.serial_number_label, h_box)
        form_layout.addRow(self.chemistry_label, self.chemistry_combobox)
        form_layout.addRow(self.capacity_label, self.capacity_input)
        form_layout.addRow(self.cell_count_label, self.cell_count_input)
        form_layout.addRow(self.max_flight_time_label, self.max_flight_time_input)
        form_layout.addRow(self.max_charge_cycles_label, self.max_charge_cycles_input)
        form_layout.addRow(self.max_flights_label, self.max_flights_input)
        form_layout.addRow(self.purchase_date_label, self.purchase_date_input)
        form_layout.addRow(self.purchase_price_label, self.purchase_price_input)

        self.main_layout.addLayout(form_layout)
        self.main_layout.addWidget(self.save_button)

    def generate_serial_number(self) -> None:
        serial_number = utilities.generate_random_string(models.Battery)
        self.serial_number_input.setText(serial_number)
    
    def is_serial_number_valid(self, serial_number: str) -> bool:
        return self.session.query(models.Battery).filter_by(serial_number=serial_number).first() is None
    
    def validate_form(self) -> ValidationResult:
        validation_result = ValidationResult()

        if self.name_input.text() == "":
            validation_result.add_error("Battery Name is required.")
        if self.serial_number_input.text() == "":
            validation_result.add_error("Battery Serial Number is required.")
        else:
            if not self.serial_number_valid(self.serial_number_input.text()):
                validation_result.add_error("Battery serial number already exists.")
        if self.chemistry_combobox.currentText() == "":
            validation_result.add_error("Battery chemistry is required.")
        return validation_result
        
    def save(self) -> None:
        validation_result = self.validate_form()

        if validation_result.show_error():
            return
        
        name = self.name_input.text()
        serial_number = self.serial_number_input.text()
        chemistry = self.chemistry_combobox.currentText()
        capacity = self.capacity_input.value()
        cell_count = self.cell_count_input.value()
        max_flight_time = self.max_flight_time_input.value()
        max_charge_cycles = self.max_charge_cycles_input.value()
        max_flights = self.max_flights_input.value()
        purchase_date = self.purchase_date_input.date().toPyDate()
        purchase_price = self.purchase_price_input.value()

        chemistry_object = self.session.query(models.BatteryChemistry).filter_by(name=chemistry).first()
        self.battery = models.Battery(
            name=name,
            serial_number=serial_number,
            chemistry_id=chemistry_object.id,
            capacity=capacity,
            cell_count=cell_count,
            max_flight_time=max_flight_time,
            max_charge_cycles=max_charge_cycles,
            max_flights=max_flights,
            purchase_date=purchase_date,
            price=purchase_price
        )
        self.session.add(self.battery)
        self.session.commit()
        self.accept()
        self.close()
    

class CreateEquipmentDialog(Dialog):
    def __init__(self, session: Session, parent=None):
        super().__init__(title="Add Equipment", parent=parent)

        self.equipment = None # type: models.Equipment
        self.session = session

        self.name_label = QtWidgets.QLabel("Name:")
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.editingFinished.connect(lambda: utilities.clean_text_input(self.name_input))

        self.serial_number_label = QtWidgets.QLabel("Serial Number:")
        self.serial_number_input = QtWidgets.QLineEdit()
        self.serial_number_input.editingFinished.connect(lambda: utilities.clean_text_input(self.serial_number_input))
        self.generate_equipment_serial_number_button = QtWidgets.QPushButton("Generate")
        self.generate_equipment_serial_number_button.clicked.connect(self.generate_equipment_serial_number)
        self.generate_equipment_serial_number_button.setFixedWidth(75)

        self.type_label = QtWidgets.QLabel("Type:")
        self.type_combobox = QtWidgets.QComboBox()
        items = [item.name for item in self.session.query(models.EquipmentType).order_by(models.EquipmentType.name).all()]
        self.type_combobox.addItems(items)

        self.purchase_date_label = QtWidgets.QLabel("Purchase Date:")
        self.purchase_date_input = QtWidgets.QDateEdit()
        self.purchase_date_input.setDate(QtCore.QDate.currentDate())
        self.purchase_date_input.setCalendarPopup(True)

        self.purchase_price_label = QtWidgets.QLabel("Purchase Price:")
        self.purchase_price_input = QtWidgets.QDoubleSpinBox()
        self.purchase_price_input.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.purchase_price_input.setRange(0, 1000000)
        self.purchase_price_input.setValue(0)
        self.purchase_price_input.setPrefix("$ ")

        self.description_label = QtWidgets.QLabel("Description:")
        self.description_input = QtWidgets.QTextEdit()

        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save)

        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow(self.name_label, self.name_input)
        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addWidget(self.serial_number_input, stretch=1)
        h_layout.addWidget(self.generate_equipment_serial_number_button)
        form_layout.addRow(self.serial_number_label, h_layout)
        form_layout.addRow(self.type_label, self.type_combobox)
        form_layout.addRow(self.purchase_date_label, self.purchase_date_input)
        form_layout.addRow(self.purchase_price_label, self.purchase_price_input)
        form_layout.addRow(self.description_label, self.description_input)
        self.main_layout.addLayout(form_layout)
        self.main_layout.addWidget(self.save_button)

    def generate_serial_number(self) -> None:
        serial_number = utilities.generate_random_string(models.Equipment)
        self.serial_number_input.setText(serial_number)

    def is_serial_number_valid(self, serial_number: str) -> bool:
        x = self.session.query(models.Equipment).filter_by(serial_number=serial_number).first()
        if x is None: return True
        return False

    def validate_form(self) -> ValidationResult:
        validation_result = ValidationResult()

        if self.name_input.text() == "":
            validation_result.add_error("Equipment name is required.")
        if self.serial_number_input.text() == "":
            validation_result.add_error("Equipment serial number is required.")
        elif not self.serial_number_valid(self.serial_number_input.text()):
            validation_result.add_error("Equipment serial number already exists.")
        if self.type_combobox.currentText() == "":
            validation_result.add_error("Equipment type is required.")
        
        return validation_result

    def save(self) -> None:
        validation_result = self.validate_form()

        if validation_result.show_error():
            return
        
        self.equipment = models.Equipment.create(
            name=self.name_input.text(),
            serial_number=self.serial_number_input.text(),
            type_=self.session.query(models.EquipmentType).filter_by(name=self.type_combobox.currentText()).first(),
            purchase_date=self.purchase_date_input.date().toPyDate(),
            price=self.purchase_price_input.value(),
            description=self.description_input.toPlainText()
        )
        self.session.add(self.equipment)
        self.session.commit()
        self.accept()
        self.close()


class CreateDroneDialog(Dialog):
    def __init__(self, session: Session, parent: QtWidgets.QWidget = None):
        super().__init__(title="Create Drone", parent=parent)
        self.session = session

        self.drone = None # type: models.Drone
        self.geometry = None # type: models.DroneGeometry
        self.batteries = [] # type: List[models.Battery]
        self.flight_controller = None # type: models.Equipment
        
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
        flight_controller_type = models.EquipmentType.find_by_name("Remote Controller")
        self.drone_flight_controller_combobox.addItems([flight_controller.combobox_name for flight_controller in models.Equipment.find_by_type(flight_controller_type)])
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
        self.drone_geometry_combobox.addItems([geometry.name for geometry in models.DroneGeometry.find_all()])
        self.drone_geometry_combobox.setCurrentIndex(1)
        self.drone_geometry_combobox.currentIndexChanged.connect(self.on_drone_geometry_combobox_changed)
        self.drone_geometry_image = QtWidgets.QLabel()

        self.drone_create_button = QtWidgets.QPushButton("Create Drone")
        self.drone_create_button.clicked.connect(self.add_drone)

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
        self.main_layout.addWidget(self.drone_create_button)

        self.drone_geometry_combobox.setCurrentIndex(0)
    
    def set_flight_controller(self, combobox_text: str) -> None:
        self.flight_controller = models.Equipment.find_by_combobox_name(self.session, combobox_text)

    def generate_serial_number(self) -> None:
        serial_number = utilities.generate_random_string(models.Drone)
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
        flight_controller = dialog.result()
        if flight_controller is None: return
        self.flight_controller = flight_controller

    def add_new_battery(self) -> None:
        drone_battery_dialog = CreateBatteryDialog(self)
        drone_battery_dialog.exec()
        battery = drone_battery_dialog.result()
        if battery is None: return
        if battery not in self.batteries:
            self.batteries.append(battery)
            self.reload_drone_batteries_table()
            self.drone_remove_battery_button.setEnabled(True)

    def add_battery(self) -> None:
        dialog = SelectBatteryDialog(self.session, current_batteries=self.batteries, parent=self)
        dialog.exec()
        battery = dialog.result()
        # TODO: Rework this.
        # if len(dialog.battery_combobox_items) == 1:
        #     self.drone_add_battery_button.setEnabled(False)

        if battery is None: return
        self.add_battery_to_drone(battery)

    def on_selected_remove_battery(self) -> None:
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

    def add_battery_to_drone(self, battery: models.Battery) -> None:
        if battery is None: return
        if battery not in self.batteries:
            self.batteries.append(battery)
            self.reload_drone_batteries_table()
            self.drone_remove_battery_button.setEnabled(True)
    
    def on_drone_geometry_combobox_changed(self, index: int) -> None:
        name = self.drone_geometry_combobox.itemText(index)
        self.geometry = models.DroneGeometry.find_by_name(name) # type: models.DroneGeometry
        if self.geometry is None: return
        image = self.geometry.image
        qimage = image.to_QImage()
        qimage = qimage.scaled(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT, QtCore.Qt.KeepAspectRatio) # Scale the image
        pixmap = QtGui.QPixmap.fromImage(qimage)
        self.drone_geometry_image.setPixmap(pixmap)
    
    def is_serial_number_valid(self, serial_number: str) -> bool:
        return self.session.query(models.Drone).filter_by(serial_number=serial_number).first() is None
    
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

        if not validation_result.show_error():
            return

        serial_number = self.drone_serial_number_input.text()
        flight_controller = self.flight_controller
        geometry = self.geometry
        batteries = self.batteries
        self.drone = models.Drone.create(
            serial_number=serial_number,
            flight_controller=flight_controller,
            geometry=geometry,
            batteries=batteries,
            name=self.drone_name_input.text()
        )
        self.accept()
        self.close()


class CreateFlightControllerDialog(Dialog):
    def __init__(self, session: Session, parent: QtWidgets.QWidget = None):
        super().__init__(title="Create Flight Controller", parent=parent)
        self.session = session

        self.flight_controller = None # type: models.Equipment

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
        serial_number = utilities.generate_random_string(models.FlightController)
        self.flight_controller_serial_number_input.setText(serial_number)
    
    def serial_number_valid(self, serial_number: str) -> bool:
        return self.session.query(models.FlightController).filter_by(serial_number=serial_number).first() is None

    def validate_form(self) -> ValidationResult:
        validation_result = ValidationResult()

        if self.flight_controller_name_input.text() == "":
            validation_result.add_error("Flight controller name is required.")
        if self.flight_controller_serial_number_input.text() == "":
            validation_result.add_error("Flight controller serial number is required.")
        elif not self.serial_number_valid(self.flight_controller_serial_number_input.text()):
            validation_result.add_error("Flight controller serial number already exists.")

        return validation_result
    
    def result(self) -> Optional[models.Equipment]:
        return self.flight_controller

    def save(self) -> None:
        validation_result = self.validate_form()

        if not validation_result.show_error():
            return
        
        self.flight_controller = models.Equipment.create(
            name=self.flight_controller_name_input.text(),
            serial_number=self.flight_controller_serial_number_input.text(),
            purchase_date=self.flight_controller_purchase_date_input.date().toPyDate(),
            price=self.flight_controller_purchase_price_input.value(),
            type_=models.EquipmentType.find_by_name(self.session, "Remote Controller")
        )
        self.accept()
        self.close()


class SelectFlightEquipmentDialog(Dialog):
    def __init__(self, session: Session, flight: models.Flight, equipment: models.Equipment=None, parent=None):
        super().__init__(title="Select Flight Equipment", parent=parent)
        self.session = session
        
        self.flight = flight
        self.equipment = equipment

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

        equipment = models.Equipment.find_all(self.session)
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
        new_equipment = models.Equipment.find_by_combobox_name(value)
        if self.equipment and self.equipment.id != new_equipment.id:
            self.flight.remove_equipment(self.equipment)
        self.flight.add_equipment(new_equipment)
        self.accept()
        self.close()