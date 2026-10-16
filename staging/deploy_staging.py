"""Deploy the CivicConnect release candidate into an isolated staging root.

Usage: python staging/deploy_staging.py --env-root /path/to/staging-env [--source /path/to/pack]

Clean-install behaviour: copies only the files named in staging.config.json into
releases/<rc-id>/, verifies each copy by SHA-256 against the source and against
evidence_manifest.json, points `current` at the release, creates the staging
database from the deployed schema and loads synthetic fixtures. Refuses to run
unless CIVICCONNECT_ENV=staging so it cannot be aimed at a real database.
"""
import argparse, hashlib, json, os, platform, shutil, sqlite3, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def rc_fingerprint(source, files):
    digest = hashlib.sha256()
    for rel in sorted(files):
        digest.update(rel.encode() + b"\0" + sha(source / rel).encode() + b"\n")
    return digest.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-root", required=True)
    parser.add_argument("--source", default=str(HERE.parent))
    parser.add_argument("--rc-label", default="RC-M3-candidate")
    args = parser.parse_args()
    if os.environ.get("CIVICCONNECT_ENV") != "staging":
        sys.exit("Refusing to deploy: set CIVICCONNECT_ENV=staging")
    config = json.loads((HERE / "staging.config.json").read_text(encoding="utf-8"))
    source, root = Path(args.source).resolve(), Path(args.env_root).resolve()
    if root == source or source in root.parents and root.name == "product":
        sys.exit("Staging root must be separate from the source tree")
    files = config["release_files"]

    manifest = {e["path"]: e["sha256"] for e in json.loads((source / "evidence_manifest.json").read_text(encoding="utf-8"))}
    problems = [rel for rel in files if manifest.get(rel) and manifest[rel] != sha(source / rel)]
    if problems:
        sys.exit("Source differs from evidence manifest: " + ", ".join(problems))

    fingerprint = rc_fingerprint(source, files)
    release_id = f"{args.rc_label}-{fingerprint[:12]}"
    release_dir = root / config["paths"]["release_root"] / release_id
    for key in ("data_dir", "backup_dir", "log_dir"):
        (root / config["paths"][key]).mkdir(parents=True, exist_ok=True)
    if release_dir.exists():
        shutil.rmtree(release_dir)
    copied = {}
    for rel in files:
        target = release_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / rel, target)
        if sha(target) != sha(source / rel):
            sys.exit(f"Copy verification failed for {rel}")
        copied[rel] = sha(target)
    release = {
        "release_id": release_id, "rc_label": args.rc_label, "fingerprint_sha256": fingerprint,
        "documented_rc_commit": "214e47d32df5fcd5543e22217a48ca5214370400 (Governance.md; confirm with Member 1)",
        "deployed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": copied, "python": platform.python_version(), "sqlite": sqlite3.sqlite_version,
        "platform": platform.platform(), "config_sha256": sha(HERE / "staging.config.json"),
    }
    (release_dir / "release.json").write_text(json.dumps(release, indent=2), encoding="utf-8")

    link = root / config["paths"]["current_link"]
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(release_dir, target_is_directory=True)

    sys.path.insert(0, str(link / "product"))
    from lifecycle import SqliteLifecycleStore, seed_demo
    db = root / config["paths"]["data_dir"] / "civicconnect-staging.sqlite3"
    if db.exists():
        db.unlink()
    store = SqliteLifecycleStore(db)
    store.initialise()
    seed_demo(store)
    connection = store.connect()
    with connection:   # second staging fixture for the rejection path
        connection.execute("INSERT INTO requests(reference,citizen_id,department,status,submitted_at) VALUES(?,?,?,?,?)",
                           ("CC-STG-002", "citizen-b", "Water", "Submitted", "2026-09-24T08:30:00+00:00"))
    connection.close()
    print(json.dumps({"deployed": release_id, "current": str(link.resolve()), "database": str(db),
                      "python": release["python"], "sqlite": release["sqlite"]}, indent=2))

if __name__ == "__main__":
    main()
