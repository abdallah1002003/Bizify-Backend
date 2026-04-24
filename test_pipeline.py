import asyncio
import uuid
import httpx

async def main():
    body = {
        "user_id": str(uuid.uuid4()),
        "user_profile": {
            "curiosity_domain": "Technology",
            "experience_level": "Beginner",
            "business_interests": ["E-commerce"],
            "target_region": "Global",
            "founder_setup": "Co-founder",
            "risk_tolerance": "I thrive in high-risk, high-reward situations"
        },
        "career_profile": {
            "free_day_preferences": [
                "Build or create something",
                "Solve a problem",
                "Work with technology"
            ],
            "preferred_work_types": [
                "Working with technology",
                "Analyzing data"
            ],
            "problem_solving_styles": [
                "Logical or technical problems"
            ],
            "preferred_work_environments": [
                "Remote / flexible"
            ],
            "desired_impact": [
                "Build products",
                "Innovate new ideas"
            ]
        }
    }
    
    headers = {
        "x-api-key": "7f986c28-88d1-424d-8622-776ffaff3452",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post("https://bizifyai-production.up.railway.app/pipeline/run", headers=headers, json=body)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")

asyncio.run(main())
