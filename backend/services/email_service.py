import logging
import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


async def send_email(to_address: str, subject: str, html_body: str, raise_on_error: bool = False) -> bool:
    if not settings.BREVO_API_KEY:
        msg = "BREVO_API_KEY is not configured"
        logger.warning(msg)
        if raise_on_error:
            raise ValueError(msg)
        return False

    if not settings.EMAIL_FROM_ADDRESS:
        msg = "EMAIL_FROM_ADDRESS is not configured"
        logger.warning(msg)
        if raise_on_error:
            raise ValueError(msg)
        return False

    payload = {
        "sender": {
            "name": settings.EMAIL_FROM_NAME,
            "email": settings.EMAIL_FROM_ADDRESS,
        },
        "to": [{"email": to_address}],
        "subject": subject,
        "htmlContent": html_body,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                BREVO_API_URL,
                headers={
                    "api-key": settings.BREVO_API_KEY,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
        logger.info(f"Email sent to {to_address}: {subject}")
        return True
    except httpx.HTTPStatusError as e:
        error = f"Brevo API error {e.response.status_code}: {e.response.text}"
        logger.error(f"Email send failed to {to_address}: {error}")
        if raise_on_error:
            raise ValueError(error)
        return False
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