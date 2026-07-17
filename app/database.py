import os
import time

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

MAX_RETRIES = 10

engine = None

for _ in range(MAX_RETRIES):
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True
        )

        conn = engine.connect()
        print("Connected to Neon PostgreSQL")
        conn.close()
        break

    except Exception as e:
        print(e)
        time.sleep(5)

if engine is None:
    raise Exception("Unable to connect to database.")

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()