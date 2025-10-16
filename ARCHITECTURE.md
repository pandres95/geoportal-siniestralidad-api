# Geo‑Portal Backend — Unified Overview

## 🧭 System Summary

A minimal, serverless, and fully containerized backend for managing, storing, and serving geospatial accident data as an open REST/OGC API.

The stack ingests raw GeoJSON data of traffic accidents (with injuries and fatalities) into a Neon serverless PostGIS database and exposes it publicly using **pg\_featureserv**.

Everything is stateless except the database. Deployment and scaling are fully automated.

---

## 🗺️ Architecture Diagram (Mermaid)

```mermaid
flowchart LR
  classDef svc fill:#17233c,stroke:#6d7aa6,color:#e7ecf7,rx:10;
  classDef data fill:#0f2f2a,stroke:#2a6a5b,color:#e7ecf7,rx:10;
  classDef client fill:#3b2a16,stroke:#6c5233,color:#ffe9c7,rx:10;
  classDef note fill:#121a2b,stroke:#2a3551,color:#9fb0d9,rx:6;

  subgraph DB[Neon (Serverless PostGIS)]
    direction TB
    T1["accidents_injuries\n• occurred_at (btree)\n• geom (GiST)"]:::data
    T2["accidents_fatalities\n• occurred_at (btree)\n• geom (GiST)"]:::data
  end

  LDR["Loader (Python)\nGeoPandas · Pandas · Psycopg2\n• Coerce Time → String\n• Clean NaN → null\n• Bulk INSERT"]:::svc
  API["pg_featureserv (OGC API – Features)\n/collections · /items · CQL · bbox · properties"]:::svc
  FE["Frontend / Client\nMapLibre · Leaflet · Deck.gl"]:::client

  LDR -- "COPY / execute_values (bulk)" --> T1
  LDR -- "COPY / execute_values (bulk)" --> T2
  DB -- "read-only SQL" --> API
  API -- "HTTPS GeoJSON" --> FE

  N1(["Stateless services: only Neon stores data → easy redeploys"]):::note
  N2(["Filters: bbox, CQL (e.g., edad BETWEEN 20 AND 35), properties= projection"]):::note
  N3(["Optional: add pg_tileserv for vector tiles"]):::note

  N1 -.-> API
  N2 -.-> API
  N3 -.-> API
```

---

## 🗃️ Database Layer — Neon (Serverless PostGIS)

**Engine:** PostgreSQL 16 + PostGIS 3.4\
**Behavior:** Auto‑pause when idle, fast cold starts

### Schema

```sql
CREATE TABLE public.accidents_template (
  id bigserial PRIMARY KEY,
  codigo_acc text NOT NULL,
  formulario text,
  occurred_at timestamptz NOT NULL,
  edad smallint,
  genero text,
  condicion text,
  geom geometry(Point, 4326) NOT NULL,
  extra_props jsonb
);
```

Tables:

- `accidents_injuries`
- `accidents_fatalities`

### Indexes

```sql
CREATE INDEX ON accidents_injuries (occurred_at);
CREATE INDEX ON accidents_injuries USING gist (geom);
CREATE INDEX ON accidents_fatalities (occurred_at);
CREATE INDEX ON accidents_fatalities USING gist (geom);
```

---

## ⚙️ Loader (Python Service)

Responsible for ingesting GeoJSON data into Neon.

### Flow

1. Reads `.geojson` or `.json` from `/data`
2. Parses `FECHA_OCUR` + `HORA_OCURR` → `occurred_at`
3. Cleans `NaN` and string `'NaN'` values → `null`
4. Converts geometries to WKT
5. Bulk‑inserts using `execute_values`

### Stack

| Library   | Use                       |
| --------- | ------------------------- |
| GeoPandas | Read & validate GeoJSON   |
| Pandas    | Clean & transform data    |
| Psycopg2  | Connect to Neon / PostGIS |
| Shapely   | Geometry parsing          |

---

## 🌐 API Layer — pg\_featureserv

Exposes PostGIS data via REST/OGC endpoints.

### Features

- Auto‑discovers tables/views
- Returns **GeoJSON**
- Filters:
  - `bbox=minLon,minLat,maxLon,maxLat`
  - `filter=edad BETWEEN 20 AND 35` (CQL)
  - `properties=codigo_acc,edad,occurred_at`
- Can be extended with pg\_tileserv for vector tiles.

### Example Queries

```http
GET /collections/accidents_with_injuries/items?filter=edad BETWEEN 20 AND 35
GET /collections/accidents_with_injuries/items?bbox=-74.2,4.55,-73.95,4.90
GET /collections/accidents_with_injuries/items?properties=codigo_acc,edad,occurred_at
```

---

## ☁️ Deployment (Render)

### Why Render

- No CLI needed
- Free HTTPS + subdomain
- One environment variable

### Steps

1. Create **Web Service → Existing Image**
   - Image: `pramsey/pg_featureserv:latest`
2. Add `DATABASE_URL` from Neon:

   ```
   postgres://user:pwd@ep-xxx.neon.tech/db?sslmode=require&options=endpoint%3Dep-xxx
   ```

3. Expose port **9000**
4. Deploy → `https://geoapi.onrender.com/collections`

---

## 🧩 Extension Points

| Need                          | Solution                           |
| ----------------------------- | ---------------------------------- |
| **Vector tiles**              | Add `pg_tileserv` container        |
| **Auth / Access control**     | Add reverse proxy or API gateway   |
| **Additional datasets**       | Append new GeoJSON → extend loader |
| **Computed fields / aliases** | Define SQL views                   |

---

## 🧠 Developer Notes

- **Stateless design** — only Neon stores data
- **Easy migrations** — re‑deploy containers anywhere
- **CI integration** — loader can run in GitHub Actions
- **Front‑end ready** — any map library can consume GeoJSON output

---

*Maintainer: @pandre95 — Last updated: 2025‑10‑16*
