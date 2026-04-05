from peewee import BooleanField, CharField, Check, DateTimeField, ForeignKeyField, IntegerField, TextField

from app.database import BaseModel
from app.models.user import User


class Url(BaseModel):
    user = ForeignKeyField(User, backref="urls", column_name="user_id", on_delete="RESTRICT")
    short_code = CharField(
        max_length=6,
        unique=True,
        constraints=[Check("short_code ~ '^[A-Za-z0-9]{6}$'")],
    )
    original_url = TextField(constraints=[Check("char_length(btrim(original_url)) > 0")])
    title = CharField(constraints=[Check("char_length(btrim(title)) > 0")])
    is_active = BooleanField(default=True)
    click_count = IntegerField(default=0)
    expires_at = DateTimeField(null=True)
    created_at = DateTimeField()
    updated_at = DateTimeField()

    class Meta:
        table_name = "urls"
        indexes = (
            (("user", "original_url", "is_active"), False),
            (("user", "created_at"), False),
            (("is_active", "expires_at"), False),
        )
