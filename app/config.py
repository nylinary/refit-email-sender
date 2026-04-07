import os

from dotenv import load_dotenv

load_dotenv()


def _get(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


SMTP_HOST: str = _get("SMTP_HOST", "localhost")
SMTP_PORT: int = int(_get("SMTP_PORT", "587"))
SMTP_USERNAME: str = _get("SMTP_USERNAME")
SMTP_PASSWORD: str = _get("SMTP_PASSWORD")
SMTP_USE_TLS: bool = _get("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")

MAIL_FROM: str = _get("MAIL_FROM")

SHOP_NAME: str = _get("SHOP_NAME", "Магазин")
SHOP_PHONE: str = _get("SHOP_PHONE")
SHOP_EMAIL: str = _get("SHOP_EMAIL")

WEBHOOK_SECRET: str = _get("WEBHOOK_SECRET")
