"""
Reports service for retrieving processed clinical reports
"""

import uuid
from typing import List
from sqlalchemy.orm import Session, joinedload
import structlog

from src.models.clinical import Report, Patient, LabTest
from src.models.reference import Organization
from src.schemas.clinical import ReportResponse, Observation, Patient as PatientSchema, Recommendation
from src.core.exceptions import ReportNotFoundError
from src.db.database import set_tenant_context

logger = structlog.get_logger()


class ReportsService:
    """Service for clinical reports"""
    
    def __init__(self, db: Session, tenant_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id
        set_tenant_context(db, str(tenant_id))
    
    async def get_report(self, report_id: uuid.UUID) -> ReportResponse:
        """Get structured clinical report with observations"""
        
        # Query report with related data
        report = self.db.query(Report).options(
            joinedload(Report.patient),
            joinedload(Report.performer_organization)
        ).filter(
            Report.id == report_id
        ).first()
        
        if not report:
            raise ReportNotFoundError(str(report_id))
        
        # Get lab tests for this report
        lab_tests = self.db.query(LabTest).filter(
            LabTest.document_id == report.document_id
        ).order_by(LabTest.collected_at.desc()).all()
        
        # Convert to response format
        return ReportResponse(
            report_id=report.id,
            patient=self._convert_patient(report.patient),
            category=report.category,
            title=report.title,
            conclusion_text=report.conclusion_text,
            summary_pt=report.summary_pt,
            recommendations=self._convert_recommendations(report.recommendations or []),
            observations=self._convert_observations(lab_tests),
            status=report.status,
            issued_at=report.issued_at,
            effective_period={
                "start": report.effective_period_start,
                "end": report.effective_period_end
            } if report.effective_period_start else None,
            performer_organization=self._convert_organization(report.performer_organization),
            provenance=None,  # TODO: Load provenance data
            created_at=report.created_at,
        )
    
    def _convert_patient(self, patient: Patient) -> PatientSchema:
        """Convert Patient model to schema"""
        age_years = None
        if patient.date_of_birth:
            from datetime import date
            today = date.today()
            age_years = today.year - patient.date_of_birth.year
            if today.month < patient.date_of_birth.month or \
               (today.month == patient.date_of_birth.month and today.day < patient.date_of_birth.day):
                age_years -= 1
        
        return PatientSchema(
            patient_id=patient.id,
            external_id=patient.external_id,
            age_years=age_years,
            sex=patient.sex,
            pregnancy_status=patient.pregnancy_status,
        )
    
    def _convert_observations(self, lab_tests: List[LabTest]) -> List[Observation]:
        """Convert LabTest models to Observation schemas"""
        observations = []
        
        for test in lab_tests:
            reference_range = None
            if test.ref_low is not None or test.ref_high is not None or test.ref_text:
                reference_range = {
                    "low": test.ref_low,
                    "high": test.ref_high,
                    "text": test.ref_text,
                }
            
            observation = Observation(
                observation_id=test.id,
                loinc_code=test.loinc_code,
                display=test.analyte_display,
                analyte_raw=test.analyte_raw,
                value_numeric=test.value_num,
                value_text=test.value_text,
                unit_ucum=test.unit_ucum,
                unit_raw=test.unit_raw,
                reference_range=reference_range,
                flag=test.flag,
                confidence_score=test.confidence_score,
                method_name=test.method_name,
                sample_type=test.sample_type,
                collected_at=test.collected_at,
                resulted_at=test.resulted_at,
            )
            observations.append(observation)
        
        return observations
    
    def _convert_recommendations(self, recommendations_data: List[dict]) -> List[Recommendation]:
        """Convert recommendation data to schemas"""
        recommendations = []
        
        for rec_data in recommendations_data:
            recommendation = Recommendation(
                code=rec_data.get("code", ""),
                text=rec_data.get("text", ""),
                level=rec_data.get("level", "info"),
                evidence=rec_data.get("evidence"),
                disclaimer=rec_data.get("disclaimer", "Esta recomendação é informativa e não substitui avaliação médica."),
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _convert_organization(self, org: Organization) -> dict:
        """Convert Organization model to dict"""
        if not org:
            return None
        
        return {
            "organization_id": org.id,
            "name": org.name,
            "identifier": org.identifier,
            "org_type": org.org_type,
        }