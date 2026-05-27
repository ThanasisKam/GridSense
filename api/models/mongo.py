from typing import Any, Dict, Optional
from pydantic import BaseModel


class EquipmentIn(BaseModel):
    asset_id: str
    asset_type: str     # Transformer | SmartMeter | Switchgear | ...
    # All other fields are free-form — stored as-is in MongoDB
    metadata: Dict[str, Any] = {}


class EquipmentOut(BaseModel):
    asset_id: str
    asset_type: str
    metadata: Dict[str, Any] = {}


class EquipmentPatch(BaseModel):
    # Partial update — only provided fields are updated
    metadata: Optional[Dict[str, Any]] = None
    asset_type: Optional[str] = None