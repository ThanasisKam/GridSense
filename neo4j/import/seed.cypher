// GridSense Neo4j Seed Data
// Hierarchy: GridSupplyPoint → Substation → Transformer → SmartMeter
// Relationships carry physical properties (feeder_id, voltage, cable length)
// because those properties describe the CONNECTION, not either endpoint.

// ── Constraints (idempotent — IF NOT EXISTS) ─────────────────────────────────
CREATE CONSTRAINT substation_id IF NOT EXISTS
    FOR (s:Substation) REQUIRE s.substation_id IS UNIQUE;

CREATE CONSTRAINT transformer_id IF NOT EXISTS
    FOR (t:Transformer) REQUIRE t.asset_id IS UNIQUE;

CREATE CONSTRAINT meter_id IF NOT EXISTS
    FOR (m:SmartMeter) REQUIRE m.meter_id IS UNIQUE;

CREATE CONSTRAINT gsp_id IF NOT EXISTS
    FOR (g:GridSupplyPoint) REQUIRE g.gsp_id IS UNIQUE;

// ── Grid Supply Points ────────────────────────────────────────────────────────
MERGE (:GridSupplyPoint {gsp_id:"GSP_NORTH", name:"Northern Grid Supply Point", voltage_kV:132, region:"North Metro"});
MERGE (:GridSupplyPoint {gsp_id:"GSP_SOUTH", name:"Southern Grid Supply Point", voltage_kV:132, region:"South Metro"});

// ── Substations (10) ─────────────────────────────────────────────────────────
MERGE (:Substation {substation_id:"SS_001", name:"Volos Primary",      voltage_kV:11, lat:39.358, lon:22.938, commissioned_year:1998, status:"operational"});
MERGE (:Substation {substation_id:"SS_002", name:"Nea Ionia",          voltage_kV:11, lat:39.371, lon:22.951, commissioned_year:2003, status:"operational"});
MERGE (:Substation {substation_id:"SS_003", name:"Agria",              voltage_kV:11, lat:39.340, lon:22.988, commissioned_year:2001, status:"operational"});
MERGE (:Substation {substation_id:"SS_004", name:"Portaria",           voltage_kV:11, lat:39.402, lon:22.997, commissioned_year:2005, status:"operational"});
MERGE (:Substation {substation_id:"SS_005", name:"Almyros",            voltage_kV:11, lat:39.179, lon:22.756, commissioned_year:1999, status:"operational"});
MERGE (:Substation {substation_id:"SS_006", name:"Velestino",          voltage_kV:11, lat:39.385, lon:22.750, commissioned_year:2007, status:"operational"});
MERGE (:Substation {substation_id:"SS_007", name:"Nea Anchialos",      voltage_kV:11, lat:39.267, lon:22.817, commissioned_year:2002, status:"operational"});
MERGE (:Substation {substation_id:"SS_008", name:"Glafkos Industrial", voltage_kV:11, lat:39.355, lon:22.920, commissioned_year:2010, status:"operational"});
MERGE (:Substation {substation_id:"SS_009", name:"University Campus",  voltage_kV:11, lat:39.360, lon:22.928, commissioned_year:2015, status:"operational"});
MERGE (:Substation {substation_id:"SS_010", name:"Port Authority",     voltage_kV:11, lat:39.363, lon:22.945, commissioned_year:2008, status:"operational"});

// ── Transformers (40) ────────────────────────────────────────────────────────
MERGE (:Transformer {asset_id:"TX_001_A", rating_kVA:400,  manufacturer:"ABB",     model:"ONAN-400",   installed:date("2012-06-15"), last_inspection:date("2024-09-01"), load_pct:72});
MERGE (:Transformer {asset_id:"TX_001_B", rating_kVA:250,  manufacturer:"Siemens", model:"DTSS-250",   installed:date("2015-03-20"), last_inspection:date("2024-08-10"), load_pct:45});
MERGE (:Transformer {asset_id:"TX_001_C", rating_kVA:630,  manufacturer:"ABB",     model:"ONAN-630",   installed:date("2018-11-01"), last_inspection:date("2024-10-05"), load_pct:88});
MERGE (:Transformer {asset_id:"TX_001_D", rating_kVA:100,  manufacturer:"Legrand", model:"TRI-100",    installed:date("2008-07-30"), last_inspection:date("2023-12-01"), load_pct:55});
MERGE (:Transformer {asset_id:"TX_002_A", rating_kVA:400,  manufacturer:"ABB",     model:"ONAN-400",   installed:date("2013-02-10"), last_inspection:date("2024-07-15"), load_pct:61});
MERGE (:Transformer {asset_id:"TX_002_B", rating_kVA:250,  manufacturer:"Siemens", model:"DTSS-250",   installed:date("2016-09-05"), last_inspection:date("2024-09-20"), load_pct:38});
MERGE (:Transformer {asset_id:"TX_002_C", rating_kVA:630,  manufacturer:"Schneider",model:"SM630",     installed:date("2019-04-12"), last_inspection:date("2024-11-01"), load_pct:91});
MERGE (:Transformer {asset_id:"TX_002_D", rating_kVA:160,  manufacturer:"ABB",     model:"ONAN-160",   installed:date("2010-08-22"), last_inspection:date("2024-06-30"), load_pct:42});
MERGE (:Transformer {asset_id:"TX_003_A", rating_kVA:400,  manufacturer:"Siemens", model:"DTSS-400",   installed:date("2014-05-18"), last_inspection:date("2024-08-25"), load_pct:67});
MERGE (:Transformer {asset_id:"TX_003_B", rating_kVA:250,  manufacturer:"ABB",     model:"ONAN-250",   installed:date("2017-01-30"), last_inspection:date("2024-10-12"), load_pct:53});
MERGE (:Transformer {asset_id:"TX_004_A", rating_kVA:630,  manufacturer:"Schneider",model:"SM630",     installed:date("2020-07-01"), last_inspection:date("2024-11-15"), load_pct:79});
MERGE (:Transformer {asset_id:"TX_004_B", rating_kVA:400,  manufacturer:"ABB",     model:"ONAN-400",   installed:date("2015-12-10"), last_inspection:date("2024-09-05"), load_pct:44});
MERGE (:Transformer {asset_id:"TX_005_A", rating_kVA:250,  manufacturer:"Siemens", model:"DTSS-250",   installed:date("2011-03-25"), last_inspection:date("2024-07-20"), load_pct:58});
MERGE (:Transformer {asset_id:"TX_005_B", rating_kVA:160,  manufacturer:"Legrand", model:"TRI-160",    installed:date("2009-11-14"), last_inspection:date("2023-11-30"), load_pct:35});
MERGE (:Transformer {asset_id:"TX_006_A", rating_kVA:400,  manufacturer:"ABB",     model:"ONAN-400",   installed:date("2016-06-20"), last_inspection:date("2024-08-01"), load_pct:70});
MERGE (:Transformer {asset_id:"TX_006_B", rating_kVA:630,  manufacturer:"Schneider",model:"SM630",     installed:date("2021-02-14"), last_inspection:date("2024-10-20"), load_pct:82});
MERGE (:Transformer {asset_id:"TX_007_A", rating_kVA:250,  manufacturer:"Siemens", model:"DTSS-250",   installed:date("2013-09-08"), last_inspection:date("2024-07-05"), load_pct:49});
MERGE (:Transformer {asset_id:"TX_007_B", rating_kVA:400,  manufacturer:"ABB",     model:"ONAN-400",   installed:date("2018-04-30"), last_inspection:date("2024-09-15"), load_pct:63});
MERGE (:Transformer {asset_id:"TX_008_A", rating_kVA:1000, manufacturer:"Siemens", model:"DTSS-1000",  installed:date("2019-08-15"), last_inspection:date("2024-10-25"), load_pct:85});
MERGE (:Transformer {asset_id:"TX_008_B", rating_kVA:630,  manufacturer:"ABB",     model:"ONAN-630",   installed:date("2020-12-01"), last_inspection:date("2024-11-10"), load_pct:76});
MERGE (:Transformer {asset_id:"TX_009_A", rating_kVA:400,  manufacturer:"Schneider",model:"SM400",     installed:date("2022-03-10"), last_inspection:date("2024-11-20"), load_pct:40});
MERGE (:Transformer {asset_id:"TX_009_B", rating_kVA:250,  manufacturer:"ABB",     model:"ONAN-250",   installed:date("2021-07-25"), last_inspection:date("2024-10-01"), load_pct:33});
MERGE (:Transformer {asset_id:"TX_010_A", rating_kVA:630,  manufacturer:"Siemens", model:"DTSS-630",   installed:date("2017-05-12"), last_inspection:date("2024-08-20"), load_pct:74});
MERGE (:Transformer {asset_id:"TX_010_B", rating_kVA:400,  manufacturer:"ABB",     model:"ONAN-400",   installed:date("2016-10-18"), last_inspection:date("2024-09-10"), load_pct:57});
// 16 more transformers to reach 40 total (SS_001 to SS_010, 4 each for first 4)
MERGE (:Transformer {asset_id:"TX_001_E", rating_kVA:160,  manufacturer:"Legrand", model:"TRI-160",    installed:date("2007-04-10"), last_inspection:date("2023-10-15"), load_pct:30});
MERGE (:Transformer {asset_id:"TX_002_E", rating_kVA:400,  manufacturer:"ABB",     model:"ONAN-400",   installed:date("2014-11-22"), last_inspection:date("2024-07-01"), load_pct:66});
MERGE (:Transformer {asset_id:"TX_003_C", rating_kVA:630,  manufacturer:"Schneider",model:"SM630",     installed:date("2019-09-30"), last_inspection:date("2024-11-05"), load_pct:80});
MERGE (:Transformer {asset_id:"TX_003_D", rating_kVA:250,  manufacturer:"Siemens", model:"DTSS-250",   installed:date("2016-02-15"), last_inspection:date("2024-08-30"), load_pct:47});
MERGE (:Transformer {asset_id:"TX_004_C", rating_kVA:160,  manufacturer:"Legrand", model:"TRI-160",    installed:date("2012-08-05"), last_inspection:date("2024-06-10"), load_pct:29});
MERGE (:Transformer {asset_id:"TX_004_D", rating_kVA:250,  manufacturer:"ABB",     model:"ONAN-250",   installed:date("2017-12-20"), last_inspection:date("2024-09-25"), load_pct:51});
MERGE (:Transformer {asset_id:"TX_005_C", rating_kVA:400,  manufacturer:"Siemens", model:"DTSS-400",   installed:date("2015-06-08"), last_inspection:date("2024-08-05"), load_pct:69});
MERGE (:Transformer {asset_id:"TX_005_D", rating_kVA:630,  manufacturer:"Schneider",model:"SM630",     installed:date("2020-01-15"), last_inspection:date("2024-10-30"), load_pct:84});
MERGE (:Transformer {asset_id:"TX_006_C", rating_kVA:100,  manufacturer:"Legrand", model:"TRI-100",    installed:date("2008-03-28"), last_inspection:date("2023-09-20"), load_pct:25});
MERGE (:Transformer {asset_id:"TX_007_C", rating_kVA:400,  manufacturer:"ABB",     model:"ONAN-400",   installed:date("2018-07-14"), last_inspection:date("2024-09-30"), load_pct:60});
MERGE (:Transformer {asset_id:"TX_007_D", rating_kVA:250,  manufacturer:"Siemens", model:"DTSS-250",   installed:date("2019-11-20"), last_inspection:date("2024-10-15"), load_pct:43});
MERGE (:Transformer {asset_id:"TX_008_C", rating_kVA:400,  manufacturer:"Schneider",model:"SM400",     installed:date("2021-04-05"), last_inspection:date("2024-11-01"), load_pct:56});
MERGE (:Transformer {asset_id:"TX_009_C", rating_kVA:160,  manufacturer:"ABB",     model:"ONAN-160",   installed:date("2020-09-10"), last_inspection:date("2024-10-05"), load_pct:37});
MERGE (:Transformer {asset_id:"TX_010_C", rating_kVA:630,  manufacturer:"Siemens", model:"DTSS-630",   installed:date("2018-03-22"), last_inspection:date("2024-08-15"), load_pct:71});
MERGE (:Transformer {asset_id:"TX_010_D", rating_kVA:250,  manufacturer:"ABB",     model:"ONAN-250",   installed:date("2016-08-30"), last_inspection:date("2024-09-20"), load_pct:48});

// ── Smart Meters (sample — seed.py will add the full 200) ────────────────────
MERGE (:SmartMeter {meter_id:"SM_00001", premise_id:"PREM_10001", tariff_class:"residential", phase:"single", voltage_rating:230});
MERGE (:SmartMeter {meter_id:"SM_00002", premise_id:"PREM_10002", tariff_class:"residential", phase:"single", voltage_rating:230});
MERGE (:SmartMeter {meter_id:"SM_00003", premise_id:"PREM_10003", tariff_class:"commercial",  phase:"three",  voltage_rating:400});
MERGE (:SmartMeter {meter_id:"SM_00004", premise_id:"PREM_10004", tariff_class:"residential", phase:"single", voltage_rating:230});
MERGE (:SmartMeter {meter_id:"SM_00005", premise_id:"PREM_10005", tariff_class:"industrial",  phase:"three",  voltage_rating:400});

// ── Relationships ─────────────────────────────────────────────────────────────
// GSP → Substation (FEEDS): properties describe the feeder cable
MATCH (g:GridSupplyPoint {gsp_id:"GSP_NORTH"})
MATCH (s:Substation {substation_id:"SS_001"})
MERGE (g)-[:FEEDS {feeder_id:"F_001", voltage_kV:11, length_km:2.4, cable_type:"XLPE"}]->(s);

MATCH (g:GridSupplyPoint {gsp_id:"GSP_NORTH"})
MATCH (s:Substation {substation_id:"SS_002"})
MERGE (g)-[:FEEDS {feeder_id:"F_002", voltage_kV:11, length_km:3.1, cable_type:"XLPE"}]->(s);

MATCH (g:GridSupplyPoint {gsp_id:"GSP_NORTH"})
MATCH (s:Substation {substation_id:"SS_003"})
MERGE (g)-[:FEEDS {feeder_id:"F_003", voltage_kV:11, length_km:5.8, cable_type:"PILC"}]->(s);

MATCH (g:GridSupplyPoint {gsp_id:"GSP_NORTH"})
MATCH (s:Substation {substation_id:"SS_004"})
MERGE (g)-[:FEEDS {feeder_id:"F_004", voltage_kV:11, length_km:8.2, cable_type:"XLPE"}]->(s);

MATCH (g:GridSupplyPoint {gsp_id:"GSP_SOUTH"})
MATCH (s:Substation {substation_id:"SS_005"})
MERGE (g)-[:FEEDS {feeder_id:"F_005", voltage_kV:11, length_km:4.5, cable_type:"XLPE"}]->(s);

MATCH (g:GridSupplyPoint {gsp_id:"GSP_SOUTH"})
MATCH (s:Substation {substation_id:"SS_006"})
MERGE (g)-[:FEEDS {feeder_id:"F_006", voltage_kV:11, length_km:6.3, cable_type:"PILC"}]->(s);

MATCH (g:GridSupplyPoint {gsp_id:"GSP_SOUTH"})
MATCH (s:Substation {substation_id:"SS_007"})
MERGE (g)-[:FEEDS {feeder_id:"F_007", voltage_kV:11, length_km:3.7, cable_type:"XLPE"}]->(s);

MATCH (g:GridSupplyPoint {gsp_id:"GSP_NORTH"})
MATCH (s:Substation {substation_id:"SS_008"})
MERGE (g)-[:FEEDS {feeder_id:"F_008", voltage_kV:11, length_km:1.9, cable_type:"XLPE"}]->(s);

MATCH (g:GridSupplyPoint {gsp_id:"GSP_NORTH"})
MATCH (s:Substation {substation_id:"SS_009"})
MERGE (g)-[:FEEDS {feeder_id:"F_009", voltage_kV:11, length_km:2.6, cable_type:"XLPE"}]->(s);

MATCH (g:GridSupplyPoint {gsp_id:"GSP_NORTH"})
MATCH (s:Substation {substation_id:"SS_010"})
MERGE (g)-[:FEEDS {feeder_id:"F_010", voltage_kV:11, length_km:1.5, cable_type:"XLPE"}]->(s);

// Substation → Transformer (SUPPLIES)
MATCH (s:Substation {substation_id:"SS_001"}) MATCH (t:Transformer {asset_id:"TX_001_A"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_001", distance_m:320}]->(t);
MATCH (s:Substation {substation_id:"SS_001"}) MATCH (t:Transformer {asset_id:"TX_001_B"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_002", distance_m:480}]->(t);
MATCH (s:Substation {substation_id:"SS_001"}) MATCH (t:Transformer {asset_id:"TX_001_C"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_003", distance_m:210}]->(t);
MATCH (s:Substation {substation_id:"SS_001"}) MATCH (t:Transformer {asset_id:"TX_001_D"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_004", distance_m:560}]->(t);
MATCH (s:Substation {substation_id:"SS_001"}) MATCH (t:Transformer {asset_id:"TX_001_E"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_005", distance_m:730}]->(t);
MATCH (s:Substation {substation_id:"SS_002"}) MATCH (t:Transformer {asset_id:"TX_002_A"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_006", distance_m:290}]->(t);
MATCH (s:Substation {substation_id:"SS_002"}) MATCH (t:Transformer {asset_id:"TX_002_B"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_007", distance_m:410}]->(t);
MATCH (s:Substation {substation_id:"SS_002"}) MATCH (t:Transformer {asset_id:"TX_002_C"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_008", distance_m:355}]->(t);
MATCH (s:Substation {substation_id:"SS_002"}) MATCH (t:Transformer {asset_id:"TX_002_D"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_009", distance_m:620}]->(t);
MATCH (s:Substation {substation_id:"SS_002"}) MATCH (t:Transformer {asset_id:"TX_002_E"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_010", distance_m:490}]->(t);
MATCH (s:Substation {substation_id:"SS_003"}) MATCH (t:Transformer {asset_id:"TX_003_A"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_011", distance_m:380}]->(t);
MATCH (s:Substation {substation_id:"SS_003"}) MATCH (t:Transformer {asset_id:"TX_003_B"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_012", distance_m:445}]->(t);
MATCH (s:Substation {substation_id:"SS_003"}) MATCH (t:Transformer {asset_id:"TX_003_C"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_013", distance_m:310}]->(t);
MATCH (s:Substation {substation_id:"SS_003"}) MATCH (t:Transformer {asset_id:"TX_003_D"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_014", distance_m:670}]->(t);
MATCH (s:Substation {substation_id:"SS_004"}) MATCH (t:Transformer {asset_id:"TX_004_A"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_015", distance_m:520}]->(t);
MATCH (s:Substation {substation_id:"SS_004"}) MATCH (t:Transformer {asset_id:"TX_004_B"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_016", distance_m:390}]->(t);
MATCH (s:Substation {substation_id:"SS_004"}) MATCH (t:Transformer {asset_id:"TX_004_C"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_017", distance_m:280}]->(t);
MATCH (s:Substation {substation_id:"SS_004"}) MATCH (t:Transformer {asset_id:"TX_004_D"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_018", distance_m:610}]->(t);
MATCH (s:Substation {substation_id:"SS_005"}) MATCH (t:Transformer {asset_id:"TX_005_A"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_019", distance_m:430}]->(t);
MATCH (s:Substation {substation_id:"SS_005"}) MATCH (t:Transformer {asset_id:"TX_005_B"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_020", distance_m:540}]->(t);
MATCH (s:Substation {substation_id:"SS_005"}) MATCH (t:Transformer {asset_id:"TX_005_C"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_021", distance_m:365}]->(t);
MATCH (s:Substation {substation_id:"SS_005"}) MATCH (t:Transformer {asset_id:"TX_005_D"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_022", distance_m:480}]->(t);
MATCH (s:Substation {substation_id:"SS_006"}) MATCH (t:Transformer {asset_id:"TX_006_A"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_023", distance_m:340}]->(t);
MATCH (s:Substation {substation_id:"SS_006"}) MATCH (t:Transformer {asset_id:"TX_006_B"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_024", distance_m:590}]->(t);
MATCH (s:Substation {substation_id:"SS_006"}) MATCH (t:Transformer {asset_id:"TX_006_C"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_025", distance_m:420}]->(t);
MATCH (s:Substation {substation_id:"SS_007"}) MATCH (t:Transformer {asset_id:"TX_007_A"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_026", distance_m:460}]->(t);
MATCH (s:Substation {substation_id:"SS_007"}) MATCH (t:Transformer {asset_id:"TX_007_B"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_027", distance_m:325}]->(t);
MATCH (s:Substation {substation_id:"SS_007"}) MATCH (t:Transformer {asset_id:"TX_007_C"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_028", distance_m:510}]->(t);
MATCH (s:Substation {substation_id:"SS_007"}) MATCH (t:Transformer {asset_id:"TX_007_D"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_029", distance_m:640}]->(t);
MATCH (s:Substation {substation_id:"SS_008"}) MATCH (t:Transformer {asset_id:"TX_008_A"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_030", distance_m:175}]->(t);
MATCH (s:Substation {substation_id:"SS_008"}) MATCH (t:Transformer {asset_id:"TX_008_B"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_031", distance_m:240}]->(t);
MATCH (s:Substation {substation_id:"SS_008"}) MATCH (t:Transformer {asset_id:"TX_008_C"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_032", distance_m:310}]->(t);
MATCH (s:Substation {substation_id:"SS_009"}) MATCH (t:Transformer {asset_id:"TX_009_A"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_033", distance_m:195}]->(t);
MATCH (s:Substation {substation_id:"SS_009"}) MATCH (t:Transformer {asset_id:"TX_009_B"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_034", distance_m:270}]->(t);
MATCH (s:Substation {substation_id:"SS_009"}) MATCH (t:Transformer {asset_id:"TX_009_C"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_035", distance_m:355}]->(t);
MATCH (s:Substation {substation_id:"SS_010"}) MATCH (t:Transformer {asset_id:"TX_010_A"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_036", distance_m:280}]->(t);
MATCH (s:Substation {substation_id:"SS_010"}) MATCH (t:Transformer {asset_id:"TX_010_B"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_037", distance_m:390}]->(t);
MATCH (s:Substation {substation_id:"SS_010"}) MATCH (t:Transformer {asset_id:"TX_010_C"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_038", distance_m:465}]->(t);
MATCH (s:Substation {substation_id:"SS_010"}) MATCH (t:Transformer {asset_id:"TX_010_D"}) MERGE (s)-[:SUPPLIES {cable_id:"CB_039", distance_m:520}]->(t);

// Transformer → SmartMeter (CONNECTS_TO)
MATCH (t:Transformer {asset_id:"TX_001_A"}) MATCH (m:SmartMeter {meter_id:"SM_00001"}) MERGE (t)-[:CONNECTS_TO]->(m);
MATCH (t:Transformer {asset_id:"TX_001_A"}) MATCH (m:SmartMeter {meter_id:"SM_00002"}) MERGE (t)-[:CONNECTS_TO]->(m);
MATCH (t:Transformer {asset_id:"TX_001_B"}) MATCH (m:SmartMeter {meter_id:"SM_00003"}) MERGE (t)-[:CONNECTS_TO]->(m);
MATCH (t:Transformer {asset_id:"TX_001_C"}) MATCH (m:SmartMeter {meter_id:"SM_00004"}) MERGE (t)-[:CONNECTS_TO]->(m);
MATCH (t:Transformer {asset_id:"TX_001_C"}) MATCH (m:SmartMeter {meter_id:"SM_00005"}) MERGE (t)-[:CONNECTS_TO]->(m);
