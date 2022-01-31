from sqlalchemy.engine import Engine
from sqlalchemy.schema import MetaData
import json
import datetime
import base64
import os
from database import SCHEMA


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, bytes):
            return base64.b64encode(obj).decode('utf-8')


def dump_database(engine: Engine) -> str:
    """Returns the entire content of a database as lists of dicts"""
    meta = MetaData()
    meta.reflect(bind=engine)  # http://docs.sqlalchemy.org/en/rel_0_9/core/reflection.html
    result = {}
    for table in meta.sorted_tables:
        result[table.name] = [dict(row) for row in engine.execute(table.select())]
    return json.dumps(result, cls=JSONEncoder, indent=4)


def restore_database() -> None:
    """Restores the database from the given dump """
    # TODO: implement
    raise NotImplementedError("Not implemented yet")


def save_dump(dump: str, folder_path) -> None:
    """ Saves the given dump to the given file path"""
    file_name_prefix = SCHEMA
    time_date = datetime.datetime.now().strftime("[%Y-%m-%d_%H-%M-%S]")
    file_name = f"{file_name_prefix}_{time_date}.json"
    file_path = os.path.join(folder_path, file_name)
    with open(file_path, "w") as f:
        f.write(dump)


def create(engine: Engine, folder_path: str) -> None:
    """ Creates a new database backup """
    dump = dump_database(engine)
    save_dump(dump, folder_path)