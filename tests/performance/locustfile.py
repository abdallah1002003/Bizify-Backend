import uuid
from locust import HttpUser, task, between

class IdeaSparkUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Perform login and get token."""
        # Create a unique email for each locust user
        self.email = f"locust_{uuid.uuid4().hex[:8]}@example.com"
        self.password = "pass123"
        
        # 1. Register
        self.client.post("/api/v1/auth/register", json={
            "email": self.email,
            "password": self.password,
            "name": "Locust User",
            "role": "entrepreneur"
        })
        
        # 2. Login
        response = self.client.post("/api/v1/auth/login", data={
            "username": self.email,
            "password": self.password
        })
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            self.headers = {}

    @task(3)
    def view_ideas(self):
        self.client.get("/api/v1/ideas/", headers=self.headers)

    @task(2)
    def create_business_and_idea(self):
        # Create Business
        biz_res = self.client.post("/api/v1/businesses/", json={
            "owner_id": str(uuid.uuid4()), # Mock UUID or get real ID if needed
            "stage": "early"
        }, headers=self.headers)
        
        if biz_res.status_code == 200:
            biz_id = biz_res.json()["id"]
            # Create Idea linked to business
            self.client.post("/api/v1/ideas/", json={
                "owner_id": str(uuid.uuid4()),
                "business_id": biz_id,
                "title": f"Idea {uuid.uuid4().hex[:5]}",
                "description": "Load test description",
                "status": "draft",
                "ai_score": 7.5
            }, headers=self.headers)

    @task(1)
    def check_profile(self):
        self.client.get("/api/v1/users/me", headers=self.headers)
