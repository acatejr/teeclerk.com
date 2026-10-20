# teeclerk.com

The start of a golf club management and scoring system. The first data set is the Tucson City Golf courses.

## What's here

| Path | Contents |
|---|---|
| `data/tucson/` | Scorecard PDFs for El Rio, Fred Enke, Randolph North, Randolph Dell Urich and Silverbell |
| `db/schema.sql` | SQLite schema for operators, facilities, courses, holes, tees, ratings, stroke indexes and local rules |
| `db/SCHEMA.md` | Design notes for the schema |
| `db/schema.png`, `db/schema.svg` | Schema diagram |
| `db/load_scorecards.py` | Loads the scorecard data into SQLite and checks it against the printed totals |
| `db/golf.db` | The loaded database |
| `tourney_scoring.md` | Plan for tournament scoring, starting with gross and net skins |

## Building the database

Requires Python 3 (standard library only).

```sh
python3 db/load_scorecards.py              # writes db/golf.db
python3 db/load_scorecards.py other.db     # or a path of your choice
```

The script creates the schema if the database is empty and refuses to load into a database that already has data. Every tee's OUT/IN/TOT yardage is checked against the totals printed on the cards; if any don't match, nothing is loaded.

To rebuild from scratch, delete `db/golf.db` first.

## Example query

```sh
sqlite3 db/golf.db "SELECT tee_name, out_yards, in_yards, total_yards, total_par FROM v_tee_totals ORDER BY course_id, total_yards DESC;"
```

## Status

- Done: course schema and Tucson City Golf course data.
- Next: tournament score entry and gross/net skins (see `tourney_scoring.md`).
