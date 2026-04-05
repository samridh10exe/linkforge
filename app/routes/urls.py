from flask import Blueprint, current_app, jsonify, redirect, request

from app.metrics import mark_redirect
from app.services.events import enqueue_click_event
from app.services.urls import (
    create_short_url,
    deactivate_short_code,
    delete_url_by_id,
    get_url_by_id,
    list_urls,
    resolve_short_code,
    serialize_url_resource,
    update_url_by_id,
)
from app.validators import validate_delete_payload, validate_shorten_payload
from app.errors import APIError

urls_bp = Blueprint("urls", __name__)


@urls_bp.post("/shorten")
def shorten():
    payload = validate_shorten_payload()
    url = create_short_url(
        payload["original_url"],
        payload["title"],
        payload["user_id"],
        payload["expires_at"],
        code_length=current_app.config["SHORT_CODE_LENGTH"],
        max_attempts=current_app.config["SHORT_CODE_ATTEMPTS"],
    )
    return jsonify(serialize_url_resource(url)), 201


def _pagination():
    page = request.args.get("page")
    per_page = request.args.get("per_page")
    if page is None or per_page is None:
        return None, None
    try:
        page = int(page)
        per_page = int(per_page)
    except ValueError as exc:
        raise APIError(400, "invalid_pagination", "page and per_page must be integers") from exc
    if page < 1 or per_page < 1:
        raise APIError(400, "invalid_pagination", "page and per_page must be positive")
    return page, per_page


@urls_bp.post("/urls")
def create_url():
    payload = validate_shorten_payload()
    url = create_short_url(
        payload["original_url"],
        payload["title"],
        payload["user_id"],
        payload["expires_at"],
        code_length=current_app.config["SHORT_CODE_LENGTH"],
        max_attempts=current_app.config["SHORT_CODE_ATTEMPTS"],
    )
    return jsonify(serialize_url_resource(url)), 201


@urls_bp.get("/urls")
def get_urls():
    user_id = request.args.get("user_id")
    is_active = request.args.get("is_active")
    if user_id is not None:
        try:
            user_id = int(user_id)
        except ValueError as exc:
            raise APIError(400, "invalid_user_id", "user_id must be an integer") from exc
    if is_active is not None:
        lowered = is_active.strip().lower()
        if lowered not in {"true", "false"}:
            raise APIError(400, "invalid_is_active", "is_active must be true or false")
        is_active = lowered == "true"
    page, per_page = _pagination()
    return jsonify(
        [
            serialize_url_resource(url)
            for url in list_urls(user_id=user_id, is_active=is_active, page=page, per_page=per_page)
        ]
    )


@urls_bp.get("/urls/<int:url_id>")
def get_url(url_id):
    return jsonify(serialize_url_resource(get_url_by_id(url_id)))


@urls_bp.put("/urls/<int:url_id>")
def put_url(url_id):
    from app.validators import parse_json_body

    return jsonify(serialize_url_resource(update_url_by_id(url_id, parse_json_body())))


@urls_bp.delete("/urls/<int:url_id>")
def remove_url(url_id):
    delete_url_by_id(url_id)
    return "", 204


@urls_bp.delete("/<string:short_code>")
def delete_url(short_code):
    payload = validate_delete_payload()
    deactivate_short_code(short_code, payload["user_id"], payload["reason"])
    return jsonify({"message": "URL deactivated", "reason": payload["reason"]})


@urls_bp.get("/<string:short_code>")
def redirect_short_code(short_code):
    url = resolve_short_code(short_code)
    is_dict = isinstance(url, dict)
    _id = url["id"] if is_dict else url.id
    _user_id = url["user_id"] if is_dict else url.user_id
    _short_code = url["short_code"] if is_dict else url.short_code
    _original_url = url["original_url"] if is_dict else url.original_url
    enqueue_click_event(
        _id,
        _user_id,
        {
            "short_code": _short_code,
            "referrer": request.headers.get("Referer"),
            "user_agent": request.headers.get("User-Agent"),
            "remote_addr": request.headers.get("X-Forwarded-For", request.remote_addr),
        },
    )
    mark_redirect()
    response = redirect(_original_url, code=302)
    response.headers["X-Cache"] = "HIT" if is_dict else "MISS"
    return response
