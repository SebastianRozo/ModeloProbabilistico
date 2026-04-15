import os
import psycopg
from dotenv import load_dotenv
from sqlalchemy.orm import declarative_base

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
Base = declarative_base()

class Connection:
    def __init__(self):
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL is not set in the environment or .env file")
        self.conn = psycopg.connect(DATABASE_URL)

    def close(self):
        self.conn.close()
