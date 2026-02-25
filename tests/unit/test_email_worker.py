import pytest
from unittest.mock import patch, MagicMock
from app.services.core.email_worker import process_email_queue
from app.models.core.core import EmailMessage

@pytest.fixture
def mock_db_session():
    with patch("app.services.core.email_worker.SessionLocal") as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        yield mock_db

@pytest.mark.asyncio
async def test_process_email_queue_empty(mock_db_session):
    """Test that process_email_queue handles empty queue gracefully."""
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = []
    
    await process_email_queue()
    
    mock_db_session.execute.assert_called_once()
    mock_db_session.commit.assert_not_called()
    mock_db_session.close.assert_called_once()

@pytest.mark.asyncio
@patch("app.services.core.email_worker.settings")
@patch("app.services.core.email_worker._send_fastapi_mail")
async def test_process_email_queue_success(mock_send_mail, mock_settings, mock_db_session):
    """Test successful email processing."""
    mock_settings.MAIL_ENABLED = True
    
    mock_email = EmailMessage(
        id="123",
        to_email="test@example.com",
        subject="Test",
        html_body="<p>Body</p>",
        status="PENDING",
        retries=0,
        max_retries=3
    )
    
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = [mock_email]
    
    await process_email_queue()
    
    mock_send_mail.assert_called_once_with("test@example.com", "Test", "<p>Body</p>")
    assert mock_email.status == "SENT"
    assert mock_email.error_message is None
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
@patch("app.services.core.email_worker.settings")
@patch("app.services.core.email_worker._send_fastapi_mail")
async def test_process_email_queue_failure_retry(mock_send_mail, mock_settings, mock_db_session):
    """Test email processing failure, resulting in retry."""
    mock_settings.MAIL_ENABLED = True
    mock_send_mail.side_effect = Exception("SMTP Error")
    
    mock_email = EmailMessage(
        id="123",
        to_email="test@example.com",
        status="PENDING",
        retries=0,
        max_retries=3
    )
    
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = [mock_email]
    
    await process_email_queue()
    
    assert mock_email.status == "RETRYING"
    assert mock_email.retries == 1
    assert mock_email.error_message == "SMTP Error"
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
@patch("app.services.core.email_worker.settings")
@patch("app.services.core.email_worker._send_fastapi_mail")
async def test_process_email_queue_failure_max_retries(mock_send_mail, mock_settings, mock_db_session):
    """Test email processing failure resulting in DEAD/FAILED status after max retries."""
    mock_settings.MAIL_ENABLED = True
    mock_send_mail.side_effect = Exception("SMTP Error")
    
    mock_email = EmailMessage(
        id="123",
        to_email="test@example.com",
        status="RETRYING",
        retries=2,
        max_retries=3
    )
    
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = [mock_email]
    
    await process_email_queue()
    
    assert mock_email.status == "FAILED"
    assert mock_email.retries == 3
    assert mock_email.error_message == "SMTP Error"
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
@patch("app.services.core.email_worker.settings")
@patch("app.services.core.email_worker._send_fastapi_mail")
async def test_process_email_queue_mocked_disabled(mock_send_mail, mock_settings, mock_db_session):
    """Test email processing when MAIL_ENABLED is False (mocked mode)."""
    mock_settings.MAIL_ENABLED = False
    
    mock_email = EmailMessage(to_email="test@example.com", status="PENDING", retries=0)
    
    mock_db_session.execute.return_value.scalars.return_value.all.return_value = [mock_email]
    
    await process_email_queue()
    
    mock_send_mail.assert_not_called()
    assert mock_email.status == "SENT"
    mock_db_session.commit.assert_called_once()
