# GridSense — Smart Power Grid Analytics & Fault Management

> Final assignment for **Advanced Data Management** · University of Thessaly · ECE · Spring 2026

GridSense is a prototype platform for a Regional Power Authority (RPA) that consolidates sensor data, network topology, equipment metadata, billing records, and real-time alerts into a single queryable system.

---

## Architecture

Five databases, each chosen for a specific workload:

| Service | Technology | Port | Role |
|---|---|---|---|
| `timeseries-db` | Apache Cassandra 4.1 | 9042 | Sensor readings (time-series, write-heavy) |
| `graph-db` | Neo4j 5 Community | 7474 / 7687 | Grid topology & fault propagation |
| `catalog-db` | MongoDB 7 | 27017 | Equipment metadata (flexible schema) |
| `billing-db` | PostgreSQL 15 | 5432 | Billing & accounts (ACID transactions) |
| `cache` | Redis 7 | 6379 | Dashboard cache & real-time alerts (Pub/Sub) |
| `api` | FastAPI (Python 3.11) | 8000 | REST gateway for all databases |

---

## Quick Start

**Prerequisites:** Docker Desktop with at least 6 GB RAM allocated.

```bash
# 1. Clone
git clone https://github.com/ThanasisKam/GridSense.git
cd GridSense

# 2. Create environment file
cp .env.example .env

# 3. Boot everything
docker compose up --build
```

Wait for:
```
api  | INFO: Application startup complete.
```
(first boot takes ~3-4 minutes for Cassandra and Neo4j to initialise)

```bash
# 4. Seed the databases (first time only)
docker compose exec api python scripts/seed.py
```

---

## API Examples

```bash
# Ingest sensor readings (batch)
curl -X POST http://localhost:8000/sensors/readings \
  -H "Content-Type: application/json" \
  -d '[{"sensor_id":"SM_00001","metric_type":"voltage","value":231.4,"unit":"V","quality_flag":0}]'

# Get last 10 readings for a sensor
curl "http://localhost:8000/sensors/SM_00001/readings?limit=10"

# Fault impact -- all nodes that lose power if SS_001 trips
curl "http://localhost:8000/grid/fault-impact/SS_001?max_depth=6"

# Get equipment profile
curl "http://localhost:8000/equipment/EQ_TX_001"

# Get billing account
curl "http://localhost:8000/billing/account/PREM_10001"

# Publish a fault alert
curl -X POST http://localhost:8000/alerts/publish \
  -H "Content-Type: application/json" \
  -d '{"node_id":"SS_001","severity":"critical","message":"Relay trip detected"}'

# Get active alerts
curl "http://localhost:8000/alerts/active"
```

Interactive API docs available at **http://localhost:8000/docs**

---

## Stopping & Resetting

```bash
# Stop (data persists)
docker compose down

# Full reset (deletes all data)
docker compose down -v
```
