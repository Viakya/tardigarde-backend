from google.auth.transport import requests
from google.oauth2 import id_token

from app.core.exceptions import AuthenticationError, ValidationError


def verify_google_token(credential, audience):
    if not audience:
        raise ValidationError("Google login not configured")

    if not credential:
        raise AuthenticationError("Missing Google credential")

    try:
        id_info = id_token.verify_oauth2_token(credential, requests.Request(), audience)
    except ValueError as exc:
        raise AuthenticationError("Invalid Google token") from exc

    if not id_info.get("email"):
        raise AuthenticationError("Google account email missing")

    if not id_info.get("email_verified"):
        raise AuthenticationError("Google account email not verified")

    return id_info
