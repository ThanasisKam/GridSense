"""
Benchmark script for Part C measurements.
Run: docker compose exec api python scripts/benchmark.py
"""
import time
import random
import statistics
import os
import sys

# Use cassandra driver directly for throughput test (avoids HTTP overhead)
from cassandra.cluster import Cluster
from cassandra.policies import RoundRobinPolicy

CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "timeseries-db")


def bench_cassandra_writes():
    """C.1 — Cassandra write throughput at consistency ONE."""
    from cassandra import ConsistencyLevel
    from cassandra.query import SimpleStatement
    from datetime import datetime, timezone

    cluster = Cluster([CASSANDRA_HOST], load_balancing_policy=RoundRobinPolicy(), protocol_version=4)
    session = cluster.connect("gridsense")

    insert_cql = session.prepare("""
        INSERT INTO sensor_readings
            (sensor_id, bucket, reading_time, metric_type, value, unit, quality_flag)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """)

    def bucket(dt):
        return dt.strftime("%Y%m%d%H")

    def run_batch(n_rows, n_iters, consistency):
        insert_cql.consistency_level = consistency
        times = []
        for i in range(n_iters):
            now = datetime.now(timezone.utc)
            b = bucket(now)
            t0 = time.perf_counter()
            for j in range(n_rows):
                session.execute(insert_cql, (
                    f"BENCH_{n_rows}_{i}_{j}", b, now,
                    "voltage", round(220 + random.random() * 20, 2), "V", 0
                ))
            t1 = time.perf_counter()
            times.append((t1 - t0) * 1000)
        return times

    print("\n=== C.1: Cassandra Write Throughput ===")
    print("Consistency level ONE (single-node dev cluster)")
    print(f"{'Batch':>10} {'Iters':>6} {'Avg ms':>8} {'p50 ms':>8} {'p95 ms':>8} {'writes/s':>10}")
    print("-" * 55)

    for batch_size, n_iters in [(1, 100), (10, 50), (100, 30), (500, 20)]:
        t = sorted(run_batch(batch_size, n_iters, ConsistencyLevel.ONE))
        avg = statistics.mean(t)
        p50 = t[len(t) // 2]
        p95 = t[int(len(t) * 0.95)]
        wps = int(batch_size * 1000 / avg)
        print(f"{batch_size:>10} {n_iters:>6} {avg:>8.1f} {p50:>8.1f} {p95:>8.1f} {wps:>10,}")

    cluster.shutdown()


def bench_neo4j_traversal():
    """C.2 — Neo4j traversal depth vs latency."""
    import urllib.request
    import json

    BASE = "http://localhost:8000"
    NODE_ID = "SS_001"
    N_ITERS = 35  # >30 as required

    print("\n=== C.2: Neo4j Traversal Depth vs Latency ===")
    print(f"Node: {NODE_ID} | Iterations per depth: {N_ITERS}")
    print(f"{'Depth':>6} {'Nodes':>7} {'Median ms':>10} {'P95 ms':>8} {'Under 200ms?':>14}")
    print("-" * 50)

    for depth in range(1, 9):
        times = []
        nodes_returned = 0
        url = f"{BASE}/grid/fault-impact/{NODE_ID}?max_depth={depth}"
        for _ in range(N_ITERS):
            t0 = time.perf_counter()
            req = urllib.request.urlopen(url)
            data = json.loads(req.read())
            t1 = time.perf_counter()
            times.append((t1 - t0) * 1000)
            nodes_returned = data.get("total_affected", 0)

        times.sort()
        median_ms = times[N_ITERS // 2]
        p95_ms = times[int(N_ITERS * 0.95)]
        ok = "YES" if p95_ms < 200 else "NO  <-- SLA BREACH"
        print(f"{depth:>6} {nodes_returned:>7} {median_ms:>10.1f} {p95_ms:>8.1f} {ok:>14}")


def bench_redis_cache():
    """C.3 — Redis cache effectiveness."""
    import urllib.request
    import json
    import redis as redis_lib

    BASE = "http://localhost:8000"
    REDIS_URL = os.getenv("REDIS_URL", "redis://:gridsense_dev_pass@cache:6379/0")
    SENSOR_ID = "SENSOR_001"

    # Ensure sensor has data
    data = json.dumps([{
        "sensor_id": SENSOR_ID, "metric_type": "voltage",
        "value": 231.4, "unit": "V", "quality_flag": 0
    }]).encode()
    req = urllib.request.Request(f"{BASE}/sensors/readings", data=data,
                                  headers={"Content-Type": "application/json"}, method="POST")
    urllib.request.urlopen(req)

    r = redis_lib.from_url(REDIS_URL)

    def fetch_summary():
        t0 = time.perf_counter()
        resp = urllib.request.urlopen(f"{BASE}/sensors/{SENSOR_ID}/summary")
        result = json.loads(resp.read())
        t1 = time.perf_counter()
        return (t1 - t0) * 1000, result.get("source", "?")

    print("\n=== C.3: Redis Cache Effectiveness ===")
    print("30-second TTL | Sensor: SENSOR_001")

    # Cold cache — force miss
    r.delete(f"sensor:summary:{SENSOR_ID}")
    cold_times = []
    for i in range(50):
        r.delete(f"sensor:summary:{SENSOR_ID}")
        ms, source = fetch_summary()
        cold_times.append(ms)

    # Warm cache — keep cache alive
    warm_times = []
    _, _ = fetch_summary()  # prime the cache
    for i in range(200):
        ms, source = fetch_summary()
        warm_times.append(ms)

    def stats(t):
        t = sorted(t)
        return {
            "p50": t[len(t) // 2],
            "p95": t[int(len(t) * 0.95)],
            "p99": t[int(len(t) * 0.99)] if len(t) >= 100 else t[-1],
            "avg": statistics.mean(t),
        }

    cs = stats(cold_times)
    ws = stats(warm_times)

    print(f"{'':20} {'p50':>8} {'p95':>8} {'p99':>8} {'avg':>8}")
    print(f"{'Cold (Cassandra)':20} {cs['p50']:>8.1f} {cs['p95']:>8.1f} {cs['p99']:>8.1f} {cs['avg']:>8.1f}")
    print(f"{'Warm (Redis)':20} {ws['p50']:>8.1f} {ws['p95']:>8.1f} {ws['p99']:>8.1f} {ws['avg']:>8.1f}")
    speedup = cs['p50'] / ws['p50'] if ws['p50'] > 0 else 0
    print(f"Speedup (p50): {speedup:.1f}x")
    print(f"Hit rate simulation (200 warm / 250 total): {200/250*100:.0f}%")


if __name__ == "__main__":
    bench_cassandra_writes()
    bench_neo4j_traversal()
    bench_redis_cache()
    print("\nDone.")