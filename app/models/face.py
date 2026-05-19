from tortoise import fields
from app.lib.database import BaseModel


class Face(BaseModel):
    id      = fields.CharField(max_length=255, primary_key=True)
    user    = fields.ForeignKeyField("models.User", related_name="faces", on_delete=fields.CASCADE)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "faces"

    def __str__(self):
        return f"Face(id={self.id}, user_id={self.user_id})"
