import uuid
from tortoise import fields
from app.lib.database import BaseModel


class User(BaseModel):
    id       = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    email    = fields.CharField(max_length=255, unique=True, index=True)
    password = fields.TextField()
    api_key  = fields.CharField(max_length=255, unique=True, index=True)

    class Meta:
        table = "users"

    def __str__(self):
        return f"User(id={self.id}, email={self.email})"