"""Load the Tucson City Golf scorecards (data/tucson/*.pdf) into db/golf.db.

Values were transcribed from the PDFs. Combo tees are given as an 18-letter
string read from the triangle markers: U = the upper (longer) tee of the pair
is played on that hole, L = the lower one.

Before committing, every tee's computed OUT/IN/TOT (from v_tee_totals) is
checked against the totals printed on the card; any mismatch aborts the load.

Usage: python3 db/load_scorecards.py [path/to/golf.db]
"""

import sqlite3
import sys
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent
WEBSITE = "www.tucsoncitygolf.com"

STANDARD_RULES = [
    "Please repair ball marks on greens and rake bunkers. Use sand to fill divots if provided.",
    "Please keep all carts 30 yards from tees and greens. Use cart paths where provided.",
]
FREE_RELIEF_ROCKS = "Free relief from rocks with wire mesh to include penalty areas (Rule 16.1a(1) applies)."
FREE_RELIEF_PATHS = (
    "Free relief no nearer the hole from paths, guard screens, staked trees, irrigation systems "
    "and components, bridges, temporary greens, and drains (except in penalty area)."
)
OB_MAINTENANCE = (
    "Out of bounds — beyond all course boundaries marked by fences and/or stakes. Any ball "
    "on the other side of the fence surrounding the Maintenance Compound is considered "
    "to be out of bounds."
)
PACE = "All players must maintain their position on the course. Pace of Play will be enforced."
CAUTION = [
    "Venomous snakes and burrowing creatures exist within golf course areas and facilities. "
    "There are holes in the ground. Players enter at their own risk.",
    "Golf course irrigated with reclaimed water. Not for human consumption.",
]

FACILITIES = [
    {
        "name": "El Rio",
        "street": "1400 West Speedway Blvd", "postal_code": "85745", "phone": "520-791-4229",
        "rules": STANDARD_RULES + [
            PACE,
            "No more than 4 players may play in a group at any given time. No exceptions.",
            "Free drop nearest relief no nearer the hole from all roads, staked trees, irrigation "
            "systems and components, bridges, temporary greens, and French drains.",
            "All water features are penalty areas.",
            "Out of bounds — beyond all course boundaries marked by fences and/or stakes. Any ball "
            "on the other side of the fence surrounding the Maintenance Compound is considered "
            "to be out of bounds.",
            "All water pump areas, holes 2, 5, and 12, will be played as immovable obstructions "
            "under Rule 16.1. (Does not give you line of sight relief)",
            "Guard Screens on holes 1 and 18 are immovable obstructions under Rule 16.1.",
        ],
        "courses": [{
            "name": "El Rio", "revision": "03/26",
            "par": [4, 4, 4, 3, 4, 4, 4, 3, 5, 4, 4, 4, 3, 4, 3, 4, 4, 5],
            "printed_par": 70,
            "tees": [
                ("Blue", [353, 446, 344, 203, 322, 366, 417, 219, 561, 394, 406, 427, 117, 442, 189, 376, 343, 511], (3231, 3205, 6436)),
                ("Blue/White", "LLULUULLL" "ULLULLUUL", (None, None, 6142)),
                ("White", [323, 425, 322, 176, 306, 356, 388, 193, 534, 368, 373, 400, 103, 418, 158, 356, 320, 492], (3023, 2988, 6011)),
                ("White/Red", "ULUUUULLL" "UULULUUUL", (None, None, 5718)),
                ("Red", [280, 387, 302, 154, 254, 276, 338, 176, 470, 318, 341, 367, 85, 361, 139, 334, 303, 458], (2637, 2706, 5343)),
                ("Silver", [258, 302, 284, 127, 224, 262, 320, 157, 415, 314, 316, 328, 72, 214, 118, 264, 274, 437], (2349, 2337, 4686)),
            ],
            "stroke_index": {
                "Handicap": [13, 1, 17, 7, 11, 15, 5, 3, 9, 12, 6, 4, 18, 2, 16, 8, 14, 10],
                "Red/Silver Handicap": [17, 3, 7, 13, 9, 15, 5, 11, 1, 14, 8, 4, 18, 6, 16, 10, 12, 2],
            },
            # tee: (men, women); None = "--" on the card
            "ratings": {
                "Blue": ((69.4, 124), None),
                "Blue/White": ((68.2, 121), None),
                "White": ((67.4, 119), (73.1, 123)),
                "White/Red": ((66.1, 115), (71.7, 119)),
                "Red": ((64.1, 111), (69.1, 113)),
                "Silver": (None, (65.3, 107)),
            },
            # Assumption (see SCHEMA.md): the tee-labeled row applies to those
            # tees for both genders; "Handicap" applies to every other tee.
            "si_for": lambda tee, gender: "Red/Silver Handicap" if tee in ("Red", "Silver") else "Handicap",
        }],
    },
    {
        "name": "Fred Enke",
        "street": "8251 East Irvington Rd", "postal_code": "85730", "phone": "520-791-2539",
        "rules": STANDARD_RULES + [
            "All players must maintain their position on the course. Expected Pace-of-Play policy not "
            "to exceed 4 hours and 30 minutes will be enforced.",
            "Penalty Areas – All desert areas are red penalty areas, and the edge of the penalty area "
            "is where the grass and desert meet (Rule 17 applies). *Drop areas are available on Hole "
            "2 and Hole 11 (Rule 14 applies).",
            "Out of Bounds – Beyond all course boundaries marked by fences or white stakes (Rule "
            "18 applies).",
            FREE_RELIEF_ROCKS,
            FREE_RELIEF_PATHS,
        ],
        "courses": [{
            "name": "Fred Enke", "revision": "05/25",
            "par": [4, 5, 3, 4, 4, 3, 4, 4, 5, 4, 3, 5, 4, 5, 3, 4, 4, 4],
            "printed_par": 72,
            "tees": [
                ("Blue", [399, 567, 208, 322, 411, 147, 362, 402, 512, 373, 224, 539, 342, 561, 159, 391, 387, 450], (3330, 3426, 6756)),
                ("Blue/White", "ULLUULUUL" "ULULLULUL", (None, None, 6466)),
                ("White", [379, 515, 180, 303, 342, 134, 353, 340, 476, 346, 180, 489, 329, 539, 123, 361, 327, 398], (3022, 3092, 6114)),
                ("White/Gold", "LLLUUUUUL" "ULLULULLL", (None, None, 5777)),
                ("Gold", [346, 413, 158, 284, 315, 116, 320, 340, 446, 302, 137, 460, 300, 509, 109, 342, 298, 398], (2738, 2855, 5593)),
                ("Gold/Red", "LULUUUULU" "UUUUUUULL", (None, None, 5387)),
                ("Red", [298, 395, 117, 268, 300, 95, 267, 312, 380, 292, 137, 391, 285, 433, 90, 329, 281, 326], (2432, 2564, 4996)),
            ],
            "stroke_index": {
                "Handicap": [12, 6, 8, 16, 4, 18, 14, 2, 10, 13, 9, 5, 15, 3, 17, 11, 7, 1],
                "Gold/Red Handicap": [10, 4, 16, 14, 8, 18, 12, 2, 6, 13, 15, 5, 7, 1, 17, 11, 9, 3],
            },
            "ratings": {
                "Blue": ((71.4, 130), None),
                "Blue/White": ((70.0, 124), None),
                "White": ((68.6, 120), (74.5, 134)),
                "White/Gold": ((66.8, 115), (72.4, 131)),
                "Gold": ((65.8, 113), (70.8, 129)),
                "Gold/Red": ((64.8, 110), (69.9, 125)),
                "Red": ((63.2, 105), (69.0, 117)),
            },
            # Assumption: "Gold/Red Handicap" covers the Gold, Gold/Red and Red tees.
            "si_for": lambda tee, gender: "Gold/Red Handicap" if tee in ("Gold", "Gold/Red", "Red") else "Handicap",
        }],
    },
    {
        "name": "Randolph",
        "street": "600 South Alvernon Way", "postal_code": "85711", "phone": "520-791-4161",
        "rules": STANDARD_RULES + [
            PACE,
            "Penalty Areas are defined by red/ yellow lines or stakes.",
            "Ditches and un-staked tree basins – play ball as it lies (unless “unplayable lie” is elected).",
            OB_MAINTENANCE,
            FREE_RELIEF_ROCKS,
            FREE_RELIEF_PATHS,
        ],
        "courses": [
            {
                "name": "North", "revision": "09/25",
                "par": [4, 4, 5, 4, 4, 3, 4, 3, 5, 4, 3, 4, 5, 4, 3, 5, 4, 4],
                "printed_par": 72,
                "tees": [
                    ("Blue", [365, 415, 569, 429, 440, 136, 373, 198, 469, 423, 197, 388, 480, 432, 193, 574, 368, 434], (3394, 3489, 6883)),
                    ("Blue/White", "ULLLLUULU" "LLUUULLUL", (None, None, 6639)),
                    ("White", [354, 337, 550, 412, 411, 126, 342, 181, 441, 411, 187, 369, 471, 405, 172, 560, 360, 407], (3154, 3342, 6496)),
                    ("White/Gold", "LUULUUULL" "LLUUULLLU", (None, None, 6216)),
                    ("Gold", [341, 326, 504, 375, 407, 120, 336, 160, 412, 351, 177, 363, 467, 382, 149, 478, 355, 368], (2981, 3090, 6071)),
                    ("Gold/Red", "LUULLLULU" "LLUULUULU", (None, None, 5725)),
                    ("Red", [202, 230, 474, 335, 347, 110, 320, 144, 397, 351, 110, 326, 400, 375, 131, 434, 348, 338], (2559, 2813, 5372)),
                ],
                "stroke_index": {
                    "Men's": [7, 9, 11, 1, 3, 13, 15, 5, 17, 2, 14, 10, 16, 8, 6, 18, 12, 4],
                    "Women's": [5, 9, 7, 3, 1, 15, 13, 17, 11, 12, 18, 8, 14, 6, 16, 4, 10, 2],
                },
                "ratings": {
                    "Blue": ((71.7, 126), None),
                    "Blue/White": ((70.4, 123), None),
                    "White": ((69.8, 120), (75.9, 134)),
                    "White/Gold": ((68.3, 117), (74.4, 130)),
                    "Gold": ((67.4, 114), (73.3, 127)),
                    "Gold/Red": ((65.9, 110), (71.6, 124)),
                    "Red": ((64.2, 106), (69.7, 119)),
                },
                "si_for": lambda tee, gender: "Men's" if gender == "M" else "Women's",
            },
            {
                # No revision date is printed on the Dell Urich card.
                "name": "Dell Urich", "revision": None,
                "par": [4, 3, 5, 4, 3, 5, 4, 4, 3, 4, 3, 4, 5, 4, 4, 4, 3, 4],
                "printed_par": 70,
                "tees": [
                    ("Blue", [373, 213, 557, 299, 156, 540, 445, 457, 187, 390, 193, 451, 515, 468, 429, 380, 137, 439], (3227, 3402, 6629)),
                    ("Blue/White", "ULUUUULLL" "ULLULLUUU", (None, None, 6336)),
                    ("White", [347, 170, 534, 277, 143, 527, 402, 437, 170, 364, 173, 411, 502, 427, 360, 350, 126, 401], (3007, 3114, 6121)),
                    ("White/Gold", "ULUUULULL" "ULLULUULL", (None, None, 5932)),
                    ("Gold", [333, 153, 511, 267, 140, 490, 387, 407, 155, 334, 158, 383, 488, 407, 342, 322, 113, 387], (2843, 2934, 5777)),
                    ("Gold/Red", "LUUUUULLL" "ULUULLUUL", (None, None, 5522)),
                    ("Red", [310, 140, 447, 243, 113, 460, 362, 379, 133, 314, 137, 366, 464, 373, 267, 287, 102, 360], (2587, 2670, 5257)),
                ],
                "stroke_index": {
                    "Men's": [9, 5, 13, 17, 11, 15, 1, 3, 7, 10, 16, 6, 18, 4, 14, 8, 12, 2],
                    "Women's": [5, 11, 9, 15, 13, 7, 1, 3, 17, 12, 16, 8, 4, 6, 18, 14, 10, 2],
                },
                # Printed on the North card under "DELL URICH RATING & SLOPE".
                "ratings": {
                    "Blue": ((70.3, 124), None),
                    "Blue/White": ((68.5, 120), None),
                    "White": ((67.8, 116), (73.6, 131)),
                    "White/Gold": ((67.0, 114), (72.9, 129)),
                    "Gold": ((66.6, 112), (71.8, 126)),
                    "Gold/Red": ((65.4, 109), (70.6, 122)),
                    "Red": ((63.9, 105), (68.5, 117)),
                },
                "si_for": lambda tee, gender: "Men's" if gender == "M" else "Women's",
            },
        ],
    },
    {
        "name": "Silverbell",
        "street": "3600 North Silverbell Rd", "postal_code": "85745", "phone": "520-791-5235",
        "rules": STANDARD_RULES + [
            PACE,
            "Penalty Areas are defined by red/ yellow lines or stakes.",
            OB_MAINTENANCE,
            FREE_RELIEF_ROCKS,
            FREE_RELIEF_PATHS,
        ],
        "courses": [{
            "name": "Silverbell", "revision": "01/26",
            "par": [4, 5, 3, 4, 4, 3, 5, 4, 3, 4, 4, 3, 4, 4, 4, 3, 4, 5],
            "printed_par": 70,
            "tees": [
                ("Blue", [470, 559, 152, 497, 370, 220, 595, 450, 195, 383, 395, 200, 440, 465, 343, 237, 410, 555], (3508, 3428, 6936)),
                ("Blue/White", "LUULULULL" "UULLLULUU", (None, None, 6657)),
                ("White", [440, 522, 143, 455, 336, 186, 548, 395, 177, 335, 378, 178, 420, 430, 316, 214, 380, 538], (3202, 3189, 6391)),
                ("White/Yellow", "LUULULUUU" "UULLLULUL", (None, None, 6141)),
                ("Yellow", [407, 492, 128, 432, 313, 165, 523, 367, 152, 315, 352, 161, 393, 355, 257, 186, 333, 512], (2979, 2864, 5843)),
                ("Yellow/Red", "LUULULLUU" "UULLUULUL", (None, None, 5560)),
                ("Red", [357, 430, 118, 390, 295, 137, 482, 355, 130, 299, 290, 136, 373, 305, 220, 162, 297, 459], (2694, 2541, 5235)),
            ],
            "stroke_index": {
                "Men's": [5, 3, 17, 9, 13, 11, 1, 7, 15, 14, 10, 18, 8, 4, 16, 12, 6, 2],
                "Women's": [7, 3, 17, 5, 11, 15, 1, 9, 13, 10, 12, 18, 4, 6, 16, 14, 8, 2],
            },
            "ratings": {
                "Blue": ((71.6, 124), None),
                "Blue/White": ((70.3, 120), None),
                "White": ((68.9, 121), (74.9, 131)),
                "White/Yellow": ((67.7, 118), (73.2, 126)),
                "Yellow": ((66.7, 114), (72.5, 124)),
                "Yellow/Red": ((65.4, 110), (71.2, 118)),
                "Red": ((63.7, 105), (69.0, 115)),
            },
            "si_for": lambda tee, gender: "Men's" if gender == "M" else "Women's",
        }],
    },
]


def load_course(cur, facility_id, c):
    cur.execute(
        "INSERT INTO course (facility_id, name, hole_count, scorecard_revision) VALUES (?, ?, 18, ?)",
        (facility_id, c["name"], c["revision"]),
    )
    course_id = cur.lastrowid

    hole_ids = []
    for number, par in enumerate(c["par"], start=1):
        cur.execute("INSERT INTO hole (course_id, number, par) VALUES (?, ?, ?)", (course_id, number, par))
        hole_ids.append(cur.lastrowid)

    tee_ids = {}
    for order, (name, _, _) in enumerate(c["tees"], start=1):
        cur.execute(
            "INSERT INTO tee (course_id, name, is_combo, sort_order) VALUES (?, ?, ?, ?)",
            (course_id, name, int("/" in name), order),
        )
        tee_ids[name] = cur.lastrowid

    for name, holes, _ in c["tees"]:
        if isinstance(holes, str):
            upper, lower = name.split("/")
            assert len(holes) == 18 and set(holes) <= {"U", "L"}, name
            for hole_id, mark in zip(hole_ids, holes):
                source = tee_ids[upper if mark == "U" else lower]
                cur.execute(
                    "INSERT INTO tee_hole (tee_id, hole_id, source_tee_id) VALUES (?, ?, ?)",
                    (tee_ids[name], hole_id, source),
                )
        else:
            assert len(holes) == 18, name
            for hole_id, yards in zip(hole_ids, holes):
                cur.execute(
                    "INSERT INTO tee_hole (tee_id, hole_id, yards) VALUES (?, ?, ?)",
                    (tee_ids[name], hole_id, yards),
                )

    si_ids = {}
    for set_name, indexes in c["stroke_index"].items():
        cur.execute("INSERT INTO stroke_index_set (course_id, name) VALUES (?, ?)", (course_id, set_name))
        si_ids[set_name] = cur.lastrowid
        for hole_id, si in zip(hole_ids, indexes):
            cur.execute(
                "INSERT INTO hole_stroke_index (stroke_index_set_id, hole_id, stroke_index) VALUES (?, ?, ?)",
                (si_ids[set_name], hole_id, si),
            )

    for tee, by_gender in c["ratings"].items():
        for gender, rating in zip(("M", "F"), by_gender):
            if rating is None:
                continue
            cur.execute(
                "INSERT INTO tee_rating (tee_id, gender, course_rating, slope_rating, stroke_index_set_id) "
                "VALUES (?, ?, ?, ?, ?)",
                (tee_ids[tee], gender, rating[0], rating[1], si_ids[c["si_for"](tee, gender)]),
            )

    return course_id


def verify(cur, course_id, c):
    """Return a list of mismatches between computed and printed totals."""
    errors = []
    for name, _, (out_y, in_y, tot_y) in c["tees"]:
        row = cur.execute(
            "SELECT out_yards, in_yards, total_yards, total_par FROM v_tee_totals "
            "WHERE course_id = ? AND tee_name = ?",
            (course_id, name),
        ).fetchone()
        printed = (out_y, in_y, tot_y, c["printed_par"])
        for label, got, want in zip(("OUT", "IN", "TOT", "PAR"), row, printed):
            if want is not None and got != want:
                errors.append(f"{c['name']} {name} {label}: computed {got}, card says {want}")
    return errors


def main():
    db_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DB_DIR / "golf.db"
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()

    has_schema = cur.execute("SELECT 1 FROM sqlite_master WHERE name = 'operator'").fetchone()
    if not has_schema:
        con.executescript((DB_DIR / "schema.sql").read_text())
    elif cur.execute("SELECT COUNT(*) FROM operator").fetchone()[0]:
        sys.exit(f"{db_path} already has data; refusing to load twice.")

    errors = []
    with con:
        cur.execute("INSERT INTO operator (name, website) VALUES (?, ?)", ("Tucson City Golf", WEBSITE))
        operator_id = cur.lastrowid
        for f in FACILITIES:
            cur.execute(
                "INSERT INTO facility (operator_id, name, street, city, state, postal_code, phone, website) "
                "VALUES (?, ?, ?, 'Tucson', 'AZ', ?, ?, ?)",
                (operator_id, f["name"], f["street"], f["postal_code"], f["phone"], WEBSITE),
            )
            facility_id = cur.lastrowid
            for kind, bodies in (("local_rule", f["rules"]), ("caution", CAUTION)):
                for position, body in enumerate(bodies, start=1):
                    cur.execute(
                        "INSERT INTO facility_rule (facility_id, kind, position, body) VALUES (?, ?, ?, ?)",
                        (facility_id, kind, position, body),
                    )
            for c in f["courses"]:
                course_id = load_course(cur, facility_id, c)
                errors += verify(cur, course_id, c)
        if errors:
            con.rollback()
            sys.exit("Totals don't match the cards; nothing was loaded:\n  " + "\n  ".join(errors))

    print(f"Loaded {db_path}; all tee totals match the printed cards.")


if __name__ == "__main__":
    main()
