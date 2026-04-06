from flask import jsonify


def api_response(success, message, data=None, status_code=200):
    payload = {
        "success": success,
        "message": message,
        "data": data if data is not None else {},
    }
    return jsonify(payload), status_code
