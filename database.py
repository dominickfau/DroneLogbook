from __future__ import annotations
from ast import Not
from dataclasses import dataclass
import datetime
import os
import enum
import string
import random
import base64
from typing import overload
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm.session import Session as session_type_hint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import LONGBLOB
from PyQt5.QtGui import QImage

from errors import *

# FILE_NAME = "dronelogbook.db"
# DATABASE_URL = f"sqlite:///{FILE_NAME}"
# if os.path.exists(FILE_NAME):
#     os.remove(FILE_NAME)

SCHEMA = "dronelogbook"
USER = "root"
PASSWORD = "Redpurple23"
HOST = "192.168.1.107"
PORT = "3306"
DATABASE_URL_WITHOUT_SCHEMA = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}"
DATABASE_URL = f"{DATABASE_URL_WITHOUT_SCHEMA}/{SCHEMA}"

IMAGE_FOLDER = os.path.join(os.path.dirname(__file__), "images")
DRONE_GEOMETRY_IMAGE_FOLDER = os.path.join(IMAGE_FOLDER, "drone_geometry")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
global_session = Session() # type: session_type_hint
Base = declarative_base()

import databasebackup

def generate_random_string(check_table, limit=13) -> str:
    string_ = ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=limit))
    while not check_random_sting(string_, check_table):
        string_ = ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=limit))
    return string_

def check_random_sting(string: str, table_name) -> bool:
    """Checks if the string is not in the table."""
    with Session() as session:
        try:
            x = session.query(table_name).filter_by(uuid=string).first()
        except InvalidRequestError:
            x = session.query(table_name).filter_by(serial_number=string).first()
        if x:
            return False
        return True


def backup_database(folder_path: str):
    databasebackup.create(engine, folder_path)


@dataclass
class Status:
    id: int
    name: str


@dataclass
class Location:
    latitude: float
    longitude: float
    address: str = None

    def __str__(self) -> str:
        string = f"Latitude: {self.latitude}, Longitude: {self.longitude}"
        if self.address:
            string = f"Address: {self.address}"
        return string



class Airworthyness(enum.Enum):
    Airworthy = "Airworthy"
    Maintenance = "Under Maintenance"
    Retired = "Retired"

    @classmethod
    def all(cls) -> list[str]:
        return [e.value for e in cls]


class EquipmentGroup(enum.Enum):
    Ground_Equipment = "Ground Equipment"
    """Used for equipment that will stay on the ground."""
    Airborne_Equipment = "Airborne Equipment"
    """Used for equipment that will attach to a drone."""

    @classmethod
    def all(cls) -> list[str]:
        return [e.value for e in cls]


class LegalRule(Base):
    """Represents a legal rule that applies to a flight."""
    __tablename__ = "legal_rules"

    Not_Required = "Not Required"
    Part_107 = "Part 107"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)

    @staticmethod
    def find_by_name(name: str) -> LegalRule:
        return global_session.query(LegalRule).filter_by(name=name).first()
    
    @staticmethod
    def create_defaults() -> None:
        data = [
            LegalRule(name=LegalRule.Not_Required),
            LegalRule(name=LegalRule.Part_107)
        ]

        for item in data:
            if not LegalRule.find_by_name(item.name):
                global_session.add(item)
        global_session.commit()


class EquipmentType(Base):
    """Represents a type of equipment."""
    __tablename__ = "equipment_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    group = Column(Enum(*EquipmentGroup.all()), nullable=False) # type: str

    @staticmethod
    def find_by_name(name: str) -> EquipmentType:
        return global_session.query(EquipmentType).filter_by(name=name).first()

    @staticmethod
    def create_defaults() -> None:
        data = [
            EquipmentType(name="Airframe", group=EquipmentGroup.Airborne_Equipment.value),
            EquipmentType(name="Anenometer", group=EquipmentGroup.Ground_Equipment.value),
            EquipmentType(name="Battery", group=EquipmentGroup.Airborne_Equipment.value),
            EquipmentType(name="Charger", group=EquipmentGroup.Ground_Equipment.value),
            EquipmentType(name="Camera", group=EquipmentGroup.Airborne_Equipment.value),
            EquipmentType(name="Cradle", group=EquipmentGroup.Ground_Equipment.value),
            EquipmentType(name="Drive (Disk, Flash, etc.)", group=EquipmentGroup.Ground_Equipment.value),
            EquipmentType(name="FPV Glasses", group=EquipmentGroup.Ground_Equipment.value),
            EquipmentType(name="GPS", group=EquipmentGroup.Ground_Equipment.value),
            EquipmentType(name="Lens", group=EquipmentGroup.Airborne_Equipment.value),
            EquipmentType(name="Light", group=EquipmentGroup.Airborne_Equipment.value),
            EquipmentType(name="Monitor", group=EquipmentGroup.Ground_Equipment.value),
            EquipmentType(name="Motor", group=EquipmentGroup.Airborne_Equipment.value),
            EquipmentType(name="Parachute", group=EquipmentGroup.Airborne_Equipment.value),
            EquipmentType(name="Phone / Tablet", group=EquipmentGroup.Ground_Equipment.value),
            EquipmentType(name="Power Supply", group=EquipmentGroup.Ground_Equipment.value),
            EquipmentType(name="Prop Guards", group=EquipmentGroup.Airborne_Equipment.value),
            EquipmentType(name="Propeller", group=EquipmentGroup.Airborne_Equipment.value),
            EquipmentType(name="Radio Receiver", group=EquipmentGroup.Ground_Equipment.value),
            EquipmentType(name="Radio Transmitter", group=EquipmentGroup.Ground_Equipment.value),
            EquipmentType(name="Range Extender", group=EquipmentGroup.Airborne_Equipment.value),
            EquipmentType(name="Laser Range Finder", group=EquipmentGroup.Airborne_Equipment.value),
            EquipmentType(name="Remote Controller", group=EquipmentGroup.Airborne_Equipment.value),
            EquipmentType(name="Sensor", group=EquipmentGroup.Airborne_Equipment.value),
            EquipmentType(name="Spreader", group=EquipmentGroup.Airborne_Equipment.value),
            EquipmentType(name="Telemetry Radio", group=EquipmentGroup.Airborne_Equipment.value),
            EquipmentType(name="Tripod", group=EquipmentGroup.Ground_Equipment.value),
            EquipmentType(name="Video Transmitter", group=EquipmentGroup.Airborne_Equipment.value),
            EquipmentType(name="Other Ground", group=EquipmentGroup.Ground_Equipment.value),
        ]
        for equipment in data:
            if not EquipmentType.find_by_name(equipment.name):
                global_session.add(equipment)
        global_session.commit()


class MaintenanceStatus(Base):
    __tablename__ = "maintenance_status"

    Scheduled = Status(id=10, name="Scheduled")
    In_Progress = Status(id=20, name="In Progress")
    Completed = Status(id=30, name="Completed")

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)

    @staticmethod
    def find_by_name(name: str) -> MaintenanceStatus:
        return global_session.query(MaintenanceStatus).filter_by(name=name).first()
    
    @staticmethod
    def create_defaults() -> None:
        data = [
            MaintenanceStatus.Scheduled,
            MaintenanceStatus.In_Progress,
            MaintenanceStatus.Completed,
        ]
        for status in data:
            if not MaintenanceStatus.find_by_name(status.name):
                global_session.add(MaintenanceStatus(id=status.id, name=status.name))
        global_session.commit()


class MaintenanceTaskStatus(Base):
    """Represents the status of a maintenance task."""
    __tablename__ = "maintenance_task_status"

    Open = Status(id=10, name="Open")
    Partial = Status(id=20, name="Partial")
    Done = Status(id=30, name="Done")

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)

    @staticmethod
    def find_by_name(name: str) -> MaintenanceTaskStatus:
        return global_session.query(MaintenanceTaskStatus).filter_by(name=name).first()
    
    @staticmethod
    def create_defaults() -> None:
        data = [
            MaintenanceTaskStatus.Open,
            MaintenanceTaskStatus.Partial,
            MaintenanceTaskStatus.Done,
        ]
        for status in data:
            if not MaintenanceTaskStatus.find_by_name(status.name):
                global_session.add(MaintenanceTaskStatus(id=status.id, name=status.name))
        global_session.commit()


class FlightOperationApproval(Base):
    """Represents the approval of a flight operation."""
    __tablename__ = "flight_operation_approval"

    Not_Required = "Not Required"
    Controlled_Airspace_Area = "Controlled Airspace Area Approval"
    Over_People = "Over People Approval"
    Parcel_Delivery = "Parcel Delivery Approval"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False, unique=True)
    description = Column(String(256), nullable=False)

    flight_operation_types = relationship("FlightOperationTypeToApproval", back_populates="flight_operation_approval") # type: list[FlightOperationTypeToApproval]

    @staticmethod
    def find_by_name(name: str) -> FlightOperationApproval:
        return global_session.query(FlightOperationApproval).filter_by(name=name).first()
    
    @staticmethod
    def create_defaults() -> None:
        data = [
            FlightOperationApproval(name=FlightOperationApproval.Not_Required, description="No approval required."),
            FlightOperationApproval(name=FlightOperationApproval.Controlled_Airspace_Area, description="Approval for flight operations that will be within controlled airspace."),
            FlightOperationApproval(name=FlightOperationApproval.Over_People, description="Approval for flight operations that will be over people."),
            FlightOperationApproval(name=FlightOperationApproval.Parcel_Delivery, description="Approval for flight operations that will be delivering parcels."),
        ]
        for approval in data:
            if not FlightOperationApproval.find_by_name(approval.name):
                global_session.add(approval)
        global_session.commit()


class FlightOperationTypeToApproval(Base):
    """Represents the relationship between a flight operation type and its approval."""
    __tablename__ = "flight_operation_type_to_approval"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flight_operation_type_id = Column(Integer, ForeignKey("flight_operation_type.id"), nullable=False)
    flight_operation_approval_id = Column(Integer, ForeignKey("flight_operation_approval.id"), nullable=False)
    required = Column(Boolean, nullable=False)

    flight_operation_type = relationship("FlightOperationType", back_populates="approvals") # type: list[FlightOperationType]
    flight_operation_approval = relationship("FlightOperationApproval", back_populates="flight_operation_types") # type: list[FlightOperationApproval]


class FlightOperationType(Base):
    """Represents the type of a flight operation."""
    __tablename__ = "flight_operation_type"

    VLOS_Manual = "VLOS Manual"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(256), nullable=False)

    approvals = relationship("FlightOperationTypeToApproval", back_populates="flight_operation_type") # type: list[FlightOperationTypeToApproval]
    
    @staticmethod
    def find_by_name(name: str) -> FlightOperationType:
        return global_session.query(FlightOperationType).filter_by(name=name).first()
    
    @staticmethod
    def create_defaults() -> None:
        data = [
            FlightOperationType(name=FlightOperationType.VLOS_Manual, description="Maintain manual VLOS for the duration of the flight."),
        ]
        for operation in data:
            if not FlightOperationType.find_by_name(operation.name):
                global_session.add(operation)
        global_session.commit()


class FlightType(Base):
    """Represents the type of a flight."""
    __tablename__ = "flight_type"

    Commercial_Agriculture = "Commercial - Agriculture"
    Commercial_Inspection = "Commercial - Inspection"
    Commercial_Mapping = "Commercial - Mapping"
    Commercial_Survey = "Commercial - Survey"
    Commercial_Photo_Video = "Commercial - Photo/Video"
    Commercial_Other = "Commercial - Other"
    Emergency = "Emergency"
    Hobby_Entertainment = "Hobby - Entertainment"
    Maintenance = "Maintenance"
    Mapping_HR = "Mapping - HR"
    Mapping_UHR = "Mapping - UHR"
    Photogrammetry = "Photogrammetry"
    Science = "Science"
    Search_Rescue = "Search & Rescue"
    Simulator = "Simulator"
    Situational_Awareness = "Situational Awareness"
    Spreading = "Spreading"
    Survaliance = "Survaliance"
    Test_Flight = "Test Flight"
    Training = "Training"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False, unique=True)
    description = Column(String(256), nullable=False)
    operation_type_id = Column(Integer, ForeignKey("flight_operation_type.id"), nullable=False, default=1)

    operation_type = relationship("FlightOperationType", foreign_keys=[operation_type_id]) # type: FlightOperationType

    @staticmethod
    def find_by_name(name: str) -> FlightType:
        return global_session.query(FlightType).filter_by(name=name).first()
    
    @staticmethod
    def create_defaults() -> None:
        data = [
            FlightType(name=FlightType.Commercial_Agriculture, description="Commercial - Agriculture"),
            FlightType(name=FlightType.Commercial_Inspection, description="Commercial - Inspection"),
            FlightType(name=FlightType.Commercial_Mapping, description="Commercial - Mapping"),
            FlightType(name=FlightType.Commercial_Survey, description="Commercial - Survey"),
            FlightType(name=FlightType.Commercial_Photo_Video, description="Commercial - Photo/Video"),
            FlightType(name=FlightType.Commercial_Other, description="Commercial - Other"),
            FlightType(name=FlightType.Emergency, description="Emergency"),
            FlightType(name=FlightType.Hobby_Entertainment, description="Hobby - Entertainment"),
            FlightType(name=FlightType.Maintenance, description="Maintenance"),
            FlightType(name=FlightType.Mapping_HR, description="Mapping - HR"),
            FlightType(name=FlightType.Mapping_UHR, description="Mapping - UHR"),
            FlightType(name=FlightType.Photogrammetry, description="Photogrammetry"),
            FlightType(name=FlightType.Science, description="Science"),
            FlightType(name=FlightType.Search_Rescue, description="Search & Rescue"),
            FlightType(name=FlightType.Simulator, description="Simulator"),
            FlightType(name=FlightType.Situational_Awareness, description="Situational Awareness"),
            FlightType(name=FlightType.Spreading, description="Spreading"),
            FlightType(name=FlightType.Survaliance, description="Survaliance"),
            FlightType(name=FlightType.Test_Flight, description="Test Flight"),
            FlightType(name=FlightType.Training, description="Training"),
        ]
        for type_ in data:
            if not FlightType.find_by_name(type_.name):
                global_session.add(type_)
        global_session.commit()


class FlightStatus(Base):
    """Represents the status of a flight."""
    __tablename__ = "flight_status"

    Entered = Status(10, "Entered")
    InProgress = Status(20, "In Prosess")
    Completed = Status(30, "Completed")

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)

    def __repr__(self):
        return f"<FlightStatus(name={self.name})>"
    
    @staticmethod
    def find_by_name(name: str) -> FlightStatus:
        """Finds a flight status by name."""
        return global_session.query(FlightStatus).filter(FlightStatus.name == name).first()
    
    @staticmethod
    def create_defaults() -> None:
        """Creates the default flight statuses."""
        data = [
            FlightStatus.Entered,
            FlightStatus.InProgress,
            FlightStatus.Completed
        ]
            
        for status in data:
            if not FlightStatus.find_by_name(status.name):
                global_session.add(FlightStatus(id=status.id, name=status.name))
        global_session.commit()


class FlightController(Base):
    """Represents a flight controller."""
    __tablename__ = "flight_controller"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date_created = Column(DateTime, default=datetime.datetime.now)
    date_modified = Column(DateTime, default=datetime.datetime.now)
    serial_number = Column(String(256), unique=True)
    name = Column(String(50))
    purchase_date = Column(DateTime, default=datetime.datetime.now)
    status = Column(Enum(*Airworthyness.all()), default=Airworthyness.Airworthy.name) # type: Airworthyness
    item_value = Column(Float, default=0.00)
    """Flight controller's value in US dollars."""
    last_flight_date = Column(DateTime)
    last_flight_duration = Column(Float)
    """Duration of the last flight in minutes."""
    
    drone = relationship("Drone", uselist=False, back_populates="flight_controller") # type: Drone

    @staticmethod
    def create(name: str, serial_number: str, purchase_date: datetime.datetime, item_value: float) -> FlightController:
        """Creates a new flight controller."""
        controller = FlightController(name=name, serial_number=serial_number, purchase_date=purchase_date, item_value=item_value)
        global_session.add(controller)
        global_session.commit()
        return controller

    @property
    def total_flight_time(self) -> float:
        """Returns the total flight time of the drone in minutes."""
        if not self.drone: return 0.00
        return sum(flight.duration for flight in self.drone.flights if flight.active)

    @property
    def total_flights(self) -> int:
        """Returns the total number of flights the drone has taken."""
        if not self.drone: return 0.00
        return len([flight for flight in self.drone.flights if flight.active])

    @property
    def combobox_name(self) -> str:
        return f"[{self.serial_number}] {self.name}"
    
    def set_attribute(self, column: Column, value) -> None:
        """Sets the value of a column in the database.

        Args:
            column (Column): The column to set.
            value: The value to set the column to.
        """
        setattr(self, column.name, value)
        self.date_modified = datetime.datetime.now()
        global_session.commit()
    
    @property
    def age(self) -> float:
        """Returns the age of the battery in years from the purchase date."""
        return round((datetime.datetime.now() - self.purchase_date).days / 365, 2) if self.purchase_date else 0

    @staticmethod
    def find_by_serial_number(serial_number: str) -> FlightController:
        """Finds a flight controller by serial number."""
        return global_session.query(FlightController).filter(FlightController.serial_number == serial_number).first()
    
    @staticmethod
    def find_by_combobox_name(combobox_name: str) -> FlightController:
        """Finds a flight controller by combobox name."""
        serial_number = combobox_name.split("]")[0].strip("[").strip()
        return FlightController.find_by_serial_number(serial_number)
    
    @staticmethod
    def find_all() -> list[FlightController]:
        """Finds all flight controllers."""
        return global_session.query(FlightController).all()
 
    def start_flight(self, flight: Flight):
        """Starts a flight."""
        # TODO: Implement this.
        pass

    def end_flight(self, flight: Flight) -> None:
        """Ends a flight."""

        if flight.drone.flight_controller_id != self.id:
            raise ValueError("The flight controller used for this flight does not match the flight controller of the drone.")

        self.last_flight_date = flight.date
        self.last_flight_duration = flight.duration
        global_session.commit()
    
    def delete(self) -> None:
        """Deletes the flight controller from the database."""
        if self.drone is not None:
            raise ValueError("Can not delete flight controller assigned to a drone.")
        global_session.delete(self)
        global_session.commit()


@dataclass
class ImageData:
    file_path: str
    file_name: str
    file_extension: str
    data: bytes


class Image(Base):
    """Represents an image."""
    __tablename__ = "image"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False, unique=True)
    data = Column(LONGBLOB, nullable=False)
    file_extention = Column(String(10), nullable=False)
    read_only = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<Image(name={self.name})>"
    
    def to_QImage(self) -> QImage:
        """Converts the image to a QImage."""
        return QImage.fromData(self.data, format=self.file_extention)
    
    @staticmethod
    def create_defaults() -> None:
        """Creates the default images."""
        for root, dirs, files in os.walk(DRONE_GEOMETRY_IMAGE_FOLDER):
            for file in files:
                image_data = Image.convert_to_bytes(os.path.join(root, file)) # type: ImageData
                image_data.file_name = image_data.file_name.replace("_", " ")
                if not Image.find_by_name(image_data.file_name):
                    image = Image(name=image_data.file_name, data=image_data.data, file_extention=image_data.file_extension, read_only=True)
                    global_session.add(image)
        global_session.commit()
    
    @staticmethod
    def find_by_name(name: str) -> Image:
        """Finds an image by name."""
        return global_session.query(Image).filter(Image.name == name).first()

    @staticmethod
    def convert_to_bytes(file_path: str) -> ImageData:
        """Converts a file path to bytes."""
        file_name, file_extension = os.path.basename(file_path).split(".")
        with open(file_path, "rb") as f:
            data = f.read()
        return ImageData(file_path=file_path, file_name=file_name, file_extension=file_extension, data=data)
    
    @overload
    @staticmethod
    def upload(name: str, data: bytes, file_extention: str) -> Image:
        """Uploads an image."""
        if Image.find_by_name(name):
            raise ImageExistsError("An image with this name already exists.")
        image = Image(name=name, data=data, file_extention=file_extention)
        global_session.add(image)
        global_session.commit()
        return image
    
    @overload
    @staticmethod
    def upload(image_data: ImageData) -> Image:
        """Uploads an image."""
        if Image.find_by_name(image_data.file_name):
            raise ImageExistsError("An image with this name already exists.")
        image = Image(name=image_data.file_name, data=image_data.data, file_extention=image_data.file_extension)
        global_session.add(image)
        global_session.commit()
        return image


class DroneGeometry(Base):
    """Represents the geometry of a drone."""
    __tablename__ = "drone_geometry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False, unique=True)
    description = Column(String(256), nullable=False)
    image_id = Column(Integer, ForeignKey("image.id"), nullable=False)
    number_of_propellers = Column(Integer, nullable=False)
    alternating_rotaion = Column(Boolean, nullable=False, default=False)
    """True if the propellers rotate in alternating directions, False if they rotate in the same direction."""
    trust_direction = Column(Enum("Vertical", "Horizontal"), nullable=False, default="Vertical")
    """The direction the propellers trust. Defaults to Vertical."""

    image = relationship("Image", uselist=False) # type: Image

    @staticmethod
    def find_by_name(name: str) -> DroneGeometry:
        """Finds a drone geometry by name."""
        return global_session.query(DroneGeometry).filter(DroneGeometry.name == name).first()
    
    @staticmethod
    def find_all() -> list[DroneGeometry]:
        """Finds all drone geometries."""
        return global_session.query(DroneGeometry).all()
    
    @staticmethod
    def create_defaults() -> None:
        """Creates the default drone geometries."""
        data = [
            DroneGeometry(name="Fixed Wing 1",
                          description="A fixed wing drone with one propeller on the front nose.",
                          image_id=Image.find_by_name("Fixed Wing 1").id,
                          number_of_propellers=1,trust_direction="Horizontal"
                         ),
            DroneGeometry(name="Fixed Wing 2",
                          description="A fixed wing drone with one propeller on the back.",
                          image_id=Image.find_by_name("Fixed Wing 2").id,
                          number_of_propellers=1,trust_direction="Horizontal"
                         ),
            DroneGeometry(name="Hexa Plus",
                          description="A drone with six propellers, starting from the front.",
                          image_id=Image.find_by_name("Hexa Plus").id,
                          number_of_propellers=6,
                          alternating_rotaion=True
                         ),
            DroneGeometry(name="Hexa X",
                          description="A drone with six propellers, starting from the front right.",
                          image_id=Image.find_by_name("Hexa X").id,
                          number_of_propellers=6,
                          alternating_rotaion=True
                         ),
            DroneGeometry(name="Octa Plus",
                          description="A drone with eight propellers, starting from the front.",
                          image_id=Image.find_by_name("Octa Plus").id,
                          number_of_propellers=8,
                          alternating_rotaion=True
                         ),
            DroneGeometry(name="Octa V",
                          description="A drone with eight propellers, a row on each side in the shape o a V.",
                          image_id=Image.find_by_name("Octa V").id,
                          number_of_propellers=8,
                          alternating_rotaion=True
                         ),
            DroneGeometry(name="Octa X",
                          description="A drone with eight propellers, starting from the front right.",
                          image_id=Image.find_by_name("Octa X").id,
                          number_of_propellers=8,
                          alternating_rotaion=True
                         ),
            DroneGeometry(name="Quad Plus",
                          description="A drone with four propellers, starting from the front.",
                          image_id=Image.find_by_name("Quad Plus").id,
                          number_of_propellers=4,
                          alternating_rotaion=True
                         ),
            DroneGeometry(name="Quad X",
                          description="A drone with four propellers, starting from the front right.",
                          image_id=Image.find_by_name("Quad X").id,
                          number_of_propellers=4,
                          alternating_rotaion=True
                         ),
            DroneGeometry(name="Single Coaxial",
                          description="A drone with two propellers on the top.",
                          image_id=Image.find_by_name("Single Coaxial").id,
                          number_of_propellers=2,
                          alternating_rotaion=True
                         ),
            DroneGeometry(name="Single Rotor",
                          description="A drone with one propeller on the top.",
                          image_id=Image.find_by_name("Single Rotor").id,
                          number_of_propellers=1,
                          alternating_rotaion=False
                         ),
            DroneGeometry(name="Tri",
                          description="A drone with three propellers, starting from the front right in the shape of a Y.",
                          image_id=Image.find_by_name("Tri").id,
                          number_of_propellers=3,
                          alternating_rotaion=False
                         ),
            DroneGeometry(name="VTOL 1",
                          description="A drone / air plane hybrid.",
                          image_id=Image.find_by_name("VTOL 1").id,
                          number_of_propellers=5,
                          alternating_rotaion=True,
                          trust_direction="Horizontal"
                         ),
            DroneGeometry(name="VTOL 2",
                          description="An air plane with 2 propellers on the wings.",
                          image_id=Image.find_by_name("VTOL 2").id,
                          number_of_propellers=2,
                          trust_direction="Vertical"
                         ),
            DroneGeometry(name="VTOL 3",
                          description="A drone / air plane hybrid, starting from the front right in the shape of a Y.",
                          image_id=Image.find_by_name("VTOL 3").id,
                          number_of_propellers=6,
                          alternating_rotaion=True
                         ),
            DroneGeometry(name="X8 Coaxial",
                          description="A drone with eight propellers, similar to a Quad Plus, but with popellers top and bottom.",
                          image_id=Image.find_by_name("X8 Coaxial").id,
                          number_of_propellers=8,
                          alternating_rotaion=True
                         ),
            DroneGeometry(name="Y6 Coaxial",
                          description="A drone with six propellers, similar to a Tri, but with popellers top and bottom.",
                          image_id=Image.find_by_name("Y6 Coaxial").id,
                          number_of_propellers=6,
                          alternating_rotaion=True
                         ),
        ]
        for item in data:
            if DroneGeometry.find_by_name(item.name):
                continue
            global_session.add(item)
        global_session.commit()



class Drone(Base):
    """Represents a drone."""
    __tablename__ = "drone"

    id = Column(Integer, primary_key=True, autoincrement=True)
    color = Column(String(25))
    brand = Column(String(50))
    date_created = Column(DateTime, default=datetime.datetime.now)
    date_modified = Column(DateTime, default=datetime.datetime.now)
    description = Column(String(256))
    flight_controller_id = Column(Integer, ForeignKey("flight_controller.id"), nullable=False)
    geometry_id = Column(Integer, ForeignKey("drone_geometry.id"), nullable=False)
    item_value = Column(Float, default=0.00)
    """Drone's value in US dollars."""
    legal_id = Column(String(256))
    max_payload_weight = Column(Float, default=0.00)
    """Maximum payload weight in kilograms."""
    max_service_interval = Column(Integer, nullable=False, default=10)
    """Maximum service interval in flight time hours."""
    max_speed = Column(Float, default=0.00)
    """Maximum speed of the drone in meters per second."""
    max_vertical_speed = Column(Float, default=0.00)
    """Maximum vertical speed of the drone in meters per second."""
    model = Column(String(50))
    name = Column(String(50))
    purchase_date = Column(DateTime, default=datetime.datetime.now)
    serial_number = Column(String(256), unique=True)
    status = Column(Enum(*Airworthyness.all()), default=Airworthyness.Airworthy.name) # type: Airworthyness
    """The airworthyness of the drone."""
    weight = Column(Float, default=0.00)
    """The drone's weight in kilograms."""

    batteries = relationship("BatteryToDrone", back_populates="drone") # type: list[BatteryToDrone]
    flight_controller = relationship("FlightController", back_populates="drone", uselist=False) # type: FlightController
    flights = relationship("Flight", back_populates="drone") # type: list[Flight]
    geometry = relationship("DroneGeometry", uselist=False) # type: DroneGeometry

    def set_attribute(self, column: Column, value) -> None:
        """Sets the value of a column in the database.

        Args:
            column (Column): The column to set.
            value: The value to set the column to.
        """
        setattr(self, column.name, value)
        self.date_modified = datetime.datetime.now()
        global_session.commit()

    @property
    def combobox_name(self) -> str:
        """Returns the name of the drone for use in a combobox."""
        return f"[{self.serial_number}] {self.name}"

    @property
    def total_flight_time(self) -> float:
        """Returns the total flight time of the drone in minutes."""
        return sum(flight.duration for flight in self.flights if flight.active)

    @property
    def total_flights(self) -> int:
        """Returns the total number of flights the drone has taken."""
        return len([flight for flight in self.flights if flight.active])

    @property
    def inventory_id(self) -> str:
        """Returns the inventory ID of the drone. Used for adding barcodes to the drone."""
        return self.serial_number
    
    def delete(self) -> None:
        """Deletes the drone from the database."""
        if self.flights:
            raise DeleteDroneError("Can not delete a drone that has flights.")

        for battery_to_drone in self.batteries:
            global_session.delete(battery_to_drone)
        global_session.commit()
        global_session.delete(self)
        global_session.commit()
    
    @staticmethod
    def create(serial_number: str, geometry: DroneGeometry, batteries: list[Battery], flight_controller: FlightController, name: str=None) -> Drone:
        """Creates a new drone.

        Args:
            serial_number (str): The serial number of the drone.
            geometry (DroneGeometry): The geometry of the drone.
            batteries (list[Battery]): The batteries of the drone.
            flight_controller (FlightController): The flight controller the drone is using.

        Returns:
            Drone: The newly created drone.
        """
        drone = Drone(
            serial_number=serial_number,
            geometry_id=geometry.id,
            flight_controller_id=flight_controller.id,
            name=name
            )
        global_session.add(drone)
        global_session.commit()
        drone.add_batteries(batteries)
        return drone
    
    @staticmethod
    def find_by_serial_number(serial_number: str) -> Drone:
        """Finds a drone by its serial number."""
        return global_session.query(Drone).filter(Drone.serial_number == serial_number).first()
    
    @staticmethod
    def find_by_combobox_name(combobox_name: str) -> Drone:
        """Finds a drone by its combobox name."""
        serial_number = combobox_name.split("]")[0].strip("[").strip()
        return Drone.find_by_serial_number(serial_number)
    
    def add_battery(self, battery: Battery) -> None:
        """Adds a battery to the drone. If the battery is already attached to the drone, it is ignored."""
        batteries = [battery_to_drone.battery for battery_to_drone in self.batteries]
        if battery not in batteries:
            battery_to_drone = BatteryToDrone(drone_id=self.id, battery_id=battery.id)
            global_session.add(battery_to_drone)
            global_session.commit()
        
    def add_batteries(self, batteries: list[Battery]) -> None:
        """Adds a list of batteries to the drone. If any of the batteries are already attached to the drone, they are ignored."""
        for battery in batteries:
            self.add_battery(battery)
    
    def remove_battery(self, battery: Battery) -> None:
        """Removes a battery from the drone. If the battery is not attached to the drone, it is ignored."""
        if len(self.batteries) == 1: raise BatteryRemoveError(f"Can not remove battery from drone {self.combobox_name}. Drone must have at least one battery.")
        batteries = [battery_to_drone.battery for battery_to_drone in self.batteries]
        if battery not in batteries: return
        for battery_to_drone in self.batteries:
            if battery_to_drone.battery != battery: continue
            global_session.delete(battery_to_drone)
            global_session.commit()
            break
    
    def remove_batteries(self, batteries: list[Battery]) -> None:
        """Removes a list of batteries from the drone. If any of the batteries are not attached to the drone, they are ignored."""
        for battery in batteries:
            self.remove_battery(battery)


class Weather(Base):
    """Represents a weather condition during a flight."""
    __tablename__ = "weather"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cloud_cover = Column(Float, nullable=False)
    """Cloud cover in percent."""
    date = Column(DateTime, default=datetime.datetime.now)
    date_modified = Column(DateTime, default=datetime.datetime.now)
    flight_id = Column(Integer, ForeignKey("flight.id"), nullable=False, unique=True)
    humidity = Column(Float, nullable=False)
    """Humidity in percent."""
    notes = Column(String(256))
    pressure = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    """The temperature in degrees Celsius."""
    wind_speed = Column(Float, nullable=False)
    """The wind speed in meters per second."""
    wind_direction = Column(Float, nullable=False)
    """The wind direction in degrees."""
    visibility = Column(Float, nullable=False)
    """The visibility in meters."""

    flight = relationship("Flight", back_populates="weather") # type: Flight

    def set_attribute(self, column: Column, value) -> None:
        """Sets the value of a column in the database.

        Args:
            column (Column): The column to set.
            value: The value to set the column to.
        """
        setattr(self, column.name, value)
        self.date_modified = datetime.datetime.now()
        global_session.commit()


class Flight(Base):
    """Represents a flight with a drone and any other items used."""
    __tablename__ = "flight"

    id = Column(Integer, primary_key=True, autoincrement=True)
    active = Column(Boolean, default=True, doc="Whether the flight is active or not. If the flight is not active, it will not be included in any statistics.")
    """Whether the flight is active or not. If the flight is not active, it will not be included in any statistics."""
    address = Column(String(256))
    battery_id = Column(Integer, ForeignKey("battery.id"))
    battery_notes = Column(String(256))
    date = Column(DateTime, default=datetime.datetime.now)
    distance_traveled = Column(Float, default=0.00)
    """The distance traveled in meters."""
    drone_id = Column(Integer, ForeignKey("drone.id"), nullable=False)
    duration = Column(Float, default=0.00)
    """The flight time in minutes."""
    encounter_with_law = Column(Boolean, default=False)
    external_case_id = Column(String(256), default="")
    in_flight_notes = Column(String(256))
    location_latitude = Column(Float)
    """The latitude of the flight's location."""
    location_longitude = Column(Float)
    """The longitude of the flight's location."""
    legal_rule_id = Column(Integer, ForeignKey("legal_rules.id"), nullable=False, default=1)
    legal_rule_details = Column(String(256), default="")
    max_agl_altitude = Column(Float, default=0.00)
    """The maximum altitude AGL in meters."""
    name = Column(String(256))
    night_flight = Column(Boolean, default=False)
    notes = Column(String(256))
    operation_type_id = Column(Integer, ForeignKey("flight_operation_type.id"), nullable=False, default=1)
    operation_approval_id = Column(Integer, ForeignKey("flight_operation_approval.id"), nullable=False, default=1)
    post_flight_notes = Column(String(256))
    status_id = Column(Integer, ForeignKey("flight_status.id"), nullable=False, default=FlightStatus.Entered.id)
    type_id = Column(Integer, ForeignKey("flight_type.id"), nullable=False)
    utm_authorization = Column(String(256))
    """The Unmanned Aircraft System Traffic Management (UTM or LAANC) of the flight."""
    uuid = Column(String(14), unique=True, default=lambda: generate_random_string(Flight))

    battery = relationship("Battery", back_populates="flights") # type: Battery
    crew_members = relationship("CrewMemberToFlight", back_populates="flight") # type: list[CrewMemberToFlight]
    drone = relationship("Drone", back_populates="flights") # type: Drone
    legal_rule = relationship("LegalRule", foreign_keys=[legal_rule_id]) # type: LegalRule
    operation_type = relationship("FlightOperationType", foreign_keys=[operation_type_id]) # type: FlightOperationType
    operation_approval = relationship("FlightOperationApproval", foreign_keys=[operation_approval_id]) # type: FlightOperationApproval
    status = relationship("FlightStatus", foreign_keys=[status_id]) # type: FlightStatus
    type_ = relationship("FlightType", foreign_keys=[type_id]) # type: FlightType
    used_equipment = relationship("EquipmentToFlight", back_populates="flight") # type: list[EquipmentToFlight]
    weather = relationship("Weather", back_populates="flight", uselist=False) # type: Weather

    def __repr__(self) -> str:
        return f'Flight "{self.inventory_id}", {self.date.strftime("%m/%d/%Y")}, {self.drone.name}'
    
    def set_attribute(self, column: Column, value) -> None:
        """Sets the value of a column in the database.

        Args:
            column (Column): The column to set.
            value: The value to set the column to.
        """
        setattr(self, column.name, value)
        self.date_modified = datetime.datetime.now()
        global_session.commit()
    
    @staticmethod
    def create(drone: Drone, type_: FlightType, crew: list[tuple[CrewMember, CrewMemberRole]]=None) -> Flight:
        """Creates a new flight."""
        flight = Flight(drone_id=drone.id, type_id=type_.id)
        global_session.add(flight)
        global_session.commit()
        flight.name = f"Flight {flight.date}"
        global_session.commit()
        if crew is not None:
            for member, role in crew:
                flight.add_crew_member(member, role)
        return flight
    
    def delete(self) -> None:
        """Deletes the flight from the database."""
        
        for crew_member_to_flight in self.crew_members:
            global_session.delete(crew_member_to_flight)
        
        for equipment_to_flight in self.used_equipment:
            global_session.delete(equipment_to_flight)
        
        if self.weather:
            global_session.delete(self.weather)
        
        global_session.commit()
        global_session.delete(self)
        global_session.commit()

    # @validates("battery_id")
    # def validate_battery_id(self, key: str, battery_id: int) -> int:
    #     """Checks if the battery is usable by the drone."""
    #     useable_battery_ids = [battery_to_drone.battery.id for battery_to_drone in self.drone.batteries]
    #     if battery_id not in useable_battery_ids:
    #         raise BatteryNotAssignedError("Could not add battery to flight. Battery is not assigned to the drone.")
    #     return battery_id

    @property
    def location(self) -> Location:
        """Returns the location of the flight."""
        return Location(self.location_latitude, self.location_longitude, address=self.address)

    @property
    def inventory_id(self) -> str:
        """Returns the inventory ID of the flight. Used for adding barcodes to the flight."""
        return self.uuid
    
    @property
    def total_equipment_weight(self) -> float:
        """Returns the total equipment weight in kilograms."""
        total = 0.00

        for equipment_to_flight in self.used_equipment:
            equipment = equipment_to_flight.equipment
            if equipment.type_.group == EquipmentGroup.Airborne_Equipment.value:
                total += equipment.weight
        return total
    
    @property
    def battery_weight(self) -> float:
        """Returns the battery weight in kilograms."""
        return self.battery.weight
    
    @property
    def total_crew_members(self) -> int:
        """Returns the total number of crew members."""
        return len(self.crew_members)
    
    @property
    def total_takeoff_weight(self) -> float:
        """Returns the total takeoff weight in kilograms."""
        return round(self.drone.weight + self.total_equipment_weight + self.battery_weight, 4)
    
    def add_equipment(self, equipment: Equipment) -> None:
        """Adds an equipment to the flight. If the equipment is already attached to the flight, it is ignored."""
        used_equipment = [equipment_to_flight.equipment for equipment_to_flight in self.used_equipment] # type: list[Equipment]
        if equipment not in used_equipment:
            equipment_to_flight = EquipmentToFlight(flight=self, equipment=equipment)
            self.used_equipment.append(equipment_to_flight)
            global_session.commit()
    
    def remove_equipment(self, equipment: Equipment) -> None:
        """Removes an equipment from the flight. If the equipment is not attached to the flight, it is ignored."""
        used_equipment = [equipment_to_flight.equipment for equipment_to_flight in self.used_equipment] # type: list[Equipment]
        if equipment in used_equipment:
            for equipment_to_flight in self.used_equipment:
                if equipment_to_flight.equipment == equipment:
                    global_session.delete(equipment_to_flight)
                    global_session.commit()
                    break
        
    def add_crew_member(self, crew_member: CrewMember, role: CrewMemberRole) -> None:
        """Adds a crew member to the flight. If the crew member is already attached to the flight, it is ignored."""
        crew_members = [crew_member_to_flight.crew_member for crew_member_to_flight in self.crew_members]
        if crew_member in crew_members: return

        # Check if the crew member can preform the role
        if not crew_member.can_preform_role(role):
            raise RoleNotAssignedError(f"Could not add crew member {crew_member.full_name} to flight. Missing role {role.name}.")

        crew_member_to_flight = CrewMemberToFlight(flight_id=self.id, crew_member_id=crew_member.id, role_id=role.id)
        global_session.add(crew_member_to_flight)
        global_session.commit()
    
    def remove_crew_member(self, crew_member: CrewMember) -> None:
        """Removes a crew member from the flight. If the crew member is not attached to the flight, it is ignored."""
        crew_members = [crew_member_to_flight.crew_member for crew_member_to_flight in self.crew_members]
        if crew_member not in crew_members: return
        for crew_member_to_flight in self.crew_members:
            if crew_member_to_flight.crew_member == crew_member:
                role = crew_member_to_flight.role
                if role.required_for_flight:
                    raise RoleRemovalError(f"Could not remove crew member {crew_member.full_name} from flight. Role {role.name} is required for the flight.")
                global_session.delete(crew_member_to_flight)
                global_session.commit()
                return
    
    def set_battery(self, battery: Battery) -> None:
        """Sets the battery used for this flight."""
        useable_battery_ids = [battery_to_drone.battery.id for battery_to_drone in self.drone.batteries]
        if battery.id not in useable_battery_ids:
            raise BatteryNotAssignedError(f"Could not add battery to flight. Battery {battery.serial_number} is not assigned to the drone.")

        self.battery_id = battery.id
        global_session.commit()
    
    def set_weather(self, weather: Weather) -> None:
        """Sets the weather for this flight."""
        self.weather = weather
        global_session.commit()
    
    def set_location(self, location: Location) -> None:
        """Sets the location of the flight."""
        self.location_latitude = location.latitude
        self.location_longitude = location.longitude
        self.address = location.address
        global_session.commit()
    
    def start(self) -> None:
        """Starts the flight."""

        if self.status_id >= FlightStatus.InProgress.id:
            raise FlightAlreadyStartedError("Can not restart a flight that has already started or finished.")

        if self.battery_id is None:
            raise BatteryNotAssignedError("Could not start flight. No battery assigned to flight.")
        
        if self.total_crew_members == 0:
            raise NoCrewMembersError("Could not start flight. No crew members linked to flight.")

        required_roles = global_session.query(CrewMemberRole).filter(CrewMemberRole.required_for_flight == True).all()
        current_roles = [crew_member_to_flight.role for crew_member_to_flight in self.crew_members]

        for role in required_roles:
            if role not in current_roles:
                raise MissingRequiredRoleError(f"Could not start flight. Missing required role {role.name}.")
        
        self.status_id = FlightStatus.InProgress.id
        global_session.commit()
        self.drone.flight_controller.start_flight(self)
    
    def end(self, duration: float) -> None:
        """Ends the flight.

        Args:
            duration (float): The flight time in minutes.
        """        
        self.duration = duration
        self.status_id = FlightStatus.Completed.id
        global_session.commit()
        self.drone.flight_controller.end_flight(self)


class EquipmentToFlight(Base):
    """Links equipment to a flight."""
    __tablename__ = "equipment_to_flight"

    flight_id = Column(Integer, ForeignKey("flight.id"), primary_key=True, nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), primary_key=True, nullable=False)

    flight = relationship("Flight", back_populates="used_equipment") # type: Flight
    equipment = relationship("Equipment") # type: Equipment


class BatteryToDrone(Base):
    """Links batteries to a drone."""
    __tablename__ = "battery_to_drone"

    battery_id = Column(Integer, ForeignKey("battery.id"), primary_key=True, nullable=False)
    drone_id = Column(Integer, ForeignKey("drone.id"), primary_key=True, nullable=False)

    battery = relationship("Battery") # type: Battery
    drone = relationship("Drone", back_populates="batteries") # type: Drone


class BatteryChemistry(Base):
    """Represents a battery chemistry."""
    __tablename__ = "battery_chemistry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(String(200), nullable=False)
    unrecoverable_low_cell_voltage = Column(Float, nullable=False)
    """The lowest cell voltage that is considered to be unrecoverable from."""
    nominal_cell_voltage = Column(Float, nullable=False)
    """The nominal cell voltage."""
    safe_min_cell_voltage = Column(Float, nullable=False)
    """Safe minimum cell voltage in volts."""
    max_cell_voltage = Column(Float, nullable=False)
    """Maximum cell voltage in volts."""
    min_temperature = Column(Float, nullable=False)
    """Minimum temperature in degrees Celsius."""
    max_temperature = Column(Float, nullable=False)
    """Maximum temperature in degrees Celsius."""
    max_charge_current = Column(Float, nullable=False)
    """Maximum charge current in amps."""
    max_discharge_current = Column(Float, nullable=False)
    """Maximum discharge current in amps."""
    esr = Column(Float)
    """Equivalent series resistance in ohms."""

    @property
    def combobox_name(self) -> str:
        """Returns the name of the battery chemistry in a combobox format."""
        return f"[{self.code}] - {self.name}"
    
    @staticmethod
    def create_defaults() -> None:
        """Creates the default battery chemistry."""
        data = [
            BatteryChemistry(
                name="Lithium Ion",
                code="Li-Ion",
                description="Lithium Ion battery chemistry.",
                unrecoverable_low_cell_voltage=3.0,
                nominal_cell_voltage=3.7,
                safe_min_cell_voltage=3.3,
                max_cell_voltage=4.2,
                min_temperature=20,
                max_temperature=40,
                max_charge_current=2.5,
                max_discharge_current=2.5,
                esr=0.5
            ),
            BatteryChemistry(
                name="Lithium Polymer",
                code="Li-Po",
                description="Lithium Polymer battery chemistry.",
                unrecoverable_low_cell_voltage=3.2,
                nominal_cell_voltage=3.7,
                safe_min_cell_voltage=3.3,
                max_cell_voltage=4.2,
                min_temperature=20,
                max_temperature=40,
                max_charge_current=2.5,
                max_discharge_current=2.5,
                esr=0.5
            ),
            BatteryChemistry(
                name="Nickel Cadmium",
                code="NiCd",
                description="Nickel Cadmium battery chemistry.",
                unrecoverable_low_cell_voltage=3.2,
                nominal_cell_voltage=3.7,
                safe_min_cell_voltage=3.3,
                max_cell_voltage=4.2,
                min_temperature=20,
                max_temperature=40,
                max_charge_current=2.5,
                max_discharge_current=2.5,
                esr=0.5
            ),
            BatteryChemistry(
                name="Nickel Metal Hydride",
                code="NiMH",
                description="Nickel Metal Hydride battery chemistry.",
                unrecoverable_low_cell_voltage=3.2,
                nominal_cell_voltage=3.7,
                safe_min_cell_voltage=3.3,
                max_cell_voltage=4.2,
                min_temperature=20,
                max_temperature=40,
                max_charge_current=2.5,
                max_discharge_current=2.5,
                esr=0.5
            ),
        ]
        for item in data:
            if not BatteryChemistry.find_by_code(item.code):
                global_session.add(item)
        global_session.commit()
    
    @staticmethod
    def find_by_code(code: str) -> BatteryChemistry:
        """Finds a battery chemistry by code.

        Args:
            code (str): The code of the battery chemistry.

        Returns:
            BatteryChemistry: The battery chemistry.
        """
        return global_session.query(BatteryChemistry).filter(BatteryChemistry.code == code).first()
    
    @staticmethod
    def find_by_name(name: str) -> BatteryChemistry:
        """Finds a battery chemistry by name.

        Args:
            name (str): The name of the battery chemistry.

        Returns:
            BatteryChemistry: The battery chemistry.
        """
        return global_session.query(BatteryChemistry).filter(BatteryChemistry.name == name).first()
    
    @staticmethod
    def find_by_combobox_name(combobox_name: str) -> BatteryChemistry:
        """Finds a battery chemistry by combobox name.

        Args:
            combobox_name (str): The combobox name of the battery chemistry.

        Returns:
            BatteryChemistry: The battery chemistry.
        """
        code = combobox_name.split("]")[0].strip("[").strip()
        return BatteryChemistry.find_by_code(code)


class Battery(Base):
    """Represents a battery."""
    __tablename__ = "battery"

    id = Column(Integer, primary_key=True, autoincrement=True)
    capacity = Column(Integer, nullable=False)
    """The battery's capacity in mAh."""
    cell_count = Column(Integer, nullable=False)
    """The number of cells in the battery."""
    charge_cycle_count = Column(Integer, default=0)
    """The number of times the battery has been charged."""
    chemistry_id = Column(Integer, ForeignKey("battery_chemistry.id"), nullable=False, default=1)
    date_created = Column(DateTime, default=datetime.datetime.now)
    date_modified = Column(DateTime, default=datetime.datetime.now)
    notes = Column(String(256))
    item_value = Column(Float, default=0.00)
    """The value of the battery in US dollars."""
    max_flight_time = Column(Integer, default=30)
    """The maximum flight time in minutes per charge."""
    name = Column(String(50), nullable=False)
    max_charge_cycles = Column(Integer, default=200)
    """The max number of charge cycles the battery can last."""
    max_flights = Column(Integer, default=1000)
    """The max number of flights the battery can last."""
    purchase_date = Column(DateTime, default=datetime.datetime.now)
    serial_number = Column(String(256), unique=True, nullable=False)
    status = Column(Enum(*Airworthyness.all()), default=Airworthyness.Airworthy.name, nullable=False) # type: Airworthyness
    """The airworthiness status of the battery."""
    weight = Column(Float, default=0.00)
    """The battery's weight in kilograms."""

    chemistry = relationship("BatteryChemistry", uselist=False) # type: BatteryChemistry
    flights = relationship("Flight", back_populates="battery") # type: list[Flight]

    def __str__(self) -> str:
        return f'Battery "{self.inventory_id}", {self.capacity}mAh, {self.cell_count} cells'
    
    def set_attribute(self, column: Column, value) -> None:
        """Sets the value of a column in the database.

        Args:
            column (Column): The column to set.
            value: The value to set the column to.
        """
        setattr(self, column.name, value)
        self.date_modified = datetime.datetime.now()
        global_session.commit()

    @property
    def combobox_name(self) -> str:
        """Returns the name of the battery in a combobox format."""
        return f"[{self.serial_number}] - {self.name}"

    @property
    def inventory_id(self) -> str:
        """Returns the inventory ID of the battery. Used for adding barcodes to the battery."""
        return self.serial_number
    
    @property
    def age(self) -> float:
        """Returns the age of the battery in years from the purchase date."""
        return round((datetime.datetime.now() - self.purchase_date).days / 365, 2) if self.purchase_date else 0
    
    @property
    def total_flight_time(self) -> float:
        """Returns the flight time of the battery in minutes."""
        return sum(flight.duration for flight in self.flights if flight.active)
    
    @property
    def total_flights(self) -> int:
        """Returns the total number of flights the battery has been used in."""
        return len([flight for flight in self.flights if flight.active])
    
    @property
    def remaining_charge_cycles(self) -> int:
        """Returns the remaining number of charge cycles the battery can last."""
        return self.max_charge_cycles - self.charge_cycle_count
    
    @property
    def remaining_flights(self) -> int:
        """Returns the remaining number of flights the battery can last."""
        return self.max_flights - self.total_flights
    
    @property
    def min_pack_voltage(self) -> float:
        """Returns the minimum pack voltage of the battery in volts."""
        return self.chemistry.safe_min_cell_voltage * self.cell_count
    
    @property
    def nominal_pack_voltage(self) -> float:
        """Returns the nominal pack voltage of the battery."""
        return self.chemistry.nominal_cell_voltage * self.cell_count
    
    @property
    def max_pack_voltage(self) -> float:
        """Returns the max pack voltage of the battery."""
        return self.chemistry.max_cell_voltage * self.cell_count
    
    @property
    def remaining_charge_cycles_percent(self) -> float:
        """Returns the percentage of charge cycles remaining."""
        return self.remaining_charge_cycles / self.max_charge_cycles * 100
    
    @property
    def remaining_flights_percent(self) -> float:
        """Returns the percentage of flights remaining."""
        return self.remaining_flights / self.max_flights * 100
    
    def delete(self) -> None:
        """Deletes the battery from the database."""
        if self.total_flights > 0:
            raise DeleteBatteryError("Cannot delete battery with flights.")
        
        drones = global_session.query(BatteryToDrone).filter(BatteryToDrone.battery_id == self.id).all()
        if drones:
            raise DeleteBatteryError("Cannot delete battery linked to drones.")
        
        global_session.delete(self)
        global_session.commit()

    def add_charge_cycle(self):
        """Adds a charge cycle to the battery."""
        self.charge_cycle_count += 1
        global_session.commit()
    
    @staticmethod
    def find_all() -> list[Battery]:
        """Finds all batteries."""
        return global_session.query(Battery).all()
    
    @staticmethod
    def find_by_serial_number(serial_number: str) -> Battery:
        """Finds a battery by its serial number."""
        return global_session.query(Battery).filter_by(serial_number=serial_number).first()
    
    @staticmethod
    def find_by_combobox_name(combobox_name: str) -> Battery:
        """Finds a battery by its combobox name."""
        serial_number = combobox_name.split("]")[0].strip("[").strip()
        return Battery.find_by_serial_number(serial_number)


class Equipment(Base):
    """Represents an item of equipment."""
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    description = Column(String(256))
    date_created = Column(DateTime, default=datetime.datetime.now)
    date_modified = Column(DateTime, default=datetime.datetime.now)
    serial_number = Column(String(256), unique=True, nullable=False)
    purchase_date = Column(DateTime, default=datetime.datetime.now)
    status = Column(Enum(*Airworthyness.all()), default=Airworthyness.Airworthy.name) # type: Airworthyness
    """The airworthiness status of the equipment."""
    weight = Column(Float, default=0.00)
    """The equipment's weight in kilograms."""
    type_id = Column(Integer, ForeignKey("equipment_type.id"), nullable=False)
    item_value = Column(Float, default=0.00)
    """The value of the equipment in US dollars."""

    type_ = relationship("EquipmentType") # type: EquipmentType
    flights = relationship("EquipmentToFlight", back_populates="equipment") # type: list[EquipmentToFlight]

    def set_attribute(self, column: Column, value) -> None:
        """Sets the value of a column in the database.

        Args:
            column (Column): The column to set.
            value: The value to set the column to.
        """
        setattr(self, column.name, value)
        self.date_modified = datetime.datetime.now()
        global_session.commit()

    @property
    def combobox_name(self) -> str:
        """Returns the name of the equipment in a combobox format."""
        return f"[{self.serial_number}] - {self.name}"

    @property
    def inventory_id(self) -> str:
        """Returns the inventory ID of the equipment. Used for adding barcodes to the equipment."""
        return self.serial_number
    
    @property
    def total_flights(self) -> int:
        """Returns the total number of flights the equipment has been used in."""
        return len([flight for flight in self.flights if flight.active])
    
    @property
    def age(self) -> float:
        """Returns the age of the equipment in years from the purchase date."""
        return round((datetime.datetime.now() - self.purchase_date).days / 365, 2) if self.purchase_date else 0
    
    @property
    def total_flight_time(self) -> float:
        """Returns the flight time of the equipment in minutes."""
        return sum(equipment_to_flight.flight.duration for equipment_to_flight in self.flights if equipment_to_flight.flight.active)
    
    @staticmethod
    def find_by_serial_number(serial_number: str) -> Equipment:
        """Finds an equipment by its serial number."""
        return global_session.query(Equipment).filter_by(serial_number=serial_number).first()
    
    @staticmethod
    def find_by_combobox_name(combobox_name: str) -> Equipment:
        """Finds a equipment by its combobox name."""
        serial_number = combobox_name.split("]")[0].strip("[").strip()
        return Equipment.find_by_serial_number(serial_number)
    
    @staticmethod
    def create(name: str, serial_number: str, purchase_date: datetime.datetime, item_value: float, type_: EquipmentType, description: str="") -> Equipment:
        """Creates a new equipment.

        Args:
            name (str): The name of the equipment.
            serial_number (str): The serial number of the equipment.
            purchase_date (datetime.datetime): The date the equipment was purchased.
            item_value (float): The value of the equipment in US dollars.
            type_ (EquipmentType): The type of the equipment.
            description (str): The description of the equipment.
        """
        equipment = Equipment(
            name=name,
            serial_number=serial_number,
            purchase_date=purchase_date,
            item_value=item_value,
            type_id=type_.id,
            description=description
            )

        global_session.add(equipment)
        global_session.commit()
        return equipment
    
    def delete(self) -> None:
        """Deletes the equipment from the database."""
        if self.total_flights > 0:
            raise DeleteEquipmentError("Cannot delete equipment with flights.")
        
        equipment = global_session.query(EquipmentToFlight).filter(EquipmentToFlight.equipment_id == self.id).all()
        if equipment:
            raise DeleteEquipmentError("Cannot delete equipment linked to flights.")
        
        global_session.delete(self)
        global_session.commit()


class DroneMaintenance(Base):
    """Represents a maintenance event for a drone."""
    __tablename__ = "drone_maintenance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cost = Column(Float, default=0.00)
    """The cost of the maintenance in US dollars."""
    date_scheduled = Column(DateTime, default=datetime.datetime.now)
    """The date the maintenance was scheduled or preformed."""
    name = Column(String(50), nullable=False)
    notes = Column(String(256), nullable=False)
    drone_id = Column(Integer, ForeignKey("drone.id"))
    status_id = Column(Integer, ForeignKey("maintenance_status.id"), default=10)

    drone = relationship("Drone") # type: Drone
    status = relationship("MaintenanceStatus") # type: MaintenanceStatus
    tasks = relationship("DroneMaintenanceTask", back_populates="maintenance") # type: list[DroneMaintenanceTask]


class DroneMaintenanceTask(Base):
    """Represents a task for a drone maintenance event."""
    __tablename__ = "drone_maintenance_task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String(256))
    drone_maintenance_id = Column(Integer, ForeignKey("drone_maintenance.id"))
    crew_member_id = Column(Integer, ForeignKey("crew_member.id"))
    status_id = Column(Integer, ForeignKey("maintenance_task_status.id"), default=10)
    part_number = Column(String(50))
    part_description = Column(String(256))
    part_replased = Column(Boolean, default=False)
    """Whether or not the part was replaced."""
    new_part_serial_number = Column(String(256))
    """The serial number of the new part. Only used if the part was replaced."""

    crew_member = relationship("CrewMember") # type: CrewMember
    """The crew member who performed the task."""
    maintenance = relationship("DroneMaintenance", back_populates="tasks") # type: DroneMaintenance
    """The maintenance event this task is associated with."""
    status = relationship("MaintenanceTaskStatus", foreign_keys=[status_id]) # type: MaintenanceTaskStatus
    

class EquipmentBatteryMaintenance(Base):
    """Represents a maintenance event for a battery or equipment."""
    __tablename__ = "equipment_battery_maintenance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cost = Column(Float, default=0.00)
    """The cost of the maintenance in US dollars."""
    date_scheduled = Column(DateTime, default=datetime.datetime.now)
    """The date the maintenance was scheduled or preformed."""
    name = Column(String(50), nullable=False)
    notes = Column(String(256))
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    status_id = Column(Integer, ForeignKey("maintenance_status.id"), default=10)

    equipment = relationship("Equipment") # type: Equipment
    status = relationship("MaintenanceStatus") # type: MaintenanceStatus


class DroneScheduledTask(Base):
    """Represents a scheduled task for a drone."""
    __tablename__ = "drone_scheduled_task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    interval = Column(Integer)
    """The interval in flight hours to preform the task again."""
    maintenance_task_id = Column(Integer, ForeignKey("drone_maintenance_task.id"), unique=True)
    used = Column(Boolean, default=False)
    """Whether or not the task has been used."""

    drone_maintenance_task = relationship("DroneMaintenanceTask") # type: DroneMaintenanceTask

    @staticmethod
    def schedule_recurring_tasks(task: DroneMaintenanceTask, interval: int) -> DroneScheduledTask:
        """Schedules a recurring task for a drone maintenance task.

        Args:
            task (DroneMaintenanceTask): The task to schedule.
            interval (int): The interval in flight hours to preform the task again.

        Raises:
            ScheduledTaskExistsError: If the task is already scheduled.

        Returns:
            DroneScheduledTask: The scheduled task.
        """
        result = global_session.query(DroneScheduledTask).filter(DroneScheduledTask.maintenance_task_id == task.id).first()

        if result: raise ScheduledTaskExistsError(f"A scheduled task for task {task.id} already exists.")

        new_task = DroneScheduledTask(maintenance_task_id=task.id, interval=interval)
        global_session.add(new_task)
        global_session.commit()
        
        return new_task


class CrewMemberRole(Base):
    """Represents a role a crew member can have."""

    Approved_Delegate = "Approved Delegate"
    """A crew member who is approved to fly a drone."""
    Ground_Support = "Ground Support"
    """A crew member who is responsible for ground support."""
    Maintenance_Controller = "Maintenance Controller"
    """A crew member who is responsible for maintenance."""
    Observer = "Observer"
    """A crew member who is responsible for keeping VLOS of the drone during flight."""
    Payload_Controller = "Payload Controller"
    """A crew member who is responsible for payload control."""
    Pilot = "Pilot"
    """A crew member who is responsible for flying the drone."""
    Student = "Student"
    """A crew member who is a student learning."""
    Remote_Pilot_In_Command = "Remote Pilot In Command (Remote PIC)"
    """A crew member who holds a remote pilot certificate with an sUAS rating and has the final authority and responsibility for the operation and safety of an sUAS operation conducted under part 107."""

    __tablename__ = "crew_member_role"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(256))
    required_for_flight = Column(Boolean, default=False)

    @staticmethod
    def create_defaults() -> None:
        """Creates the default roles."""
        data = [
            CrewMemberRole(name=CrewMemberRole.Approved_Delegate, description="A crew member who is approved to fly a drone."),
            CrewMemberRole(name=CrewMemberRole.Ground_Support, description="A crew member who is responsible for ground support."),
            CrewMemberRole(name=CrewMemberRole.Maintenance_Controller, description="A crew member who is responsible for maintenance."),
            CrewMemberRole(name=CrewMemberRole.Observer, description="A crew member who is responsible for keeping VLOS of the drone during flight."),
            CrewMemberRole(name=CrewMemberRole.Payload_Controller, description="A crew member who is responsible for payload control."),
            CrewMemberRole(name=CrewMemberRole.Pilot, description="A crew member who is responsible for flying the drone."),
            CrewMemberRole(name=CrewMemberRole.Student, description="A crew member who is a student learning."),
            CrewMemberRole(name=CrewMemberRole.Remote_Pilot_In_Command, required_for_flight=True, description="A crew member who holds a remote pilot certificate with an sUAS rating and has the final authority and responsibility for the operation and safety of an sUAS operation conducted under part 107.")
        ]

        for role in data:
            x = global_session.query(CrewMemberRole).filter(CrewMemberRole.name == role.name).first()
            if x: continue
            global_session.add(role)
        global_session.commit()

    
    @staticmethod
    def find_by_name(name: str) -> CrewMemberRole:
        """Finds a role by name.

        Args:
            name (str): The name of the role.

        Returns:
            CrewMemberRole: The role or None if it does not exist.
        """
        return global_session.query(CrewMemberRole).filter(CrewMemberRole.name == name).first()


class CrewMemberToRole(Base):
    """Represents a mapping between a crew member and a role they can preform."""
    __tablename__ = "crew_member_to_role"

    crew_member_id = Column(Integer, ForeignKey("crew_member.id"), primary_key=True, nullable=False)
    role_id = Column(Integer, ForeignKey("crew_member_role.id"), primary_key=True, nullable=False)

    crew_member = relationship("CrewMember", back_populates="roles") # type: CrewMember
    role = relationship("CrewMemberRole") # type: CrewMemberRole


class CrewMemberToFlight(Base):
    """Represents a mapping between a crew member and a flight."""
    __tablename__ = "crew_member_to_flight"

    crew_member_id = Column(Integer, ForeignKey("crew_member.id"), primary_key=True, nullable=False)
    flight_id = Column(Integer, ForeignKey("flight.id"), primary_key=True, nullable=False)
    role_id = Column(Integer, ForeignKey("crew_member_role.id"), primary_key=True, nullable=False)

    crew_member = relationship("CrewMember", back_populates="flights") # type: CrewMember
    flight = relationship("Flight", back_populates="crew_members") # type: Flight
    role = relationship("CrewMemberRole") # type: CrewMemberRole


class DocumentType(Base):
    """Represents a document type."""
    __tablename__ = "document_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(256))

    @staticmethod
    def create_defaults():
        """Creates the default document types."""
        data = [
            DocumentType(name="Pilot Registration", description="A document that shows the pilot's registration."),
            DocumentType(name="Pilot License", description="A document that shows the pilot's license."),
            DocumentType(name="Remote Pilot Certificate", description="A document that shows the remote pilot's certificate."),
            DocumentType(name="Medical Certificate", description="A document that shows the medical certificate."),
            DocumentType(name="Other", description="A document that shows other documents.")
        ]

        for document_type in data:
            x = global_session.query(DocumentType).filter(DocumentType.name == document_type.name).first()
            if x: continue
            global_session.add(document_type)
        global_session.commit()
    
    @staticmethod
    def find_by_name(name: str) -> DocumentType:
        """Finds a document type by name.

        Args:
            name (str): The name of the document type.

        Returns:
            DocumentType: The document type.
        """
        return global_session.query(DocumentType).filter(DocumentType.name == name).first()


class Document(Base):
    """Represents a document."""
    __tablename__ = "document"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date_uploaded = Column(DateTime, default=datetime.datetime.now)
    """The date the document was uploaded."""
    date_modified = Column(DateTime, default=datetime.datetime.now)
    """The date the document was last modified."""
    name = Column(String(50), nullable=False, unique=True)
    """The name of the document."""
    description = Column(String(256))
    """The description of the document."""
    file_extension = Column(String(10), nullable=False)
    """The file extension of the document."""
    file_data = Column(LONGBLOB, nullable=False) # type: bytes
    """The file data of the document. As represented by a base64 encoded bytes object."""
    creator_id = Column(Integer, ForeignKey("crew_member.id"))
    """The crew member who uploaded the document."""
    type_id = Column(Integer, ForeignKey("document_type.id"), nullable=False)


    creator = relationship("CrewMember") # type: CrewMember
    type_ = relationship("DocumentType") # type: DocumentType

    @staticmethod
    def convert_to_bytes(file_path: str) -> bytes:
        """Converts a file to bytes.

        Args:
            file_path (str): The path to the file.

        Returns:
            bytes: The file data.
        """
        with open(file_path, "rb") as file:
            return base64.b64encode(file.read())

    @staticmethod
    def upload(name: str, file_path: str, document_type: DocumentType, creator: CrewMember, description: str=None) -> Document:
        """Uploads a document.

        Args:
            name (str): The name of the document.
            file_path (str): The path to the file.
            document_type (DocumentType): The document type.
            creator (CrewMember): The crew member who uploaded the document.
            description (str, Optional): The description of the document. Defaults to None.

        Returns:
            Document: The uploaded document.
        """
        file_extension = os.path.splitext(file_path)[1]
        file_data = Document.convert_to_bytes(file_path)
        x = global_session.query(Document).filter(Document.name == name, Document.type_ == document_type).first()
        if x: raise DocumentExistsError(f"A document with the name {name} already exists.")
        new_document = Document(name=name, file_extension=file_extension, file_data=file_data, creator=creator, type_=document_type, description=description)
        global_session.add(new_document)
        global_session.commit()

        return new_document

    def save_to_path(self, path: str) -> None:
        """Saves the document to a path.
            Note: If the files extension was provided, it will be replaced with the file extension of the document.

        Args:
            path (str): The path to save the document to.
        """

        if os.path.splitext(path)[1] == "":
            path += self.file_extension
        else:
            path_root = os.path.splitext(path)[0]
            if path_root[-1] != ".":
                path_root += "."
            path = path_root + self.file_extension

        with open(path, "wb") as file:
            file.write(base64.b64decode(self.file_data))


class CrewMemberToDocument(Base):
    """Represents a document a crew member has."""
    __tablename__ = "crew_member_to_document"

    crew_member_id = Column(Integer, ForeignKey("crew_member.id"), nullable=False, primary_key=True)
    document_id = Column(Integer, ForeignKey("document.id"), nullable=False, primary_key=True)

    crew_member = relationship("CrewMember", back_populates="documents") # type: CrewMember
    document = relationship("Document") # type: Document


class CrewMember(Base):
    """Represents a crew member."""
    __tablename__ = "crew_member"

    id = Column(Integer, primary_key=True, autoincrement=True)
    active = Column(Boolean, default=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    phone = Column(String(50))
    email = Column(String(50))

    roles = relationship("CrewMemberToRole", back_populates="crew_member") # type: list[CrewMemberToRole]
    documents = relationship("CrewMemberToDocument", back_populates="crew_member") # type: list[CrewMemberToDocument]
    flights = relationship("CrewMemberToFlight", back_populates="crew_member") # type: list[CrewMemberToFlight]

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    def can_preform_role(self, role: CrewMemberRole) -> bool:
        """Checks if the crew member can preform a role.

        Args:
            role (Role): The role.

        Returns:
            bool: True if the crew member can preform the role, False otherwise.
        """
        for crew_member_to_role in self.roles:
            if crew_member_to_role.role == role:
                return True
        return False
    
    def __str__(self) -> str:
        return f"{self.full_name}"

    def add_document(self, document: Document) -> None:
        """Adds a document to the crew member.

        Args:
            document (Document): The document to add.
        """
        x = global_session.query(CrewMemberToDocument).filter(CrewMemberToDocument.crew_member_id == self.id, CrewMemberToDocument.document_id == document.id).first()
        if x: return
        global_session.add(CrewMemberToDocument(crew_member_id=self.id, document_id=document.id))
        global_session.commit()
    
    def remove_document(self, document: Document) -> None:
        """Removes a document from the crew member.
            This will not delete the document.

        Args:
            document (Document): The document to remove.
        """
        x = global_session.query(CrewMemberToDocument).filter(CrewMemberToDocument.crew_member_id == self.id, CrewMemberToDocument.document_id == document.id).first()
        if not x: return
        global_session.delete(x)
        global_session.commit()
    
    def add_role(self, role: CrewMemberRole) -> None:
        """Adds a role to the crew member.

        Args:
            role (Role): The role to add.
        """
        x = global_session.query(CrewMemberToRole).filter(CrewMemberToRole.crew_member_id == self.id, CrewMemberToRole.role_id == role.id).first()
        if x: return
        global_session.add(CrewMemberToRole(crew_member_id=self.id, role_id=role.id))
        global_session.commit()
    
    def remove_role(self, role: CrewMemberRole) -> None:
        """Removes a role from the crew member.
            This will not delete the role.

        Args:
            role (Role): The role to remove.
        """
        x = global_session.query(CrewMemberToRole).filter(CrewMemberToRole.crew_member_id == self.id, CrewMemberToRole.role_id == role.id).first()
        if not x: return
        global_session.delete(x)
        global_session.commit()
    
    @staticmethod
    def create(first_name: str, last_name: str, username: str, phone: str=None, email: str=None) -> CrewMember:
        """Creates a crew member.

        Args:
            first_name (str): The first name of the crew member.
            last_name (str): The last name of the crew member.
            username (str): The username of the crew member.
            phone (str, Optional): The phone number of the crew member. Defaults to None.
            email (str, Optional): The email of the crew member. Defaults to None.

        Returns:
            CrewMember: The crew member.
        """
        x = global_session.query(CrewMember).filter(CrewMember.username == username).first()
        if x: raise CrewMemberExistsError(f"A crew member with the username {username} already exists.")
        new_crew_member = CrewMember(first_name=first_name, last_name=last_name, username=username, phone=phone, email=email)
        global_session.add(new_crew_member)
        global_session.commit()

        return new_crew_member
    
    @staticmethod
    def find_by_username(username: str) -> CrewMember:
        """Finds a crew member by username.

        Args:
            username (str): The username of the crew member.

        Returns:
            Optional[CrewMember]: The crew member.
        """
        return global_session.query(CrewMember).filter(CrewMember.username == username).first()



def create_tables():
    Base.metadata.create_all(engine)
    create_default_data()

def drop_tables():
    Base.metadata.drop_all(engine)

def create_test_data():
    with Session() as session:
        batteries = [
            Battery(
                charge_cycle_count=10,
                capacity=1000,
                cell_count=3,
                item_value=55.00,
                name="Battery 1",
                serial_number="3QFPHCKCA5095C",
                weight=0.5,
                purchase_date=datetime.datetime(2020, 1, 1, 0, 0, 0),
            ),
            Battery(
                charge_cycle_count=75,
                capacity=1000,
                cell_count=3,
                item_value=55.00,
                name="Battery 2",
                serial_number="3QFPHCKCA5098C",
                weight=0.55
            ),
            Battery(
                charge_cycle_count=180,
                capacity=1000,
                cell_count=3,
                item_value=55.00,
                name="Battery 3",
                serial_number="3QFPHCJCA50ACE",
                weight=0.5
            )
        ]

        flight_controllers = [
            FlightController(
                name="Flight Controller 1",
                serial_number="3QDSHCG0033GJQ"
            )
        ]

        drones = [
            Drone(
                color="Gray",
                brand="DJI",
                flight_controller_id=1,
                geometry_id=DroneGeometry.find_by_name("Quad X").id,
                item_value=550.00,
                model="Mavic Mini 2",
                name="Mavic Mini 2",
                serial_number="3Q4SHC900335YD",
                weight=0.240
            )
        ]

        equipment = [
            Equipment(
                name="3-Way Charging Station",
                description="A charging station that can charge up to 3 batteries at once.",
                serial_number="3T2ZHCH004GWUH",
                weight=1.0,
                type_id=EquipmentType.find_by_name("Charger").id
            ),
            Equipment(
                name="Wall Charging Adapter",
                description="",
                serial_number="39YBHCB63100D0",
                weight=1.0,
                type_id=EquipmentType.find_by_name("Charger").id
            ),
            Equipment(
                name="Charging Cable",
                description="",
                serial_number="1TSJHAWXC17E25",
                weight=0.5,
                type_id=EquipmentType.find_by_name("Charger").id
            ),
            Equipment(
                name="Camera Lens Filter",
                description="",
                serial_number="123456789",
                weight=0.05,
                type_id=EquipmentType.find_by_name("Lens").id
            ),
        ]


        session.add_all(batteries)
        session.add_all(equipment)
        session.add_all(flight_controllers)
        session.add_all(drones)
        session.commit()

        for drone in drones:
            drone.add_batteries(batteries)
    
def create_default_data():
    LegalRule.create_defaults()
    EquipmentType.create_defaults()
    MaintenanceStatus.create_defaults()
    MaintenanceTaskStatus.create_defaults()
    FlightOperationApproval.create_defaults()
    FlightOperationType.create_defaults()
    FlightType.create_defaults()
    FlightStatus.create_defaults()
    CrewMemberRole.create_defaults()
    DocumentType.create_defaults()
    BatteryChemistry.create_defaults()
    Image.create_defaults()
    DroneGeometry.create_defaults()



def force_recreate():
    if DATABASE_URL.startswith("mysql"):
        temp_engine = create_engine(DATABASE_URL_WITHOUT_SCHEMA)
        temp_engine.execute(f"CREATE DATABASE IF NOT EXISTS {SCHEMA} DEFAULT CHARACTER SET utf8 COLLATE utf8_bin")
        temp_engine.dispose()

    drop_tables()
    create_tables()
    create_test_data()

    crew_member = CrewMember.create(
        first_name="Test",
        last_name="User",
        username="test"
    )

    crew_member.add_role(CrewMemberRole.find_by_name("Remote Pilot In Command (Remote PIC)"))

    drone = Drone.find_by_serial_number("3Q4SHC900335YD")
    battery = Battery.find_by_serial_number("3QFPHCKCA5095C")
    remote_pic = CrewMember.find_by_username("test")
    flight_type = FlightType.find_by_name("Hobby - Entertainment")

    flight = Flight.create(
        drone=drone,
        type_=flight_type
    ) # type: Flight

    flight.set_battery(battery)
    flight.set_location(Location(latitude=0, longitude=0))
    flight.set_weather(Weather(
        flight_id=flight.id,
        temperature=0,
        wind_speed=0,
        wind_direction=0,
        humidity=0,
        pressure=0,
        visibility=0,
        cloud_cover=0
    ))

    flight.add_equipment(Equipment.find_by_serial_number("123456789"))

    flight.add_crew_member(
        crew_member=remote_pic,
        role=CrewMemberRole.find_by_name("Remote Pilot In Command (Remote PIC)")
        )

    flight.start()

    flight.end(duration=12.25)


    flight = Flight.create(
        drone=drone,
        type_=flight_type
    )

    flight.set_battery(Battery.find_by_serial_number("3QFPHCKCA5098C"))
    flight.add_crew_member(
        crew_member=remote_pic,
        role=CrewMemberRole.find_by_name("Remote Pilot In Command (Remote PIC)")
    )
    flight.set_location(Location(latitude=101.5, longitude=25.2))
    flight.set_weather(Weather(
        flight_id=flight.id,
        temperature=0,
        wind_speed=0,
        wind_direction=0,
        humidity=0,
        pressure=0,
        visibility=0,
        cloud_cover=0
    ))

    flight.start()

    flight.end(duration=10.2)
    flight.battery.add_charge_cycle()

    flight = Flight.create(
        drone=drone,
        type_=flight_type
    )

    flight.set_battery(Battery.find_by_serial_number("3QFPHCJCA50ACE"))
    flight.add_crew_member(
        crew_member=remote_pic,
        role=CrewMemberRole.find_by_name("Remote Pilot In Command (Remote PIC)")
    )
    flight.set_location(Location(latitude=85.78, longitude=95.2))
    flight.set_weather(Weather(
        flight_id=flight.id,
        temperature=0,
        wind_speed=0,
        wind_direction=0,
        humidity=0,
        pressure=0,
        visibility=0,
        cloud_cover=0
    ))

    flight.start()

    flight.end(duration=14.0)
    flight.battery.add_charge_cycle()

    flight = Flight.create(
        drone=drone,
        type_=flight_type
    )

    flight.set_battery(Battery.find_by_serial_number("3QFPHCKCA5095C"))
    flight.add_crew_member(
        crew_member=remote_pic,
        role=CrewMemberRole.find_by_name("Remote Pilot In Command (Remote PIC)")
    )
    flight.set_location(Location(latitude=48.54, longitude=90.54, address="123 Main St, Somewhere, CA"))
    flight.set_weather(Weather(
        flight_id=flight.id,
        temperature=0,
        wind_speed=0,
        wind_direction=0,
        humidity=0,
        pressure=0,
        visibility=0,
        cloud_cover=0
    ))

    flight.start()

    flight.end(duration=8.5)
    flight.battery.add_charge_cycle()

    batteries = global_session.query(Battery).all()
    for battery in batteries:
        print(f"{battery.serial_number} - {battery.remaining_flights_percent}")


if __name__ == "__main__":
    force_recreate()