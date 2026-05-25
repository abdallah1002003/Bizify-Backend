import logging
import smtplib
import time
from email.message import EmailMessage
from typing import Literal

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

EmailProvider = Literal["resend", "smtp"]

# Transient SMTP failures worth retrying. Auth/recipient errors are not.
_TRANSIENT_SMTP_EXCEPTIONS = (
    smtplib.SMTPConnectError,
    smtplib.SMTPServerDisconnected,
    smtplib.SMTPHeloError,
    TimeoutError,
    ConnectionError,
)


class EmailDeliveryError(RuntimeError):
    """Raised when an outbound email could not be delivered."""


def configured_provider() -> EmailProvider:
    """Return which provider `send_email` will use given the current config."""
    if settings.RESEND_API_KEY:
        return "resend"
    return "smtp"


def validate_email_config() -> tuple[bool, str]:
    """
    Check the email config at startup. Returns (ok, message).
    Called from main.py to fail loudly when the deployment is misconfigured.
    """
    provider = configured_provider()

    if provider == "resend":
        if not settings.EMAILS_FROM_EMAIL:
            return False, (
                "RESEND_API_KEY is set but EMAILS_FROM_EMAIL is not. "
                "The default 'onboarding@resend.dev' only delivers to the Resend "
                "account owner's address — production users won't receive emails. "
                "Set EMAILS_FROM_EMAIL to an address on a domain verified in Resend."
            )
        return True, f"Resend configured (from: {settings.EMAILS_FROM_EMAIL})."

    # SMTP path
    missing = [
        name for name, value in [
            ("SMTP_HOST", settings.SMTP_HOST),
            ("SMTP_USER", settings.SMTP_USER),
            ("SMTP_PASSWORD", settings.SMTP_PASSWORD),
        ] if not value
    ]
    if missing:
        return False, (
            f"No email provider configured. RESEND_API_KEY is unset and SMTP is "
            f"missing: {', '.join(missing)}. Configure Resend or SMTP."
        )
    return True, f"SMTP configured ({settings.SMTP_HOST}:{settings.SMTP_PORT})."


def send_email(
    email_to: str,
    subject: str,
    html_content: str,
) -> None:
    """Send an email via Resend API (preferred) or SMTP (fallback)."""
    if configured_provider() == "resend":
        _send_via_resend(email_to, subject, html_content)
        return

    _send_via_smtp(email_to, subject, html_content)


def _send_via_resend(email_to: str, subject: str, html_content: str) -> None:
    """Send email using the Resend API. Retries once on transient network failure."""
    from_address = settings.EMAILS_FROM_EMAIL or "Bizify <onboarding@resend.dev>"
    payload = {
        "from": from_address,
        "to": [email_to],
        "subject": subject,
        "html": html_content,
    }
    headers = {
        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    last_exc: Exception | None = None
    for attempt in (1, 2):
        try:
            with httpx.Client(timeout=15) as client:
                response = client.post(
                    "https://api.resend.com/emails",
                    headers=headers,
                    json=payload,
                )
            if response.is_error:
                # API-level errors (4xx/5xx) are not retried — the request reached
                # Resend and was rejected, so a retry will produce the same result.
                body = response.text
                logger.error(
                    "Resend API error %s for %s (from=%s): %s",
                    response.status_code, email_to, from_address, body,
                )
                hint = _resend_hint(response.status_code, body)
                raise EmailDeliveryError(
                    f"Resend rejected the request ({response.status_code}). {hint}"
                )
            logger.info("Email sent via Resend to %s (attempt %d)", email_to, attempt)
            return
        except httpx.RequestError as exc:
            last_exc = exc
            logger.warning(
                "Resend network error on attempt %d for %s: %s", attempt, email_to, exc,
            )
            if attempt == 1:
                time.sleep(1)

    logger.error("Resend unreachable after retries for %s: %s", email_to, last_exc)
    raise EmailDeliveryError(
        "Could not reach Resend after 2 attempts. Check outbound network connectivity."
    ) from last_exc


def _resend_hint(status_code: int, body: str) -> str:
    """Best-effort guidance for the most common Resend rejection reasons."""
    body_lower = body.lower()
    if status_code in (401, 403):
        return "Check RESEND_API_KEY — it may be invalid, revoked, or expired."
    if "domain" in body_lower and ("not verified" in body_lower or "verify" in body_lower):
        return (
            "The sender domain is not verified in Resend. Verify the domain in "
            "EMAILS_FROM_EMAIL at resend.com/domains."
        )
    if "testing emails" in body_lower or "onboarding@resend.dev" in body_lower:
        return (
            "Resend's shared sender 'onboarding@resend.dev' can only deliver to "
            "your own Resend account email. Verify a domain and set EMAILS_FROM_EMAIL."
        )
    if status_code == 429:
        return "Rate limit exceeded. Wait, or upgrade the Resend plan."
    return "See backend logs for the full Resend response body."


def _send_via_smtp(email_to: str, subject: str, html_content: str) -> None:
    """
    Send email via SMTP. Picks the correct connection mode based on SMTP_PORT
    (465 → implicit SSL, anything else → STARTTLS if SMTP_TLS is true).
    Retries once on transient network failures.
    """
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.error("SMTP settings are incomplete (host/user/password). Email not sent.")
        raise EmailDeliveryError(
            "SMTP is not fully configured. Set SMTP_HOST, SMTP_USER, and SMTP_PASSWORD."
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.EMAILS_FROM_EMAIL or settings.SMTP_USER
    message["To"] = email_to
    message.set_content(html_content, subtype="html")

    host = settings.SMTP_HOST
    port = settings.SMTP_PORT or 587

    last_exc: Exception | None = None
    for attempt in (1, 2):
        try:
            _smtp_send(host, port, message)
            logger.info("Email sent via SMTP %s:%s to %s (attempt %d)", host, port, email_to, attempt)
            return
        except smtplib.SMTPAuthenticationError as exc:
            # Permanent — do not retry.
            logger.error("SMTP auth failed for %s@%s: %s", settings.SMTP_USER, host, exc)
            raise EmailDeliveryError(_smtp_auth_hint(host, exc)) from exc
        except smtplib.SMTPRecipientsRefused as exc:
            # Permanent — recipient rejected.
            logger.error("SMTP recipient refused for %s: %s", email_to, exc)
            raise EmailDeliveryError(f"Recipient '{email_to}' was rejected by the SMTP server.") from exc
        except _TRANSIENT_SMTP_EXCEPTIONS as exc:
            last_exc = exc
            logger.warning("Transient SMTP failure attempt %d (%s:%s): %s", attempt, host, port, exc)
            if attempt == 1:
                time.sleep(1)
        except Exception as exc:
            # Unknown SMTP error — log fully, do not retry.
            logger.exception("Unexpected SMTP error (%s:%s)", host, port)
            raise EmailDeliveryError(f"SMTP send failed: {exc}") from exc

    logger.error("SMTP unreachable after retries (%s:%s): %s", host, port, last_exc)
    raise EmailDeliveryError(
        f"Could not reach SMTP server {host}:{port} after 2 attempts."
    ) from last_exc


def _smtp_send(host: str, port: int, message: EmailMessage) -> None:
    """One SMTP send attempt. Caller handles retries and exception classification."""
    if port == 465:
        server = smtplib.SMTP_SSL(host, port, timeout=15)
    else:
        server = smtplib.SMTP(host, port, timeout=15)
        if settings.SMTP_TLS:
            server.ehlo()
            server.starttls()
            server.ehlo()

    with server:
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(message)


def _smtp_auth_hint(host: str, exc: smtplib.SMTPAuthenticationError) -> str:
    """Provide actionable guidance for the common Gmail App Password mistake."""
    if "gmail" in (host or "").lower():
        return (
            "Gmail SMTP authentication failed. Gmail no longer accepts regular "
            "passwords — you must use a 16-character App Password generated at "
            "myaccount.google.com/apppasswords (2-Step Verification must be enabled). "
            f"Server said: {exc.smtp_error.decode('utf-8', 'ignore') if isinstance(exc.smtp_error, bytes) else exc.smtp_error}"
        )
    return f"SMTP authentication failed for {settings.SMTP_USER}@{host}. Check SMTP_USER and SMTP_PASSWORD."


def send_otp_email(email_to: str, otp: str) -> None:
    """
    Sends a formatted OTP verification email with a 6-digit code.
    """
    subject = f"{settings.PROJECT_NAME} - Account Verification Code"
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <h2 style="color: #4CAF50; text-align: center;">Welcome to {settings.PROJECT_NAME}!</h2>
                <p>Hello,</p>
                <p>Thank you for registering. Please use the following One-Time Password (OTP) to verify your account:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #4CAF50; background: #f9f9f9; padding: 10px 20px; border-radius: 5px; border: 1px dashed #4CAF50;">
                        {otp}
                    </span>
                </div>
                <p>This code will expire in 10 minutes. If you didn't request this, please ignore this email.</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #888; text-align: center;">
                    &copy; 2026 {settings.PROJECT_NAME}. All rights reserved.
                </p>
            </div>
        </body>
    </html>
    """
    
    send_email(email_to, subject, html_content)


def send_team_invite_email(email_to: str, business_name: str, inviter_name: str, invite_url: str) -> None:
    """
    Sends a formatted team invitation email.
    """
    subject = f"Invitation to join {business_name} on {settings.PROJECT_NAME}"
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <h2 style="color: #2196F3; text-align: center;">Team Invitation</h2>
                <p>Hello,</p>
                <p><strong>{inviter_name}</strong> has invited you to collaborate on the project <strong>{business_name}</strong> on {settings.PROJECT_NAME}.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{invite_url}" style="background-color: #2196F3; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        Accept Invitation
                    </a>
                </div>
                <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #888;">{invite_url}</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #888; text-align: center;">
                    &copy; 2026 {settings.PROJECT_NAME}. All rights reserved.
                </p>
            </div>
        </body>
    </html>
    """
    
    send_email(email_to, subject, html_content)


def send_join_request_status_email(email_to: str, business_name: str, status: str) -> None:
    """
    Sends an email to the user informing them if their join request was approved or rejected.
    """
    is_approved = status.lower() == "approved"
    subject = f"Update on your request to join {business_name}"
    status_text = "Approved" if is_approved else "Rejected"
    status_color = "#4CAF50" if is_approved else "#F44336"
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <h2 style="color: {status_color}; text-align: center;">Join Request {status_text}</h2>
                <p>Hello,</p>
                <p>We wanted to let you know that your request to join the project <strong>{business_name}</strong> has been <strong>{status_text.lower()}</strong>.</p>
                
                {"<p>You can now access the project dashboard and collaborate with your team.</p>" if is_approved else "<p>Unfortunately, the project owner has decided not to approve your request at this time.</p>"}
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://bizify.app/dashboard" style="background-color: {status_color}; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                        Go to Dashboard
                    </a>
                </div>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #888; text-align: center;">
                    &copy; 2026 {settings.PROJECT_NAME}. All rights reserved.
                </p>
            </div>
        </body>
    </html>
    """
    
    send_email(email_to, subject, html_content)
