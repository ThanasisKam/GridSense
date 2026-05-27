from fastapi import APIRouter, HTTPException, Query
from db.neo4j import get_driver
from models.graph import (
    AffectedNode, FaultImpactResponse,
    RestorePathResponse, NodeIn, RelationshipIn,
)

router = APIRouter(prefix="/grid", tags=["Grid Topology (Neo4j)"])


@router.get("/fault-impact/{node_id}", response_model=FaultImpactResponse)
async def get_fault_impact(node_id: str, max_depth: int = Query(default=6, le=10)):
    """
    Return all nodes that lose supply if node_id trips.
    Cypher variable-length traversal — complexity stays O(nodes reached),
    unlike SQL which requires max_depth JOIN clauses.
    """
    if max_depth > 10:
        raise HTTPException(status_code=400, detail="max_depth cannot exceed 10")

    # Depth must be an integer literal in Cypher variable-length patterns (Neo4j 5).
    # Safe to interpolate directly — max_depth is validated as int <= 10 above.
    cypher = f"""
        MATCH (origin)
        WHERE origin.substation_id = $node_id
           OR origin.asset_id      = $node_id
           OR origin.meter_id      = $node_id
           OR origin.gsp_id        = $node_id
        MATCH (origin)-[:FEEDS|SUPPLIES|CONNECTS_TO*1..{max_depth}]->(downstream)
        RETURN
            labels(downstream)[0] AS node_type,
            COALESCE(
                downstream.substation_id,
                downstream.asset_id,
                downstream.meter_id,
                downstream.gsp_id
            ) AS node_id,
            COALESCE(downstream.name, downstream.meter_id, downstream.asset_id) AS name,
            1 AS depth
        ORDER BY node_type
    """

    driver = get_driver()
    async with driver.session(database="neo4j") as session:
        result = await session.run(cypher, node_id=node_id)
        records = await result.data()

    if not records:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found or has no downstream nodes")

    affected = [AffectedNode(**r) for r in records]
    return FaultImpactResponse(
        origin_id=node_id,
        affected_nodes=affected,
        total_affected=len(affected),
    )


@router.get("/restore-paths/{node_id}", response_model=RestorePathResponse)
async def get_restore_paths(node_id: str):
    """
    Find alternative upstream supply paths that could restore a faulted node.
    Uses allShortestPaths to find all routes back to a GridSupplyPoint.
    """
    cypher = """
        MATCH (target)
        WHERE target.substation_id = $node_id OR target.asset_id = $node_id
        MATCH (gsp:GridSupplyPoint)
        MATCH path = allShortestPaths((gsp)-[:FEEDS|SUPPLIES|CONNECTS_TO*]->(target))
        RETURN [n IN nodes(path) |
            COALESCE(n.gsp_id, n.substation_id, n.asset_id, n.meter_id)
        ] AS path_nodes
        LIMIT 5
    """

    driver = get_driver()
    async with driver.session(database="neo4j") as session:
        result = await session.run(cypher, node_id=node_id)
        records = await result.data()

    paths = [r["path_nodes"] for r in records]
    return RestorePathResponse(
        faulted_node_id=node_id,
        paths=paths,
        total_paths=len(paths),
    )


@router.post("/nodes", status_code=201)
async def add_node(node: NodeIn):
    """Add a new node to the topology graph."""
    props_str = ", ".join(f"{k}: ${k}" for k in node.properties)
    cypher = f"CREATE (n:{node.label} {{{props_str}}}) RETURN n"

    driver = get_driver()
    async with driver.session(database="neo4j") as session:
        await session.run(cypher, **node.properties)

    return {"created": True, "label": node.label, "properties": node.properties}


@router.post("/relationships", status_code=201)
async def add_relationship(rel: RelationshipIn):
    """Add a relationship between two existing nodes."""
    props_str = (
        "{" + ", ".join(f"{k}: ${k}" for k in rel.properties) + "}"
        if rel.properties else ""
    )
    cypher = f"""
        MATCH (a), (b)
        WHERE COALESCE(a.substation_id, a.asset_id, a.meter_id, a.gsp_id) = $from_id
          AND COALESCE(b.substation_id, b.asset_id, b.meter_id, b.gsp_id) = $to_id
        CREATE (a)-[r:{rel.rel_type} {props_str}]->(b)
        RETURN r
    """

    driver = get_driver()
    async with driver.session(database="neo4j") as session:
        result = await session.run(
            cypher, from_id=rel.from_id, to_id=rel.to_id, **rel.properties
        )
        record = await result.single()

    if not record:
        raise HTTPException(status_code=404, detail="One or both nodes not found")
    return {"created": True, "relationship": rel.rel_type}