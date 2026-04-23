import os
import shutil
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.partner_profile import ApprovalStatus, PartnerProfile
from app.models.user import User, UserRole
from app.repositories.notification_repo import notification_repo
from app.repositories.partner_repo import partner_repo
from app.repositories.user_repo import user_repo
from app.schemas.partner_profile import PartnerProfileCreate, PartnerProfileUpdate

try:
    from supabase import create_client, Client
except ImportError:
    # Handle if supabase is not installed yet
    create_client = None
    Client = None


class PartnerService:
    """Partner application and profile workflows."""

    @staticmethod
    def apply_partner(
        db: Session,
        user: User,
        profile_in: PartnerProfileCreate,
        files: List[UploadFile],
        *,
        commit: bool = True,
        refresh: bool = True,
    ) -> PartnerProfile:
        """Create a partner application and store uploaded documents."""
        existing_profile = partner_repo.get_by_user_id(db, user.id)
        if existing_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Partner profile already exists for this user",
            )

        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supporting documents are required for partner registration",
            )

        file_paths: List[str] = []
        try:
            for file in files:
                file_paths.append(PartnerService.save_id_document(user.id, file))

            profile = partner_repo.create(
                db,
                obj_in={
                    "user_id": user.id,
                    **profile_in.model_dump(exclude={"user_id"}),
                    "documents_json": file_paths,
                },
                commit=False,
                refresh=False,
            )
            PartnerService._notify_admin(
                db,
                title=f"New Partner Application: {user.id}",
                message="A new partner has submitted their profile for review.",
                commit=False,
                refresh=False,
            )

            if commit:
                db.commit()
            else:
                db.flush()

            if refresh:
                db.refresh(profile)

            return profile
        except Exception:
            PartnerService.cleanup_documents(file_paths)
            raise

    @staticmethod
    def _notify_admin(
        db: Session,
        title: str,
        message: str,
        *,
        commit: bool = True,
        refresh: bool = True,
    ) -> None:
        """Notify the first admin user about partner-related changes."""
        admin = user_repo.get_first_by_role(db, UserRole.ADMIN)
        if not admin:
            return

        notification_repo.create(
            db,
            obj_in={
                "user_id": admin.id,
                "title": title,
                "message": message,
                "type": "SYSTEM",
            },
            commit=commit,
            refresh=refresh,
        )

    @staticmethod
    def update_profile(
        db: Session,
        user_id: uuid.UUID,
        profile_in: PartnerProfileUpdate,
    ) -> PartnerProfile:
        """Update a partner profile and reset approval to pending."""
        profile = partner_repo.get_by_user_id(db, user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Partner profile not found")

        update_data = profile_in.model_dump(exclude_unset=True)
        update_data["approval_status"] = ApprovalStatus.PENDING
        update_data["approved_by"] = None
        update_data["approved_at"] = None

        updated_profile = partner_repo.update(db, db_obj=profile, obj_in=update_data)
        PartnerService._notify_admin(
            db,
            title=f"Partner Profile Updated: {user_id}",
            message=(
                "An approved partner updated their profile and now needs a fresh review."
            ),
        )
        return updated_profile

    @staticmethod
    def get_user_profile(
        db: Session,
        user_id: uuid.UUID,
    ) -> Optional[PartnerProfile]:
        """Fetch the partner profile for a specific user."""
        return partner_repo.get_by_user_id(db, user_id)

    @staticmethod
    def list_requests(
        db: Session,
        status: Optional[ApprovalStatus] = None,
    ) -> List[PartnerProfile]:
        """List partner profiles, optionally filtered by approval status."""
        return partner_repo.get_filtered(db, status)

    @staticmethod
    def get_all_requests(db: Session) -> List[PartnerProfile]:
        """Return all partner applications."""
        return partner_repo.get_all(db)

    @staticmethod
    def get_pending_requests(db: Session) -> List[PartnerProfile]:
        """Return all pending partner applications."""
        return partner_repo.get_pending(db)

    @staticmethod
    def get_active_partners(db: Session) -> List[PartnerProfile]:
        """Return all approved partner profiles."""
        return partner_repo.get_approved(db)

    @staticmethod
    def save_id_document(user_id: uuid.UUID, file: UploadFile) -> str:
        """Store an uploaded partner document on disk or Supabase."""
        file_name = file.filename or "document"
        unique_filename = f"{uuid.uuid4().hex}_{file_name}"
        
        # If Supabase is configured and installed, use it
        if settings.SUPABASE_URL and settings.SUPABASE_KEY and create_client:
            try:
                supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                file_path = f"partners/{user_id}/{unique_filename}"
                
                # Upload the file
                file_content = file.file.read()
                # reset file pointer in case it needs to be read again
                file.file.seek(0)
                
                supabase.storage.from_(settings.SUPABASE_BUCKET_NAME).upload(
                    path=file_path,
                    file=file_content,
                    file_options={"content-type": file.content_type}
                )
                
                # Return the public URL
                public_url = supabase.storage.from_(settings.SUPABASE_BUCKET_NAME).get_public_url(file_path)
                return public_url
            except Exception as e:
                # If Supabase fails, we could raise an error or fallback to local. Raising is safer for production.
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload document to Supabase: {str(e)}"
                )
                
        # Fallback to local storage (e.g., for local development)
        upload_dir = os.path.join("uploads", "partners", str(user_id))
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, unique_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            # reset file pointer
            file.file.seek(0)

        return file_path

    @staticmethod
    def cleanup_documents(file_paths: Optional[List[str]]) -> None:
        """Remove uploaded files that should not be kept after a failed workflow."""
        for file_path in file_paths or []:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError:
                continue

    @staticmethod
    def approve_request(
        db: Session,
        profile_id: uuid.UUID,
        admin_id: uuid.UUID,
    ) -> PartnerProfile:
        """Approve a partner request and update the user's role."""
        profile = partner_repo.get_by_profile_id(db, profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found",
            )

        profile.approval_status = ApprovalStatus.APPROVED
        profile.approved_by = admin_id
        profile.approved_at = datetime.now(timezone.utc)

        user = user_repo.get(db, profile.user_id)
        if user:
            user.role = UserRole(profile.partner_type.value)
            user_repo.save(db, db_obj=user, commit=False, refresh=False)

        partner_repo.save(db, db_obj=profile, commit=False, refresh=False)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def reject_request(
        db: Session,
        profile_id: uuid.UUID,
        admin_id: uuid.UUID,
    ) -> PartnerProfile:
        """Reject a partner request without changing the user's role."""
        profile = partner_repo.get_by_profile_id(db, profile_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found",
            )

        profile.approval_status = ApprovalStatus.REJECTED
        profile.approved_by = admin_id
        profile.approved_at = datetime.now(timezone.utc)
        return partner_repo.save(db, db_obj=profile)
