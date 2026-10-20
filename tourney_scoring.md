# Tournament Scoring Plan

A plan for entering each player's round in a tournament, picking winners under several formats, and paying out skins. It builds on the course schema in `db/schema.sql` (see `db/SCHEMA.md`).

## Goals

**First priority: gross and net skins.** The other tournament formats come later.

1. Set up a tournament: course, date(s), tees, players, and which competitions are running.
2. Enter hole-by-hole scores for each player.
3. Calculate gross and net skins and the payout per skin.
4. Later: leaderboards and winners for stroke play, Stableford and team formats, with flights, teams and tiebreakers.

## Guiding principles

- **Store raw scores, calculate results.** As with OUT/IN/TOT in `v_tee_totals`, totals, net scores, points and skins are calculated from hole scores rather than stored. A mistyped score is fixed in one place and every result updates.
- **Snapshot anything that can change after the round.** Handicap Index, course rating, slope and par change over time. Copy them onto the scorecard when the player is entered, so results don't shift later. This also closes the "no rating history" gap in `SCHEMA.md`.
- **One set of scores, many competitions.** Players often play gross, net and skins off the same card. A tournament holds several *competitions* that all read the same scores.
- **Keep the scoring engine pure.** Calculations live in plain Python functions that take scores and settings and return results, with no database access. That makes them easy to test against hand-worked examples.

## Data model additions

New tables, added to `db/schema.sql`:

| Table | Holds |
|---|---|
| `player` | Name, gender (`M`/`F`, to pick the rating), optional GHIN number, contact info |
| `tournament` | Name, facility, start and end dates, status (`setup`, `in_progress`, `final`) |
| `tournament_round` | Round number, course and date. A one-day event has one row; a two-day event has two |
| `flight` | *(Later)* Optional grouping by Handicap Index range or by name (Championship, A, B, ...) |
| `entry` | A player in a tournament: Handicap Index snapshot, tee, flight |
| `team` / `team_member` | *(Later)* Teams for team formats, with each member's entry |
| `competition` | One contest in the tournament: format, gross or net, handicap allowance, team size, entry fee, settings |
| `competition_entry` | Who is in each competition (skins is usually opt-in) |
| `scorecard` | One card per round, owned by either an entry or a team. Holds snapshots of the course handicap, playing handicap, course rating, slope, par and stroke-index set, plus a status (`open`, `final`, `WD`, `DQ`) |
| `hole_score` | Strokes for one hole on one scorecard. A missing row means the hole wasn't played or wasn't entered |

For skins, only `player`, `tournament`, `tournament_round`, `entry`, `competition`, `competition_entry`, `scorecard` and `hole_score` are needed. `entry.flight_id` and `scorecard.team_id` can be added as nullable columns when those features arrive.

Notes:

- A `scorecard` has either `entry_id` or `team_id`, never both, enforced with a check constraint like the one on `tee_hole`.
- Scramble and other one-ball team formats get a team scorecard. Best ball and shamble use each player's own card, and the team score is calculated from those.
- Format-specific options (for example the Stableford points table, or whether skins carry over) go in `competition.settings` as JSON, so new options don't require schema changes.
- If a tournament needs a frozen result after it's final (for a trophy record, say), add a `competition_result` table written once at finalization. Until then, everything is calculated.

## Handicap calculations

Based on the World Handicap System (WHS):

1. **Course Handicap** = Handicap Index × (Slope ÷ 113) + (Course Rating − Par), rounded to the nearest whole number. Slope and Course Rating come from `tee_rating` for the player's tee and gender.
2. **Playing Handicap** = Course Handicap × format allowance, rounded. Default allowances (WHS Appendix C, check against the current rules before release):

   | Format | Allowance |
   |---|---|
   | Individual stroke play | 95% |
   | Individual Stableford | 95% |
   | Four-ball (best ball) stroke play | 85% |
   | Singles match play | 100% |
   | 2-player scramble | 35% low / 15% high |
   | 4-player scramble | 25% / 20% / 15% / 10%, lowest to highest |

   Allowances are stored on the competition so the committee can override them.
3. **Strokes per hole.** Hand out strokes by the stroke-index set linked from the player's `tee_rating`: one stroke on holes ranked 1 through N; past 18, a second stroke starting again at 1. Plus handicaps give strokes back starting at index 18.
4. **Mixed tees and genders.** The (Course Rating − Par) term already adjusts players on different tees. Par is stored once per hole, so this holds as long as par doesn't differ by tee (see the open question in `SCHEMA.md`).

## Formats (later)

Not part of the first build. Kept here so the data model leaves room for them.

Each format is a function that takes the scorecards and competition settings and returns a ranked list.

| Format | Scoring | Lower or higher wins |
|---|---|---|
| Stroke play (gross) | Total strokes | Lower |
| Stroke play (net) | Total strokes − playing handicap | Lower |
| Stableford | Points per hole from the net score vs par. Standard: 0 for double bogey or worse, 1 bogey, 2 par, 3 birdie, 4 eagle, 5 albatross | Higher |
| Modified Stableford | Same, with a configurable table (for example −3 / −1 / 0 / +2 / +5 / +8) | Higher |
| Best ball (four-ball) | Team's lowest net (or gross) score on each hole, summed | Lower |
| Two best balls of four | Sum of the 2 lowest scores per hole; the count is a setting | Lower |
| Scramble | Team scorecard; team playing handicap from the scramble allowances | Lower |
| Shamble | Each player's own card; scored like best ball | Lower |
| Match play | Later phase; needs pairings and brackets | — |

Multi-round tournaments add up the rounds per competition. Flights are ranked separately when a competition is flighted.

### Tiebreakers (later)

Skins don't need tiebreakers: a tie on a hole means no skin. Configurable per competition, in this order by default:

1. Card-off (matching scorecards): best score over the back 9, then back 6, back 3 and the 18th hole. For net, subtract ½, ⅓, ⅙ and 1/18 of the playing handicap for each segment.
2. For shotgun starts, an option to compare holes 10–18 regardless of where the player started, or to use the last 9 holes played.
3. If still tied: report a tie, so the committee can call a playoff or split the prize.

## Skins

Gross and net skins are separate competitions in the same tournament. A player can enter one, both or neither, each with its own entry fee and pot.

- **Gross skins** use the strokes on the card. No handicap is involved.
- **Net skins** subtract the player's handicap strokes on each hole (see "Strokes per hole" above). The handicap allowance is a competition setting; 100% of the course handicap is the default until the club says otherwise.

For each hole, among the players in the skins competition:

1. Work out each player's gross or net score on the hole. Net skins can use full strokes or half strokes (each handicap stroke counts as ½); that's a setting.
2. If exactly one player has the lowest score, they win the skin.
3. If two or more tie, there's no skin. With **carryover** turned on, the skin is added to the next hole. A setting decides what happens to carryovers left after the 18th (drop them, or split them among the 18th-hole winners).
4. **Payout:** pot = number of players × entry fee (minus any fee taken by the house). Value per skin = pot ÷ skins won. If no skins are won, the pot is refunded or rolled over, as set by the committee.
5. Round amounts to cents and report any leftover so the totals match.
6. A player with a missing hole score can't win that hole, and that hole is skipped for them. A `WD` or `DQ` card is left out of every hole.

**Skins report:** for each competition, list each hole with its winner, score and number of skins (including carryovers), followed by each winner's total skins and payout.

## Score entry

- **Phase 1: file import and CLI.** A CSV with one row per player and 18 hole columns, plus a command-line tool to fix single holes. Validate as you go: strokes between 1 and 20, hole numbers that exist on the course, and a warning when a card is missing holes.
- **Phase 2: web form.** Hole-by-hole entry per group, with running totals so the person entering can check them against the paper card (the same check `load_scorecards.py` does for yardages).
- **Finalizing:** a card becomes `final` once all holes are in. Leaderboards show unfinished cards as "thru N", and the tournament can't be finalized until every card is `final`, `WD` or `DQ`.

## Code layout

```
scoring/
    models.py       # Dataclasses: Scorecard, HoleScore, Competition, settings
    handicap.py     # Course handicap, playing handicap, strokes per hole
    formats.py      # Stroke play, Stableford, best ball, scramble, shamble
    tiebreak.py     # Card-off and shotgun rules
    skins.py        # Skins, carryovers, payouts
    leaderboard.py  # Runs competitions, groups by flight, applies tiebreakers
db/
    repository.py   # Reads and writes the database, builds the dataclasses
cli.py              # Tournament setup, score import, leaderboard and skins reports
tests/
```

## Testing

- Unit-test each function against hand-worked examples: a plus handicap, a handicap over 18, a three-way skins tie with carryover, a card-off that goes to the 18th hole.
- Use the real Tucson course data in `db/golf.db` for tests that cover a full round.
- Check the handicap math against the USGA's published course handicap tables for one Tucson course and tee.

## Phases

1. **Schema and handicap math.** The tables skins needs, course and playing handicap, stroke allocation. Tests.
2. **Gross and net skins.** CSV score import, skins calculation with carryover and payouts, and a CLI skins report. **This is the first deliverable.**
3. **Individual stroke play.** Gross and net leaderboards, flights, tiebreakers.
4. **Stableford and team formats.** Stableford, modified Stableford, best ball, scramble, shamble.
5. **Multi-round tournaments.** Totals across rounds, cuts if needed.
6. **Web score entry and live leaderboard.**
7. **Match play** (pairings, brackets), if needed.

## Open questions

- Which formats does the club run after skins? That decides the order of phases 3 and 4.
- Where do Handicap Indexes come from: typed in by hand, or imported from GHIN? I don't know what GHIN access is available.
- For net skins: what handicap allowance (100% or less), and full or half strokes?
- Do skins carry over? If so, what happens to carryovers after the 18th?
- Does the house take a cut of the skins pot?
- Who enters scores (pro shop staff, or players on their phones)? That shapes the phase 5 design and whether logins are needed.
- Should the default allowances be the WHS values above, or does the club use its own?
