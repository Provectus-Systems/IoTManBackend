import os
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
    SQLModel.metadata.create_all(engine)
    yield
    # Code to run on shutdown (if any)

app = FastAPI(lifespan=lifespan)

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
