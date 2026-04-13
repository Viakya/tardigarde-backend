from app.routes.auth_routes import auth_bp
from app.routes.ai_routes import ai_bp
from app.routes.attendance_routes import attendance_bp
from app.routes.admin_routes import admin_bp
from app.routes.batch_routes import batches_bp
from app.routes.batch_teacher_routes import batch_teachers_bp
from app.routes.fee_routes import fees_bp
from app.routes.health_routes import health_bp
from app.routes.parent_routes import parents_bp
from app.routes.reporting_routes import reports_bp
from app.routes.salary_routes import salary_bp
from app.routes.student_routes import students_bp
from app.routes.test_routes import tests_bp
from app.routes.teacher_routes import teachers_bp
from app.routes.teacher_dashboard_routes import teacher_dashboard_bp
from app.routes.payment_routes import payments_bp
from app.routes.batch_resource_routes import batch_resources_bp
from app.routes.quiz_routes import quizzes_bp
from app.routes.export_routes import exports_bp
from app.routes.calendar_routes import calendar_bp


def register_blueprints(app):
    app.register_blueprint(health_bp, url_prefix="/api/v1")
    app.register_blueprint(admin_bp, url_prefix="/api/v1")
    app.register_blueprint(auth_bp, url_prefix="/api/v1")
    app.register_blueprint(ai_bp, url_prefix="/api/v1")
    app.register_blueprint(attendance_bp, url_prefix="/api/v1")
    app.register_blueprint(fees_bp, url_prefix="/api/v1")
    app.register_blueprint(parents_bp, url_prefix="/api/v1")
    app.register_blueprint(reports_bp, url_prefix="/api/v1")
    app.register_blueprint(salary_bp, url_prefix="/api/v1")
    app.register_blueprint(tests_bp, url_prefix="/api/v1")
    app.register_blueprint(batches_bp, url_prefix="/api/v1")
    app.register_blueprint(batch_teachers_bp, url_prefix="/api/v1")
    app.register_blueprint(students_bp, url_prefix="/api/v1")
    app.register_blueprint(teachers_bp, url_prefix="/api/v1")
    app.register_blueprint(teacher_dashboard_bp, url_prefix="/api/v1")
    app.register_blueprint(payments_bp, url_prefix="/api/v1")
    app.register_blueprint(batch_resources_bp, url_prefix="/api/v1")
    app.register_blueprint(quizzes_bp, url_prefix="/api/v1")
    app.register_blueprint(exports_bp, url_prefix="/api/v1")
    app.register_blueprint(calendar_bp, url_prefix="/api/v1")
