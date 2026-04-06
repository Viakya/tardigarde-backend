from functools import wraps

from flask_jwt_extended import get_jwt, verify_jwt_in_request

from app.core.exceptions import AuthenticationError


def roles_required(*allowed_roles):
    allowed = {role.lower() for role in allowed_roles}

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            role = (claims.get("role") or "").lower()

            if role not in allowed:
                raise AuthenticationError("You do not have permission to access this resource", 403)

            return fn(*args, **kwargs)

        return wrapper

    return decorator
