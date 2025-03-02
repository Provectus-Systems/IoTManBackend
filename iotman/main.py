import os
import time
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, create_engine, SQLModel, select
from typing import List
from datetime import datetime
from contextlib import asynccontextmanager

from models import BatteryData

# Environment Variables
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("POSTGRES_DB", "iot_db")
DB_USER = os.environ.get("POSTGRES_USER", "myuser")
DB_PASS = os.environ.get("POSTGRES_PASSWORD", "mypassword")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

# Create the engine
engine = create_engine(DATABASE_URL, echo=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    # Add retry logic for database connection
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Try to create tables
            SQLModel.metadata.create_all(engine)
            print("Successfully connected to the database")
            break
        except Exception as e:
            retry_count += 1
            wait_time = 2 ** retry_count  # Exponential backoff
            print(f"Database connection attempt {retry_count} failed. Retrying in {wait_time} seconds...")
            print(f"Error: {e}")
            time.sleep(wait_time)
            
            if retry_count == max_retries:
                print("Maximum retries reached. Could not connect to database.")
                # We'll continue and let the application start anyway
                # This allows the container to stay up even if DB is down
    
    yield

app = FastAPI(
    title="IoT Battery Management API",
    description="API for managing IoT battery data",
    version="1.0.0",
    docs_url="/",  # This sets the Swagger UI to the root URL
    redoc_url="/redoc"
)

@app.post("/data", response_model=BatteryData)
def post_data(data: BatteryData):
    """
    POST /data
    Accepts JSON with battery_id, battery_voltage, and timestamp.
    Inserts into the database and returns the newly created row.
    """
    # Ensure the timestamp field has a valid value
    if data.timestamp is None:
        data.timestamp = datetime.utcnow()

    with Session(engine) as session:
        session.add(data)
        session.commit()
        session.refresh(data)
        return data


@app.get("/data", response_model=List[BatteryData])
def get_data():
    """
    GET /data
    Returns the last 100 entries, sorted by timestamp descending.
    """
    with Session(engine) as session:
        statement = (
            select(BatteryData)
            .order_by(BatteryData.timestamp.desc())
            .limit(100)
        )
        results = session.exec(statement).all()
        return results
