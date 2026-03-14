import smtplib
from email.message import EmailMessage
from typing import Optional
from app.core.config import settings

def send_email(
    email_to: str,
    subject: str,
    html_content: str,
) -> None:
    """
    Generic function to send an email via SMTP.
    """
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("WARNING: SMTP settings not configured. Email NOT sent.")
        print(f"Content for {email_to}: \n{html_content}")
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.EMAILS_FROM_EMAIL or settings.SMTP_USER
    message["To"] = email_to
    message.set_content(html_content, subtype="html")

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
            print(f"Successfully sent email to {email_to}")
    except Exception as e:
        print(f"ERROR: Failed to send email to {email_to}: {e}")

def send_otp_email(email_to: str, otp: str) -> None:
    """
    Send a formatted OTP verification email.
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
