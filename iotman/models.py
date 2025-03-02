from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class BatteryData(SQLModel, table=True):
    __tablename__ = "battery_data"
    id: Optional[int] = Field(default=None, primary_key=True)
    battery_id: str
    battery_voltage: float
    timestamp: datetime
