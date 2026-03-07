import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.core.email_worker import EmailWorkerService
from app.models.core.core import EmailMessage

@pytest.fixture
def mock_db_session():
    # In EmailWorkerService, we mock AsyncSessionLocal because it creates its own session
    with patch("app.services.core.email_worker.AsyncSessionLocal") as mock_session_local:
        mock_db = AsyncMock()
        # Mocking the async context manager: async with AsyncSessionLocal() as db
        mock_session_local.return_value.__aenter__.return_value = mock_db
        yield mock_db

@pytest.mark.asyncio
async def test_process_email_queue_empty(mock_db_session):
    """Test that process_email_queue handles empty queue gracefully."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db_session.execute.return_value = mock_result
    
    # Pass mocked DB session to constructor
    service = EmailWorkerService(mock_db_session)
    await service.process_email_queue()
    
    mock_db_session.execute.assert_called_once()
    mock_db_session.commit.assert_not_called()

@pytest.mark.asyncio
@patch("app.services.core.email_worker.settings")
@patch("app.services.core.email_worker.EmailWorkerService._send_fastapi_mail")
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
    
    # Mock result for scalars().all()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_email]
    mock_db_session.execute.return_value = mock_result
    
    service = EmailWorkerService(mock_db_session)
    await service.process_email_queue()
    
    mock_send_mail.assert_called_once_with("test@example.com", "Test", "<p>Body</p>")
    assert mock_email.status == "SENT"
    assert mock_email.error_message is None
    # Called once per email in this implementation (inside the loop)
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
@patch("app.services.core.email_worker.settings")
@patch("app.services.core.email_worker.EmailWorkerService._send_fastapi_mail")
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
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_email]
    mock_db_session.execute.return_value = mock_result
    
    service = EmailWorkerService(mock_db_session)
    await service.process_email_queue()
    
    assert mock_email.status == "RETRYING"
    assert mock_email.retries == 1
    assert mock_email.error_message == "SMTP Error"
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
@patch("app.services.core.email_worker.settings")
@patch("app.services.core.email_worker.EmailWorkerService._send_fastapi_mail")
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
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_email]
    mock_db_session.execute.return_value = mock_result
    
    service = EmailWorkerService(mock_db_session)
    await service.process_email_queue()
    
    assert mock_email.status == "FAILED"
    assert mock_email.retries == 3
    assert mock_email.error_message == "SMTP Error"
    mock_db_session.commit.assert_called_once()
