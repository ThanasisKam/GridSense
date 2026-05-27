from typing import List, Optional
from pydantic import BaseModel


class AffectedNode(BaseModel):
    node_id: str
    node_type: str
    name: Optional[str] = None
    depth: int


class FaultImpactResponse(BaseModel):
    origin_id: str
    affected_nodes: List[AffectedNode]
    total_affected: int


class RestorePathResponse(BaseModel):
    faulted_node_id: str
    paths: List[List[str]]
    total_paths: int


class NodeIn(BaseModel):
    label: str          # Substation | Transformer | SmartMeter | GridSupplyPoint
    properties: dict


class RelationshipIn(BaseModel):
    from_id: str
    to_id: str
    rel_type: str       # FEEDS | SUPPLIES | CONNECTS_TO
    properties: dict = {}