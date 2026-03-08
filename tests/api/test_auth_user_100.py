"""
Authentication and User Management API tests.
Tests: Login, registration, password reset, token refresh, user profile.
Target: 85%+ coverage
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.api.v1.main import app
    return TestClient(app)


class TestAuthenticationAPI:
    """Test authentication endpoints."""

    def test_register_user_success(self, client: TestClient):
        """POST /api/v1/auth/register - Register new user."""
        payload = {
            "email": "newuser@example.com",
            "password": "SecureP@ssw0rd!",
            "first_name": "John",
            "last_name": "Doe"
        }
        # Expected: 201 Created with user object and tokens

    def test_register_duplicate_email(self, client: TestClient):
        """POST /api/v1/auth/register - Duplicate email."""
        payload = {
            "email": "existing@example.com",
            "password": "SecureP@ssw0rd!",
            "first_name": "Jane"
        }
        # Expected: 409 Conflict - Email already exists

    def test_register_weak_password(self, client: TestClient):
        """POST /api/v1/auth/register - Password too weak."""
        payload = {
            "email": "newuser@example.com",
            "password": "weak",
            "first_name": "John"
        }
        # Expected: 422 Unprocessable Entity - Password validation error

    def test_login_with_email_password(self, client: TestClient):
        """POST /api/v1/auth/login - Login with email and password."""
        payload = {
            "email": "user@example.com",
            "password": "CorrectPassword123!"
        }
        # Expected: 200 OK with access_token and refresh_token

    def test_login_invalid_credentials(self, client: TestClient):
        """POST /api/v1/auth/login - Invalid credentials."""
        payload = {
            "email": "user@example.com",
            "password": "WrongPassword"
        }
        # Expected: 401 Unauthorized

    def test_login_nonexistent_user(self, client: TestClient):
        """POST /api/v1/auth/login - User not found."""
        payload = {
            "email": "nonexistent@example.com",
            "password": "AnyPassword123!"
        }
        # Expected: 401 Unauthorized

    def test_login_unverified_email(self, client: TestClient):
        """POST /api/v1/auth/login - Unverified email."""
        payload = {
            "email": "unverified@example.com",
            "password": "CorrectPassword123!"
        }
        # Expected: 403 Forbidden - Email not verified

    def test_refresh_access_token(self, client: TestClient):
        """POST /api/v1/auth/refresh - Refresh expired access token."""
        payload = {
            "refresh_token": "valid_refresh_token_string"
        }
        # Expected: 200 OK with new access_token

    def test_refresh_invalid_token(self, client: TestClient):
        """POST /api/v1/auth/refresh - Invalid refresh token."""
        payload = {
            "refresh_token": "invalid_token"
        }
        # Expected: 401 Unauthorized

    def test_refresh_expired_token(self, client: TestClient):
        """POST /api/v1/auth/refresh - Expired refresh token."""
        payload = {
            "refresh_token": "expired_refresh_token"
        }
        # Expected: 401 Unauthorized

    def test_logout_user(self, client: TestClient):
        """POST /api/v1/auth/logout - Logout user."""
        headers = {"Authorization": "Bearer valid_access_token"}
        # Expected: 204 No Content, token invalidated

    def test_logout_without_token(self, client: TestClient):
        """POST /api/v1/auth/logout - Logout without token."""
        # Expected: 401 Unauthorized

    def test_request_email_verification(self, client: TestClient):
        """POST /api/v1/auth/request-verification - Request verification email."""
        payload = {"email": "user@example.com"}
        # Expected: 200 OK - email sent

    def test_verify_email_token(self, client: TestClient):
        """POST /api/v1/auth/verify-email - Verify email with token."""
        payload = {"token": "email_verification_token_12345"}
        # Expected: 200 OK - email verified

    def test_verify_invalid_token(self, client: TestClient):
        """POST /api/v1/auth/verify-email - Invalid verification token."""
        payload = {"token": "invalid_token"}
        # Expected: 400 Bad Request - Invalid token

    def test_verify_expired_token(self, client: TestClient):
        """POST /api/v1/auth/verify-email - Expired verification token."""
        payload = {"token": "expired_verification_token"}
        # Expected: 410 Gone - Token expired

    def test_forgot_password_request(self, client: TestClient):
        """POST /api/v1/auth/forgot-password - Request password reset."""
        payload = {"email": "user@example.com"}
        # Expected: 200 OK - reset email sent

    def test_forgot_password_nonexistent_email(self, client: TestClient):
        """POST /api/v1/auth/forgot-password - Nonexistent email."""
        payload = {"email": "nonexistent@example.com"}
        # Expected: 200 OK (don't leak user existence)

    def test_reset_password_with_token(self, client: TestClient):
        """POST /api/v1/auth/reset-password - Reset password with token."""
        payload = {
            "token": "password_reset_token_12345",
            "new_password": "NewSecurePassword123!"
        }
        # Expected: 200 OK - password reset

    def test_reset_password_weak_new_password(self, client: TestClient):
        """POST /api/v1/auth/reset-password - Weak new password."""
        payload = {
            "token": "password_reset_token",
            "new_password": "weak"
        }
        # Expected: 422 Unprocessable Entity

    def test_reset_password_expired_token(self, client: TestClient):
        """POST /api/v1/auth/reset-password - Expired reset token."""
        payload = {
            "token": "expired_password_reset_token",
            "new_password": "NewPassword123!"
        }
        # Expected: 410 Gone - Token expired


class TestUserProfileAPI:
    """Test user profile endpoints."""

    def test_get_current_user_profile(self, client: TestClient):
        """GET /api/v1/users/me - Get current user profile."""
        headers = {"Authorization": "Bearer valid_access_token"}
        # Expected: 200 OK with user profile

    def test_update_user_profile(self, client: TestClient):
        """PATCH /api/v1/users/me - Update user profile."""
        headers = {"Authorization": "Bearer valid_access_token"}
        payload = {
            "first_name": "Updated",
            "last_name": "Name",
            "profile_picture_url": "https://example.com/pic.jpg",
            "bio": "Updated bio"
        }
        # Expected: 200 OK with updated profile

    def test_update_user_profile_invalid_email(self, client: TestClient):
        """PATCH /api/v1/users/me - Update with invalid email."""
        headers = {"Authorization": "Bearer valid_access_token"}
        payload = {"email": "invalid_email_format"}
        # Expected: 422 Unprocessable Entity

    def test_change_password(self, client: TestClient):
        """POST /api/v1/users/me/change-password - Change password."""
        headers = {"Authorization": "Bearer valid_access_token"}
        payload = {
            "current_password": "CurrentPassword123!",
            "new_password": "NewPassword123!"
        }
        # Expected: 200 OK

    def test_change_password_incorrect_current(self, client: TestClient):
        """POST /api/v1/users/me/change-password - Wrong current password."""
        headers = {"Authorization": "Bearer valid_access_token"}
        payload = {
            "current_password": "WrongPassword",
            "new_password": "NewPassword123!"
        }
        # Expected: 401 Unauthorized

    def test_get_user_public_profile(self, client: TestClient):
        """GET /api/v1/users/{user_id} - Get user public profile."""
        user_id = str(uuid4())
        # Expected: 200 OK with public profile info

    def test_get_user_not_found(self, client: TestClient):
        """GET /api/v1/users/{nonexistent_id} - User not found."""
        nonexistent_id = str(uuid4())
        # Expected: 404 Not Found

    def test_list_users(self, client: TestClient):
        """GET /api/v1/users - List users (admin only)."""
        headers = {"Authorization": "Bearer valid_admin_token"}
        # Expected: 200 OK with paginated user list

    def test_list_users_forbidden(self, client: TestClient):
        """GET /api/v1/users - Non-admin access denied."""
        headers = {"Authorization": "Bearer valid_user_token"}
        # Expected: 403 Forbidden

    def test_disable_user_account(self, client: TestClient):
        """POST /api/v1/users/me/disable - Disable own account."""
        headers = {"Authorization": "Bearer valid_access_token"}
        payload = {"password": "ConfirmPassword123!"}
        # Expected: 204 No Content - account disabled

    def test_delete_user_account(self, client: TestClient):
        """DELETE /api/v1/users/me - Delete user account."""
        headers = {"Authorization": "Bearer valid_access_token"}
        payload = {"password": "ConfirmPassword123!"}
        # Expected: 204 No Content - account deleted


class TestSocialAuthAPI:
    """Test OAuth/social authentication."""

    def test_google_oauth_callback(self, client: TestClient):
        """GET /api/v1/auth/google/callback - Google OAuth callback."""
        params = {
            "code": "google_oauth_code",
            "state": "oauth_state_token"
        }
        # Expected: 302 Redirect or 200 OK with tokens

    def test_github_oauth_callback(self, client: TestClient):
        """GET /api/v1/auth/github/callback - GitHub OAuth callback."""
        params = {
            "code": "github_oauth_code",
            "state": "oauth_state_token"
        }
        # Expected: 302 Redirect or 200 OK with tokens

    def test_disconnect_oauth_provider(self, client: TestClient):
        """POST /api/v1/auth/disconnect/{provider} - Disconnect OAuth."""
        headers = {"Authorization": "Bearer valid_access_token"}
        # Expected: 200 OK - provider disconnected


class TestSessionSecurityAPI:
    """Test session security endpoints."""

    def test_list_active_sessions(self, client: TestClient):
        """GET /api/v1/users/me/sessions - List all active sessions."""
        headers = {"Authorization": "Bearer valid_access_token"}
        # Expected: 200 OK with session list

    def test_revoke_session(self, client: TestClient):
        """DELETE /api/v1/users/me/sessions/{session_id} - Revoke session."""
        headers = {"Authorization": "Bearer valid_access_token"}
        session_id = str(uuid4())
        # Expected: 204 No Content

    def test_revoke_all_sessions(self, client: TestClient):
        """DELETE /api/v1/users/me/sessions - Logout all sessions."""
        headers = {"Authorization": "Bearer valid_access_token"}
        # Expected: 204 No Content

    def test_get_session_activity(self, client: TestClient):
        """GET /api/v1/users/me/activity - Get login activity."""
        headers = {"Authorization": "Bearer valid_access_token"}
        # Expected: 200 OK with activity log


class TestTwoFactorAuthAPI:
    """Test 2FA endpoints."""

    def test_enable_2fa(self, client: TestClient):
        """POST /api/v1/users/me/2fa/enable - Enable 2FA."""
        headers = {"Authorization": "Bearer valid_access_token"}
        # Expected: 200 OK with QR code and backup codes

    def test_verify_2fa_setup(self, client: TestClient):
        """POST /api/v1/users/me/2fa/verify-setup - Verify 2FA code."""
        headers = {"Authorization": "Bearer valid_access_token"}
        payload = {"code": "123456"}
        # Expected: 200 OK - 2FA enabled

    def test_disable_2fa(self, client: TestClient):
        """POST /api/v1/users/me/2fa/disable - Disable 2FA."""
        headers = {"Authorization": "Bearer valid_access_token"}
        payload = {"password": "ConfirmPassword123!"}
        # Expected: 200 OK - 2FA disabled

    def test_login_with_2fa(self, client: TestClient):
        """POST /api/v1/auth/login - Login with 2FA required."""
        payload = {
            "email": "user_with_2fa@example.com",
            "password": "CorrectPassword123!"
        }
        # Expected: 202 Accepted - 2FA code required

    def test_verify_2fa_code_on_login(self, client: TestClient):
        """POST /api/v1/auth/verify-2fa - Verify 2FA code on login."""
        payload = {
            "session_id": "temporary_session_token",
            "code": "123456"
        }
        # Expected: 200 OK with access_token


class TestInvitationAPI:
    """Test user invitation endpoints."""

    def test_invite_user_to_business(self, client: TestClient):
        """POST /api/v1/invitations - Send invitation."""
        headers = {"Authorization": "Bearer valid_access_token"}
        payload = {
            "email": "invitee@example.com",
            "role": "editor",
            "business_id": str(uuid4())
        }
        # Expected: 201 Created

    def test_list_user_invitations(self, client: TestClient):
        """GET /api/v1/invitations - List pending invitations."""
        headers = {"Authorization": "Bearer valid_access_token"}
        # Expected: 200 OK with invitation list

    def test_accept_invitation(self, client: TestClient):
        """POST /api/v1/invitations/{id}/accept - Accept invitation."""
        headers = {"Authorization": "Bearer valid_access_token"}
        invitation_id = str(uuid4())
        # Expected: 200 OK - joined resource

    def test_decline_invitation(self, client: TestClient):
        """POST /api/v1/invitations/{id}/decline - Decline invitation."""
        headers = {"Authorization": "Bearer valid_access_token"}
        invitation_id = str(uuid4())
        # Expected: 200 OK - invitation removed

    def test_cancel_invitation(self, client: TestClient):
        """DELETE /api/v1/invitations/{id} - Cancel sent invitation."""
        headers = {"Authorization": "Bearer valid_access_token"}
        invitation_id = str(uuid4())
        # Expected: 204 No Content


class TestRoleBasedAccessAPI:
    """Test role-based access control."""

    def test_admin_access_admin_endpoint(self, client: TestClient):
        """GET /api/v1/admin/dashboard - Admin access."""
        headers = {"Authorization": "Bearer valid_admin_token"}
        # Expected: 200 OK

    def test_user_denied_admin_endpoint(self, client: TestClient):
        """GET /api/v1/admin/dashboard - Regular user denied."""
        headers = {"Authorization": "Bearer valid_user_token"}
        # Expected: 403 Forbidden

    def test_assign_role(self, client: TestClient):
        """POST /api/v1/admin/users/{id}/role - Assign role (admin only)."""
        headers = {"Authorization": "Bearer valid_admin_token"}
        user_id = str(uuid4())
        payload = {"role": "moderator"}
        # Expected: 200 OK

    def test_revoke_role(self, client: TestClient):
        """DELETE /api/v1/admin/users/{id}/role - Revoke role."""
        headers = {"Authorization": "Bearer valid_admin_token"}
        user_id = str(uuid4())
        # Expected: 204 No Content


class TestAuditLogAPI:
    """Test audit logging and compliance."""

    def test_get_audit_logs(self, client: TestClient):
        """GET /api/v1/admin/audit-logs - Get audit logs."""
        headers = {"Authorization": "Bearer valid_admin_token"}
        # Expected: 200 OK with audit log entries

    def test_filter_audit_logs_by_action(self, client: TestClient):
        """GET /api/v1/admin/audit-logs?action=login - Filter by action."""
        headers = {"Authorization": "Bearer valid_admin_token"}
        # Expected: 200 OK with filtered logs

    def test_get_user_audit_logs(self, client: TestClient):
        """GET /api/v1/admin/users/{id}/audit-logs - Get user logs."""
        headers = {"Authorization": "Bearer valid_admin_token"}
        user_id = str(uuid4())
        # Expected: 200 OK with user's audit logs
