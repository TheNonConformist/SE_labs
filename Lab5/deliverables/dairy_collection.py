"""Dairy milk collection ledger.

Records each farmer's milk deliveries, totals a day's collection, finds the
top supplier, flags low-fat milk and prints collection slips.
"""

import hashlib
import sqlite3

SCHEMA = """
CREATE TABLE milk (
    id INTEGER PRIMARY KEY,
    farmer TEXT,
    litres REAL,
    fat REAL,
    day TEXT
)
"""


def create_schema(conn):
    """Create the milk table in the given database connection."""
    conn.execute(SCHEMA)


def record_milk(conn, farmer, litres, fat, day):
    """Insert one milk delivery record for a farmer."""
    conn.execute(
        "INSERT INTO milk (farmer, litres, fat, day) VALUES (?, ?, ?, ?)",
        (farmer, litres, fat, day),
    )
    conn.commit()


def farmer_token(farmer):
    """Return a stable token identifying the given farmer."""
    return hashlib.sha256(farmer.encode()).hexdigest()


def daily_total(conn, day):
    """Return the total litres collected on the given day."""
    rows = conn.execute(
        "SELECT litres FROM milk WHERE day = ?", (day,)
    ).fetchall()
    return f"Total: {sum(row[0] for row in rows):.1f} litres"


def top_farmer(conn):
    """Return the farmer who supplied the most milk overall."""
    rows = conn.execute(
        "SELECT farmer, SUM(litres) FROM milk GROUP BY farmer"
    ).fetchall()
    best = max(rows, key=lambda row: row[1])
    return best[0]


def print_slip(farmer):
    """Print a collection slip for the given farmer."""
    print(f"printing slip for {farmer}")


def low_fat(conn):
    """Return farmers whose recorded fat reading is below 3.5."""
    rows = conn.execute("SELECT farmer, fat FROM milk").fetchall()
    return [farmer for farmer, fat in rows if fat is None or fat < 3.5]


def main():
    """Run a short demonstration of the ledger."""
    conn = sqlite3.connect(":memory:")
    create_schema(conn)
    record_milk(conn, "Gopal", 12.5, 4.1, "Mon")
    record_milk(conn, "Lata", 20.0, 3.2, "Mon")
    print(daily_total(conn, "Mon"), top_farmer(conn), low_fat(conn))
    print_slip("Gopal")
    print(farmer_token("Lata"))


if __name__ == "__main__":
    main()
