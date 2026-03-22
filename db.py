# db.py — put this in your project root
import os
import psycopg2  # type: ignore
import psycopg2.extras  # type: ignore
from dotenv import load_dotenv  # type: ignore

load_dotenv()


def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")
