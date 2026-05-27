from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SensorReadingIn(BaseModel):
    sensor_id: str
    metric_type: str   # voltage | current | power_factor | temperature
    value: float
    unit: str
    quality_flag: int = Field(default=0, ge=0, le=2)  # 0=good,1=suspect,2=bad


class SensorReadingOut(BaseModel):
    sensor_id: str
    reading_time: datetime
    metric_type: str
    value: float
    unit: str
    quality_flag: int


class RelayEventIn(BaseModel):
    feeder_id: str
    relay_id: str
    event_type: str    # TRIP | RECLOSE | LOCKOUT
    fault_type: Optional[str] = None
    current_kA: Optional[float] = None
    voltage_kV: Optional[float] = None
    notes: Optional[str] = None