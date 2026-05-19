import os
import logging
from tortoise import Tortoise
from tortoise.models import Model

DB_PATH = os.getenv("DB_PATH", os.path.join(os.getcwd(), "storage", "app.db"))
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

TORTOISE_ORM = {
    "connections": {
        "default": f"sqlite://{DB_PATH}",
    },
    "apps": {
        "models": {
            "models": [
                "app.models.user",
                "app.models.face",
                "app.models.embedding",
            ],
            "migrations": "app.db.migrations",
            "default_connection": "default",
            
        }
    },
}

# BaseModel untuk semua model
class BaseModel(Model):
    class Meta:
        abstract = True

async def init_db(logger=None):
    logger = logger or logging.getLogger(__name__)
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas(safe=True)
    logger.info("Database initialized")

async def close_db(logger=None):
    logger = logger or logging.getLogger(__name__)
    await Tortoise.close_connections()
    logger.info("Database connections closed")