"""Small server-rendered WSGI interface for the CivicConnect request workflow."""

from collections import OrderedDict, deque
from datetime import datetime, timezone
from html import escape
import base64
import hashlib
import hmac
import json
import math
import secrets
import threading
import time
from http.cookies import SimpleCookie
from urllib.parse import parse_qs
from zoneinfo import ZoneInfo

from lifecycle import (
    Conflict,
    Forbidden,
    InvalidTransition,
    LifecyclePolicy,
    RequestLifecycleCoordinator,
)


COOKIE_NAME = "civicconnect_session"
SESSION_SECONDS = 1800
MAX_BODY_BYTES = 32_768
LOGIN_WINDOW_SECONDS = 900
LOGIN_ACCOUNT_LIMIT = 8
LOGIN_ADDRESS_LIMIT = 60
LOGIN_BUCKET_LIMIT = 4096


def _e(value):
    return escape(str(value if value is not None else ""), quote=True)


def _page(title, body, nav=""):
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · CivicConnect</title>
<style>
:root{{font-family:system-ui,sans-serif;color:#17302d;background:#f3f7f5}}
body{{margin:0}}header,main,footer{{max-width:62rem;margin:auto;padding:1rem}}
header{{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #ccd9d4}}
main{{padding-top:2rem}}.panel,.card{{background:white;border:1px solid #ccd9d4;border-radius:.6rem;padding:1.2rem;margin:1rem 0}}
form{{display:grid;gap:.8rem;max-width:38rem}}label{{display:grid;gap:.3rem;font-weight:600}}
input,textarea,select,button{{font:inherit;padding:.65rem;border:1px solid #82958e;border-radius:.35rem}}
textarea{{min-height:8rem}}button,.button{{background:#145a49;color:white;border:0;cursor:pointer;padding:.7rem 1rem}}
a{{color:#075d8c}}.error{{border-left:4px solid #a12222;background:#fff2f2;padding:.8rem}}
.muted{{color:#536761}}.row{{display:flex;gap:1rem;flex-wrap:wrap}}
footer{{color:#536761;border-top:1px solid #ccd9d4;margin-top:3rem}}
</style></head><body><header><div><strong>CivicConnect</strong>
<div class="muted">Service requests and accountable progress</div></div>{nav}</header>
<main><h1>{title}</h1>{body}</main><footer>CivicConnect request service</footer></body></html>""".format(
        title=_e(title), nav=nav, body=body
    )


class CivicConnectWeb:
    """Authenticate users and render request pages without a separate web framework."""

    def __init__(self, store, session_secret, cookie_secure=False, clock=None, admin_setup_token=None):
        if isinstance(session_secret, str):
            session_secret = session_secret.encode("utf-8")
        if not isinstance(session_secret, bytes) or len(session_secret) < 32:
            raise ValueError("CIVICCONNECT_SESSION_SECRET must contain at least 32 bytes")
        self.store = store
        self.secret = session_secret
        self.cookie_secure = cookie_secure
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        if admin_setup_token is not None and (not isinstance(admin_setup_token, str) or len(admin_setup_token.encode("utf-8")) < 32):
            raise ValueError("CIVICCONNECT_ADMIN_SETUP_TOKEN must contain at least 32 bytes")
        self.admin_setup_token = admin_setup_token
        self.coordinator = RequestLifecycleCoordinator(store, clock=self._now)
        self._login_failures = OrderedDict()
        self._login_lock = threading.Lock()

    def _now(self):
        return self.clock().astimezone(timezone.utc).isoformat()

    @staticmethod
    def _landing_path(role):
        return {"Administrator": "/admin/accounts", "Management": "/management/summary"}.get(role, "/requests")

    def _encode_session(self, session):
        payload = json.dumps(session, separators=(",", ":")).encode("utf-8")
        token = base64.urlsafe_b64encode(payload).rstrip(b"=")
        signature = hmac.new(self.secret, token, hashlib.sha256).digest()
        return (token + b"." + base64.urlsafe_b64encode(signature).rstrip(b"=")).decode(
            "ascii"
        )

    def _decode_session(self, cookie_header):
        cookie = SimpleCookie()
        try:
            cookie.load(cookie_header or "")
            value = cookie[COOKIE_NAME].value
            token, signature = value.encode("ascii").split(b".", 1)
            padding = b"=" * (-len(signature) % 4)
            provided = base64.urlsafe_b64decode(signature + padding)
            expected = hmac.new(self.secret, token, hashlib.sha256).digest()
            if not hmac.compare_digest(provided, expected):
                return None
            payload = base64.urlsafe_b64decode(token + b"=" * (-len(token) % 4))
            session = json.loads(payload.decode("utf-8"))
            if not isinstance(session, dict) or session.get("expires", 0) < int(self.clock().timestamp()):
                return None
            if not isinstance(session.get("csrf"), str) or len(session["csrf"]) < 32:
                return None
            return session
        except (KeyError, ValueError, TypeError, UnicodeError, json.JSONDecodeError):
            return None

    def _new_session(self, account_id=None):
        session = {
            "account_id": account_id,
            "csrf": secrets.token_urlsafe(32),
            "expires": int(self.clock().timestamp()) + SESSION_SECONDS,
        }
        return session

    def _cookie(self, session):
        value = f"{COOKIE_NAME}={self._encode_session(session)}; Path=/; HttpOnly; SameSite=Lax; Max-Age={SESSION_SECONDS}"
        if self.cookie_secure:
            value += "; Secure"
        return value

    def _login_keys(self, environ, username):
        address = str(environ.get("REMOTE_ADDR") or "unknown")[:128]
        normalized = username.strip().casefold() if isinstance(username, str) else ""
        return ("account", address, normalized), ("address", address, "")

    def _login_retry_after(self, keys, now):
        retry_after = 0
        with self._login_lock:
            for key, failures in list(self._login_failures.items()):
                while failures and now - failures[0] >= LOGIN_WINDOW_SECONDS:
                    failures.popleft()
                if not failures:
                    self._login_failures.pop(key, None)
            for key in keys:
                failures = self._login_failures.get(key)
                limit = LOGIN_ADDRESS_LIMIT if key[0] == "address" else LOGIN_ACCOUNT_LIMIT
                if failures and len(failures) >= limit:
                    retry_after = max(
                        retry_after,
                        math.ceil(LOGIN_WINDOW_SECONDS - (now - failures[0])),
                    )
        return retry_after

    def _record_login_failure(self, keys, now):
        limits = (LOGIN_ACCOUNT_LIMIT, LOGIN_ADDRESS_LIMIT)
        with self._login_lock:
            for key, limit in zip(keys, limits):
                failures = self._login_failures.get(key)
                if failures is None:
                    failures = deque()
                    self._login_failures[key] = failures
                while failures and now - failures[0] >= LOGIN_WINDOW_SECONDS:
                    failures.popleft()
                failures.append(now)
                self._login_failures.move_to_end(key)
                while len(self._login_failures) > LOGIN_BUCKET_LIMIT:
                    self._login_failures.popitem(last=False)

    def _clear_login_failure(self, account_key):
        with self._login_lock:
            self._login_failures.pop(account_key, None)

    @staticmethod
    def _body(environ):
        try:
            length = int(environ.get("CONTENT_LENGTH") or "0")
        except ValueError as exc:
            raise InvalidTransition("Invalid form submission") from exc
        if length < 0 or length > MAX_BODY_BYTES:
            raise InvalidTransition("Form submission is too large")
        raw = environ["wsgi.input"].read(length)
        try:
            return {
                key: values[-1]
                for key, values in parse_qs(
                    raw.decode("utf-8"), keep_blank_values=True, max_num_fields=32
                ).items()
            }
        except (UnicodeDecodeError, ValueError) as exc:
            raise InvalidTransition("Form submission is invalid") from exc

    @staticmethod
    def _response(start_response, status, body="", headers=None, cookie=None):
        response_headers = [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Cache-Control", "no-store"),
            ("X-Content-Type-Options", "nosniff"),
            ("Referrer-Policy", "no-referrer"),
            (
                "Content-Security-Policy",
                "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
            ),
            ("X-Frame-Options", "DENY"),
            ("Permissions-Policy", "camera=(), microphone=(), geolocation=()"),
        ]
        if headers:
            response_headers.extend(headers)
        if cookie:
            response_headers.append(("Set-Cookie", cookie))
        payload = body.encode("utf-8")
        response_headers.append(("Content-Length", str(len(payload))))
        start_response(status, response_headers)
        return [payload]

    @staticmethod
    def _redirect(start_response, location, cookie=None):
        return CivicConnectWeb._response(
            start_response, "303 See Other", "", [("Location", location)], cookie
        )

    @staticmethod
    def _hidden_csrf(session):
        return f'<input type="hidden" name="csrf" value="{_e(session["csrf"])}">'

    @staticmethod
    def _nav(session):
        if session.get("account_id"):
            links = ""
            if session.get("role") == "Administrator":
                links += ' <a href="/admin/accounts">Accounts</a> <a href="/admin/categories">Categories</a>'
            if session.get("role") in {"Management", "Administrator"}:
                links += ' <a href="/management/summary">Management summary</a>'
            if session.get("role") in {"Citizen", "Staff"}:
                links += ' <a href="/requests">Requests</a>'
            return (
                f'<span>{_e(session["account_id"])}</span>'
                + links
                + '<form method="post" action="/logout" style="display:inline">'
                f'{CivicConnectWeb._hidden_csrf(session)}<button type="submit">Sign out</button></form>'
            )
        return '<a href="/login">Sign in</a> · <a href="/register">Create account</a>'

    def _login_page(self, session, error=""):
        alert = f'<p class="error" role="alert">{_e(error)}</p>' if error else ""
        return _page(
            "Sign in",
            alert
            + '<section class="panel"><p>Sign in to view or manage requests.</p>'
            + '<form method="post" action="/login">'
            + self._hidden_csrf(session)
            + '<label>Username<input name="username" autocomplete="username" maxlength="80" required></label>'
            + '<label>Password<input name="password" type="password" autocomplete="current-password" maxlength="1024" required></label>'
            + '<button type="submit">Sign in</button></form>'
            + '<p>New to CivicConnect? <a href="/register">Create an account</a>.</p></section>',
            self._nav(session),
        )

    def _register_page(self, session, error=""):
        alert = f'<p class="error" role="alert">{_e(error)}</p>' if error else ""
        return _page(
            "Create citizen account",
            alert
            + '<section class="panel"><form method="post" action="/register">'
            + self._hidden_csrf(session)
            + '<label>Username<input name="username" autocomplete="username" maxlength="80" required></label>'
            + '<label>Password (at least 12 characters)<input name="password" type="password" autocomplete="new-password" minlength="12" maxlength="1024" required></label>'
            + '<button type="submit">Create account</button></form></section>',
            self._nav(session),
        )

    def _bootstrap_page(self, session, error=""):
        alert = f'<p class="error" role="alert">{_e(error)}</p>' if error else ""
        return _page(
            "Set up administrator",
            alert + '<section class="panel"><p>Create the first administrator account. Setup closes permanently after an administrator account is created.</p>'
            + '<form method="post" action="/setup/administrator">' + self._hidden_csrf(session)
            + '<label>Username<input name="username" maxlength="80" required></label>'
            + '<label>Password (at least 12 characters)<input name="password" type="password" minlength="12" maxlength="1024" required></label>'
            + '<label>One-time setup token<input name="setup_token" type="password" autocomplete="off" required></label>'
            + '<button type="submit">Create administrator</button></form></section>', self._nav(session)
        )

    def _request_form(self, session, categories, error="", values=None, field_error=None):
        values = values or {}
        alert = f'<p class="error" role="alert">{_e(error)}</p>' if error else ""
        def field(name, label, minimum, maximum, multiline=False):
            issue = (
                f'<span class="error" id="{name}-error">{_e(field_error)}</span>'
                if field_error and name in field_error.lower()
                else ""
            )
            safe_value = _e(values.get(name, ""))
            if multiline:
                control = f'<textarea id="{name}" name="{name}" minlength="{minimum}" maxlength="{maximum}" required>{safe_value}</textarea>'
            else:
                control = f'<input id="{name}" name="{name}" minlength="{minimum}" maxlength="{maximum}" value="{safe_value}" required>'
            return f'<label for="{name}">{label}{control}{issue}</label>'

        options = "".join(
            f'<option value="{_e(category["id"])}">{_e(category["label"])}</option>'
            for category in categories
        )
        category_error = (
            f'<span class="error" id="category_id-error">{_e(field_error)}</span>'
            if field_error and "category" in field_error.lower()
            else ""
        )
        body = (
            alert
            + '<section class="panel"><p>Fields marked required must be completed. A reference is created when the request is saved.</p>'
            + '<form method="post" action="/requests">'
            + self._hidden_csrf(session)
            + field("title", "Title (5–120 characters)", 5, 120)
            + field("description", "Description (10–2,000 characters)", 10, 2000, True)
            + field("location", "Location (3–200 characters)", 3, 200)
            + '<label for="category_id">Category<select id="category_id" name="category_id" required>'
            + '<option value="">Choose a category</option>'
            + options
            + f"</select>{category_error}</label><button type=\"submit\">Submit request</button></form></section>"
        )
        return _page("Submit a service request", body, self._nav(session))

    def _list_page(self, session, requests, filters=None):
        filters = filters or {}
        role = "staff requests" if session.get("role") == "Staff" else "your requests"
        cards = "".join(
            '<article class="card"><div class="row"><strong>'
            + f'<a href="/requests/{_e(item["reference"])}">{_e(item["reference"])}</a></strong>'
            + f'<span>{_e(item["status"])}</span></div><h2>{_e(item["title"])}</h2>'
            + f'<p>{_e(item["category_label"])} · {_e(item["location"])}</p>'
            + f'<p class="muted">Submitted {_e(item["submitted_at"])}</p></article>'
            for item in requests
        )
        if not cards:
            cards = '<section class="panel"><p>No requests are available.</p></section>'
        submit = (
            '<p><a class="button" href="/requests/new">Submit a request</a></p>'
            if session.get("role") == "Citizen"
            else ""
        )
        search = ""
        if session.get("role") == "Staff":
            selected = lambda name, value: " selected" if filters.get(name, "") == value else ""
            search = (
                '<section class="panel"><h2>Find requests</h2><form method="get" action="/requests">'
                f'<label>Reference or title<input name="q" maxlength="120" value="{_e(filters.get("q", ""))}"></label>'
                '<label>Category<select name="category"><option value="">All categories</option>'
                + "".join(f'<option value="{_e(c["id"])}"{selected("category", c["id"])}>{_e(c["label"])}</option>' for c in self.store.categories())
                + '</select></label><label>Status<select name="status"><option value="">All statuses</option>'
                + "".join(f'<option{selected("status", s)}>{s}</option>' for s in sorted(LifecyclePolicy.NEXT.keys() | {"Rejected"}))
                + '</select></label><label>Assignee username<input name="assignee" maxlength="80" value="'
                + _e(filters.get("assignee", ""))
                + '"></label><label>Sort by<select name="sort">'
                + "".join(f'<option value="{v}"{selected("sort", v)}>{label}</option>' for v,label in (("submitted","Submission date"),("due","Due date"),("reference","Reference"),("title","Title")))
                + '</select></label><label>Direction<select name="direction">'
                + ''.join(f'<option value="{v}"{selected("direction", v)}>{v.title()}</option>' for v in ("asc","desc"))
                + '</select></label><button type="submit">Apply filters</button><a href="/requests">Clear filters</a></form></section>'
            )
        return _page(
            "Requests", f"<p>View {role} and their current status.</p>{submit}{search}{cards}", self._nav(session)
        )

    def _admin_accounts_page(self, session, accounts, error=""):
        alert = f'<p class="error" role="alert">{_e(error)}</p>' if error else ""
        rows = "".join(
            '<tr><td>' + _e(a["username"]) + '</td><td><form method="post" action="/admin/accounts">'
            + self._hidden_csrf(session) + f'<input type="hidden" name="username" value="{_e(a["username"])}">'
            + '<label>Role<select name="role">' + "".join(
                f'<option{" selected" if a["role"] == role else ""}>{role}</option>'
                for role in ("Citizen", "Staff", "Management", "Administrator"))
            + '</select></label><label>Department<input name="department" maxlength="80" value="'
            + _e(a["department"]) + '"></label><label>State<select name="active">'
            + f'<option value="1"{" selected" if a["active"] else ""}>Active</option>'
            + f'<option value="0"{" selected" if not a["active"] else ""}>Inactive</option>'
            + '</select></label><label>New password (optional)<input name="password" type="password" minlength="12" maxlength="1024" autocomplete="new-password"></label>'
            + '<button type="submit">Update account</button></form></td></tr>' for a in accounts)
        form = (
            '<section class="panel"><h2>Create or update account</h2><form method="post" action="/admin/accounts">'
            + self._hidden_csrf(session)
            + '<label>Username<input name="username" maxlength="80" required></label>'
            + '<label>Role<select name="role"><option>Citizen</option><option>Staff</option><option>Management</option><option>Administrator</option></select></label>'
            + '<label>Department (staff only)<input name="department" maxlength="80"></label>'
            + '<label>Account state<select name="active"><option value="1">Active</option><option value="0">Inactive</option></select></label>'
            + '<label>Password (required for new accounts; 12+ characters)<input name="password" type="password" minlength="12" maxlength="1024" autocomplete="new-password"></label>'
            + '<button type="submit">Save account</button></form></section>'
        )
        return _page("Account administration", alert + form + '<section class="panel"><h2>Accounts</h2><table><thead><tr><th>Username</th><th>Role, department, state and password</th></tr></thead><tbody>' + rows + '</tbody></table></section>', self._nav(session))

    def _admin_categories_page(self, session, categories, error=""):
        alert = f'<p class="error" role="alert">{_e(error)}</p>' if error else ""
        rows = "".join(
            '<tr><td>' + _e(c["id"]) + '</td><td><form method="post" action="/admin/categories">'
            + self._hidden_csrf(session) + f'<input type="hidden" name="category_id" value="{_e(c["id"])}">'
            + f'<label>Label<input name="label" maxlength="120" value="{_e(c["label"])}" required></label>'
            + f'<label>Department<input name="department" maxlength="80" value="{_e(c["department"])}" required></label>'
            + f'<label>State<select name="active"><option value="1"{" selected" if c["active"] else ""}>Active</option><option value="0"{" selected" if not c["active"] else ""}>Inactive</option></select></label>'
            + '<button type="submit">Update category</button></form></td></tr>' for c in categories)
        create = ('<section class="panel"><h2>Add category</h2><form method="post" action="/admin/categories">'
                  + self._hidden_csrf(session) + '<label>Category identifier<input name="category_id" maxlength="80" required></label>'
                  + '<label>Label<input name="label" maxlength="120" required></label><label>Department<input name="department" maxlength="80" required></label>'
                  + '<input type="hidden" name="active" value="1"><button type="submit">Add category</button></form></section>')
        return _page("Category administration", alert + create + '<section class="panel"><h2>Categories</h2><table><thead><tr><th>Identifier</th><th>Label, department and state</th></tr></thead><tbody>' + rows + '</tbody></table><p>Inactive categories stay attached to past requests but cannot be selected for new submissions.</p></section>', self._nav(session))

    def _management_page(self, session, summary, date_from, date_to, category, status):
        counts = f'<li>Open: {summary["open_count"]}</li><li>Overdue: {summary["overdue_count"]}</li>' + "".join(f'<li>{_e(k)}: {int(v)}</li>' for k,v in sorted(summary["counts"].items()))
        category_counts = "".join(f'<li>{_e(row["category_label"])} · {_e(row["status"])}: {int(row["count"])}</li>' for row in summary["category_counts"]) or "<li>No requests match these filters.</li>"
        today = datetime.now(timezone.utc).date()
        rows = "".join(f'<tr><td>{_e(r["reference"])}</td><td>{_e(r["status"])}</td><td>{_e(r["category_label"])}</td><td>{_e(r["assignee"] or "Unassigned")}</td><td>{_e(r["submitted_at"])}</td><td>{max(0, (today - datetime.fromisoformat(r["submitted_at"]).date()).days)}</td><td>{_e(r["title"])}</td></tr>' for r in summary["requests"])
        form = ('<section class="panel"><h2>Report filters</h2><form method="get" action="/management/summary">'
                f'<label>From<input type="date" name="from" value="{_e(date_from)}"></label><label>To<input type="date" name="to" value="{_e(date_to)}"></label>'
                f'<label>Category<select name="category"><option value="">All categories</option>'
                + "".join(f'<option value="{_e(c["id"])}"{" selected" if category == c["id"] else ""}>{_e(c["label"])}</option>' for c in self.store.categories())
                + '</select></label><label>Status<select name="status"><option value="">All statuses</option>'
                + "".join(f'<option{" selected" if status == s else ""}>{_e(s)}</option>' for s in sorted(LifecyclePolicy.NEXT.keys() | {"Rejected"}))
                + '</select></label><button type="submit">Update summary</button></form></section>')
        return _page("Management summary", form + '<section class="panel"><h2>Requests by status</h2><ul>' + counts + '</ul><h2>Requests by category and status</h2><ul>' + category_counts + '</ul></section><section class="panel"><h2>Request activity</h2><table><thead><tr><th>Reference</th><th>Status</th><th>Category</th><th>Assignee</th><th>Submitted</th><th>Age (days)</th><th>Title</th></tr></thead><tbody>' + rows + '</tbody></table></section>', self._nav(session))

    def _detail_page(self, session, detail, error=""):
        request = detail["request"]
        events = "".join(
            f'<li><strong>{_e(event["to_status"])}</strong> — {_e(event["occurred_at"])}'
            f'<p>{_e(event["explanation"])}</p></li>'
            for event in detail["events"]
        ) or "<li>No status changes have been recorded.</li>"
        alert = f'<p class="error" role="alert">{_e(error)}</p>' if error else ""
        body = (
            alert
            + f'<section class="panel"><p><strong>Reference:</strong> {_e(request["reference"])}</p>'
            + f'<p><strong>Status:</strong> {_e(request["status"])}</p>'
            + f'<p><strong>Category:</strong> {_e(request["category_label"])}</p>'
            + f'<p><strong>Title:</strong> {_e(request["title"])}</p>'
            + f'<p><strong>Description:</strong><br>{_e(request["description"])}</p>'
            + f'<p><strong>Location:</strong> {_e(request["location"])}</p>'
            + f'<p><strong>Submitted:</strong> {_e(request["submitted_at"])}</p>'
            + f'<p><strong>Assigned staff:</strong> {_e(request["assignee"] or "Not assigned")}</p>'
            + f'<p><strong>Due:</strong> {_e(request["due_at"] or "Not set")}</p>'
            + f'<h2>Progress history</h2><ol>{events}</ol></section>'
        )
        if session.get("role") == "Staff":
            body += (
                f'<p><strong>Requester:</strong> {_e(request["citizen_id"])}</p>'
                + '<section class="panel"><h2>Update status</h2>'
                '<form method="post" action="/requests/'
                + _e(request["reference"])
                + '/transition">'
                + self._hidden_csrf(session)
                + f'<input type="hidden" name="version" value="{int(request["version"])}">'
                + '<label>New status<select name="target" required>'
                + "".join(
                    f'<option>{_e(target)}</option>'
                    for target in sorted(LifecyclePolicy.NEXT.get(request["status"], set()))
                )
                + '</select></label><label>Explanation<textarea name="explanation" maxlength="2000"></textarea></label>'
                + '<label>Assignee username (required when accepting)<input name="assignee" maxlength="80"></label>'
                + '<label>Due date (required when accepting)<input name="due_at" type="datetime-local"></label>'
                + '<button type="submit">Save update</button></form></section>'
            )
        return _page("Request details", body, self._nav(session))

    def __call__(self, environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")
        session = self._decode_session(environ.get("HTTP_COOKIE"))
        new_session = session is None
        if session is None:
            session = self._new_session()
        cookie_header = self._cookie(session) if new_session else None
        if session.get("account_id"):
            account = self.store.authenticate_session(session["account_id"])
            if account is None:
                session = self._new_session()
                cookie_header = self._cookie(session)
            else:
                session["role"] = account["role"]

        try:
            form = self._body(environ) if method == "POST" else {}
            if method == "POST" and not hmac.compare_digest(
                str(form.get("csrf", "")), session["csrf"]
            ):
                return self._response(
                    start_response,
                    "400 Bad Request",
                    _page("Form expired", '<p class="error" role="alert">Refresh the page and try again.</p>', self._nav(session)),
                    cookie=cookie_header,
                )

            if method == "GET" and path in {"/", "/login"}:
                if session.get("account_id"):
                    return self._redirect(start_response, self._landing_path(session.get("role")), cookie_header)
                return self._response(
                    start_response, "200 OK", self._login_page(session), cookie=cookie_header
                )
            if method == "GET" and path == "/register":
                return self._response(
                    start_response, "200 OK", self._register_page(session), cookie=cookie_header
                )
            if method == "GET" and path == "/setup/administrator":
                if self.admin_setup_token is None or not self.store.needs_admin_setup():
                    raise Forbidden("Administrator setup is already complete")
                return self._response(start_response, "200 OK", self._bootstrap_page(session), cookie=cookie_header)
            if method == "POST" and path == "/setup/administrator":
                supplied_token = form.get("setup_token", "")
                if self.admin_setup_token is None or not hmac.compare_digest(supplied_token, self.admin_setup_token):
                    raise Forbidden("Administrator setup is not available")
                try:
                    account_id = self.store.bootstrap_administrator(form.get("username"), form.get("password"), self._now())
                except InvalidTransition as exc:
                    return self._response(start_response, "400 Bad Request", self._bootstrap_page(session, str(exc)), cookie=cookie_header)
                session = self._new_session(account_id)
                session["role"] = "Administrator"
                return self._redirect(start_response, "/admin/accounts", self._cookie(session))
            if method == "POST" and path == "/register":
                try:
                    account = self.store.register_citizen(
                        form.get("username"), form.get("password"), self._now()
                    )
                except InvalidTransition as exc:
                    return self._response(
                        start_response,
                        "400 Bad Request",
                        self._register_page(session, str(exc)),
                        cookie=cookie_header,
                    )
                session = self._new_session(account["id"])
                session["role"] = account["role"]
                return self._redirect(start_response, "/requests", self._cookie(session))
            if method == "POST" and path == "/login":
                username = form.get("username", "")
                keys = self._login_keys(environ, username)
                retry_after = self._login_retry_after(keys, time.monotonic())
                if retry_after:
                    return self._response(
                        start_response,
                        "429 Too Many Requests",
                        self._login_page(
                            session, "Too many sign-in attempts. Try again later."
                        ),
                        headers=[("Retry-After", str(retry_after))],
                        cookie=cookie_header,
                    )
                account = self.store.authenticate(username, form.get("password", ""))
                if account is None:
                    self._record_login_failure(keys, time.monotonic())
                    return self._response(
                        start_response,
                        "401 Unauthorized",
                        self._login_page(session, "Username or password is incorrect."),
                        cookie=cookie_header,
                    )
                self._clear_login_failure(keys[0])
                session = self._new_session(account["id"])
                session["role"] = account["role"]
                return self._redirect(start_response, self._landing_path(account["role"]), self._cookie(session))
            if method == "POST" and path == "/logout":
                session = self._new_session()
                return self._redirect(start_response, "/login", self._cookie(session))

            if not session.get("account_id"):
                return self._redirect(start_response, "/login", cookie_header)
            if method == "GET" and path == "/requests":
                query = parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=True)
                filters = {key: query.get(key, [""])[0][:120] for key in ("q", "category", "status", "assignee", "sort", "direction")}
                if session.get("role") == "Staff":
                    requests = self.store.list_staff_requests(
                        session["account_id"], filters["q"], filters["category"],
                        filters["status"], filters["assignee"], filters["sort"] or "submitted",
                        filters["direction"] or "desc",
                    )
                else:
                    requests = self.store.list_requests(session["account_id"])
                return self._response(
                    start_response,
                    "200 OK",
                    self._list_page(session, requests, filters),
                    cookie=cookie_header,
                )
            if method == "GET" and path == "/admin/accounts":
                if session.get("role") != "Administrator":
                    raise Forbidden("Administrator access required")
                return self._response(start_response, "200 OK", self._admin_accounts_page(session, self.store.accounts(session["account_id"])), cookie=cookie_header)
            if method == "GET" and path == "/admin/categories":
                if session.get("role") != "Administrator":
                    raise Forbidden("Administrator access required")
                return self._response(start_response, "200 OK", self._admin_categories_page(session, self.store.all_categories(session["account_id"])), cookie=cookie_header)
            if method == "POST" and path == "/admin/categories":
                if session.get("role") != "Administrator":
                    raise Forbidden("Administrator access required")
                try:
                    self.store.manage_category(session["account_id"], form.get("category_id"), form.get("label"), form.get("department"), form.get("active"))
                except InvalidTransition as exc:
                    return self._response(start_response, "400 Bad Request", self._admin_categories_page(session, self.store.all_categories(session["account_id"]), str(exc)), cookie=cookie_header)
                return self._redirect(start_response, "/admin/categories", cookie_header)
            if method == "POST" and path == "/admin/accounts":
                if session.get("role") != "Administrator":
                    raise Forbidden("Administrator access required")
                try:
                    self.store.manage_account(
                        session["account_id"], form.get("username"), form.get("role"),
                        form.get("department", ""), form.get("active"), form.get("password", ""), self._now()
                    )
                except InvalidTransition as exc:
                    return self._response(start_response, "400 Bad Request", self._admin_accounts_page(session, self.store.accounts(session["account_id"]), str(exc)), cookie=cookie_header)
                return self._redirect(start_response, "/admin/accounts", cookie_header)
            if method == "GET" and path == "/management/summary":
                if session.get("role") not in {"Management", "Administrator"}:
                    raise Forbidden("Management access required")
                query = parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=True)
                date_from = query.get("from", [""])[0][:10]
                date_to = query.get("to", [""])[0][:10]
                category = query.get("category", [""])[0][:80]
                status = query.get("status", [""])[0][:30]
                try:
                    summary = self.store.management_summary(session["account_id"], date_from, date_to, category, status)
                except InvalidTransition as exc:
                    return self._response(start_response, "400 Bad Request", _page("Invalid report filters", f'<p class="error" role="alert">{_e(exc)}</p><p><a href="/management/summary">Return to summary</a></p>', self._nav(session)), cookie=cookie_header)
                return self._response(start_response, "200 OK", self._management_page(session, summary, date_from, date_to, category, status), cookie=cookie_header)
            if method == "GET" and path == "/requests/new":
                if session.get("role") != "Citizen":
                    raise Forbidden("Only citizens can submit requests")
                return self._response(
                    start_response,
                    "200 OK",
                    self._request_form(session, self.store.categories()),
                    cookie=cookie_header,
                )
            if method == "POST" and path == "/requests":
                if session.get("role") != "Citizen":
                    raise Forbidden("Only citizens can submit requests")
                values = {key: form.get(key, "") for key in ("title", "description", "location")}
                try:
                    reference = self.store.submit_request(
                        session["account_id"],
                        values["title"],
                        values["description"],
                        values["location"],
                        form.get("category_id", ""),
                        self._now(),
                    )
                except InvalidTransition as exc:
                    message = str(exc)
                    return self._response(
                        start_response,
                        "400 Bad Request",
                        self._request_form(
                            session, self.store.categories(), message, values, message
                        ),
                        cookie=cookie_header,
                    )
                return self._redirect(start_response, f"/requests/{reference}", cookie_header)

            reference = path.removeprefix("/requests/").split("/", 1)[0]
            if reference and method == "GET" and path == f"/requests/{reference}":
                return self._response(
                    start_response,
                    "200 OK",
                    self._detail_page(
                        session, self.store.history(session["account_id"], reference)
                    ),
                    cookie=cookie_header,
                )
            if reference and method == "POST" and path == f"/requests/{reference}/transition":
                if session.get("role") != "Staff":
                    raise Forbidden("Only authorised staff can update request status")
                version = form.get("version", "")
                if not version.isdecimal():
                    raise InvalidTransition("Reload this request before updating it")
                target = form.get("target", "")
                due_at = form.get("due_at", "").strip() or None
                if due_at:
                    try:
                        parsed_due = datetime.fromisoformat(due_at)
                        if parsed_due.tzinfo is None:
                            parsed_due = parsed_due.replace(
                                tzinfo=ZoneInfo("Africa/Johannesburg")
                            )
                        due_at = parsed_due.astimezone(timezone.utc).isoformat()
                    except ValueError as exc:
                        raise InvalidTransition("Enter a valid due date") from exc
                try:
                    self.coordinator.transition(
                        session["account_id"],
                        reference,
                        target,
                        int(version),
                        form.get("explanation", ""),
                        form.get("assignee", "").strip() or None,
                        due_at,
                    )
                except (InvalidTransition, Conflict) as exc:
                    detail = self.store.history(session["account_id"], reference)
                    return self._response(
                        start_response,
                        "400 Bad Request" if isinstance(exc, InvalidTransition) else "409 Conflict",
                        self._detail_page(session, detail, str(exc)),
                        cookie=cookie_header,
                    )
                return self._redirect(start_response, f"/requests/{reference}", cookie_header)
            return self._response(
                start_response,
                "404 Not Found",
            _page("Page not found", '<p>The requested page could not be found.</p>', self._nav(session)),
                cookie=cookie_header,
            )
        except Forbidden:
            return self._response(
                start_response,
                "403 Forbidden",
                _page("Not available", '<p class="error" role="alert">This request is not available to your account.</p>', self._nav(session)),
                cookie=cookie_header,
            )
        except (InvalidTransition, Conflict) as exc:
            return self._response(
                start_response,
                "400 Bad Request" if isinstance(exc, InvalidTransition) else "409 Conflict",
                _page("Unable to update request", f'<p class="error" role="alert">{_e(exc)}</p><p><a href="/requests">Return to requests</a></p>', self._nav(session)),
                cookie=cookie_header,
            )
        except Exception:
            return self._response(
                start_response,
                "500 Internal Server Error",
                _page(
                    "Request could not be completed",
                    '<p class="error" role="alert">The request could not be completed. Try again later.</p>',
                    self._nav(session),
                ),
                cookie=cookie_header,
            )
