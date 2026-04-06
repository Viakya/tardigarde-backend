from app.services.health_service import get_health_payload
from app.utils.response import api_response


def health_check():
    payload = get_health_payload()
    return api_response(True, "Service is healthy", payload, 200)


def wakeup_ping():
    return api_response(True, "Service is awake", {"status": "awake"}, 200)
