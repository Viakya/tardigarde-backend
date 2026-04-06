from flask import Flask
from flask_cors import CORS
from flasgger import swag_from
from flask_jwt_extended.exceptions import JWTExtendedException
from sqlalchemy.exc import SQLAlchemyError

from app.commands import register_commands
from app.core.exceptions import AppError
from app.docs import init_swagger
from app.extensions import db, jwt, migrate
from app.routes import register_blueprints
from app.utils.response import api_response
from config import get_config


def create_app(config_object=None):
    app = Flask(__name__)
    CORS(
        app,
        origins="*",
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        supports_credentials=False,
    )

    if config_object is None:
        config_object = get_config()

    app.config.from_object(config_object)

    register_extensions(app)
    register_core_routes(app)
    register_blueprints(app)
    register_error_handlers(app)
    register_jwt_callbacks(app)
    register_shell_context(app)
    register_commands(app)

    with app.app_context():
        from app import models  # noqa: F401

    return app


def register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    init_swagger(app)


def register_core_routes(app):
    @app.get("/")
    @swag_from(
        {
            "tags": ["Core"],
            "summary": "Get API root metadata",
            "security": [],
            "responses": {200: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
        }
    )
    def root():
        return api_response(
            True,
            "Coaching Management API",
            {
                "base_url": "/api/v1",
                "health": "/api/v1/health",
                "wakeup": "/api/v1/wakeup",
            },
            200,
        )

    @app.get("/api/v1")
    @swag_from(
        {
            "tags": ["Core"],
            "summary": "Get API v1 root metadata",
            "security": [],
            "responses": {200: {"schema": {"$ref": "#/definitions/StandardResponse"}}},
        }
    )
    def api_root():
        return api_response(
            True,
            "API is reachable",
            {"health": "/api/v1/health", "wakeup": "/api/v1/wakeup"},
            200,
        )


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def app_error_handler(error):
        return api_response(False, error.message, {}, error.status_code)

    @app.errorhandler(JWTExtendedException)
    def jwt_exception_handler(error):
        return api_response(False, str(error), {}, 401)

    @app.errorhandler(SQLAlchemyError)
    def db_exception_handler(_error):
        db.session.rollback()
        return api_response(False, "Database operation failed", {}, 500)

    @app.errorhandler(404)
    def not_found(_error):
        return api_response(
            False,
            "Resource not found. Use /api/v1 routes.",
            {"health": "/api/v1/health"},
            404,
        )

    @app.errorhandler(500)
    def internal_error(_error):
        return api_response(False, "Internal server error", {}, 500)


def register_jwt_callbacks(app):
    @jwt.unauthorized_loader
    def unauthorized_callback(error_message):
        return api_response(False, error_message, {}, 401)

    @jwt.invalid_token_loader
    def invalid_token_callback(error_message):
        return api_response(False, error_message, {}, 422)

    @jwt.expired_token_loader
    def expired_token_callback(_jwt_header, _jwt_payload):
        return api_response(False, "Token has expired", {}, 401)


def register_shell_context(app):
    @app.shell_context_processor
    def shell_context():
        from app.models import (
            Attendance,
            Batch,
            FeePayment,
            BatchResource,
            Salary,
            Student,
            Teacher,
            Test,
            TestResult,
            User,
            Quiz,
            QuizQuestion,
            QuizSubmission,
            QuizAnswer,
        )

        return {
            "db": db,
            "User": User,
            "Student": Student,
            "Batch": Batch,
            "Teacher": Teacher,
            "Attendance": Attendance,
            "FeePayment": FeePayment,
            "BatchResource": BatchResource,
            "Salary": Salary,
            "Test": Test,
            "TestResult": TestResult,
            "Quiz": Quiz,
            "QuizQuestion": QuizQuestion,
            "QuizSubmission": QuizSubmission,
            "QuizAnswer": QuizAnswer,
        }
