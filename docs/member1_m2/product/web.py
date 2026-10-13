"""Small server-rendered WSGI interface for the CivicConnect request workflow."""

from datetime import datetime, timezone
from html import escape
import base64
import hashlib
import hmac
import json
import secrets
from http.cookies import SimpleCookie
from urllib.parse import parse_qs
from zoneinfo import ZoneInfo

from lifecycle import (
    Conflict,
    Forbidden,
    InvalidTransition,
    RequestLifecycleCoordinator,
)


COOKIE_NAME = "civicconnect_session"
SESSION_SECONDS = 1800
MAX_BODY_BYTES = 32_768


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

    def __init__(self, store, session_secret, cookie_secure=False, clock=None):
        if isinstance(session_secret, str):
            session_secret = session_secret.encode("utf-8")
        if not isinstance(session_secret, bytes) or len(session_secret) < 32:
            raise ValueError("CIVICCONNECT_SESSION_SECRET must contain at least 32 bytes")
        self.store = store
        self.secret = session_secret
        self.cookie_secure = cookie_secure
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.coordinator = RequestLifecycleCoordinator(store, clock=self._now)

    def _now(self):
        return self.clock().astimezone(timezone.utc).isoformat()

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
            return (
                f'<span>{_e(session["account_id"])}</span>'
                '<form method="post" action="/logout" style="display:inline">'
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
            + '<label>Password<input name="password" type="password" autocomplete="new-password" maxlength="1024" required></label>'
            + '<button type="submit">Create account</button></form></section>',
            self._nav(session),
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

    def _list_page(self, session, requests):
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
        return _page(
            "Requests", f"<p>View {role} and their current status.</p>{submit}{cards}", self._nav(session)
        )

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
                    return self._redirect(start_response, "/requests", cookie_header)
                return self._response(
                    start_response, "200 OK", self._login_page(session), cookie=cookie_header
                )
            if method == "GET" and path == "/register":
                return self._response(
                    start_response, "200 OK", self._register_page(session), cookie=cookie_header
                )
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
                account = self.store.authenticate(
                    form.get("username", ""), form.get("password", "")
                )
                if account is None:
                    return self._response(
                        start_response,
                        "401 Unauthorized",
                        self._login_page(session, "Username or password is incorrect."),
                        cookie=cookie_header,
                    )
                session = self._new_session(account["id"])
                session["role"] = account["role"]
                return self._redirect(start_response, "/requests", self._cookie(session))
            if method == "POST" and path == "/logout":
                session = self._new_session()
                return self._redirect(start_response, "/login", self._cookie(session))

            if not session.get("account_id"):
                return self._redirect(start_response, "/login", cookie_header)
            if method == "GET" and path == "/requests":
                return self._response(
                    start_response,
                    "200 OK",
                    self._list_page(session, self.store.list_requests(session["account_id"])),
                    cookie=cookie_header,
                )
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
                self.coordinator.transition(
                    session["account_id"],
                    reference,
                    target,
                    int(version),
                    form.get("explanation", ""),
                    form.get("assignee", "").strip() or None,
                    due_at,
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
