"""
Seed script — inserts approved marketplace partners and their categories.
Run once:  python scripts/seed_marketplace_partners.py
Idempotent: re-running updates existing rows (matched by email/name) instead of
creating duplicates.
"""
import os
import sys
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.partner_category import PartnerCategory
from app.models.partner_profile import ApprovalStatus, PartnerProfile, PartnerType
from app.models.user import User, UserRole

DEFAULT_PASSWORD = "partner123"

# ── Categories ────────────────────────────────────────────────────────────────
CATEGORIES = [
    # Mentors
    {"name": "Business Strategy",    "partner_type": PartnerType.MENTOR},
    {"name": "Fundraising & VC",     "partner_type": PartnerType.MENTOR},
    {"name": "Brand & Marketing",    "partner_type": PartnerType.MENTOR},
    {"name": "Product & Tech",       "partner_type": PartnerType.MENTOR},
    {"name": "Legal & Finance",      "partner_type": PartnerType.MENTOR},
    {"name": "Operations",           "partner_type": PartnerType.MENTOR},
    # Suppliers
    {"name": "Textiles & Fabrics",   "partner_type": PartnerType.SUPPLIER},
    {"name": "Packaging & Print",    "partner_type": PartnerType.SUPPLIER},
    {"name": "Raw Materials",        "partner_type": PartnerType.SUPPLIER},
    {"name": "Electronics & Components", "partner_type": PartnerType.SUPPLIER},
    {"name": "Food & Beverages",     "partner_type": PartnerType.SUPPLIER},
    {"name": "Office Supplies",      "partner_type": PartnerType.SUPPLIER},
    # Manufacturers
    {"name": "Apparel & Garments",   "partner_type": PartnerType.MANUFACTURER},
    {"name": "Metal Fabrication",    "partner_type": PartnerType.MANUFACTURER},
    {"name": "Plastics & Polymers",  "partner_type": PartnerType.MANUFACTURER},
    {"name": "Electronics",          "partner_type": PartnerType.MANUFACTURER},
    {"name": "Food Processing",      "partner_type": PartnerType.MANUFACTURER},
    {"name": "Furniture & Wood",     "partner_type": PartnerType.MANUFACTURER},
]

# ── Partners ──────────────────────────────────────────────────────────────────
PARTNERS = [
    # ── Real Mentors ──────────────────────────────────────────────────────────
    {
        "email": "yair.levy@bizify.com",
        "full_name": "Yair Levy",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "brain.space",
        "phone_number": "",
        "category_name": "Product & Tech",
        "linkedin_url": "https://www.linkedin.com/in/levyair/",
        "headline": "Co-founder & CEO at brain.space",
        "about_summary": (
            "Yair Levy is co-founder and CEO of brain.space, an Israeli startup developing "
            "portable EEG headsets to advance brain data insights in AI."
        ),
        "description": "Co-founder & CEO of brain.space — portable EEG & brain-data AI startup.",
        "skills_json": ["Neurotechnology", "AI", "Startup"],
        "country": "Israel",
        "services_json": ["Neurotechnology", "AI", "Startup"],
        "experience_json": [{"role": "Co-founder & CEO", "company": "brain.space"}],
    },
    {
        "email": "chris.farinacci@bizify.com",
        "full_name": "Chris Farinacci",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "SignalFire",
        "phone_number": "",
        "category_name": "Business Strategy",
        "linkedin_url": "https://www.linkedin.com/in/chrisfarinacci/",
        "headline": "Executive-in-Residence at SignalFire; Former COO at Asana",
        "about_summary": (
            "Chris Farinacci is a seasoned technology executive with over 30 years of leadership "
            "experience. He served as Chief Operating Officer at Asana, scaling the company's "
            "revenue from ~$10M to ~$500M ARR. He currently serves as an Executive-in-Residence "
            "at SignalFire."
        ),
        "description": "Former COO at Asana ($10M → $500M ARR). Now EIR at SignalFire helping founders scale.",
        "skills_json": ["Go-to-Market", "Growth Strategy", "Operations"],
        "country": "United States",
        "services_json": ["Go-to-Market", "Growth Strategy", "Operations"],
        "experience_json": [
            {"role": "COO", "company": "Asana"},
            {"role": "Executive-in-Residence", "company": "SignalFire"},
        ],
    },
    {
        "email": "conny.dorrestijn@bizify.com",
        "full_name": "Conny Dorrestijn",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "BankiFi",
        "phone_number": "",
        "category_name": "Brand & Marketing",
        "linkedin_url": "https://www.linkedin.com/in/conny-dorrestijn-prins-74b365/",
        "headline": "Founding Partner at BankiFi",
        "about_summary": (
            "Conny Dorrestijn is a fintech marketing veteran and Founding Partner of BankiFi, "
            "a UK/Netherlands open banking startup she co-founded in 2018. She has over 25 years "
            "of experience in fintech marketing and business development, and was named one of "
            "the 50 Most Influential Women in Fintech."
        ),
        "description": "25+ years in fintech marketing. Founding Partner at BankiFi. Top 50 Women in Fintech.",
        "skills_json": ["Fintech", "Open Banking", "Marketing"],
        "country": "Netherlands",
        "services_json": ["Fintech", "Open Banking", "Marketing"],
        "experience_json": [{"role": "Founding Partner", "company": "BankiFi", "since": "2018"}],
    },
    {
        "email": "dagmar.claasen@bizify.com",
        "full_name": "Dagmar van Ravenswaay Claasen",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "LUMO Labs",
        "phone_number": "",
        "category_name": "Fundraising & VC",
        "linkedin_url": "https://www.linkedin.com/in/dagmar-van-ravenswaay-claasen-ccdda74b/",
        "headline": "Senior Partner at LUMO Labs; Founder of Daxivin",
        "about_summary": (
            "Dagmar van Ravenswaay Claasen is a Senior Partner at LUMO Labs, a Netherlands-based "
            "VC fund. She is also a lawyer and the founder of Daxivin, a biological wine startup, "
            "and was a former Director at Adyen."
        ),
        "description": "Senior Partner at LUMO Labs (VC). Former Director at Adyen. Lawyer & serial founder.",
        "skills_json": ["Fintech", "Legal", "Entrepreneurship"],
        "country": "Netherlands",
        "services_json": ["Fintech", "Legal", "Entrepreneurship"],
        "experience_json": [
            {"role": "Senior Partner", "company": "LUMO Labs"},
            {"role": "Former Director", "company": "Adyen"},
        ],
    },
    {
        "email": "aaron.caradonna@bizify.com",
        "full_name": "Aaron Caradonna",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "EQ Concepts, Inc.",
        "phone_number": "",
        "category_name": "Legal & Finance",
        "linkedin_url": "https://www.linkedin.com/in/aaroncaradonna",
        "headline": "Co-Founder at EQ Concepts, Inc.",
        "about_summary": (
            "Aaron Caradonna is co-founder of EQ Concepts, Inc., a VC-backed ticketing startup. "
            "He served as General Counsel at Summit Information Solutions and has been a mentor "
            "for Techstars and gener8tor."
        ),
        "description": "Co-founder of VC-backed ticketing startup. Techstars & gener8tor mentor. Legal expertise.",
        "skills_json": ["Entrepreneurship", "Legal", "EventTech"],
        "country": "United States",
        "services_json": ["Entrepreneurship", "Legal", "EventTech"],
        "experience_json": [
            {"role": "Co-Founder", "company": "EQ Concepts, Inc."},
            {"role": "General Counsel", "company": "Summit Information Solutions"},
        ],
    },
    {
        "email": "tom.blomfield@bizify.com",
        "full_name": "Tom Blomfield",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "Y Combinator",
        "phone_number": "",
        "category_name": "Fundraising & VC",
        "linkedin_url": "https://www.linkedin.com/in/tomblomfield",
        "headline": "General Partner at Y Combinator; Co-founder of Monzo and GoCardless",
        "about_summary": (
            "Tom Blomfield is co-founder of Monzo and GoCardless, and currently a General "
            "Partner at Y Combinator. Under his leadership, Monzo raised over £500M, and "
            "he co-founded GoCardless (YC S11) as well."
        ),
        "description": "GP at Y Combinator. Co-founder of Monzo (raised £500M+) and GoCardless (YC S11).",
        "skills_json": ["Fintech", "Entrepreneurship", "Product"],
        "country": "United Kingdom",
        "services_json": ["Fintech", "Entrepreneurship", "Product"],
        "experience_json": [
            {"role": "General Partner", "company": "Y Combinator"},
            {"role": "Co-founder", "company": "Monzo"},
            {"role": "Co-founder", "company": "GoCardless"},
        ],
    },
    {
        "email": "nicolas.dessaigne@bizify.com",
        "full_name": "Nicolas Dessaigne",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "Y Combinator",
        "phone_number": "",
        "category_name": "Fundraising & VC",
        "linkedin_url": "https://www.linkedin.com/in/nicolasdessaigne",
        "headline": "General Partner at Y Combinator; Co-founder of Algolia",
        "about_summary": (
            "Nicolas Dessaigne is General Partner at Y Combinator. He co-founded Algolia, "
            "a search API platform, and served as its CEO until 2020. Algolia grew to over "
            "350 employees under his leadership."
        ),
        "description": "GP at Y Combinator. Co-founded Algolia (search API, 350+ employees).",
        "skills_json": ["Search", "APIs", "Scale-ups"],
        "country": "France",
        "services_json": ["Search", "APIs", "Scale-ups"],
        "experience_json": [
            {"role": "General Partner", "company": "Y Combinator"},
            {"role": "Co-founder & CEO", "company": "Algolia"},
        ],
    },
    {
        "email": "tyler.bosmeny@bizify.com",
        "full_name": "Tyler Bosmeny",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "Y Combinator",
        "phone_number": "",
        "category_name": "Fundraising & VC",
        "linkedin_url": "https://www.linkedin.com/in/tylerbosmeny",
        "headline": "General Partner at Y Combinator; Co-founder and former CEO of Clever",
        "about_summary": (
            "Tyler Bosmeny is General Partner at Y Combinator. He co-founded Clever, an "
            "education platform for K–12 schools, which was acquired in 2021 for $500 million. "
            "Clever achieved over 60% penetration in U.S. schools under his leadership."
        ),
        "description": "GP at Y Combinator. Co-founded Clever (EdTech, acquired $500M, 60% of US schools).",
        "skills_json": ["EdTech", "Product Management", "Scaling"],
        "country": "United States",
        "services_json": ["EdTech", "Product Management", "Scaling"],
        "experience_json": [
            {"role": "General Partner", "company": "Y Combinator"},
            {"role": "Co-founder & CEO", "company": "Clever (acquired $500M)"},
        ],
    },
    {
        "email": "brad.flora@bizify.com",
        "full_name": "Brad Flora",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "Y Combinator",
        "phone_number": "",
        "category_name": "Fundraising & VC",
        "linkedin_url": "https://www.linkedin.com/in/bradflora",
        "headline": "General Partner at Y Combinator; Co-founder of Perfect Audience",
        "about_summary": (
            "Brad Flora is a General Partner at Y Combinator and co-founder of Perfect Audience, "
            "a digital advertising platform acquired by Marin Software in 2014. He is an active "
            "angel investor and startup marketing expert."
        ),
        "description": "GP at Y Combinator. Co-founded Perfect Audience (acquired by Marin Software 2014).",
        "skills_json": ["Digital Advertising", "Growth", "Startups"],
        "country": "United States",
        "services_json": ["Digital Advertising", "Growth", "Startups"],
        "experience_json": [
            {"role": "General Partner", "company": "Y Combinator"},
            {"role": "Co-founder", "company": "Perfect Audience"},
        ],
    },
    {
        "email": "diana.hu@bizify.com",
        "full_name": "Diana Hu",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "Y Combinator",
        "phone_number": "",
        "category_name": "Fundraising & VC",
        "linkedin_url": "https://www.linkedin.com/in/diana-hu",
        "headline": "General Partner at Y Combinator; Co-founder and former CTO of Escher Reality",
        "about_summary": (
            "Diana Hu is a General Partner at Y Combinator. She co-founded Escher Reality, "
            "an AR backend company acquired by Niantic (Pokémon Go maker) in 2017. "
            "She later led data science at OnCue TV (acquired by Verizon)."
        ),
        "description": "GP at Y Combinator. Co-founded Escher Reality (acquired by Niantic). ML & AR expert.",
        "skills_json": ["Augmented Reality", "Machine Learning", "Scale-ups"],
        "country": "United States",
        "services_json": ["Augmented Reality", "Machine Learning", "Scale-ups"],
        "experience_json": [
            {"role": "General Partner", "company": "Y Combinator"},
            {"role": "Co-founder & CTO", "company": "Escher Reality (acq. Niantic)"},
        ],
    },
    {
        "email": "pete.koomen@bizify.com",
        "full_name": "Pete Koomen",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "Y Combinator",
        "phone_number": "",
        "category_name": "Fundraising & VC",
        "linkedin_url": "https://www.linkedin.com/in/petekoomen",
        "headline": "General Partner at Y Combinator; Co-founder of Optimizely",
        "about_summary": (
            "Pete Koomen is a General Partner at Y Combinator. He co-founded Optimizely, "
            "a website experimentation platform, and grew it to $100M ARR before its "
            "acquisition in 2020."
        ),
        "description": "GP at Y Combinator. Co-founded Optimizely ($100M ARR, acquired 2020).",
        "skills_json": ["A/B Testing", "Startup Growth", "Product"],
        "country": "United States",
        "services_json": ["A/B Testing", "Startup Growth", "Product"],
        "experience_json": [
            {"role": "General Partner", "company": "Y Combinator"},
            {"role": "Co-founder", "company": "Optimizely"},
        ],
    },
    {
        "email": "david.lieb@bizify.com",
        "full_name": "David Lieb",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "Y Combinator",
        "phone_number": "",
        "category_name": "Fundraising & VC",
        "linkedin_url": "https://www.linkedin.com/in/davidlieberman",
        "headline": "General Partner at Y Combinator; Co-founder of Bump",
        "about_summary": (
            "David Lieb is a General Partner at Y Combinator. He co-founded Bump, a mobile "
            "app used by 150 million users, which was acquired by Google in 2013 and whose "
            "technology later became part of Google Photos."
        ),
        "description": "GP at Y Combinator. Co-founded Bump (150M users, acquired by Google → Google Photos).",
        "skills_json": ["Mobile", "Startup", "AI"],
        "country": "United States",
        "services_json": ["Mobile", "Startup", "AI"],
        "experience_json": [
            {"role": "General Partner", "company": "Y Combinator"},
            {"role": "Co-founder", "company": "Bump (acq. Google)"},
        ],
    },
    {
        "email": "federico.travella@bizify.com",
        "full_name": "Federico Travella",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "Novicap",
        "phone_number": "",
        "category_name": "Fundraising & VC",
        "linkedin_url": "https://www.linkedin.com/in/federicotravella",
        "headline": "Founder & Executive Chairman at Novicap",
        "about_summary": (
            "Federico Travella is founder and Executive Chairman of Novicap, a fintech platform "
            "for working capital. He is a serial entrepreneur who scaled Lazada in Asia as part "
            "of Rocket Internet."
        ),
        "description": "Founder & Chairman at Novicap (fintech). Scaled Lazada in Asia with Rocket Internet.",
        "skills_json": ["FinTech", "Entrepreneurship", "Fundraising"],
        "country": "Belgium",
        "services_json": ["FinTech", "Entrepreneurship", "Fundraising"],
        "experience_json": [
            {"role": "Founder & Executive Chairman", "company": "Novicap"},
            {"role": "Scaled Operations", "company": "Lazada / Rocket Internet"},
        ],
    },
    {
        "email": "lora.kratchounova@bizify.com",
        "full_name": "Lora Kratchounova",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "Scratch Marketing + Media",
        "phone_number": "",
        "category_name": "Brand & Marketing",
        "linkedin_url": "https://www.linkedin.com/in/lorakratchounova",
        "headline": "Founder and CEO at Scratch Marketing + Media",
        "about_summary": (
            "Lora Kratchounova is founder and CEO of Scratch Marketing + Media, a tech marketing "
            "agency. She has over two decades of experience and mentors numerous startup programs, "
            "including TechStars Boston."
        ),
        "description": "Founder & CEO of Scratch Marketing. TechStars Boston mentor. 20+ years in tech marketing.",
        "skills_json": ["Marketing", "Tech Startups", "Communication"],
        "country": "United States",
        "services_json": ["Marketing", "Tech Startups", "Communication"],
        "experience_json": [
            {"role": "Founder & CEO", "company": "Scratch Marketing + Media"},
        ],
    },
    {
        "email": "nora.khalili@bizify.com",
        "full_name": "Nora Khalili",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "Independent Consultant",
        "phone_number": "",
        "category_name": "Business Strategy",
        "linkedin_url": "https://www.linkedin.com/in/norakhalili",
        "headline": "B2B Sales & Customer Success Leader; Techstars Mentor",
        "about_summary": (
            "Nora Khalili is a B2B sales and customer success executive with over 20 years in "
            "AI and SaaS. She has led sales teams through Series A/B funding rounds, serving as "
            "VP of Sales at Receipt Bank (Dext) and ID.me."
        ),
        "description": "20+ years in B2B SaaS sales. Former VP Sales at Receipt Bank & ID.me. Techstars mentor.",
        "skills_json": ["Sales", "Customer Success", "SaaS"],
        "country": "United States",
        "services_json": ["Sales", "Customer Success", "SaaS"],
        "experience_json": [
            {"role": "VP of Sales", "company": "Receipt Bank (Dext)"},
            {"role": "VP of Sales", "company": "ID.me"},
        ],
    },
    {
        "email": "steve.walsh@bizify.com",
        "full_name": "Steve Walsh",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "Hands On Angel LLC",
        "phone_number": "",
        "category_name": "Fundraising & VC",
        "linkedin_url": "https://www.linkedin.com/in/handsonangel",
        "headline": "Founder at Hands On Angel (Angel Investor); Techstars Mentor",
        "about_summary": (
            "Steve Walsh is an angel investor and Techstars Mentor-in-Residence. As founder of "
            "Hands On Angel, he has invested in and mentored over 60 startups, helping them "
            "secure millions in funding."
        ),
        "description": "Angel investor & Techstars Mentor-in-Residence. Invested in 60+ startups.",
        "skills_json": ["Angel Investing", "Mentorship", "Pitch Training"],
        "country": "United States",
        "services_json": ["Angel Investing", "Mentorship", "Pitch Training"],
        "experience_json": [
            {"role": "Founder", "company": "Hands On Angel"},
            {"role": "Mentor-in-Residence", "company": "Techstars"},
        ],
    },
    {
        "email": "nik.storonsky@bizify.com",
        "full_name": "Nikolay Storonsky",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "Revolut",
        "phone_number": "",
        "category_name": "Business Strategy",
        "linkedin_url": "https://www.linkedin.com/in/nikstoronsky",
        "headline": "Founder & CEO at Revolut",
        "about_summary": (
            "Nikolay (Nik) Storonsky is co-founder and CEO of Revolut, a UK-based fintech "
            "unicorn. Under his leadership, Revolut raised over $1 billion in funding and "
            "grew to serve millions of customers worldwide."
        ),
        "description": "Co-founder & CEO of Revolut (fintech unicorn, $1B+ raised, millions of customers).",
        "skills_json": ["Fintech", "Scaling", "Leadership"],
        "country": "United Kingdom",
        "services_json": ["Fintech", "Scaling", "Leadership"],
        "experience_json": [{"role": "Co-founder & CEO", "company": "Revolut"}],
    },
    {
        "email": "paulo.veras@bizify.com",
        "full_name": "Paulo Veras",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "99 (acquired by Didi Chuxing)",
        "phone_number": "",
        "category_name": "Fundraising & VC",
        "linkedin_url": "https://www.linkedin.com/in/pauloveras",
        "headline": "Co-founder of 99",
        "about_summary": (
            "Paulo Veras is co-founder of 99, a Brazilian ride-hailing startup that was later "
            "acquired by Didi Chuxing, marking a successful exit for the company."
        ),
        "description": "Co-founder of 99 (Brazilian ride-hailing, acquired by Didi Chuxing).",
        "skills_json": ["Ride-sharing", "Startup Growth", "Entrepreneurship"],
        "country": "Brazil",
        "services_json": ["Ride-sharing", "Startup Growth", "Entrepreneurship"],
        "experience_json": [{"role": "Co-founder", "company": "99 (acq. by Didi Chuxing)"}],
    },
    {
        "email": "shailesh.rao@bizify.com",
        "full_name": "Shailesh Rao",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "TPG Growth",
        "phone_number": "",
        "category_name": "Fundraising & VC",
        "linkedin_url": "https://www.linkedin.com/in/shailesh-rao",
        "headline": "Partner at TPG Growth",
        "about_summary": "Shailesh Rao is a Partner at TPG Growth, a leading growth equity firm.",
        "description": "Partner at TPG Growth — leading growth equity investor.",
        "skills_json": ["Investment", "Growth Equity", "Entrepreneurship"],
        "country": "United States",
        "services_json": ["Investment", "Growth Equity", "Entrepreneurship"],
        "experience_json": [{"role": "Partner", "company": "TPG Growth"}],
    },
    {
        "email": "harshita.arora@bizify.com",
        "full_name": "Harshita Arora",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "Y Combinator",
        "phone_number": "",
        "category_name": "Fundraising & VC",
        "linkedin_url": "https://www.linkedin.com/in/harshita-arora",
        "headline": "General Partner at Y Combinator; Co-founder of AtoB",
        "about_summary": (
            "Harshita Arora is a General Partner at Y Combinator. She co-founded AtoB, "
            "a fintech for trucking payments (YC S20). Previously, she built a crypto "
            "portfolio app acquired by an Indian company, earning national recognition."
        ),
        "description": "GP at Y Combinator. Co-founded AtoB (fintech for trucking payments, YC S20).",
        "skills_json": ["Fintech", "Payments", "Entrepreneurship"],
        "country": "United States",
        "services_json": ["Fintech", "Payments", "Entrepreneurship"],
        "experience_json": [
            {"role": "General Partner", "company": "Y Combinator"},
            {"role": "Co-founder", "company": "AtoB (YC S20)"},
        ],
    },
    {
        "email": "gustaf.alstromer@bizify.com",
        "full_name": "Gustaf Alströmer",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "Y Combinator",
        "phone_number": "",
        "category_name": "Fundraising & VC",
        "linkedin_url": "https://www.linkedin.com/in/gustafalstromer",
        "headline": "General Partner at Y Combinator; former Product Lead at Airbnb",
        "about_summary": (
            "Gustaf Alströmer is a General Partner at Y Combinator. He spent 4.5 years at "
            "Airbnb as a Product Lead on the Growth team, and was previously CEO & co-founder "
            "of Heysan (YC W07)."
        ),
        "description": "GP at Y Combinator. Former Product Lead (Growth) at Airbnb. Co-founder of Heysan (YC W07).",
        "skills_json": ["Growth Strategy", "Product", "Startup"],
        "country": "Sweden",
        "services_json": ["Growth Strategy", "Product", "Startup"],
        "experience_json": [
            {"role": "General Partner", "company": "Y Combinator"},
            {"role": "Product Lead, Growth", "company": "Airbnb"},
        ],
    },
    {
        "email": "garry.tan@bizify.com",
        "full_name": "Garry Tan",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "Y Combinator",
        "phone_number": "",
        "category_name": "Fundraising & VC",
        "linkedin_url": "https://www.linkedin.com/in/garrytan",
        "headline": "President & CEO of Y Combinator; Co-founder of Initialized Capital and Posterous",
        "about_summary": (
            "Garry Tan is President and CEO of Y Combinator. He co-founded Initialized Capital "
            "and was co-founder of Posterous (acquired by Twitter)."
        ),
        "description": "President & CEO of Y Combinator. Co-founded Initialized Capital & Posterous (acq. Twitter).",
        "skills_json": ["Investment", "Startup", "Product"],
        "country": "United States",
        "services_json": ["Investment", "Startup", "Product"],
        "experience_json": [
            {"role": "President & CEO", "company": "Y Combinator"},
            {"role": "Co-founder", "company": "Initialized Capital"},
        ],
    },
    {
        "email": "gal.nachum@bizify.com",
        "full_name": "Gal Nachum",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "Molecular Reality",
        "phone_number": "",
        "category_name": "Fundraising & VC",
        "linkedin_url": "https://www.linkedin.com/in/galnachum",
        "headline": "Serial Entrepreneur and Angel Investor",
        "about_summary": (
            "Gal Nachum is a serial entrepreneur (7x founder, 4 exits), angel investor, "
            "and startup mentor at Techstars and other accelerators."
        ),
        "description": "7x founder, 4 exits. Angel investor. Techstars mentor.",
        "skills_json": ["Entrepreneurship", "Angel Investing", "Mentorship"],
        "country": "Israel",
        "services_json": ["Entrepreneurship", "Angel Investing", "Mentorship"],
        "experience_json": [{"role": "Serial Founder & Angel Investor", "company": "Molecular Reality"}],
    },
    {
        "email": "nomiki.petrolla@bizify.com",
        "full_name": "Nomiki Petrolla",
        "role": UserRole.MENTOR,
        "partner_type": PartnerType.MENTOR,
        "company_name": "PDS Lab",
        "phone_number": "",
        "category_name": "Brand & Marketing",
        "linkedin_url": "https://www.linkedin.com/in/nomikipetrolla",
        "headline": "Founder & CEO at PDS Lab",
        "about_summary": (
            "Nomiki Petrolla is the founder and CEO of PDS Lab, a tech accelerator for women, "
            "and co-founder of Theanna, a social network for women founders."
        ),
        "description": "Founder & CEO of PDS Lab (tech accelerator for women). Co-founder of Theanna.",
        "skills_json": ["Entrepreneurship", "Diversity Advocacy", "Tech Incubation"],
        "country": "United States",
        "services_json": ["Entrepreneurship", "Diversity Advocacy", "Tech Incubation"],
        "experience_json": [
            {"role": "Founder & CEO", "company": "PDS Lab"},
            {"role": "Co-founder", "company": "Theanna"},
        ],
    },
    # ── Suppliers ─────────────────────────────────────────────────────────────
    {
        "email": "nile.supplies@bizify.com",
        "full_name": "Nile Supplies",
        "role": UserRole.SUPPLIER,
        "partner_type": PartnerType.SUPPLIER,
        "company_name": "Nile Supplies Co.",
        "phone_number": "+20 101 222 0301",
        "category_name": "Textiles & Fabrics",
        "linkedin_url": None,
        "description": (
            "Wholesale supplier of organic cotton, linen, and recycled "
            "polyester for fashion and home-textile brands. MOQ 200 units."
        ),
        "services_json": ["Organic cotton", "Linen", "Recycled polyester", "Low MOQ"],
        "experience_json": [{"since": "2015", "clients": "120+ brands"}],
    },
    {
        "email": "pyramid.packaging@bizify.com",
        "full_name": "Pyramid Packaging",
        "role": UserRole.SUPPLIER,
        "partner_type": PartnerType.SUPPLIER,
        "company_name": "Pyramid Packaging Ltd.",
        "phone_number": "+20 101 222 0302",
        "category_name": "Packaging & Print",
        "linkedin_url": None,
        "description": (
            "Custom eco-friendly packaging: kraft boxes, compostable mailers, "
            "and printed tissue. Lead time 10-14 days from artwork approval."
        ),
        "services_json": ["Custom boxes", "Compostable mailers", "Printed tissue"],
        "experience_json": [{"since": "2018", "monthly_volume": "300K units"}],
    },
    {
        "email": "deltaworks.mfg@bizify.com",
        "full_name": "DeltaWorks Manufacturing",
        "role": UserRole.MANUFACTURER,
        "partner_type": PartnerType.MANUFACTURER,
        "company_name": "DeltaWorks Manufacturing",
        "phone_number": "+20 102 777 0401",
        "category_name": "Apparel & Garments",
        "linkedin_url": None,
        "description": (
            "Full-service apparel manufacturer in 10th of Ramadan. Cut-and-sew, "
            "knit, and woven garments. CMT and full-package available."
        ),
        "services_json": ["Apparel CMT", "Full-package production", "Sampling"],
        "experience_json": [
            {"capacity": "80K units/month", "certifications": ["BSCI", "OEKO-TEX"]},
        ],
    },
    {
        "email": "redsea.mfg@bizify.com",
        "full_name": "Red Sea Metal Works",
        "role": UserRole.MANUFACTURER,
        "partner_type": PartnerType.MANUFACTURER,
        "company_name": "Red Sea Metal Works",
        "phone_number": "+20 102 777 0402",
        "category_name": "Metal Fabrication",
        "linkedin_url": None,
        "description": (
            "Precision metal fabrication for furniture and small appliance "
            "startups. Laser cutting, powder coating, and short-run assembly."
        ),
        "services_json": ["Laser cutting", "Powder coating", "Short-run assembly"],
        "experience_json": [{"min_order": "50 units", "lead_time": "3-5 weeks"}],
    },
]


def _upsert_category(db, *, name, partner_type) -> PartnerCategory:
    cat = (
        db.query(PartnerCategory)
        .filter(PartnerCategory.name == name, PartnerCategory.partner_type == partner_type)
        .first()
    )
    if cat:
        return cat
    cat = PartnerCategory(name=name, partner_type=partner_type)
    db.add(cat)
    db.flush()
    return cat


def _upsert_user(db, *, email, full_name, role) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.full_name = full_name
        user.role = role
        user.is_active = True
        user.is_verified = True
        return user
    user = User(
        email=email,
        password_hash=get_password_hash(DEFAULT_PASSWORD),
        full_name=full_name,
        role=role,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.flush()
    return user


def _upsert_partner_profile(db, *, user_id, data, category_id) -> PartnerProfile:
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == user_id).first()
    now = datetime.now(timezone.utc)

    if profile:
        profile.partner_type = data["partner_type"]
        profile.company_name = data["company_name"]
        profile.phone_number = data["phone_number"]
        profile.description = data["description"]
        profile.services_json = data["services_json"]
        profile.experience_json = data["experience_json"]
        profile.category_id = category_id
        profile.linkedin_url = data.get("linkedin_url")
        profile.headline = data.get("headline")
        profile.about_summary = data.get("about_summary")
        profile.skills_json = data.get("skills_json")
        profile.country = data.get("country")
        profile.approval_status = ApprovalStatus.APPROVED
        profile.approved_at = profile.approved_at or now
        return profile

    profile = PartnerProfile(
        user_id=user_id,
        partner_type=data["partner_type"],
        company_name=data["company_name"],
        phone_number=data["phone_number"],
        description=data["description"],
        services_json=data["services_json"],
        experience_json=data["experience_json"],
        category_id=category_id,
        linkedin_url=data.get("linkedin_url"),
        headline=data.get("headline"),
        about_summary=data.get("about_summary"),
        skills_json=data.get("skills_json"),
        country=data.get("country"),
        approval_status=ApprovalStatus.APPROVED,
        approved_at=now,
    )
    db.add(profile)
    return profile


def seed():
    db = SessionLocal()
    try:
        # 1. Upsert all categories
        print("Seeding categories...")
        cat_map: dict[str, PartnerCategory] = {}
        for c in CATEGORIES:
            cat = _upsert_category(db, name=c["name"], partner_type=c["partner_type"])
            cat_map[c["name"]] = cat
            print(f"  {c['partner_type'].value}: {c['name']}")
        db.flush()

        # 2. Upsert partners
        print("\nSeeding partners...")
        created, updated = 0, 0
        for entry in PARTNERS:
            existed = db.query(User).filter(User.email == entry["email"]).first() is not None
            user = _upsert_user(db, email=entry["email"], full_name=entry["full_name"], role=entry["role"])
            cat = cat_map[entry["category_name"]]
            _upsert_partner_profile(db, user_id=user.id, data=entry, category_id=cat.id)
            if existed:
                updated += 1
                print(f"  Updated: {entry['company_name']} ->[{entry['category_name']}]")
            else:
                created += 1
                print(f"  Created: {entry['company_name']} ->[{entry['category_name']}]")

        db.commit()
        print(f"\nDone. {created} partners created, {updated} updated.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
