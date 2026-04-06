from flask import Blueprint
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.controllers.fee_controller import (
    create_fee_payment_controller,
    delete_fee_payment_controller,
    get_fee_payment_controller,
    list_fee_payments_controller,
    update_fee_payment_controller,
)

fees_bp = Blueprint("fees", __name__)


@fees_bp.route("/fee-payments", methods=["POST"])
@jwt_required()
def create_fee_payment():
    current_user_id = get_jwt_identity()
    return create_fee_payment_controller(current_user_id)


@fees_bp.route("/fee-payments", methods=["GET"])
@jwt_required()
def list_fee_payments():
    return list_fee_payments_controller()


@fees_bp.route("/fee-payments/<int:payment_id>", methods=["GET"])
@jwt_required()
def get_fee_payment(payment_id):
    return get_fee_payment_controller(payment_id)


@fees_bp.route("/fee-payments/<int:payment_id>", methods=["DELETE"])
@jwt_required()
def delete_fee_payment(payment_id):
    return delete_fee_payment_controller(payment_id)


@fees_bp.route("/fee-payments/<int:payment_id>", methods=["PUT"])
@jwt_required()
def update_fee_payment(payment_id):
    return update_fee_payment_controller(payment_id)
