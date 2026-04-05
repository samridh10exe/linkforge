from app.models import Event, Url


def test_delete_deactivates_owned_short_code(client, active_url):
    response = client.delete(
        f"/{active_url.short_code}",
        json={"user_id": active_url.user_id, "reason": "user_requested"},
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload == {"message": "URL deactivated", "reason": "user_requested"}
    assert Url.get_by_id(active_url.id).is_active is False
    assert Event.select().where(Event.event_type == "deleted").count() == 1


def test_delete_rejects_invalid_reason(client, active_url):
    response = client.delete(
        f"/{active_url.short_code}",
        json={"user_id": active_url.user_id, "reason": "bogus"},
    )
    assert response.status_code == 400


def test_delete_rejects_wrong_owner(client, active_url):
    response = client.delete(
        f"/{active_url.short_code}",
        json={"user_id": active_url.user_id + 1, "reason": "user_requested"},
    )
    assert response.status_code == 403


def test_delete_returns_410_when_already_inactive(client, active_url):
    Url.update(is_active=False).where(Url.id == active_url.id).execute()
    response = client.delete(
        f"/{active_url.short_code}",
        json={"user_id": active_url.user_id, "reason": "user_requested"},
    )
    assert response.status_code == 410
