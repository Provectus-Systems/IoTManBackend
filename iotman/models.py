from datetime import datetime
from sqlmodel import SQLModel, Field

class BatteryData(SQLModel, table=True):
    __tablename__ = "battery_data"
    idx: int = Field(primary_key=True, sa_column_kwargs={"autoincrement": True})
    battery_id: str
    voltage: float
    timestamp: datetime

