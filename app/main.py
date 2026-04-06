import logging

from fastapi import FastAPI

from app.routes.webhook import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(title="Refit Email Sender")

app.include_router(router)
