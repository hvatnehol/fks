import sqlite3
import bcrypt
from contextlib import contextmanager
from datetime import date

DB_NAME = "fks_leads.db"

STATUSES = [
    "Ny lead",
    "Kontaktet",
    "Besøk avtalt",
    "Besøk gjennomført",
    "Søkt",
    "Elev",
    "Sluttet",
]

LEAD_PIPELINE_STATUSES = ["Ny lead", "Kontaktet", "Besøk avtalt", "Besøk gjennomført", "Søkt"]

CLOSE_REASONS = [
    "Begynte på videregående",
    "Trivdes ikke på skolen",
    "Skolen passet ikke for familien",
    "Valgte annen skole",
    "Økonomi",
    "Flyttet",
    "Faglig tilbud ikke møtt",
    "Forhold ved skolen",
    "Annet",
]

FOLLOWUP_TYPES = [
    "Telefonsamtale",
    "E-post",
    "Møte",
    "Skolebesøk",
    "SMS",
    "Annet",
]

RELATIONS = [
    "Mor",
    "Far",
    "Stefar",
    "Stemor",
    "Fosterforelder",
    "Besteforelder",
    "Annen foresatt",
]


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def create_tables():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'bruker',
                active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS families (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                display_name TEXT NOT NULL,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS guardians (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                relation TEXT,
                FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS children (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                family_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                birth_year INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Ny lead',
                note TEXT,
                enrolled_at DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                close_reason TEXT,
                close_reason_detail TEXT,
                FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS follow_ups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                child_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                note TEXT,
                performed_by_id INTEGER,
                performed_by_name TEXT NOT NULL,
                next_followup_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (child_id) REFERENCES children(id) ON DELETE CASCADE,
                FOREIGN KEY (performed_by_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS status_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                child_id INTEGER NOT NULL,
                old_status TEXT,
                new_status TEXT NOT NULL,
                changed_by_id INTEGER,
                changed_by_name TEXT NOT NULL,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (child_id) REFERENCES children(id) ON DELETE CASCADE
            );
        """)

        # Migrate: add enrolled_at if it doesn't exist yet
        try:
            conn.execute("ALTER TABLE children ADD COLUMN enrolled_at DATE")
        except Exception:
            pass

        row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
        if row[0] == 0:
            pw_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
            conn.execute(
                "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                ("admin", pw_hash, "Administrator", "admin"),
            )


# ── AUTH ──────────────────────────────────────────────────────────────────────

def verify_user(username, password):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? AND active = 1", (username,)
        ).fetchone()
        if row and bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
            return dict(row)
        return None


def get_all_users():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, username, full_name, role, active, created_at FROM users ORDER BY full_name"
        ).fetchall()
        return [dict(r) for r in rows]


def add_user(username, password, full_name, role):
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            (username, pw_hash, full_name, role),
        )


def update_user_role(user_id, role):
    with get_db() as conn:
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))


def toggle_user_active(user_id):
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET active = CASE WHEN active = 1 THEN 0 ELSE 1 END WHERE id = ?",
            (user_id,),
        )


def change_password(user_id, new_password):
    pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?", (pw_hash, user_id)
        )


# ── FAMILIES ──────────────────────────────────────────────────────────────────

def get_all_families():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM families ORDER BY display_name").fetchall()
        return [dict(r) for r in rows]


def add_family(display_name, note=""):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO families (display_name, note) VALUES (?, ?)",
            (display_name, note),
        )
        return cursor.lastrowid


def update_family(family_id, display_name, note):
    with get_db() as conn:
        conn.execute(
            "UPDATE families SET display_name = ?, note = ? WHERE id = ?",
            (display_name, note, family_id),
        )


def delete_family(family_id):
    with get_db() as conn:
        conn.execute("DELETE FROM families WHERE id = ?", (family_id,))


# ── GUARDIANS ─────────────────────────────────────────────────────────────────

def get_guardians(family_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM guardians WHERE family_id = ? ORDER BY name", (family_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def add_guardian(family_id, name, phone, email, relation):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO guardians (family_id, name, phone, email, relation) VALUES (?, ?, ?, ?, ?)",
            (family_id, name, phone, email, relation),
        )


def update_guardian(guardian_id, name, phone, email, relation):
    with get_db() as conn:
        conn.execute(
            "UPDATE guardians SET name = ?, phone = ?, email = ?, relation = ? WHERE id = ?",
            (name, phone, email, relation, guardian_id),
        )


def delete_guardian(guardian_id):
    with get_db() as conn:
        conn.execute("DELETE FROM guardians WHERE id = ?", (guardian_id,))


# ── CHILDREN ──────────────────────────────────────────────────────────────────

def calculate_grade(birth_year):
    today = date.today()
    grade = (today.year - birth_year - 5) if today.month >= 8 else (today.year - birth_year - 6)
    if grade < 1:
        return None, "Ikke startet ennå"
    elif grade <= 10:
        return grade, f"{grade}. trinn"
    else:
        return None, "Ferdig grunnskole"


def get_all_children_with_family():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT c.*, f.display_name as family_name
            FROM children c
            JOIN families f ON c.family_id = f.id
            ORDER BY f.display_name, c.name
        """).fetchall()
        return [dict(r) for r in rows]


def get_families_with_children():
    """Returns list of (family, [children]) sorted by family name."""
    with get_db() as conn:
        families = conn.execute(
            "SELECT * FROM families ORDER BY display_name"
        ).fetchall()
        result = []
        for fam in families:
            children = conn.execute(
                "SELECT * FROM children WHERE family_id = ? ORDER BY name",
                (fam["id"],),
            ).fetchall()
            result.append((dict(fam), [dict(c) for c in children]))
        return result


def get_children_by_family(family_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM children WHERE family_id = ? ORDER BY name", (family_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_child(child_id):
    with get_db() as conn:
        row = conn.execute(
            """SELECT c.*, f.display_name as family_name
               FROM children c JOIN families f ON c.family_id = f.id
               WHERE c.id = ?""",
            (child_id,),
        ).fetchone()
        return dict(row) if row else None


def add_child(family_id, name, birth_year, status, note=""):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO children (family_id, name, birth_year, status, note) VALUES (?, ?, ?, ?, ?)",
            (family_id, name, birth_year, status, note),
        )
        return cursor.lastrowid


def update_child(child_id, name, birth_year, status, note, changed_by_id, changed_by_name):
    with get_db() as conn:
        old = conn.execute("SELECT status FROM children WHERE id = ?", (child_id,)).fetchone()
        conn.execute(
            "UPDATE children SET name = ?, birth_year = ?, status = ?, note = ? WHERE id = ?",
            (name, birth_year, status, note, child_id),
        )
        if old and old["status"] != status:
            conn.execute(
                "INSERT INTO status_log (child_id, old_status, new_status, changed_by_id, changed_by_name) VALUES (?, ?, ?, ?, ?)",
                (child_id, old["status"], status, changed_by_id, changed_by_name),
            )


def update_child_status(child_id, new_status, changed_by_id, changed_by_name):
    with get_db() as conn:
        old = conn.execute("SELECT status FROM children WHERE id = ?", (child_id,)).fetchone()
        conn.execute("UPDATE children SET status = ? WHERE id = ?", (new_status, child_id))
        if old:
            conn.execute(
                "INSERT INTO status_log (child_id, old_status, new_status, changed_by_id, changed_by_name) VALUES (?, ?, ?, ?, ?)",
                (child_id, old["status"], new_status, changed_by_id, changed_by_name),
            )


def update_enrolled_at(child_id, enrolled_at):
    with get_db() as conn:
        conn.execute(
            "UPDATE children SET enrolled_at = ? WHERE id = ?", (enrolled_at, child_id)
        )


def close_child_lead(child_id, close_reason, close_reason_detail, changed_by_id, changed_by_name):
    from datetime import datetime
    with get_db() as conn:
        old = conn.execute("SELECT status FROM children WHERE id = ?", (child_id,)).fetchone()
        conn.execute(
            "UPDATE children SET status = 'Sluttet', closed_at = ?, close_reason = ?, close_reason_detail = ? WHERE id = ?",
            (datetime.now().isoformat(), close_reason, close_reason_detail, child_id),
        )
        if old:
            conn.execute(
                "INSERT INTO status_log (child_id, old_status, new_status, changed_by_id, changed_by_name) VALUES (?, ?, ?, ?, ?)",
                (child_id, old["status"], "Avsluttet", changed_by_id, changed_by_name),
            )


def delete_child(child_id):
    with get_db() as conn:
        conn.execute("DELETE FROM children WHERE id = ?", (child_id,))


# ── STATUS LOG ────────────────────────────────────────────────────────────────

def get_status_log(child_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM status_log WHERE child_id = ? ORDER BY changed_at DESC",
            (child_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_status_transition_counts():
    """Returns counts of each status transition for statistics."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT old_status, new_status, COUNT(*) as count FROM status_log GROUP BY old_status, new_status"
        ).fetchall()
        return [dict(r) for r in rows]


def get_avg_days_per_status():
    """Average days spent in each status before moving on."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                s1.new_status as status,
                AVG(CAST(
                    (julianday(COALESCE(s2.changed_at, datetime('now'))) -
                     julianday(s1.changed_at))
                AS REAL)) as avg_days
            FROM status_log s1
            LEFT JOIN status_log s2
                ON s2.child_id = s1.child_id
                AND s2.id = (
                    SELECT MIN(id) FROM status_log
                    WHERE child_id = s1.child_id AND id > s1.id
                )
            GROUP BY s1.new_status
        """).fetchall()
        return {r["status"]: round(r["avg_days"] or 0, 1) for r in rows}


# ── FOLLOW-UPS ────────────────────────────────────────────────────────────────

def get_follow_ups(child_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM follow_ups WHERE child_id = ? ORDER BY created_at DESC",
            (child_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def add_follow_up(child_id, type_, note, performed_by_id, performed_by_name, next_followup_date=None):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO follow_ups (child_id, type, note, performed_by_id, performed_by_name, next_followup_date) VALUES (?, ?, ?, ?, ?, ?)",
            (child_id, type_, note, performed_by_id, performed_by_name, next_followup_date),
        )


def delete_follow_up(follow_up_id):
    with get_db() as conn:
        conn.execute("DELETE FROM follow_ups WHERE id = ?", (follow_up_id,))


# ── STATISTICS ────────────────────────────────────────────────────────────────

def get_stats():
    with get_db() as conn:
        active_leads = conn.execute(
            "SELECT COUNT(*) FROM children WHERE status NOT IN ('Sluttet', 'Elev')"
        ).fetchone()[0]
        active_students = conn.execute(
            "SELECT COUNT(*) FROM children WHERE status = 'Elev'"
        ).fetchone()[0]
        total_families = conn.execute("SELECT COUNT(*) FROM families").fetchone()[0]
        closed_3m = conn.execute(
            "SELECT COUNT(*) FROM children WHERE status = 'Sluttet' AND closed_at >= datetime('now', '-3 months')"
        ).fetchone()[0]
        closed_12m = conn.execute(
            "SELECT COUNT(*) FROM children WHERE status = 'Sluttet' AND closed_at >= datetime('now', '-12 months')"
        ).fetchone()[0]
        overdue = conn.execute(
            "SELECT COUNT(DISTINCT child_id) FROM follow_ups WHERE next_followup_date < date('now') AND next_followup_date IS NOT NULL"
        ).fetchone()[0]
        upcoming_7d = conn.execute(
            "SELECT COUNT(DISTINCT child_id) FROM follow_ups WHERE next_followup_date BETWEEN date('now') AND date('now', '+7 days')"
        ).fetchone()[0]
        return {
            "active_leads": active_leads,
            "active_students": active_students,
            "total_families": total_families,
            "closed_3m": closed_3m,
            "closed_12m": closed_12m,
            "overdue": overdue,
            "upcoming_7d": upcoming_7d,
        }


def get_status_counts():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as count FROM children GROUP BY status"
        ).fetchall()
        return {r["status"]: r["count"] for r in rows}


def get_close_reason_counts():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT close_reason, COUNT(*) as count FROM children WHERE status = 'Sluttet' AND close_reason IS NOT NULL GROUP BY close_reason"
        ).fetchall()
        return {r["close_reason"]: r["count"] for r in rows}


def get_sluttet_by_period(from_date=None, to_date=None):
    """Returns children who have Sluttet, with optional date range on closed_at."""
    conditions = ["status = 'Sluttet'"]
    params = []
    if from_date:
        conditions.append("date(closed_at) >= ?")
        params.append(from_date)
    if to_date:
        conditions.append("date(closed_at) <= ?")
        params.append(to_date)
    where = " AND ".join(conditions)
    with get_db() as conn:
        rows = conn.execute(
            f"""SELECT c.*, f.display_name as family_name
                FROM children c JOIN families f ON c.family_id = f.id
                WHERE {where}
                ORDER BY c.closed_at DESC""",
            params,
        ).fetchall()
        return [dict(r) for r in rows]


def get_sluttet_reason_counts_by_period(from_date=None, to_date=None):
    conditions = ["status = 'Sluttet'", "close_reason IS NOT NULL"]
    params = []
    if from_date:
        conditions.append("date(closed_at) >= ?")
        params.append(from_date)
    if to_date:
        conditions.append("date(closed_at) <= ?")
        params.append(to_date)
    where = " AND ".join(conditions)
    with get_db() as conn:
        rows = conn.execute(
            f"SELECT close_reason, COUNT(*) as count FROM children WHERE {where} GROUP BY close_reason ORDER BY count DESC",
            params,
        ).fetchall()
        return {r["close_reason"]: r["count"] for r in rows}


def get_monthly_new_leads(months=12):
    with get_db() as conn:
        rows = conn.execute(
            f"SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count FROM children WHERE created_at >= datetime('now', '-{months} months') GROUP BY month ORDER BY month"
        ).fetchall()
        return [dict(r) for r in rows]


def get_upcoming_followups(limit=15):
    with get_db() as conn:
        rows = conn.execute(
            """SELECT f.id, f.next_followup_date, f.type, f.note, f.performed_by_name,
                      c.id as child_id, c.name as child_name, c.status as child_status
               FROM follow_ups f
               JOIN children c ON f.child_id = c.id
               WHERE f.next_followup_date IS NOT NULL
               AND f.next_followup_date >= date('now')
               ORDER BY f.next_followup_date ASC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_overdue_followups(limit=15):
    with get_db() as conn:
        rows = conn.execute(
            """SELECT f.id, f.next_followup_date, f.type, f.note, f.performed_by_name,
                      c.id as child_id, c.name as child_name, c.status as child_status
               FROM follow_ups f
               JOIN children c ON f.child_id = c.id
               WHERE f.next_followup_date < date('now')
               AND f.next_followup_date IS NOT NULL
               ORDER BY f.next_followup_date ASC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


# ── DUPLICATE CHECK ──────────────────────────────────────────────────────────

def find_duplicate_children(name, birth_year):
    """Returns children with similar name and same birth year."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT c.*, f.display_name as family_name
               FROM children c JOIN families f ON c.family_id = f.id
               WHERE LOWER(c.name) LIKE LOWER(?) AND c.birth_year = ?""",
            (f"%{name.strip()}%", birth_year),
        ).fetchall()
        return [dict(r) for r in rows]


# ── IMPORT ────────────────────────────────────────────────────────────────────

def import_from_df(df, col_map, default_status, changed_by_id, changed_by_name):
    """
    Import children (and optionally guardians) from a DataFrame.
    col_map keys: child_name, birth_year, guardian_name, guardian_phone,
                  guardian_email, guardian_relation, family_name, note, status
    Returns (imported_count, skipped_count, errors)
    """
    imported = 0
    skipped = 0
    errors = []

    def cell(row, key):
        col = col_map.get(key)
        if col and col in row.index and col != "(ingen)":
            val = row[col]
            if val is None or (isinstance(val, float) and __import__("math").isnan(val)):
                return ""
            return str(val).strip()
        return ""

    for idx, row in df.iterrows():
        child_name = cell(row, "child_name")
        birth_year_raw = cell(row, "birth_year")

        if not child_name:
            skipped += 1
            continue

        try:
            birth_year = int(float(birth_year_raw)) if birth_year_raw else None
            if not birth_year or birth_year < 2000 or birth_year > 2030:
                errors.append(f"Rad {idx+1} ({child_name}): ugyldig fødselsår '{birth_year_raw}'")
                skipped += 1
                continue
        except ValueError:
            errors.append(f"Rad {idx+1} ({child_name}): kan ikke lese fødselsår '{birth_year_raw}'")
            skipped += 1
            continue

        family_name = cell(row, "family_name") or child_name
        note = cell(row, "note")
        status = cell(row, "status") or default_status
        if status not in STATUSES:
            status = default_status

        guardian_name = cell(row, "guardian_name")
        guardian_phone = cell(row, "guardian_phone")
        guardian_email = cell(row, "guardian_email")
        guardian_relation = cell(row, "guardian_relation") or "Foresatt"

        try:
            with get_db() as conn:
                # Reuse existing family if same name
                existing_fam = conn.execute(
                    "SELECT id FROM families WHERE display_name = ?", (family_name,)
                ).fetchone()
                if existing_fam:
                    fam_id = existing_fam["id"]
                else:
                    cursor = conn.execute(
                        "INSERT INTO families (display_name) VALUES (?)", (family_name,)
                    )
                    fam_id = cursor.lastrowid

                cursor = conn.execute(
                    "INSERT INTO children (family_id, name, birth_year, status, note) VALUES (?, ?, ?, ?, ?)",
                    (fam_id, child_name, birth_year, status, note),
                )
                child_id = cursor.lastrowid

                conn.execute(
                    "INSERT INTO status_log (child_id, old_status, new_status, changed_by_id, changed_by_name) VALUES (?, ?, ?, ?, ?)",
                    (child_id, None, status, changed_by_id, f"Import av {changed_by_name}"),
                )

                if guardian_name:
                    conn.execute(
                        "INSERT INTO guardians (family_id, name, phone, email, relation) VALUES (?, ?, ?, ?, ?)",
                        (fam_id, guardian_name, guardian_phone, guardian_email, guardian_relation),
                    )

            imported += 1
        except Exception as e:
            errors.append(f"Rad {idx+1} ({child_name}): {e}")
            skipped += 1

    return imported, skipped, errors
