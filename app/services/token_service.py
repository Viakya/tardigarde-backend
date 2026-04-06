from flask_jwt_extended import create_access_token


def generate_access_token(user):
    return create_access_token(
        identity=str(user.id),
        additional_claims={
            "email": user.email,
            "role": user.role,
        },
    )
