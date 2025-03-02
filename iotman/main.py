import os
import time
from fastapi import FastAPI, HTTPException, Query
from fastapi.params import Depends
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select
from datetime import datetime, timezone
from contextlib import asynccontextmanager
import asyncio

from models import BatteryData
from schemas import BatteryDataCreate, BatteryDataResponse, BatteryDataResponseAll

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
            timestamp = timestamp.astimezone(timezone.utc)
            # Then remove timezone info
            timestamp = timestamp.replace(tzinfo=None)
        
        battery_data = BatteryData(
            battery_id=data.battery_id,
            voltage=reading.voltage,
            timestamp=timestamp
        )
        
        pg_session.add(battery_data)
        created_records.append(battery_data)
    
    await pg_session.commit()
    
    # Refresh all created records to get their assigned IDs
    for record in created_records:
        await pg_session.refresh(record)
    
    return created_records


@app.get("/data", response_model=BatteryDataResponseAll)
async def get_data(
    start_time: datetime = Query(None, description="Start time for filtering data (UTC)"),
    end_time: datetime = Query(None, description="End time for filtering data (UTC)"),
    pg_session: AsyncSession = Depends(get_async_session)
):
    """
    GET /data
    Returns the last 100 entries, sorted by timestamp descending.
    Optional query parameters:
    - start_time: Filter data after this time (UTC)
    - end_time: Filter data before this time (UTC)
    """
    # Start building the query
    query = select(BatteryData)
    
    # Add time filters if provided
    if start_time:
        # Ensure start_time is in UTC and remove timezone info
        if start_time.tzinfo is not None:
            start_time = start_time.astimezone(timezone.utc)
        start_time = start_time.replace(tzinfo=None)
        query = query.where(BatteryData.timestamp >= start_time)
    
    if end_time:
        # Ensure end_time is in UTC and remove timezone info
        if end_time.tzinfo is not None:
            end_time = end_time.astimezone(timezone.utc)
        end_time = end_time.replace(tzinfo=None)
        query = query.where(BatteryData.timestamp <= end_time)
    
    # Apply sorting and limit
    query = query.order_by(BatteryData.timestamp.desc())
    
    # Execute query
    result = await pg_session.exec(query)
    data = result.scalars().all()
    
    return {"items": data, "total_items": len(data)}
