import logging
from app.services.ideation.idea_version import register_idea_version_handlers
from app.services.business.business_roadmap import register_business_roadmap_handlers
from app.services.business.business_collaborator import register_business_collaborator_handlers
from app.services.core.email_service import register_email_handlers

logger = logging.getLogger(__name__)

def register_all_handlers():  # type: ignore
    """Register all service event handlers."""
    logger.info("Registering internal event handlers...")
    
    # Ideation handlers
    register_idea_version_handlers()
    
    # Business handlers
    register_business_roadmap_handlers()
    register_business_collaborator_handlers()
    
    # Core handlers
    register_email_handlers()
    
    logger.info("All internal event handlers registered successfully.")
