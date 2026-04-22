import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings


logger = logging.getLogger(__name__)


class EmailDeliveryError(RuntimeError):
    """Raised when an outbound email could not be delivered."""


def send_email(
    email_to: str,
    subject: str,
    html_content: str,
) -> None:
    """
    Generic function to send an email via SMTP.
    Raise an explicit error when configuration is missing or delivery fails.
    """
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.error("SMTP settings are incomplete. Email was not sent.")
        raise EmailDeliveryError("SMTP settings are incomplete")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.EMAILS_FROM_EMAIL or settings.SMTP_USER
    message["To"] = email_to
    message.set_content(html_content, subtype = "html")

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
            
            logger.info(f"Successfully sent email to {email_to}")
    except Exception as e:
        logger.exception("Failed to send email to %s", email_to)
        raise EmailDeliveryError("Failed to send email") from e


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
