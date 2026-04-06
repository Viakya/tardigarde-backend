from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.quiz_controller import (
    close_quiz_controller,
    create_quiz_controller,
    delete_quiz_controller,
    generate_ai_quiz_controller,
    get_quiz_controller,
    list_quizzes_controller,
    publish_quiz_controller,
    submit_quiz_controller,
    update_quiz_controller,
    update_quiz_questions_controller,
)
from app.utils.auth import roles_required

quizzes_bp = Blueprint("quizzes", __name__)


@quizzes_bp.post("/quizzes/ai-generate")
@jwt_required()
@roles_required("coach", "admin", "director", "manager")
def generate_ai_quiz_route():
    return generate_ai_quiz_controller()


@quizzes_bp.post("/quizzes")
@jwt_required()
@roles_required("coach", "admin", "director", "manager")
def create_quiz_route():
    return create_quiz_controller()


@quizzes_bp.get("/batches/<int:batch_id>/quizzes")
@jwt_required()
@roles_required("coach", "student", "admin", "director", "manager")
def list_quizzes_route(batch_id):
    return list_quizzes_controller(batch_id)


@quizzes_bp.get("/quizzes/<int:quiz_id>")
@jwt_required()
@roles_required("coach", "student", "admin", "director", "manager")
def get_quiz_route(quiz_id):
    return get_quiz_controller(quiz_id)


@quizzes_bp.put("/quizzes/<int:quiz_id>")
@jwt_required()
@roles_required("coach", "admin", "director", "manager")
def update_quiz_route(quiz_id):
    return update_quiz_controller(quiz_id)


@quizzes_bp.put("/quizzes/<int:quiz_id>/questions")
@jwt_required()
@roles_required("coach", "admin", "director", "manager")
def update_quiz_questions_route(quiz_id):
    return update_quiz_questions_controller(quiz_id)


@quizzes_bp.post("/quizzes/<int:quiz_id>/publish")
@jwt_required()
@roles_required("coach", "admin", "director", "manager")
def publish_quiz_route(quiz_id):
    return publish_quiz_controller(quiz_id)


@quizzes_bp.post("/quizzes/<int:quiz_id>/close")
@jwt_required()
@roles_required("coach", "admin", "director", "manager")
def close_quiz_route(quiz_id):
    return close_quiz_controller(quiz_id)


@quizzes_bp.delete("/quizzes/<int:quiz_id>")
@jwt_required()
@roles_required("coach", "admin", "director", "manager")
def delete_quiz_route(quiz_id):
    return delete_quiz_controller(quiz_id)


@quizzes_bp.post("/quizzes/<int:quiz_id>/submit")
@jwt_required()
@roles_required("student")
def submit_quiz_route(quiz_id):
    return submit_quiz_controller(quiz_id)
