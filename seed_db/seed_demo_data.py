"""
==============================================================
  Bizify - Comprehensive Mock Data Seeder
==============================================================
  Covers: Auth, Admin, Users, Profiling, Ideas, Notifications,
          Teams/Groups, Partner Profiles, Billing/Plans, Skills
  All passwords: password123
==============================================================
"""
import os
import sys
import uuid
import logging
import secrets
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.user_profile import UserProfile, GuideStatus
from app.models.user_skill import UserSkill
from app.models.business import Business, BusinessStage
from app.models.idea import Idea, IdeaStatus
from app.models.notification import Notification
from app.models.partner_profile import PartnerProfile, PartnerType, ApprovalStatus
from app.models.group import Group
from app.models.group_member import GroupMember, GroupRole, GroupMemberStatus
from app.models.group_message import GroupMessage
from app.models.group_invite import GroupInvite, GroupInviteStatus
from app.models.plan import Plan

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PASSWORD = get_password_hash("password123")

# ─────────────────────────────────────────────
# Helper to build a Notification row
# ─────────────────────────────────────────────
def make_notification(user_id, title, content):
    return Notification(
        user_id=user_id,
        title=title,
        message=content,
        content=content,
        type="SYSTEM",
    )


def seed():
    db = SessionLocal()
    try:
        # ── Clean Up ──────────────────────────────────────────
        logger.info("🧹 Cleaning up old demo data...")
        for email_pattern in [
            "admin@bizify.com",
            "entrepreneur_%@bizify.com",
            "mentor_%@bizify.com",
            "supplier_%@bizify.com",
        ]:
            db.query(User).filter(User.email.like(email_pattern)).delete(synchronize_session=False)
        db.query(Plan).filter(Plan.name.like("% Plan")).delete(synchronize_session=False)
        db.commit()
        logger.info("✅ Cleanup done.\n")

        # ══════════════════════════════════════════════════════
        # 1. ADMIN
        # ══════════════════════════════════════════════════════
        logger.info("👑 Creating Admin...")
        admin = User(
            id=uuid.uuid4(), email="admin@bizify.com",
            password_hash=PASSWORD, full_name="System Admin",
            role=UserRole.ADMIN, is_active=True, is_verified=True,
        )
        db.add(admin)
        db.flush()
        logger.info(f"   ✅ admin@bizify.com / password123  (id: {admin.id})\n")

        # ══════════════════════════════════════════════════════
        # 2. ENTREPRENEURS (5)
        # ══════════════════════════════════════════════════════
        logger.info("🚀 Creating 5 Entrepreneurs...")
        entrepreneur_data = [
            ("Ahmed Ali",      "Technology",  "E-commerce",    ["Python", "Marketing"]),
            ("Sara Hassan",    "Healthcare",  "Telemedicine",  ["Design", "Business Dev"]),
            ("Omar Khaled",    "Education",   "EdTech",        ["Data Analysis", "React"]),
            ("Nour Youssef",   "Finance",     "FinTech",       ["Accounting", "Python"]),
            ("Tarek Mahmoud",  "Logistics",   "Supply Chain",  ["Operations", "SQL"]),
        ]
        entrepreneurs = []
        for i, (name, domain, interest, skills_list) in enumerate(entrepreneur_data, 1):
            e = User(
                id=uuid.uuid4(), email=f"entrepreneur_{i}@bizify.com",
                password_hash=PASSWORD, full_name=name,
                role=UserRole.ENTREPRENEUR, is_active=True, is_verified=True,
            )
            db.add(e)
            db.flush()

            # Profile with questionnaire data
            db.add(UserProfile(
                id=uuid.uuid4(), user_id=e.id,
                bio=f"Passionate {domain} entrepreneur.",
                onboarding_completed=True,
                guide_status=GuideStatus.COMPLETED,
                preferences_json={
                    "curiosity_domain": domain,
                    "experience_level": "Intermediate",
                    "business_interests": [interest],
                    "target_region": "Global",
                    "founder_setup": "Co-founder",
                    "risk_tolerance": "Moderate",
                },
                personality_json={
                    "free_day_preferences": ["Build or create something", "Solve a problem"],
                    "preferred_work_types": ["Working with technology", "Analyzing data"],
                    "problem_solving_styles": ["Logical or technical problems"],
                    "preferred_work_environments": ["Remote / flexible"],
                    "desired_impact": ["Build products", "Innovate new ideas"],
                },
            ))

            # 5 skills per entrepreneur
            for j, skill in enumerate(skills_list + ["Leadership", "Communication", "AI Tools"], 1):
                db.add(UserSkill(id=uuid.uuid4(), user_id=e.id, skill_name=skill, declared_level=j * 2))

            # 5 notifications per entrepreneur
            notifs = [
                ("Welcome to Bizify!", "Your account is set up and ready."),
                ("Profile Complete", "Great job completing your profile!"),
                ("New Idea Tip", "Ready to add your first business idea?"),
                ("Partner Available", "A new mentor just joined the platform."),
                ("Weekly Digest", "Check out the latest insights for your domain."),
            ]
            for title, content in notifs:
                db.add(make_notification(e.id, title, content))

            entrepreneurs.append(e)
            logger.info(f"   ✅ entrepreneur_{i}@bizify.com  ({name})")

        db.flush()

        # ── 5 Ideas per entrepreneur ──────────────────────────
        logger.info("\n💡 Creating Ideas (5 per entrepreneur)...")
        all_ideas = []
        idea_templates = [
            ("AI-Powered Analytics Platform",   "Use ML to provide real-time business analytics.",  IdeaStatus.VALIDATED),
            ("Smart Inventory Management",      "IoT-based solution for warehouse automation.",      IdeaStatus.DRAFT),
            ("B2B Marketplace Platform",        "Connect suppliers directly with retailers.",         IdeaStatus.DRAFT),
            ("Personalized Learning App",       "AI tutor that adapts to each student.",             IdeaStatus.VALIDATED),
            ("Green Energy Tracker",            "Help businesses measure their carbon footprint.",   IdeaStatus.DRAFT),
        ]
        for e in entrepreneurs:
            for title, desc, status in idea_templates:
                idea = Idea(
                    id=uuid.uuid4(), owner_id=e.id,
                    title=title, description=desc,
                    status=status,
                    ai_score=round(70 + 20 * (hash(title) % 10) / 10, 1),
                    budget=5000 + (hash(e.email) % 45000),
                    skills=["Python", "Design", "Marketing"],
                )
                db.add(idea)
                all_ideas.append(idea)
        db.flush()

        # ── 5 Businesses (one per entrepreneur) ───────────────
        logger.info("🏢 Creating Businesses...")
        businesses = []
        for i, e in enumerate(entrepreneurs):
            b = Business(
                id=uuid.uuid4(), owner_id=e.id,
                stage=BusinessStage.EARLY,
                context_json={
                    "name": f"Startup #{i+1} - {entrepreneur_data[i][2]}",
                    "description": f"Building the future of {entrepreneur_data[i][1]}.",
                    "type": "B2B", "industry": entrepreneur_data[i][1],
                }
            )
            db.add(b)
            db.flush()
            businesses.append(b)

        # ── Groups + Members + Messages (one group per business) ─
        logger.info("👥 Creating Groups, Members & Messages...")
        for i, (business, entrepreneur) in enumerate(zip(businesses, entrepreneurs)):
            group = Group(
                id=uuid.uuid4(), business_id=business.id,
                name=f"Core Team #{i+1}", description="Main collaboration group",
                default_role=GroupRole.VIEWER, is_chat_enabled=True,
            )
            db.add(group)
            db.flush()

            # Owner as OWNER member
            db.add(GroupMember(
                id=uuid.uuid4(), group_id=group.id, user_id=entrepreneur.id,
                role=GroupRole.OWNER, status=GroupMemberStatus.ACTIVE,
            ))

            # 5 chat messages
            messages = [
                "Hey team, let's kick off this sprint!",
                "I've just uploaded the new design mockups.",
                "Can someone review the API docs?",
                "Great progress everyone, keep it up!",
                "Meeting scheduled for Friday at 3pm.",
            ]
            for msg in messages:
                db.add(GroupMessage(
                    id=uuid.uuid4(), group_id=group.id,
                    sender_id=entrepreneur.id, content=msg,
                ))

            # 5 pending group invites
            for k in range(5):
                db.add(GroupInvite(
                    id=uuid.uuid4(), group_id=group.id,
                    email=f"invitee_{i}_{k}@example.com",
                    token=secrets.token_urlsafe(32),
                    role=GroupRole.VIEWER,
                    status=GroupInviteStatus.PENDING,
                    invited_by=entrepreneur.id,
                    expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                ))

        # ══════════════════════════════════════════════════════
        # 3. MENTORS (5)
        # ══════════════════════════════════════════════════════
        logger.info("\n🎓 Creating 5 Mentors...")
        mentor_data = [
            ("Dr. Youssef Salem",   "Business Strategy"),
            ("Prof. Mona Adel",     "Tech & Innovation"),
            ("Eng. Karim Fahmy",    "Product Management"),
            ("Dr. Laila Nasser",    "Marketing & Growth"),
            ("Mr. Hassan Sami",     "Finance & Investment"),
        ]
        mentors = []
        for i, (name, specialty) in enumerate(mentor_data, 1):
            m = User(
                id=uuid.uuid4(), email=f"mentor_{i}@bizify.com",
                password_hash=PASSWORD, full_name=name,
                role=UserRole.MENTOR, is_active=True, is_verified=True,
            )
            db.add(m)
            db.flush()

            # Partner Profile - mix of statuses for Admin testing
            status = [ApprovalStatus.PENDING, ApprovalStatus.APPROVED,
                      ApprovalStatus.REJECTED, ApprovalStatus.PENDING,
                      ApprovalStatus.APPROVED][i - 1]
            db.add(PartnerProfile(
                id=uuid.uuid4(), user_id=m.id,
                partner_type=PartnerType.MENTOR,
                company_name=f"{name} Consulting",
                description=f"Expert in {specialty} with 10+ years experience.",
                services_json={"services": [specialty, "Workshops", "1-on-1 Coaching"]},
                experience_json={"years": 10, "industries": [specialty]},
                documents_json={"files": []},
                approval_status=status,
                approved_by=admin.id if status == ApprovalStatus.APPROVED else None,
            ))

            # 5 notifications per mentor
            for title, content in [
                ("Application Received", "Your partner application is under review."),
                ("Profile Tips", "Complete your profile to get more visibility."),
                ("New Connection Request", "An entrepreneur wants to connect with you."),
                ("Platform Update", "New features have been added to the platform."),
                ("Reminder", "Don't forget to update your availability."),
            ]:
                db.add(make_notification(m.id, title, content))

            mentors.append(m)
            logger.info(f"   ✅ mentor_{i}@bizify.com  ({name}) - {status.value}")

        # ══════════════════════════════════════════════════════
        # 4. SUPPLIERS (5)
        # ══════════════════════════════════════════════════════
        logger.info("\n🏭 Creating 5 Suppliers...")
        supplier_names = [
            "TechParts Egypt", "CloudStore Co.", "RawMaterials Hub",
            "DevTools Ltd.", "LogiSupply Inc.",
        ]
        for i, name in enumerate(supplier_names, 1):
            s = User(
                id=uuid.uuid4(), email=f"supplier_{i}@bizify.com",
                password_hash=PASSWORD, full_name=name,
                role=UserRole.SUPPLIER, is_active=True, is_verified=True,
            )
            db.add(s)
            db.flush()

            db.add(PartnerProfile(
                id=uuid.uuid4(), user_id=s.id,
                partner_type=PartnerType.SUPPLIER,
                company_name=name,
                description=f"Leading supplier in the tech industry.",
                services_json={"services": ["Wholesale", "Bulk Supply", "Custom Orders"]},
                experience_json={"years": 5, "industries": ["Technology"]},
                documents_json={"files": []},
                approval_status=ApprovalStatus.PENDING,
            ))
            logger.info(f"   ✅ supplier_{i}@bizify.com  ({name})")

        # ══════════════════════════════════════════════════════
        # 5. BILLING PLANS
        # ══════════════════════════════════════════════════════
        logger.info("\n💳 Creating Billing Plans...")
        plans_data = [
            ("Free Plan",       0,    {"ideas": 3, "ai_analysis": False, "team_members": 1}),
            ("Starter Plan",    9.99, {"ideas": 10, "ai_analysis": True,  "team_members": 3}),
            ("Pro Plan",        29.99,{"ideas": 50, "ai_analysis": True,  "team_members": 10}),
            ("Business Plan",   79.99,{"ideas": -1, "ai_analysis": True,  "team_members": -1}),
            ("Enterprise Plan", 199.99,{"ideas": -1,"ai_analysis": True,  "team_members": -1, "dedicated_support": True}),
        ]
        for plan_name, price, features in plans_data:
            db.add(Plan(
                id=uuid.uuid4(), name=plan_name,
                price=price, features_json=features, is_active=True,
            ))
            logger.info(f"   ✅ {plan_name} (${price}/mo)")

        # ── Final Commit ─────────────────────────────────────
        db.commit()

        # ══════════════════════════════════════════════════════
        # SUMMARY
        # ══════════════════════════════════════════════════════
        print("\n" + "═" * 55)
        print("  🎉  Mock Data Created Successfully!")
        print("═" * 55)
        print("  All passwords: password123")
        print("─" * 55)
        print("  ADMIN")
        print("    admin@bizify.com")
        print("─" * 55)
        print("  ENTREPRENEURS (5)")
        for i in range(1, 6):
            print(f"    entrepreneur_{i}@bizify.com")
        print("─" * 55)
        print("  MENTORS (5)")
        for i in range(1, 6):
            print(f"    mentor_{i}@bizify.com")
        print("─" * 55)
        print("  SUPPLIERS (5)")
        for i in range(1, 6):
            print(f"    supplier_{i}@bizify.com")
        print("═" * 55)
        print("  API Docs: http://localhost:8000/docs")
        print("═" * 55 + "\n")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
