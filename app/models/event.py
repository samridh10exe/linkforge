from peewee import CharField, Check, DateTimeField, ForeignKeyField
from playhouse.postgres_ext import BinaryJSONField

from app.database import BaseModel
from app.models.url import Url
from app.models.user import User


class Event(BaseModel):
    url = ForeignKeyField(Url, backref="events", column_name="url_id", on_delete="RESTRICT")
    user = ForeignKeyField(User, backref="events", column_name="user_id", on_delete="RESTRICT")
    event_type = CharField(
        constraints=[Check("event_type IN ('created', 'updated', 'deleted', 'clicked')")]
    )
    timestamp = DateTimeField()
    details = BinaryJSONField(default=dict)

    class Meta:
        table_name = "events"
        indexes = (
            (("url", "timestamp"), False),
            (("user", "timestamp"), False),
            (("event_type", "timestamp"), False),
        )
