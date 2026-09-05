-- Esquema del índice de trazabilidad del PPI.
-- Compatible con SQLite (uso diario) y PostgreSQL (opcional, ver compose/).
-- Nada de lo que hay aquí es fuente de verdad: todo se reconstruye con
-- `ppi-trace ingest` desde los .md y .csv versionados. Si la base se borra,
-- no se pierde información. Ese es el punto.

CREATE TABLE IF NOT EXISTS requisito (
  id            TEXT PRIMARY KEY,        -- REQ-001
  texto         TEXT NOT NULL,
  origen        TEXT,                    -- Jurado obs.1 / Sesión 02 diap.33
  fase          TEXT,                    -- F04
  estado        TEXT,                    -- cumplido | parcial | no_cumplido
  evidencia     TEXT,
  responsable   TEXT,
  compromiso    TEXT                     -- fecha ISO o vacío
);

CREATE TABLE IF NOT EXISTS claim (
  id            TEXT PRIMARY KEY,        -- CLAIM-004
  texto         TEXT NOT NULL,
  estado        TEXT,                    -- OBTENIDO|VALIDADO|PLANIFICADO|REFUTADO
  fuente        TEXT                     -- ruta relativa dentro del producto
);

CREATE TABLE IF NOT EXISTS enlace (          -- requisito <-> claim <-> artefacto
  requisito     TEXT,
  claim         TEXT,
  artefacto     TEXT,
  fuente        TEXT,
  estado        TEXT
);

CREATE TABLE IF NOT EXISTS riesgo (
  id TEXT PRIMARY KEY, texto TEXT, severidad TEXT, estado TEXT, mitigacion TEXT
);

CREATE TABLE IF NOT EXISTS entregable (
  id TEXT PRIMARY KEY, nombre TEXT, estado TEXT, ruta TEXT
);

-- Un artefacto es un archivo real del producto, con su hash en el momento de
-- la indexación. Si el hash cambia, las afirmaciones que lo citan quedan en
-- observación: no se invalidan solas, pero se listan con `ppi-trace check`.
CREATE TABLE IF NOT EXISTS artefacto (
  ruta          TEXT PRIMARY KEY,
  sha256        TEXT,
  bytes         INTEGER,
  visto         TEXT                     -- timestamp ISO de la indexación
);

-- Cifra extraída del texto de un claim. Permite responder «¿de dónde sale
-- este número?» sin depender de que alguien recuerde en qué documento estaba.
CREATE TABLE IF NOT EXISTS cifra (
  valor         TEXT,                    -- normalizada: 88.8
  crudo         TEXT,                    -- tal como aparece: 88,8 %
  claim         TEXT,
  contexto      TEXT
);

CREATE INDEX IF NOT EXISTS ix_cifra_valor  ON cifra(valor);
CREATE INDEX IF NOT EXISTS ix_enlace_req   ON enlace(requisito);
CREATE INDEX IF NOT EXISTS ix_enlace_claim ON enlace(claim);
