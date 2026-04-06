from app.core.exceptions import ValidationError


def _normalize_string(value, field_name, max_len=None, required=False):
    if value is None:
        if required:
            raise ValidationError(f"{field_name} is required")
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    value = value.strip()
    if required and not value:
        raise ValidationError(f"{field_name} is required")
    if max_len and len(value) > max_len:
        raise ValidationError(f"{field_name} is too long")
    return value


def _normalize_url(value):
    url = _normalize_string(value, "url", max_len=500, required=True)
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValidationError("url must start with http:// or https://")
    return url


def _normalize_resource_type(value):
    resource_type = _normalize_string(value, "resource_type", max_len=40) or "link"
    return resource_type.lower()


def validate_create_batch_resource_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    title = _normalize_string(payload.get("title"), "title", max_len=180, required=True)
    description = _normalize_string(payload.get("description"), "description", max_len=2000)
    url = _normalize_url(payload.get("url"))
    resource_type = _normalize_resource_type(payload.get("resource_type"))
    visible_to_students = payload.get("visible_to_students", True)
    if not isinstance(visible_to_students, bool):
        raise ValidationError("visible_to_students must be a boolean")

    return {
        "title": title,
        "description": description,
        "url": url,
        "resource_type": resource_type,
        "visible_to_students": visible_to_students,
    }


def validate_update_batch_resource_payload(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Invalid request payload")

    result = {}

    if "title" in payload:
        result["title"] = _normalize_string(payload.get("title"), "title", max_len=180, required=True)
    if "description" in payload:
        result["description"] = _normalize_string(payload.get("description"), "description", max_len=2000)
    if "url" in payload:
        result["url"] = _normalize_url(payload.get("url"))
    if "resource_type" in payload:
        result["resource_type"] = _normalize_resource_type(payload.get("resource_type"))
    if "visible_to_students" in payload:
        visible = payload.get("visible_to_students")
        if not isinstance(visible, bool):
            raise ValidationError("visible_to_students must be a boolean")
        result["visible_to_students"] = visible

    if not result:
        raise ValidationError("At least one field is required for update")

    return result
