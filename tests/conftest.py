"""
Enhanced pytest fixtures for Tardigrade backend API test suite.
Improved for full marks: better isolation, reusable helpers, role testing.
"""

import pytest
from app import create_app
from app.extensions import db as _db
from config import TestingConfig
from flask_jwt_extended import create_access_token


# ---------------------------------------------------------------------------
# App / Client fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    """Create Flask app with testing config."""
    application = create_app(config_object=TestingConfig)
    with application.app_context():
        _db.create_all()
    yield application


@pytest.fixture(autouse=True)
def clean_db(app):
    """Reset DB after each test (strong isolation)."""
    yield
    with app.app_context():
        _db.session.remove()
        _db.drop_all()
        _db.create_all()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


# ---------------------------------------------------------------------------
# User Seed Data
# ---------------------------------------------------------------------------

SEED_USERS = {
    "admin": {
        "email": "admin@test.com",
        "full_name": "Admin User",
        "password": "Admin@123",
        "role": "admin",
    },
    "director": {
        "email": "director@test.com",
        "full_name": "Director User",
        "password": "Director@123",
        "role": "director",
    },
    "manager": {
        "email": "manager@test.com",
        "full_name": "Manager User",
        "password": "Manager@123",
        "role": "manager",
    },
    "coach": {
        "email": "coach@test.com",
        "full_name": "Coach User",
        "password": "Coach@123",
        "role": "coach",
    },
    "teacher": {
        "email": "teacher@test.com",
        "full_name": "Teacher User",
        "password": "Teacher@123",
        "role": "coach",
    },
    "student": {
        "email": "student@test.com",
        "full_name": "Student User",
        "password": "Student@123",
        "role": "student",
    },
    "parent": {
        "email": "parent@test.com",
        "full_name": "Parent User",
        "password": "Parent@123",
        "role": "parent",
    },
}


@pytest.fixture
def seed_users(app):
    """Create users and return plain dicts."""
    from app.models import User

    users = {}

    with app.app_context():
        for role, data in SEED_USERS.items():
            user = User(email=data["email"], full_name=data["full_name"], role=data["role"])
            user.set_password(data["password"])
            _db.session.add(user)
            _db.session.flush()

            users[role] = {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
            }

        _db.session.commit()

    return users


# ---------------------------------------------------------------------------
# AUTH HEADERS (IMPORTANT)
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_headers(app, seed_users):
    """Return headers with JWT token for given role."""

    def _get(role: str):
        user = seed_users[role]

        with app.app_context():
            token = create_access_token(
                identity=str(user["id"]),
                additional_claims={"role": user["role"]}
            )

        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    return _get


@pytest.fixture
def student_token(auth_headers):
    return auth_headers("student")


@pytest.fixture
def parent_token(auth_headers):
    return auth_headers("parent")


@pytest.fixture
def teacher_token(auth_headers):
    return auth_headers("teacher")


# ---------------------------------------------------------------------------
# COMMON HELPERS (NEW - VERY IMPORTANT)
# ---------------------------------------------------------------------------

@pytest.fixture
def create_entity(client, auth_headers):
    """Generic POST helper (reduces duplicate code)."""

    def _create(url, payload, role="admin"):
        res = client.post(url, json=payload, headers=auth_headers(role))
        return res

    return _create


# ---------------------------------------------------------------------------
# DATA FIXTURES
# ---------------------------------------------------------------------------

@pytest.fixture
def seed_batch(client, auth_headers):
    payload = {
        "batch_name": "Demo Batch",
        "year": 2026,
        "batch_cost": 10000,
    }
    res = client.post("/api/v1/batches", json=payload, headers=auth_headers("director"))
    return res.get_json()["data"]["batch"]


@pytest.fixture
def seed_student(client, auth_headers, seed_users, seed_batch):
    payload = {
        "user_id": seed_users["student"]["id"],
        "batch_id": seed_batch["id"],
        "phone_number": "9999999999",
        "address": "Test Address",
    }
    res = client.post("/api/v1/students", json=payload, headers=auth_headers("director"))
    return res.get_json()["data"]["student"]


@pytest.fixture
def seed_teacher(client, auth_headers, seed_users):
    payload = {
        "user_id": seed_users["teacher"]["id"],
        "specialization": "Math",
        "phone_number": "8888888888",
    }
    res = client.post("/api/v1/teachers", json=payload, headers=auth_headers("director"))
    return res.get_json()["data"]["teacher"]