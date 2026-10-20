# Golf Course Database Schema

Design notes for `db/schema.sql`, developed from the Tucson City Golf scorecard PDFs in `data/tucson/`:

- TCG-El-Rio-Scorecard.pdf
- TCG-Fred-Enke-Scorecard.pdf
- TCG-Randolph-Dell-Urich-Scorecard.pdf
- TCG-Randolph-North-Scorecard.pdf
- TCG-Silverbell-Scorecard.pdf

Target database: SQLite 3. The SQL is standard and should port to PostgreSQL with a few type changes.

## What the scorecards contain

- **Operator and locations.** Tucson City Golf runs four locations. Randolph has two courses, North and Dell Urich. Each location has an address, phone number and website.
- **Holes.** Each hole has a par and a yardage for every tee.
- **Two kinds of tees.**
  - Single tees (Blue, White, Gold, Red, Silver, Yellow) have their own yardages.
  - Combined tees (Blue/White, White/Gold, Gold/Red, White/Red, White/Yellow, Yellow/Red) mix two single tees hole by hole. Small triangles on the card show which single tee is used on each hole. Only the total yardage is printed, but combined tees have their own ratings.
- **Rating and slope.** Each tee has a course rating and slope, separately for men and women. Some are blank ("--"). El Rio's Silver tee is rated for women only.
- **Handicap (stroke index) rows.** Each course prints two rows ranking hole difficulty from 1 to 18.
  - Randolph North, Randolph Dell Urich and Silverbell label them Men's and Women's.
  - El Rio labels them "Handicap" and "Red/Silver Handicap".
  - Fred Enke labels them "Handicap" and "Gold/Red Handicap".
- **Other card content.** Local rules, a caution notice, and a card revision date (for example 09/25).

## Tables

| Table | Holds |
|---|---|
| `operator` | The organization running the locations (Tucson City Golf) |
| `facility` | A location with an address, phone and website (Randolph, El Rio, ...) |
| `course` | A course at a location (North, Dell Urich), with hole count and card revision date |
| `hole` | Hole number and par |
| `tee` | Each tee for a course, with a flag for combined tees and a display order |
| `tee_hole` | Single tees store yards per hole; combined tees point to the single tee used on that hole |
| `stroke_index_set` | A named handicap row ("Men's", "Red/Silver Handicap", ...) |
| `hole_stroke_index` | The 1–18 ranking of each hole within a handicap row |
| `tee_rating` | Course rating and slope per tee and gender, plus which handicap row applies |
| `facility_rule` | Local rules and caution notices, optionally narrowed to one course |

### Views

| View | Shows |
|---|---|
| `v_tee_hole_yardage` | Yardage per hole for every tee, with combined tees resolved to their source tee |
| `v_tee_totals` | The scorecard's OUT / IN / TOT yardage and total par for every tee |

## Design decisions

- **Totals are calculated, not stored.** OUT/IN/TOT and combined-tee yardages come from the views, so they can't drift out of sync with the hole data.
- **Combined tees reference single tees.** A `tee_hole` row has either `yards` (single tee) or `source_tee_id` (combined tee), never both. A check constraint enforces this.
- **Handicap rows are named sets, linked from ratings.** The cards label the rows by gender at some courses and by tee at others. Linking each `tee_rating` (tee + gender) to a `stroke_index_set` handles both.
- **A missing rating is a missing row.** A "--" on the card means no `tee_rating` row for that tee and gender.
- **Rules belong to the location.** Randolph's rules cover both courses, so `facility_rule` hangs off `facility`, with an optional `course_id`.

## Testing

I loaded Randolph North's Blue, White and Blue/White data into a scratch database. The calculated totals match the card exactly:

| Tee | OUT | IN | TOT | Par |
|---|---|---|---|---|
| Blue | 3394 | 3489 | 6883 | 72 |
| Blue/White | 3234 | 3405 | 6639 | 72 |
| White | 3154 | 3342 | 6496 | 72 |

The constraints also rejected bad rows: a `tee_hole` row with both yards and a source tee, and two holes in the same handicap row with the same ranking.

## Assumptions and open questions

- **El Rio and Fred Enke handicap rows.** I assumed the tee-labeled row (for example "Red/Silver Handicap") applies to those tees for both men and women, and the other row applies to all other tees. The cards don't say this outright; it needs confirming.
- **Par is stored once per hole.** That covers these cards, but some courses set a different par for women. Supporting that would need a per-tee par override.
- **No 9-hole ratings.** The cards don't print front-nine or back-nine ratings, so the schema has no columns for them.
- **Dell Urich's card revision date** wasn't visible in what I could read from the PDF.
- **One revision date per course.** Card history isn't kept, so new ratings overwrite old ones.
- **Combined-tee source tees aren't checked against the course.** Nothing in the schema stops a combined tee from pointing at a tee on another course. A trigger could enforce it.

## Next step: loading the card data

The schema has no data from the cards yet. Reading the triangle markers by eye is error-prone: on North's White/Gold I first got 6193 against the printed 6216 because I misread hole 14. When entering the cards, check every tee in `v_tee_totals` against the printed OUT/IN/TOT values so misreads show up.
