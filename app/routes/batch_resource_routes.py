from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.batch_resource_controller import (
    create_batch_resource_controller,
    delete_batch_resource_controller,
    list_batch_resources_controller,
    update_batch_resource_controller,
)
from app.utils.auth import roles_required

batch_resources_bp = Blueprint("batch_resources", __name__)


@batch_resources_bp.get("/batches/<int:batch_id>/resources")
@jwt_required()
@roles_required("student", "coach", "admin", "director", "manager")
def list_batch_resources(batch_id):
    return list_batch_resources_controller(batch_id)


@batch_resources_bp.post("/batches/<int:batch_id>/resources")
@jwt_required()
@roles_required("coach", "admin", "director", "manager")
def create_batch_resource(batch_id):
    return create_batch_resource_controller(batch_id)


@batch_resources_bp.put("/batch-resources/<int:resource_id>")
@jwt_required()
@roles_required("coach", "admin", "director", "manager")
def update_batch_resource(resource_id):
    return update_batch_resource_controller(resource_id)


@batch_resources_bp.delete("/batch-resources/<int:resource_id>")
@jwt_required()
@roles_required("coach", "admin", "director", "manager")
def delete_batch_resource(resource_id):
    return delete_batch_resource_controller(resource_id)
