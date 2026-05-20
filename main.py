
from app.lib.suppress_stderr import SuppressStderr
from dotenv import load_dotenv
load_dotenv()

with SuppressStderr():
    from app.lib.database import init_db,close_db
    from fastapi import FastAPI, logger
    from app.lib.store import EmbeddingStore
    import app.routes as routes
    from app.routes import create_router
    from contextlib import asynccontextmanager
    from deepface import DeepFace
    from app.lib.logging import setup_logger  # kalau kamu pisah file


    logger = setup_logger("face-api")
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await init_db(logger)
        logger.info("Preloading DeepFace models...")

        # preload model
        DeepFace.build_model("ArcFace")
        DeepFace.build_model("retinaface", "face_detector")
        # DeepFace.build_model("Fasnet", "spoofing")

        # DeepFace.modeling.cached_models.clear();
        logger.info("DeepFace ready")

        logger.info("Loading embeddings...")
        store = EmbeddingStore(logger=logger)
        routes.init(store)
        app.include_router(create_router())

        yield  # yield your app, dont delete this
        await close_db()
        logger.info("Shutting down, bye...")

    app   = FastAPI(lifespan=lifespan)



# ── Print route list ──────────────────────────────────────────
# METHOD_COLORS = {
#     "GET":    "\033[92m",   # green
#     "POST":   "\033[94m",   # blue
#     "PUT":    "\033[93m",   # yellow
#     "PATCH":  "\033[93m",   # yellow
#     "DELETE": "\033[91m",   # red
# }
# RESET = "\033[0m"
# DIM   = "\033[2m"

# routes = [
#     (sorted(r.methods), r.path)
#     for r in app.routes
#     if hasattr(r, "methods") and r.methods
# ]
# routes.sort(key=lambda x: x[1])  # sort by path

# pad = max(len(p) for _, p in routes)

# print(f"\n{DIM}{'─' * (pad + 20)}{RESET}")
# for methods, path in routes:
#     for method in methods:
#         color = METHOD_COLORS.get(method, "\033[0m")
#         print(f"  {color}{method:<7}{RESET}  {path}")
# print(f"{DIM}{'─' * (pad + 20)}{RESET}\n")
# ─────────────────────────────────────────────────────────────
