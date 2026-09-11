from __future__ import annotations
import base64, hashlib, hmac, json, os, secrets, sqlite3, time
from pathlib import Path

DB = Path(os.getenv("AURA_AUTH_DB", str(Path(__file__).resolve().parent.parent / "data" / "aura_auth.db")))
DB.parent.mkdir(parents=True, exist_ok=True)

ROLE_ALLOWLIST = {"researcher", "project_manager", "developer", "admin"}


def _auth_secret() -> bytes:
    secret = os.getenv("AURA_AUTH_SECRET", "").strip()
    if not secret:
        if os.getenv("AURA_ENV", "development").lower() in {"production", "prod"}:
            raise RuntimeError("AURA_AUTH_SECRET must be configured in production.")
        secret = "aura-development-secret-change-in-production"
    if len(secret) < 32:
        if os.getenv("AURA_ENV", "development").lower() in {"production", "prod"}:
            raise RuntimeError("AURA_AUTH_SECRET must contain at least 32 characters in production.")
    return secret.encode()


def _normalize_email(email: str) -> str:
    value = email.strip().lower()
    if len(value) > 320 or "@" not in value or value.startswith("@") or value.endswith("@"):
        raise ValueError("Invalid email address")
    return value


def _db_connection():
    """Return a SQLite connection that callers must close.

    A sqlite3.Connection context manager commits/rolls back transactions but
    does not close the connection. Explicit closure is required on Windows
    so temporary auth databases can be removed cleanly after tests.
    """
    DB.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB)


def init_db():
    # Tests and deployments may swap AURA_AUTH_DB at runtime; always ensure
    # the current parent directory exists before opening SQLite.
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = _db_connection()
    try:
        con.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'researcher', created_at REAL NOT NULL)")
        con.execute("CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, user_id INTEGER, action TEXT NOT NULL, created_at REAL NOT NULL, detail TEXT)")
        con.commit()
    finally:
        con.close()


def _hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 160000)
    return base64.b64encode(salt + dk).decode()


def _check(password: str, encoded: str) -> bool:
    raw = base64.b64decode(encoded.encode()); salt, expected = raw[:16], raw[16:]
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 160000)
    return hmac.compare_digest(actual, expected)


def register(email: str, password: str, role: str = "researcher") -> dict:
    init_db()
    email = _normalize_email(email)
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters")
    role = role if role in ROLE_ALLOWLIST else "researcher"
    con = _db_connection()
    try:
        try:
            cur = con.execute("INSERT INTO users(email,password_hash,role,created_at) VALUES(?,?,?,?)", (email, _hash(password), role, time.time()))
            con.commit()
            uid = cur.lastrowid
        except sqlite3.IntegrityError:
            con.rollback()
            raise ValueError("User already exists")
    finally:
        con.close()
    return {"id": uid, "email": email, "role": role}


def login(email: str, password: str) -> dict:
    init_db()
    email = _normalize_email(email)
    con = _db_connection()
    try:
        row = con.execute("SELECT id,email,password_hash,role FROM users WHERE email=?", (email,)).fetchone()
    finally:
        con.close()
    if not row or not _check(password, row[2]): raise ValueError("Invalid credentials")
    payload = {"sub": row[0], "email": row[1], "role": row[3], "exp": int(time.time()) + 86400}
    body = base64.urlsafe_b64encode(json.dumps(payload,separators=(",",":")).encode()).decode().rstrip("=")
    secret = _auth_secret()
    sig = hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()
    return {"access_token": body + "." + sig, "token_type": "bearer", "user": {"id": row[0], "email": row[1], "role": row[3]}}


def verify(token: str) -> dict:
    if not isinstance(token, str) or not token or len(token) > 4096:
        raise ValueError("Invalid token")
    try:
        body, sig = token.split(".", 1)
    except ValueError:
        raise ValueError("Invalid token")
    if not body or not sig or len(sig) != 64:
        raise ValueError("Invalid token")
    secret = _auth_secret()
    if not hmac.compare_digest(hmac.new(secret, body.encode(), hashlib.sha256).hexdigest(), sig): raise ValueError("Invalid token")
    try:
        raw = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
        payload = json.loads(raw)
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError("Invalid token")
    if not isinstance(payload, dict) or not isinstance(payload.get("exp"), int) or not payload.get("sub"):
        raise ValueError("Invalid token")
    if payload["exp"] < int(time.time()):
        raise ValueError("Token expired")
    return payload

init_db()
