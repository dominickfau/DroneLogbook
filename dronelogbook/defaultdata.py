import logging
from .config import *
from .database import DBContext
from . import models


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
            uom_obj = session.query(models.Uom).filter(models.Uom.name == uom["type_name"]).first() # type: models.Uom
            if not uom_obj:
                uom_obj = models.Uom(**uom)
                uom_obj.type_name = uom["type_name"]
                session.add(uom_obj)
                session.commit()
                logger.info(f"[SYSTEM] Created '{uom_obj}'")
            else:
                logger.debug(f"[SYSTEM] Uom '{uom['name']}' already exists.")
        
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

            uom_conversion_obj = session.query(models.UomConversion).filter_by(from_uom_id=from_uom.id, to_uom_id=to_uom.id).first() # type: models.UomConversion
            if not uom_conversion_obj:
                uom_conversion_obj = models.UomConversion(**uom_conversion)
                uom_conversion_obj.created_by_user = user_obj
                uom_conversion_obj.modified_by_user = user_obj
                session.add(uom_conversion_obj)
                session.commit()
                logger.info(f"[SYSTEM] Created '{uom_conversion_obj}'")
            else:
                logger.debug(f"[SYSTEM] UomConversion '{uom_conversion_obj}' already exists.")


        # Create LegalRule
        logger.info("[SYSTEM] Checking LegalRules.")
        for rule_name in legal_rules:
            obj = session.query(models.LegalRule).filter(models.LegalRule.name == rule_name).first()
            if not obj:
                session.add(models.LegalRule(name=rule_name))
                session.commit()
                logger.info(f"[SYSTEM] Created '{obj}'")
            else:
                logger.debug(f"[SYSTEM] UomConversion '{obj}' already exists.")


        # Create equipment types
        logger.info("[SYSTEM] Checking EquipmentTypes.")
        for equipment_type in equipment_types:
            obj = session.query(models.EquipmentType).filter(models.EquipmentType.name == equipment_type["name"]).first()
            if not obj:
                session.add(models.EquipmentType(*equipment_type))
                session.commit()
                logger.info(f"[SYSTEM] Created '{obj}'")
            else:
                logger.debug(f"[SYSTEM] EquipmentType '{obj}' already exists.")


        # Create MaintenanceStatus
        logger.info("[SYSTEM] Checking MaintenanceStatus.")
        for maintenance_status in maintenance_statuses:
            obj = session.query(models.MaintenanceStatus).filter(models.MaintenanceStatus.name == maintenance_status).first()
            if not obj:
                session.add(models.MaintenanceStatus(name=maintenance_status))
                session.commit()
                logger.info(f"[SYSTEM] Created '{obj}'")
            else:
                logger.debug(f"[SYSTEM] MaintenanceStatus '{obj}' already exists.")


        # Create MaintenanceTaskStatus
        logger.info("[SYSTEM] Checking MaintenanceTaskStatus.")
        for maintenance_task_status in maintenance_task_statuses:
            obj = session.query(models.MaintenanceTaskStatus).filter(models.MaintenanceTaskStatus.name == maintenance_task_status["name"]).first()
            if not obj:
                session.add(models.MaintenanceTaskStatus(*maintenance_task_status))
                session.commit()
                logger.info(f"[SYSTEM] Created '{obj}'")
            else:
                logger.debug(f"[SYSTEM] MaintenanceTaskStatus '{obj}' already exists.")


        # Create FlightOperationApproval
        logger.info("[SYSTEM] Checking FlightOperationApprovals.")
        for flight_operation_approval in flight_operation_approvals:
            obj = session.query(models.FlightOperationApproval).filter(models.FlightOperationApproval.name == flight_operation_approval["name"]).first()
            if not obj:
                session.add(models.FlightOperationApproval(*flight_operation_approval))
                session.commit()
                logger.info(f"[SYSTEM] Created '{uom_conversion_obj}'")
            else:
                obj.description = flight_operation_approval["description"]
                session.commit()
                logger.debug(f"[SYSTEM] FlightOperationApproval '{obj}' already exists. Updating description.")
    

        # Create FlightOperationType
        logger.info("[SYSTEM] Checking FlightOperationTypes.")
        for flight_operation_type in flight_operation_types:
            obj = session.query(models.FlightOperationType).filter(models.FlightOperationType.name == flight_operation_type["name"]).first()
            if not obj:
                session.add(models.FlightOperationType(*flight_operation_type))
                session.commit()
                logger.info(f"[SYSTEM] Created '{uom_conversion_obj}'")
            else:
                obj.description = flight_operation_type["description"]
                session.commit()
                logger.debug(f"[SYSTEM] FlightOperationType '{obj}' already exists. Updating description.")


        # Create FlightType
        logger.info("[SYSTEM] Checking FlightTypes.")
        for flight_type in flight_types:
            obj = session.query(models.FlightType).filter(models.FlightType.name == flight_type["name"]).first()
            if not obj:
                session.add(models.FlightType(*flight_type))
                session.commit()
                logger.info(f"[SYSTEM] Created '{uom_conversion_obj}'")
            else:
                obj.description = flight_type["description"]
                session.commit()
                logger.debug(f"[SYSTEM] FlightType '{obj}' already exists. Updating description.")


        # Create FlightStatus
        logger.info("[SYSTEM] Checking FlightStatus.")
        for flight_status in flight_statuses:
            obj = session.query(models.FlightStatus).filter(models.FlightStatus.name == flight_status["name"]).first()
            if not obj:
                session.add(models.FlightStatus(*flight_status))
                session.commit()
                logger.info(f"[SYSTEM] Created '{obj}'")
            else:
                logger.debug(f"[SYSTEM] FlightStatus '{obj}' already exists.")

        # Create Images
        logger.info("[SYSTEM] Checking Images.")
        for root, dirs, files in os.walk(DRONE_GEOMETRY_IMAGE_FOLDER):
            for file in files:
                image_data = models.Image.convert_to_bytes(os.path.join(root, file)) # type: models.ImageData
                image_data.file_name = image_data.file_name.replace("_", " ")
                if not models.Image.find_by_name(image_data.file_name):
                    image = models.Image(name=image_data.file_name, data=image_data.data, file_extention=image_data.file_extension, read_only=True)
                    session.add(image)
                    logger.info(f"[SYSTEM] Created Image '{image_data.file_name}.{image_data.file_extension}'")
                else:
                    logger.debug(f"[SYSTEM] Image '{image_data.file_name}.{image_data.file_extension}' already exists.")
        session.commit()



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
        "group": "Airborne Equipment"
    },
    {
        "name": "Anenometer",
        "group": "Ground Equipment"
    },
    {
        "name": "Battery",
        "group": "Airborne Equipment"
    },
    {
        "name": "Charger",
        "group": "Ground Equipment"
    },
    {
        "name": "Camera",
        "group": "Airborne Equipment"
    },
    {
        "name": "Cradle",
        "group": "Ground Equipment"
    },
    {
        "name": "Drive (Disk, Flash, etc.)",
        "group": "Ground Equipment"
    },
    {
        "name": "FPV Glasses",
        "group": "Ground Equipment"
    },
    {
        "name": "GPS",
        "group": "Ground Equipment"
    },
    {
        "name": "Lens",
        "group": "Airborne Equipment"
    },
    {
        "name": "Light",
        "group": "Airborne Equipment"
    },
    {
        "name": "Monitor",
        "group": "Ground Equipment"
    },
    {
        "name": "Motor",
        "group": "Airborne Equipment"
    },
    {
        "name": "Parachute",
        "group": "Airborne Equipment"
    },
    {
        "name": "Phone / Tablet",
        "group": "Ground Equipment"
    },
    {
        "name": "Power Supply",
        "group": "Ground Equipment"
    },
    {
        "name": "Prop Guards",
        "group": "Airborne Equipment"
    },
    {
        "name": "Propeller",
        "group": "Airborne Equipment"
    },
    {
        "name": "Radio Receiver",
        "group": "Ground Equipment"
    },
    {
        "name": "Radio Transmitter",
        "group": "Ground Equipment"
    },
    {
        "name": "Range Extender",
        "group": "Airborne Equipment"
    },
    {
        "name": "Laser Range Finder",
        "group": "Airborne Equipment"
    },
    {
        "name": "Remote Controller",
        "group": "Airborne Equipment"
    },
    {
        "name": "Sensor",
        "group": "Airborne Equipment"
    },
    {
        "name": "Spreader",
        "group": "Airborne Equipment"
    },
    {
        "name": "Telemetry Radio",
        "group": "Airborne Equipment"
    },
    {
        "name": "Tripod",
        "group": "Ground Equipment"
    },
    {
        "name": "Video Transmitter",
        "group": "Airborne Equipment"
    },
    {
        "name": "Other Ground",
        "group": "Ground Equipment"
    }
]


maintenance_statuses = [
    "Scheduled",
    "InProgress",
    "Completed",
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
        "name": "Done"
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
        "description": ""
    },
    {
        "name": "Commercial - Inspection",
        "description": ""
    },
    {
        "name": "Commercial - Mapping",
        "description": ""
    },
    {
        "name": "Commercial - Survey",
        "description": ""
    },
    {
        "name": "Commercial - Photo/Video",
        "description": ""
    },
    {
        "name": "Commercial - Other",
        "description": ""
    },
    {
        "name": "Emergency",
        "description": ""
    },
    {
        "name": "Hobby - Entertainment",
        "description": ""
    },
    {
        "name": "Maintenance",
        "description": ""
    },
    {
        "name": "Mapping - HR",
        "description": ""
    },
    {
        "name": "Mapping - UHR",
        "description": ""
    },
    {
        "name": "Photogrammetry",
        "description": ""
    },
    {
        "name": "Science",
        "description": ""
    },
    {
        "name": "Search & Rescue",
        "description": ""
    },
    {
        "name": "Simulator",
        "description": ""
    },
    {
        "name": "Situational Awareness",
        "description": ""
    },
    {
        "name": "Spreading",
        "description": ""
    },
    {
        "name": "Survaliance",
        "description": ""
    },
    {
        "name": "Test Flight",
        "description": ""
    },
    {
        "name":"Training",
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

data = [
    DroneGeometry(name="Fixed Wing 1",
                    description="A fixed wing drone with one propeller on the front nose.",
                    image_id=Image.find_by_name("Fixed Wing 1").id,
                    number_of_propellers=1,thrust_direction="Horizontal"
                    ),
    DroneGeometry(name="Fixed Wing 2",
                    description="A fixed wing drone with one propeller on the back.",
                    image_id=Image.find_by_name("Fixed Wing 2").id,
                    number_of_propellers=1,thrust_direction="Horizontal"
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
                    thrust_direction="Horizontal"
                    ),
    DroneGeometry(name="VTOL 2",
                    description="An air plane with 2 propellers on the wings.",
                    image_id=Image.find_by_name("VTOL 2").id,
                    number_of_propellers=2,
                    thrust_direction="Vertical"
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

data = [
    DocumentType(name="Pilot Registration", description="A document that shows the pilot's registration."),
    DocumentType(name="Pilot License", description="A document that shows the pilot's license."),
    DocumentType(name="Remote Pilot Certificate", description="A document that shows the remote pilot's certificate."),
    DocumentType(name="Medical Certificate", description="A document that shows the medical certificate."),
    DocumentType(name="Other", description="A document that shows other documents.")
]