from fastapi import APIRouter, HTTPException
from db.mongo import get_db
from models.mongo import EquipmentIn, EquipmentOut, EquipmentPatch

router = APIRouter(prefix="/equipment", tags=["Equipment (MongoDB)"])


@router.get("/{asset_id}", response_model=EquipmentOut)
async def get_equipment(asset_id: str):
    """Retrieve full metadata for a single piece of equipment."""
    db = get_db()
    doc = await db.equipment.find_one({"asset_id": asset_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Equipment '{asset_id}' not found")
    return EquipmentOut(**doc)


@router.post("", status_code=201, response_model=EquipmentOut)
async def create_equipment(equipment: EquipmentIn):
    """
    Register new equipment. The metadata field accepts any JSON shape,
    which is MongoDB's key advantage: a new meter model with 40 non-standard
    fields requires no schema migration.
    """
    db = get_db()
    existing = await db.equipment.find_one({"asset_id": equipment.asset_id})
    if existing:
        raise HTTPException(status_code=409, detail=f"Equipment '{equipment.asset_id}' already exists")

    doc = equipment.model_dump()
    await db.equipment.insert_one(doc)
    return EquipmentOut(**{k: v for k, v in doc.items() if k != "_id"})


@router.patch("/{asset_id}", response_model=EquipmentOut)
async def update_equipment(asset_id: str, patch: EquipmentPatch):
    """
    Partial update: only provided fields are changed.
    metadata fields are merged (not replaced), preserving existing keys.
    """
    db = get_db()
    update_fields = {}
    if patch.asset_type is not None:
        update_fields["asset_type"] = patch.asset_type
    if patch.metadata is not None:
        # Merge new metadata keys into existing — MongoDB dot-notation
        for key, val in patch.metadata.items():
            update_fields[f"metadata.{key}"] = val

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = await db.equipment.update_one(
        {"asset_id": asset_id},
        {"$set": update_fields}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Equipment '{asset_id}' not found")

    doc = await db.equipment.find_one({"asset_id": asset_id}, {"_id": 0})
    return EquipmentOut(**doc)