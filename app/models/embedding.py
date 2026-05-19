import uuid
from tortoise import fields
from app.lib.database import BaseModel


class Embedding(BaseModel):
    id         = fields.IntField(primary_key=True)
    name       = fields.CharField(max_length=255, unique=True, index=True)
    face       = fields.ForeignKeyField("models.Face", related_name="embeddings", on_delete=fields.CASCADE)
    embedding = fields.BinaryField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "embeddings"

    def __str__(self):
        return f"Embedding(id={self.id}, face_id={self.face_id})"