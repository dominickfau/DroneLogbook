import os
import bcrypt
import base64
import logging
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from typing import Optional
from sqlalchemy.orm.session import Session
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Enum, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import LONGBLOB
from PyQt5.QtGui import QImage
from .database import DeclarativeBase, engine, create_engine

from . import errors, enums, config, utilities

logger = logging.getLogger("backend")



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


@dataclass
class ImageData:
    file_path: str
    file_name: str
    file_extension: str
    """File extention without dot"""
    data: bytes


class Base(DeclarativeBase):
    __abstract__ = True
    # __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)


class Status(Base):
    __abstract__ = True
    __table_args__ = {"sqlite_autoincrement": False}

    name = Column(String(50), nullable=False, unique=True)

    def __repr__(self):
        return f'<{self.__class__.name}(id={self.id}, name="{self.name}")>'
    
    def __str__(self) -> str:
        return self.name
    
    def find_by_id(self, session: Session, id_: int) -> Optional['Status']:
        return session.query(self.__class__).filter_by(id=id_).first()
    
    def find_by_name(self, session: Session, name: str) -> Optional['Status']:
        return session.query(self.__class__).filter_by(name=name).first()


class Type_(Base):
    __abstract__ = True

    name = Column(String(50), nullable=False, unique=True)

    def __repr__(self):
        return f'<{self.__class__.name}(id={self.id}, name="{self.name}")>'
    
    def __str__(self) -> str:
        return self.name
    
    @classmethod
    def find_by_id(cls, session: Session, id_: int) -> Optional['Status']:
        return session.query(cls.__class__).filter_by(id=id_).first()
    
    @classmethod
    def find_by_name(cls, session: Session, name: str) -> Optional['Status']:
        return session.query(cls.__class__).filter_by(name=name).first()


class User(Base):
    __tablename__ = 'user'

    active = Column(Boolean, nullable=False, default=True)
    last_login_date = Column(DateTime) # type: datetime
    email = Column(String(256))
    first_name = Column(String(15), nullable=False)
    last_name = Column(String(15), nullable=False)
    phone = Column(String(256))
    username = Column(String(256), nullable=False, unique=True, index=True)
    password_hash = Column(String(256), nullable=False)

    # Relationship

    def __repr__(self) -> str:
        return f"User('{self.username}', '{self.email}')"
    
    def __str__(self) -> str:
        return self.full_name
    
    def on_login(self) -> 'UserLoginLog':
        """Log a login event."""
        return UserLoginLog.create(event_type=enums.LoginEventType.Login, user=self)
    
    def on_logout(self) -> 'UserLoginLog':
        """Log a logout event."""
        return UserLoginLog.create(event_type=enums.LoginEventType.Logout, user=self)
    
    @property
    def last_login_date_str(self) -> str:
        return self.last_login_date.strftime(config.DATETIME_FORMAT)
    
    @property
    def password(self) -> None:
        """Prevent password from being accessed."""
        raise AttributeError('password is not a readable attribute!')
    
    @property
    def is_superuser(self) -> bool:
        """Check if the user is a superuser."""
        return self.id == 1

    @password.setter
    def password(self, password: str):
        """Hash password on the fly. This allows the plan text password to be used when creating a User instance."""
        self.password_hash = User.generate_password_hash(password)
    
    @property
    def full_name(self) -> str:
        """Return the full name of the user. In the following format: first_name, last_name"""
        return f"{self.first_name}, {self.last_name}"
    
    @property
    def initials(self) -> str:
        """Return the initials of the user."""
        return f"{self.first_name[0].upper()}{self.last_name[0].upper()}"
    
    def check_password(self, password: str) -> bool:
        return User.verify_password(self.password_hash, password)
    
    @staticmethod
    def verify_password(password_hash: str, password: str) -> bool:
        """Check if password matches the one provided."""
        return bcrypt.checkpw(password.encode(config.ENCODING_STR), password_hash.encode(config.ENCODING_STR))
    
    @staticmethod
    def generate_password_hash(password: str) -> str:
        """Generate a hashed password."""
        return bcrypt.hashpw(password.encode(config.ENCODING_STR), bcrypt.gensalt()).decode(config.ENCODING_STR)


class UserLoginLog(Base):
    """A simple log for tracking who logged in or out and when."""
    __tablename__ = 'user_login'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_date = Column(DateTime, nullable=False, default=datetime.now)
    event_type = Column(Enum(enums.LoginEventType))
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    # Relationships
    user = relationship('User', foreign_keys=[user_id]) # type: User

    def __repr__(self) -> str:
        return f"<UserLoginLog(id={self.id}, event_date={self.event_date}, event_type={self.event_type}, user={self.user})>"
    
    def __str__(self) -> str:
        return f"{self.event_date} - {self.event_type} - {self.user}"

    @staticmethod
    def create(event_type: enums.LoginEventType, user: User) -> 'UserLoginLog':
        """Create a new user login log."""
        log = UserLoginLog(event_type=event_type, user=user)
        return log

    @staticmethod
    def on_login(user: User) -> 'UserLoginLog':
        """Log a login event."""
        return UserLoginLog.create(event_type=enums.LoginEventType.Login, user=user)
    
    @staticmethod
    def on_logout(user: User) -> 'UserLoginLog':
        """Log a logout event."""
        return UserLoginLog.create(event_type=enums.LoginEventType.Logout, user=user)


class LegalRule(Type_):
    """Represents a legal rule that applies to a flight."""
    __tablename__ = "legal_rule"


class EquipmentType(Type_):
    """Represents a type of equipment."""
    __tablename__ = "equipment_type"

    group = Column(Enum(enums.EquipmentGroup), nullable=False) # type: enums.EquipmentGroup


class MaintenanceStatus(Status):
    __tablename__ = "maintenance_status"


class MaintenanceTaskStatus(Status):
    """Represents the status of a maintenance task."""
    __tablename__ = "maintenance_task_status"


class UomConversion(DeclarativeBase):
    """Represents how to convert from one Uom to another."""
    __tablename__ = 'uom_conversion'

    to_uom_id = Column(Integer, ForeignKey('uom.id'), nullable=False, primary_key=True)
    from_uom_id = Column(Integer, ForeignKey('uom.id'), nullable=False, primary_key=True)
    description = Column(String(100))
    factor = Column(Float, nullable=False)
    multiply = Column(Float, nullable=False)

    # Relationships
    from_uom = relationship('Uom', foreign_keys=[from_uom_id])  # type: Uom
    to_uom = relationship('Uom', foreign_keys=[to_uom_id])  # type: Uom

    def __repr__(self) -> str:
        return f'UomConversion(from_uom="{self.from_uom}", to_uom="{self.to_uom}")'

    def convert(self, value: float) -> float:
        """Apply the conversion to the givin value."""
        return value * self.multiply / self.factor
    
    @staticmethod
    def create(session: Session, user: User, from_uom: 'Uom', to_uom: 'Uom', factor: float, multiply: float, description: str=None) -> 'UomConversion':
        """Creates a new conversion and adds it to the session.

        Args:
            session (Session): The DB session used for saving.
            user (User): The user creating this conversion.
            from_uom (Uom): The uom to convert from.
            to_uom (Uom): The uom to convert to.
            factor (float): When converting, the value is multiplied by multiply then divided by this.
            multiply (float): When converting, the value is multiplied by this.
            description (str, optional): A shot description for this conversion. Defaults to None.

        Returns:
            UomConversion: Returns the new conversion obj.
        """

        conversion = UomConversion(
            from_uom=from_uom,
            to_uom=to_uom,
            factor=factor,
            multiply=multiply,
            description=description,
            created_by_user=user,
            modified_by_user=user
        )
        session.add(conversion)
        return conversion


class Uom(Base):
    """Represents a unit of measure."""
    __tablename__ = 'uom'
    __table_args__ = (
        UniqueConstraint("code", "name"),
    )

    active = Column(Boolean, default=True)
    code = Column(String(10), nullable=False)
    description = Column(String(100), nullable=False)
    name = Column(String(50), nullable=False)
    read_only = Column(Boolean, default=False)
    type_name = Column(Enum(enums.UomType), nullable=False) # type: enums.UomType

    # Relationships
    conversions = relationship("UomConversion", back_populates="from_uom", foreign_keys=UomConversion.from_uom_id) # type: list[UomConversion]

    def __repr__(self) -> str:
        return f'<Uom(id={self.id}, name="{self.name}")>'
    
    def add_conversion(self, session: Session, user: User, to_uom: 'Uom', factor: float, multiply: float, description: str=None) -> UomConversion:
        """Add a new conversion to this uom.

        Args:
            session (Session): The DB session used for saving.
            user (User): The user creating this conversion.
            to_uom (Uom): The uom to convert to.
            factor (float): When converting, the value is multiplied by multiply then divided by this.
            multiply (float): When converting, the value is multiplied by this.
            description (str, optional): A shot description for this conversion. Defaults to None.
        
        Raises:
            errors.UomConversionError: Raised if uom types are incompatible.

        Returns:
            UomConversion: Returns the new conversion obj.
        """
        for conversion in self.conversions:
            if conversion.to_uom == to_uom:
                return conversion
        
        if self.type_name != to_uom.type_name:
            raise errors.UomConversionError(f"Can not add uom conversion from {self.name} to {to_uom.name}. Uoms have incompatible types {self.type_name} - {to_uom.type_name}.")

        conversion = UomConversion.create(
                        session,
                        user,
                        from_uom=self,
                        to_uom=to_uom,
                        factor=factor,
                        multiply=multiply,
                        description=description
                        )
        self.conversions.append(conversion)
        self.date_modified = datetime.now()
        self.modified_by_user = user
        return conversion
    
    def remove_conversion(self, session: Session, user: User, conversion: UomConversion) -> None:
        """Remove a conversion.

        Args:
            session (Session): The DB session used for saving.
            user (User): The user removing this conversion.
            conversion (UomConversion): The conversion to remove.
        """
        if conversion not in self.conversions:
            return None
        self.conversions.remove(conversion)
        session.delete(conversion)
        self.date_modified = datetime.now()
        self.modified_by_user = user
    
    def convert_to(self, to_uom: 'Uom', value: float) -> float:
        """Returns conversion to another Uom.

        Args:
            to_uom (Uom): The Uom to convert to.
            value (float): The value to convert.

        Raises:
            errors.UomConversionError: Raised if the Uom types are not compatible.
            errors.UomConversionError: Raised if unable to find conversion.

        Returns:
            float: The converted value.
        """
        if self.id == to_uom.id:
            return value
        if self.type_name != to_uom.type_name:
            raise errors.UomConversionError("Uoms must be of the same type.")
        if to_uom not in [conversion.to_uom for conversion in self.conversions]:
            raise errors.UomConversionError(f"Unknown conversion from '{self.name}' to '{to_uom.name}'")

        for uom_conversion in self.conversions:
            if uom_conversion.to_uom == to_uom:
                break
        return uom_conversion.convert(value)

    @staticmethod
    def find_by_name(session: Session, name: str) -> Optional['Uom']:
        """Returns a Uom by name."""
        return session.query(Uom).filter_by(name=name).first() # type: Uom

    @staticmethod
    def find_by_code(session: Session, code: str) -> Optional['Uom']:
        """Returns a Uom by code."""
        return session.query(Uom).filter_by(code=code).first() # type: Uom

    @staticmethod
    def find_by_id(session: Session, id: int) -> Optional['Uom']:
        """Returns a Uom by id."""
        return session.query(Uom).filter_by(id=id).first() # type: Uom


flight_operation_type_to_approval_table = Table(
    "flight_operation_type_to_approval",
    DeclarativeBase.metadata,
    Column("flight_operation_type_id", ForeignKey("flight_operation_type.id"), primary_key=True),
    Column("flight_operation_approval_id", ForeignKey("flight_operation_approval.id"), primary_key=True),
)


class FlightOperationApproval(Type_):
    """Represents the approval of a flight operation."""
    __tablename__ = "flight_operation_approval"
    
    description = Column(String(256), nullable=False)

    # Relationships
    flight_operation_types = relationship("FlightOperationType", secondary=flight_operation_type_to_approval_table) # type: List[FlightOperationType]


class FlightOperationType(Status):
    """Represents the type of a flight operation."""
    __tablename__ = "flight_operation_type"

    description = Column(String(256), nullable=False)

    # Relationships
    approvals = relationship("FlightOperationApproval", secondary=flight_operation_type_to_approval_table) # type: List[FlightOperationApproval]


class FlightType(Base):
    """Represents the type of a flight."""
    __tablename__ = "flight_type"

    name = Column(String(256), nullable=False, unique=True)
    description = Column(String(256), nullable=False)
    flight_operation_type_id = Column(Integer, ForeignKey("flight_operation_type.id"), nullable=False)

    flight_operation_type = relationship("FlightOperationType", foreign_keys=[flight_operation_type_id]) # type: FlightOperationType


class FlightStatus(Status):
    """Represents the status of a flight."""
    __tablename__ = "flight_status"


# class FlightController(Base):
#     """Represents a flight controller."""
#     __tablename__ = "flight_controller"

#     serial_number = Column(String(256), unique=True)
#     name = Column(String(50))
#     purchase_date = Column(DateTime, default=datetime.now)
#     status = Column(Enum(enums.Airworthyness), default=enums.Airworthyness.Airworthy) # type: enums.Airworthyness
#     price = Column(Float, default=0.00)
#     """Flight controller's value in US dollars."""
#     last_flight_date = Column(DateTime)
#     last_flight_duration = Column(Float)
#     """Duration of the last flight in minutes."""
    
#     drone = relationship("Drone", uselist=False, back_populates="flight_controller") # type: Drone

#     @staticmethod
#     def create(name: str, serial_number: str, purchase_date: datetime, price: float=0.00) -> 'FlightController':
#         """Creates a new flight controller."""
#         controller = FlightController(name=name, serial_number=serial_number, purchase_date=purchase_date, price=price)
#         return controller

#     @property
#     def total_flight_time(self) -> float:
#         """Returns the total flight time of the drone in minutes."""
#         if not self.drone: return 0.00
#         return sum(flight.duration for flight in self.drone.flights if flight.active)

#     @property
#     def total_flights(self) -> int:
#         """Returns the total number of flights the drone has taken."""
#         if not self.drone: return 0.00
#         return len([flight for flight in self.drone.flights if flight.active])

#     @property
#     def combobox_name(self) -> str:
#         return f"[{self.serial_number}] {self.name}"
    
#     @property
#     def age(self) -> float:
#         """Returns the age of the battery in years from the purchase date."""
#         return round((datetime.now() - self.purchase_date).days / 365, 2) if self.purchase_date else 0

#     @staticmethod
#     def find_by_serial_number(session: Session, serial_number: str) -> 'FlightController':
#         """Finds a flight controller by serial number."""
#         return session.query(FlightController).filter(FlightController.serial_number == serial_number).first()
    
#     @staticmethod
#     def find_by_combobox_name(combobox_name: str) -> 'FlightController':
#         """Finds a flight controller by combobox name."""
#         serial_number = combobox_name.split("]")[0].strip("[").strip()
#         return FlightController.find_by_serial_number(serial_number)
    
#     @staticmethod
#     def find_all(session: Session) -> List['FlightController']:
#         """Finds all flight controllers."""
#         return session.query(FlightController).all()


class Image(Base):
    """Represents an image."""
    __tablename__ = "image"

    name = Column(String(256), nullable=False, unique=True)
    data = Column(LONGBLOB, nullable=False)
    file_extention = Column(String(10), nullable=False)
    """File extention without dot."""
    read_only = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<Image(name={self.name})>"
    
    def to_QImage(self) -> QImage:
        """Converts the image to a QImage."""
        return QImage.fromData(self.data, format=self.file_extention)
    
    @staticmethod
    def find_by_name(session: Session, name: str) -> 'Image':
        """Finds an image by name."""
        return session.query(Image).filter(Image.name == name).first()

    @staticmethod
    def convert_to_bytes(file_path: str) -> ImageData:
        """Converts a file path to bytes."""
        file_name, file_extension = os.path.basename(file_path).split(".")
        with open(file_path, "rb") as f:
            data = f.read()
        return ImageData(file_path=file_path, file_name=file_name, file_extension=file_extension, data=data)

    @staticmethod
    def upload(session: Session, name: str, data: bytes, file_extention: str) -> 'Image':
        """Uploads an image."""
        if Image.find_by_name(session, name):
            raise errors.ImageExistsError("An image with this name already exists.")
        file_extention = file_extention.replace(".", "")
        image = Image(name=name, data=data, file_extention=file_extention)
        session.add(image)
        return image
    
    @staticmethod
    def upload_from_image_data(session: Session, image_data: ImageData) -> 'Image':
        """Uploads an image."""
        if Image.find_by_name(session, image_data.file_name):
            raise errors.ImageExistsError("An image with this name already exists.")
        image = Image(name=image_data.file_name, data=image_data.data, file_extention=image_data.file_extension.replace(".", ""))
        session.add(image)
        return image


class DroneGeometry(Base):
    """Represents the geometry of a drone."""
    __tablename__ = "drone_geometry"

    name = Column(String(256), nullable=False, unique=True)
    description = Column(String(256), nullable=False)
    image_id = Column(Integer, ForeignKey("image.id"), nullable=False)
    number_of_propellers = Column(Integer, nullable=False)
    alternating_rotaion = Column(Boolean, nullable=False, default=False)
    """True if the propellers rotate in alternating directions, False if they rotate in the same direction."""
    thrust_direction = Column(Enum(enums.ThrustDirection), nullable=False, default=enums.ThrustDirection.Vertical)
    """The direction the propellers thrust. Defaults to Vertical."""

    image = relationship("Image", foreign_keys=[image_id]) # type: Image

    @staticmethod
    def find_by_name(session: Session, name: str) -> 'DroneGeometry':
        """Finds a drone geometry by name."""
        return session.query(DroneGeometry).filter(DroneGeometry.name == name).first()
    
    @staticmethod
    def find_all(session: Session) -> List['DroneGeometry']:
        """Finds all drone geometries."""
        return session.query(DroneGeometry).all()
    

class BatteryChemistry(Base):
    """Represents a battery chemistry."""
    __tablename__ = "battery_chemistry"

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
    def find_by_code(session: Session, code: str) -> 'BatteryChemistry':
        """Finds a battery chemistry by code."""
        return session.query(BatteryChemistry).filter(BatteryChemistry.code == code).first()
    
    @staticmethod
    def find_by_name(session: Session, name: str) -> 'BatteryChemistry':
        """Finds a battery chemistry by name."""
        return session.query(BatteryChemistry).filter(BatteryChemistry.name == name).first()
    
    @staticmethod
    def find_by_combobox_name(session: Session, combobox_name: str) -> 'BatteryChemistry':
        """Finds a battery chemistry by combobox name."""
        code = combobox_name.split("]")[0].strip("[").strip()
        return BatteryChemistry.find_by_code(session, code)


class Battery(Base):
    """Represents a battery."""
    __tablename__ = "battery"

    capacity = Column(Integer, nullable=False)
    """The battery's capacity in mAh."""
    cell_count = Column(Integer, nullable=False)
    """The number of cells in the battery."""
    charge_cycle_count = Column(Integer, default=0)
    """The number of times the battery has been charged."""
    chemistry_id = Column(Integer, ForeignKey("battery_chemistry.id"), nullable=False, default=1)
    notes = Column(String(256))
    price = Column(Float, default=0.00)
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
    status = Column(Enum(enums.Airworthyness), default=enums.Airworthyness.Airworthy, nullable=False) # type: enums.Airworthyness
    """The airworthiness status of the battery."""
    weight = Column(Float, default=0.00)
    """The battery's weight in kilograms."""

    chemistry = relationship("BatteryChemistry", foreign_keys=[chemistry_id]) # type: BatteryChemistry
    flights = relationship("Flight", back_populates="battery") # type: List[Flight]

    def __str__(self) -> str:
        return f'Battery "{self.inventory_id}", {self.capacity}mAh, {self.cell_count} cells'

    @property
    def combobox_name(self) -> str:
        """Returns the name of the battery in a combobox format."""
        return f"[{self.serial_number}] - {self.name}"
    
    @property
    def age(self) -> float:
        """Returns the age of the battery in years from the purchase date."""
        return round((datetime.now() - self.purchase_date).days / 365, 2) if self.purchase_date else 0
    
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

    def add_charge_cycle(self):
        """Adds a charge cycle to the battery."""
        self.charge_cycle_count += 1
    
    @staticmethod
    def find_all(session: Session) -> List['Battery']:
        """Finds all batteries."""
        return session.query(Battery).all()
    
    @staticmethod
    def find_by_serial_number(session: Session, serial_number: str) -> 'Battery':
        """Finds a battery by its serial number."""
        return session.query(Battery).filter_by(serial_number=serial_number).first()
    
    @staticmethod
    def find_by_combobox_name(session: Session, combobox_name: str) -> 'Battery':
        """Finds a battery by its combobox name."""
        serial_number = combobox_name.split("]")[0].strip("[").strip()
        return Battery.find_by_serial_number(session, serial_number)


drone_to_batteries_table = Table(
    "drone_to_batteries",
    DeclarativeBase.metadata,
    Column("drone_id", ForeignKey("drone.id"), primary_key=True),
    Column("battery_id", ForeignKey("battery.id"), primary_key=True),
)


class Drone(Base):
    """Represents a drone."""
    __tablename__ = "drone"

    color = Column(String(25))
    brand = Column(String(50))
    description = Column(String(256))
    flight_controller_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    geometry_id = Column(Integer, ForeignKey("drone_geometry.id"), nullable=False)
    price = Column(Float, default=0.00)
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
    status = Column(Enum(enums.Airworthyness), default=enums.Airworthyness.Airworthy) # type: enums.Airworthyness
    """The airworthyness of the drone."""
    weight = Column(Float, default=0.00)
    """The drone's weight in kilograms."""

    batteries = relationship("Battery", secondary=drone_to_batteries_table) # type: List[Battery]
    flight_controller = relationship("Equipment", back_populates="drone", foreign_keys=[flight_controller_id]) # type: Equipment
    flights = relationship("Flight", back_populates="drone") # type: List[Flight]
    geometry = relationship("DroneGeometry", foreign_keys=[geometry_id]) # type: DroneGeometry

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
    
    @staticmethod
    def create(serial_number: str, geometry: DroneGeometry, batteries: List['Battery'], flight_controller: 'Equipment', name: str=None) -> 'Drone':
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

        drone.add_batteries(batteries)
        return drone
    
    @staticmethod
    def find_by_serial_number(session: Session, serial_number: str) -> 'Drone':
        """Finds a drone by its serial number."""
        return session.query(Drone).filter(Drone.serial_number == serial_number).first()
    
    @staticmethod
    def find_by_combobox_name(session: Session, combobox_name: str) -> 'Drone':
        """Finds a drone by its combobox name."""
        serial_number = combobox_name.split("]")[0].strip("[").strip()
        return Drone.find_by_serial_number(session, serial_number)
    
    def add_battery(self, battery: 'Battery') -> None:
        """Adds a battery to the drone. If the battery is already attached to the drone, it is ignored."""
        if battery not in self.batteries:
            self.batteries.append(battery)  
        
    def add_batteries(self, batteries: List['Battery']) -> None:
        """Adds a list of batteries to the drone. If any of the batteries are already attached to the drone, they are ignored."""
        for battery in batteries:
            self.add_battery(battery)
    
    def remove_battery(self, battery: 'Battery') -> None:
        """Removes a battery from the drone. If the battery is not attached to the drone, it is ignored."""
        if battery in self.batteries:
            self.batteries.remove(battery)
    
    def remove_batteries(self, batteries: List['Battery']) -> None:
        """Removes a list of batteries from the drone. If any of the batteries are not attached to the drone, they are ignored."""
        for battery in batteries:
            self.remove_battery(battery)


class Weather(Base):
    """Represents a weather condition during a flight."""
    __tablename__ = "weather"

    cloud_cover = Column(Float, nullable=False)
    """Cloud cover in percent."""
    date = Column(DateTime, default=datetime.now)
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

    flight = relationship("Flight", back_populates="weather", foreign_keys=[flight_id]) # type: Flight


flight_to_equipment_table = Table(
    "flight_to_equipment",
    DeclarativeBase.metadata,
    Column("flight_id", ForeignKey("flight.id"), primary_key=True),
    Column("equipment_id", ForeignKey("equipment.id"), primary_key=True),
)


class Flight(Base):
    """Represents a flight with a drone and any other items used."""
    __tablename__ = "flight"

    id = Column(Integer, primary_key=True, autoincrement=True)
    active = Column(Boolean, default=True, doc="Whether the flight is active or not. If the flight is not active, it will not be included in any statistics.")
    """Whether the flight is active or not. If the flight is not active, it will not be included in any statistics."""
    address = Column(String(256))
    battery_id = Column(Integer, ForeignKey("battery.id"))
    battery_notes = Column(String(256))
    date = Column(DateTime, default=datetime.now)
    date_started = Column(DateTime)
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
    legal_rule_id = Column(Integer, ForeignKey("legal_rules.id"), nullable=False)
    legal_rule_details = Column(String(256), default="")
    max_agl_altitude = Column(Float, default=0.00)
    """The maximum altitude AGL in meters."""
    name = Column(String(256))
    night_flight = Column(Boolean, default=False)
    notes = Column(String(256))
    operation_type_id = Column(Integer, ForeignKey("flight_operation_type.id"), nullable=False)
    operation_approval_id = Column(Integer, ForeignKey("flight_operation_approval.id"), nullable=False)
    post_flight_notes = Column(String(256))
    status_id = Column(Integer, ForeignKey("flight_status.id"), nullable=False)
    type_id = Column(Integer, ForeignKey("flight_type.id"), nullable=False)
    utm_authorization = Column(String(256))
    """The Unmanned Aircraft System Traffic Management (UTM or LAANC) of the flight."""
    uuid = Column(String(14), unique=True, default=lambda: utilities.generate_random_string(Flight))

    # Relationships
    battery = relationship("Battery", back_populates="flights") # type: Battery
    crew_members = relationship("CrewMemberToFlight", back_populates="flight") # type: List[CrewMemberToFlight]
    drone = relationship("Drone", back_populates="flights") # type: Drone
    legal_rule = relationship("LegalRule", foreign_keys=[legal_rule_id]) # type: LegalRule
    operation_type = relationship("FlightOperationType", foreign_keys=[operation_type_id]) # type: FlightOperationType
    operation_approval = relationship("FlightOperationApproval", foreign_keys=[operation_approval_id]) # type: FlightOperationApproval
    status = relationship("FlightStatus", foreign_keys=[status_id]) # type: FlightStatus
    type_ = relationship("FlightType", foreign_keys=[type_id]) # type: FlightType
    used_equipment = relationship("Equipment", secondary=flight_to_equipment_table) # type: List[Equipment]
    weather = relationship("Weather", back_populates="flight", uselist=False) # type: Weather

    def __repr__(self) -> str:
        return f'Flight "{self.uuid}", {self.date.strftime(config.DATE_FORMAT)}, {self.drone.name}'
    
    @staticmethod
    def create(session: Session, drone: Drone, type_: FlightType, crew: list[tuple['CrewMember', 'CrewMemberRole']]=None) -> 'Flight':
        """Creates a new flight."""
        flight = Flight(drone_id=drone.id, type_id=type_.id)
        flight.name = f"Flight {flight.date}"
        if crew is not None:
            for member, role in crew:
                flight.add_crew_member(session, member, role)
        return flight

    # @validates("battery_id")
    # def validate_battery_id(self, key: str, battery_id: int) -> int:
    #     """Checks if the battery is usable by the drone."""
    #     useable_battery_ids = [battery_to_drone.battery.id for battery_to_drone in self.drone.batteries]
    #     if battery_id not in useable_battery_ids:
    #         raise BatteryNotAssignedError("Could not add battery to flight. Battery is not assigned to the drone.")
    #     return battery_id

    @property
    def location(self) -> 'Location':
        """Returns the location of the flight."""
        return Location(self.location_latitude, self.location_longitude, address=self.address)
    
    @property
    def total_equipment_weight(self) -> float:
        """Returns the total equipment weight in kilograms."""
        total = 0.00

        for equipment in self.used_equipment:
            if equipment.type_.group == enums.EquipmentGroup.Airborne_Equipment:
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
    
    def add_equipment(self, equipment: 'Equipment') -> None:
        """Adds an equipment to the flight. If the equipment is already attached to the flight, it is ignored."""
        if equipment not in self.used_equipment:
            self.used_equipment.append(equipment)
    
    def remove_equipment(self, equipment: 'Equipment') -> None:
        """Removes an equipment from the flight. If the equipment is not attached to the flight, it is ignored."""
        if equipment in self.used_equipment:
            self.used_equipment.append(equipment)
        
    def add_crew_member(self, session: Session, crew_member: 'CrewMember', role: 'CrewMemberRole') -> None:
        """Adds a crew member to the flight. If the crew member is already attached to the flight, it is ignored."""
        crew_members = [crew_member_to_flight.crew_member for crew_member_to_flight in self.crew_members]
        if crew_member in crew_members: return

        # Check if the crew member can preform the role
        if not crew_member.can_preform_role(role):
            raise errors.RoleNotAssignedError(f"Could not add crew member {crew_member.full_name} to flight. This crew member can not preform role {role.name}.")

        crew_member_to_flight = CrewMemberToFlight(flight_id=self.id, crew_member_id=crew_member.id, role_id=role.id)
        session.add(crew_member_to_flight)
    
    def remove_crew_member(self, session: Session, crew_member: 'CrewMember') -> None:
        """Removes a crew member from the flight. If the crew member is not attached to the flight, it is ignored."""
        crew_members = [crew_member_to_flight.crew_member for crew_member_to_flight in self.crew_members]
        if crew_member not in crew_members: return
        for crew_member_to_flight in self.crew_members:
            if crew_member_to_flight.crew_member == crew_member:
                role = crew_member_to_flight.role
                if role.required_for_flight:
                    raise errors.RoleRemovalError(f"Could not remove crew member {crew_member.full_name} from flight. Role {role.name} is required for the flight.")
                session.delete(crew_member_to_flight)
                return
    
    def set_battery(self, battery: Battery) -> None:
        """Sets the battery used for this flight."""
        if battery.id not in self.drone.batteries:
            raise errors.BatteryNotAssignedError(f"Could not add battery to flight. Battery {battery.serial_number} is not assigned to the drone.")
        self.battery = battery
    
    def set_weather(self, weather: Weather) -> None:
        """Sets the weather for this flight."""
        self.weather = weather
    
    def set_location(self, location: Location) -> None:
        """Sets the location of the flight."""
        self.location_latitude = location.latitude
        self.location_longitude = location.longitude
        self.address = location.address
    
    def start(self, session: Session) -> None:
        """Starts the flight."""

        if self.status_id >= FlightStatus.find_by_name(session, "InProgress"):
            raise errors.FlightAlreadyStartedError("Can not restart a flight that has already started or finished.")

        if self.battery_id is None:
            raise errors.BatteryNotAssignedError("Could not start flight. No battery assigned to flight.")
        
        if self.total_crew_members == 0:
            raise errors.NoCrewMembersError("Could not start flight. No crew members linked to flight.")

        required_roles = session.query(CrewMemberRole).filter(CrewMemberRole.required_for_flight == True).all() # type: List[CrewMemberRole]
        current_roles = [crew_member_to_flight.role for crew_member_to_flight in self.crew_members]

        for role in required_roles:
            if role not in current_roles:
                raise errors.MissingRequiredRoleError(f"Could not start flight. Missing required role {role.name}.")
        
        self.status = FlightStatus.find_by_name(session, "InProgress")
        self.date_started = datetime.now()
        self.drone.flight_controller.start_flight(self)
    
    def end(self, session: Session, duration: float) -> None:
        """Ends the flight.

        Args:
            duration (float): The flight time in minutes.
        """        
        self.duration = duration
        self.status_id = FlightStatus.find_by_name(session, "Completed")
        self.drone.flight_controller.end_flight(self)


class Equipment(Base):
    """Represents an item of equipment."""
    __tablename__ = "equipment"

    description = Column(String(256))
    serial_number = Column(String(256), unique=True)
    name = Column(String(50))
    purchase_date = Column(DateTime, default=datetime.now)
    status = Column(Enum(enums.Airworthyness), default=enums.Airworthyness.Airworthy) # type: enums.Airworthyness
    price = Column(Float, default=0.00)
    """Flight controller's value in US dollars."""
    last_flight_date = Column(DateTime)
    last_flight_duration = Column(Float)
    """Duration of the last flight in minutes."""
    """The airworthiness status of the equipment."""
    weight = Column(Float, default=0.00)
    """The equipment's weight in kilograms."""
    type_id = Column(Integer, ForeignKey("equipment_type.id"), nullable=False)

    type_ = relationship("EquipmentType") # type: EquipmentType
    flights = relationship("Flight", secondary=flight_to_equipment_table) # type: List[Flight]

    def start_flight(self, flight: Flight):
        """Starts a flight."""
        # TODO: Implement this.
        pass

    def end_flight(self, flight: Flight) -> None:
        """Ends a flight."""

        self.last_flight_date = flight.date
        self.last_flight_duration = flight.duration

    @property
    def combobox_name(self) -> str:
        """Returns the name of the equipment in a combobox format."""
        return f"[{self.serial_number}] - {self.name}"
    
    @property
    def total_flights(self) -> int:
        """Returns the total number of flights the equipment has been used in."""
        return len([flight for flight in self.flights if flight.active])
    
    @property
    def age(self) -> float:
        """Returns the age of the equipment in years from the purchase date."""
        return round((datetime.now() - self.purchase_date).days / 365, 2) if self.purchase_date else 0
    
    @property
    def total_flight_time(self) -> float:
        """Returns the flight time of the equipment in minutes."""
        return sum(equipment_to_flight.flight.duration for equipment_to_flight in self.flights if equipment_to_flight.flight.active)
    
    @staticmethod
    def find_by_serial_number(session: Session, serial_number: str) -> 'Equipment':
        """Finds an equipment by its serial number."""
        return session.query(Equipment).filter_by(serial_number=serial_number).first()
    
    @staticmethod
    def find_by_type(session: Session, type_: EquipmentType) -> Optional[List['Equipment']]:
        """Finds all equipment by type."""
        return session.query(Equipment).filter_by(type_=type_).all()
    
    @staticmethod
    def find_all(session: Session) -> List['Equipment']:
        """Finds all equipment."""
        return session.query(Equipment).all()
    
    @staticmethod
    def find_by_combobox_name(session: Session, combobox_name: str) -> 'Equipment':
        """Finds a equipment by its combobox name."""
        serial_number = combobox_name.split("]")[0].strip("[").strip()
        return Equipment.find_by_serial_number(session, serial_number)
    
    @staticmethod
    def create(name: str, serial_number: str, purchase_date: datetime.datetime, price: float, type_: EquipmentType, description: str="") -> 'Equipment':
        """Creates a new equipment.

        Args:
            name (str): The name of the equipment.
            serial_number (str): The serial number of the equipment.
            purchase_date (datetime.datetime): The date the equipment was purchased.
            price (float): The value of the equipment in US dollars.
            type_ (EquipmentType): The type of the equipment.
            description (str): The description of the equipment.
        """
        equipment = Equipment(
            name=name,
            serial_number=serial_number,
            purchase_date=purchase_date,
            price=price,
            type_id=type_.id,
            description=description
            )
        return equipment


class DroneMaintenance(Base):
    """Represents a maintenance event for a drone."""
    __tablename__ = "drone_maintenance"

    cost = Column(Float, default=0.00)
    """The cost of the maintenance in US dollars."""
    date_scheduled = Column(DateTime, default=datetime.now)
    """The date the maintenance was scheduled or preformed."""
    name = Column(String(50), nullable=False)
    notes = Column(String(256), nullable=False)
    drone_id = Column(Integer, ForeignKey("drone.id"))
    status_id = Column(Integer, ForeignKey("maintenance_status.id"))

    drone = relationship("Drone") # type: Drone
    status = relationship("MaintenanceStatus") # type: MaintenanceStatus
    tasks = relationship("DroneMaintenanceTask", back_populates="maintenance") # type: List[DroneMaintenanceTask]


class DroneMaintenanceTask(Base):
    """Represents a task for a drone maintenance event."""
    __tablename__ = "drone_maintenance_task"

    description = Column(String(256))
    drone_maintenance_id = Column(Integer, ForeignKey("drone_maintenance.id"))
    crew_member_id = Column(Integer, ForeignKey("crew_member.id"))
    status_id = Column(Integer, ForeignKey("maintenance_task_status.id"), default=10)
    part_number = Column(String(50))
    part_description = Column(String(256))
    part_replaced = Column(Boolean, default=False)
    """Whether or not the part was replaced."""
    new_part_serial_number = Column(String(256))
    """The serial number of the new part. Only used if the part was replaced."""

    crew_member = relationship("CrewMember") # type: CrewMember
    """The crew member who performed the task."""
    maintenance = relationship("DroneMaintenance", back_populates="tasks") # type: DroneMaintenance
    """The maintenance event this task is associated with."""
    status = relationship("MaintenanceTaskStatus", foreign_keys=[status_id]) # type: MaintenanceTaskStatus
    

class EquipmentMaintenance(Base):
    """Represents a maintenance event for an equipment."""
    __tablename__ = "equipment_maintenance"

    cost = Column(Float, default=0.00)
    """The cost of the maintenance in US dollars."""
    date_scheduled = Column(DateTime, default=datetime.now)
    """The date the maintenance was scheduled or preformed."""
    name = Column(String(50), nullable=False)
    notes = Column(String(256))
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    status_id = Column(Integer, ForeignKey("maintenance_status.id"))

    equipment = relationship("Equipment") # type: Equipment
    status = relationship("MaintenanceStatus") # type: MaintenanceStatus


class BatteryMaintenance(Base):
    """Represents a maintenance event for a battery."""
    __tablename__ = "battery_maintenance"

    cost = Column(Float, default=0.00)
    """The cost of the maintenance in US dollars."""
    date_scheduled = Column(DateTime, default=datetime.now)
    """The date the maintenance was scheduled or preformed."""
    name = Column(String(50), nullable=False)
    notes = Column(String(256))
    batteryid = Column(Integer, ForeignKey("battery.id"))
    status_id = Column(Integer, ForeignKey("maintenance_status.id"))

    battery = relationship("Battery") # type: Battery
    status = relationship("MaintenanceStatus") # type: MaintenanceStatus


class DroneScheduledTask(Base):
    """Represents a scheduled task for a drone."""
    __tablename__ = "drone_scheduled_task"

    interval = Column(Integer)
    """The interval in flight hours to preform the task again."""
    maintenance_task_id = Column(Integer, ForeignKey("drone_maintenance_task.id"), unique=True)
    used = Column(Boolean, default=False)
    """Whether or not the task has been used."""

    drone_maintenance_task = relationship("DroneMaintenanceTask") # type: DroneMaintenanceTask

    @staticmethod
    def schedule_recurring_tasks(session: Session, task: DroneMaintenanceTask, interval: int) -> 'DroneScheduledTask':
        """Schedules a recurring task for a drone maintenance task.

        Args:
            task (DroneMaintenanceTask): The task to schedule.
            interval (int): The interval in flight hours to preform the task again.

        Raises:
            ScheduledTaskExistsError: If the task is already scheduled.

        Returns:
            DroneScheduledTask: The scheduled task.
        """
        result = session.query(DroneScheduledTask).filter(DroneScheduledTask.maintenance_task_id == task.id).first()
        if result:
            raise errors.ScheduledTaskExistsError(f"A scheduled task for task {task.id} already exists.")

        new_task = DroneScheduledTask(maintenance_task_id=task.id, interval=interval)
        return new_task


class CrewMemberRole(Type_):
    """Represents a role a crew member can have."""
    __tablename__ = "crew_member_role"

    description = Column(String(256))
    required_for_flight = Column(Boolean, default=False)


class CrewMemberToFlight(DeclarativeBase):
    """Represents a mapping between a crew member and a flight."""
    __tablename__ = "crew_member_to_flight"

    crew_member_id = Column(Integer, ForeignKey("crew_member.id"), primary_key=True, nullable=False)
    flight_id = Column(Integer, ForeignKey("flight.id"), primary_key=True, nullable=False)
    role_id = Column(Integer, ForeignKey("crew_member_role.id"), primary_key=True, nullable=False)

    crew_member = relationship("CrewMember", back_populates="flights") # type: CrewMember
    flight = relationship("Flight", back_populates="crew_members") # type: Flight
    role = relationship("CrewMemberRole") # type: CrewMemberRole


class DocumentType(Type_):
    """Represents a document type."""
    __tablename__ = "document_type"

    description = Column(String(256))


class Document(Base):
    """Represents a document."""
    __tablename__ = "document"

    date_uploaded = Column(DateTime, default=datetime.now)
    """The date the document was uploaded."""
    name = Column(String(50), nullable=False, unique=True)
    """The name of the document."""
    description = Column(String(256))
    """The description of the document."""
    file_extension = Column(String(10), nullable=False)
    """The file extension of the document."""
    file_data = Column(LONGBLOB, nullable=False) # type: bytes
    """The file data of the document. As represented by a base64 encoded bytes object."""
    created_by_id = Column(Integer, ForeignKey("crew_member.id"))
    """The crew member who uploaded the document."""
    type_id = Column(Integer, ForeignKey("document_type.id"), nullable=False)


    created_by = relationship("CrewMember") # type: CrewMember
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
    def upload(session: Session, name: str, file_path: str, document_type: DocumentType, creator: 'CrewMember', description: str=None) -> 'Document':
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
        x = session.query(Document).filter(Document.name == name, Document.type_ == document_type).first()
        if x:
            raise errors.DocumentExistsError(f"A document with the name {name} already exists.")
        new_document = Document(name=name, file_extension=file_extension, file_data=file_data, creator=creator, type_=document_type, description=description)
        return new_document

    def download(self, path: str) -> None:
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


crew_member_to_document_table = Table(
    "crew_member_to_document",
    DeclarativeBase.metadata,
    Column("crew_member_id", ForeignKey("crew_member.id"), primary_key=True),
    Column("document_id", ForeignKey("document.id"), primary_key=True),
)


crew_member_to_role_table = Table(
    "crew_member_to_role",
    DeclarativeBase.metadata,
    Column("crew_member_id", ForeignKey("crew_member.id"), primary_key=True),
    Column("crew_member_role_id", ForeignKey("crew_member_role.id"), primary_key=True),
)


class CrewMember(Base):
    """Represents a crew member."""
    __tablename__ = "crew_member"

    active = Column(Boolean, default=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    phone = Column(String(50))
    email = Column(String(50))

    # Relationships
    roles = relationship("CrewMemberRole", secondary=crew_member_to_role_table) # type: List[CrewMemberRole]
    documents = relationship("Document", secondary=crew_member_to_document_table) # type: List[Document]
    flights = relationship("CrewMemberToFlight", back_populates="crew_member") # type: list[CrewMemberToFlight]

    def __str__(self) -> str:
        return f"{self.full_name}"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    def can_preform_role(self, role: CrewMemberRole) -> bool:
        """Checks if the crew member can preform a role."""
        for crew_member_to_role in self.roles:
            if crew_member_to_role.role == role:
                return True
        return False

    def add_document(self, document: Document) -> None:
        """Adds a document to the crew member."""
        if document in self.documents:
            return
        self.documents.append(document)
    
    def remove_document(self, document: Document) -> None:
        """Removes a document from the crew member."""
        if document not in self.documents:
            return
        self.documents.remove(document)
    
    def add_role(self, role: CrewMemberRole) -> None:
        """Adds a role to the crew member."""
        if role in self.roles:
            return
        self.roles.append(role)
    
    def remove_role(self, role: CrewMemberRole) -> None:
        """Removes a role from the crew member."""
        if role not in self.roles:
            return
        self.roles.remove(role)
    
    @staticmethod
    def create(session: Session, first_name: str, last_name: str, username: str, phone: str=None, email: str=None) -> 'CrewMember':
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
        if session.query(CrewMember).filter(CrewMember.username == username).first():
            raise errors.CrewMemberExistsError(f"A crew member with the username {username} already exists.")
        new_crew_member = CrewMember(first_name=first_name, last_name=last_name, username=username, phone=phone, email=email)
        return new_crew_member
    
    @staticmethod
    def find_by_username(session: Session, username: str) -> 'CrewMember':
        """Finds a crew member by username."""
        return session.query(CrewMember).filter(CrewMember.username == username).first()


def create_tables():
    logger.info("[SYSTEM] Creating tables...")
    Base.metadata.create_all(engine)


def drop_tables():
    logger.warning("[SYSTEM] Droping tables...")
    Base.metadata.drop_all(engine)


def create_test_data():
    logger.info("[SYSTEM] Creating test data...")
    pass


def force_recreate():
    logger.warning("[SYSTEM] Force recreating database. Data loss will occur.")
    if config.DATABASE_URL_WITHOUT_SCHEMA.startswith("mysql"):
        temp_engine = create_engine(config.DATABASE_URL_WITHOUT_SCHEMA)
        temp_engine.execute(config.SCHEMA_CREATE_STATEMENT)
        temp_engine.dispose()

    drop_tables()
    create_database()


def create_database():
    logger.info("[SYSTEM] Creating database...")
    if config.DATABASE_URL_WITHOUT_SCHEMA.startswith("mysql"):
        temp_engine = create_engine(config.DATABASE_URL_WITHOUT_SCHEMA)
        temp_engine.execute(config.SCHEMA_CREATE_STATEMENT)
        temp_engine.dispose()

    create_tables()