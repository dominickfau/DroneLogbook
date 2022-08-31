import random
import string
import string
from PyQt5.QtWidgets import QLineEdit
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.decl_api import _DeclarativeBase


def clean_text_input(widget: QLineEdit):
    """Strips text from widget."""
    widget.setText(widget.text().strip())


def generate_random_string(check_table: _DeclarativeBase, limit=13) -> str:
    """Generates a unique random string. To be used in the database.

    Args:
        check_table (_DeclarativeBase): The SQLAlchemy table class to generate for.
        limit (int, optional): Limit string length to this amount. Defaults to 13.

    Returns:
        str: _description_
    """
    string_ = ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=limit))
    while not check_random_sting(string_, check_table):
        string_ = ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=limit))
    return string_


def check_random_sting(session: Session, string: str, table_: _DeclarativeBase) -> bool:
    """Checks if the givin string exists in the serial_number column of the table_.

    Args:
        session (Session): The session to use.
        string (str): The string to look for.
        table_ (_DeclarativeBase): The table class to search in.

    Returns:
        bool: Returns True if string is unique.
    """
    try:
        x = session.query(table_).filter_by(uuid=string).first()
    except InvalidRequestError:
        x = session.query(table_).filter_by(serial_number=string).first()
    if x:
        return False
    return True