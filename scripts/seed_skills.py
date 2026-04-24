"""
Seed script: inserts default skill categories and their predefined skills.
Run once after migration:
    python3 scripts/seed_skills.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.skill_category import SkillCategory
from app.models.predefined_skill import PredefinedSkill

SKILL_DATA = {
    "Technology & Engineering": [
        # Software Development & Programming
        "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "Go", "Rust",
        "Swift", "Kotlin", "PHP", "Ruby", "Scala", "SQL", "HTML/CSS",
        "React", "Angular", "Vue.js", "Node.js", ".NET Framework", "Spring Boot",
        "Django", "Flask", "REST API Design", "GraphQL",
        "Object-Oriented Programming (OOP)", "Functional Programming",
        "Data Structures & Algorithms", "Git Version Control",
        "Unit Testing", "Integration Testing", "Debugging & Profiling",
        "Software Architecture Patterns", "Microservices", "Containerization (Docker)",
        # Cloud & DevOps
        "Amazon Web Services (AWS)", "Microsoft Azure", "Google Cloud Platform (GCP)",
        "Kubernetes", "Infrastructure as Code (Terraform, CloudFormation)",
        "CI/CD Pipelines", "Jenkins", "GitHub Actions", "Ansible",
        "Linux System Administration", "Shell Scripting (Bash)",
        "Monitoring & Observability (Prometheus, Grafana)", "Serverless Architecture",
        # Networking & Telecommunications
        "TCP/IP & OSI Model", "Routing & Switching (BGP, OSPF)",
        "Network Configuration (Cisco, Juniper)", "Wireless Technologies (Wi-Fi, 5G/LTE)",
        "VoIP", "Software-Defined Networking (SDN)",
        "Network Troubleshooting", "Firewall Configuration",
        # Hardware & Embedded Systems
        "Embedded C", "VHDL / Verilog", "FPGA Design",
        "Microcontroller Programming (Arduino, ARM)", "PCB Design (Altium, Eagle)",
        "Real-Time Operating Systems (RTOS)", "Digital Signal Processing (DSP)",
        "IoT Architecture", "Sensor Integration",
        # Mechanical Engineering
        "CAD Modeling (SolidWorks, AutoCAD)", "Finite Element Analysis (FEA)",
        "Computational Fluid Dynamics (CFD)", "Thermodynamics", "Fluid Mechanics",
        "Heat Transfer", "HVAC System Design", "Materials Science & Selection",
        "Geometric Dimensioning & Tolerancing (GD&T)", "CNC Machining & G-code",
        "Additive Manufacturing (3D Printing)",
        # Electrical Engineering
        "Circuit Design & Analysis", "Analog Electronics", "Power Systems",
        "Control Systems", "Electromagnetics", "Power Electronics",
        "Electrical Safety Standards", "Motor Drives",
        "Photovoltaics / Renewable Energy Systems", "Schematic Capture",
        # Civil & Structural Engineering
        "Structural Analysis", "Concrete & Steel Design", "Geotechnical Engineering",
        "Surveying & GIS", "Transportation Engineering", "Water Resources Engineering",
        "Environmental Engineering", "BIM (Building Information Modeling)",
        "Construction Management",
        # Chemical & Process Engineering
        "Process Simulation (Aspen HYSYS)", "Chemical Reaction Engineering",
        "Heat & Mass Transfer", "Process Safety Management",
        "Distillation & Separation Processes", "Polymers & Materials Engineering",
        "Process Control & Instrumentation",
        # Aerospace Engineering
        "Aerodynamics", "Propulsion Systems", "Flight Mechanics & Avionics",
        "Composite Materials", "Orbital Mechanics", "Wind Tunnel Testing",
        # Robotics & Automation
        "ROS (Robot Operating System)", "Path Planning & Navigation",
        "Control Theory (PID, MPC)", "Computer Vision for Robotics",
        "PLC Programming (Ladder Logic)", "SCADA Systems", "Mechatronics",
        "Collaborative Robots (Cobots)",
        # Industrial & Systems Engineering
        "Lean Manufacturing / Six Sigma", "Operations Research",
        "Statistical Process Control (SPC)", "Reliability Engineering",
        "Human Factors & Ergonomics", "Systems Integration",
        # Engineering Design & Project Management
        "Model-Based Systems Engineering (MBSE)", "Agile/Scrum Methodologies",
        "Requirement Analysis", "Design for Manufacturability (DFM)",
        "Failure Mode & Effects Analysis (FMEA)", "Technical Writing & Documentation",
        "Cost Estimation", "Standards & Codes (ISO, ASME, IEEE)",
        # Quality & Testing
        "Metrology & Calibration", "Non-Destructive Testing (NDT)",
        "Environmental Testing", "Hardware-in-the-Loop (HIL) Testing",
        "Software Quality Assurance", "Automated Testing Frameworks",
        # Other Emerging Tech
        "Blockchain Development", "Extended Reality (AR/VR)",
        "Quantum Computing Fundamentals", "Edge Computing", "Digital Twin Technology",
    ],

    "Data & Analytics": [
        # Statistics & Mathematics
        "Descriptive Statistics", "Inferential Statistics", "Hypothesis Testing",
        "ANOVA", "Chi-Square Test", "Multivariate Analysis", "Survival Analysis",
        "Time Series Analysis", "Forecasting Techniques", "Regression Modeling",
        "Logistic Regression", "Factor Analysis", "Cluster Analysis",
        "Association Rules (Market Basket Analysis)", "Principal Component Analysis (PCA)",
        "Non-parametric Tests", "A/B Testing & Experimentation", "Statistical Power Analysis",
        "Bayesian Statistics", "Monte Carlo Simulation",
        "Advanced Regression (Ridge, Lasso, Elastic Net)",
        "Time Series Modeling (ARIMA, SARIMA, Prophet)", "Outlier Detection",
        "Missing Data Imputation",
        
        # Data Manipulation & Querying
        "SQL (Advanced Joins, Window Functions, CTEs)", "PL/SQL or T-SQL (Stored Procedures)",
        "Python (Pandas, NumPy)", "R (Tidyverse, dplyr, ggplot2)",
        "Advanced Excel (Power Query, Power Pivot, VBA)", "Pivot Tables",
        "Advanced Lookup Functions (XLOOKUP, INDEX-MATCH)", "DAX (for Power BI & Excel)",
        "MDX (for Cubes)", "Data Cleaning / Wrangling", "Exploratory Data Analysis (EDA)",
        "Tidy Data Principles", "Regular Expressions", "Data Transformation",
        "Flat File Processing (CSV, JSON, Parquet)", "Web Scraping",
        "Data Extraction via APIs",

        # Data Architecture & Modeling
        "Dimensional Modeling (Star/Snowflake Schema)", "Data Vault Modeling",
        "Normalization / Denormalization", "Graph Data Modeling",
        "Data Warehousing (Kimball/Inmon)", "Data Lakes",
        "Lakehouse Architecture (Delta Lake, Iceberg)", "ETL (Extract, Transform, Load)",
        "ELT (Extract, Load, Transform)", "Change Data Capture (CDC)",
        "ETL Tools (Informatica, Talend, SSIS)", "Data Pipelines",
        "Orchestration (Apache Airflow, Prefect, Dagster)",
        "Apache Kafka / Kinesis (Data Streaming)", "Stream Processing (Spark Streaming, Flink)",
        "Apache Spark (PySpark)", "Hadoop Ecosystem (Hive, HDFS)",
        "Relational Databases (PostgreSQL, MySQL, SQL Server)",
        "NoSQL Databases (MongoDB, Cassandra)", "Time Series Databases (InfluxDB, TimescaleDB)",
        "Graph Databases (Neo4j, GraphDB)", "Query Optimization & Indexing",
        "Execution Plan Analysis", "Materialized Views", "Columnar Storage",
        "Data Virtualization (Denodo)", "Data Mesh Architecture",

        # Cloud & Big Data Platforms
        "AWS Analytics (Redshift, Glue, EMR, Athena)",
        "Azure Analytics (Synapse, Data Factory, Databricks)",
        "GCP Analytics (BigQuery, Dataflow, Dataproc)", "Snowflake", "Databricks",

        # Visualization & Business Intelligence
        "Google Looker / LookML", "Tableau (Calculations, LODs, Table Prep)",
        "Power BI (Measures, Modeling, Service)", "Qlik Sense / QlikView",
        "Python Visualization Libraries (Matplotlib, Seaborn, Plotly)", "ggplot2 (R)",
        "D3.js (Custom Web Charts)", "Dashboard Design", "Data Storytelling",
        "KPI Definition & Design", "Funnel Analysis", "Cohort Analysis",
        "RFM Segmentation", "Churn Analysis", "Customer Lifetime Value (CLV) Modeling",
        "Attribution Modeling", "Sensitivity Analysis",
        "Geospatial Analysis (GIS, PostGIS, GeoPandas)",

        # Text & Advanced Analytics
        "NLP for Analytics (NER, Topic Modeling)", "Sentiment Analysis",
        "Text Mining", "Network / Graph Analytics", "Image Analytics Basics",

        # Data Governance & Quality
        "Master Data Management (MDM)", "Data Quality (Profiling, Cleansing Rules)",
        "Metadata Management", "Data Catalog (Collibra, Alation)", "Data Lineage",
        "Data Privacy (GDPR, CCPA Compliance)", "Analytical Data Security (Encryption, Masking)",
        "Anonymization / Pseudonymization", "Data Ethics & Bias Detection",
        "Data Governance Frameworks",

        # Machine Learning for Analytics
        "Feature Engineering", "Feature Selection",
        "Model Evaluation (Confusion Matrix, ROC, Precision-Recall)", "Cross-Validation",
        "Hyperparameter Tuning", "Predictive ML (Random Forest, XGBoost, LightGBM)",
        "Unsupervised ML (K-Means, DBSCAN, Hierarchical)",
        "Dimensionality Reduction (t-SNE, UMAP)", "Model Deployment as API",
        "Model Monitoring / Drift Detection",

        # Data Operations & Lifecycle
        "MLOps for Analytics", "dbt (Data Build Tool)", "Data Testing (Great Expectations)",
        "DataOps", "Data Integration (APIs, Messaging)",
        "Basic Recommendation Systems (Collaborative Filtering)",
        "Real-Time Analytics & Dashboards", "Data Lifecycle Management",
        "Automated Job Scheduling",

        # Business & Traditional BI
        "Financial & Budgeting Analytical Modeling (NPV, IRR, Risk Analysis)",
        "Traditional BI Tools (MicroStrategy, SAP BO)", "Augmented Analytics",

        # Project & Process Skills
        "Analytical Requirements Gathering", "CRISP-DM Methodology",
        "Stakeholder Communication", "Agile/Scrum for Data Projects",
        "Technical Writing for Analytics"
    ],

    "Security, Defense & Emergency": [
        "Network Security", "Ethical Hacking / Penetration Testing",
        "Cryptography", "Identity & Access Management (IAM)",
        "Security Information & Event Management (SIEM)",
        "Vulnerability Assessment", "Incident Response", "Cloud Security",
        "Secure Coding Practices", "Digital Forensics",
    ],

    "Skilled Trades & Manufacturing": [
        "Injection Molding", "Welding & Fabrication",
        "Industrial Robotics Programming", "Value Stream Mapping",
        "Production Line Design", "Just-in-Time (JIT) Manufacturing",
    ],

    "Healthcare & Medical": [
        # Clinical Foundation Skills
        "Patient History Taking", "Physical Examination (General & Systemic)",
        "Vital Signs Measurement & Interpretation (BP, HR, RR, Temp)",
        "Auscultation (Heart, Lung, Bowel Sounds)", "Palpation & Percussion",
        "Neurological Examination (Cranial Nerves, Reflexes)", "Mental Status Examination",
        "Clinical Documentation (SOAP Notes)", "Differential Diagnosis Formulation",
        "Diagnostic Reasoning", "Clinical Decision-Making", "Triage & Prioritization",
        "Pain Assessment", "Nutritional & Hydration Assessment",
        "Skin & Wound Assessment", "Functional Capacity Evaluation",

        # Emergency & Critical Care
        "Basic Life Support (BLS)", "Advanced Cardiac Life Support (ACLS)",
        "Pediatric Advanced Life Support (PALS)", "Neonatal Resuscitation (NRP)",
        "First Aid & Hemorrhage Control", "Airway Management (OPA, NPA, Suctioning)",
        "Endotracheal Intubation", "Defibrillation & Cardioversion",
        "Central Line Insertion & Management", "Arterial Blood Gas (ABG) Sampling & Interpretation",
        "Emergency Thoracentesis / Chest Tube", "Rapid Sequence Induction (RSI)",
        "Trauma Assessment (Primary & Secondary Survey)", "Septic Shock Management",

        # Nursing & Direct Patient Care
        "Medication Administration (Oral, IV, IM, SC, PR)", "IV Cannulation & Venipuncture",
        "Infusion Pump Programming", "Blood Transfusion Administration",
        "Wound Dressing & Debridement", "Stoma & Ostomy Care",
        "Catheterization (Urinary, Suprapubic)", "Nasogastric (NG) / Orogastric Tube Insertion",
        "Enteral & Parenteral Nutrition Management", "Patient Positioning & Mobilization",
        "Pressure Ulcer Prevention", "Infection Prevention & Control (Hand Hygiene, PPE)",
        "Sterile Technique & Aseptic Non-Touch", "Isolation Precautions (Contact, Droplet, Airborne)",
        "Specimen Collection (Blood, Urine, Sputum, CSF)", "Vital Signs Monitoring & Telemetry Interpretation",
        "Fall Risk Assessment & Prevention", "End-of-Life / Palliative Care Basics",
        "Pediatric & Geriatric Care Nuances",

        # Diagnostic & Laboratory Skills
        "Venipuncture & Phlebotomy", "Capillary Blood Sampling",
        "Hematology & Coagulation Testing", "Microbiology Specimen Processing (Gram Stain, Culture)",
        "Point-of-Care Testing (POCT) - Glucose, INR, HbA1c", "Rapid Diagnostic Tests (Strep, HIV, Pregnancy)",
        "Histopathology & Cytology Sample Preparation", "Clinical Chemistry Analysis (Electrolytes, Enzymes)",
        "Molecular Diagnostics (PCR, Next-Gen Sequencing basics)", "Immunology & Serology Techniques (ELISA)",
        "Blood Banking & Crossmatching",

        # Imaging & Radiology
        "X-Ray Interpretation (Chest, MSK, Abdomen)", "Computed Tomography (CT) Interpretation",
        "Magnetic Resonance Imaging (MRI) Basics", "Ultrasound (FAST, Obstetric, Vascular)",
        "Echocardiography (TTE, TEE)", "Mammography", "Nuclear Medicine (PET, SPECT)",
        "Fluoroscopy Procedures", "Radiation Safety & Protection",
        "Contrast Administration & Allergy Management",

        # Surgical & Procedural Skills
        "Basic Suturing & Wound Closure", "Surgical Instrument Identification",
        "Scrubbing, Gowning, and Gloving (Sterile)", "Minor Surgical Procedures (Incision & Drainage, Biopsy)",
        "Endoscopic Techniques (Gastroscopy, Colonoscopy - awareness)", "Laparoscopic / Robotic Surgery Basics",
        "Anesthesia Monitoring (Depth, Paralysis)", "Post-Operative Pain Management",
        "Drain & Catheter Removal",

        # Pharmacology & Therapeutics
        "Pharmacokinetics & Pharmacodynamics", "Prescribing & Deprescribing",
        "Drug Interaction Checking", "IV Fluid & Electrolyte Management",
        "Antimicrobial Stewardship", "Chemotherapy & Biologics Administration",
        "Immunization & Vaccine Management", "Controlled Substance Handling",
        "Transfusion Medicine & Hemotherapy",

        # Medical Specialty Knowledge (Core Skill Areas)
        "ECG Interpretation (12-Lead, Arrhythmias)", "Spirometry & Pulmonary Function Tests",
        "Insulin & Diabetes Management", "Hypertension & Cardiovascular Risk Management",
        "Stroke Assessment (NIHSS)", "Obstetric & Prenatal Examination",
        "Pediatric Growth & Development Milestones", "Dermatological Lesion Recognition",
        "Musculoskeletal Joint Examination", "Ophthalmoscopy & Visual Acuity Testing",
        "Otoscopy & Hearing Screening", "Psychiatric Interview & Risk Assessment",

        # Allied Health & Rehabilitative Skills
        "Physiotherapy Exercise Prescription", "Gait & Mobility Assessment",
        "Manual Therapy & Mobilization", "Occupational Therapy ADL Training",
        "Cognitive Rehabilitation", "Speech & Swallowing Therapy (Dysphagia Assessment)",
        "Audiometry & Hearing Aid Fitting", "Dietetic Assessment & Meal Planning",
        "Orthotics & Prosthetics Fitting", "Respiratory Therapy (Nebulization, Chest PT)",
        "Cardiac Rehabilitation",

        # Mental Health & Therapeutic Communication
        "Active Listening & Therapeutic Communication", "De-escalation Techniques",
        "Cognitive Behavioral Therapy (CBT) Basics", "Dialectical Behavior Therapy (DBT) Skills",
        "Crisis Intervention", "Suicide Risk Assessment & Prevention",
        "Substance Use Screening & Brief Intervention", "Psychoeducation Delivery",
        "Mindfulness-Based Interventions",

        # Preventive Medicine & Public Health
        "Screening Program Implementation (Cancer, HTN, DM)", "Epidemiology & Outbreak Investigation",
        "Vaccination Campaign Management", "Health Education & Promotion",
        "Community Health Needs Assessment", "Environmental Health Risk Assessment",
        "Public Health Surveillance (COVID, Influenza etc.)", "Contact Tracing",
        "Health Policy Advocacy",

        # Healthcare Administration & Management
        "Healthcare Compliance (HIPAA, GDPR for health)", "Medical Coding (ICD, CPT, HCPCS)",
        "Medical Billing & Claims Processing", "Electronic Health Record (EHR) Navigation (Epic, Cerner)",
        "Health Informatics & Data Analytics", "Clinical Workflow Optimization",
        "Patient Scheduling & Flow", "Medical Staff Credentialing",
        "Risk Management & Root Cause Analysis", "Quality Improvement (QI) Methodologies",
        "Hospital Operations & Throughput", "Supply Chain for Medical Equipment/Pharma",
        "Health Economics & Cost-Effectiveness Analysis", "Medical Legal Documentation",

        # Health Technology & Digital Health
        "Telemedicine Platform Use", "Digital Health App Design / Evaluation",
        "AI in Diagnostic Support", "Implantable & Wearable Device Management",
        "Genomics & Personalized Medicine Basics", "mHealth & Remote Patient Monitoring",
        "Cybersecurity Awareness for Health Data",

        # Research & Evidence-Based Practice
        "Clinical Research Methodology", "Biostatistics for Medical Research",
        "Systematic Review & Meta-Analysis", "Critical Appraisal of Literature",
        "Informed Consent Process", "Good Clinical Practice (GCP) Guidelines",
        "Ethics Committee / IRB Procedures", "Grant Writing for Healthcare Research",

        # Legal, Ethical & Professional
        "Medical Ethics (Autonomy, Beneficence, Non-maleficence, Justice)",
        "End-of-Life Decision Making (Advance Directives, DNR)", "Capacity Assessment & Informed Consent",
        "Patient Confidentiality & Data Sharing", "Mandatory Reporting (Abuse, Infectious Diseases)",
        "Professional Boundaries", "Cultural Competency in Healthcare",
        "Interprofessional Collaboration (TeamSTEPPS)",

        # Education & Training
        "Clinical Teaching & Precepting", "Simulation Scenario Design & Facilitation",
        "Patient Education Materials Development", "Peer Review & Case Presentation",
        "Continuing Medical Education (CME) Planning",
    ],

    "Management & Operations": [
        # General Management & Leadership
        "Strategic Vision & Mission Setting", "Organizational Design & Structure",
        "Decision-Making Frameworks", "Delegation & Empowerment",
        "Cross-Functional Team Leadership", "Conflict Resolution & Mediation",
        "Negotiation & Influence", "Coaching & Mentoring", "Succession Planning",
        "Performance Management (Reviews, PIPs)", "Goal Setting (SMART, OKRs)",
        "Talent Management & Development", "Emotional Intelligence (EQ)",
        "Motivation & Engagement Techniques", "Diversity, Equity & Inclusion (DEI) Strategy",
        "Ethical Leadership & Compliance", "Corporate Governance",
        "Board & Investor Relations",

        # Project & Program Management
        "Project Planning & Scheduling (Gantt, Milestones)",
        "Agile Methodologies (Scrum, Kanban, SAFe)", "Waterfall Project Management",
        "Critical Path Method (CPM)", "Resource Allocation & Leveling",
        "Risk Identification & Mitigation in Projects",
        "Scope & Change Request Management", "Stakeholder Communication Plans",
        "Project Budgeting & Cost Control", "Earned Value Management (EVM)",
        "Project Management Software (MS Project, Jira, Asana)",
        "PMP / PRINCE2 Methodologies", "Program Governance & Roadmapping",
        "Portfolio Management & Prioritization", "Benefits Realization Tracking",
        "Vendor & Contract Management in Projects",

        # Process Improvement & Quality
        "Lean Management (5S, Kaizen, VSM)", "Six Sigma (DMAIC, DMADV, Statistical Tools)",
        "Lean Six Sigma Belts (Yellow, Green, Black)", "Total Quality Management (TQM)",
        "Business Process Reengineering (BPR)", "Root Cause Analysis (5 Whys, Fishbone)",
        "Failure Mode & Effects Analysis (FMEA)", "Standard Operating Procedures (SOPs)",
        "Work Instruction Development", "Statistical Process Control (SPC)",
        "ISO Quality Standards (9001, 14001)", "Continuous Improvement Culture",
        "Benchmarking & Best Practices", "Process Mining & Analysis",

        # Supply Chain Management
        "Supply Chain Strategy & Design", "Procurement & Strategic Sourcing",
        "Supplier Relationship Management (SRM)", "Contract Negotiation & Management",
        "Inventory Optimization (EOQ, Safety Stock)", "Demand Planning & Forecasting",
        "Sales & Operations Planning (S&OP)", "Logistics & Distribution Network Design",
        "Transportation Management (TMS)", "Warehouse Management (WMS)",
        "Last-Mile Delivery", "Reverse Logistics & Returns",
        "Global Trade & Customs Compliance", "Supply Chain Risk & Resilience",
        "Cold Chain Management", "Sustainable Supply Chain / Green Logistics",

        # Operations Management
        "Capacity Planning & Utilization", "Production Scheduling & Sequencing",
        "Queue Management & Bottleneck Analysis", "Facility Layout & Design",
        "Line Balancing", "Total Productive Maintenance (TPM)",
        "Overall Equipment Effectiveness (OEE)", "Manufacturing Execution Systems (MES)",
        "Materials Requirement Planning (MRP/MRP II)", "Kanban & Pull Systems",
        "Just-in-Time (JIT) Manufacturing", "Worker Safety & OSHA Compliance",
        "Ergonomics & Workplace Safety Design", "Environmental Health & Safety (EHS) Management",
        "Service Operations Design", "Workforce Planning & Shift Scheduling",
        "Operational Auditing", "Cost of Quality & Waste Reduction",

        # Service & Customer Operations
        "Customer Experience (CX) Design", "Service Level Agreement (SLA) Negotiation & Monitoring",
        "Contact Center Management (KPIs, AHT, FCR)", "Net Promoter Score (NPS) & CSAT Analysis",
        "Customer Journey Mapping", "Field Service Management",
        "Incident & Problem Management (ITIL)", "IT Service Management (ITSM) Frameworks",

        # Strategic Performance & Analytics
        "Balanced Scorecard Development", "Key Performance Indicator (KPI) Selection & Tracking",
        "Dashboard & Reporting Development (Tableau, Power BI)",
        "Business Intelligence for Operations", "Data-Driven Decision Making",
        "Operational Efficiency Ratios", "Cost-Benefit Analysis",
        "P&L Analysis for Operations", "Activity-Based Costing (ABC)",
        "Management by Objectives (MBO)",

        # Change & Transformation
        "Change Management Models (ADKAR, Kotter)", "Stakeholder Impact Assessment",
        "Communication Strategy for Change", "Training & Enablement Programs",
        "Cultural Transformation", "Organizational Readiness Assessment",
        "Resistance Management", "Post-Merger Integration (PMI)",
        "Digital Transformation in Operations", "Automation Strategy (RPA, AI Implementation)",

        # People Operations & HR Management
        "Recruitment & Selection Processes", "Onboarding & Orientation Design",
        "Learning & Development (L&D) Programs", "Competency Matrix & Skills Mapping",
        "Compensation & Benefits Structuring", "Payroll & HRIS Management",
        "Employee Relations & Grievance Handling", "Labor Law & Union Negotiations",
        "Workplace Investigation", "HR Analytics & People Metrics",
        "Employee Retention Strategies", "Remote/Hybrid Work Policy Design",

        # Finance & Budgeting for Operations
        "Operational Budgeting (OPEX vs CAPEX)", "Zero-Based Budgeting (ZBB)",
        "Variance Analysis (Plan vs. Actual)", "Business Case Justification",
        "Capital Expenditure (CAPEX) Approval Process", "Working Capital Optimization",

        # Risk & Compliance
        "Operational Risk Management (ORM)", "Business Continuity Planning (BCP)",
        "Disaster Recovery Planning (DRP)", "Crisis Management & Communication",
        "Internal Controls & Segregation of Duties", "Regulatory Compliance (Industry-specific)",
        "Audit Preparation & Management", "Information Security Operations Basics",
        "Physical Security & Asset Protection",

        # Administrative & Facility Management
        "Office & Facility Space Planning", "Lease & Property Management",
        "Energy & Sustainability Management", "Security & Access Control Systems",
        "Travel & Expense Policy Management", "Vendor & Supplier Performance Reviews",
        "Records Management & Archiving",

        # Specialized Operations Fields
        "Lean Services (Healthcare, Banking, etc.)", "Clinical/Medical Operations Management",
        "Aviation/Transport Operations Management", "Hospitality Operations Management",
        "Retail Operations (Store, E-commerce)", "Construction Operations & Site Management",
        "Call Center WFM (Workforce Management)", "Field Operations & Dispatch Management",
        "Fleet Management & Telematics",

        # Soft Skills & Interpersonal in Ops
        "Cross-Cultural Communication", "Managing Remote Teams",
        "Meeting Facilitation & Workshop Design", "Time Management & Prioritization",
        "Stress & Burnout Management", "Persuasive Communication & Buy-in",
        "Problem Solving & Critical Thinking", "Negotiation Skills (Internal & External)",
    ],

    "Business & Finance": [
        # Accounting & Financial Reporting
        "Financial Accounting Standards (GAAP, IFRS)", "Managerial Accounting",
        "General Ledger Management", "Accounts Payable / Receivable",
        "Payroll Processing", "Bank Reconciliation", "Chart of Accounts Design",
        "Month-End / Year-End Close", "Consolidation of Financial Statements",
        "Revenue Recognition", "Lease Accounting", "Fixed Asset Accounting",
        "Tax Preparation & Filing (Corporate & Indirect)",
        "Cost Accounting (Job Order, Process, Activity-Based)",
        "Variance Analysis (Budget vs. Actual)", "Break-Even Analysis",
        "Transfer Pricing", "Inventory Valuation (FIFO, LIFO, Weighted Average)",
        "Auditing (Internal & External)", "SOX / Internal Controls Compliance",
        "Forensic Accounting", "Financial Statement Analysis (Ratio, Common-Size)",
        
        # Financial Analysis & Planning
        "Budgeting & Forecasting", "Rolling Forecasts", "Long-Range Financial Planning",
        "Financial Modeling (3-Statement)", "Discounted Cash Flow (DCF) Analysis",
        "Net Present Value (NPV) & IRR", "Sensitivity & Scenario Analysis",
        "Capital Budgeting", "Business Valuation (DCF, Comps, Precedent Transactions)",
        "Leveraged Buyout (LBO) Modeling", "Merger & Acquisition (M&A) Accretion/Dilution",
        "Working Capital Management", "Cash Flow Forecasting",
        "EBITDA & Free Cash Flow Analysis", "Unit Economics (CAC, LTV, Churn)",
        "Return on Investment (ROI) Analysis", "Profitability Analysis (Product, Customer, Channel)",
        "P&L Management", "KPI Dashboard Design (Financial)",
        
        # Corporate Finance & Treasury
        "Capital Structure Optimization", "Debt & Equity Financing",
        "Credit Analysis & Risk Rating", "Loan Covenant Monitoring",
        "Treasury Management Systems (TMS)", "Cash Management & Liquidity Planning",
        "Foreign Exchange (FX) Risk Management", "Interest Rate Hedging",
        "Trade Finance (Letters of Credit)", "Dividend Policy & Share Buybacks",
        "Investor Relations & Roadshow Preparation",
        
        # Investment & Portfolio Management
        "Modern Portfolio Theory (MPT)", "Asset Allocation", "Equity Research & Analysis",
        "Fixed Income Analysis (Duration, Convexity)", "Derivatives Pricing & Strategies",
        "Alternative Investments (Private Equity, Hedge Funds)",
        "Real Estate Valuation (Cap Rates, DCF)", "Technical Analysis (Candlesticks, Indicators)",
        "Fundamental Analysis", "Portfolio Performance Attribution",
        "Risk-Adjusted Return Metrics (Sharpe, Sortino)",
        "Trading & Order Management Systems (OMS/EMS)",
        "ESG / Sustainable Investing Analysis", "Wealth Management & Personal Finance Planning",
        
        # Risk Management & Compliance
        "Enterprise Risk Management (ERM)", "Market Risk (VaR, CVaR)",
        "Credit Risk Modeling", "Operational Risk Management", "Liquidity Risk",
        "Regulatory Compliance (Basel, Dodd-Frank, MiFID)",
        "Anti-Money Laundering (AML) / KYC", "Model Risk Management",
        "Business Continuity Planning", "Insurance & Claims Management",
        
        # Marketing & Sales
        "Digital Marketing (SEO, SEM, PPC)", "Social Media Marketing",
        "Content Marketing & Storytelling", "Brand Strategy & Positioning",
        "Customer Relationship Management (CRM)", "Sales Pipeline Management",
        "Pricing Strategy & Optimization", "Marketing Automation (HubSpot, Marketo)",
        "Web Analytics (Google Analytics, Adobe Analytics)",
        "Conversion Rate Optimization (CRO)", "Net Promoter Score (NPS) Analysis",
        "Product-Market Fit Assessment", "Lead Generation & Nurturing",
        "Category Management",

        # Economics & Data
        "Macroeconomics Analysis (GDP, Inflation, Interest Rates)",
        "Microeconomics (Supply/Demand, Elasticity)",
        "Econometrics & Statistical Modeling for Business",
        "Financial Data Analysis with Python/R", "Bloomberg Terminal Proficiency",
        "FactSet / Capital IQ", "Data Visualization for Finance (Tableau, Power BI)",
        "SQL for Financial Data Extraction", "Advanced Excel (Macros, VBA, Power Query)",
        "Business Intelligence (BI) Tool Deployment",

        # Entrepreneurship & Innovation
        "Lean Startup Methodology", "Business Model Canvas",
        "Fundraising / Venture Capital Pitch Preparation", "Cap Table Management",
        "Customer Development & Discovery", "Intellectual Property Strategy",
        "Product Lifecycle Management", "Market Entry Strategy",
        "Innovation Funnel Management",
    ],
    "Design & Creativity": [
        # Design Foundations & Principles
        "Design Thinking Process", "Visual Hierarchy", "Balance & Symmetry",
        "Contrast & Emphasis", "Proportion & Scale", "Unity & Harmony",
        "Gestalt Principles", "White Space & Minimalism", "Design Systems Creation",
        "Design Critique & Feedback",

        # Graphic Design & Visual Communication
        "Logo Design", "Brand Guidelines Creation", "Corporate Identity Design",
        "Iconography & Pictograms", "Infographic Design", "Layout & Grid Systems",
        "Publication Design (Magazines, Books)", "Editorial Design",
        "Poster & Billboard Design", "Brochure & Flyer Design",
        "Stationery & Collateral Design", "Social Media Graphic Design",
        "Banner & Display Ad Design", "Visual Storytelling", "Art Direction",

        # Typography & Lettering
        "Typeface Selection & Pairing", "Typographic Hierarchy",
        "Kerning, Leading & Tracking", "Custom Type Design (Font Creation)",
        "Hand Lettering", "Calligraphy", "Expressive Typography", "Variable Fonts",

        # Color Theory & Application
        "Color Theory Fundamentals", "Color Psychology", "Palette Creation & Harmonization",
        "Color Management (CMYK, RGB, Pantone)", "Accessibility & Color Contrast (WCAG)",
        "Monochromatic & Duotone Effects",

        # Branding & Identity
        "Brand Strategy & Positioning", "Naming & Nomenclature",
        "Visual Identity Systems", "Brand Voice & Tone", "Rebranding & Refresh",
        "Brand Architecture", "Style Guide Documentation", "Brand Experience Design",

        # UX/UI & Product Design
        "User Research (Interviews, Surveys)", "Persona Development",
        "User Journey Mapping", "Empathy Mapping", "Information Architecture (IA)",
        "Wireframing (Low & High Fidelity)", "Interactive Prototyping",
        "Usability Testing", "Heuristic Evaluation", "Accessibility Design (A11y)",
        "Interaction Design (IxD)", "Micro-interaction Design",
        "Mobile-First & Responsive Design", "Design System (Component Libraries)",
        "Storyboarding for UX", "Service Design Blueprinting",

        # Web & Digital Design
        "UI Design for Web & Apps", "Responsive Layouts (Flexbox/Grid)",
        "Landing Page Design", "Email Newsletter Design", "E-commerce Design",
        "Dashboard & Data UI Design", "Portfolio Website Design",
        "Basic HTML/CSS for Designers",

        # Motion Graphics & Animation
        "2D Animation (After Effects)", "3D Motion Graphics (Cinema 4D, Blender)",
        "Kinetic Typography", "Title Sequence Design", "UI Animation & Transitions",
        "Explainer Video Production", "Stop Motion", "Character Animation",
        "VFX & Compositing Basics", "Lottie Animations for Web/Apps",

        # Illustration & Drawing
        "Digital Illustration (Procreate, Illustrator)", "Vector Illustration",
        "Raster Painting & Shading", "Character Design", "Environment & Background Art",
        "Storyboarding for Film/Animation", "Technical Illustration",
        "Medical/Scientific Illustration", "Children's Book Illustration",
        "Fashion Illustration (Croquis)", "Architectural Sketching",

        # Photography & Image Making
        "Digital Photography (Composition & Lighting)", "Studio & Portrait Photography",
        "Product Photography", "Architectural & Interior Photography",
        "Photo Editing & Retouching (Photoshop, Lightroom)", "Color Grading",
        "Photo Manipulation & Compositing", "Food Photography",
        "Fashion Photography", "Aerial/Drone Photography", "Stock Image Curation",

        # Print & Production Design
        "Pre-press & Print File Preparation", "Die-Cutting & Finishing Techniques",
        "Print Production Management", "Large Format Printing", "Screen Printing",
        "Risograph & Specialty Printing", "Packaging Dielines & Structural Design",
        "Sustainable Print Practices",

        # Packaging Design
        "Structural Packaging Design", "Label Design",
        "Consumer Packaged Goods (CPG) Design", "Unboxing Experience Design",
        "Point-of-Sale Display Design", "Folding Carton & Corrugated Design",

        # Industrial & Product Design
        "Design Sketching & Rendering", "3D CAD Modeling (SolidWorks, Fusion 360)",
        "Ergonomic Design", "Concept Development & Prototyping",
        "Material & Manufacturing Knowledge", "User-Centered Industrial Design",
        "CMF Design (Color, Material, Finish)", "Sustainable Product Design",

        # Interior & Spatial Design
        "Space Planning & Layout", "Furniture, Fixtures & Equipment (FF&E) Specification",
        "Lighting Design", "Materials & Finishes Selection",
        "3D Rendering (V-Ray, Enscape)", "Mood & Material Boards", "Residential Design",
        "Retail & Hospitality Design", "Exhibition & Trade Show Booth Design",
        "Signage & Wayfinding Design",

        # Architecture & Environmental Design
        "Architectural Drafting (AutoCAD, Revit)", "BIM (Building Information Modeling)",
        "Site Planning", "Conceptual Architecture Design", "Landscape Design",
        "Environmental Graphics", "Urban Planning Concepts",

        # Fashion & Textile Design
        "Fashion Design & Conceptualization", "Technical Flats & Spec Sheets",
        "Pattern Making & Draping", "Sewing & Garment Construction",
        "Textile Print Design", "Surface Pattern Design",
        "Embroidery & Embellishment", "Accessory Design",
        "Shoe & Footwear Design", "Costume Design",

        # Game & Interactive Design
        "Game Art & Concept Design", "Level Design", "Character Modeling & Texturing",
        "Environment Modeling", "Prop Design", "Game UI/HUD Design",
        "Asset Creation & Optimization", "Interactive Storytelling",

        # Sound & Audio Design
        "Sound Design for Video/Animation", "Foley & Audio Effects",
        "Music Composition & Scoring for Media", "Audio Editing & Mixing (Audacity, Audition)",
        "Podcast Intro & Outro Creation",

        # Writing & Content Creation
        "Copywriting (Advertising, Web)", "Creative Writing",
        "Storytelling & Narrative Development", "Content Strategy for Creatives",
        "Scriptwriting (Video, Animation, Commercial)", "Editing & Proofreading",
        "UX Writing & Microcopy", "Tone of Voice Definition",

        # Creative Direction & Concept
        "Creative Concept Development", "Moodboarding & Visual Research",
        "Campaign Ideation", "Pitching Creative Ideas",
        "Cross-Disciplinary Art Direction", "Client Presentation Skills",
        "Creative Brief Writing", "Trend Forecasting & Cultural Research",

        # Tools & Software Mastery
        "Adobe Creative Suite (Photoshop, Illustrator, InDesign)",
        "Figma / Sketch / Adobe XD", "Canva & Easy Design Tools",
        "Procreate / Affinity Suite", "Blender / Cinema 4D / Maya",
        "Final Cut Pro / DaVinci Resolve", "After Effects / Premiere Pro",
        "FigJam / Miro (Collaborative Ideation)", "Zeplin / Avocode (Developer Handoff)",

        # Process & Collaboration
        "Agile/Scrum for Design Teams", "Design Sprints",
        "Cross-Functional Collaboration (Dev, PM, Marketing)",
        "Constructive Feedback & Critique", "Stakeholder Management",
        "Portfolio Curation & Presentation",

        # Emerging & Experimental
        "Generative AI for Art & Design (Midjourney, DALL·E, Firefly)",
        "AR/VR Experience Design", "3D Scanning & Photogrammetry",
        "Bio Design & Biodesign", "Data Physicalization",
        "Interactive Installation Art",
    ],
    "Cognitive & Soft Skills": [
        # Core Cognitive Skills
        "Critical Thinking", "Analytical Reasoning", "Logical Reasoning",
        "Deductive Reasoning", "Inductive Reasoning", "Abductive Reasoning",
        "Numerical Reasoning", "Verbal Reasoning", "Spatial Reasoning",
        "Abstract Reasoning", "Pattern Recognition", "Systems Thinking",
        "Lateral Thinking", "Strategic Thinking", "Conceptual Thinking",
        "Holistic Thinking", "Design Thinking Mindset", "Creative Thinking",
        "Problem Solving", "Complex Problem Solving", "Decision Making",
        "Judgment Under Uncertainty", "Information Processing", "Data Interpretation",
        "Mental Math", "Working Memory", "Long-Term Memory Techniques",
        "Attention to Detail", "Selective Attention", "Divided Attention",
        "Sustained Concentration (Focus)", "Cognitive Flexibility", "Mental Agility",
        "Adaptability of Thought", "Learning Agility (Quick Learning)",
        "Rapid Knowledge Acquisition", "Comprehension (Reading, Listening)",
        "Synthesis of Information", "Evaluation of Evidence",
        "Metacognition (Thinking About Thinking)", "Self-Reflection", "Introspection",

        # Personal Effectiveness & Self-Management
        "Self-Awareness", "Self-Regulation", "Self-Discipline", "Self-Motivation",
        "Time Management", "Task Prioritization", "Goal Setting (Short & Long Term)",
        "Planning & Scheduling", "Organization Skills", "Personal Accountability",
        "Reliability & Dependability", "Work Ethic", "Perseverance & Grit",
        "Resilience & Bouncing Back", "Stress Management", "Emotional Control",
        "Adaptability to Change", "Flexibility", "Dealing with Ambiguity",
        "Initiative (Proactiveness)", "Resourcefulness", "Patience", "Persistence",
        "Attention Management", "Energy Management", "Habit Formation",

        # Emotional Intelligence (EQ)
        "Emotional Self-Awareness", "Emotional Expression", "Empathy (Cognitive & Affective)",
        "Compassion", "Active Listening", "Reading Body Language",
        "Nonverbal Communication Awareness", "Emotional Regulation in Others (Influence)",
        "Conflict Management Through EQ", "Building Rapport", "Trustworthiness",
        "Interpersonal Sensitivity",

        # Communication Skills
        "Verbal Communication", "Written Communication", "Public Speaking",
        "Presentation Skills", "Storytelling", "Simplifying Complex Ideas",
        "Persuasion & Influence", "Negotiation", "Facilitation (Meetings, Workshops)",
        "Giving Constructive Feedback", "Receiving Feedback",
        "Assertiveness (vs. Aggression/Passivity)", "Diplomatic Communication",
        "Cross-Cultural Communication", "Virtual Communication Etiquette",
        "Listening Comprehension", "Summarization & Paraphrasing",
        "Editing & Proofreading (Precision)",

        # Interpersonal & Social Skills
        "Teamwork & Collaboration", "Relationship Building", "Networking",
        "Conflict Resolution", "Mediation", "Humor & Lightheartedness",
        "Inclusivity & Respect for Diversity", "Service Orientation (Customer/Client Focus)",
        "Hospitality Mindset", "Mentoring & Coaching Peers", "Teaching & Knowledge Transfer",
        "Managing Up (Boss Relationships)", "Political Savvy (Organizational Awareness)",

        # Leadership & Influence Skills
        "Visionary Leadership", "Servant Leadership", "Situational Leadership",
        "Delegation", "Empowerment of Others", "Motivating Teams",
        "Inspiring a Shared Vision", "Leading Change", "Decision-Making under Pressure",
        "Accountability in Leadership", "Courageous Conversations", "Talent Development",
        "Championing Innovation",

        # Teamwork & Collaborative Skills
        "Co-creation", "Consensus Building", "Virtual Team Collaboration",
        "Cross-Functional Collaboration", "Psychological Safety Contribution",
        "Group Problem Solving", "Brainstorming Techniques", "Peer Accountability",

        # Creativity & Innovation Skills
        "Ideation & Brainstorming", "Thinking Outside the Box", "Curiosity",
        "Openness to Experience", "Imagination", "Improvisation",
        "Experimentation & Risk-Taking", "Connecting Disparate Ideas",
        "Iterative Prototyping (in thought)",

        # Learning & Growth Mindset
        "Growth Mindset", "Continuous Learning", "Learning from Failure",
        "Unlearning & Relearning", "Self-Directed Learning",
        "Teaching Others to Solidify Learning", "Study Habits & Techniques",
        "Knowledge Management (Personal)", "Reading Comprehension Strategies",
        "Note-taking & Organization",

        # Professional & Work Ethic Traits
        "Integrity", "Honesty", "Ethical Judgment", "Confidentiality",
        "Professionalism", "Punctuality", "Follow-Through", "Taking Ownership",
        "Positive Attitude", "Gratitude at Work", "Handling Criticism Gracefully",
        "Dress & Presence (Professional Image)",

        # Additional Cognitive & Soft Skill Combinations
        "Troubleshooting", "Root Cause Analysis (5 Whys)", "Intuition & Gut Feel (Informed)",
        "Risk Assessment (Personal/Team)", "Mindfulness & Present-Moment Awareness",
        "Visualization Techniques", "Self-Coaching",
        "Bias Awareness (Cognitive Bias Mitigation)", "Perspective Taking",
        "Graciousness & Diplomacy", "Constructive Positivity", "Managing Expectations",
    ],
    "Law & Public Policy": [
    # Legal Research & Analysis
    "Statutory Interpretation", "Case Law Analysis (IRAC Method)",
    "Legal Research Databases (Westlaw, LexisNexis)", "Legislative History Research",
    "Regulatory Code Tracking (CFR, Federal Register)", "Shepardizing / KeyCite (Citation Checking)",
    "Comparative Legal Analysis", "Precedent Identification & Application",
    "Constitutional Law Analysis", "Legal Citation Mastery (Bluebook, ALWD)",

    # Legal Writing & Drafting
    "Persuasive Writing (Motions, Briefs)", "Objective Legal Writing (Memos, Opinions)",
    "Contract Drafting", "Pleading Drafting (Complaints, Answers)",
    "Discovery Documents (Interrogatories, RFPs)", "Settlement Agreements",
    "Judicial Orders & Opinions", "Legislative Drafting (Bills, Amendments)",
    "Policy Memoranda for Government", "FOIA / Public Records Requests Drafting",
    "Plain Language Drafting for Public Notices",

    # Litigation & Dispute Resolution
    "Civil Procedure (Pre-trial to Appeal)", "Criminal Procedure & Sentencing",
    "Evidence Law & Admissibility", "Trial Advocacy & Courtroom Presentation",
    "Direct & Cross-Examination", "Opening & Closing Arguments",
    "Jury Selection (Voir Dire)", "Witness Preparation",
    "Deposition Taking & Defending", "Motion Practice (Summary Judgment, Dismissal)",
    "E-Discovery & Legal Technology (Relativity)", "Class Action Procedure",
    "Appellate Brief Writing & Oral Argument", "Alternative Dispute Resolution (ADR) Design",
    "Mediation Advocacy", "Arbitration Procedure (AAA, ICC, LCIA)",
    "Negotiation Theory & Tactics", "Settlement Strategy",
    "International Commercial Arbitration",

    # Transactional & Corporate Law
    "Mergers & Acquisitions (Due Diligence)", "Joint Venture Agreements",
    "Corporate Governance & Board Resolutions", "Securities Law (SEC Filings, ’33/’34 Acts)",
    "Venture Capital & Private Equity Transactions", "Term Sheet Drafting",
    "Commercial Contracting (MSAs, SOWs)", "Licensing & Franchise Agreements",
    "Bankruptcy & Restructuring (Chapter 7, 11)", "Secured Transactions (UCC Article 9)",
    "Antitrust & Competition Law Analysis", "Tax Law Fundamentals (Corporate, International)",
    "Executive Compensation & Benefits",

    # Regulatory & Compliance
    "Administrative Law & Rulemaking Process", "Regulatory Comment Submission",
    "Compliance Program Design & Auditing", "Anti-Money Laundering (AML) / KYC",
    "Foreign Corrupt Practices Act (FCPA) Compliance", "Data Privacy Law (GDPR, CCPA, HIPAA)",
    "Environmental Law & Permitting", "Financial Services Regulation (Dodd-Frank, Basel)",
    "Food & Drug Law (FDA)", "Healthcare Law & Stark/Anti-Kickback",
    "Energy & Utilities Regulation", "Telecommunications Law (FCC)",
    "Zoning & Land Use Permitting", "Occupational Safety & Health (OSHA)",
    "Immigration Law & Visa Processing", "Import/Export Controls & Sanctions (OFAC)",

    # Intellectual Property & Technology Law
    "Patent Drafting & Prosecution", "Patent Prior Art Searching",
    "Trademark Clearance & Registration", "Copyright Fair Use Analysis",
    "Trade Secret Protection", "IP Licensing & Technology Transfer",
    "Open Source Software Licensing", "Digital Millennium Copyright Act (DMCA) Takedown",
    "Artificial Intelligence & Algorithmic Accountability Law",

    # Criminal Law & Justice
    "Criminal Complaint & Indictment Review", "Bail & Detention Hearings",
    "Plea Bargain Negotiation", "Sentencing Guidelines Application",
    "Juvenile Justice Procedure", "Victims' Rights Advocacy",
    "Restorative Justice Facilitation", "Forensic Evidence & Expert Witnesses",

    # Family & Personal Law
    "Divorce & Separation Agreements", "Child Custody & Visitation",
    "Adoption & Surrogacy Law", "Domestic Violence Protection Orders",
    "Pre/Post-Nuptial Agreements", "Estate Planning (Wills, Trusts)",
    "Probate & Estate Administration", "Elder Law & Guardianship",

    # Real Estate & Property
    "Title Search & Examination", "Closing & Escrow Management",
    "Commercial Leasing", "Condemnation & Eminent Domain",
    "Construction Law & Lien Waivers", "Real Estate Finance & Mortgages",

    # Constitutional, Civil Rights & Public Interest
    "First Amendment (Speech, Religion) Analysis", "Fourth Amendment Search & Seizure",
    "Due Process & Equal Protection", "Civil Rights Litigation (Section 1983)",
    "Human Rights Treaty Interpretation", "Impact Litigation Strategy",
    "Public Interest Advocacy", "Environmental Justice",
    "Indigenous Rights & Tribal Law",

    # International Law & Relations
    "Public International Law (UN Charter, Treaties)", "International Criminal Law (ICC, Tribunals)",
    "Law of the Sea", "Extradition & Mutual Legal Assistance",
    "International Trade Law (WTO, USMCA)", "Investor-State Dispute Settlement (ISDS)",
    "Refugee & Asylum Law", "International Humanitarian Law (Geneva Conventions)",

    # Public Policy Core Skills
    "Policy Analysis & Problem Framing", "Cost-Benefit Analysis (CBA)",
    "Regulatory Impact Assessment", "Program Evaluation (Logic Models, RCTs)",
    "Qualitative Research (Interviews, Focus Groups)", "Quantitative Policy Analysis (Statistics, Modeling)",
    "Policy Memo & Briefing Note Writing", "Stakeholder Mapping & Power Analysis",
    "Public Consultation & Engagement Design", "Policy Implementation Planning",
    "Monitoring & Evaluation (M&E) Frameworks", "Performance Measurement & KPIs",
    "Policy Advocacy & Campaign Strategy", "Coalition Building & Grassroots Organizing",
    "Lobbying & Government Relations", "Budget Analysis & Fiscal Note Preparation",
    "Grant Writing & Fundraising for Policy Initiatives",

    # Government & Political Process
    "Legislative Process & Procedure (Parliamentary/Congressional)",
    "Bill Tracking & Amendment Strategy", "Committee Hearing Preparation",
    "Executive Order & Directive Analysis", "Federal/State/Local Government Relations",
    "Intergovernmental Relations Management", "Public Administration & Agency Management",
    "Rulemaking & Regulatory Development", "Administrative Hearings & Adjudication",
    "Government Ethics & Transparency (Sunshine Laws)", "Public Records & Open Meetings Law",
    "Election Law & Campaign Finance", "Voting Rights & Redistricting",

    # Ethics, Professional Responsibility & Soft Skills
    "Legal Ethics & Professional Conduct (ABA Rules)", "Conflict of Interest Analysis",
    "Client Confidentiality & Privilege", "Attorney-Client Privilege Management",
    "Pro Bono Best Practices", "Judicial Ethics", "Policy & Legislative Ethics",
    "Cross-Cultural Competence in Law & Policy", "Legal Project Management",
    "Public Speaking for Hearings & Briefings", "Media & Crisis Communication for Law/Policy",
    "Negotiation & Mediation in Public Sector",
    "Interdisciplinary Collaboration (Economists, Scientists)",
],
    "Education & Training": [
    # Foundational Pedagogy & Teaching
    "Lesson Planning", "Curriculum Development",
    "Backward Design (Understanding by Design)", "Differentiated Instruction",
    "Classroom Management", "Student Engagement Strategies",
    "Active Learning Techniques", "Inquiry-Based Learning",
    "Project-Based Learning (PBL)", "Problem-Based Learning",
    "Cooperative & Collaborative Learning", "Direct Instruction / Explicit Teaching",
    "Socratic Method / Questioning", "Scaffolding & Gradual Release (I Do, We Do, You Do)",
    "Metacognition Teaching Strategies", "Culturally Responsive Teaching",
    "Universal Design for Learning (UDL)", "Multi-Tiered Systems of Support (MTSS / RTI)",
    "Growth Mindset Cultivation", "Educational Psychology Application",
    "Learning Theories (Behaviorism, Cognitivism, Constructivism)",

    # Instructional Design & Technology
    "Instructional Systems Design (ADDIE Model)", "SAM Model (Successive Approximation)",
    "Learning Objectives & Outcomes Writing (Bloom's Taxonomy)", "Storyboarding for eLearning",
    "eLearning Authoring Tools (Articulate Storyline, Captivate)",
    "Learning Management System (LMS) Administration (Moodle, Canvas, Blackboard)",
    "SCORM / xAPI / cmi5 Standards", "Gamification in Learning",
    "Microlearning Design", "Multimedia Design Principles (Mayer's)",
    "Video Production for Education", "Flipped Classroom Design",
    "Blended Learning Models", "Mobile Learning Design",
    "Rapid Prototyping for Training", "User Experience (UX) for Learning Platforms",
    "Accessibility in Digital Learning (WCAG, Section 508)",

    # Assessment & Evaluation
    "Formative Assessment Design", "Summative Assessment Design",
    "Rubric Development (Holistic & Analytic)", "Authentic / Performance-Based Assessment",
    "Standardized Test Administration & Analysis", "Item Writing for Tests (MCQs, Essays)",
    "Psychometrics / Item Analysis (Difficulty, Discrimination)", "Reliability & Validity of Assessments",
    "Peer & Self-Assessment Techniques", "Portfolio Assessment",
    "Data-Driven Instruction (Analyzing Student Data)", "Grading & Reporting Systems",
    "Standards-Based Grading", "Competency-Based Assessment",
    "Needs Analysis for Training", "Training Evaluation (Kirkpatrick Model)",
    "Return on Investment (ROI) in Training",

    # Classroom & Behavioral Management
    "Positive Behavior Interventions & Supports (PBIS)",
    "Restorative Practices in Education", "Conflict Resolution & Peer Mediation",
    "Trauma-Informed Teaching", "Social-Emotional Learning (SEL) Facilitation",
    "Classroom Routine & Procedure Establishment", "De-escalation Strategies",
    "Transitions Management", "Time-on-Task Maximization",
    "Physical Classroom Environment Design",

    # Special Education & Inclusive Practices
    "Individualized Education Program (IEP) Development", "504 Plan Implementation",
    "Special Education Law (IDEA, ADA)", "Co-Teaching & Inclusion Models",
    "Assistive Technology Integration", "Behavioral Intervention Plan (BIP) Design",
    "Functional Behavioral Assessment (FBA)", "Speech & Language Support Strategies",
    "Occupational Therapy Collaboration", "Dyslexia & Specific Learning Disability Interventions",
    "Autism Spectrum Disorder Strategies", "Gifted & Talented Education Strategies",
    "Adaptive Curriculum Modification",

    # Early Childhood Education
    "Play-Based Learning", "Developmental Milestones Monitoring",
    "Emergent Literacy & Numeracy Instruction", "Sensory Play Design",
    "Classroom Centers / Learning Stations", "Early Intervention Strategies",
    "Parent-Child Interaction Guidance",

    # Adult & Higher Education
    "Andragogy (Adult Learning Principles)", "Facilitation Skills for Workshops",
    "Seminar & Discussion-Based Teaching", "Graduate Supervision & Mentorship",
    "Academic Advising & Student Support", "Student Retention Strategies",
    "Prior Learning Assessment (PLA)", "Community of Inquiry Framework",

    # Corporate Training & Professional Development
    "Training Needs Analysis (TNA)", "Onboarding Program Design",
    "Soft Skills Training Delivery", "Leadership Development Program Design",
    "Sales Enablement Training", "Compliance Training",
    "Technical / IT Training", "Coaching & Mentoring Programs",
    "Train-the-Trainer Facilitation", "Virtual Instructor-Led Training (VILT)",
    "Learning Experience Platforms (LXP) – Degreed, EdCast",
    "Knowledge Management & Curation", "Succession Planning Training",

    # Coaching & Talent Development
    "Executive Coaching", "Performance Coaching", "Career Development Coaching",
    "360-Degree Feedback Facilitation", "Strengths-Based Development (CliftonStrengths)",
    "Action Learning Sets", "Mentorship Program Coordination",

    # EdTech & Digital Fluency
    "Interactive Whiteboard Use (Smart, Promethean)",
    "Student Response Systems (Kahoot, Poll Everywhere)",
    "Google Workspace for Education", "Microsoft Teams for Education",
    "Digital Portfolios (Seesaw, Google Sites)", "Coding & Computational Thinking Teaching",
    "AI in Education (ChatGPT, adaptive platforms)",
    "Virtual Reality (VR) / Augmented Reality (AR) in Learning",
    "Data Privacy & Digital Citizenship Education (FERPA, COPPA)",
    "Media Literacy Instruction", "Digital Content Curation",

    # Curriculum & Program Administration
    "Curriculum Mapping & Alignment", "Scope & Sequence Development",
    "Textbook & Resource Evaluation", "Program Accreditation Processes",
    "Quality Assurance in Education", "Educational Policy Interpretation",
    "Budgeting for Education Programs", "Grant Writing for Education",

    # Bilingual / Multilingual Education
    "ESL / EFL Instruction", "Sheltered Instruction Observation Protocol (SIOP)",
    "Translanguaging Pedagogy", "Bilingual Curriculum Design",
    "Literacy Across Languages",

    # Literacy & Numeracy Specialization
    "Phonics & Phonemic Awareness Instruction", "Guided Reading",
    "Balanced Literacy Approach", "Writing Workshop (Writer's Craft)",
    "Mathematics Manipulatives & Visual Models", "Math Intervention Strategies",
    "STEM / STEAM Integration",

    # Arts & Physical Education
    "Visual Arts Instruction", "Music Education Methods (Orff, Kodály)",
    "Drama / Theater Pedagogy", "Physical Education Curriculum Design",
    "Health & Wellness Education", "Adapted Physical Education",

    # Research & Scholarship of Teaching
    "Action Research in Education", "Educational Research Methods (Qualitative, Quantitative)",
    "Systematic Review in Education", "Publication & Conference Presentation",
    "Reflective Practice / Teaching Journals", "Peer Observation & Feedback",

    # Career & Technical Education (CTE/Vocational)
    "Work-Based Learning Coordination", "Apprenticeship Program Design",
    "Industry Certification Alignment", "Career Readiness & Soft Skills Instruction",
    "Job Shadowing & Internship Supervision",

    # Counselling & Student Services
    "Academic Counselling", "Social-Emotional Counselling Basics",
    "Crisis Intervention in Schools", "College & Career Readiness Counselling",

    # Leadership & Administration
    "Instructional Leadership", "School Improvement Planning",
    "Staff Supervision & Evaluation", "Professional Learning Communities (PLCs)",
    "Educational Change Management", "Community & Parent Engagement",
    "Education Law & Ethics", "Equity & Anti-Racism in Education",
    "Strategic Planning for Schools/Organizations",

    # Soft Skills Specific to Educators & Trainers
    "Empathy & Active Listening", "Public Speaking & Presentation",
    "Feedback Delivery (Constructive & Motivational)", "Facilitation & Group Dynamics",
    "Mentorship Mindset", "Patience & Resilience",
    "Creativity in Lesson Design", "Humor in Teaching",
    "Adaptability & Improvisation",
],
    "Agriculture & Environment": [
    # Agronomy & Crop Science
    "Crop Selection & Rotation Planning", "Seed Variety Selection & Breeding Basics",
    "Plant Physiology & Growth Stages", "Crop Nutrition & Fertilizer Management",
    "Weed Identification & Management", "Cover Cropping & Green Manures",
    "Intercropping & Polyculture Systems", "Harvest & Post-Harvest Handling",
    "Forage & Pasture Management", "Organic Crop Production Standards",
    "Hydroponics & Aeroponics", "Precision Agriculture Technology",

    # Soil Science & Management
    "Soil Sampling & Testing", "Soil Classification & Mapping",
    "Soil Fertility & Amendment", "Soil Erosion Control",
    "Conservation Tillage (No-till, Reduced-till)", "Soil Microbiology & Rhizosphere",
    "Composting & Vermicomposting", "Biochar Production & Application",
    "Salinity & Sodicity Management", "Soil Carbon Sequestration",

    # Animal Husbandry & Veterinary Basics
    "Livestock Nutrition & Ration Formulation", "Pasture-Based Livestock Systems",
    "Animal Breeding & Genetics", "Dairy & Meat Production Management",
    "Poultry & Swine Production", "Beekeeping & Apiculture",
    "Animal Health Monitoring & Biosecurity", "Vaccination & Deworming Protocols",
    "Animal Welfare Standards & Auditing", "Manure & Nutrient Management Planning",

    # Agricultural Engineering & Mechanization
    "Farm Machinery Operation & Maintenance", "Tractor & Implement Calibration",
    "Irrigation System Design (Drip, Sprinkler, Pivot)", "Drainage System Design",
    "Greenhouse & Controlled Environment Design", "Farm Structures & Building",
    "Renewable Energy for Farms (Solar, Biogas)", "Post-Harvest Machinery (Dryers, Mills)",

    # Water Management & Irrigation
    "Irrigation Scheduling & Water Budgeting", "Water Harvesting & Storage",
    "Watershed Management", "Water Quality Testing & Treatment",
    "Aquifer & Groundwater Management", "Flood & Drought Mitigation Planning",
    "Wetland Construction & Restoration",

    # Pest, Disease & Weed Management
    "Integrated Pest Management (IPM)", "Biological Control Agents",
    "Pesticide Application & Safety", "Herbicide Resistance Management",
    "Plant Pathology & Diagnosis", "Entomology & Beneficial Insect Habitat",
    "Rodent & Vertebrate Pest Control",

    # Agroforestry & Silviculture
    "Agroforestry System Design (Alley Cropping, Silvopasture)", "Tree Planting & Reforestation",
    "Forest Inventory & Mensuration", "Timber Stand Improvement",
    "Wildfire Fuel Management", "Non-Timber Forest Products (NTFPs)",
    "Urban Forestry & Arboriculture",

    # Sustainable Agriculture & Food Systems
    "Regenerative Agriculture Practices", "Permaculture Design",
    "Farm-to-Table & Local Food Systems", "Value-Added Product Development",
    "Community Supported Agriculture (CSA) Management", "Farmers Market Operations",

    # Aquaculture & Fisheries
    "Fish Pond & Recirculating System Management", "Water Quality in Aquaculture",
    "Fish Nutrition & Feed Formulation", "Shellfish & Seaweed Farming",
    "Fisheries Stock Assessment", "Marine & Freshwater Conservation",

    # Environmental Science & Ecology
    "Ecosystem Assessment & Monitoring", "Biodiversity Survey Methods",
    "Habitat Restoration & Creation", "Invasive Species Management",
    "Pollinator Habitat Design", "Wildlife Tracking & Telemetry",
    "Environmental Sampling (Air, Water, Soil, Biota)",

    # Climate Science & Adaptation
    "Climate Risk & Vulnerability Assessment", "Carbon Footprint Analysis",
    "Climate-Smart Agriculture Practices", "Drought-Resistant Cropping Systems",
    "Climate Modeling & Downscaling", "Carbon Offset Project Development",

    # Conservation & Natural Resource Management
    "Protected Area Management", "Land Use Planning & Zoning",
    "Conservation Easement Stewardship", "Rangeland Health Assessment",
    "Wildlife Corridor Design", "Wetland Delineation & Protection",
    "Riparian Buffer Establishment",

    # Environmental Policy, Law & Regulation
    "Environmental Impact Assessment (EIA)", "Environmental Compliance Auditing",
    "Clean Water Act (CWA) & NPDES Permitting", "Endangered Species Act (ESA) Compliance",
    "National Environmental Policy Act (NEPA) Process", "Environmental Justice Analysis",
    "Agri-Environmental Schemes & Subsidies", "Carbon Markets & Trading",

    # Waste Management & Pollution Control
    "Solid Waste Management (Reduce, Reuse, Recycle)", "Hazardous Waste Handling & Disposal",
    "Composting Facility Operations", "Wastewater Treatment (Constructed Wetlands, Lagoons)",
    "Air Quality Monitoring & Emission Control", "Plasticulture Waste Management",
    "Nutrient Runoff & Eutrophication Control",

    # Renewable Energy & Bioeconomy
    "Anaerobic Digestion & Biogas Production", "Biofuel Crop Production",
    "Agrivoltaics (Solar + Agriculture Integration)", "Biomass Supply Chain Management",
    "Woody Biomass & Pellet Production",

    # GIS, Remote Sensing & Data
    "GIS Mapping for Agriculture & Environment (ArcGIS, QGIS)",
    "GPS & GNSS for Precision Ag and Surveying", "Drone/UAV Operation & Image Analysis",
    "Satellite Imagery Interpretation (NDVI, Landsat)", "Environmental Modeling (SWAT, MODFLOW)",
    "Data Loggers & Sensor Networks", "Ag Data Analysis (Yield Maps, Prescriptions)",

    # Food Safety & Post-Harvest Management
    "Good Agricultural Practices (GAP) Certification", "HACCP for Farm Operations",
    "Cold Chain & Storage Management", "Food Traceability Systems",
    "Mycotoxin & Contaminant Testing", "Processing & Preservation (Drying, Fermenting)",

    # Agricultural Economics & Extension
    "Farm Business Planning & Budgeting", "Cost of Production Analysis",
    "Commodity Marketing & Risk Management", "Cooperative Management",
    "Agricultural Lending & Microfinance", "Extension Education & Farmer Training",
    "Participatory Rural Appraisal (PRA)", "Value Chain Analysis & Development",

    # Environmental Health & Toxicology
    "Ecotoxicology & Risk Assessment", "Pesticide Residue Analysis",
    "Bioremediation & Phytoremediation", "Brownfield & Contaminated Land Remediation",
    "Drinking Water Safety & Sanitation",

    # Urban Agriculture & Green Infrastructure
    "Rooftop & Vertical Farming", "Community Garden Design & Management",
    "Green Roof & Living Wall Installation", "Rain Garden & Bioswale Design",
    "Urban Soil Remediation & Safety",

    # Natural Disaster & Emergency Management
    "Drought Early Warning Systems", "Floodplain Management",
    "Post-Fire Rehabilitation (BAER)", "Disaster Resilience for Rural Communities",

    # Research & Lab Skills
    "Field Trial Design & Plot Layout", "Statistical Analysis for Ag/Env (R, SPSS)",
    "Soil & Plant Tissue Lab Analysis", "Water Microbiology Testing",
    "DNA Barcoding & Environmental DNA (eDNA)", "Greenhouse & Growth Chamber Experiments",

    # Communication & Stakeholder Engagement
    "Science Communication for Non-Technical Audiences", "Public Consultation & Facilitation",
    "Grant Writing for Conservation & Ag Projects", "Conflict Resolution in Resource Management",
    "Interdisciplinary Team Collaboration",
],
    "Services & Hospitality": [
    # Customer Service Excellence
    "Customer Needs Assessment", "Active Listening for Service",
    "Complaint Handling & Resolution", "Service Recovery Strategies",
    "Anticipatory Service", "Personalization & Guest Recognition",
    "Customer Loyalty & Retention Techniques", "Net Promoter Score (NPS) Management",
    "Mystery Guest / Quality Audits", "Service Blueprinting",
    "Moments of Truth Analysis", "Call Center & Contact Center Operations",

    # Hospitality Operations
    "Front Desk & Reception Management", "Concierge Services",
    "Bell Services & Valet", "Guest Check-in / Check-out Procedures",
    "Property Management Systems (PMS) – Opera, Maestro",
    "Housekeeping Standards & Inspection", "Laundry & Linen Management",
    "Turndown Service", "Public Area Cleaning & Maintenance",
    "Pest Control in Hospitality", "Waste Management & Recycling",

    # Food & Beverage Management
    "Menu Engineering & Design", "Culinary Fundamentals & Food Preparation",
    "Food Safety (HACCP, ServSafe)", "Beverage Management & Mixology",
    "Wine & Spirits Knowledge (Sommelier basics)", "Bar Management",
    "Restaurant Service (Mise en Place, Sequence of Service)",
    "Banquet & Event F&B Service", "Room Service Operations",
    "Coffee & Barista Skills", "Dietary Restriction Management",

    # Hotel & Resort Management
    "Revenue Management & Yield Optimization", "OTA & Channel Management (Booking.com, Expedia)",
    "Direct Booking Strategy", "Rate Parity & Dynamic Pricing",
    "Forecasting & Overbooking Management", "Group Block Management",
    "Spa & Wellness Facility Management", "Recreation & Activities Programming",
    "Kids Club & Family Programming", "Resort Fee & Package Design",

    # Restaurant & Quick Service Management
    "Point of Sale (POS) Systems (Toast, Micros)", "Table Turnover Optimization",
    "Queue & Waitlist Management", "Online Ordering & Delivery Platform Management",
    "Ghost Kitchen Operations", "Drive-Thru Efficiency Design",
    "Franchise Operations Management", "Standard Operating Procedure (SOP) Adherence",

    # Event Management & Catering
    "Event Planning & Conceptualization", "Banquet Event Order (BEO) Execution",
    "Wedding & Social Event Coordination", "Corporate Meeting & Conference Management",
    "Exhibition & Trade Show Logistics", "Audio-Visual Setup for Events",
    "Event Budgeting & P&L", "Vendor Sourcing & Contract Negotiation",
    "On-site Event Troubleshooting", "Post-Event Evaluation & ROI",

    # Travel & Tourism
    "Tour Itinerary Design & Packaging", "Destination Knowledge & Interpretation",
    "Guided Tour Techniques", "Adventure & Eco-Tour Operations",
    "Group Travel Coordination", "Travel Agency Operations",
    "GDS Systems (Amadeus, Sabre)", "Airline Ticketing & Reservations",
    "Cruise Line Service Operations", "Visa & Passport Processing Assistance",
    "Cultural Sensitivity & Interpretation",

    # Spa, Wellness & Leisure
    "Spa Treatment Protocols (Massage, Facials)", "Hydrotherapy & Thermal Suite Operations",
    "Fitness Center Management & Personal Training", "Pool & Aquatic Facility Safety",
    "Yoga & Mindfulness Instruction", "Product Knowledge & Retail Sales",
    "Appointment Scheduling & Yield", "Wellness Program Design",

    # Housekeeping & Facility Maintenance
    "Cleaning Chemical & Equipment Knowledge", "Room Inspection Checklists",
    "Deep Cleaning & Seasonal Maintenance", "Carpet & Upholstery Care",
    "Sustainability in Housekeeping (Green Key, LEED)",
    "Preventive Maintenance Scheduling", "HVAC & Lighting Basics",
    "Safety & OSHA Compliance", "Pool Chemical Management",

    # Customer Relationship & CRM
    "CRM Platforms (Salesforce, Revinate)", "Guest Profile & Preference Management",
    "Automated Pre-arrival & Post-stay Communication", "Reputation Management (TripAdvisor, Google)",
    "Social Media Customer Care", "Chatbot & AI Concierge Implementation",

    # Revenue & Profit Management
    "Menu Profitability Analysis (Food Cost %)", "Labor Cost Control & Scheduling",
    "Inventory & Stock Rotation (FIFO)", "Waste Tracking & Reduction",
    "Supplier & Procurement Management", "Energy & Utility Cost Control",
    "Capital Expenditure (CapEx) Planning for Properties",

    # Human Resources in Hospitality
    "High-Volume Recruitment & Onboarding", "Shift & Rota Scheduling",
    "Cross-Training & Multi-skilling", "Tip & Service Charge Distribution",
    "Seasonal Workforce Planning", "Internal Talent Pipelines",
    "Coaching & Corrective Action in Service Teams",

    # Service Marketing & Distribution
    "Digital Menu Board & QR Code Design", "Up-selling & Cross-Selling Scripts",
    "Loyalty Program Design (Points, Tiers)", "Hotel Photography & Virtual Tours",
    "Distribution & Parity Management", "SEO & Local Search for Hospitality",

    # Soft & Interpersonal Skills
    "Emotional Intelligence in Service", "Conflict De-escalation",
    "Professional Presentation & Grooming", "Multilingual Greetings & Basic Phrases",
    "Cultural Competence & Adaptability", "Teamwork Under Pressure (Kitchen, Events)",
    "Empathy & Patience", "Attention to Detail (Table Setting, Room Setup)",
    "Warmth & Authentic Hospitality Mindset", "Anticipating Unspoken Needs",

    # Safety, Security & Crisis
    "Emergency Evacuation Procedures", "Fire Safety & Warden Training",
    "First Aid & CPR Certification", "Foodborne Illness Outbreak Response",
    "Guest Data Privacy (PCI Compliance, GDPR)", "Loss Prevention & Asset Protection",
    "Natural Disaster & Crisis Communication Plan",

    # Specialized Niche Services
    "Butler & VIP Service", "Wedding Planning & Coordination",
    "Luxury Hospitality Standards (Forbes, AAA Diamond)", "Accessible & Inclusive Service Design",
    "Pet-Friendly Hospitality", "Casino & Gaming Service Etiquette",
    "Theme Park Operations & Guest Flow",

    # Behind-the-Scenes & Support
    "Purchasing & Storeroom Management", "Kitchen Stewarding & Dishwashing Systems",
    "Uniform & Linen Par Levels", "Loading Dock & Receiving",
    "Interdepartmental Communication Logs", "Task Assignment & PM Tools (HotSOS, Alice)",
],
    "Pure Sciences & Research": [
    # Physics
    "Classical Mechanics", "Electromagnetism & Electrodynamics",
    "Thermodynamics & Statistical Mechanics", "Quantum Mechanics",
    "Relativity (Special & General)", "Optics & Photonics",
    "Condensed Matter Physics", "Nuclear & Particle Physics",
    "Astrophysics & Cosmology", "Acoustics & Wave Physics",
    "Fluid Dynamics", "Plasma Physics",
    "Computational Physics", "Mathematical Physics",

    # Chemistry
    "Analytical Chemistry (Titration, Spectroscopy)", "Organic Synthesis & Reaction Mechanisms",
    "Inorganic Chemistry & Coordination Complexes", "Physical Chemistry & Kinetics",
    "Quantum Chemistry & Molecular Modeling", "Biochemistry & Chemical Biology",
    "Polymer Chemistry", "Materials Chemistry",
    "Environmental Chemistry", "Nuclear Chemistry",
    "Chromatography (GC, HPLC)", "Mass Spectrometry",
    "NMR Spectroscopy Interpretation", "X-ray Crystallography",

    # Biology & Life Sciences
    "Molecular Biology (PCR, Cloning)", "Cell Culture & Aseptic Technique",
    "Genetics & Genomics", "Microbiology & Sterile Technique",
    "Immunology & ELISA", "Physiology & Organ Systems",
    "Developmental Biology", "Ecology & Field Sampling",
    "Evolutionary Biology & Phylogenetics", "Neuroscience & Electrophysiology",
    "Plant Biology & Herbarium Techniques", "Marine & Freshwater Biology",
    "Structural Biology", "Bioinformatics (BLAST, Sequence Alignment)",

    # Mathematics
    "Calculus & Real Analysis", "Linear Algebra",
    "Abstract Algebra & Group Theory", "Number Theory",
    "Probability Theory", "Statistical Inference",
    "Discrete Mathematics & Graph Theory", "Optimization & Linear Programming",
    "Differential Equations (ODE/PDE)", "Numerical Analysis & Methods",
    "Topology & Geometry", "Mathematical Proof Writing & Logic",

    # Earth & Environmental Sciences
    "Petrology & Mineralogy", "Stratigraphy & Sedimentology",
    "Structural Geology & Mapping", "Geophysics (Seismic, Gravity)",
    "Geochemistry", "Paleontology & Biostratigraphy",
    "Oceanography (Physical, Chemical)", "Meteorology & Climate Science",
    "Hydrology & Water Resource Modeling", "Soil Science & Pedology",
    "Volcanology & Geohazards",

    # Astronomy & Space Sciences
    "Telescope Operation & Observation Planning", "Photometry & Spectroscopy of Celestial Objects",
    "Stellar Evolution & Nucleosynthesis", "Galactic & Extragalactic Astronomy",
    "Planetary Science & Remote Sensing", "Radio & X-ray Astronomy",
    "Astrometry & Celestial Mechanics", "Cosmic Ray & Particle Astrophysics",

    # Research Methods & Experimental Design
    "Hypothesis Formulation & Testing", "Literature Review & Systematic Review",
    "Experimental Design (Control Groups, Randomization)", "Blind & Double-Blind Studies",
    "Power Analysis & Sample Size Calculation", "Replication & Reproducibility",
    "Peer Review Process", "Qualitative Research Methods (Interviews, Thematic Analysis)",
    "Mixed Methods Research", "Fieldwork Planning & Logistics",

    # Statistics & Biostatistics
    "Descriptive & Inferential Statistics", "Regression Models (Linear, Logistic, GLM)",
    "ANOVA, MANOVA & ANCOVA", "Survival Analysis & Kaplan-Meier",
    "Meta-Analysis & Forest Plots", "Multivariate Analysis (PCA, Cluster)",
    "Bayesian Statistics", "Non-parametric Tests",
    "Statistical Software (R, SPSS, SAS, Stata)", "Data Visualization (ggplot2, matplotlib)",

    # Laboratory Techniques & Safety
    "Lab Safety & Hazard Communication", "Chemical Hygiene & Waste Disposal",
    "Biosafety Levels (BSL-1,2,3) & Practices", "Fume Hood & Glove Box Use",
    "Pipetting & Solution Preparation", "Microscopy (Light, Fluorescence, SEM, TEM)",
    "Centrifugation & Ultracentrifugation", "Electrophoresis (SDS-PAGE, Agarose)",
    "Spectrophotometry & Fluorometry", "Calorimetry & Thermal Analysis",
    "Cryogenics & Vacuum Systems", "Cleanroom Protocols",

    # Data Science & Scientific Computing
    "Programming for Science (Python, R, MATLAB)", "Data Wrangling & Cleaning",
    "Scientific Databases & SQL", "Machine Learning for Research (Scikit-learn, TensorFlow)",
    "Image Analysis & Processing (ImageJ, FIJI)", "Signal Processing & Filtering",
    "High-Performance Computing (HPC) & Cluster Use", "Version Control for Research (Git)",
    "Electronic Lab Notebook (ELN) Use", "Scientific Workflow Tools (KNIME, Galaxy)",

    # Academic Writing & Communication
    "Manuscript Writing & Formatting (LaTeX, Word)", "Citation Management (Zotero, EndNote, Mendeley)",
    "Graphical Abstract & Figure Preparation", "Poster & Oral Presentation Design",
    "Writing Grant Proposals", "Thesis & Dissertation Writing",
    "Plain Language Summary for Public Audiences", "Press Release & Media Interviewing for Scientists",

    # Grant Writing & Research Funding
    "Grant Mechanism Knowledge (NIH, NSF, ERC, Horizon Europe)", "Budget Preparation & Justification",
    "Project Timeline & Milestone Design", "Finding Funding Opportunities",
    "Collaboration & Consortium Building", "Ethical Approval & IRB Applications",

    # Research Ethics & Integrity
    "Responsible Conduct of Research (RCR)", "Conflict of Interest Disclosure",
    "Human Subjects Protection (Belmont, Declaration of Helsinki)", "Animal Welfare & 3Rs (Replace, Reduce, Refine)",
    "Data Privacy & Anonymization", "Plagiarism Detection & Avoidance",
    "Authorship Criteria & Disputes", "Reproducibility & Open Data Standards",
    "Pre-registration of Studies",

    # Project & Laboratory Management
    "Lab Inventory & Supply Ordering", "Equipment Maintenance & Calibration",
    "Student & Technician Supervision", "Collaborative Project Coordination",
    "Conference & Symposium Organization", "Budget Tracking & Cost Allocation",

    # Soft Skills for Researchers
    "Critical Thinking & Skepticism", "Intellectual Curiosity & Question Formulation",
    "Resilience & Handling Experimental Failure", "Interdisciplinary Collaboration",
    "Mentoring & Supervising Students", "Time Management Across Multiple Projects",
    "Scientific Storytelling", "Networking at Conferences",
    "Peer Feedback (Giving & Receiving)", "Public Engagement & Citizen Science",
],
    "Arts, Entertainment & Media": [
    # Visual Arts & Fine Art
    "Oil & Acrylic Painting", "Watercolor Techniques",
    "Figure Drawing & Life Drawing", "Perspective & Composition",
    "Sculpture & 3D Construction (Clay, Stone, Metal)", "Printmaking (Linocut, Etching, Screen)",
    "Mixed Media & Collage", "Art History & Critical Theory",
    "Gallery Presentation & Curation", "Art Handling & Installation",

    # Performing Arts (General)
    "Stage Presence & Performance Energy", "Character Development & Motivation",
    "Script Analysis & Text Work", "Improvisation (Theatre, Comedy)",
    "Audition Technique (Monologue, Cold Read)", "Physical Theatre & Mime",
    "Voice Projection & Breath Control", "Accents & Dialects",
    "Choreography Creation", "Performance Improvisation Safety",

    # Theatre & Live Performance
    "Monologue & Scene Study", "Blocking & Stage Movement",
    "Stage Combat (Certified)", "Lighting Design & Operation (DMX, ETC)",
    "Set Design & Construction", "Prop Sourcing & Fabrication",
    "Costume Design & Stitching", "Sound Design & Cue Programming (QLab)",
    "Stage Management (Calling, Prompt Book)", "FOH & Audience Services",

    # Dance
    "Ballet Technique", "Contemporary & Modern Dance",
    "Jazz & Tap", "Urban/Street Styles (Hip-Hop, Breaking)",
    "Ballroom & Latin", "Choreography & Notation (Laban)",

    # Music Performance & Theory
    "Instrumental Proficiency (Piano, Guitar, etc.)", "Vocal Technique & Repertoire",
    "Music Theory & Harmony", "Sight-Reading & Ear Training",
    "Orchestration & Arranging", "Conducting & Ensemble Direction",
    "Lyric & Songwriting", "Live Looping & Electronic Performance",

    # Music Production & Audio
    "Digital Audio Workstations (Ableton, Pro Tools, Logic)", "Recording & Mic Techniques",
    "Mixing & Mastering", "MIDI Programming & Virtual Instruments",
    "Sound Synthesis & Sound Design", "Foley & Field Recording",
    "Beat Making & Sampling", "Music Publishing & Copyright Clearance",
    "Atmos / Spatial Audio Mixing",

    # Film & Video Production
    "Screenwriting & Story Structure", "Storyboarding & Shot Listing",
    "Directing Actors & Camera", "Cinematography (Lighting, Composition)",
    "Camera Operation (DSLR, Cinema, ARRI, RED)", "Grip & Dolly Techniques",
    "Location Scouting & Permitting", "Production Sound Recording",
    "Video Editing (Premiere, DaVinci, Final Cut)", "Color Grading & Color Correction",
    "Visual Effects (VFX) – After Effects, Nuke", "Motion Graphics & Titles",
    "Assistant Directing (AD) & Scheduling", "Continuity & Script Supervision",

    # Animation & Game Development
    "2D Hand-Drawn Animation", "3D Animation (Maya, Blender)",
    "Rigging & Skinning", "Motion Capture Direction",
    "Game Design Documentation (GDD)", "Level & Environment Design",
    "Interactive Storytelling & Branching Narratives", "Playtesting & User Research",

    # Broadcasting & Journalism
    "Newswriting & Reporting (AP Style)", "Investigative Research & Fact-Checking",
    "Interviewing (Live, Recorded, Hostile)", "Broadcast Presentation & Teleprompter",
    "Field & Outside Broadcast Coordination", "Newsroom Control Room Operations",
    "Podcast Production & Hosting", "Technical Directing & Vision Mixing",
    "Anchoring & Commentary (Sports, News)",

    # Digital & Social Media Content
    "Content Strategy & Calendar Planning", "Short-Form Video (TikTok, Reels, Shorts)",
    "YouTube Content & Channel Management", "Live Streaming & Real-Time Engagement",
    "Influencer Brand Partnerships", "Community Management & Moderation",
    "Meme Culture & Viral Trend Adaptation",

    # Photography & Image Making
    "Portrait & Headshot Photography", "Event & Wedding Photography",
    "Street & Documentary Photography", "Fine Art Conceptual Photography",
    "Product & Still Life Photography", "Sports & Action Photography",
    "Raw Processing (Lightroom, Capture One)", "Advanced Retouching & Frequency Separation",

    # Writing & Publishing
    "Fiction Writing (Novel, Short Story)", "Non-Fiction & Feature Writing",
    "Poetry & Spoken Word", "Playwriting & Scriptwriting",
    "Comedy Writing (Sketch, Stand-up)", "Copyediting & Line Editing",
    "Ghostwriting", "Literary Agent Querying",
    "Self-Publishing & Print-on-Demand", "Blogging & SEO Writing",

    # Media Production & Management
    "Production Budgeting & Cost Reporting", "Production Insurance & Legal",
    "Talent Release & Contract Management", "Union Rules (SAG-AFTRA, IATSE)",
    "Post-Production Workflow & Dailies", "Asset Management & Archival Standards",
    "Broadcast Compliance & OFCOM/FCC Regulations",

    # Fashion & Beauty (Media Focus)
    "Styling & Wardrobe for Camera", "Makeup for Film/TV/Stage",
    "Special Effects (SFX) Makeup", "Hairstyling & Wig Dressing",
    "Fashion Editorial Direction", "Runway Production & Choreography",

    # Immersive & Interactive Media
    "Virtual Reality (VR) Experience Design", "Augmented Reality (AR) Filter Creation",
    "Projection Mapping (Resolume, MadMapper)", "Interactive Installation Art",
    "Escape Room & Immersive Theatre Design",

    # Arts Administration & Curation
    "Exhibition Curation & Interpretation", "Museum Registrar & Condition Reporting",
    "Grant Writing for Arts Nonprofits", "Donor Cultivation & Sponsorship",
    "Box Office & Ticketing Management", "Arts Marketing & Audience Development",

    # Voice & Vocal Work
    "Voice Acting for Animation & Games", "Audiobook Narration & Direction",
    "Dubbing & ADR (Automated Dialogue Replacement)", "Commercial Voiceover",
    "Vocal Health & Care",

    # Entertainment Law & Business
    "Basic IP & Copyright for Creatives", "Contract Negotiation for Talent",
    "Royalties, Publishing & Sync Licensing", "Distribution Deals & Aggregators",
    "Business Management for Freelance Artists",

    # Criticism & Discourse
    "Art & Film Criticism", "Cultural Commentary & Op-Ed Writing",
    "Panel Moderation & Hosting", "Academic Art Theory",
    "Lifestyle & Service Journalism",

    # Soft & Collaboration Skills
    "Creative Collaboration Under Pressure", "Taking & Implementing Direction",
    "Rehearsal Discipline & Preparation", "Cross-Departmental Communication (Art, Tech, Design)",
    "Pitching Ideas & Treatments", "Constructive Critique & Workshopping",
    "Deadline-Driven Creative Production",
],
    "Social & Community Services": [
    # Core Social Work & Case Management
    "Case Management & Coordination", "Intake & Psychosocial Assessment",
    "Service Plan Development & Monitoring", "Strengths-Based Assessment",
    "Risk & Safety Assessment (Child, Elder, Vulnerable)", "Mandated Reporting",
    "Home Visits & Environmental Assessment", "Discharge & Aftercare Planning",
    "Interdisciplinary Team Collaboration", "Electronic Case Records & Documentation (HMIS, EHR)",

    # Counseling & Therapeutic Support
    "Active Listening & Empathic Communication", "Motivational Interviewing",
    "Cognitive Behavioral Therapy (CBT) Basics", "Solution-Focused Brief Therapy",
    "Trauma-Informed Care Practices", "Crisis Intervention & De-escalation",
    "Grief & Bereavement Counseling", "Group Facilitation & Therapy",
    "Family Systems & Parenting Support", "Anger Management Facilitation",

    # Community Development & Organizing
    "Community Needs Assessment & Asset Mapping", "Participatory Action Research",
    "Coalition Building & Network Weaving", "Community Organizing & Mobilization",
    "Advocacy Campaign Planning", "Public Meeting Facilitation",
    "Community Capacity Building", "Social Capital Measurement",

    # Child, Youth & Family Services
    "Child Protective Services (CPS) Procedures", "Foster Care & Adoption Casework",
    "Youth Mentoring & Development", "Early Intervention Services",
    "Reunification & Family Preservation", "Juvenile Justice Support",
    "Child Life Specialist Skills", "Domestic Violence Shelter Operations",

    # Aging, Disability & Vulnerable Populations
    "Geriatric Assessment & Care Planning", "Aging-in-Place Support",
    "Disability Rights & Independent Living Philosophy", "Accessible Program Design",
    "Guardianship & Conservatorship Navigation", "Adult Protective Services",
    "End-of-Life & Palliative Care Coordination",

    # Housing & Homelessness Services
    "Housing First & Rapid Re-Housing Models", "Tenant Rights & Eviction Prevention",
    "Homeless Outreach & Engagement", "Continuum of Care (CoC) Coordination",
    "Transitional & Supportive Housing Management",

    # Substance Use & Recovery Services
    "Addiction Screening (SASSI, AUDIT)", "Harm Reduction Principles & Practices",
    "Recovery Coaching & Peer Support", "Medication-Assisted Treatment (MAT) Navigation",
    "Relapse Prevention Planning", "Sober Living Environment Support",

    # Mental Health & Crisis Services
    "Suicide Risk Assessment & Safety Planning", "Crisis Hotline & Textline Operation",
    "Psychiatric Rehabilitation (Recovery Model)", "Dual Diagnosis Support",
    "Consumer-Run & Peer-Run Programs", "Psychoeducation Delivery",

    # Refugee, Immigrant & Migrant Services
    "Resettlement & Reception Casework", "Cultural Orientation & Bridging",
    "Asylum & Immigration Legal Support Navigation", "Language Access & Interpretation Coordination",
    "Anti-Trafficking Victim Identification & Support", "Unaccompanied Minor Services",

    # Health & Public Health Social Work
    "Medical Social Work (Hospital, Clinic, Hospice)", "Patient Navigation & Health Literacy",
    "HIV/AIDS Support Services", "Maternal & Child Health Outreach",
    "Environmental Health & Justice Advocacy", "Food Security & Nutrition Assistance (SNAP, WIC)",

    # Nonprofit Management & Administration
    "Nonprofit Strategic Planning", "Board Development & Governance",
    "Volunteer Recruitment & Management", "Program Design & Logic Models",
    "Outcome Measurement & Performance Indicators", "Fidelity Monitoring & Quality Assurance",
    "Nonprofit Financial Management (990, Restricted Funds)", "Social Enterprise Development",

    # Grant Writing & Fundraising
    "Federal & Foundation Grant Writing", "Proposal Budgeting & Justification",
    "Individual Donor Cultivation & Stewardship", "Corporate Partnership & Sponsorship",
    "Crowdfunding & Digital Campaigns", "Annual Fund & Capital Campaigns",
    "Planned Giving & Endowments",

    # Advocacy, Policy & Systems Change
    "Policy Research & Analysis", "Legislative & Budget Advocacy",
    "Lobbying & Grassroots Mobilization", "Human Rights Documentation & Reporting",
    "Racial Equity & Anti-Oppression Frameworks", "Gender-Based Analysis Plus (GBA+)",
    "Impact Litigation Support", "Civil Legal Aid Navigation",

    # Restorative & Transformative Justice
    "Restorative Circles & Conferencing", "Victim-Offender Dialogue Facilitation",
    "Community Accountability Processes", "Reentry & Post-Release Support",
    "Prison & Jail-Based Programming",

    # Education & Prevention Services
    "Prevention Curriculum Development", "Life Skills & Financial Literacy Training",
    "Parent Education & Support Groups", "HIV/STI Prevention Education",
    "Violence Prevention & Bystander Intervention Training",

    # Specialized Therapeutic Modalities
    "Play Therapy Essentials", "Art-Based & Expressive Arts Facilitation",
    "Mindfulness-Based Stress Reduction (MBSR)", "Narrative Therapy Techniques",
    "Dialectical Behavior Therapy (DBT) Skills Group", "Eye Movement Desensitization & Reprocessing (EMDR) Awareness",

    # Program Evaluation & Research
    "Logic Model & Theory of Change Development", "Quantitative & Qualitative Methods for Social Programs",
    "Survey Design & Administration", "Focus Group Facilitation & Analysis",
    "Community-Based Participatory Research (CBPR)", "Data Visualization for Advocacy",

    # Diversity, Equity, Inclusion & Belonging (DEIB)
    "Implicit Bias Awareness & Mitigation", "Culturally Responsive Service Delivery",
    "Trauma-Informed Systems Design", "Language Justice & Interpretation",
    "Equitable Hiring & Retention Practices", "Intersectionality Application",

    # Professional Ethos & Self-Care
    "Ethical Decision-Making (NASW Code, etc.)", "Professional Boundaries & Dual Relationships",
    "Vicarious Trauma & Compassion Fatigue Management", "Reflective Supervision & Peer Consultation",
    "Burnout Prevention & Resilience Building", "Cultural Humility", "Advocacy & Whistleblowing",

    # Additional Specialist Areas
    "Employment & Vocational Support", "Wraparound Service Coordination (Child & Family)",
    "Public Benefits Navigation (Medicaid, SSI/SSDI)", "Forensic Social Work (Courts, Corrections)",
    "School Social Work & Pupil Personnel Services", "Emergency Management & Disaster Relief (ESF-6)",
],
   "Real Estate & Property Management": [
    # Real Estate Sales & Brokerage
    "Comparative Market Analysis (CMA)", "Property Valuation & Pricing",
    "Listing Presentation & Marketing", "Buyer Representation & Advocacy",
    "Negotiation & Offer Management", "Escrow & Closing Coordination",
    "MLS Systems (Multiple Listing Service)", "Lead Generation & Prospecting",
    "CRM for Real Estate (Salesforce, Follow Up Boss)", "Open House Management",
    "Due Diligence Facilitation (Inspections, Title)", "1031 Exchange Basics",

    # Residential Property Management
    "Tenant Screening & Background Checks", "Lease Agreement Preparation & Execution",
    "Rent Collection & Arrears Enforcement", "Tenant Relations & Conflict Resolution",
    "Maintenance Request Coordination", "Move-In & Move-Out Inspections",
    "Security Deposit Accounting", "Eviction Procedures & Unlawful Detainer",
    "Fair Housing Act (FHA) Compliance", "Pet & ESA Policy Management",
    "Resident Retention Programs", "Multifamily Lease-Up Management",

    # Commercial Property Management
    "Commercial Lease Administration (Gross, Net, NNN)", "CAM (Common Area Maintenance) Reconciliation",
    "Tenant Improvement (TI) Coordination", "Percentage Rent Calculation",
    "Industrial & Retail Management Nuances", "Property Operating Expense (OPEX) Budgeting",

    # Facilities & Maintenance Management
    "Preventive Maintenance Scheduling", "Work Order Systems (Yardi, Building Engines)",
    "HVAC, Electrical & Plumbing System Oversight", "Life Safety & Fire Code Compliance",
    "Janitorial & Grounds Contract Management", "Capital Reserve Planning",
    "Energy Management & Benchmarking (ENERGY STAR)", "Pest Control Management",

    # Real Estate Finance & Investment
    "Net Operating Income (NOI) Analysis", "Cap Rate & Cash-on-Cash Return",
    "Discounted Cash Flow (DCF) Modeling for Properties", "Pro Forma Development",
    "Debt Service Coverage Ratio (DSCR)", "Investment Underwriting & Presentation",
    "Loan Origination & Refinancing (Fannie Mae, Freddie Mac)", "Real Estate Investment Trust (REIT) Metrics",
    "Waterfall Distribution Modeling", "Due Diligence for Acquisitions",

    # Real Estate Development
    "Site Selection & Highest/Best Use Analysis", "Land Acquisition & Assemblage",
    "Entitlement & Rezoning Processes", "Pro Forma & Feasibility Study",
    "Architect & GC Selection & RFPs", "Construction Draw & Lien Waiver Management",
    "Horizontal vs. Vertical Development", "Mixed-Use Project Planning",
    "Affordable Housing & LIHTC Programs", "Community & Municipal Approvals",

    # Legal & Contractual
    "Purchase & Sale Agreement (PSA) Terms", "Title Review & Encumbrance Analysis",
    "Understanding of Deeds, Easements, CC&Rs", "Contract Contingency Management",
    "Master Lease vs. Sublease Structuring", "Legal Notice Drafting (3-Day, 30-Day)",
    "ADA & Accessibility Compliance in Property", "Risk Management & GL Insurance Placement",

    # Marketing & Leasing
    "Online Listing Syndication (Zillow, CoStar, LoopNet)", "Virtual Tour & Drone Photography",
    "Lease-Up Marketing Strategy", "Signage & Curb Appeal Enhancement",
    "Digital Campaigns (PPC, Social) for Leasing", "Leasing Scripts & Closing Techniques",
    "Competitor Market Surveying & Positioning",

    # Homeowners Association (HOA) & Condo Management
    "CC&R Enforcement & Interpretation", "HOA Budgeting & Reserve Study",
    "Board Meeting Preparation & Facilitation", "Common Area Asset Management",
    "Violation & Fine Processing", "Vendor Contract Management for HOAs",

    # Valuation & Appraisal
    "Sales Comparison Approach", "Income Capitalization Approach",
    "Cost Approach to Value", "Appraisal Report Reading (URAR, Narrative)",
    "Market Absorption & Trend Analysis", "Environmental Contamination (Phase I/II) Impact",

    # Real Estate Technology (PropTech)
    "Property Management Software (Yardi, AppFolio, Buildium)", "Smart Building Technology (IoT)",
    "Access Control & Key Fob Systems", "Tenant Experience Apps (Rise, Locale)",
    "Real Estate Data Analytics (CoStar, REIS)", "Building Information Modeling (BIM) for Ops",

    # Economic, Market & Feasibility Analysis
    "Urban & Regional Economics Basics", "Land Use & Zoning Code Analysis",
    "Rent Comparability Studies", "Supply & Demand Assessment",
    "Public-Private Partnership (P3) Structuring",

    # Environmental & Sustainability
    "LEED, BREEAM, WELL Certification Processes", "Building Energy Audits",
    "Solar & Green Roof Feasibility", "Environmental Site Assessment (ESA Phase I)",
    "Waste Stream & Recycling Program Management",

    # Soft Skills & Interpersonal
    "High-Stakes Negotiation", "Resolving Neighbor-to-Neighbor Disputes",
    "Effective Client Status Updates", "Active Listening for Tenant Complaints",
    "Managing Difficult Personalities", "Trust & Rapport Building",
    "Multilingual Communication for Diverse Tenants",
    "Board Presentation & Public Meeting Confidence",

    # Business & Administrative
    "Trust Account & Escrow Management", "Portfolio Performance Reporting",
    "Asset Management Strategy", "Business Development & Networking",
    "Continuing Education & License Maintenance",
    "Rent Roll & Occupancy Analysis", "Insurance Claim Filing & Recovery",
    "Emergency Preparedness & Business Continuity",
],
    "Transportation, Aviation & Maritime": [
    # Aviation – Piloting & Flight Operations
    "Private Pilot License (PPL) Knowledge", "Commercial Pilot License (CPL) Knowledge",
    "Airline Transport Pilot (ATP) Certification", "Instrument Flight Rules (IFR) Navigation",
    "Crew Resource Management (CRM)", "Cockpit Automation & Flight Management Systems (FMS)",
    "Aviation Weather Analysis & Meteorology", "Airspeed, Altitude & Performance Calculations",
    "Multi-Engine & Jet Transition", "Unmanned Aerial Systems (UAS/Drone) Operation",
    "Helicopter Rotorcraft Knowledge", "Flight Planning & International Flight Rules",

    # Aviation – Air Traffic Control & Airspace
    "Air Traffic Control (ATC) Procedures", "Radar & Non-Radar Separation",
    "Airspace Classification & Clearance", "Communication Protocols & Phraseology",
    "Conflict Alert & Collision Avoidance", "NOTAM & Flight Plan Filing",
    "ADS-B & NextGen Technologies",

    # Aviation – Maintenance & Engineering
    "Aircraft Maintenance Technician (A&P) Certification", "Line & Base Maintenance",
    "Avionics & Electrical Systems Troubleshooting", "Turbine & Piston Engine Overhaul",
    "Composite & Sheet Metal Repair", "Aircraft Inspection (100-Hr, Annual)",
    "MEL (Minimum Equipment List) & CDL", "Safety Management System (SMS) in Aviation",
    "Aircraft Logbook & Documentation",

    # Aviation – Airport & Ground Operations
    "Airport Operations & Ramp Safety", "Ground Handling (Pushback, Baggage, Cargo)",
    "De-icing & Anti-icing Procedures", "Gate Management & Turnaround Coordination",
    "Airport Security (TSA, ICAO Annex 17)", "Emergency Response Plan Execution",
    "Wildlife Hazard Management", "Airport Certification & 14 CFR Part 139",

    # Aviation – Cabin & Passenger Services
    "Cabin Safety & Evacuation Procedures", "First Aid & Inflight Medical Emergencies",
    "Dangerous Goods (DG) Handling & Notification", "Conflict De-escalation & Unruly Passengers",
    "Service Excellence in Premium Cabins", "Food Safety & Inflight Catering",

    # Maritime – Navigation & Seamanship
    "COLREGs (Rules of the Road) Application", "Electronic Chart Display (ECDIS) Operation",
    "Terrestrial & Celestial Navigation", "GMDSS Radio Operation (GOC/ROC)",
    "Ship Handling & Mooring", "Anchoring & Dredging Operations",
    "Bridge Resource Management (BRM)", "Tides, Currents & Under-Keel Clearance",
    "Passage Planning & Weather Routing",

    # Maritime – Engineering & Maintenance
    "Marine Diesel Engine Operation & Repair", "Marine Boiler & Turbine Plant Management",
    "Auxiliary Systems (Pumps, Hydraulics)", "Electrical Power Generation & Distribution at Sea",
    "Refrigeration & HVAC for Ships", "Dry-Docking & Shipyard Supervision",
    "Corrosion Prevention & Marine Coatings", "Ballast Water & Fuel Oil Management",

    # Maritime – Safety, Survival & Regulatory
    "SOLAS & MARPOL Compliance", "ISM Code & Safety Management Systems",
    "Personal Survival Techniques (STCW)", "Fire Prevention & Firefighting (Basic/Advanced)",
    "Lifeboat & Rescue Boat Operations", "Oil Spill Response & OPAC/OPRC",
    "Port State Control (PSC) Inspections", "Maritime Security (ISPS Code, Piracy Mitigation)",

    # Maritime – Port, Terminal & Cargo Operations
    "Port & Terminal Management", "Stevedoring & Cargo Handling Equipment",
    "Container Terminal Operating Systems (TOS)", "Bulk & Breakbulk Cargo Handling",
    "Dangerous Goods Handling by Sea (IMDG Code)", "Customs Clearance & Documentation",
    "Logistics & Supply Chain for Maritime",

    # Maritime – Specialized & Offshore
    "Dynamic Positioning (DP) Operation", "ROV (Remote Operated Vehicle) Piloting",
    "Offshore Supply & Anchor Handling", "Subsea Engineering & Inspection",
    "Fishing Vessel Operations & Gear", "Cruise Ship & Passenger Vessel Management",

    # Road Transportation – Trucking & Fleet
    "Commercial Driver's License (CDL) – Class A/B/C", "Hours of Service (HOS) & ELD Compliance",
    "Pre-Trip, En-Route, Post-Trip Inspection", "Cargo Securement & Weight Distribution",
    "Hazmat (Hazardous Materials) Transportation (49 CFR)", "Refrigerated (Reefer) Trailer Operation",
    "Tanker & Liquid Bulk Transport", "Oversize & Overweight Load Permitting",
    "Last-Mile Delivery & White-Glove Service",

    # Road Transportation – Passenger Transit
    "Bus & Motorcoach Operation", "Transit Route Planning & Scheduling",
    "Paratransit & Accessible Service Management", "School Bus Safety & Student Management",
    "Ride-hailing & Microtransit Platform Management",

    # Rail Transportation
    "Locomotive Operation & Engineer Certification", "Train Braking & Air Brake Systems",
    "Track Inspection & Geometry", "Signaling & Positive Train Control (PTC)",
    "Railcar Switching & Yard Management", "Railway Safety Standards (FRA, RSSB)",
    "Passenger Rail Operations & Ticketing", "Freight Train Manifest & Intermodal Logistics",

    # Logistics & Supply Chain
    "Freight Forwarding & Multimodal Transport", "Incoterms & International Trade",
    "Customs Brokerage & Tariff Classification", "Warehouse Management (WMS)",
    "Cross-Docking & Distribution Center Operations", "Inventory Control & Cycle Counting",
    "Demand Planning & S&OP", "Cold Chain Logistics (Pharma, Food)",
    "Reverse Logistics & Returns Management",

    # Transport Infrastructure & Engineering
    "Traffic Engineering & Modeling (HCM, SYNCHRO)", "Pavement Design & Maintenance",
    "Bridge Inspection & Rating (NBIS)", "Intelligent Transportation Systems (ITS)",
    "Toll & Congestion Pricing Systems", "Public Transport Infrastructure Design",
    "Railway Track Design & Alignment",

    # Environmental & Sustainability
    "Emissions Control & IMO 2020 / EPA Standards", "Alternative Fuels (EV, Hydrogen, LNG, SAF)",
    "Noise & Vibration Monitoring", "Environmental Impact Assessment for Transport",
    "Carbon Offsetting & Net-Zero Fleet Strategy",

    # Safety, Security & Emergency
    "Occupational Health & Safety (OSHA, HSWA)", "Accident Investigation & Root Cause Analysis",
    "Transport Security (TWIC, HAZMAT Security Plan)", "Crowd Management for Mass Transit",
    "Pandemic & Health Emergency Response in Transport",

    # Fleet & Asset Management
    "Fleet Telematics & GPS Tracking", "Fuel Management & Cost Control",
    "Preventive Maintenance Scheduling (Fleet, Aircraft, Ship)", "Life-Cycle Cost & Replacement Planning",
    "Warranty & Parts Inventory Management",

    # Regulatory, Legal & Compliance
    "FAA, EASA, ICAO Regulations", "IMO & Flag State Compliance",
    "FMCSA / DOT (US) & EU Mobility Package", "Transport Contract Law & COGSA / Warsaw Convention",
    "Insurance & Liability in Transport (P&I, Hull)", "Accident & Incident Reporting (NTSB, MAIB)",

    # Technology & Specialized Systems
    "GIS & Spatial Analysis for Transport", "Simulation (Flight Sim, Bridge Sim, Traffic Modeling)",
    "Autonomous Vehicle / Vessel Technology Awareness", "Drone Traffic Management (UTM / U-Space)",
    "Blockchain for Supply Chain Visibility", "Meteorology for Transport Operations",
    "Data Analytics for Fleet Performance",

    # Customer Service & Passenger Experience
    "Terminal Passenger Flow Design", "Lost & Found / Baggage Tracing (WorldTracer)",
    "Airline Revenue Management & Pricing", "Frequent Traveler Program Management",

    # Training & Instruction
    "Flight Instructor (CFI) Certification", "STCW Instructor / Assessor",
    "CDL Training & Testing", "Simulator Instruction (Aviation, Maritime, Rail)",
    "Safety & Compliance Training Delivery",

    # Soft & Human Factors
    "Situational Awareness", "Crisis Decision-Making under Time Pressure",
    "Teamwork in High-Risk Environments", "Fatigue Risk Management",
    "Intercultural Communication with Crew/Passengers", "Incident Debriefing & Just Culture",
],
    "Religion, Theology & Spirituality": [
    # Theology & Religious Studies (Academic)
    "Systematic Theology", "Historical Theology", "Biblical Theology",
    "Dogmatic Theology", "Contextual Theology", "Liberation Theology",
    "Feminist & Womanist Theology", "Postcolonial Theology",
    "Queer Theology", "Process Theology", "Political Theology",

    # Biblical Studies & Exegesis
    "Hebrew Bible (Old Testament) Exegesis", "New Testament Exegesis",
    "Biblical Greek", "Biblical Hebrew", "Aramaic Basics",
    "Textual Criticism", "Hermeneutics & Interpretation Theory",
    "Form, Source & Redaction Criticism", "Septuagint & Apocrypha Studies",

    # Comparative Religion & World Religions
    "Islam: Qur'an & Hadith Studies", "Judaism: Torah, Talmud & Rabbinics",
    "Hinduism: Vedas, Upanishads & Bhakti", "Buddhism: Theravada, Mahayana & Vajrayana",
    "Sikhism: Guru Granth Sahib & History", "Indigenous & Folk Religion Traditions",
    "Comparative Mysticism", "Phenomenology of Religion",

    # Church History & Patristics
    "Early Church & Patristic Thought", "Medieval & Scholastic Theology",
    "Reformation Studies", "Modern & Global Church History",
    "Denominational History & Doctrine",

    # Canon Law & Church Polity
    "Roman Catholic Canon Law (CIC/CCEO)", "Anglican Canon Law & Constitutions",
    "Orthodox Canonical Tradition", "Protestant Polity (Presbyterian, Episcopal, Congregational)",
    "Ecumenical Councils & Documents",

    # Ethics & Moral Theology
    "Christian Ethics (Virtue, Natural Law)", "Catholic Social Teaching",
    "Bioethics & Medical Ethics", "Environmental & Eco-Theology Ethics",
    "Business & Economic Ethics from Faith Perspective",
    "Sexual & Family Ethics",

    # Pastoral Care & Counseling
    "Active Listening & Empathic Presence", "Pastoral Counseling Techniques",
    "Grief & Bereavement Support", "Crisis & Trauma Spiritual Care",
    "Hospital & Healthcare Chaplaincy", "Mental Health First Aid for Clergy",
    "Marriage & Pre-Marital Counseling", "Family Systems & Conflict Mediation",
    "Substance Abuse & Addiction Ministry", "Suicide Prevention & Postvention",
    "Domestic Violence & Abuse Awareness for Faith Leaders",

    # Spiritual Direction & Formation
    "Ignatian Spiritual Exercises", "Spiritual Direction / Accompaniment",
    "Discernment Processes (Individual & Communal)", "Mentoring & Disciple-Making",
    "Rule of Life & Personal Discipline", "Retreat Design & Facilitation",
    "Contemplative & Centering Prayer", "Lectio Divina & Sacred Reading",
    "Journaling & Reflective Practice",

    # Preaching & Worship Leadership
    "Sermon Preparation & Expository Preaching", "Narrative & Topical Preaching",
    "Liturgy Design (Word & Table)", "Sacramental Theology & Administration",
    "Eucharist / Communion / Mass", "Baptism, Confirmation & Initiation Rites",
    "Wedding & Funeral Planning & Officiating", "Music & Arts in Worship Planning",
    "Seasonal & Lectionary-Based Worship (Advent, Lent, etc.)", "Digital Worship & Live-streaming",

    # Religious Education & Catechesis
    "Catechesis & Faith Formation Curriculum", "Sunday School & Children's Ministry",
    "Youth & Young Adult Ministry", "Adult Education & Bible Study",
    "RCIA / Catechumenate Process", "Confirmation Preparation",
    "Special Needs Faith Formation", "Curriculum Writing & Evaluation",

    # Chaplaincy (Specialized)
    "Military Chaplaincy (Multi-Faith Support)", "Hospice & Palliative Chaplaincy",
    "Prison & Correctional Chaplaincy", "Campus / University Chaplaincy",
    "Corporate & Workplace Chaplaincy", "Fire & Police Chaplaincy",
    "Disaster Spiritual Care (Red Cross, FEMA)", "First Responder Crisis Intervention (CISM)",

    # Missiology & Cross-Cultural Ministry
    "Cross-Cultural Communication of Faith", "Intercultural Theology",
    "Mission Strategy & Church Planting", "Contextualization & Inculturation",
    "Short-Term Mission Trip Planning & Ethics", "Language Acquisition for Ministry",

    # Interfaith & Ecumenical Dialogue
    "Interfaith Dialogue Facilitation", "Abrahamic Traditions Dialogue (Judaism, Christianity, Islam)",
    "Ecumenical Movement & Councils (WCC, NCCC)", "Common Word & Global Interfaith Initiatives",
    "Pluralism & Religious Diversity Training", "Mediation of Religious Conflicts",

    # Social Justice & Advocacy
    "Faith-Based Community Organizing", "Prophetic Witness & Public Theology",
    "Immigration & Refugee Ministry", "Anti-Racism & Reconciliation Ministry",
    "Fair Trade & Ethical Purchasing for Congregations", "Housing & Homelessness Ministry",
    "Environmental Stewardship & Creation Care", "Food Justice & Community Gardens",

    # Religious Administration & Leadership
    "Congregational Strategic Planning", "Church Business Administration",
    "Non-Profit Management for Faith-Based Orgs", "Staff & Volunteer Management",
    "Stewardship & Fundraising (Annual Pledges, Capital Campaigns)", "Grant Writing for Religious Nonprofits",
    "Budgeting & Financial Oversight", "Facilities & Property Management for Religious Buildings",
    "HR & Clergy Wellness", "Safe Church / Safe Sanctuary Policy & Training",

    # Digital Ministry & Media
    "Social Media for Faith Communities", "Content Creation (Podcasts, Videos, Blogs)",
    "Virtual Community Building", "Church Management Software (ChMS – Planning Center, Servant Keeper)",
    "Graphic Design for Bulletins & Media", "Photography & Storytelling for Ministry",

    # Ritual, Symbol & Sacrament
    "Blessing & Anointing of the Sick", "Exorcism & Deliverance Ministry (Catholic/Charismatic)",
    "Laying on of Hands & Healing Services", "Benediction & Adoration",
    "Sacred Space Design & Altar Guild", "Liturgical Dance & Movement",

    # Monastic & Religious Life
    "Vows & Community Life (Poverty, Chastity, Obedience)", "Monastic Hospitality",
    "Rule Interpretation (Benedictine, Franciscan)", "Novitiate & Formation Programs",

    # Apologetics & Evangelism
    "Cultural Apologetics", "Public Debates & Dialogues",
    "Seeker-Sensitive Evangelism", "Relational Discipleship & Evangelism",
    "New Atheism & Secularism Engagement", "Scientific Apologetics (Evolution, Cosmology)",

    # Death, Dying & Afterlife Ministry
    "Funeral Rites Across Traditions", "Thanatology & Theology of Death",
    "Green Burial & Memorial Planning", "Ancestral Veneration & All Souls' Traditions",

    # Religion & the Arts
    "Iconography & Religious Art", "Sacred Music Performance (Organ, Chant, Gospel)",
    "Liturgical Textile & Vestment Design", "Religious Poetry & Literature",
    "Church Architecture & Sacred Geometry",

    # Research & Writing
    "Academic Theological Writing", "Exegetical Paper & Commentary Writing",
    "Publishing in Peer-Reviewed Journals", "Editing & Proofreading for Religious Publishers",
    "Translation of Religious Texts", "Archival Research in Church Records",

    # Personal & Contemplative Practices
    "Silence & Solitude", "Fasting & Abstinence", "Pilgrimage Planning & Leadership",
    "Labyrinth Walking Facilitation", "Sacred Dance & Embodied Prayer",
    "Nature & Wilderness Spirituality", "Mindfulness & Meditation Instruction (from own tradition)",

    # Specialized Skills & Accreditations
    "Clinical Pastoral Education (CPE) Units", "Board-Certified Chaplain (BCC)",
    "Ordination & Endorsement Processes", "Denominational Polity & Discipline",
    "Records Management (Baptism, Marriage, Death Registers)",
    "Confidentiality & Seal of Confession",

    # Soft Skills for Religious Professionals
    "Boundaries & Self-Care in Ministry", "Empathy & Non-Anxious Presence",
    "Courageous Conversations & Conflict Transformation", "Cultural Humility & Anti-Oppression",
    "Public Speaking & Rhetoric", "Ethical Decision-Making in Ministry",
    "Team Building & Laity Empowerment",
],
    "Humanities & Cultural Heritage": [
    # History & Historiography
    "Archival Research Methods", "Primary Source Analysis",
    "Historical Narrative & Writing", "Historiographical Theory & Critique",
    "Chronological Reasoning & Periodization", "Comparative History",
    "Public History Practice", "Oral History Interviewing & Transcription",

    # Archaeology & Fieldwork
    "Archaeological Survey (Pedestrian, Geophysical)", "Excavation Techniques (Stratigraphic, Open-Area)",
    "Stratigraphy & Harris Matrix", "Artifact Illustration & Photography",
    "Site Grid & Total Station Surveying", "Flotation & Soil Sampling",
    "Zooarchaeology & Paleoethnobotany", "Ceramic & Lithic Analysis",
    "Human Osteology & Bioarchaeology", "Underwater & Maritime Archaeology",
    "Community Archaeology & Stakeholder Engagement",

    # Classics & Ancient Languages
    "Latin (Reading, Translation)", "Ancient Greek (Attic, Koine)",
    "Sanskrit", "Akkadian & Cuneiform", "Egyptian Hieroglyphs (Middle Egyptian)",
    "Paleography (Latin, Greek Minuscule)", "Epigraphy & Inscription Recording",
    "Papyrology & Textual Reconstruction", "Numismatics (Coin Identification & Cataloging)",

    # Art History & Visual Culture
    "Art Historical Period Analysis", "Iconography & Iconology",
    "Visual Culture Theory", "Connoisseurship & Attribution",
    "Decorative Arts & Material Culture", "Architectural History & Styles",
    "Provenance Research", "Digital Art History & Image Archives",

    # Museum Studies & Curation
    "Exhibition Conceptualization & Narrative", "Object Selection & Layout",
    "Collections Management (CMS Databases, TMS)", "Condition Reporting & Handling",
    "Museum Registration & Cataloguing", "Preventive Conservation Basics (Light, RH, IPM)",
    "Museum Education & Public Programming", "Visitor Studies & Evaluation",
    "Museum Ethics & AAM/ICOM Standards",

    # Conservation & Heritage Science
    "Paintings Conservation (Cleaning, Lining)", "Paper & Book Conservation",
    "Textile Conservation", "Object Conservation (Ceramics, Metals, Wood)",
    "Architectural Conservation (Stone, Plaster, Timber)", "Preventive Conservation (Environmental Monitoring)",
    "Scientific Analysis (XRF, FTIR, Microscopy)", "Digital Restoration & Replication",

    # Archival Science & Records Management
    "Archival Appraisal & Accessioning", "Arrangement & Description (ISAD-G, DACS)",
    "Finding Aid Creation & EAD Encoding", "Digital Archives & Preservation (OAIS Model)",
    "Records Retention Scheduling & Disposition", "Privacy, GDPR & Ethical Access",
    "Preservation of Audiovisual & Born-Digital Materials",

    # Library & Information Science
    "Cataloguing & Classification (MARC, RDA, Dewey, LCC)", "Information Retrieval & Reference Services",
    "Information Literacy Instruction", "Collection Development & Weeding",
    "Digital Repositories & Institutional Archives", "Research Data Management",
    "Linked Data & Semantic Web for Culture",

    # Cultural Heritage Management & Policy
    "UNESCO World Heritage Nomination Process", "Cultural Resource Management (CRM) – Section 106/NEPA",
    "Heritage Impact Assessment (HIA)", "Site Management Planning",
    "Intangible Cultural Heritage (ICH) Safeguarding", "Heritage Law & International Conventions (Hague, UNIDROIT)",
    "Cultural Property Protection in Conflict", "Repatriation & Restitution Ethics",

    # Heritage Interpretation & Education
    "Interpretive Planning (Freeman Tilden Principles)", "Tour Guiding & Living History",
    "Exhibit Text & Label Writing", "Graphic Panel & Wayfinding Design",
    "Multi-Sensory & Accessible Interpretation", "Digital Storytelling & Virtual Tours",
    "Curriculum Development for Heritage Sites",

    # Anthropology & Cultural Studies
    "Ethnographic Fieldwork & Participant Observation", "Cultural Analysis & Semiotics",
    "Kinship & Social Structure Analysis", "Ritual & Symbolic Anthropology",
    "Medical Anthropology & Cultural Competence", "Applied & Advocacy Anthropology",
    "Visual Anthropology & Ethnographic Film",

    # Folklore & Ethnomusicology
    "Folk Narrative Collection & Indexing (ATU, Motif-Index)", "Field Recording & Transcription",
    "Traditional Music & Dance Documentation", "Oral Tradition & Performance Studies",
    "Material Folk Culture & Vernacular Architecture", "Foodways & Traditional Ecological Knowledge",

    # Linguistics & Language Documentation
    "Phonetic Transcription (IPA)", "Language Documentation & Description",
    "Endangered Language Revitalization", "Linguistic Field Methods",
    "Corpus Linguistics & Annotation", "Sociolinguistics & Language Policy",
    "Translation Studies & Skopos Theory",

    # Literature, Critical Theory & Writing
    "Close Reading & Literary Analysis", "Comparative World Literatures",
    "Genre & Narrative Theory", "Poetry & Poetics", "Creative Non-Fiction & Memoir",
    "Postcolonial & Decolonial Theory", "Feminist, Queer & Critical Race Theory",
    "Editing & Scholarly Publishing", "Manuscript Studies & Textual Editing",

    # Philosophy & Intellectual History
    "Logic & Argument Analysis", "Ethical Reasoning & Applied Ethics",
    "History of Philosophy (Ancient to Contemporary)", "Political & Legal Philosophy",
    "Aesthetics & Art Theory", "Phenomenology & Hermeneutics",
    "Philosophy of Science & Technology",

    # Digital Humanities
    "Text Encoding & TEI-XML", "Historical GIS & Spatial Analysis",
    "Network Analysis for Historical Data", "Topic Modeling & Distant Reading",
    "Data Visualization for Humanities", "Crowdsourcing & Citizen Humanities",
    "Computational Linguistics & Stylometry", "3D Modeling for Heritage (Photogrammetry, LiDAR)",

    # Preservation & Built Heritage
    "Historic Structure Reports", "Building Pathology & Condition Surveys",
    "Traditional Building Crafts (Masonry, Timber Framing, Lime Plaster)", "Adaptive Reuse & Heritage-Led Regeneration",
    "Historic Landscape Characterisation (HLC)", "Disaster Preparedness for Cultural Sites",

    # Professional & Soft Skills
    "Project Management for Cultural Projects", "Grant Writing for Humanities & Heritage (NEH, Getty, Horizon Europe)",
    "Research Ethics (Informed Consent, Community Collaboration)", "Stakeholder & Descendant Community Consultation",
    "Cultural Diplomacy & Soft Power", "Academic Writing & Peer-Review",
    "Interdisciplinary Teamwork", "Public Speaking & Lecture Preparation",
    "Copyright & IP for Cultural Materials", "Multilingual Proficiency (for Research & Translation)",
],
    "Personal Care & Wellness": [
    # Skincare & Esthetics
    "Facial Treatments (Cleansing, Extractions, Mask)", "Skin Analysis & Typing (Fitzpatrick, Baumann)",
    "Chemical Peels (AHA, BHA, TCA)", "Microdermabrasion & Dermaplaning",
    "Microneedling & Collagen Induction", "LED Light Therapy (Red, Blue, NIR)",
    "Hydrafacial & Oxygen Infusion", "Acne Management & Extraction Protocols",
    "Anti-Aging & Preventative Skincare", "Hyperpigmentation & Melasma Treatment",
    "Sensitive Skin & Rosacea Care", "Product Ingredient Knowledge (Retinoids, Peptides, Ceramides)",
    "Back Facials & Body Treatments", "Waxing & Threading (Full Body, Brazilian)",
    "Brow Lamination & Shaping", "Eyelash Extensions & Lifting",

    # Makeup Artistry
    "Color Theory & Undertone Matching", "Foundation Matching & Application",
    "Contouring, Highlighting & Strobing", "Smokey Eye & Cut Crease Techniques",
    "Bridal & Special Event Makeup", "Editorial & Avant-Garde Makeup",
    "Airbrush Makeup", "SFX (Special Effects) Makeup Basics",
    "Prosthetic Application & Bald Cap", "Male Grooming & Natural Makeup",
    "Clean Beauty & Hypoallergenic Methods",

    # Nail Care & Nail Art
    "Manicure & Pedicure (Basic & Spa)", "Gel Polish Application & Removal",
    "Acrylic & Dip Powder Systems", "Nail Art (Freehand, Stamping, 3D)",
    "Nail Health & Disorder Recognition", "Electric File (E-File) Techniques",
    "Press-On & Custom Nail Design", "Pedicure for Diabetic/Medical Clients",

    # Hair Care & Styling
    "Hair Cutting (Precision, Texturizing, Razor)", "Blowout & Thermal Styling",
    "Updos, Chignons & Bridal Hair", "Braiding & Cornrowing",
    "Hair Relaxing & Keratin Treatments", "Perming & Waving (Basic & Digital)",
    "Color Theory & Formulation (Permanent, Demi, Semi)", "Balayage, Ombre & Foiling Techniques",
    "Color Correction & Bleaching", "Men's Barbering (Fades, Clipper Work, Straight Razor Shave)",
    "Beard & Mustache Grooming", "Scalp Analysis & Treatment (Dandruff, Psoriasis)",

    # Massage Therapy & Bodywork
    "Swedish / Relaxation Massage", "Deep Tissue Massage",
    "Sports & Stretching Massage", "Trigger Point Therapy",
    "Hot Stone Massage", "Prenatal / Pregnancy Massage",
    "Lymphatic Drainage (Manual, Vodder Technique)", "Reflexology (Foot, Hand, Ear)",
    "Myofascial Release", "Cupping Therapy", "Aromatherapy & Essential Oil Blending",

    # Spa & Body Treatments
    "Body Wraps (Detox, Hydrating, Seaweed)", "Body Scrubs & Polishes",
    "Vichy Shower & Hydrotherapy", "Steam & Sauna Protocol",
    "Spa Manicure/Pedicure (Paraffin, Hot Stone)", "Couples' Treatment Sequencing",
    "Spa Reception & Journey Design",

    # Fitness & Personal Training
    "Fitness Assessment (PAR-Q, Body Comp, VO2max)", "Program Design & Periodization",
    "Strength & Resistance Training (Free Weights, Machines)", "Functional & Movement Pattern Training",
    "Cardiovascular Conditioning (HIIT, LISS)", "Flexibility & Mobility Training",
    "Core Stability & Balance Training", "Injury Prevention & Corrective Exercise",
    "Pre/Post-Natal Exercise Prescription", "Senior Fitness & Fall Prevention",

    # Pilates, Yoga & Mind-Body Disciplines
    "Mat Pilates (Classical & Contemporary)", "Pilates Reformer & Apparatus",
    "Yoga Asana Sequencing (Hatha, Vinyasa)", "Pranayama & Breathwork",
    "Kundalini & Chakra Balancing", "Restorative & Yin Yoga",
    "Meditation Guidance (Mindfulness, TM, Body Scan)", "Tai Chi & Qigong Instruction",
    "Barre & Fusion Class Design",

    # Nutrition & Dietary Coaching
    "Macronutrient & Micronutrient Analysis", "Meal Planning & Prep",
    "Weight Management & Energy Balance", "Sports Nutrition Basics",
    "Special Diets (Keto, Vegan, Paleo, FODMAP)", "Supplements & Nutraceuticals",
    "Intuitive Eating & Mindful Eating Coaching", "Food Allergy & Sensitivity Awareness",
    "Gut Health & Microbiome Basics",

    # Health & Wellness Coaching
    "Health Risk Assessment & Wellness Inventory", "Behavior Change Models (Transtheoretical, MI)",
    "Motivational Interviewing for Wellness", "Goal Setting (SMART, HARD, WOOP)",
    "Accountability & Follow-Up Systems", "Positive Psychology Interventions",
    "Holistic Lifestyle Planning", "Chronic Disease Self-Management Support",

    # Mental & Emotional Wellness
    "Stress Management Technique Instruction", "Guided Imagery & Visualization",
    "Emotional Freedom Technique (EFT / Tapping)", "Journaling & Expressive Writing Facilitation",
    "Sleep Hygiene & CBT-I Basics", "Digital Detox & Tech-Life Balance",
    "Forest Bathing & Nature Therapy", "Laughter & Joy Coaching",

    # Energy & Holistic Healing
    "Reiki (Level I, II, Master)", "Crystal Healing & Layouts",
    "Sound Healing & Tuning Fork Therapy", "Chakra Assessment & Balancing",
    "Acupressure & Meridian Theory", "Ayurvedic Body Types (Dosha) & Lifestyle",
    "Holistic Iridology Basics",

    # Beauty Technology & Devices
    "Laser Hair Removal (IPL & Diode Basics)", "Radiofrequency (RF) for Tightening",
    "Cryolipolysis & Body Contouring Basics", "Ultrasound Cavitation",
    "Spray Tan Application (HVLP & Airbrush)", "Permanent Makeup / Microblading (PMU)",
    "Tattoo Removal Basics (Laser)",

    # Salon & Spa Business Management
    "Client Consultation & Record Management", "Retail & Product Sales (Scripting, Upselling)",
    "Booth Rental & Independent Contractor Management", "Salon/Studio Software (Boulevard, Mindbody, Vagaro)",
    "Sanitation, Sterilization & State Board Compliance", "OSHA & Safety Data Sheets (SDS)",
    "Loyalty Programs & Rebooking Systems",

    # Personal Styling & Image Consulting
    "Body Shape Analysis & Wardrobe Audit", "Color Analysis (Seasonal, Tonal)",
    "Personal Shopping & Capsule Wardrobe", "Accessories & Jewelry Selection",
    "Virtual Styling & Digital Closet", "Corporate Image & Executive Presence",

    # Hygiene & Sanitation (Personal Care Context)
    "Infection Control & Sterilization (Autoclave, Barbicide)", "Bloodborne Pathogens Standard",
    "Patch Testing & Allergy Precautions", "Tools & Equipment Maintenance",
    "Personal Protective Equipment (PPE) Proper Use",

    # Professional Boundaries & Ethics
    "Informed Consent & Intake Forms", "Contraindication Recognition & Referral",
    "Client Privacy & HIPAA for Wellness Professionals", "Scope of Practice Awareness",
    "Draping & Modesty Protocols", "Self-Care & Burnout Prevention for Practitioners",

    # Communication & Client Experience
    "Building Rapport & Trust", "Active Listening & Emotional Presence",
    "Consultation Customization", "Managing Difficult Client Conversations",
    "Empathy & Non-Judgment", "Cross-Cultural Sensitivity in Beauty & Wellness",
],
    "Domestic & Household Management": [
    # Home Cleaning & Organization
    "Routine Cleaning & Chore Scheduling", "Decluttering & Space Optimization (KonMari, Swedish Death Cleaning)",
    "Deep Cleaning (Ovens, Refrigerators, Grout, Windows)", "Natural/Green Cleaning Methods (Vinegar, Baking Soda)",
    "Floor Care (Hardwood, Tile, Carpet, Steam Cleaning)", "Surface-Specific Disinfection & Sanitization",
    "Organizing Closets, Pantries & Storage Units", "Seasonal Cleaning & Wardrobe Rotation",
    "Dust Control & Allergen Reduction", "Professional Housekeeping Protocols",

    # Cooking & Meal Management
    "Menu Planning (Weekly, Monthly)", "Grocery Shopping & Pantry Stocking",
    "Food Budgeting & Price Comparison", "Meal Prep & Batch Cooking",
    "Special Diet Management (Gluten-Free, Diabetic, Halal, Kosher)", "Nutritional Balance & Portion Control",
    "Table Setting & Service Etiquette (Formal, Informal)", "Waste-Free & Root-to-Stalk Cooking",
    "Cooking for Large Groups & Freezer Meals", "Feeding Infants, Children & Picky Eaters",

    # Laundry & Fabric Care
    "Laundry Sorting (Fiber, Color, Soil Level)", "Stain Identification & Treatment (Protein, Tannin, Oil)",
    "Machine Washing & Drying Settings", "Hand Washing Delicates (Silk, Wool, Lace)",
    "Ironing, Steaming & Pressing Techniques", "Fabric Softening & Scent Customization",
    "Clothing Repair (Buttons, Hems, Zippers)", "Sweater Shaving & Pilling Removal",
    "Linen & Bedding Care (Hospital Corners)", "Leather & Suede Care Basics",

    # Household Finance & Administration
    "Household Budgeting & Cash Flow Tracking", "Bill Payment & Subscription Management",
    "Filing Systems (Medical, Insurance, Tax, Warranties)", "Insurance Policy Management (Home, Auto, Life)",
    "Identity & Privacy Protection at Home", "Tax Preparation & Home Office Deductions",
    "Long-Term Home Maintenance Fund Planning",

    # Home Maintenance & Repairs
    "Basic Plumbing (Unclogging, Toilet Flapper, Faucet Washer Replacement)",
    "Basic Electrical (Resetting Breakers, Replacing Outlets, Light Fixture Install)",
    "Painting & Touch-Up (Cutting In, Patch, Sand)", "Caulking & Weatherproofing",
    "Drywall Repair (Holes, Cracks)", "Furniture Assembly & Anchoring",
    "Appliance Troubleshooting (Dishwasher, Washer, Dryer)", "HVAC Filter Replacement & Maintenance",
    "Sump Pump & Water Heater Basics", "Pest Prevention & Rodent Proofing",

    # Gardening & Outdoor Maintenance
    "Lawn Mowing, Edging & Seasonal Fertilizing", "Weeding, Mulching & Bed Maintenance",
    "Container & Raised-Bed Vegetable Gardening", "Pruning Shrubs, Roses & Small Trees",
    "Composting (Hot, Cold, Vermicomposting)", "Rainwater Harvesting & Irrigation Timer Setup",
    "Snow Removal & Ice Treatment", "Outdoor Furniture Care & Storage",
    "Basic Pest & Disease Identification (Non-Toxic Control)", "Houseplant Care & Propagation",

    # Child & Family Care Management
    "Daily Routine & Transitions (Meals, Naps, School)", "Age-Appropriate Activity & Play Planning",
    "School & Extracurricular Coordination", "Childproofing & Home Safety",
    "Pediatric First Aid & Fever Management", "Developmental Milestone Awareness",
    "Potty Training & Sleep Training Methods", "Managing Screen Time & Digital Safety",
    "Family Meeting & Chore Charts Design",

    # Elder & Special Needs Care
    "Medication Management & Reminder Systems", "Mobility Aid & Fall-Proofing the Home",
    "Dementia & Cognitive Decline Home Modifications", "Respite & Caregiver Support Planning",
    "Transportation & Appointment Coordination",
    "Special Diet & Mealtime Assistance",

    # Pet Care & Management
    "Pet Feeding & Hydration Routines", "Grooming (Brushing, Bathing, Nail Trimming)",
    "Litter Box & Waste Cleanup Protocols", "Exercise & Enrichment Activities",
    "Basic Obedience Training & Commands", "Medication Administration (Pill, Topical)",
    "Veterinary & Vaccination Scheduling", "Pet First Aid & Poison Control Basics",
    "Aquarium & Small Animal Habitat Maintenance",

    # Home Décor & Curating
    "Furniture Layout & Space Planning", "Color Palette & Textile Coordination",
    "Lighting for Mood & Task", "Art & Frame Hanging (Leveling, Picture Rail)",
    "Seasonal & Holiday Decorating", "Vignette & Shelf Styling",
    "Upcycling & DIY Home Projects",

    # Food Preservation & Storage
    "Canning (Water Bath, Pressure)", "Freezing & Blanching Protocols",
    "Dehydrating (Fruits, Herbs, Jerky)", "Fermenting (Sauerkraut, Kimchi, Kombucha)",
    "Root Cellaring & Cold Storage", "Vacuum Sealing & Oxygen Absorbers",

    # Sewing, Mending & Textiles
    "Hand Sewing & Hemming", "Sewing Machine Operation & Basic Projects",
    "Patching & Darning (Visible Mending)", "Curtain & Drape Measuring/Shortening",
    "Upholstery Cleaning & Simple Recover",

    # Home Technology & Smart Home
    "Smart Home Hub & Automation (Alexa, Google Home)", "Wi-Fi Mesh & Network Troubleshooting",
    "Security Cameras & Video Doorbell Setup", "Smart Thermostat & Zoning",
    "Appliance Connectivity & Remote Control", "Digital Family Calendar & Task Sharing",

    # Safety & Emergency Preparedness
    "Fire Escape Plan & Ladder Use", "Smoke/CO Detector Testing & Battery Rotation",
    "Flood & Severe Weather Kit Preparation", "Emergency Contact & Medical Info Sheet",
    "Poison Control & Hazardous Product Locking",
    "Basic First Aid & CPR for Household",

    # Hospitality & Entertaining
    "Event Planning & Timeline (Dinners, Holidays, Parties)", "Guest Room Preparation & Welcome",
    "Buffet, Plated & Cocktail Service Coordination", "Hosting Overnight Guests & Long-Term Visitors",
    "Menu Planning for Entertaining (Dietary Restrictions)",

    # Sustainability & Waste Management
    "Zero-Waste Home Practices", "Recycling & Composting Guidelines Compliance",
    "E-Waste & Hazardous Waste Disposal", "Upcycling & Repair Café Principles",
    "Sustainable Product Swaps & DIY Cleaning",

    # Inventory & Home Administration Binder
    "Pantry, Freezer & Household Supply Inventory", "Home Maintenance Log & Contractor Contacts",
    "Digital & Physical Receipt Management", "Passport, ID & Vital Records Safe Storage",

    # Personal Concierge & Errand Running
    "Vendor Coordination & Supervision (Cleaners, Landscapers)", "Returns, Exchanges & Warranty Claims",
    "Mail & Package Hold/Forwarding", "Gift Purchasing & Wrapping",
    "Donation Pickup & Disposal Scheduling",

    # Time Management & Household Systems
    "Family Command Center Setup", "Chore Rotation & Scheduling (Daily/Weekly/Monthly)",
    "Time Blocking for Errands & Meal Prep", "Project Management for Renovation or Move",
    "Executive Function Supports & ADHD Home Strategies",

    # Specialized Domestic Professions
    "Butler & Valet Service (Wardrobe, Shoe Shine)", "Estate & Household Staff Management",
    "Silver, Crystal & Fine China Care", "Wine Cellar & Spirits Inventory",
    "Fine Art & Antique Care & Rotation",
],
    "Languages, Linguistics & Translation": [
    # Core Linguistics
    "Phonetics & Phonology", "Morphology & Word Formation",
    "Syntax & Sentence Structure", "Semantics & Pragmatics",
    "Historical & Comparative Linguistics", "Sociolinguistics & Dialectology",
    "Psycholinguistics & Neurolinguistics", "Cognitive Linguistics",
    "Corpus Linguistics & Annotation", "Discourse Analysis & Conversation Analysis",
    "Typology & Language Universals", "Anthropological Linguistics",

    # Language Documentation & Fieldwork
    "Field Methods & Elicitation", "Endangered Language Documentation",
    "Language Revitalization & Reclamation", "Community-Based Language Research",
    "Transcription (IPA, Orthographic, ELAN)", "Metadata Creation & Archiving",

    # Language Acquisition & Learning
    "First Language Acquisition", "Second Language Acquisition (SLA) Theory",
    "Bilingualism & Multilingualism", "Heritage Language Learning",
    "Immersion & Content-Based Instruction", "Language Assessment & Proficiency Testing (ACTFL, CEFR)",
    "Error Analysis & Corrective Feedback", "Language Learning Strategies & Self-Regulation",

    # Translation (Written)
    "Source Text Analysis & Interpretation", "Target Text Composition & Adaptation",
    "Literary Translation (Fiction, Poetry)", "Technical & Scientific Translation",
    "Legal & Certified Translation", "Medical & Pharmaceutical Translation",
    "Financial & Commercial Translation", "Transcreation & Marketing Copy",
    "Machine Translation Post-Editing (MTPE)", "Subtitling & Captioning (Intralingual & Interlingual)",
    "Video Game & Software Localisation (L10n)", "Website & eCommerce Localisation",

    # Interpreting (Spoken/Signed)
    "Consecutive Interpreting (Observe, Recall, Render)", "Simultaneous Interpreting (Booth, Whispering)",
    "Sight Translation", "Liaison & Bilateral Interpreting",
    "Community & Medical Interpreting", "Court & Legal Interpreting",
    "Conference Interpreting (AIIC standards)", "Telephone & Remote Interpreting (VRI/OPI)",
    "Note-Taking for Consecutive Interpreting (Rozan, Symbols)",

    # Sign Language & Deaf Studies
    "Sign Language Proficiency (ASL, BSL, LSF, etc.)", "Deaf Culture & Identity",
    "Sign Linguistics (Phonology, Morphology)", "Interpreting for Deaf-Blind (Tactile, Pro-Tactile)",

    # Terminology & Lexicography
    "Terminology Extraction & Management", "Glossary & Termbase Creation (TBX, MultiTerm)",
    "Lexicography (Monolingual & Bilingual Dictionaries)", "Neologism & Coinage Decision-Making",

    # Revision, Editing & Quality Assurance
    "Proofreading & Copyediting (Multilingual)", "Style Guide Adherence (Chicago, Microsoft, Custom)",
    "Quality Assurance Metrics (LISA, DQF/MQM)", "Peer Review & Bureau Editing",

    # Translation Technology & CAT Tools
    "CAT Tools (Trados Studio, memoQ, Wordfast, OmegaT)", "Translation Management Systems (TMS – XTM, Smartling, Phrase)",
    "Machine Translation Engines (NMT, GPT-based)", "Regular Expressions & File Parsing for Localisation",
    "Aligning Parallel Texts", "OCR & Text Extraction for Translation",

    # Computational Linguistics & NLP
    "Part-of-Speech (POS) Tagging & Parsing", "Named Entity Recognition (NER)",
    "Sentiment Analysis", "Machine Translation System Customisation",
    "Speech Recognition & Text-to-Speech Alignment", "Python for NLP (NLTK, spaCy, Hugging Face)",
    "LLM Prompt Engineering for Language Tasks", "Tokenisation & Language Model Evaluation",

    # Language-Specific Mastery (Foundation skills for any working language)
    "Grammar & Syntax Mastery (L1 & L2)", "Vocabulary Range & Register Differentiation",
    "Idiomatic & Cultural Fluency", "Pronunciation & Accent Reduction/Coaching",
    "Script & Orthographic Mastery (Latin, Cyrillic, Arabic, CJK, etc.)",

    # Professional Language Services
    "Freelance Translation Business Management", "Translation Project Management (Agile, Waterfall)",
    "Client Consultation & Quote Preparation", "Confidentiality & Data Security (GDPR, NDA)",
    "Continuing Professional Development (ATA, ITI, CIOL)", "Ethical Decision-Making for Translators/Interpreters",
    "Language Services Vendor Management", "CAT Tool Training & Instructional Design",

    # Cross-Cultural Communication
    "Intercultural Competence & Sensitivity", "Cultural Adaptation & Localisation Strategy",
    "Non-Verbal Communication Across Cultures", "Cultural Dimensions Frameworks (Hofstede, Hall)",

    # Literacy & Language Arts
    "Phonics & Reading Instruction", "Writing Tutoring & Composition Coaching",
    "ESL/EFL Curriculum Development", "Grammar Pedagogy", "Adult Literacy Tutoring",

    # Forensic & Legal Linguistics
    "Authorship Attribution & Stylometry", "Linguistic Fingerprinting for Law Enforcement",
    "Trademark & Brand Name Linguistic Analysis", "Emergency Call & Voir Dire Interpretation Analysis",

    # Soft & Support Skills
    "Active Listening Across Languages", "Memory & Recall Enhancement (for Interpreting)",
    "Stress Management & Interpreter Self-Care", "Confidence in Public Service Interpreting",
    "Simultaneous Multi-Device Workflow", "Time Estimation & Deadline Management for Language Tasks",
],
    "Library & Information Sciences": [
    # Cataloguing & Classification
    "Descriptive Cataloguing (MARC21, Dublin Core, RDA)", "Subject Classification (Dewey Decimal, Library of Congress Classification)",
    "Subject Heading Assignment (LCSH, MeSH, Sears)", "Authority Control & Name Authority Records (NACO)",
    "FRBR, LRM & RDF-Based Cataloguing (BIBFRAME)", "Copy Cataloguing & Record Enhancement",
    "Original Cataloguing for Rare & Special Collections", "Metadata Schema Design (MODS, EAD, VRA Core)",

    # Collection Development & Management
    "Collection Analysis & Assessment (Usage Statistics, Overlap)", "Selection & Acquisitions (Physical & Digital)",
    "Deaccessioning & Weeding (MUSTIE, CREW Methods)", "Collection Development Policy Writing",
    "Database & E-Resource Licensing & Negotiation", "Serials & Standing Order Management",
    "Gifts & Donations Processing & Policies", "Intellectual Freedom & Challenged Materials Response",

    # Reference & Research Services
    "Reference Interview Techniques (In-Person, Chat, Email)", "Ready Reference & Quick Information Retrieval",
    "In-Depth Research Consultation & Literature Review", "Citation Management Support (Zotero, EndNote, Mendeley)",
    "Readers' Advisory (Fiction & Non-Fiction)", "Government Documents & UN Depository",
    "Business & Legal Reference", "Health / Consumer Health Information Services",
    "Genealogy & Local History Research",

    # Information Literacy & Instruction
    "Information Literacy Framework (ACRL, ANZIIL, SCONUL)", "One-Shot Library Instruction Session Design",
    "Course-Integrated & Embedded Librarianship", "Credit Course Design & Syllabus Writing",
    "Tutorial & LibGuide Creation (Springshare, LibGuides, Canvas)", "Database & Search Strategy Instruction",
    "Fake News & Misinformation Literacy", "Digital & Media Literacy Curriculum",

    # Digital Libraries & Repositories
    "DSpace, Fedora, Islandora, Samvera Administration", "Institutional Repository Management & Scholarly Communications",
    "Digital Preservation Formats & Migration (PDF/A, TIFF, WAV)", "Open Access Policy & APC Administration",
    "Research Data Management & Data Management Plans (DMP)", "Open Educational Resources (OER) Curation & Advocacy",
    "Linked Data & Semantic Web for Libraries",

    # Archives & Special Collections
    "Archival Arrangement (Provenance, Original Order)", "Finding Aid Creation & EAD Encoding (ArchivesSpace)",
    "Photograph & A/V Material Handling & Preservation", "Digital Curation & OAIS-Compliant Workflows",
    "Records Retention Scheduling & Appraisal", "Rare Book & Manuscript Handling & Exhibition",
    "Oral History Collection Management & Transcription",

    # Library Technology & Systems
    "Integrated Library System (ILS/LSP) Administration (Alma, Sierra, Koha, Evergreen)",
    "Discovery Layer & Federated Search Configuration (Primo, EDS, Summon)",
    "Link Resolver & Proxy/EZProxy/OpenAthens Management", "Library Website Design & UX",
    "Makerspace Equipment & Programming (3D Printers, Laser Cutters, VR)",
    "Self-Checkout & Automated Materials Handling",

    # User Services & Access
    "Circulation & Reserves (Course, Electronic, Media)", "Interlibrary Loan & Document Delivery (ILLiad, Rapido)",
    "Student Worker & Volunteer Supervision", "Accessibility Services & Assistive Technology",
    "Library Space Design & Space Assessment", "Community Outreach & Programming (All Ages)",
    "Children's & Young Adult Program Planning", "Adult & Senior Services Programming",
    "Cultural & Heritage Programming",

    # Youth & School Librarianship
    "Children's Literature & Media Curation", "Storytime Planning & Early Literacy Practices (ECRR)",
    "K-12 Information Literacy Standards (AASL, ISTE)", "Reading Promotion & Summer Reading Program Design",
    "Teen Advisory Group Facilitation", "Book Talking & Author Visit Coordination",

    # Data & Research Services
    "Bibliometric & Research Impact Analysis (h-index, JIF)", "Data Visualization Support (Tableau for Libraries)",
    "Text & Data Mining Support", "Systematic Review Searching (PRISMA Guidelines)",
    "GIS & Spatial Data Support (ArcGIS for Libraries)", "Data Curation Profile & Repository Planning",

    # Library Management & Administration
    "Library Strategic Planning", "Library Budget Preparation & Allocation",
    "Grant Writing for Libraries (IMLS, LSTA, Foundation)", "HR & Staff Development (Performance Reviews, Training Plan)",
    "Facilities & Emergency Planning", "Library Policy Development (Patron Behavior, Meeting Room)",

    # Assessment & Evaluation
    "User Experience (UX) & Usability Testing in Libraries", "Patron Satisfaction Surveys & Focus Groups",
    "Library Assessment (LibQUAL+, Balanced Scorecard)", "Annual Reporting & Data-Driven Advocacy",
    "Gate Count & Circulation Data Analysis",

    # Marketing, Advocacy & Communication
    "Library Branding & Graphic Design (Canva, Adobe)", "Social Media Strategy (Twitter/X, Instagram, TikTok)",
    "Library Newsletter & Blog Management", "Community & Stakeholder Relationship Building",
    "Friends & Foundation Support Group Cultivation", "Legislative & Budget Advocacy for Libraries",

    # Professional Ethics & Trends
    "ALA Bill of Rights & Code of Ethics", "Privacy & Confidentiality (Patron Records, RFID, FERPA)",
    "Copyright, Fair Use & Creative Commons (Library Context)", "Equity, Diversity, Inclusion & Anti-Racism in Libraries",
    "Trauma-Informed Librarianship", "Book Banning & Censorship Preparedness",
    "Green Libraries & Sustainable Library Practices",
    "Emergency Preparedness & Cultural Property Protection",
],
    "Mind Sports & Strategic Gaming": [
    # Chess – Core Skills
    "Opening Principles & Repertoire", "Middlegame Planning & Piece Coordination",
    "Endgame Theory (King & Pawn, Rook, Minor Pieces)", "Calculation & Visualization (Deep Lines)",
    "Pattern Recognition (Tactics: Pins, Forks, Skewers)", "Positional Evaluation & Static Analysis",
    "Pawn Structure & Weakness Exploitation", "Prophylaxis & Opponent's Plans",
    "Time Management & Clock Usage", "Blitz & Rapid Adaptation",

    # Chess – Advanced & Specialized
    "Correspondence & Engine-Assisted Analysis", "Chess960 / Fischer Random Strategy",
    "Opening Preparation & Novelty Research", "Computer-Aided Training (Engines, Databases)",
    "Tournament Psychology & Stamina", "Handling Drawish Positions & Swindles",

    # Go / Baduk / Weiqi
    "Opening Theory (Fuseki & Joseki)", "Life-and-Death (Tsumego) Problem Solving",
    "Tesuji (Tactical Moves) & Shape Recognition", "Endgame Counting & Ko Fights",
    "Whole-Board Thinking & Direction of Play", "Influence vs. Territory Evaluation",
    "Handicap & Teaching Game Strategy", "Go AI-Assisted Review (KataGo, Leela Zero)",

    # Shogi (Japanese Chess)
    "Opening Strategies (Static Rook, Ranging Rook)", "Tsume (Checkmate Problem) Solving",
    "Piece Drop Tactics & Counter-Drops", "Castle Building (Mino, Anaguma, Boat)",
    "Endgame Speed Calculation (Brinkmate)",

    # Xiangqi (Chinese Chess)
    "Opening Phase (Cannon, Horse, Pawn)", "Midgame Attack & Defense", "Checkmate Patterns Under Palace Rules",
    "Sacrifice & Exchange Evaluation", "Endgame Precision & Repetition Rules",

    # Bridge (Contract Bridge)
    "Bidding System Mastery (Standard American, Acol, Precision)", "Card Play Technique (Finesse, Squeeze, Endplay)",
    "Defensive Signaling (Attitude, Count, Suit Preference)", "Declarer Play Planning & Danger Hand Avoidance",
    "Duplicate Bridge Strategy & Matchpoints", "Convention Usage & Partnership Tuning",

    # Poker (Texas Hold'em, Tournament & Cash)
    "Hand Selection & Pre-flop Ranges", "Post-flop Play: Continuation Betting & Pot Control",
    "Implied Odds & Reverse Implied Odds", "Bluffing & Semi-Bluffing Frequencies",
    "Player Profiling & Exploitative Adjustments", "Tournament ICM (Independent Chip Model) Decisions",
    "Bankroll Management & Tilt Control",

    # Bridge, Mahjong & Other Card Games
    "Mahjong (Riichi, MCR) Tile Efficiency & Defense", "Spades & Hearts Advanced Play",
    "Canasta / Pinochle Strategic Play", "Tarot / Tarock Bidding & Point Optimization",

    # Scrabble & Word Games
    "Word Knowledge & Anagramming Speed", "Tile Tracking & Bag Management",
    "Board Geometry & Triple-Word Setup", "Rack Leave & Balance (Consonants/Vowels)",
    "Bingos & High-Probability Hooks",

    # Backgammon & Dice-Based Strategy
    "Opening Move Theory (Splitting, Slotting, Running)", "Prime & Blitz Structures",
    "Holding & Back Game Plans", "Cube (Doubling Cube) Decision & Equity Math",
    "Race Calculations (Efficient Pip Count)", "Match Score & Crawford Rule Logic",

    # Abstract Strategy Games (General)
    "Spatial Thinking & Territory Control (Reversi/Othello)", "Pattern & Connection Strategy (Connect Four/Hex)",
    "Mancala Family Strategy & Counting", "Abalone & Push-Fight Mechanics",

    # eSports Strategy Games (RTS)
    "Real-Time Strategy (RTS) Macro & Micro (StarCraft, Age of Empires)", "Build Order Optimization & Timing Attacks",
    "Resource Management & Expansion Rate", "Map Awareness & Minimap Reading",
    "APM (Actions Per Minute) & Hotkey Efficiency", "Scouting & Fog of War Information Processing",

    # eSports Strategy Games (MOBA & Autobattler)
    "MOBA Draft Phase & Team Composition (LoL, Dota 2)", "Laning Phase Mechanics & Wave Control",
    "Vision Control & Warding", "Objective Trading & Rotations", "Itemization & Adaptive Build Paths",
    "Autobattler Economy & Positioning (TFT, Hearthstone Battlegrounds)",

    # eSports Strategy Games (CCG & Tactical)
    "Collectible Card Game (CCG) Meta Analysis & Deckbuilding (Magic, Hearthstone)",
    "Value Trading & Tempo Calculation in CCGs", "Turn-Based Tactical Positioning (XCOM, Into the Breach)",
    "Probability & Risk Assessment in Digital Card Draw",

    # General Mind Sports Psychology
    "Mental Endurance & Concentration", "Tilt Management & Emotional Regulation",
    "Handling Time Pressure & Low Time Panic", "Confidence Without Overconfidence",
    "Pre-Game & Pre-Move Routines", "Post-Game Analysis & Self-Reflection",

    # Game Analysis & Post-Mortem
    "Self-Review Without Engine First", "Computer Engine Use & Interpretation",
    "Error Categorization (Blunder, Mistake, Inaccuracy)", "Opponent Pattern Exploitation",
    "Notation & Game Recording (PGN, SGF, etc.)",

    # Memory & Calculation
    "Blindfold & Memory Palace Techniques", "Pattern & Opening/Variation Memorization",
    "Long Variations & Candidate Move Trees", "Probability Calculation & Expected Value (EV)",

    # Time Management & Clock Skills
    "Time Allocation per Move Phase", "Increment & Delay Usage Strategy",
    "Byoyomi / Sudden Death Tactics", "Playing in Time Scramble",

    # Tournament & Competition Skills
    "Tournament Preparation & Scouting Opponents", "Handling Draw Offers & Sportsmanship",
    "Dealing with Distractions & Venue Conditions", "Online vs. OTB Adaptability",
    "Ranking & Rating System Understanding (Elo, Glicko, MMR)",

    # Coaching, Training & Pedagogy
    "Lesson Plan Creation for Mind Sports", "Analytic Game Review with Students",
    "Creating Training Puzzles & Exercises", "Giving Clear Feedback & Encouragement",
    "Youth Talent Identification & Development",

    # Tactics, Logic & Puzzles (General)
    "Sudoku & Logic Puzzle Optimization (X-Wing, Swordfish)", "Killer Sudoku & Kakuro Calculation",
    "Nonogram / Picross Deduction", "KenKen & Mathdoku Speed",
    "Escape Room Puzzle Logic & Pattern Finding",

    # eSports & Digital Strategy: Team Roles & Leadership
    "In-Game Leader (IGL) Shot Calling (CS:GO, Valorant)", "Captaincy & Coordination in Team Mind Sports",
    "Role Specialization & Meta Adaptation",

    # Additional Niche Mind Sports
    "Checkers / Draughts Endgame Database Use", "Abstractions (Hex, Y, Twixt)",
    "GIPF Project Game Strategies", "Quoridor & Blocking Path Strategy",
    "Hive (Insect-Themed) Opening & Tactics",

    # Soft & Interpersonal in Competitive Play
    "Table Presence & Reading Opponent Tells", "Poker Face & Concealing Emotions",
    "Sportsmanship & Grace in Defeat", "Negotiation Skills (Bridge/Contract)",

    # Game Design & Theory (Applied)
    "Game Theory Optimal (GTO) Play Concept", "Nash Equilibrium Application", "Exploit vs. Balance Decision",
    "Meta-Game Cycles & Adaptation",
],
}



def seed():
    db = SessionLocal()
    try:
        inserted_categories = 0
        inserted_skills = 0

        for category_name, skills in SKILL_DATA.items():
            # Skip if already exists
            existing = db.query(SkillCategory).filter_by(name=category_name).first()
            if existing:
                category = existing
            else:
                category = SkillCategory(name=category_name)
                db.add(category)
                db.flush()  # get the id
                inserted_categories += 1

            for skill_name in skills:
                already = (
                    db.query(PredefinedSkill)
                    .filter_by(name=skill_name, category_id=category.id)
                    .first()
                )
                if not already:
                    db.add(PredefinedSkill(name=skill_name, category_id=category.id))
                    inserted_skills += 1

        db.commit()
        print(f"✅ Seeded {inserted_categories} categories and {inserted_skills} skills.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
