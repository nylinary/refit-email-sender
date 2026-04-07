import hashlib
import hmac
import logging
import time

from fastapi import APIRouter, HTTPException, Request
from pydantic import ValidationError

from app.config import WEBFLOW_WEBHOOK_SECRET
from app.email_service import send_order_confirmation
from app.schemas import WebflowOrderPayload

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_AGE_MS = 300_000  # 5 minutes


def _verify_webflow_signature(secret: str, timestamp: str, raw_body: bytes, signature: str) -> None:
    ts = int(timestamp)
    if (time.time() * 1000) - ts > MAX_AGE_MS:
        raise ValueError("Request is older than 5 minutes")

    data = f"{ts}:{raw_body.decode()}"
    expected = hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise ValueError("Invalid signature")


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/webhooks/webflow-order")
async def webflow_order(request: Request):
    logger.info("Incoming request headers: %s", dict(request.headers))

    timestamp = request.headers.get("x-webflow-timestamp", "")
    signature = request.headers.get("x-webflow-signature", "")
    raw_body = await request.body()

    logger.info("Raw body (%d bytes): %s", len(raw_body), raw_body[:2000])
    logger.info("x-webflow-timestamp=%s x-webflow-signature=%s", timestamp, signature)

    try:
        _verify_webflow_signature(WEBFLOW_WEBHOOK_SECRET, timestamp, raw_body, signature)
    except Exception as exc:
        logger.warning("Signature verification failed: %s", exc)
        raise HTTPException(status_code=403, detail="forbidden")

    logger.info("Webhook received — signature valid")

    payload = await request.json()
    logger.info("Parsed JSON payload keys: %s", list(payload.keys()))
    logger.info("Full payload: %s", payload)

    if not payload.get("customer_email"):
        logger.warning("Missing customer_email in payload: %s", payload)
        raise HTTPException(status_code=400, detail="customer_email is required")

    try:
        order = WebflowOrderPayload(**payload)
    except ValidationError as exc:
        logger.warning("Pydantic validation failed: %s | payload: %s", exc, payload)
        raise HTTPException(status_code=400, detail="invalid payload")

    logger.info(
        "Parsed order: customer=%s email=%s items_count=%s",
        order.customer_name,
        order.customer_email,
        order.order_items_count,
    )

    try:
        send_order_confirmation(order)
    except Exception as exc:
        logger.error("Email send failed: %s", exc)
        raise HTTPException(status_code=500, detail="failed to send email")

    return {"status": "ok", "message": "Email sent"}
