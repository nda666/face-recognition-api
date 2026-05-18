
from core.suppress_stderr import SuppressStderr
from dotenv import load_dotenv
load_dotenv()

with SuppressStderr():
    from fastapi import FastAPI, logger
    from core.store import EmbeddingStore
    import web
    from web import create_router
    from contextlib import asynccontextmanager
    from deepface import DeepFace
    from core.logging import setup_logger  # kalau kamu pisah file


    logger = setup_logger("face-api")
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Preloading DeepFace models...")

        # preload model
        DeepFace.build_model("ArcFace")
        DeepFace.build_model("opencv", "face_detector")
        DeepFace.build_model("Fasnet", "spoofing")

        # DeepFace.modeling.cached_models.clear();
        logger.info("DeepFace ready")

        yield  # yield your app, dont delete this

        logger.info("Shutting down, bye...")

    app   = FastAPI(lifespan=lifespan)
    store = EmbeddingStore(logger=logger)


    web.init(store)
    app.include_router(create_router())


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
