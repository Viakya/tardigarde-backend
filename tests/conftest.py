"""
Shared pytest fixtures for the Tardigrade backend API test suite.

Uses a fresh in-memory SQLite DB for each test via table drop/recreate.
All seed data is returned as plain dicts to avoid DetachedInstanceError.
"""

import pytest

from app import create_app
from app.extensions import db as _db
from app.services.token_service import generate_access_token
from config import TestingConfig


# ---------------------------------------------------------------------------
# App / Client fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    """Create the Flask application with testing config (SQLite in-memory)."""
    application = create_app(config_object=TestingConfig)
    with application.app_context():
        _db.create_all()
    yield application


@pytest.fixture(autouse=True)
def _clean_tables(app):
    """
    Wipe all rows between tests without dropping/recreating tables.

    drop_all() + create_all() causes SQLite to raise "index already exists"
    for explicitly-named indexes (e.g. ix_batch_resources_batch_id) because
    SQLAlchemy's in-memory metadata still tracks them after the first session.
    Instead we delete every row with FK checks disabled, which is both faster
    and safe for an in-memory SQLite database.
    """
    yield
    with app.app_context():
        _db.session.remove()
        con = _db.engine.connect()
        trans = con.begin()
        # Disable FK enforcement so we can delete in any order
        con.execute(_db.text("PRAGMA foreign_keys = OFF"))
        for table in reversed(_db.metadata.sorted_tables):
            con.execute(table.delete())
        con.execute(_db.text("PRAGMA foreign_keys = ON"))
        trans.commit()
        con.close()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


# ---------------------------------------------------------------------------
# User seed helpers
# ---------------------------------------------------------------------------

SEED_USERS = {
    "admin":    {"email": "admin@test.com",    "full_name": "Test Admin",    "password": "Admin@1234",    "role": "admin"},
    "director": {"email": "director@test.com", "full_name": "Test Director", "password": "Director@1234", "role": "director"},
    "manager":  {"email": "manager@test.com",  "full_name": "Test Manager",  "password": "Manager@1234",  "role": "manager"},
    "coach":    {"email": "coach@test.com",    "full_name": "Test Coach",    "password": "Coach@1234",    "role": "coach"},
    "student":  {"email": "student@test.com",  "full_name": "Test Student",  "password": "Student@1234",  "role": "student"},
    "parent":   {"email": "parent@test.com",   "full_name": "Test Parent",   "password": "Parent@1234",   "role": "parent"},
}


@pytest.fixture
def seed_users(app):
    """
    Create one user for every role and return a dict mapping
    role -> plain dict with user data (id, email, full_name, role).

    Returns plain dicts to avoid SQLAlchemy DetachedInstanceError.
    """
    from app.models import User

    users = {}
    with app.app_context():
        for role, data in SEED_USERS.items():
            user = User(email=data["email"], full_name=data["full_name"], role=data["role"])
            user.set_password(data["password"])
            _db.session.add(user)
            _db.session.flush()
            # Eagerly snapshot into a plain dict
            users[role] = {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
            }
        _db.session.commit()
    return users


@pytest.fixture
def auth_headers(app, seed_users):
    """
    Factory fixture: returns a function that produces
    ``{"Authorization": "Bearer <token>"}`` headers for a given role.
    """
    from flask_jwt_extended import create_access_token

    def _make(role: str) -> dict:
        user_data = seed_users[role]
        with app.app_context():
            token = create_access_token(
                identity=str(user_data["id"]),
                additional_claims={
                    "email": user_data["email"],
                    "role": user_data["role"],
                },
            )
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    return _make


# ---------------------------------------------------------------------------
# Data-factory fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def seed_batch(client, auth_headers):
    """Create and return a sample batch dict via the API."""
    payload = {
        "batch_name": "Foundation Demo",
        "year": 2026,
        "batch_cost": 15000,
    }
    resp = client.post("/api/v1/batches", json=payload, headers=auth_headers("director"))
    data = resp.get_json()
    return data["data"]["batch"]


@pytest.fixture
def seed_student(client, auth_headers, seed_users, seed_batch):
    """Create and return a sample student profile dict via the API."""
    student_user = seed_users["student"]
    payload = {
        "user_id": student_user["id"],
        "batch_id": seed_batch["id"],
        "phone_number": "9876543210",
        "address": "123 Test Lane",
    }
    resp = client.post("/api/v1/students", json=payload, headers=auth_headers("director"))
    data = resp.get_json()
    return data["data"]["student"]


@pytest.fixture
def seed_teacher(client, auth_headers, seed_users):
    """Create and return a sample teacher profile dict via the API."""
    coach_user = seed_users["coach"]
    payload = {
        "user_id": coach_user["id"],
        "specialization": "Mathematics",
        "phone_number": "9876500000",
    }
    resp = client.post("/api/v1/teachers", json=payload, headers=auth_headers("director"))
    data = resp.get_json()
    return data["data"]["teacher"]
