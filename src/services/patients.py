"""
Patients service for patient data and observations
"""

import uuid
from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import structlog

from src.models.clinical import Patient, LabTest
from src.schemas.clinical import ObservationList, Observation
from src.schemas.common import PaginationResponse
from src.core.exceptions import PatientNotFoundError
from src.db.database import set_tenant_context

logger = structlog.get_logger()


class PatientsService:
    """Service for patient data and observations"""
    
    def __init__(self, db: Session, tenant_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id
        set_tenant_context(db, str(tenant_id))
    
    async def get_patient_observations(
        self,
        patient_id: uuid.UUID,
        loinc_code: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        flag: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> ObservationList:
        """Get patient's lab observations with filtering and pagination"""
        
        # Verify patient exists and belongs to tenant
        patient = self.db.query(Patient).filter(
            Patient.id == patient_id
        ).first()
        
        if not patient:
            raise PatientNotFoundError(str(patient_id))
        
        # Build query
        query = self.db.query(LabTest).filter(
            LabTest.patient_id == patient_id
        )
        
        # Apply filters
        if loinc_code:
            query = query.filter(LabTest.loinc_code == loinc_code)
        
        if date_from:
            query = query.filter(LabTest.collected_at >= date_from)
        
        if date_to:
            query = query.filter(LabTest.collected_at <= date_to)
        
        if flag:
            query = query.filter(LabTest.flag == flag)
        
        # Apply cursor pagination
        if cursor:
            # Simple cursor implementation using ID
            # In production, use proper cursor encoding
            try:
                cursor_id = uuid.UUID(cursor)
                query = query.filter(LabTest.id > cursor_id)
            except ValueError:
                pass  # Invalid cursor, ignore
        
        # Order by collected_at descending, then by ID for consistency
        query = query.order_by(LabTest.collected_at.desc(), LabTest.id.asc())
        
        # Get limit + 1 to check if there are more results
        lab_tests = query.limit(limit + 1).all()
        
        # Check if there are more results
        has_next = len(lab_tests) > limit
        if has_next:
            lab_tests = lab_tests[:-1]  # Remove extra item
        
        # Generate next cursor
        next_cursor = None
        if has_next and lab_tests:
            next_cursor = str(lab_tests[-1].id)
        
        # Convert to observations
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
        
        return ObservationList(
            data=observations,
            pagination=PaginationResponse(
                next_cursor=next_cursor,
                has_next=has_next,
                limit=limit,
            )
        )