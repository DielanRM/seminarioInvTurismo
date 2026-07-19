from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from config import Config


def crear_url_conexion():
    # En Render usa la URL completa configurada en Environment.
    if Config.DATABASE_URL:
        return Config.DATABASE_URL

    # En local usa las variables del archivo .env.
    return URL.create(
        drivername="postgresql+psycopg2",
        username=Config.DB_USER,
        password=Config.DB_PASSWORD,
        host=Config.DB_HOST,
        port=int(Config.DB_PORT),
        database=Config.DB_NAME
    )


engine = create_engine(
    crear_url_conexion(),
    pool_pre_ping=True
)