from __future__ import annotations
import os
import logging
from dataclasses import dataclass
from PyQt5.QtCore import QSettings
from .label_template_data import INVENTORY_BARCODE_TEMPLATE


@dataclass
class DefaultSetting:
    """Default settings."""

    settings: QSettings
    name: str
    value: str
    group_name: str = None

    @property
    def hive_location(self) -> str:
        """Return the hive location path for this setting."""
        base = f"HKEY_CURRENT_USER/SOFTWARE/{COMPANY_NAME}/{PROGRAM_NAME}"
        if self.group_name:
            base += f"/{self.group_name}"
        return f"{base}/{self.name}"
    
    @property
    def base_hive_location(self) -> str:
        """Return the base hive location path for this setting."""
        base = f"HKEY_CURRENT_USER/SOFTWARE/{COMPANY_NAME}/{PROGRAM_NAME}"
        if self.group_name:
            base += f"/{self.group_name}"
        return f"{base}"

    def initialize_setting(self) -> DefaultSetting:
        """Initialize the default setting or pulls the current setting value."""
        if self.group_name:
            self.settings.beginGroup(self.group_name)

        if not self.settings.contains(self.name):
            self.settings.setValue(self.name, self.value)
        else:
            self.value = self.settings.value(self.name)

        if self.group_name:
            self.settings.endGroup()
        return self

    def save(self) -> DefaultSetting:
        """Save the default setting."""
        if self.group_name:
            self.settings.beginGroup(self.group_name)

        self.settings.setValue(self.name, self.value)

        if self.group_name:
            self.settings.endGroup()
        return self



COMPANY_NAME = "DF-Software"
PROGRAM_NAME = "Drone Logbook"
PROGRAM_VERSION = "0.0.1"
USER_HOME_FOLDER = os.path.expanduser("~")
COMPANY_FOLDER = os.path.join(USER_HOME_FOLDER, "Documents", COMPANY_NAME)
PROGRAM_FOLDER = os.path.join(COMPANY_FOLDER, PROGRAM_NAME)
LOG_FOLDER = os.path.join(PROGRAM_FOLDER, "Logs")
LABEL_TEMPLATE_FOLDER = os.path.join(PROGRAM_FOLDER, 'Label Templates')
DUMPS_FOLDER = os.path.join(PROGRAM_FOLDER, 'Dumps')


if not os.path.exists(COMPANY_FOLDER):
    os.mkdir(COMPANY_FOLDER)

if not os.path.exists(PROGRAM_FOLDER):
    os.mkdir(PROGRAM_FOLDER)

if not os.path.exists(LOG_FOLDER):
    os.mkdir(LOG_FOLDER)

if not os.path.exists(LABEL_TEMPLATE_FOLDER):
    os.makedirs(LABEL_TEMPLATE_FOLDER)
    with open(os.path.join(LABEL_TEMPLATE_FOLDER, INVENTORY_BARCODE_TEMPLATE["FileName"]), 'w') as f:
        f.write(INVENTORY_BARCODE_TEMPLATE["Data"])

if not os.path.exists(DUMPS_FOLDER):
    os.makedirs(DUMPS_FOLDER)


settings = QSettings(COMPANY_NAME, PROGRAM_NAME)

# Program settings
DATETIME_FORMAT = "%m-%d-%Y %H:%M"
DATE_FORMAT = "%m-%d-%Y"
ENCODING_STR = "utf-8"
THUMBNAIL_HEIGHT, THUMBNAIL_WIDTH = 250, 400
LABEL_PRINTING_ENABLED = True

DEBUG = DefaultSetting(settings=settings, name="debug", value=False).initialize_setting().value
if DEBUG == "true":
    DEBUG = True
else:
    DEBUG = False


# Logging settings
LOG_FILE = f"{PROGRAM_NAME}.log"
SQLALCHEMY_ENGINE_LOG_FILE = "SQLAlchemy Engine.log"
SQLALCHEMY_POOL_LOG_FILE = "SQLAlchemy Pool.log"
SQLALCHEMY_DIALECT_LOG_FILE = "SQLAlchemy Dialect.log"
SQLALCHEMY_ORM_LOG_FILE = "SQLAlchemy ORM.log"

MAX_LOG_SIZE_MB = DefaultSetting(settings=settings, group_name="Logging", name="Max Log Size Mb", value=5).initialize_setting().value
MAX_LOG_COUNT = DefaultSetting(settings=settings, group_name="Logging", name="Max Log Count", value=3).initialize_setting().value
LOG_LEVEL = DefaultSetting(settings=settings, group_name="Logging", name="Log Level", value=logging.INFO).initialize_setting().value
if DEBUG:
    LOG_LEVEL = logging.DEBUG


# Database Settings
SCHEMA_NAME = DefaultSetting(settings=settings, group_name="Database/MySQL", name="Schema Name", value=f"{PROGRAM_NAME.lower().replace(' ', '')}").initialize_setting()
DATABASE_USER = DefaultSetting(settings=settings, group_name="Database/MySQL", name="User", value="").initialize_setting()
DATABASE_PASSWORD = DefaultSetting(settings=settings, group_name="Database/MySQL", name="Password", value="").initialize_setting()
DATABASE_HOST = DefaultSetting(settings=settings, group_name="Database/MySQL", name="Host", value="localhost").initialize_setting()
DATABASE_PORT = DefaultSetting(settings=settings, group_name="Database/MySQL", name="Port", value="3306").initialize_setting()
DATABASE_DUMP_LOCATION = DefaultSetting(settings=settings, group_name="Database/MySQL", name="MySQLDump Location", value="").initialize_setting().value

SCHEMA_CREATE_STATEMENT = f"CREATE DATABASE IF NOT EXISTS {SCHEMA_NAME} DEFAULT CHARACTER SET utf8 COLLATE utf8_bin;"
DATABASE_URL_WITHOUT_SCHEMA = f"mysql+pymysql://{DATABASE_USER.value}:{DATABASE_PASSWORD.value}@{DATABASE_HOST.value}:{DATABASE_PORT.value}"
DATABASE_URL_WITH_SCHEMA = f"{DATABASE_URL_WITHOUT_SCHEMA}/{SCHEMA_NAME}"
FORCE_REBUILD_DATABASE = DefaultSetting(settings=settings, group_name="Database", name="Force Rebuild Database", value=False,).initialize_setting().value
if FORCE_REBUILD_DATABASE == "true":
    FORCE_REBUILD_DATABASE = True
else:
    FORCE_REBUILD_DATABASE = False


# Github settings
GITHUB_USERNAME = "dominickfau"
GITHUB_REPO_NAME = "DroneLogbook"

GITHUB_LATEST_RELEASE_ENDPOINT = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO_NAME}/releases/latest"