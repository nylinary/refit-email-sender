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


def _build_shop_plain(order: WebflowOrderPayload) -> str:
    name = order.customer_name or "—"
    email = order.customer_email
    phone = order.customer_phone or "—"
    items = order.order_items_text or "Состав заказа не передан"
    total = order.order_total or "—"
    delivery = order.delivery_method or "—"
    comment = order.customer_comment or "—"
    source = order.order_source_page or "—"
    created = order.order_created_at or "—"

    return "\n".join([
        "Новый заказ на сайте!",
        "",
        f"Клиент: {name}",
        f"Email: {email}",
        f"Телефон: {phone}",
        f"Комментарий: {comment}",
        "",
        "Состав заказа:",
        items,
        "",
        f"Итого: {total} ₽",
        f"Способ доставки: {delivery}",
        f"Страница заказа: {source}",
        f"Дата: {created}",
    ])


def _build_shop_html(order: WebflowOrderPayload) -> str:
    name = order.customer_name or "—"
    email = order.customer_email
    phone = order.customer_phone or "—"
    items = (order.order_items_text or "Состав заказа не передан").replace("\n", "<br>")
    total = order.order_total or "—"
    delivery = order.delivery_method or "—"
    comment = order.customer_comment or "—"
    source = order.order_source_page or "—"
    created = order.order_created_at or "—"

    return f"""\
<html>
<body style="font-family: sans-serif; color: #333; line-height: 1.6;">
  <h2>Новый заказ на сайте!</h2>

  <h3>Клиент</h3>
  <p>Имя: {name}<br>Email: {email}<br>Телефон: {phone}<br>Комментарий: {comment}</p>

  <h3>Состав заказа</h3>
  <p>{items}</p>

  <h3>Итого: {total} ₽</h3>
  <p>Способ доставки: {delivery}</p>

  <hr>
  <p>Страница заказа: {source}<br>Дата: {created}</p>
</body>
</html>"""


def _send_email(subject: str, from_addr: str, to_addr: str, plain: str, html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    logger.info("Connecting to SMTP %s:%s", config.SMTP_HOST, config.SMTP_PORT)

    server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15)
    if config.SMTP_USE_TLS:
        server.starttls()

    try:
        if config.SMTP_USERNAME:
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
        server.sendmail(from_addr, [to_addr], msg.as_string())
        logger.info("Email sent to %s", to_addr)
    finally:
        server.quit()


def send_order_confirmation(order: WebflowOrderPayload) -> None:
    _send_email(
        subject="Ваш заказ принят",
        from_addr=config.MAIL_FROM,
        to_addr=order.customer_email,
        plain=_build_plain(order),
        html=_build_html(order),
    )

    if config.SHOP_EMAIL:
        _send_email(
            subject=f"Новый заказ от {order.customer_name or order.customer_email}",
            from_addr=config.MAIL_FROM,
            to_addr=config.SHOP_EMAIL,
            plain=_build_shop_plain(order),
            html=_build_shop_html(order),
        )
    else:
        logger.warning("SHOP_EMAIL not set — skipping shop notification")
