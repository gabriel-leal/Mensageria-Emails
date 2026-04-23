from sqlalchemy import create_engine, text
import os
from urllib.parse import quote_plus
from db.session import DATABASE_URL, DB_NAME

def create_database_if_not_exists():
    temp_url = DATABASE_URL.rsplit("/", 1)[0] + "/postgres"

    engine_temp = create_engine(temp_url)

    db_name = DB_NAME

    with engine_temp.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")

        result = conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        )

        if not result.scalar():
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))