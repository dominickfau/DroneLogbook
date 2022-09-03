import logging
import base64
from .config import *
from .database import DBContext
from . import models, errors
from .drone_geometry import imagedata
from dronelogbook import drone_geometry


logger = logging.getLogger("backend")


def load_default_data() -> None:
    logger.info("[SYSTEM] Creating default data...")

    with DBContext() as session:

        # Create Users
        logger.info("[SYSTEM] Checking default Users.")
        user_obj = session.query(models.User).filter(models.User.username == default_user["username"]).first() # type: models.User
        if not user_obj:
            user_obj = models.User(**default_user)
            session.add(user_obj)
            session.commit()
            logger.warning(f"[SYSTEM] Created '{user_obj}'. Default username: '{default_user['username']}, Password: '{default_user['password']}'.")
        else:
            logger.debug(f"[SYSTEM] User '{user_obj}' already exists.")
        
        # Create Uoms
        logger.info("[SYSTEM] Checking Uoms.")
        for uom in uoms:
            obj = session.query(models.Uom).filter(models.Uom.name == uom["name"]).first() # type: models.Uom
            if not obj:
                obj = models.Uom(**uom)
                obj.type_name = uom["type_name"]
                session.add(obj)
                session.commit()
                logger.info(f"[SYSTEM] Created '{obj}'")
            else:
                logger.debug(f"[SYSTEM] Uom '{obj}' already exists.")
        
        # Create UomConversions
        logger.info("[SYSTEM] Checking UomConversions.")
        for uom_conversion in uom_conversions:
            from_uom_name = uom_conversion.pop("from_uom_name", None)
            to_uom_name = uom_conversion.pop("to_uom_name", None)
            from_uom = session.query(models.Uom).filter(models.Uom.name == from_uom_name).first() # type: models.Uom
            to_uom = session.query(models.Uom).filter(models.Uom.name == to_uom_name).first() # type: models.Uom

            if not from_uom or not to_uom:
                logger.error(f"[SYSTEM] Could not find from_uom '{from_uom_name}' and/or to_uom {to_uom_name}.")
                # TODO: Come up with a better error.
                raise Exception(f"Could not find from_uom '{from_uom_name}' and/or to_uom {to_uom_name}.")

            uom_conversion["from_uom_id"] = from_uom.id
            uom_conversion["to_uom_id"] = to_uom.id

            obj = session.query(models.UomConversion).filter_by(from_uom_id=from_uom.id, to_uom_id=to_uom.id).first() # type: models.UomConversion
            if not obj:
                obj = models.UomConversion(**uom_conversion)
                session.add(obj)
                session.commit()
                logger.info(f"[SYSTEM] Created '{obj}'")
            else:
                logger.debug(f"[SYSTEM] UomConversion '{obj}' already exists.")


        # Create LegalRule
        logger.info("[SYSTEM] Checking LegalRules.")
        for rule_name in legal_rules:
            obj = session.query(models.LegalRule).filter(models.LegalRule.name == rule_name).first()
            if not obj:
                obj = models.LegalRule(name=rule_name)
                session.add(obj)
                session.commit()
                logger.info(f"[SYSTEM] Created '{obj}'")
            else:
                logger.debug(f"[SYSTEM] UomConversion '{obj}' already exists.")


        # Create equipment types
        logger.info("[SYSTEM] Checking EquipmentTypes.")
        for equipment_type in equipment_types:
            obj = session.query(models.EquipmentType).filter(models.EquipmentType.name == equipment_type["name"]).first()
            if not obj:
                obj = models.EquipmentType(**equipment_type)
                session.add(obj)
                session.commit()
                logger.info(f"[SYSTEM] Created '{obj}'")
            else:
                logger.debug(f"[SYSTEM] EquipmentType '{obj}' already exists.")


        # Create MaintenanceStatus
        logger.info("[SYSTEM] Checking MaintenanceStatus.")
        for maintenance_status in maintenance_statuses:
            obj = session.query(models.MaintenanceStatus).filter(models.MaintenanceStatus.name == maintenance_status['name']).first()
            if not obj:
                obj = models.MaintenanceStatus(**maintenance_status)
                session.add(obj)
                session.commit()
                logger.info(f"[SYSTEM] Created '{obj}'")
            else:
                logger.debug(f"[SYSTEM] MaintenanceStatus '{obj}' already exists.")


        # Create MaintenanceTaskStatus
        logger.info("[SYSTEM] Checking MaintenanceTaskStatus.")
        for maintenance_task_status in maintenance_task_statuses:
            obj = session.query(models.MaintenanceTaskStatus).filter(models.MaintenanceTaskStatus.name == maintenance_task_status["name"]).first()
            if not obj:
                obj = models.MaintenanceTaskStatus(**maintenance_task_status)
                session.add(obj)
                session.commit()
                logger.info(f"[SYSTEM] Created '{obj}'")
            else:
                logger.debug(f"[SYSTEM] MaintenanceTaskStatus '{obj}' already exists.")


        # Create FlightOperationApproval
        logger.info("[SYSTEM] Checking FlightOperationApprovals.")
        for flight_operation_approval in flight_operation_approvals:
            obj = session.query(models.FlightOperationApproval).filter(models.FlightOperationApproval.name == flight_operation_approval["name"]).first()
            if not obj:
                obj = models.FlightOperationApproval(**flight_operation_approval)
                session.add(obj)
                session.commit()
                logger.info(f"[SYSTEM] Created '{obj}'")
            else:
                obj.description = flight_operation_approval["description"]
                session.commit()
                logger.debug(f"[SYSTEM] FlightOperationApproval '{obj}' already exists. Updating description.")
    

        # Create FlightOperationType
        logger.info("[SYSTEM] Checking FlightOperationTypes.")
        for flight_operation_type in flight_operation_types:
            obj = session.query(models.FlightOperationType).filter(models.FlightOperationType.name == flight_operation_type["name"]).first()
            if not obj:
                obj = models.FlightOperationType(**flight_operation_type)
                session.add(obj)
                session.commit()
                logger.info(f"[SYSTEM] Created '{obj}'")
            else:
                obj.description = flight_operation_type["description"]
                session.commit()
                logger.debug(f"[SYSTEM] FlightOperationType '{obj}' already exists. Updating description.")


        # Create FlightType
        logger.info("[SYSTEM] Checking FlightTypes.")
        for flight_type in flight_types:
            flight_operation_type = session.query(models.FlightOperationType).filter_by(name=flight_type["flight_operation_type_name"]).first()
            if not flight_operation_type:
                raise errors.LoadDefaultDataError(f"Could not find flight operation type '{flight_type['flight_operation_type_name']}'.")
            
            flight_type.pop("flight_operation_type_name", None)
            flight_type["flight_operation_type"] = flight_operation_type

            obj = session.query(models.FlightType).filter(models.FlightType.name == flight_type["name"]).first()
            if not obj:
                obj = models.FlightType(**flight_type)
                session.add(obj)
                session.commit()
                logger.info(f"[SYSTEM] Created '{obj}'")
            else:
                obj.description = flight_type["description"]
                session.commit()
                logger.debug(f"[SYSTEM] FlightType '{obj}' already exists. Updating description.")


        # Create FlightStatus
        logger.info("[SYSTEM] Checking FlightStatus.")
        for flight_status in flight_statuses:
            obj = session.query(models.FlightStatus).filter(models.FlightStatus.name == flight_status["name"]).first()
            if not obj:
                obj = models.FlightStatus(**flight_status)
                session.add(obj)
                session.commit()
                logger.info(f"[SYSTEM] Created '{obj}'")
            else:
                logger.debug(f"[SYSTEM] FlightStatus '{obj}' already exists.")


        # Create Images
        logger.info("[SYSTEM] Checking Images.")
        for file in imagedata.data:
            data = imagedata.data[file]
            image_data = models.Image.convert_from_base64(data) # type: models.ImageData
            image = models.Image.find_by_name(session, image_data.database_name)
            if not image:
                image = models.Image(name=image_data.database_name, data=image_data.data, file_extention=image_data.file_extension, read_only=True)
                session.add(image)
                logger.info(f"[SYSTEM] Created Image '{image}'")
            else:
                logger.debug(f"[SYSTEM] Image '{image}' already exists.")
        session.commit()


        # Create DroneGeometry
        logger.info("[SYSTEM] Checking DroneGeometry.")
        for drone_geometry in drone_geometries:
            obj = session.query(models.DroneGeometry).filter(models.DroneGeometry.name == drone_geometry["name"]).first()
            if not obj:
                image_name = drone_geometry.pop("image_name", None)
                image = session.query(models.Image).filter(models.Image.name == image_name).first()
                if not image:
                    raise errors.LoadDefaultDataError(f"Could not find image '{image_name}'.")
                drone_geometry['image'] = image
                obj = models.DroneGeometry(**drone_geometry)
                session.add(obj)
                session.commit()
                logger.info(f"[SYSTEM] Created '{obj}'")
            else:
                logger.debug(f"[SYSTEM] DroneGeometry '{obj}' already exists.")



default_user = {
    "first_name": "Admin",
    "last_name": "User",
    "username": "admin",
    "password": "admin"
}


uoms = [
    {
        "code": "ea",
        "description": "A single item.",
        "name": "Each",
        "read_only": True,
        "type_name": "Count"
    },
    {
        "code": "ft",
        "description": "Basic US unit of length.",
        "name": "Foot",
        "read_only": True,
        "type_name": "Length"
    },
    {
        "code": "lbs",
        "description": "Basic US unit of weight.",
        "name": "Pound",
        "read_only": True,
        "type_name": "Weight"
    },
    {
        "code": "hr",
        "description": "Basic unit of time.",
        "name": "Hour",
        "read_only": True,
        "type_name": "Time"
    },
    {
        "code": "gal",
        "description": "Basic US unit of liquid volume.",
        "name": "Gallon",
        "type_name": "Volume"
    },
    {
        "code": "floz",
        "description": "US unit of liquid volume.",
        "name": "Fluid Ounce",
        "type_name": "Volume"
    },
    {
        "code": "in",
        "description": "US unit of length.",
        "name": "Inch",
        "read_only": True,
        "type_name": "Length"
    },
    {
        "code": "in",
        "description": "US unit of length.",
        "name": "Inch",
        "read_only": True,
        "type_name": "Length"
    },
    {
        "code": "kg",
        "description": "Metric unit of weight.",
        "name": "Kilogram",
        "read_only": True,
        "type_name": "Weight"
    },
    {
        "code": "oz",
        "description": "US unit of weight.",
        "name": "Ounce",
        "read_only": True,
        "type_name": "Weight"
    },
    {
        "code": "m",
        "description": "Basic metric unit of length.",
        "name": "Meter",
        "read_only": True,
        "type_name": "Length"
    },
    {
        "code": "L",
        "description": "Basic metric unit of liquid volume.",
        "name": "Liter",
        "read_only": True,
        "type_name": "Volume"
    },
    {
        "code": "mm",
        "description": "1/1000 of a meter.",
        "name": "Millimeter",
        "type_name": "Length"
    },
    {
        "code": "cm",
        "description": "1/100 of a meter.",
        "name": "Centimeter",
        "type_name": "Length"
    },
    {
        "code": "km",
        "description": "1000 meters.",
        "name": "Kilometer",
        "type_name": "Length"
    },
    {
        "code": "g",
        "description": "Metric unit of weight.",
        "name": "Gram",
        "type_name": "Weight"
    },
    {
        "code": "mg",
        "description": "1/1000 of a gram.",
        "name": "Milligram",
        "type_name": "Weight"
    },
    {
        "code": "mL",
        "description": "1/1000 of a Liter.",
        "name": "Milliliter",
        "type_name": "Volume"
    },
    {
        "code": "min",
        "description": "1/60 of a hour.",
        "name": "Minute",
        "type_name": "Time"
    },
    {
        "code": "yd",
        "description": "Basic US unit of length.",
        "name": "Yard",
        "type_name": "Length"
    }
]


uom_conversions = [
    {
        "description": "1 Foot = 12 Inch",
        "from_uom_name": "Foot",
        "to_uom_name": "Inch",
        "factor": 1,
        "multiply": 12
    },
    {
        "description": "12 Inch = 1 Foot",
        "from_uom_name": "Inch",
        "to_uom_name": "Foot",
        "factor": 12,
        "multiply": 1
    },
    {
        "description": "1 Gallon = 128 Fluid Ounce",
        "from_uom_name": "Gallon",
        "to_uom_name": "Fluid Ounce",
        "factor": 1,
        "multiply": 128
    },
    {
        "description": "128 Fluid Ounce = 1 Gallon",
        "from_uom_name": "Fluid Ounce",
        "to_uom_name": "Gallon",
        "factor": 128,
        "multiply": 1
    },
    {
        "description": "2.2046 Pound = 1 Kilogram",
        "from_uom_name": "Pound",
        "to_uom_name": "Kilogram",
        "factor": 2.2046,
        "multiply": 1
    },
    {
        "description": "1 Kilogram = 2.2046 Pound",
        "from_uom_name": "Kilogram",
        "to_uom_name": "Pound",
        "factor": 1,
        "multiply": 2.2046
    },
    {
        "description": "3.2808 Foot = 1 Meter",
        "from_uom_name": "Foot",
        "to_uom_name": "Meter",
        "factor": 3.2808,
        "multiply": 1
    },
    {
        "description": "1 Meter = 3.2808 Foot",
        "from_uom_name": "Meter",
        "to_uom_name": "Foot",
        "factor": 1,
        "multiply": 3.2808
    },
    {
        "description": "3.7854 Liter = 1 Gallon",
        "from_uom_name": "Liter",
        "to_uom_name": "Gallon",
        "factor": 3.7854,
        "multiply": 1
    },
    {
        "description": "1 Gallon = 3.7854 Liter",
        "from_uom_name": "Gallon",
        "to_uom_name": "Liter",
        "factor": 1,
        "multiply": 3.7854
    },
    {
        "description": "1 Meter = 1000 Millimeter",
        "from_uom_name": "Meter",
        "to_uom_name": "Millimeter",
        "factor": 1,
        "multiply": 1000
    },
    {
        "description": "1000 Millimeter = 1 Meter",
        "from_uom_name": "Millimeter",
        "to_uom_name": "Meter",
        "factor": 1000,
        "multiply": 1
    },
    {
        "description": "1 Meter = 100 Centimeter",
        "from_uom_name": "Meter",
        "to_uom_name": "Centimeter",
        "factor": 1,
        "multiply": 100
    },
    {
        "description": "100 Centimeter = 1 Meter",
        "from_uom_name": "Centimeter",
        "to_uom_name": "Meter",
        "factor": 100,
        "multiply": 1
    },
    {
        "description": "1 Kilometer = 1000 Meter",
        "from_uom_name": "Kilometer",
        "to_uom_name": "Meter",
        "factor": 1,
        "multiply": 1000
    },
    {
        "description": "1000 Meter = 1 Kilometer",
        "from_uom_name": "Meter",
        "to_uom_name": "Kilometer",
        "factor": 1000,
        "multiply": 1
    },
    {
        "description": "1 Gram = 1000 Milligram",
        "from_uom_name": "Gram",
        "to_uom_name": "Milligram",
        "factor": 1,
        "multiply": 1000
    },
    {
        "description": "1000 Milligram = 1 Gram",
        "from_uom_name": "Milligram",
        "to_uom_name": "Gram",
        "factor": 1000,
        "multiply": 1
    },
    {
        "description": "1 Kilogram = 1000 Gram",
        "from_uom_name": "Kilogram",
        "to_uom_name": "Gram",
        "factor": 1,
        "multiply": 1000
    },
    {
        "description": "1000 Gram = 1 Kilogram",
        "from_uom_name": "Gram",
        "to_uom_name": "Kilogram",
        "factor": 1000,
        "multiply": 1
    },
    {
        "description": "1 Liter = 1000 Milliliter",
        "from_uom_name": "Liter",
        "to_uom_name": "Milliliter",
        "factor": 1,
        "multiply": 1000
    },
    {
        "description": "1000 Milliliter = 1 Liter",
        "from_uom_name": "Milliliter",
        "to_uom_name": "Liter",
        "factor": 1000,
        "multiply": 1
    },
    {
        "description": "1 Inch = 25.4 Millimeter",
        "from_uom_name": "Inch",
        "to_uom_name": "Millimeter",
        "factor": 1,
        "multiply": 25.4
    },
    {
        "description": "25.4 Millimeter = 1 Inch",
        "from_uom_name": "Millimeter",
        "to_uom_name": "Inch",
        "factor": 25.4,
        "multiply": 1
    },
    {
        "description": "1 Pound = 453.59237 Gram",
        "from_uom_name": "Pound",
        "to_uom_name": "Gram",
        "factor": 1,
        "multiply": 453.59237
    },
    {
        "description": "453.59237 Gram = 1 Pound",
        "from_uom_name": "Gram",
        "to_uom_name": "Pound",
        "factor": 453.59237,
        "multiply": 1
    },
    {
        "description": "1 Pound = 453592.37 Milligram",
        "from_uom_name": "Pound",
        "to_uom_name": "Milligram",
        "factor": 1,
        "multiply": 453592.37
    },
    {
        "description": "453592.37 Milligram = 1 Pound",
        "from_uom_name": "Milligram",
        "to_uom_name": "Pound",
        "factor": 453592.37,
        "multiply": 1
    },
    {
        "description": "1 Pound = 16 Ounce",
        "from_uom_name": "Pound",
        "to_uom_name": "Ounce",
        "factor": 1,
        "multiply": 16
    },
    {
        "description": "16 Ounce = 1 Pound",
        "from_uom_name": "Ounce",
        "to_uom_name": "Pound",
        "factor": 16,
        "multiply": 1
    },
    {
        "description": "91.44 Centimeter = 1 Yard",
        "from_uom_name": "Centimeter",
        "to_uom_name": "Yard",
        "factor": 91.44,
        "multiply": 1
    },
    {
        "description": "1 Yard = 91.44 Centimeter",
        "from_uom_name": "Yard",
        "to_uom_name": "Centimeter",
        "factor": 1,
        "multiply": 91.44
    },
    {
        "description": "0.9144 Meter = 1 Yard",
        "from_uom_name": "Meter",
        "to_uom_name": "Yard",
        "factor": 0.9144,
        "multiply": 1
    },
    {
        "description": "1 Yard = 0.9144 Meter",
        "from_uom_name": "Yard",
        "to_uom_name": "Meter",
        "factor": 1,
        "multiply": 0.9144
    },
    {
        "description": "36 Inch = 1 Yard",
        "from_uom_name": "Inch",
        "to_uom_name": "Yard",
        "factor": 36,
        "multiply": 1
    },
    {
        "description": "1 Yard = 36 Inch",
        "from_uom_name": "Yard",
        "to_uom_name": "Inch",
        "factor": 1,
        "multiply": 36
    },
    {
        "description": "3 Foot = 1 Yard",
        "from_uom_name": "Foot",
        "to_uom_name": "Yard",
        "factor": 3,
        "multiply": 1
    },
    {
        "description": "1 Yard = 3 Foot",
        "from_uom_name": "Yard",
        "to_uom_name": "Foot",
        "factor": 1,
        "multiply": 3
    },
    {
        "description": "914.4 Millimeter = 1 Yard",
        "from_uom_name": "Millimeter",
        "to_uom_name": "Yard",
        "factor": 914.4,
        "multiply": 1
    },
    {
        "description": "1 Yard = 914.4 Millimeter",
        "from_uom_name": "Yard",
        "to_uom_name": "Millimeter",
        "factor": 1,
        "multiply": 914.4
    },
    {
        "description": "1 Hour = 60 Minute",
        "from_uom_name": "Hour",
        "to_uom_name": "Minute",
        "factor": 1,
        "multiply": 60
    },
    {
        "description": "60 Minute = 1 Hour",
        "from_uom_name": "Minute",
        "to_uom_name": "Hour",
        "factor": 60,
        "multiply": 1
    }
]


legal_rules = [
    "Not Required",
    "Part 107"
]


equipment_types = [
    {
        "name": "Airframe",
        "group": "Airborne"
    },
    {
        "name": "Anenometer",
        "group": "Ground"
    },
    {
        "name": "Battery",
        "group": "Airborne"
    },
    {
        "name": "Charger",
        "group": "Ground"
    },
    {
        "name": "Camera",
        "group": "Airborne"
    },
    {
        "name": "Cradle",
        "group": "Ground"
    },
    {
        "name": "Drive (Disk, Flash, etc.)",
        "group": "Ground"
    },
    {
        "name": "FPV Glasses",
        "group": "Ground"
    },
    {
        "name": "GPS",
        "group": "Ground"
    },
    {
        "name": "Lens",
        "group": "Airborne"
    },
    {
        "name": "Light",
        "group": "Airborne"
    },
    {
        "name": "Monitor",
        "group": "Ground"
    },
    {
        "name": "Motor",
        "group": "Airborne"
    },
    {
        "name": "Parachute",
        "group": "Airborne"
    },
    {
        "name": "Phone / Tablet",
        "group": "Ground"
    },
    {
        "name": "Power Supply",
        "group": "Ground"
    },
    {
        "name": "Prop Guards",
        "group": "Airborne"
    },
    {
        "name": "Propeller",
        "group": "Airborne"
    },
    {
        "name": "Radio Receiver",
        "group": "Ground"
    },
    {
        "name": "Radio Transmitter",
        "group": "Ground"
    },
    {
        "name": "Range Extender",
        "group": "Airborne"
    },
    {
        "name": "Laser Range Finder",
        "group": "Airborne"
    },
    {
        "name": "Remote Controller",
        "group": "Airborne"
    },
    {
        "name": "Sensor",
        "group": "Airborne"
    },
    {
        "name": "Spreader",
        "group": "Airborne"
    },
    {
        "name": "Telemetry Radio",
        "group": "Airborne"
    },
    {
        "name": "Tripod",
        "group": "Ground"
    },
    {
        "name": "Video Transmitter",
        "group": "Airborne"
    },
    {
        "name": "Other Ground",
        "group": "Ground"
    }
]


maintenance_statuses = [
    {
        "id": 10,
        "name": "Open"
    },
    {
        "id": 20,
        "name": "Scheduled"
    },
    {
        "id": 30,
        "name": "InProgress"
    },
    {
        "id": 40,
        "name": "Finished"
    }
]


maintenance_task_statuses = [
    {
        "id": 10,
        "name": "Open"
    },
    {
        "id": 20,
        "name": "Partial"
    },
    {
        "id": 30,
        "name": "Finished"
    }
]


flight_operation_approvals = [
    {
        "name": "Not Required",
        "description": "No approval required."
    },
    {
        "name": "Controlled Airspace Area",
        "description": "Approval for flight operations that will be within controlled airspace."
    },
    {
        "name": "Over People",
        "description": "Approval for flight operations that will be over people."
    },
    {
        "name": "Parcel Delivery",
        "description": "Approval for flight operations that will be delivering parcels."
    }
]


flight_operation_types = [
    {
        "name": "VLOS Manual",
        "description": "Maintain manual VLOS for the duration of the flight."
    },
    {
        "name": "BVLOS",
        "description": "Remote PIC must comply with part 108 when flying."
    }
]


flight_types = [
    {
        "name": "Commercial - Agriculture",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
    {
        "name": "Commercial - Inspection",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
    {
        "name": "Commercial - Mapping",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
    {
        "name": "Commercial - Survey",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
    {
        "name": "Commercial - Photo/Video",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
    {
        "name": "Commercial - Other",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
    {
        "name": "Emergency",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
    {
        "name": "Hobby - Entertainment",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
    {
        "name": "Maintenance",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
    {
        "name": "Mapping - HR",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
    {
        "name": "Mapping - UHR",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
    {
        "name": "Photogrammetry",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
    {
        "name": "Science",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
    {
        "name": "Search & Rescue",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
    {
        "name": "Simulator",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
    {
        "name": "Situational Awareness",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
    {
        "name": "Spreading",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
    {
        "name": "Survaliance",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
    {
        "name": "Test Flight",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
    {
        "name":"Training",
        "flight_operation_type_name": "VLOS Manual",
        "description": ""
    },
]

flight_statuses = [
    {
        "id": 10,
        "name": "Entered"
    },
    {
        "id": 20,
        "name": "InProgress"
    },
    {
        "id": 30,
        "name": "Completed"
    }
]

drone_geometries = [
    {
        "name": "Fixed Wing 1",
        "description": "A fixed wing drone with one propeller on the front nose.",
        "image_name": "Fixed Wing 1",
        "number_of_propellers": 1,
        "thrust_direction": "Horizontal"
    },
    {
        "name": "Fixed Wing 2",
        "description": "A fixed wing drone with one propeller on the back.",
        "image_name": "Fixed Wing 2",
        "number_of_propellers": 1,
        "thrust_direction": "Horizontal"
    },
    {
        "name": "Hexa Plus",
        "description": "A drone with six propellers, starting from the front.",
        "image_name": "Hexa Plus",
        "number_of_propellers": 6,
        "alternating_rotaion": True
    },
    {
        "name": "Hexa X",
        "description": "A drone with six propellers, starting from the front right.",
        "image_name": "Hexa X",
        "number_of_propellers": 6,
        "alternating_rotaion": True
    },
    {
        "name": "Octa Plus",
        "description": "A drone with eight propellers, starting from the front.",
        "image_name": "Octa Plus",
        "number_of_propellers": 8,
        "alternating_rotaion": True
    },
    {
        "name": "Octa V",
        "description": "A drone with eight propellers, a row on each side in the shape o a V.",
        "image_name": "Octa V",
        "number_of_propellers": 8,
        "alternating_rotaion": True
    },
    {
        "name": "Octa X",
        "description": "A drone with eight propellers, starting from the front right.",
        "image_name": "Octa X",
        "number_of_propellers": 8,
        "alternating_rotaion": True
    },
    {
        "name": "Quad Plus",
        "description": "A drone with four propellers, starting from the front.",
        "image_name": "Quad Plus",
        "number_of_propellers": 4,
        "alternating_rotaion": True
    },
    {
        "name": "Quad X",
        "description": "A drone with four propellers, starting from the front right.",
        "image_name": "Quad X",
        "number_of_propellers": 4,
        "alternating_rotaion": True
    },
    {
        "name": "Single Coaxial",
        "description": "A drone with two propellers on the top.",
        "image_name": "Single Coaxial",
        "number_of_propellers": 2,
        "alternating_rotaion": True
    },
    {
        "name": "Single Rotor",
        "description": "A drone with one propeller on the top.",
        "image_name": "Single Rotor",
        "number_of_propellers": 1
    },
    {
        "name": "Tri",
        "description": "A drone with three propellers, starting from the front right in the shape of a Y.",
        "image_name": "Tri",
        "number_of_propellers": 3
    },
    {
        "name": "VTOL 1",
        "description": "A drone / air plane hybrid.",
        "image_name": "VTOL 1",
        "number_of_propellers": 5,
        "alternating_rotaion": True,
        "thrust_direction": "Horizontal"
    },
    {
        "name": "VTOL 2",
        "description": "An air plane with 2 propellers on the wings.",
        "image_name": "VTOL 2",
        "number_of_propellers": 2,
        "thrust_direction": "Vertical"
    },
    {
        "name": "VTOL 3",
        "description": "A drone / air plane hybrid, starting from the front right in the shape of a Y.",
        "image_name": "VTOL 3",
        "number_of_propellers": 6,
        "alternating_rotaion": True
    },
    {
        "name": "X8 Coaxial",
        "description": "A drone with eight propellers, similar to a Quad Plus, but with popellers top and bottom.",
        "image_name": "X8 Coaxial",
        "number_of_propellers": 8,
        "alternating_rotaion": True
    },
    {
        "name": "Y6 Coaxial",
        "description": "A drone with six propellers, similar to a Tri, but with popellers top and bottom.",
        "image_name": "Y6 Coaxial",
        "number_of_propellers": 6,
        "alternating_rotaion": True
    }
]


# data = [
#     BatteryChemistry(
#         name="Lithium Ion",
#         code="Li-Ion",
#         description="Lithium Ion battery chemistry.",
#         unrecoverable_low_cell_voltage=3.0,
#         nominal_cell_voltage=3.7,
#         safe_min_cell_voltage=3.3,
#         max_cell_voltage=4.2,
#         min_temperature=20,
#         max_temperature=40,
#         max_charge_current=2.5,
#         max_discharge_current=2.5,
#         esr=0.5
#     ),
#     BatteryChemistry(
#         name="Lithium Polymer",
#         code="Li-Po",
#         description="Lithium Polymer battery chemistry.",
#         unrecoverable_low_cell_voltage=3.2,
#         nominal_cell_voltage=3.7,
#         safe_min_cell_voltage=3.3,
#         max_cell_voltage=4.2,
#         min_temperature=20,
#         max_temperature=40,
#         max_charge_current=2.5,
#         max_discharge_current=2.5,
#         esr=0.5
#     ),
#     BatteryChemistry(
#         name="Nickel Cadmium",
#         code="NiCd",
#         description="Nickel Cadmium battery chemistry.",
#         unrecoverable_low_cell_voltage=3.2,
#         nominal_cell_voltage=3.7,
#         safe_min_cell_voltage=3.3,
#         max_cell_voltage=4.2,
#         min_temperature=20,
#         max_temperature=40,
#         max_charge_current=2.5,
#         max_discharge_current=2.5,
#         esr=0.5
#     ),
#     BatteryChemistry(
#         name="Nickel Metal Hydride",
#         code="NiMH",
#         description="Nickel Metal Hydride battery chemistry.",
#         unrecoverable_low_cell_voltage=3.2,
#         nominal_cell_voltage=3.7,
#         safe_min_cell_voltage=3.3,
#         max_cell_voltage=4.2,
#         min_temperature=20,
#         max_temperature=40,
#         max_charge_current=2.5,
#         max_discharge_current=2.5,
#         esr=0.5
#     ),
# ]

# data = [
#     CrewMemberRole(name=CrewMemberRole.Approved_Delegate, description="A crew member who is approved to fly a drone."),
#     CrewMemberRole(name=CrewMemberRole.Ground_Support, description="A crew member who is responsible for ground support."),
#     CrewMemberRole(name=CrewMemberRole.Maintenance_Controller, description="A crew member who is responsible for maintenance."),
#     CrewMemberRole(name=CrewMemberRole.Observer, description="A crew member who is responsible for keeping VLOS of the drone during flight."),
#     CrewMemberRole(name=CrewMemberRole.Payload_Controller, description="A crew member who is responsible for payload control."),
#     CrewMemberRole(name=CrewMemberRole.Pilot, description="A crew member who is responsible for flying the drone."),
#     CrewMemberRole(name=CrewMemberRole.Student, description="A crew member who is a student learning."),
#     CrewMemberRole(name=CrewMemberRole.Remote_Pilot_In_Command, required_for_flight=True, description="A crew member who holds a remote pilot certificate with an sUAS rating and has the final authority and responsibility for the operation and safety of an sUAS operation conducted under part 107.")
# ]

# data = [
#     DocumentType(name="Pilot Registration", description="A document that shows the pilot's registration."),
#     DocumentType(name="Pilot License", description="A document that shows the pilot's license."),
#     DocumentType(name="Remote Pilot Certificate", description="A document that shows the remote pilot's certificate."),
#     DocumentType(name="Medical Certificate", description="A document that shows the medical certificate."),
#     DocumentType(name="Other", description="A document that shows other documents.")
# ]