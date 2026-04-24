import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Register a test user
        register_data = {"email": "test500@example.com", "password": "password123", "first_name": "Test", "last_name": "User"}
        res = await client.post("/api/v1/auth/register", json=register_data)
        
        # Login
        login_data = {"username": "test500@example.com", "password": "password123"}
        res = await client.post("/api/v1/auth/login", data=login_data)
        if res.status_code != 200:
            print("Login failed:", res.text)
            return
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test add predefined skill
        print("Testing add custom skill...")
        res = await client.post("/api/v1/profile/skills", json={"skill_name": "Custom Skill XYZ"}, headers=headers)
        print("Custom skill response:", res.status_code, res.text)
        
        # Test search skills
        print("Testing search skills...")
        res = await client.get("/api/v1/profile/skills/search?q=python", headers=headers)
        print("Search skills response:", res.status_code, res.text[:200])

asyncio.run(main())
