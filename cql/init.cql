-- GridSense Cassandra Schema
-- Partition strategy: sensor_id + bucket to avoid hot partitions
-- on sensors that report every second over months.
-- cql/init.cql (starter — you must complete and extend this)

CREATE KEYSPACE IF NOT EXISTS gridsense
WITH replication = {
  'class': 'SimpleStrategy',
  'replication_factor': 1  -- use 3 in a production multi-node cluster
};

USE gridsense;

-- Table 1: sensor_reading
-- Partition key: (sensor_id, bucket)
--   bucket = YYYYMMDDHH string — caps partition size at ~3,600 rows/hour/sensor.
--   A sensor_id-only partition key would accumulate millions of rows per sensor
--   over 90 days, causing wide-partition problems and read amplification.
--
-- Clustering key: reading_time DESC — newest rows come first.
--
-- TTL: 90 days (7,776,000 seconds).

CREATE TABLE IF NOT EXISTS sensor_readings (
    sensor_id    TEXT,
    bucket       TEXT,        -- YYYYMMDDHH
    reading_time TIMESTAMP,
    metric_type  TEXT,        -- voltage, current, power_factor, temperature
    value        FLOAT,
    unit         TEXT,
    quality_flag TINYINT,     -- 0=good, 1=suspect, 2=bad
    PRIMARY KEY ((sensor_id, bucket), reading_time)
) WITH CLUSTERING ORDER BY (reading_time DESC)
  AND default_time_to_live = 7776000
  AND compaction = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_unit': 'HOURS',
    'compaction_window_size': 1
  };

  
-- Table 2: sensor_readings_by_time 
-- Partition key: time_bucket (1-minute window) — all sensors in the same minute
-- live dashboard
--
-- Write amplification: every sensor write goes to BOTH tables (2x writes).
-- At 40,000 events/sec that is 80,000 Cassandra writes/sec total.
-- This is the explicit trade-off of query-driven design.
--   land in the same partition, making a single partition scan return the dashboard.

CREATE TABLE IF NOT EXISTS sensor_readings_by_time (
    time_bucket  TEXT,        -- YYYYMMDDHHMM, e.g. '202605171432'
    reading_time TIMESTAMP,
    sensor_id    TEXT,
    metric_type  TEXT,
    value        FLOAT,
    unit         TEXT,
    quality_flag TINYINT,
    PRIMARY KEY ((time_bucket), reading_time, sensor_id)
) WITH CLUSTERING ORDER BY (reading_time DESC, sensor_id ASC)
  AND default_time_to_live = 7776000;

-- Table 3: relay_events 
-- Append-only fault event log. Causal order is preserved by TIMEUUID clustering.
-- TIMEUUID embeds a timestamp + node ID, making it globally unique and sortable
-- by time without coordinator coordination.

CREATE TABLE IF NOT EXISTS relay_events (
    feeder_id    TEXT,
    event_time   TIMEUUID,    -- TIMEUUID = timestamp-ordered UUID; causal order guaranteed
    relay_id     TEXT,
    event_type   TEXT,        -- 'TRIP' | 'RECLOSE' | 'LOCKOUT'
    fault_type   TEXT,        
    current_kA   FLOAT,
    voltage_kV   FLOAT,
    notes        TEXT,
    PRIMARY KEY ((feeder_id), event_time)
) WITH CLUSTERING ORDER BY (event_time ASC);
