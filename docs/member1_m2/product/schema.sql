PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS accounts (
  id TEXT PRIMARY KEY,
  role TEXT NOT NULL CHECK(role IN ('Citizen','Staff','Administrator')),
  department TEXT NOT NULL,
  active INTEGER NOT NULL CHECK(active IN (0,1))
);
CREATE TABLE IF NOT EXISTS requests (
  reference TEXT PRIMARY KEY,
  citizen_id TEXT NOT NULL REFERENCES accounts(id),
  department TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('Submitted','Accepted','In Progress','Resolved','Closed','Rejected')),
  submitted_at TEXT NOT NULL,
  assignee TEXT REFERENCES accounts(id),
  due_at TEXT,
  version INTEGER NOT NULL DEFAULT 0 CHECK(version >= 0)
);
CREATE TABLE IF NOT EXISTS lifecycle_events (
  id INTEGER PRIMARY KEY,
  reference TEXT NOT NULL REFERENCES requests(reference),
  from_status TEXT NOT NULL,
  to_status TEXT NOT NULL CHECK(to_status IN ('Accepted','In Progress','Resolved','Closed','Rejected')),
  actor TEXT NOT NULL REFERENCES accounts(id),
  occurred_at TEXT NOT NULL,
  explanation TEXT NOT NULL CHECK(length(trim(explanation)) > 0),
  version INTEGER NOT NULL CHECK(version > 0),
  UNIQUE(reference,version)
);
CREATE INDEX IF NOT EXISTS events_by_request ON lifecycle_events(reference,id);
