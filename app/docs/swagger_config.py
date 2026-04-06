from flasgger import Swagger


SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "Coaching Management System API",
        "description": "Production-ready Flask API with JWT and RBAC",
        "version": "1.0.0",
    },
    "basePath": "/",
    "schemes": ["http", "https"],
    "securityDefinitions": {
        "BearerAuth": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Bearer token. Example: Bearer <access_token>",
        }
    },
    "definitions": {
        "StandardResponse": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "data": {"type": "object"},
            },
        },
        "AuthRegisterRequest": {
            "type": "object",
            "required": ["full_name", "email", "password"],
            "properties": {
                "full_name": {"type": "string", "example": "John Doe"},
                "email": {"type": "string", "example": "john@example.com"},
                "password": {"type": "string", "example": "StrongPass@123"},
                "role": {
                    "type": "string",
                    "enum": ["admin", "director", "manager", "coach", "student", "parent"],
                    "example": "student",
                },
            },
        },
        "AuthLoginRequest": {
            "type": "object",
            "required": ["email", "password"],
            "properties": {
                "email": {"type": "string", "example": "john@example.com"},
                "password": {"type": "string", "example": "StrongPass@123"},
            },
        },
        "StudentRequest": {
            "type": "object",
            "required": ["user_id"],
            "properties": {
                "user_id": {"type": "integer", "example": 1},
                "batch_id": {"type": "integer", "example": 2},
                "phone_number": {"type": "string", "example": "9876543210"},
                "address": {"type": "string", "example": "City Center"},
                "date_of_birth": {"type": "string", "format": "date", "example": "2005-01-20"},
                "enrollment_date": {"type": "string", "format": "date", "example": "2026-03-01"},
                "is_active": {"type": "boolean", "example": True},
                "parent_user_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "example": [7, 8],
                },
            },
        },
        "BatchRequest": {
            "type": "object",
            "required": ["batch_name", "year"],
            "properties": {
                "batch_name": {"type": "string", "example": "JEE Evening"},
                "year": {"type": "integer", "example": 2026},
                "start_date": {"type": "string", "format": "date", "example": "2026-03-01"},
                "end_date": {"type": "string", "format": "date", "example": "2026-12-31"},
                "is_active": {"type": "boolean", "example": True},
            },
        },
        "TeacherRequest": {
            "type": "object",
            "required": ["user_id"],
            "properties": {
                "user_id": {"type": "integer", "example": 4},
                "specialization": {"type": "string", "example": "Physics"},
                "phone_number": {"type": "string", "example": "9876543210"},
                "hire_date": {"type": "string", "format": "date", "example": "2026-02-25"},
                "is_active": {"type": "boolean", "example": True},
            },
        },
        "BatchTeacherAssignRequest": {
            "type": "object",
            "required": ["teacher_id"],
            "properties": {
                "teacher_id": {"type": "integer", "example": 1},
            },
        },
        "AttendanceRequest": {
            "type": "object",
            "required": ["student_id", "batch_id", "status"],
            "properties": {
                "student_id": {"type": "integer", "example": 10},
                "batch_id": {"type": "integer", "example": 2},
                "attendance_date": {
                    "type": "string",
                    "format": "date",
                    "example": "2026-02-25",
                },
                "status": {
                    "type": "string",
                    "enum": ["present", "absent", "late"],
                    "example": "present",
                },
                "remarks": {"type": "string", "example": "Late due to traffic"},
                "is_active": {"type": "boolean", "example": True},
            },
        },
        "AttendanceUpdateRequest": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["present", "absent", "late"],
                    "example": "absent",
                },
                "remarks": {"type": "string", "example": "Sick leave"},
                "is_active": {"type": "boolean", "example": True},
            },
        },
        "StudentFeeRequest": {
            "type": "object",
            "required": ["student_id", "batch_id", "total_fee"],
            "properties": {
                "student_id": {"type": "integer", "example": 1},
                "batch_id": {"type": "integer", "example": 2},
                "total_fee": {"type": "number", "example": 50000},
                "discount_amount": {"type": "number", "example": 5000},
                "due_date": {"type": "string", "format": "date", "example": "2026-04-10"},
                "is_active": {"type": "boolean", "example": True},
            },
        },
        "FeePaymentRequest": {
            "type": "object",
            "required": ["student_fee_id", "amount"],
            "properties": {
                "student_fee_id": {"type": "integer", "example": 1},
                "amount": {"type": "number", "example": 10000},
                "payment_date": {"type": "string", "format": "date", "example": "2026-03-01"},
                "payment_method": {
                    "type": "string",
                    "enum": ["cash", "upi", "card", "bank_transfer"],
                    "example": "upi",
                },
                "reference_no": {"type": "string", "example": "TXN-12345"},
                "remarks": {"type": "string", "example": "1st installment"},
            },
        },
        "SalaryCreateRequest": {
            "type": "object",
            "required": ["teacher_id", "salary_month", "amount"],
            "properties": {
                "teacher_id": {"type": "integer", "example": 1},
                "salary_month": {"type": "string", "example": "2026-02"},
                "amount": {"type": "number", "example": 30000},
                "remarks": {"type": "string", "example": "Monthly salary"},
            },
        },
        "SalaryUpdateRequest": {
            "type": "object",
            "properties": {
                "paid_amount": {"type": "number", "example": 30000},
                "status": {
                    "type": "string",
                    "enum": ["pending", "partial", "paid"],
                    "example": "paid",
                },
                "payment_date": {"type": "string", "format": "date", "example": "2026-02-28"},
                "remarks": {"type": "string", "example": "Paid via bank transfer"},
                "is_active": {"type": "boolean", "example": True},
            },
        },
        "TestCreateRequest": {
            "type": "object",
            "required": ["batch_id", "title", "max_marks", "test_date"],
            "properties": {
                "batch_id": {"type": "integer", "example": 2},
                "title": {"type": "string", "example": "Weekly Physics Test"},
                "subject": {"type": "string", "example": "Physics"},
                "max_marks": {"type": "number", "example": 100},
                "test_date": {"type": "string", "format": "date", "example": "2026-03-05"},
            },
        },
        "TestResultCreateRequest": {
            "type": "object",
            "required": ["test_id", "student_id", "marks_obtained"],
            "properties": {
                "test_id": {"type": "integer", "example": 1},
                "student_id": {"type": "integer", "example": 4},
                "marks_obtained": {"type": "number", "example": 76},
                "remarks": {"type": "string", "example": "Good progress"},
            },
        },
    },
}

SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
}


def init_swagger(app):
    Swagger(app, template=SWAGGER_TEMPLATE, config=SWAGGER_CONFIG)
