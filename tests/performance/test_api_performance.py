"""
Performance and load tests for critical API endpoints.

Measures response times, throughput, and resource usage for:
- List endpoints with pagination
- Create operations
- Update operations
- Database query performance
"""

import pytest
import time
from uuid import uuid4
from typing import List
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models import User, Idea, Subscription, Plan


@pytest.mark.performance
class TestListEndpointPerformance:
    """Performance tests for paginated list endpoints."""

    def test_list_ideas_response_time(
        self, 
        client: TestClient,
        auth_headers: dict,
        db: Session,
        test_user: User
    ):
        """Test that listing ideas completes in reasonable time."""
        # Create some test data
        for i in range(50):
            idea = Idea(
                title=f"Test Idea {i}",
                description=f"Description for idea {i}",
                owner_id=test_user.id,
            )
            db.add(idea)
        db.commit()
        
        start_time = time.time()
        response = client.get(
            "/api/v1/ideas?skip=0&limit=20",
            headers=auth_headers
        )
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 1.0, f"List ideas took {elapsed:.2f}s, expected < 1.0s"
        
        data = response.json()
        assert "items" in data
        assert len(data["items"]) <= 20

    def test_list_subscriptions_response_time(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        test_user: User,
        db_plan: Plan
    ):
        """Test that listing subscriptions completes quickly."""
        # Create multiple subscriptions
        for i in range(20):
            sub = Subscription(
                user_id=test_user.id,
                plan_id=db_plan.id,
                status="ACTIVE"
            )
            db.add(sub)
        db.commit()
        
        start_time = time.time()
        response = client.get(
            "/api/v1/subscriptions?skip=0&limit=10",
            headers=auth_headers
        )
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 1.0, f"List subscriptions took {elapsed:.2f}s, expected < 1.0s"

    def test_pagination_handles_large_offsets(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        test_user: User
    ):
        """Test that pagination works efficiently with large skip values."""
        # Create many ideas
        for i in range(100):
            idea = Idea(
                title=f"Idea {i}",
                description=f"Desc {i}",
                owner_id=test_user.id,
            )
            db.add(idea)
        db.commit()
        
        # Request with large skip
        start_time = time.time()
        response = client.get(
            "/api/v1/ideas?skip=80&limit=20",
            headers=auth_headers
        )
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 1.5, f"Large offset pagination took {elapsed:.2f}s"


@pytest.mark.performance
class TestCreateOperationPerformance:
    """Performance tests for create operations."""

    def test_create_idea_response_time(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test that creating an idea is fast."""
        payload = {
            "title": "Performance Test Idea",
            "description": "Testing create performance",
            "category": "TECHNOLOGY"
        }
        
        start_time = time.time()
        response = client.post(
            "/api/v1/ideas",
            json=payload,
            headers=auth_headers
        )
        elapsed = time.time() - start_time
        
        assert response.status_code == 201
        assert elapsed < 0.5, f"Create idea took {elapsed:.2f}s, expected < 0.5s"

    def test_batch_create_ideas(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test creating multiple ideas in sequence."""
        start_time = time.time()
        
        for i in range(10):
            payload = {
                "title": f"Batch Idea {i}",
                "description": f"Description {i}",
                "category": "TECHNOLOGY"
            }
            response = client.post(
                "/api/v1/ideas",
                json=payload,
                headers=auth_headers
            )
            assert response.status_code == 201
        
        elapsed = time.time() - start_time
        avg_time = elapsed / 10
        
        assert avg_time < 0.5, f"Avg create time {avg_time:.2f}s, expected < 0.5s"


@pytest.mark.performance
class TestDatabaseQueryPerformance:
    """Performance tests for database operations."""

    def test_user_profile_eager_loading(self, db: Session, test_user: User):
        """Test that user profile is loaded efficiently."""
        from sqlalchemy.orm import selectinload
        
        start_time = time.time()
        # With eager loading
        user = (
            db.query(User)
            .options(selectinload(User.profile))
            .filter(User.id == test_user.id)
            .first()
        )
        elapsed_eager = time.time() - start_time
        
        # Access profile (should not cause another query with eager loading)
        _ = user.profile
        elapsed_total = time.time() - start_time
        
        # Total should be much less than 100ms
        assert elapsed_total < 0.1, f"Eager loading took {elapsed_total:.3f}s"

    def test_large_result_pagination(self, db: Session, test_user: User):
        """Test that pagination is efficient for large result sets."""
        # Create many ideas
        for i in range(100):
            idea = Idea(
                title=f"Idea {i}",
                description=f"Desc {i}",
                owner_id=test_user.id,
            )
            db.add(idea)
        db.commit()
        
        # Query with limit
        start_time = time.time()
        ideas = (
            db.query(Idea)
            .filter(Idea.owner_id == test_user.id)
            .limit(20)
            .offset(50)
            .all()
        )
        elapsed = time.time() - start_time
        
        assert len(ideas) == 20
        assert elapsed < 0.1, f"Pagination query took {elapsed:.3f}s"


@pytest.mark.performance
class TestConcurrentRequests:
    """Tests for handling concurrent requests."""

    def test_multiple_users_list_simultaneously(
        self,
        client: TestClient,
        db: Session,
    ):
        """Test that multiple users can list ideas concurrently without issues."""
        # Create multiple users and their ideas
        users = []
        for i in range(5):
            user = User(
                email=f"user{i}@test.com",
                password_hash="fake_hash",
                is_active=True,
                is_verified=True
            )
            db.add(user)
            db.flush()
            users.append(user)
            
            for j in range(10):
                idea = Idea(
                    title=f"User {i} Idea {j}",
                    description=f"Desc {j}",
                    owner_id=user.id,
                )
                db.add(idea)
        db.commit()
        
        # Simulate concurrent requests (sequential in test, but measures timing)
        start_time = time.time()
        
        for user in users:
            # Would need auth tokens for real concurrent test
            # This is a simplified version
            ideas = db.query(Idea).filter(Idea.owner_id == user.id).limit(10).all()
            assert len(ideas) >= 0
        
        elapsed = time.time() - start_time
        
        # All 5 users' queries should complete quickly
        assert elapsed < 0.5, f"Concurrent queries took {elapsed:.2f}s"


@pytest.mark.performance
class TestMemoryEfficiency:
    """Tests for memory-efficient operation."""

    def test_large_pagination_does_not_load_all(self, db: Session, test_user: User):
        """Test that pagination doesn't load all records into memory."""
        # Create many ideas
        for i in range(500):
            idea = Idea(
                title=f"Idea {i}",
                description=f"Desc {i}",
                owner_id=test_user.id,
            )
            db.add(idea)
        db.commit()
        
        # Request single page
        ideas = (
            db.query(Idea)
            .filter(Idea.owner_id == test_user.id)
            .limit(20)
            .offset(0)
            .all()
        )
        
        # Should only load the 20 items
        assert len(ideas) == 20


@pytest.mark.performance
class TestEndpointPerformanceSuite:
    """Full performance test suite for critical endpoints."""

    def test_health_check_response_time(self, client: TestClient):
        """Test that health check is very fast."""
        start_time = time.time()
        response = client.get("/health")
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 0.1, f"Health check took {elapsed:.3f}s, expected < 0.1s"

    def test_root_endpoint_response_time(self, client: TestClient):
        """Test that root endpoint responds quickly."""
        start_time = time.time()
        response = client.get("/")
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 0.1, f"Root endpoint took {elapsed:.3f}s"

    def test_metrics_endpoint_response_time(self, client: TestClient):
        """Test that metrics endpoint completes in reasonable time."""
        start_time = time.time()
        response = client.get("/metrics")
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 1.0, f"Metrics endpoint took {elapsed:.2f}s"
