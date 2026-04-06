from sqlalchemy.exc import IntegrityError

from app.core.exceptions import AuthenticationError, ConflictError, ValidationError
from app.extensions import db
from app.models import User


def create_user(email, full_name, password, role):
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        raise ConflictError("Email already exists")

    user = User(email=email, full_name=full_name, role=role)
    user.set_password(password)

    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("Unable to create user")

    return user


def authenticate_user(email, password):
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise AuthenticationError("Invalid credentials")
    if not user.is_active:
        raise AuthenticationError("User is inactive")
    return user


def authenticate_google_user(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        raise AuthenticationError("No account found for this email")
    if not user.is_active:
        raise AuthenticationError("User is inactive")
    return user


def get_user_by_id(user_id):
    return db.session.get(User, user_id)


def get_users_and_admins_summary():
    total_users = db.session.query(db.func.count(User.id)).scalar() or 0
    total_active_users = (
        db.session.query(db.func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0
    )
    admins = User.query.filter_by(role="admin").order_by(User.created_at.desc()).all()

    return {
        "total_registered_users": total_users,
        "total_active_users": total_active_users,
        "total_admins": len(admins),
        "admins": [admin.to_dict() for admin in admins],
    }


def get_registered_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return [user.to_dict() for user in users]


def update_user(user_id, data):
    user = db.session.get(User, user_id)
    if not user:
        raise ValidationError("User not found", 404)

    # Update allowed fields
    if "full_name" in data:
        user.full_name = data["full_name"]
    if "role" in data:
        user.role = data["role"]
    if "is_active" in data:
        user.is_active = data["is_active"]
    if "password" in data and data["password"]:
        user.set_password(data["password"])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("Unable to update user")

    return user


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise ValidationError("User not found", 404)
    # Soft delete by setting is_active to False
    user.is_active = False

    # Cascade cleanup for linked profiles
    if user.teacher_profile and user.teacher_profile.is_active:
        from app.services.teacher_service import delete_teacher

        delete_teacher(user.teacher_profile.id)
    if user.student_profile and user.student_profile.is_active:
        from app.services.student_service import delete_student

        delete_student(user.student_profile.id)

    db.session.commit()
    return user
