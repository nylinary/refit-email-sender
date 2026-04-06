import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app import config
from app.schemas import WebflowOrderPayload

logger = logging.getLogger(__name__)


def _build_plain(order: WebflowOrderPayload) -> str:
    name = order.customer_name or "клиент"
    items = order.order_items_text or "Состав заказа не передан"
    total = order.order_total or "—"
    delivery = order.delivery_method or "—"

    lines = [
        f"Здравствуйте, {name}!",
        "",
        "Ваш заказ принят в обработку.",
        "",
        "Состав заказа:",
        items,
        "",
        f"Итого: {total} ₽",
        f"Способ доставки: {delivery}",
        "",
        "Мы свяжемся с вами по телефону или email при необходимости.",
        "",
        "С уважением,",
        config.SHOP_NAME,
    ]

    if config.SHOP_PHONE:
        lines.append(f"Тел.: {config.SHOP_PHONE}")
    if config.SHOP_EMAIL:
        lines.append(f"Email: {config.SHOP_EMAIL}")

    return "\n".join(lines)


def _build_html(order: WebflowOrderPayload) -> str:
    name = order.customer_name or "клиент"
    items = (order.order_items_text or "Состав заказа не передан").replace("\n", "<br>")
    total = order.order_total or "—"
    delivery = order.delivery_method or "—"

    contact_lines = ""
    if config.SHOP_PHONE:
        contact_lines += f"<p>Тел.: {config.SHOP_PHONE}</p>"
    if config.SHOP_EMAIL:
        contact_lines += f"<p>Email: {config.SHOP_EMAIL}</p>"

    return f"""\
<html>
<body style="font-family: sans-serif; color: #333; line-height: 1.6;">
  <h2>Здравствуйте, {name}!</h2>
  <p>Ваш заказ принят в обработку.</p>

  <h3>Состав заказа</h3>
  <p>{items}</p>

  <h3>Итого</h3>
  <p>{total} ₽</p>

  <h3>Способ доставки</h3>
  <p>{delivery}</p>

  <hr>
  <p>Мы свяжемся с вами по телефону или email при необходимости.</p>
  <p>С уважением,<br><strong>{config.SHOP_NAME}</strong></p>
  {contact_lines}
</body>
</html>"""


def send_order_confirmation(order: WebflowOrderPayload) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Ваш заказ принят"
    msg["From"] = config.MAIL_FROM
    msg["To"] = order.customer_email

    msg.attach(MIMEText(_build_plain(order), "plain", "utf-8"))
    msg.attach(MIMEText(_build_html(order), "html", "utf-8"))

    logger.info("Connecting to SMTP %s:%s", config.SMTP_HOST, config.SMTP_PORT)

    if config.SMTP_USE_TLS:
        server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15)
        server.starttls()
    else:
        server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15)

    try:
        if config.SMTP_USERNAME:
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
        server.sendmail(config.MAIL_FROM, [order.customer_email], msg.as_string())
        logger.info("Email sent to %s", order.customer_email)
    finally:
        server.quit()
