import time
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = (
    "postgresql://postgres:postgres@postgres:5432/trade_db"
)

MAX_RETRIES = 10

for i in range(MAX_RETRIES):

    try:

        engine = create_engine(DATABASE_URL)

        connection = engine.connect()

        print("Database connected successfully")

        connection.close()

        break

    except Exception as e:

        print(f"Database connection failed: {e}")

        time.sleep(5)

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