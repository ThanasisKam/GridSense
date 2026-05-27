#!/usr/bin/env python3
"""
GridSense data seeder — idempotent, run once after docker compose up --build.

Usage (from inside the api container):
    docker compose exec api python scripts/seed.py

Populates:
    Neo4j      — 10 substations, 40 transformers, 200 smart meters + relationships
    Cassandra  — 50,000 sensor readings across 20 sensor IDs
    MongoDB    — 30 equipment records across 3 types (different schemas per type)
    PostgreSQL — 100 consumer accounts + sample invoices
"""

import asyncio
import json
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# ── Make sure we can import from /app ────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cassandra.cluster import Cluster
from cassandra.policies import RoundRobinPolicy
from neo4j import AsyncGraphDatabase
from motor.motor_asyncio import AsyncIOMotorClient
import asyncpg

# ── Config from environment (same as the API uses) ───────────────────────────
CASSANDRA_HOST  = os.getenv("CASSANDRA_HOST", "timeseries-db")
NEO4J_URI       = os.getenv("NEO4J_URI",      "bolt://graph-db:7687")
NEO4J_PASSWORD  = os.getenv("NEO4J_PASSWORD", "gridsense_dev_pass")
MONGO_URI       = os.getenv("MONGO_URI",      "mongodb://gridsense:gridsense_dev_pass@catalog-db:27017")
POSTGRES_DSN    = os.getenv("POSTGRES_DSN",   "postgresql://gridsense:gridsense_dev_pass@billing-db:5432/gridsense")

random.seed(42)  # Reproducible data


# ═══════════════════════════════════════════════════════════════════════════════
# CASSANDRA — 50,000 sensor readings across 20 sensors
# ═══════════════════════════════════════════════════════════════════════════════

def seed_cassandra():
    print("\n[Cassandra] Connecting...")
    for attempt in range(15):
        try:
            cluster = Cluster(
                [CASSANDRA_HOST],
                load_balancing_policy=RoundRobinPolicy(),
                protocol_version=4,
            )
            session = cluster.connect()
            break
        except Exception as e:
            print(f"  Attempt {attempt+1}/15 failed: {e}")
            time.sleep(8)
    else:
        raise RuntimeError("Could not connect to Cassandra.")

    # Ensure schema exists
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS gridsense
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
    """)
    session.set_keyspace("gridsense")
    session.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            sensor_id TEXT, bucket TEXT, reading_time TIMESTAMP,
            metric_type TEXT, value FLOAT, unit TEXT, quality_flag TINYINT,
            PRIMARY KEY ((sensor_id, bucket), reading_time)
        ) WITH CLUSTERING ORDER BY (reading_time DESC)
          AND default_time_to_live = 7776000
    """)
    session.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings_by_time (
            time_bucket TEXT, reading_time TIMESTAMP, sensor_id TEXT,
            metric_type TEXT, value FLOAT, unit TEXT, quality_flag TINYINT,
            PRIMARY KEY ((time_bucket), reading_time, sensor_id)
        ) WITH CLUSTERING ORDER BY (reading_time DESC, sensor_id ASC)
          AND default_time_to_live = 7776000
    """)
    session.execute("""
        CREATE TABLE IF NOT EXISTS relay_events (
            feeder_id TEXT, event_time TIMEUUID, relay_id TEXT,
            event_type TEXT, fault_type TEXT, current_kA FLOAT,
            voltage_kV FLOAT, notes TEXT,
            PRIMARY KEY ((feeder_id), event_time)
        ) WITH CLUSTERING ORDER BY (event_time ASC)
    """)

    insert_main = session.prepare("""
        INSERT INTO sensor_readings
            (sensor_id, bucket, reading_time, metric_type, value, unit, quality_flag)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """)
    insert_dashboard = session.prepare("""
        INSERT INTO sensor_readings_by_time
            (time_bucket, reading_time, sensor_id, metric_type, value, unit, quality_flag)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """)

    SENSOR_IDS = [f"SM_{i:05d}" for i in range(1, 21)]  # SM_00001 … SM_00020
    METRICS = [
        ("voltage",      220.0, 240.0, "V"),
        ("current",        0.5,  15.0, "A"),
        ("power_factor",   0.85,  1.0, "pf"),
        ("temperature",   15.0,  45.0, "C"),
    ]

    now = datetime.now(timezone.utc)
    total = 0
    target = 50_000
    readings_per_sensor = target // len(SENSOR_IDS)  # 2,500 each

    print(f"[Cassandra] Writing {target:,} readings ({readings_per_sensor} per sensor)...")

    for sensor_id in SENSOR_IDS:
        metric_type, lo, hi, unit = random.choice(METRICS)
        for i in range(readings_per_sensor):
            # Spread readings over the past 48 hours
            dt = now - timedelta(seconds=i * 1.728)  # ~48h spread
            bucket = dt.strftime("%Y%m%d%H")
            time_bucket = dt.strftime("%Y%m%d%H%M")
            value = round(random.uniform(lo, hi), 4)
            quality = 0 if random.random() > 0.02 else 1  # 2% suspect readings

            session.execute(insert_main,   (sensor_id, bucket, dt, metric_type, value, unit, quality))
            session.execute(insert_dashboard, (time_bucket, dt, sensor_id, metric_type, value, unit, quality))
            total += 1

        if total % 5000 == 0:
            print(f"  {total:,} / {target:,} written...")

    print(f"[Cassandra] Done — {total:,} readings inserted.")


# ═══════════════════════════════════════════════════════════════════════════════
# NEO4J — 200 smart meters + full relationship graph
# ═══════════════════════════════════════════════════════════════════════════════

SUBSTATIONS = [f"SS_{i:03d}" for i in range(1, 11)]
TRANSFORMER_IDS = (
    [f"TX_{ss[3:]}_{chr(65+j)}" for ss in SUBSTATIONS for j in range(4)]
)  # TX_001_A … TX_010_D = 40 transformers

async def seed_neo4j():
    print("\n[Neo4j] Connecting...")
    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=("neo4j", NEO4J_PASSWORD))
    await driver.verify_connectivity()

    async with driver.session(database="neo4j") as s:
        # Constraints (idempotent)
        for label, prop in [
            ("GridSupplyPoint", "gsp_id"),
            ("Substation",      "substation_id"),
            ("Transformer",     "asset_id"),
            ("SmartMeter",      "meter_id"),
        ]:
            await s.run(
                f"CREATE CONSTRAINT {label.lower()}_{prop}_unique IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
            )

        # GSPs
        for gsp in [
            {"gsp_id": "GSP_NORTH", "name": "Northern GSP", "voltage_kV": 132, "region": "North Metro"},
            {"gsp_id": "GSP_SOUTH", "name": "Southern GSP", "voltage_kV": 132, "region": "South Metro"},
        ]:
            await s.run("MERGE (:GridSupplyPoint {gsp_id:$gsp_id, name:$name, voltage_kV:$voltage_kV, region:$region})", **gsp)

        # Substations
        for i, ss_id in enumerate(SUBSTATIONS, 1):
            gsp = "GSP_NORTH" if i <= 7 else "GSP_SOUTH"
            await s.run("""
                MERGE (s:Substation {substation_id:$sid})
                SET s.name=$name, s.voltage_kV=11, s.gsp=$gsp, s.status='operational'
            """, sid=ss_id, name=f"Substation {ss_id}", gsp=gsp)
            await s.run("""
                MATCH (g:GridSupplyPoint {gsp_id:$gsp}), (s:Substation {substation_id:$sid})
                MERGE (g)-[:FEEDS {feeder_id:$fid, voltage_kV:11}]->(s)
            """, gsp=gsp, sid=ss_id, fid=f"F_{i:03d}")

        # Transformers (40)
        manufacturers = ["ABB", "Siemens", "Schneider", "Legrand"]
        ratings = [100, 160, 250, 400, 630, 1000]
        for tx_id in TRANSFORMER_IDS:
            parts = tx_id.split("_")   # ['TX', '001', 'A']
            ss_id = f"SS_{parts[1]}"
            await s.run("""
                MERGE (t:Transformer {asset_id:$aid})
                SET t.rating_kVA=$rating, t.manufacturer=$mfr, t.status='operational'
            """, aid=tx_id, rating=random.choice(ratings), mfr=random.choice(manufacturers))
            await s.run("""
                MATCH (s:Substation {substation_id:$sid}), (t:Transformer {asset_id:$aid})
                MERGE (s)-[:SUPPLIES {cable_id:$cid, distance_m:$dist}]->(t)
            """, sid=ss_id, aid=tx_id, cid=f"CB_{tx_id}", dist=random.randint(100, 800))

        # Smart Meters (200) — 5 per transformer
        print("[Neo4j] Creating 200 smart meters...")
        tariff_classes = ["residential", "residential", "residential", "commercial", "industrial"]
        for m_idx in range(1, 201):
            meter_id  = f"SM_{m_idx:05d}"
            premise   = f"PREM_{10000 + m_idx}"
            tx_id     = TRANSFORMER_IDS[(m_idx - 1) % len(TRANSFORMER_IDS)]
            tariff    = tariff_classes[(m_idx - 1) % len(tariff_classes)]
            phase     = "three" if tariff == "industrial" else "single"
            await s.run("""
                MERGE (m:SmartMeter {meter_id:$mid})
                SET m.premise_id=$premise, m.tariff_class=$tariff,
                    m.phase=$phase, m.voltage_rating=230
            """, mid=meter_id, premise=premise, tariff=tariff, phase=phase)
            await s.run("""
                MATCH (t:Transformer {asset_id:$aid}), (m:SmartMeter {meter_id:$mid})
                MERGE (t)-[:CONNECTS_TO]->(m)
            """, aid=tx_id, mid=meter_id)

    await driver.close()
    print("[Neo4j] Done — 2 GSPs, 10 substations, 40 transformers, 200 meters seeded.")


# ═══════════════════════════════════════════════════════════════════════════════
# MONGODB — 30 equipment records, 3 types with different schemas
# ═══════════════════════════════════════════════════════════════════════════════

async def seed_mongo():
    print("\n[MongoDB] Connecting...")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client["gridsense"]
    await client.admin.command("ping")

    # Ensure unique index on asset_id (idempotency)
    await db.equipment.create_index("asset_id", unique=True)

    docs = []

    # Type 1: Transformers (10) — electrical engineering schema
    for i in range(1, 11):
        docs.append({
            "asset_id":   f"EQ_TX_{i:03d}",
            "asset_type": "Transformer",
            "metadata": {
                "manufacturer":      random.choice(["ABB", "Siemens", "Schneider"]),
                "model":             f"ONAN-{random.choice([250, 400, 630])}",
                "rating_kVA":        random.choice([250, 400, 630]),
                "voltage_ratio":     "11kV/0.4kV",
                "vector_group":      "Dyn11",
                "impedance_pct":     round(random.uniform(4.0, 6.0), 2),
                "cooling_type":      "ONAN",
                "firmware_version":  f"3.{random.randint(0,9)}.{random.randint(0,9)}",
                "installed":         f"201{random.randint(0,9)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "weight_kg":         random.randint(800, 2500),
                "oil_type":          "mineral",
            }
        })

    # Type 2: Smart Meters (10) — communication/metering schema (different fields)
    for i in range(1, 11):
        docs.append({
            "asset_id":   f"EQ_SM_{i:03d}",
            "asset_type": "SmartMeter",
            "metadata": {
                "manufacturer":      random.choice(["Landis+Gyr", "Itron", "Elster"]),
                "model":             f"E{random.randint(100,999)}",
                "rated_voltage":     random.choice([230, 400]),
                "rated_current_A":   random.choice([10, 20, 40, 63]),
                "accuracy_class":    random.choice(["B", "C"]),
                "communication":     random.choice(["DLMS/COSEM", "MBUS", "IEC62056"]),
                "firmware_version":  f"3.{random.randint(0,9)}.{random.randint(0,9)}",
                "tamper_detection":  True,
                "display_digits":    8,
                "metrology_cert":    f"MID-{random.randint(1000,9999)}",
                "ip_rating":         "IP54",
                # These 3 fields exist ONLY on this meter model — MongoDB handles it naturally
                "remote_disconnect": True,
                "power_quality_measurement": True,
                "dlms_logical_device_name": f"GRC{random.randint(10000,99999)}",
            }
        })

    # Type 3: Switchgear (10) — protection schema (again completely different fields)
    for i in range(1, 11):
        docs.append({
            "asset_id":   f"EQ_SW_{i:03d}",
            "asset_type": "Switchgear",
            "metadata": {
                "manufacturer":      random.choice(["Eaton", "ABB", "Schneider"]),
                "model":             f"VD4-{random.randint(10,40)}",
                "rated_voltage_kV":  random.choice([11, 33]),
                "rated_current_A":   random.choice([630, 1250, 2000]),
                "breaking_capacity_kA": random.choice([16, 25, 31.5]),
                "protection_relay":  random.choice(["SEL-351", "GE-D60", "ABB-REF615"]),
                "firmware_version":  f"3.{random.randint(0,9)}.{random.randint(0,9)}",
                "arc_flash_rating":  f"{random.randint(8,40)} cal/cm2",
                "num_poles":         3,
                "interlock_scheme":  random.choice(["mechanical", "electrical", "key"]),
                # These fields exist ONLY on switchgear — no schema change needed in MongoDB
                "trip_coil_voltage": random.choice([24, 48, 110, 220]),
                "close_coil_voltage": random.choice([24, 48, 110]),
                "operating_counter": random.randint(0, 5000),
            }
        })

    inserted = 0
    for doc in docs:
        try:
            await db.equipment.insert_one(doc)
            inserted += 1
        except Exception:
            pass  # Duplicate on re-run — skip silently (idempotent)

    client.close()
    print(f"[MongoDB] Done — {inserted} new records (30 total: 10 Transformers, 10 SmartMeters, 10 Switchgear).")


# ═══════════════════════════════════════════════════════════════════════════════
# POSTGRESQL — 100 consumer accounts + sample invoices
# ═══════════════════════════════════════════════════════════════════════════════

NAMES = [
    "Γεώργιος Παπαδόπουλος", "Ελένη Κωνσταντίνου", "Δημήτριος Αλεξίου",
    "Αικατερίνη Νικολάου", "Ιωάννης Γεωργίου", "Μαρία Αντωνίου",
    "Νικόλαος Δημητρίου", "Αναστασία Παππά", "Κωνσταντίνος Σταύρου",
    "Σοφία Μιχαήλ", "Παναγιώτης Χριστοδούλου", "Ευαγγελία Παπά",
]
STREETS = [
    "Ερμού", "Δημητριάδος", "Ιάσονος", "Αντωνοπούλου",
    "Κουμουνδούρου", "Σπύρου Σπυρίδη", "Βασσάνη", "Γαλλίας",
]

TARIFF_RESIDENTIAL = {
    "bands": [
        {"up_to_kwh": 500,  "rate": 0.12},
        {"up_to_kwh": 1000, "rate": 0.15},
        {"rate": 0.18}
    ],
    "time_of_use": False
}
TARIFF_COMMERCIAL = {
    "bands": [
        {"up_to_kwh": 2000, "rate": 0.11},
        {"rate": 0.145}
    ],
    "time_of_use": True,
    "peak_hours": "07:00-23:00",
    "peak_multiplier": 1.25
}
TARIFF_INDUSTRIAL = {
    "bands": [{"rate": 0.09}],
    "demand_charge_per_kw": 4.5,
    "time_of_use": True,
    "peak_hours": "08:00-20:00"
}

async def seed_postgres():
    print("\n[PostgreSQL] Connecting...")
    pool = await asyncpg.create_pool(POSTGRES_DSN, min_size=2, max_size=5)

    inserted_accounts = 0
    inserted_invoices = 0

    for i in range(1, 101):
        premise_id    = f"PREM_{10000 + i}"
        meter_id      = f"SM_{i:05d}"
        customer_name = random.choice(NAMES)
        street        = random.choice(STREETS)
        address       = f"{street} {random.randint(1, 150)}, Βόλος"
        tariff_class  = (
            "industrial" if i > 90 else
            "commercial" if i > 70 else
            "residential"
        )
        tariff_rules = (
            TARIFF_INDUSTRIAL if tariff_class == "industrial" else
            TARIFF_COMMERCIAL if tariff_class == "commercial" else
            TARIFF_RESIDENTIAL
        )

        async with pool.acquire() as conn:
            # INSERT ... ON CONFLICT DO NOTHING — idempotent
            result = await conn.execute("""
                INSERT INTO accounts
                    (premise_id, customer_name, address, meter_id,
                     tariff_class, tariff_rules, balance_eur)
                VALUES ($1,$2,$3,$4,$5,$6::jsonb,$7)
                ON CONFLICT (premise_id) DO NOTHING
            """, premise_id, customer_name, address, meter_id,
                tariff_class, json.dumps(tariff_rules), Decimal("0.00"))

            if result == "INSERT 0 1":
                inserted_accounts += 1

            # Add one sample invoice per account
            kwh = Decimal(str(round(random.uniform(150, 800), 3)))
            bands = tariff_rules.get("bands", [])
            amount = _calc_amount(kwh, bands)
            tax    = (amount * Decimal("0.13")).quantize(Decimal("0.01"))
            total  = amount + tax
            period_end   = datetime.now(timezone.utc).date()
            period_start = (datetime.now(timezone.utc) - timedelta(days=30)).date()

            line_items = json.dumps([
                {"description": "Energy", "kwh": str(kwh), "amount": str(amount)},
                {"description": "VAT 13%", "amount": str(tax)},
            ])

            inv_result = await conn.execute("""
                INSERT INTO invoices
                    (premise_id, period_start, period_end, kwh_consumed,
                     amount_eur, tax_eur, total_eur, line_items, status, issued_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8::jsonb,'issued',NOW())
                ON CONFLICT DO NOTHING
            """, premise_id, period_start, period_end, kwh,
                amount, tax, total, line_items)

            if inv_result == "INSERT 0 1":
                inserted_invoices += 1

            # Update account balance
            await conn.execute(
                "UPDATE accounts SET balance_eur = $1 WHERE premise_id = $2",
                total, premise_id
            )

    await pool.close()
    print(f"[PostgreSQL] Done — {inserted_accounts} accounts, {inserted_invoices} invoices inserted.")


def _calc_amount(kwh: Decimal, bands: list) -> Decimal:
    if not bands:
        return (kwh * Decimal("0.15")).quantize(Decimal("0.01"))
    total = Decimal("0")
    remaining = kwh
    prev = Decimal("0")
    for band in bands:
        limit = Decimal(str(band.get("up_to_kwh", 999999)))
        rate  = Decimal(str(band["rate"]))
        chunk = min(remaining, limit - prev)
        total += chunk * rate
        remaining -= chunk
        prev = limit
        if remaining <= 0:
            break
    return total.quantize(Decimal("0.01"))


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    print("=" * 60)
    print("GridSense Data Seeder")
    print("=" * 60)

    # Cassandra is synchronous — run in thread pool
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, seed_cassandra)

    await seed_neo4j()
    await seed_mongo()
    await seed_postgres()

    print("\n" + "=" * 60)
    print("Seeding complete. Run: docker compose exec api python scripts/seed.py")
    print("to re-run (idempotent — safe to run multiple times).")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())