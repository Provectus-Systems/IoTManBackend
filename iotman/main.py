import os
import psycopg2
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from typing import Any

app = FastAPI()

# Database Connection Setup
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("POSTGRES_DB", "iot_db")
DB_USER = os.environ.get("POSTGRES_USER", "myuser")
DB_PASS = os.environ.get("POSTGRES_PASSWORD", "mypassword")

def get_db_connection():
    """
    Get a psycopg2 connection to the Postgres database.
    """
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

# Create table if not exists on startup
@app.on_event("startup")
def startup_event():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Use a JSONB column to store entire payload
    create_table_query = """
    CREATE TABLE IF NOT EXISTS iot_data (
        id SERIAL PRIMARY KEY,
        data JSONB NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """
    cursor.execute(create_table_query)
    conn.commit()
    cursor.close()
    conn.close()


@app.post("/data")
async def post_data(request: Request):
    """
    POST endpoint to accept IoT data in JSON format 
    and store it in Postgres.
    """
    try:
        payload = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    conn = get_db_connection()
    cursor = conn.cursor()
    insert_query = """
        INSERT INTO iot_data (data) 
        VALUES (%s)
        RETURNING id, created_at
    """
    cursor.execute(insert_query, [payload])
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "Data inserted successfully", "id": row[0], "created_at": row[1]}


@app.get("/data")
async def get_data():
    """
    GET endpoint to retrieve the last 100 data points
    from Postgres, sorted by creation time descending.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    select_query = """
        SELECT id, data, created_at 
        FROM iot_data
        ORDER BY created_at DESC 
        LIMIT 100
    """
    cursor.execute(select_query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Format the rows into a list of dicts
    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "data": row[1],
            "created_at": row[2].isoformat()
        })
    return {"results": results}