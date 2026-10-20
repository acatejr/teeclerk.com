-- Golf course schema, derived from the Tucson City Golf scorecards in data/tucson/.
-- Target: SQLite 3 (standard SQL; ports to PostgreSQL with minor type changes).

PRAGMA foreign_keys = ON;

-- Organization that runs one or more facilities (e.g. Tucson City Golf).
CREATE TABLE operator (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    website     TEXT
);

-- A physical location with an address. A facility can hold several courses
-- (Randolph has North and Dell Urich).
CREATE TABLE facility (
    id           INTEGER PRIMARY KEY,
    operator_id  INTEGER REFERENCES operator(id),
    name         TEXT NOT NULL,
    street       TEXT,
    city         TEXT,
    state        TEXT,
    postal_code  TEXT,
    phone        TEXT,
    website      TEXT,
    UNIQUE (operator_id, name)
);

CREATE TABLE course (
    id                  INTEGER PRIMARY KEY,
    facility_id         INTEGER NOT NULL REFERENCES facility(id),
    name                TEXT NOT NULL,
    hole_count          INTEGER NOT NULL DEFAULT 18 CHECK (hole_count IN (9, 18)),
    scorecard_revision  TEXT,   -- revision printed on the card, e.g. '09/25'
    UNIQUE (facility_id, name)
);

CREATE TABLE hole (
    id         INTEGER PRIMARY KEY,
    course_id  INTEGER NOT NULL REFERENCES course(id),
    number     INTEGER NOT NULL CHECK (number BETWEEN 1 AND 18),
    par        INTEGER NOT NULL CHECK (par BETWEEN 3 AND 6),
    UNIQUE (course_id, number)
);

-- A set of tees. Base tees (Blue, White, Gold, Red, Silver, Yellow) have their
-- own markers; combo tees (Blue/White, White/Gold, ...) mix two base tees hole by
-- hole, as shown by the triangle markers on the cards.
CREATE TABLE tee (
    id          INTEGER PRIMARY KEY,
    course_id   INTEGER NOT NULL REFERENCES course(id),
    name        TEXT NOT NULL,
    is_combo    INTEGER NOT NULL DEFAULT 0 CHECK (is_combo IN (0, 1)),
    sort_order  INTEGER NOT NULL,   -- longest first, as printed
    UNIQUE (course_id, name)
);

-- Per-hole setting for a tee. Base tees store yards; combo tees point at the
-- base tee used on that hole. Totals (OUT/IN/TOT) are derived, see views below.
CREATE TABLE tee_hole (
    tee_id         INTEGER NOT NULL REFERENCES tee(id),
    hole_id        INTEGER NOT NULL REFERENCES hole(id),
    yards          INTEGER CHECK (yards > 0),
    source_tee_id  INTEGER REFERENCES tee(id),
    PRIMARY KEY (tee_id, hole_id),
    CHECK ((yards IS NULL) <> (source_tee_id IS NULL)),
    CHECK (source_tee_id IS NULL OR source_tee_id <> tee_id)
);

-- A named stroke-index (hole handicap) allocation. Cards print two per course,
-- labeled either by gender ("Men's" / "Women's") or by tee ("Handicap" /
-- "Red/Silver Handicap", "Gold/Red Handicap").
CREATE TABLE stroke_index_set (
    id         INTEGER PRIMARY KEY,
    course_id  INTEGER NOT NULL REFERENCES course(id),
    name       TEXT NOT NULL,
    UNIQUE (course_id, name)
);

CREATE TABLE hole_stroke_index (
    stroke_index_set_id  INTEGER NOT NULL REFERENCES stroke_index_set(id),
    hole_id              INTEGER NOT NULL REFERENCES hole(id),
    stroke_index         INTEGER NOT NULL CHECK (stroke_index BETWEEN 1 AND 18),
    PRIMARY KEY (stroke_index_set_id, hole_id),
    UNIQUE (stroke_index_set_id, stroke_index)
);

-- USGA course rating / slope per tee and gender. A missing row means the card
-- shows "--" (no rating). Each rating names the stroke-index set that applies.
CREATE TABLE tee_rating (
    tee_id               INTEGER NOT NULL REFERENCES tee(id),
    gender               TEXT NOT NULL CHECK (gender IN ('M', 'F')),
    course_rating        REAL NOT NULL CHECK (course_rating > 0),
    slope_rating         INTEGER NOT NULL CHECK (slope_rating BETWEEN 55 AND 155),
    stroke_index_set_id  INTEGER NOT NULL REFERENCES stroke_index_set(id),
    PRIMARY KEY (tee_id, gender)
);

-- Local rules and notices printed on the card. Randolph's rules cover both of
-- its courses, so these hang off the facility; course_id narrows one to a course.
CREATE TABLE facility_rule (
    id           INTEGER PRIMARY KEY,
    facility_id  INTEGER NOT NULL REFERENCES facility(id),
    course_id    INTEGER REFERENCES course(id),
    kind         TEXT NOT NULL CHECK (kind IN ('local_rule', 'caution')),
    position     INTEGER NOT NULL,
    body         TEXT NOT NULL,
    UNIQUE (facility_id, kind, position)
);

-- Yardage for every tee on every hole, with combo tees resolved to their source.
CREATE VIEW v_tee_hole_yardage AS
SELECT t.course_id,
       t.id                                 AS tee_id,
       t.name                               AS tee_name,
       h.number                             AS hole_number,
       h.par,
       COALESCE(th.yards, src.yards)        AS yards,
       COALESCE(th.source_tee_id, t.id)     AS played_from_tee_id
FROM tee t
JOIN tee_hole th ON th.tee_id = t.id
JOIN hole h      ON h.id = th.hole_id
LEFT JOIN tee_hole src
       ON src.tee_id = th.source_tee_id AND src.hole_id = th.hole_id;

-- OUT / IN / TOT columns of the scorecard.
CREATE VIEW v_tee_totals AS
SELECT course_id,
       tee_id,
       tee_name,
       SUM(CASE WHEN hole_number <= 9 THEN yards END) AS out_yards,
       SUM(CASE WHEN hole_number >= 10 THEN yards END) AS in_yards,
       SUM(yards)                                      AS total_yards,
       SUM(par)                                        AS total_par
FROM v_tee_hole_yardage
GROUP BY course_id, tee_id, tee_name;
