import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.industry import Industry
from app.models.skill_benchmark import SkillBenchmark
from app.models.skill_gap_report import SkillGapReport
from app.models.user_profile import GuideStatus, UserProfile
from app.models.user_skill import UserSkill


logger = logging.getLogger(__name__)


FALLBACK_BENCHMARKS = [
    {"skill_name": "Financial Management", "minimum_required_level": 4, "weight": 3},
    {"skill_name": "Digital Marketing", "minimum_required_level": 3, "weight": 2},
    {"skill_name": "Market Research", "minimum_required_level": 4, "weight": 3},
]



class SkillGapService:
    """
    UC_11: Overview Skills Gap Identification service.
    Measures entrepreneur readiness by comparing user skills to market benchmarks.
    """

    @staticmethod
    def analyze_user_skills(db: Session, user_id: uuid.UUID) -> SkillGapReport:
        """
        UC_11: Basic Flow - Main entry point for triggering skill gap analysis.
        """
        # Gather and validate data from hierarchy and profile
        prepared_data = SkillGapService._prepare_data(db, user_id)
        
        if prepared_data.get("is_skipped"):
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "No skills found for analysis. Please complete the questionnaire."
            )
            
        # Perform comparison and weighted calculation
        analysis_result = SkillGapService._calculate_gaps(
            prepared_data["skills_to_analyze"],
            prepared_data["market_benchmarks"]
        )
        
        # Persist results to the database
        report = SkillGapService._save_report(
            db,
            user_id,
            analysis_result["report_data"],
            prepared_data["accuracy_status"],
            analysis_result["risk_level"]
        )
        
        return report

    @staticmethod
    def get_user_report(db: Session, user_id: uuid.UUID) -> Optional[SkillGapReport]:
        """
        Retrieves the most recent skill gap report for a specific user.
        """
        return db.query(SkillGapReport).filter(SkillGapReport.user_id == user_id).first()

    @staticmethod
    def skip_skills_questionnaire(db: Session, user_id: uuid.UUID) -> bool:
        """
        Updates the user profile to mark the guide status as skipped.
        """
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if profile:
            profile.guide_status = GuideStatus.SKIPPED
            db.commit()
            
            return True
            
        return False

    @staticmethod
    def _prepare_data(db: Session, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Hierarchical Data Preparation logic.
        Orders: Specialized Industry -> Main Category -> General.
        """
        user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
        
        if not user_skills:
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            if profile:
                profile.guide_status = GuideStatus.POSTPONED
                db.commit()
                
            return {"is_skipped": True}

        # Identify Industry Hierarchy for benchmarking
        business = db.query(Business).filter(Business.owner_id == user_id).first()
        industry_ids = []
        
        if business and business.industry_id:
            curr_industry = db.query(Industry).filter(Industry.id == business.industry_id).first()
            
            while curr_industry:
                industry_ids.append(curr_industry.id)
                
                if not curr_industry.parent_id:
                    break
                    
                curr_industry = db.query(Industry).filter(Industry.id == curr_industry.parent_id).first()
        
        general_industry = db.query(Industry).filter(Industry.level == 0).first()
        
        if general_industry:
            industry_ids.append(general_industry.id)

        all_benchmarks = db.query(SkillBenchmark).filter(SkillBenchmark.industry_id.in_(industry_ids)).all()
        
        market_benchmarks = {}
        
        for b_id in industry_ids:
            industry_benchmarks = [b for b in all_benchmarks if b.industry_id == b_id]
            
            for b in industry_benchmarks:
                if b.skill_name not in market_benchmarks:
                    market_benchmarks[b.skill_name] = {
                        "skill_name": b.skill_name,
                        "minimum_required_level": b.minimum_required_level,
                        "weight": getattr(b, "weight", 1.0)
                    }

        # Fallback to defaults if no benchmarks are found for the hierarchy
        if not market_benchmarks:
            logger.error("No benchmarks found for industry hierarchy. Using fallback model.")
            market_benchmarks_list = FALLBACK_BENCHMARKS
        else:
            market_benchmarks_list = list(market_benchmarks.values())

        skills_map = {s.skill_name: s.declared_level for s in user_skills}
        accuracy_status = "Validated"
        skills_to_analyze = []
        
        for mb in market_benchmarks_list:
            skill_name = mb["skill_name"]
            
            if skill_name in skills_map:
                skills_to_analyze.append({
                    "skill_name": skill_name,
                    "declared_level": skills_map[skill_name]
                })
            else:
                skills_to_analyze.append({
                    "skill_name": skill_name,
                    "declared_level": 0
                })
                accuracy_status = "Partially Accurate"
                
        return {
            "is_skipped": False,
            "skills_to_analyze": skills_to_analyze,
            "market_benchmarks": market_benchmarks_list,
            "accuracy_status": accuracy_status
        }

    @staticmethod
    def _calculate_gaps(
        user_skills: List[Dict[str, Any]], 
        benchmarks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Core logic engine for gap calculation and risk assessment.
        """
        report_data = []
        total_severity = 0.0
        is_perfect_match = True
        
        benchmark_map = {b["skill_name"]: b for b in benchmarks}
        
        try:
            for skill in user_skills:
                skill_name = skill["skill_name"]
                declared_level = skill["declared_level"]
                benchmark = benchmark_map.get(skill_name)
                
                if not benchmark:
                    continue
                    
                required_level = benchmark["minimum_required_level"]
                weight = benchmark["weight"]
                
                gap = required_level - declared_level
                has_gap = gap > 0
                
                if has_gap:
                    is_perfect_match = False
                    severity_score = gap * weight
                    total_severity += severity_score
                    
                    report_data.append({
                        "skill_name": skill_name,
                        "declared_level": declared_level,
                        "minimum_required_level": required_level,
                        "gap_size": gap,
                        "severity": str(severity_score),
                        "status": "Weak" if declared_level > 0 else "Missing",
                        "recommendation": f"Focus on improving {skill_name}."
                    })
                else:
                    report_data.append({
                        "skill_name": skill_name,
                        "declared_level": declared_level,
                        "minimum_required_level": required_level,
                        "gap_size": 0,
                        "severity": "0",
                        "status": "Proficient",
                        "recommendation": "Maintain your current level."
                    })
                    
        except Exception as e:
            logger.error(f"Gap calculation internal error: {str(e)}")
            
        if is_perfect_match:
            risk_level = "Low Risk"
        elif total_severity < 5.0:
            risk_level = "Medium Risk"
        else:
            risk_level = "High Risk"
            
        return {
            "report_data": report_data,
            "risk_level": risk_level
        }

    @staticmethod
    def _save_report(
        db: Session,
        user_id: uuid.UUID,
        data: List[Dict[str, Any]],
        accuracy: str,
        risk: str
    ) -> SkillGapReport:
        """
        Persists the gap analysis report to the database.
        """
        report = db.query(SkillGapReport).filter(SkillGapReport.user_id == user_id).first()
        
        if report:
            report.report_data = data
            report.accuracy_status = accuracy
            report.risk_level = risk
            report.is_outdated = False
        else:
            report = SkillGapReport(
                user_id = user_id,
                report_data = data,
                accuracy_status = accuracy,
                risk_level = risk,
                is_outdated = False
            )
            db.add(report)
            
        db.commit()
        db.refresh(report)
        
        return report

    @staticmethod
    def update_user_skills(
        db: Session, 
        user_id: uuid.UUID, 
        skills_data: List[Any]
    ) -> List[UserSkill]:
        """
        Updates cumulative user skills and marks analysis as outdated.
        """
        db.query(UserSkill).filter(UserSkill.user_id == user_id).delete()
        
        new_skills = [
            UserSkill(
                user_id = user_id,
                skill_name = s.skill_name,
                declared_level = s.declared_level
            )
            for s in skills_data
        ]
        
        db.add_all(new_skills)
        
        report = db.query(SkillGapReport).filter(SkillGapReport.user_id == user_id).first()
        
        if report:
            report.is_outdated = True
            
        db.commit()
        
        return new_skills