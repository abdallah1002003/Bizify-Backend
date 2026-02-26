# ruff: noqa: E402
import asyncio
import logging
from sqlalchemy import select, or_

from config.settings import settings
from app.db.database import AsyncSessionLocal
from app.models.core.core import EmailMessage
from app.core.crud_utils import _utc_now

logger = logging.getLogger(__name__)

async def _send_fastapi_mail(to_email: str, subject: str, html_body: str) -> None:
    """Low-level async sender using fastapi-mail."""
    from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig

    conf = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_STARTTLS=settings.MAIL_TLS,
        MAIL_SSL_TLS=settings.MAIL_SSL,
        USE_CREDENTIALS=bool(settings.MAIL_USERNAME),
        VALIDATE_CERTS=True,
    )

    message = MessageSchema(
        subject=subject,
        recipients=[to_email],
        body=html_body,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def process_email_queue() -> None:
    """
    Process pending and retrying emails from the database queue.
    Should be run periodically as a background task.
    """
    async with AsyncSessionLocal() as db:
        try:
            # Fetch emails that need to be sent
            stmt = select(EmailMessage).where(
                or_(
                    EmailMessage.status == "PENDING",
                    EmailMessage.status == "RETRYING"
                )
            ).limit(50)  # Process in batches
            
            result = await db.execute(stmt)
            emails = result.scalars().all()
            
            if not emails:
                return

            now = _utc_now()
            for email in emails:
                # Implement exponential backoff for retries
                if email.status == "RETRYING":
                    current_retries = int(email.retries or 0)
                    backoff_seconds = 10 * (2 ** current_retries)
                    # If updated_at is naive, assume UTC.
                    updated_at_tz = email.updated_at
                    if updated_at_tz and updated_at_tz.tzinfo is None:
                        updated_at_tz = updated_at_tz.replace(tzinfo=now.tzinfo)
                    
                    if updated_at_tz and (now - updated_at_tz).total_seconds() < backoff_seconds:
                        continue  # Skip this email for now

                try:
                    if settings.MAIL_ENABLED:
                        await _send_fastapi_mail(email.to_email, email.subject, email.html_body)
                        logger.info("Successfully sent queued email to %s", email.to_email)
                    else:
                        logger.info("MAIL_ENABLED=False - Mocked sending to %s", email.to_email)
                    
                    email.status = "SENT"
                    email.error_message = None
                except Exception as e:
                    logger.error("Failed to send queued email to %s: %s", email.to_email, str(e))
                    current_retries = int(email.retries or 0)
                    max_retries = int(email.max_retries or 3)
                    
                    email.retries = current_retries + 1
                    email.error_message = str(e)
                    if current_retries + 1 >= max_retries:
                        email.status = "FAILED"
                    else:
                        email.status = "RETRYING"
                
                await db.commit()

        except Exception as e:
            logger.exception("Error processing email queue: %s", str(e))
            await db.rollback()

async def run_email_worker(interval_seconds: int = 10) -> None:
    """
    Continuous background loop for processing emails.
    """
    logger.info("Email worker started (interval: %ds)", interval_seconds)
    while True:
        try:
            await process_email_queue()
        except asyncio.CancelledError:
            logger.info("Email worker shutting down")
            break
        except Exception as e:
            logger.error("Unhandled exception in email worker: %s", str(e))
        
        await asyncio.sleep(interval_seconds)
