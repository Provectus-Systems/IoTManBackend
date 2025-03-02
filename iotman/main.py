import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.params import Depends
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select
from datetime import datetime
from contextlib import asynccontextmanager
import asyncio

from models import BatteryData
from schemas import BatteryDataCreate, BatteryDataResponse

# Environment Variables
DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("POSTGRES_DB")
DB_USER = os.environ.get("POSTGRES_USER")
DB_PASS = os.environ.get("POSTGRES_PASSWORD")

# Use async PostgreSQL URL format
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    # Add retry logic for database connection
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Try to create tables asynchronously
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            print("Successfully connected to the database")
            break
        except Exception as e:
            retry_count += 1
            wait_time = 2 ** retry_count  # Exponential backoff
            print(f"Database connection attempt {retry_count} failed. Retrying in {wait_time} seconds...")
            print(f"Error: {e}")
            await asyncio.sleep(wait_time)
            
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
    redoc_url="/redoc",
    lifespan=lifespan
)

async def get_async_session():
    async with AsyncSession(engine) as session:
        yield session

@app.post("/data", response_model=list[BatteryDataResponse])
async def post_data(data: BatteryDataCreate, pg_session: AsyncSession = Depends(get_async_session)):
    """
    POST /data
    Accepts JSON with battery_id and a list of readings containing battery_voltage and timestamp.
    Inserts multiple entries into the database and returns the newly created rows.
    """
    created_records = []
    
    for reading in data.readings:
        # Process timestamp: first convert to UTC, then remove timezone info
        timestamp = reading.timestamp
        if timestamp.tzinfo is not None:
            # Ensure it's in UTC first
            from datetime import timezone
            timestamp = timestamp.astimezone(timezone.utc)
            # Then remove timezone info
            timestamp = timestamp.replace(tzinfo=None)
        
        battery_data = BatteryData(
            battery_id=data.battery_id,
            battery_voltage=reading.battery_voltage,
            timestamp=timestamp
        )
        
        pg_session.add(battery_data)
        created_records.append(battery_data)
    
    await pg_session.commit()
    
    # Refresh all created records to get their assigned IDs
    for record in created_records:
        await pg_session.refresh(record)
    
    return created_records


@app.get("/data", response_model=list[BatteryDataResponse])
async def get_data():
    """
    GET /data
    Returns the last 100 entries, sorted by timestamp descending.
    """
    async with AsyncSession(engine) as session:
        statement = select(BatteryData).order_by(BatteryData.timestamp.desc()).limit(100)
        result = await session.exec(statement)
        return result.scalars().all()
