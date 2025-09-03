import psycopg2
import os
from app.db.config import Config

POSTGRES_URL = os.getenv("POSTGRES_URL")

def get_pg_connection():
    try:
        print(Config.DB_NAME, Config.DB_USER, Config.DB_PASSWORD, Config.DB_HOST, Config.DB_PORT)
        connection = psycopg2.connect(
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            host=Config.DB_HOST,
            port=Config.DB_PORT
        )
        print("Database connection successful")
        return connection
    except Exception as e:
        print(f"Error while connecting to PostgreSQL: {e}")
        return None
