from datetime import datetime
from typing import List
from pydantic import BaseModel, Field, ConfigDict


class BatteryReading(BaseModel):
    """Schema for a single battery voltage reading with timestamp"""
    voltage: float = Field(..., description="Battery voltage reading in volts")
    timestamp: datetime = Field(..., description="Timestamp of the battery reading")


class BatteryDataCreate(BaseModel):
    """Schema for submitting multiple readings for a single battery"""
    battery_id: str = Field(..., description="Unique identifier for the battery")
    readings: List[BatteryReading] = Field(..., description="List of battery voltage readings with timestamps")


class BatteryDataResponse(BaseModel):
    """Schema for battery data response"""
    battery_id: str
    voltage: float
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)


class BatteryDataResponseAll(BaseModel):
    """Schema for all battery data response"""
    items: list[BatteryDataResponse]
    total_items: int