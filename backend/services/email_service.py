import logging
import ssl
import certifi
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend.config import settings

logger = logging.getLogger(__name__)


async def send_email(to_address: str, subject: str, html_body: str, raise_on_error: bool = False) -> bool:
    if not settings.GMAIL_USER or not settings.GMAIL_APP_PASSWORD:
        msg = "Gmail not configured: GMAIL_USER or GMAIL_APP_PASSWORD is missing"
        logger.warning(msg)
        if raise_on_error:
            raise ValueError(msg)
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.GMAIL_USER
    message["To"] = to_address
    message.attach(MIMEText(html_body, "html", "utf-8"))

    ssl_ctx = ssl.create_default_context(cafile=certifi.where())

    try:
        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            tls_context=ssl_ctx,
            username=settings.GMAIL_USER,
            password=settings.GMAIL_APP_PASSWORD,
        )
        logger.info(f"Email sent to {to_address}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Email send failed to {to_address}: {e}")
        if raise_on_error:
            raise
        return False


def build_notification_html(username: str, role: str, summary: str, date_str: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
  .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px;
               box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden; }}
  .header {{ background: linear-gradient(135deg, #1a56db, #0e9f6e); padding: 24px;
             color: white; }}
  .header h1 {{ margin: 0; font-size: 22px; }}
  .header p {{ margin: 4px 0 0; opacity: 0.85; font-size: 14px; }}
  .badge {{ display: inline-block; background: rgba(255,255,255,0.25); border-radius: 12px;
            padding: 2px 10px; font-size: 12px; margin-top: 8px; }}
  .body {{ padding: 24px; }}
  .summary {{ white-space: pre-wrap; line-height: 1.7; color: #374151; font-size: 14px; }}
  .footer {{ padding: 16px 24px; background: #f9fafb; border-top: 1px solid #e5e7eb;
             font-size: 12px; color: #9ca3af; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>VN Real Estate Intelligence</h1>
    <p>Daily Market Summary — {date_str}</p>
    <span class="badge">{role} Report</span>
  </div>
  <div class="body">
    <p>Hi <strong>{username}</strong>,</p>
    <div class="summary">{summary}</div>
  </div>
  <div class="footer">
    VN Real Estate Intelligence Platform &bull; Unsubscribe from notifications in your account settings.
  </div>
</div>
</body>
</html>"""
