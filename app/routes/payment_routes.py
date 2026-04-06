from flask import Blueprint
from flasgger import swag_from
from flask_jwt_extended import jwt_required

from app.controllers.payment_controller import (
    create_razorpay_order_controller,
    verify_razorpay_payment_controller,
)
from app.utils.auth import roles_required

payments_bp = Blueprint("payments", __name__)


@payments_bp.post("/payments/razorpay/order")
@jwt_required()
@roles_required("student", "parent", "manager", "director")
@swag_from(
    {
        "tags": ["Payments"],
        "summary": "Create Razorpay order for a fee payment",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {
                "in": "body",
                "name": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "integer"},
                        "amount": {"type": "number"},
                    },
                },
            }
        ],
        "responses": {201: {"description": "Order created"}},
    }
)
def create_order_route():
    return create_razorpay_order_controller()


@payments_bp.post("/payments/razorpay/verify")
@jwt_required()
@roles_required("student", "parent", "manager", "director")
@swag_from(
    {
        "tags": ["Payments"],
        "summary": "Verify Razorpay payment and create fee record",
        "security": [{"BearerAuth": []}],
        "parameters": [
            {
                "in": "body",
                "name": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "razorpay_order_id": {"type": "string"},
                        "razorpay_payment_id": {"type": "string"},
                        "razorpay_signature": {"type": "string"},
                        "student_id": {"type": "integer"},
                        "amount": {"type": "number"},
                    },
                },
            }
        ],
        "responses": {200: {"description": "Payment verified"}},
    }
)
def verify_payment_route():
    return verify_razorpay_payment_controller()
