from .base import DatabaseSchemaBase
from .mysql import DatabaseSchema as DatabaseSchemaMySQL
from .postgresql import DatabaseSchema as DatabaseSchemaPostgreSQL


def create_database_from_str(db_type, db_name, db_str):
    db_type = db_type.lower()
    assert db_type in ['base', 'mysql', 'postgresql']
    if db_type == 'base':
        return DatabaseSchemaBase.parse_from_str(db_name, db_str)
    elif db_type == 'mysql':
        return DatabaseSchemaMySQL.parse_from_str(db_name, db_str)
    elif db_type == 'postgresql':
        return DatabaseSchemaPostgreSQL.parse_from_str(db_name, db_str)
    return None
