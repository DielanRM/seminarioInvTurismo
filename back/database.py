from sqlalchemy import create_engine
from config import Config

DATABASE_URL=(
    f"postgresql://{Config.DB_USER}:"
    f"{Config.DB_PASSWORD}@"
    f"{Config.DB_HOST}:"
    f"{Config.DB_PORT}/"
    f"{Config.DB_NAME}"
)

engine = create_engine(DATABASE_URL)