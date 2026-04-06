import logging

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from app.email_service import send_order_confirmation
from app.schemas import WebflowOrderPayload

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/webhooks/webflow-order")
def webflow_order(payload: dict):
    logger.info("Webhook received")

    if not payload.get("customer_email"):
        raise HTTPException(status_code=400, detail="customer_email is required")

    try:
        order = WebflowOrderPayload(**payload)
    except ValidationError as exc:
        logger.warning("Invalid payload: %s", exc)
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
