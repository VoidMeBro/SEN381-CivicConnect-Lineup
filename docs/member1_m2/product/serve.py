"""Run the local CivicConnect server-rendered application."""

import argparse
import os
from pathlib import Path
import secrets
from wsgiref.simple_server import make_server

from lifecycle import SqliteLifecycleStore, seed_demo
from web import CivicConnectWeb


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("CIVICCONNECT_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("CIVICCONNECT_PORT", "8000")))
    parser.add_argument(
        "--seed-demo",
        action="store_true",
        help="add synthetic citizen and staff accounts for a local demonstration",
    )
    args = parser.parse_args()

    database_path = Path(os.environ.get("CIVICCONNECT_DB_PATH", "data/civicconnect.sqlite3"))
    database_path.parent.mkdir(parents=True, exist_ok=True)
    store = SqliteLifecycleStore(database_path)
    store.initialise()

    if args.seed_demo:
        demo_password = os.environ.get("CIVICCONNECT_DEMO_PASSWORD")
        if not demo_password:
            parser.error("Set CIVICCONNECT_DEMO_PASSWORD in the environment before --seed-demo")
        seed_demo(store, demo_password)
        del demo_password
        print("Synthetic demonstration accounts were added; their password was not printed.")

    session_secret = os.environ.get("CIVICCONNECT_SESSION_SECRET")
    if session_secret:
        if len(session_secret.encode("utf-8")) < 32:
            parser.error("CIVICCONNECT_SESSION_SECRET must contain at least 32 bytes")
    else:
        session_secret = secrets.token_urlsafe(48)
        print("Using an ephemeral session key; sessions will expire when the server stops.")

    admin_setup_token = os.environ.get("CIVICCONNECT_ADMIN_SETUP_TOKEN")
    if admin_setup_token is not None and len(admin_setup_token.encode("utf-8")) < 32:
        parser.error("CIVICCONNECT_ADMIN_SETUP_TOKEN must contain at least 32 bytes")

    secure_cookie = os.environ.get("CIVICCONNECT_COOKIE_SECURE", "").lower() in {
        "1",
        "true",
        "yes",
    }
    app = CivicConnectWeb(
        store, session_secret, cookie_secure=secure_cookie,
        admin_setup_token=admin_setup_token,
    )
    with make_server(args.host, args.port, app) as server:
        print(f"CivicConnect is listening on http://{args.host}:{args.port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
