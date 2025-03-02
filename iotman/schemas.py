from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class BatteryReading(BaseModel):
    """Schema for a single battery voltage reading with timestamp"""
    battery_voltage: float = Field(..., description="Battery voltage reading in volts")
    timestamp: datetime = Field(..., description="Timestamp of the battery reading")


class BatteryDataCreate(BaseModel):
    """Schema for submitting multiple readings for a single battery"""
    battery_id: str = Field(..., description="Unique identifier for the battery")
    readings: List[BatteryReading] = Field(..., description="List of battery voltage readings with timestamps")


class BatteryDataResponse(BaseModel):
    """Schema for battery data response"""
    id: int
    battery_id: str
    battery_voltage: float
    timestamp: datetime

    class Config:
        from_attributes = True
