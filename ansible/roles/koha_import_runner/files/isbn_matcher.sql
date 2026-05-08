-- ============================================================================
-- ISBN matcher seed
-- ----------------------------------------------------------------------------
-- Maakt een matcher aan met code 'ISBN' die op 020$a zoekt. Idempotent:
-- alleen invoegen als hij nog niet bestaat.
--
-- Schema (4 gekoppelde tabellen):
--   marc_matchers          : de matcher zelf
--   matchpoints            : welke index gebruiken (1 matcher kan meerdere)
--   matchpoint_components  : MARC tag + subfield(s)
--   matcher_matchpoints    : koppelt matcher <-> matchpoint (M:N)
--
-- Threshold 1000 = exacte match nodig. Score 1000 op het matchpoint = volle
-- gewicht. Dat samen betekent: 020$a moet exact gelijk zijn voor een hit.
-- ============================================================================

-- Stap 1: marc_matchers
INSERT INTO marc_matchers (code, description, record_type, threshold)
SELECT 'ISBN', 'ISBN match op 020a', 'biblio', 1000
WHERE NOT EXISTS (SELECT 1 FROM marc_matchers WHERE code = 'ISBN');

-- Stap 2: matchpoint
INSERT INTO matchpoints (matcher_id, search_index, score)
SELECT m.matcher_id, 'isbn', 1000
FROM marc_matchers m
WHERE m.code = 'ISBN'
  AND NOT EXISTS (
    SELECT 1 FROM matchpoints mp
    WHERE mp.matcher_id = m.matcher_id
      AND mp.search_index = 'isbn'
  );

-- Stap 3: matchpoint_component (welke MARC tag)
-- Backticks rond `offset` en `length` omdat dit MariaDB gereserveerde woorden zijn
INSERT INTO matchpoint_components (matchpoint_id, sequence, tag, subfields, `offset`, `length`)
SELECT mp.matchpoint_id, 0, '020', 'a', 0, 0
FROM matchpoints mp
JOIN marc_matchers m ON m.matcher_id = mp.matcher_id
WHERE m.code = 'ISBN'
  AND NOT EXISTS (
    SELECT 1 FROM matchpoint_components mc
    WHERE mc.matchpoint_id = mp.matchpoint_id
      AND mc.tag = '020'
  );

-- Stap 4: koppel matcher <-> matchpoint
INSERT INTO matcher_matchpoints (matcher_id, matchpoint_id)
SELECT m.matcher_id, mp.matchpoint_id
FROM marc_matchers m
JOIN matchpoints mp ON mp.matcher_id = m.matcher_id
WHERE m.code = 'ISBN'
  AND NOT EXISTS (
    SELECT 1 FROM matcher_matchpoints mm
    WHERE mm.matcher_id = m.matcher_id
      AND mm.matchpoint_id = mp.matchpoint_id
  );

-- Toon resultaat
SELECT 'Matcher created/exists:' AS info;
SELECT m.matcher_id, m.code, m.description, m.threshold,
       mp.search_index, mc.tag, mc.subfields
FROM marc_matchers m
LEFT JOIN matchpoints mp ON mp.matcher_id = m.matcher_id
LEFT JOIN matchpoint_components mc ON mc.matchpoint_id = mp.matchpoint_id
WHERE m.code = 'ISBN';