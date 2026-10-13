"""CivicConnect request workflow backed by SQLite and the Python standard library."""

from datetime import datetime, timezone
import hashlib
import hmac
from pathlib import Path
import secrets
import sqlite3
import uuid


class Forbidden(ValueError):
    pass


class Conflict(ValueError):
    pass


class InvalidTransition(ValueError):
    pass


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            raise ValueError("Timezone required")
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError) as exc:
        raise InvalidTransition("A valid timezone-aware timestamp is required") from exc


def _password_hash(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000)
    return "pbkdf2_sha256${}${}${}".format(
        310_000, salt.hex(), digest.hex()
    )


def _password_matches(password, encoded):
    try:
        scheme, rounds, salt_hex, digest_hex = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        rounds = int(rounds)
        if rounds < 100_000 or rounds > 2_000_000:
            return False
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), rounds
        )
        return hmac.compare_digest(actual, expected)
    except (AttributeError, TypeError, ValueError):
        return False


class LifecyclePolicy:
    """FR-13 transition rules, independent of persistence and the web interface."""

    NEXT = {
        "Submitted": {"Accepted", "Rejected"},
        "Accepted": {"In Progress"},
        "In Progress": {"Resolved"},
        "Resolved": {"Closed"},
        "Closed": set(),
        "Rejected": set(),
    }

    @classmethod
    def check(cls, request, target, explanation, assignee, due_at):
        if target not in cls.NEXT.get(request["status"], set()):
            raise InvalidTransition("Transition is not permitted")
        if not isinstance(explanation, str):
            raise InvalidTransition("Explanation must be text")
        if target in {"Rejected", "Resolved"} and not explanation.strip():
            raise InvalidTransition("Rejection and resolution require an explanation")
        if target == "Accepted":
            if not assignee or not due_at:
                raise InvalidTransition("Acceptance requires an assignee and due time")
            if timestamp(due_at) <= timestamp(request["submitted_at"]):
                raise InvalidTransition("Due time must be later than submission")


class SqliteLifecycleStore:
    """Owns accounts, request queries, submission and atomic lifecycle changes."""

    DEFAULT_CATEGORIES = (
        ("water", "Water", "Water"),
        ("roads", "Roads", "Roads"),
    )

    REQUEST_COLUMNS = {
        "title": "TEXT NOT NULL DEFAULT 'Existing request'",
        "description": "TEXT NOT NULL DEFAULT ''",
        "location": "TEXT NOT NULL DEFAULT ''",
        "category_id": "TEXT REFERENCES categories(id)",
        "category_label": "TEXT NOT NULL DEFAULT 'Legacy'",
    }

    def __init__(self, path):
        self.path = str(path)

    def connect(self):
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def initialise(self):
        connection = self.connect()
        try:
            connection.executescript(
                Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(requests)").fetchall()
            }
            for name, declaration in self.REQUEST_COLUMNS.items():
                if name not in columns:
                    connection.execute(
                        f"ALTER TABLE requests ADD COLUMN {name} {declaration}"
                    )
            with connection:
                connection.executemany(
                    "INSERT OR IGNORE INTO categories(id,label,department,active) "
                    "VALUES(?,?,?,1)",
                    self.DEFAULT_CATEGORIES,
                )
        finally:
            connection.close()

    def categories(self):
        connection = self.connect()
        try:
            rows = connection.execute(
                "SELECT id,label,department FROM categories WHERE active=1 ORDER BY label"
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def register_citizen(self, username, password, now):
        if not isinstance(username, str) or not isinstance(password, str):
            raise InvalidTransition("Username and password are required")
        username = username.strip()
        account_id = username.casefold()
        if not username or len(username) > 80:
            raise InvalidTransition("Username is required and must be at most 80 characters")
        if not password or len(password) > 1024:
            raise InvalidTransition("Password is required and is too long")
        created_at = timestamp(now).isoformat()
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO accounts(id,role,department,active) VALUES(?, 'Citizen', '', 1)",
                (account_id,),
            )
            connection.execute(
                "INSERT INTO credentials(account_id,username,password_hash,created_at) "
                "VALUES(?,?,?,?)",
                (account_id, account_id, _password_hash(password), created_at),
            )
            connection.commit()
            return {"id": account_id, "role": "Citizen"}
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            raise InvalidTransition("Username is already registered") from exc
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def authenticate(self, username, password):
        if not isinstance(username, str) or not isinstance(password, str):
            return None
        account_id = username.strip().casefold()
        connection = self.connect()
        try:
            row = connection.execute(
                "SELECT a.id,a.role,a.active,c.password_hash "
                "FROM credentials c JOIN accounts a ON a.id=c.account_id "
                "WHERE c.username=?",
                (account_id,),
            ).fetchone()
            if (
                row is None
                or not row["active"]
                or not _password_matches(password, row["password_hash"])
            ):
                return None
            return {"id": row["id"], "role": row["role"]}
        finally:
            connection.close()

    def authenticate_session(self, account_id):
        """Reload the account's current role and active state for each request."""
        connection = self.connect()
        try:
            row = connection.execute(
                "SELECT id,role,department FROM accounts WHERE id=? AND active=1",
                (account_id,),
            ).fetchone()
            return dict(row) if row is not None else None
        finally:
            connection.close()

    @staticmethod
    def _request_dict(row):
        return {
            "reference": row["reference"],
            "citizen_id": row["citizen_id"],
            "department": row["department"],
            "status": row["status"],
            "submitted_at": row["submitted_at"],
            "assignee": row["assignee"],
            "due_at": row["due_at"],
            "version": row["version"],
            "title": row["title"],
            "description": row["description"],
            "location": row["location"],
            "category_id": row["category_id"],
            "category_label": row["category_label"],
        }

    def submit_request(self, actor_id, title, description, location, category_id, now):
        values = {
            "title": (title, 5, 120),
            "description": (description, 10, 2000),
            "location": (location, 3, 200),
        }
        cleaned = {}
        for name, (value, minimum, maximum) in values.items():
            if not isinstance(value, str):
                raise InvalidTransition(f"{name.title()} is required")
            value = value.strip()
            if not minimum <= len(value) <= maximum:
                raise InvalidTransition(
                    f"{name.title()} must be {minimum} to {maximum} characters"
                )
            cleaned[name] = value
        if not isinstance(category_id, str) or not category_id.strip():
            raise InvalidTransition("Select an active category")

        submitted_at = timestamp(now).isoformat()
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            actor = connection.execute(
                "SELECT id,role,active FROM accounts WHERE id=?", (actor_id,)
            ).fetchone()
            if actor is None or not actor["active"] or actor["role"] != "Citizen":
                raise Forbidden("Only an active citizen can submit a request")
            category = connection.execute(
                "SELECT id,label,department FROM categories WHERE id=? AND active=1",
                (category_id.strip(),),
            ).fetchone()
            if category is None:
                raise InvalidTransition("Select an active category")

            reference = None
            for _ in range(5):
                candidate = "CC-{}-{}".format(
                    timestamp(submitted_at).strftime("%Y%m%d"),
                    uuid.uuid4().hex[:8].upper(),
                )
                exists = connection.execute(
                    "SELECT 1 FROM requests WHERE reference=?", (candidate,)
                ).fetchone()
                if exists is None:
                    reference = candidate
                    break
            if reference is None:
                raise Conflict("Could not allocate a unique request reference")

            connection.execute(
                "INSERT INTO requests(reference,citizen_id,department,status,submitted_at,"
                "title,description,location,category_id,category_label) "
                "VALUES(?,?,?,'Submitted',?,?,?,?,?,?)",
                (
                    reference,
                    actor_id,
                    category["department"],
                    submitted_at,
                    cleaned["title"],
                    cleaned["description"],
                    cleaned["location"],
                    category["id"],
                    category["label"],
                ),
            )
            connection.commit()
            return reference
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def list_requests(self, actor_id):
        connection = self.connect()
        try:
            connection.execute("BEGIN")
            actor = connection.execute(
                "SELECT id,role,department,active FROM accounts WHERE id=?", (actor_id,)
            ).fetchone()
            if actor is None or not actor["active"] or actor["role"] not in {"Citizen", "Staff"}:
                raise Forbidden("Request list is not accessible")
            if actor["role"] == "Citizen":
                rows = connection.execute(
                    "SELECT * FROM requests WHERE citizen_id=? ORDER BY submitted_at DESC,reference",
                    (actor_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM requests WHERE department=? ORDER BY submitted_at DESC,reference",
                    (actor["department"],),
                ).fetchall()
            return [self._request_dict(row) for row in rows]
        finally:
            connection.close()

    def change(self, actor_id, reference, target, expected_version, explanation, assignee, due_at, now):
        connection = self.connect()
        try:
            # Serialize writers and keep the request state and its audit event atomic.
            connection.execute("BEGIN IMMEDIATE")
            actor = connection.execute(
                "SELECT * FROM accounts WHERE id=?", (actor_id,)
            ).fetchone()
            request = connection.execute(
                "SELECT * FROM requests WHERE reference=?", (reference,)
            ).fetchone()
            if (
                actor is None
                or not actor["active"]
                or actor["role"] != "Staff"
                or request is None
                or actor["department"] != request["department"]
            ):
                raise Forbidden("Request is not accessible")
            if type(expected_version) is not int or request["version"] != expected_version:
                raise Conflict("Request changed; reload before retrying")
            LifecyclePolicy.check(request, target, explanation, assignee, due_at)
            if target == "Accepted":
                chosen = connection.execute(
                    "SELECT * FROM accounts WHERE id=?", (assignee,)
                ).fetchone()
                if (
                    chosen is None
                    or not chosen["active"]
                    or chosen["role"] != "Staff"
                    or chosen["department"] != request["department"]
                ):
                    raise InvalidTransition(
                        "Assignee must be active staff in the request department"
                    )
            else:
                if assignee is not None or due_at is not None:
                    raise InvalidTransition(
                        "Assignment and due time are set at acceptance in this path"
                    )
                assignee, due_at = request["assignee"], request["due_at"]
            at = timestamp(now)
            if at < timestamp(request["submitted_at"]):
                raise InvalidTransition("Event time cannot precede submission")
            feedback = explanation.strip() or f"Request status changed to {target}."
            updated = connection.execute(
                "UPDATE requests SET status=?,assignee=?,due_at=?,version=version+1 "
                "WHERE reference=? AND version=?",
                (target, assignee, due_at, reference, expected_version),
            )
            if updated.rowcount != 1:
                raise Conflict("Request changed; reload before retrying")
            connection.execute(
                "INSERT INTO lifecycle_events(reference,from_status,to_status,actor,occurred_at,explanation,version) "
                "VALUES(?,?,?,?,?,?,?)",
                (
                    reference,
                    request["status"],
                    target,
                    actor_id,
                    at.isoformat(),
                    feedback,
                    expected_version + 1,
                ),
            )
            connection.commit()
            return {
                "reference": reference,
                "status": target,
                "version": expected_version + 1,
                "explanation": feedback,
            }
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def history(self, actor_id, reference):
        connection = self.connect()
        try:
            connection.execute("BEGIN")
            actor = connection.execute(
                "SELECT * FROM accounts WHERE id=?", (actor_id,)
            ).fetchone()
            request = connection.execute(
                "SELECT * FROM requests WHERE reference=?", (reference,)
            ).fetchone()
            if (
                actor is None
                or not actor["active"]
                or request is None
                or not (
                    actor["role"] == "Citizen" and request["citizen_id"] == actor_id
                    or actor["role"] == "Staff"
                    and actor["department"] == request["department"]
                )
            ):
                raise Forbidden("Request is not accessible")
            events = connection.execute(
                "SELECT from_status,to_status,actor,occurred_at,explanation,version "
                "FROM lifecycle_events WHERE reference=? ORDER BY id",
                (reference,),
            ).fetchall()
            return {
                "reference": reference,
                "status": request["status"],
                "version": request["version"],
                "request": self._request_dict(request),
                "events": [dict(row) for row in events],
            }
        finally:
            connection.close()


class RequestLifecycleCoordinator:
    """In-process application contract for controlled lifecycle transitions."""

    def __init__(self, store, clock=None):
        self.store = store
        self.clock = clock or (lambda: datetime.now(timezone.utc).isoformat())

    def transition(
        self, actor_id, reference, target, expected_version, explanation="", assignee=None, due_at=None
    ):
        return self.store.change(
            actor_id,
            reference,
            target,
            expected_version,
            explanation,
            assignee,
            due_at,
            self.clock(),
        )


def seed_demo(store, password=None):
    """Create synthetic local accounts and a request for an isolated demonstration."""
    connection = store.connect()
    accounts = (
        ("citizen-a", "Citizen", "", 1),
        ("citizen-b", "Citizen", "", 1),
        ("staff-a", "Staff", "Water", 1),
        ("staff-b", "Staff", "Roads", 1),
        ("inactive", "Staff", "Water", 0),
    )
    try:
        with connection:
            connection.executemany(
                "INSERT OR IGNORE INTO accounts(id,role,department,active) VALUES(?,?,?,?)",
                accounts,
            )
            connection.execute(
                "INSERT OR IGNORE INTO requests(reference,citizen_id,department,status,submitted_at,"
                "title,description,location,category_id,category_label) "
                "VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    "CC-DEMO-001",
                    "citizen-a",
                    "Water",
                    "Submitted",
                    "2026-09-24T08:00:00+00:00",
                    "Leaking pipe",
                    "A leaking pipe requires repair.",
                    "Main Road",
                    "water",
                    "Water",
                ),
            )
            if password is not None:
                hashed = _password_hash(password)
                created_at = datetime.now(timezone.utc).isoformat()
                for account_id, role, _, active in accounts:
                    if active:
                        connection.execute(
                            "INSERT OR IGNORE INTO credentials(account_id,username,password_hash,created_at) "
                            "VALUES(?,?,?,?)",
                            (account_id, account_id, hashed, created_at),
                        )
    finally:
        connection.close()
