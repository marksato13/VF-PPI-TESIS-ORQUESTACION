-- Vistas de consulta rapida. Validas en SQLite y PostgreSQL.

-- Lo que el jurado va a preguntar primero: que falta y para cuando.
CREATE VIEW IF NOT EXISTS v_pendiente AS
SELECT id, texto, estado, responsable, compromiso
FROM requisito
WHERE estado <> 'cumplido'
ORDER BY CASE WHEN compromiso = '' THEN 1 ELSE 0 END, compromiso;

-- Afirmaciones sin archivo que las respalde: candidatas a no ser citables.
CREATE VIEW IF NOT EXISTS v_claim_sin_respaldo AS
SELECT id, texto, estado, fuente
FROM claim
WHERE fuente = '' OR fuente NOT LIKE '%/%';

-- Requisitos declarados cumplidos que ningun claim sostiene.
CREATE VIEW IF NOT EXISTS v_cumplido_sin_prueba AS
SELECT r.id, r.texto, r.evidencia
FROM requisito r
WHERE r.estado LIKE 'cumplido%'
  AND r.id NOT IN (SELECT requisito FROM enlace WHERE claim <> '');
