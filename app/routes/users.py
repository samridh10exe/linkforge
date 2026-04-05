import csv
import io

from flask import Blueprint, jsonify, request

from app.errors import APIError
from app.models.user import User
from app.services.urls import list_user_urls, serialize_url_resource
from app.services.users import (
    bulk_import_users,
    create_user,
    delete_user,
    get_user_by_id,
    list_users,
    serialize_user,
    update_user,
)
from app.validators import parse_json_body

users_bp = Blueprint("users", __name__)


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


@users_bp.post("/users/bulk")
def bulk_users():
    file = request.files.get("file")
    if file is None:
        raise APIError(400, "missing_file", "file is required")
    reader = csv.DictReader(io.StringIO(file.stream.read().decode("utf-8")))
    count = bulk_import_users(list(reader))
    return jsonify({"count": count}), 201


@users_bp.get("/users")
def get_users():
    page, per_page = _pagination()
    return jsonify([serialize_user(user) for user in list_users(page=page, per_page=per_page)])


@users_bp.get("/users/<int:user_id>")
def get_user(user_id):
    return jsonify(serialize_user(get_user_by_id(user_id)))


@users_bp.post("/users")
def post_user():
    payload = parse_json_body()
    username = payload.get("username")
    email = payload.get("email")
    user = create_user(username, email)
    return jsonify(serialize_user(user)), 201


@users_bp.put("/users/<int:user_id>")
@users_bp.patch("/users/<int:user_id>")
def put_user(user_id):
    payload = parse_json_body()
    user = update_user(user_id, payload)
    return jsonify(serialize_user(user))


@users_bp.delete("/users/<int:user_id>")
def remove_user(user_id):
    delete_user(user_id)
    return "", 204


@users_bp.get("/users/<int:user_id>/urls")
def get_user_urls(user_id):
    return jsonify([serialize_url_resource(url) for url in list_user_urls(user_id)])
