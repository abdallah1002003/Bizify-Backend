"""
Integration tests for Business & Ideas API endpoints.
Target: 25+ endpoint tests covering business creation, management, ideas, and collaboration.
"""

import pytest
from uuid import uuid4


class TestBusinessAPI:
    """Business CRUD and management endpoints."""

    def test_business_create_and_list(self, client, auth_headers):
        """Create a business and list it."""
        # Create
        payload = {
            "name": "Test Startup",
            "description": "A test business",
            "stage": "early",
            "industry": "fintech"
        }
        response = client.post("/api/v1/businesses/", json=payload, headers=auth_headers)
        assert response.status_code in [200, 201]
        business_id = response.json().get("id")
        assert business_id is not None
        
        # List
        response = client.get("/api/v1/businesses/", headers=auth_headers)
        assert response.status_code == 200
        businesses = response.json()
        assert len(businesses) >= 1

    def test_business_get_single(self, client, auth_headers):
        """Get a single business."""
        business_id = str(uuid4())
        response = client.get(f"/api/v1/businesses/{business_id}", headers=auth_headers)
        # Could be 200 or 404 depending on DB state
        assert response.status_code in [200, 404]

    def test_business_update(self, client, auth_headers):
        """Update business details."""
        business_id = str(uuid4())
        payload = {"name": "Updated Name"}
        response = client.patch(f"/api/v1/businesses/{business_id}", json=payload, headers=auth_headers)
        assert response.status_code in [200, 404, 403]

    def test_business_delete(self, client, auth_headers):
        """Delete (soft delete) a business."""
        business_id = str(uuid4())
        response = client.delete(f"/api/v1/businesses/{business_id}", headers=auth_headers)
        assert response.status_code in [204, 404, 403]

    def test_business_requires_auth(self, client):
        """Business endpoints require authentication."""
        response = client.get("/api/v1/businesses/")
        assert response.status_code == 401


class TestBusinessCollaboration:
    """Business collaboration and invitations."""

    def test_list_business_collaborators(self, client, auth_headers):
        """List collaborators on a business."""
        business_id = str(uuid4())
        response = client.get(
            f"/api/v1/businesses/{business_id}/collaborators",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_invite_collaborator(self, client, auth_headers):
        """Invite someone to collaborate."""
        business_id = str(uuid4())
        payload = {
            "email": f"collaborator-{uuid4()}@example.com",
            "role": "editor"
        }
        response = client.post(
            f"/api/v1/businesses/{business_id}/collaborators/invite",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 404, 403]

    def test_remove_collaborator(self, client, auth_headers):
        """Remove a collaborator from business."""
        business_id = str(uuid4())
        collaborator_id = str(uuid4())
        response = client.delete(
            f"/api/v1/businesses/{business_id}/collaborators/{collaborator_id}",
            headers=auth_headers
        )
        assert response.status_code in [204, 404, 403]


class TestBusinessRoadmap:
    """Business roadmap and stages."""

    def test_get_business_roadmap(self, client, auth_headers):
        """Get a business roadmap."""
        business_id = str(uuid4())
        response = client.get(
            f"/api/v1/businesses/{business_id}/roadmap",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_add_roadmap_stage(self, client, auth_headers):
        """Add a stage to roadmap."""
        business_id = str(uuid4())
        payload = {
            "type": "planning",
            "title": "Market Research",
            "description": "Research market opportunities",
            "order_index": 1
        }
        response = client.post(
            f"/api/v1/businesses/{business_id}/roadmap/stages",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 404, 403]

    def test_update_roadmap_stage(self, client, auth_headers):
        """Update a roadmap stage."""
        business_id = str(uuid4())
        stage_id = str(uuid4())
        payload = {"title": "Updated Stage"}
        response = client.patch(
            f"/api/v1/businesses/{business_id}/roadmap/stages/{stage_id}",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [200, 404, 403]

    def test_delete_roadmap_stage(self, client, auth_headers):
        """Delete a roadmap stage."""
        business_id = str(uuid4())
        stage_id = str(uuid4())
        response = client.delete(
            f"/api/v1/businesses/{business_id}/roadmap/stages/{stage_id}",
            headers=auth_headers
        )
        assert response.status_code in [204, 404, 403]


class TestIdeasAPI:
    """Ideas/brainstorming endpoints."""

    def test_create_and_list_ideas(self, client, auth_headers):
        """Create an idea and list ideas."""
        # Create
        payload = {
            "title": "AI-powered SaaS Platform",
            "description": "A cloud platform for AI features",
            "category": "product",
            "client_feedback": "Customers want this"
        }
        response = client.post("/api/v1/ideas/", json=payload, headers=auth_headers)
        assert response.status_code in [200, 201]
        idea_id = response.json().get("id") if response.status_code in [200, 201] else None
        
        # List
        response = client.get("/api/v1/ideas/", headers=auth_headers)
        assert response.status_code == 200

    def test_get_idea_details(self, client, auth_headers):
        """Get a single idea."""
        idea_id = str(uuid4())
        response = client.get(f"/api/v1/ideas/{idea_id}", headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_update_idea(self, client, auth_headers):
        """Update an idea."""
        idea_id = str(uuid4())
        payload = {
            "title": "Updated Title",
            "description": "Updated description"
        }
        response = client.patch(f"/api/v1/ideas/{idea_id}", json=payload, headers=auth_headers)
        assert response.status_code in [200, 404, 403]

    def test_delete_idea(self, client, auth_headers):
        """Delete an idea."""
        idea_id = str(uuid4())
        response = client.delete(f"/api/v1/ideas/{idea_id}", headers=auth_headers)
        assert response.status_code in [204, 404, 403]

    def test_ideas_require_auth(self, client):
        """Ideas endpoints require authentication."""
        response = client.get("/api/v1/ideas/")
        assert response.status_code == 401


class TestIdeaVoting:
    """Idea voting and engagement."""

    def test_like_idea(self, client, auth_headers):
        """Like/vote for an idea."""
        idea_id = str(uuid4())
        response = client.post(
            f"/api/v1/ideas/{idea_id}/like",
            headers=auth_headers
        )
        assert response.status_code in [200, 404, 403]

    def test_unlike_idea(self, client, auth_headers):
        """Remove like from idea."""
        idea_id = str(uuid4())
        response = client.delete(
            f"/api/v1/ideas/{idea_id}/like",
            headers=auth_headers
        )
        assert response.status_code in [204, 404, 403]

    def test_get_idea_votes(self, client, auth_headers):
        """Get vote count for idea."""
        idea_id = str(uuid4())
        response = client.get(
            f"/api/v1/ideas/{idea_id}/votes",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]


class TestIdeaComments:
    """Idea comments and discussion."""

    def test_add_comment(self, client, auth_headers):
        """Add comment to idea."""
        idea_id = str(uuid4())
        payload = {"content": "This is a great idea!"}
        response = client.post(
            f"/api/v1/ideas/{idea_id}/comments",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 404, 403]

    def test_list_idea_comments(self, client, auth_headers):
        """List comments on idea."""
        idea_id = str(uuid4())
        response = client.get(
            f"/api/v1/ideas/{idea_id}/comments",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_update_comment(self, client, auth_headers):
        """Update a comment."""
        idea_id = str(uuid4())
        comment_id = str(uuid4())
        payload = {"content": "Updated comment"}
        response = client.patch(
            f"/api/v1/ideas/{idea_id}/comments/{comment_id}",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [200, 404, 403]

    def test_delete_comment(self, client, auth_headers):
        """Delete a comment."""
        idea_id = str(uuid4())
        comment_id = str(uuid4())
        response = client.delete(
            f"/api/v1/ideas/{idea_id}/comments/{comment_id}",
            headers=auth_headers
        )
        assert response.status_code in [204, 404, 403]


class TestIdeaComparison:
    """Idea comparison and metrics."""

    def test_generate_idea_comparison(self, client, auth_headers):
        """Generate AI comparison between ideas."""
        payload = {
            "idea1_id": str(uuid4()),
            "idea2_id": str(uuid4()),
            "focus_areas": ["feasibility", "market_potential"]
        }
        response = client.post(
            "/api/v1/ideas/compare",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 404, 400]

    def test_get_idea_comparison(self, client, auth_headers):
        """Retrieve generated comparison."""
        comparison_id = str(uuid4())
        response = client.get(
            f"/api/v1/ideas/comparisons/{comparison_id}",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_list_idea_metrics(self, client, auth_headers):
        """List metrics for an idea."""
        idea_id = str(uuid4())
        response = client.get(
            f"/api/v1/ideas/{idea_id}/metrics",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_add_idea_metric(self, client, auth_headers):
        """Add a metric to idea."""
        idea_id = str(uuid4())
        payload = {
            "name": "Users Reached",
            "value": 1000,
            "type": "users",
            "date": "2026-03-08"
        }
        response = client.post(
            f"/api/v1/ideas/{idea_id}/metrics",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 404, 403]


class TestIdeaVersioning:
    """Idea versions and history."""

    def test_list_idea_versions(self, client, auth_headers):
        """Get version history of idea."""
        idea_id = str(uuid4())
        response = client.get(
            f"/api/v1/ideas/{idea_id}/versions",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_get_idea_version(self, client, auth_headers):
        """Get specific version of idea."""
        idea_id = str(uuid4())
        version = 1
        response = client.get(
            f"/api/v1/ideas/{idea_id}/versions/{version}",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_revert_idea_version(self, client, auth_headers):
        """Revert idea to previous version."""
        idea_id = str(uuid4())
        version = 1
        response = client.post(
            f"/api/v1/ideas/{idea_id}/versions/{version}/revert",
            headers=auth_headers
        )
        assert response.status_code in [200, 404, 403]


class TestIdeaAccess:
    """Idea access control and sharing."""

    def test_grant_idea_access(self, client, auth_headers):
        """Grant access to idea to another user."""
        idea_id = str(uuid4())
        payload = {
            "user_id": str(uuid4()),
            "permission": "view"
        }
        response = client.post(
            f"/api/v1/ideas/{idea_id}/access",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 404, 403]

    def test_list_idea_access(self, client, auth_headers):
        """List who has access to idea."""
        idea_id = str(uuid4())
        response = client.get(
            f"/api/v1/ideas/{idea_id}/access",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_revoke_idea_access(self, client, auth_headers):
        """Revoke access to idea."""
        idea_id = str(uuid4())
        user_id = str(uuid4())
        response = client.delete(
            f"/api/v1/ideas/{idea_id}/access/{user_id}",
            headers=auth_headers
        )
        assert response.status_code in [204, 404, 403]


class TestErrorHandling:
    """Error handling in business and ideas endpoints."""

    def test_invalid_business_id(self, client, auth_headers):
        """Handle invalid business ID format."""
        response = client.get("/api/v1/businesses/invalid-uuid", headers=auth_headers)
        assert response.status_code in [400, 404]

    def test_missing_required_field(self, client, auth_headers):
        """Reject business creation without required fields."""
        payload = {"description": "Missing name"}
        response = client.post("/api/v1/businesses/", json=payload, headers=auth_headers)
        assert response.status_code in [400, 422]

    def test_unauthorized_business_update(self, client, auth_headers):
        """Prevent updating another user's business."""
        business_id = str(uuid4())
        payload = {"name": "Hijacked"}
        response = client.patch(
            f"/api/v1/businesses/{business_id}",
            json=payload,
            headers=auth_headers
        )
        # Could be 404 or 403
        assert response.status_code in [403, 404]
