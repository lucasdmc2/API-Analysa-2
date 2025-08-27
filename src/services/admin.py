"""
Administration service for configuration and management
"""

import uuid
from typing import Optional
from sqlalchemy.orm import Session, joinedload
import structlog

from src.models.reference import RangeSet, LoincMapping, Organization
from src.schemas.reference import (
    CreateRangesetRequest, RangesetResponse, RangesetList,
    CreateLoincMappingRequest, LoincMappingResponse, LoincMappingList
)
from src.schemas.common import PaginationResponse
from src.core.exceptions import DuplicateResourceError
from src.db.database import set_tenant_context

logger = structlog.get_logger()


class AdminService:
    """Service for administration and configuration"""
    
    def __init__(self, db: Session, tenant_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id
        set_tenant_context(db, str(tenant_id))
    
    async def create_rangeset(self, request: CreateRangesetRequest) -> RangesetResponse:
        """Create new reference range configuration"""
        
        # Check for duplicate
        existing = self.db.query(RangeSet).filter(
            RangeSet.tenant_id == self.tenant_id,
            RangeSet.analyte_key == request.analyte_key,
            RangeSet.lab_org_id == request.lab_org_id,
            RangeSet.sex == request.sex,
            RangeSet.pregnancy_status == request.pregnancy_status,
            RangeSet.age_min_years == request.age_min_years,
            RangeSet.age_max_years == request.age_max_years,
        ).first()
        
        if existing:
            raise DuplicateResourceError(
                "RangeSet",
                f"Range already exists for analyte '{request.analyte_key}' with same criteria"
            )
        
        # Create new rangeset
        rangeset = RangeSet(
            tenant_id=self.tenant_id,
            analyte_key=request.analyte_key,
            loinc_code=request.loinc_code,
            lab_org_id=request.lab_org_id,
            age_min_years=request.age_min_years,
            age_max_years=request.age_max_years,
            sex=request.sex,
            pregnancy_status=request.pregnancy_status,
            method_name=request.method_name,
            ref_low=request.ref_low,
            ref_high=request.ref_high,
            ref_text=request.ref_text,
            unit_ucum=request.unit_ucum,
            source=request.source,
            confidence_level=request.confidence_level,
        )
        
        self.db.add(rangeset)
        self.db.commit()
        self.db.refresh(rangeset)
        
        logger.info(
            "Reference range created",
            rangeset_id=rangeset.id,
            analyte_key=request.analyte_key,
            tenant_id=self.tenant_id
        )
        
        return await self._convert_rangeset(rangeset)
    
    async def list_rangesets(
        self,
        analyte_key: Optional[str] = None,
        loinc_code: Optional[str] = None,
        lab_org_id: Optional[uuid.UUID] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> RangesetList:
        """List reference ranges with filtering"""
        
        query = self.db.query(RangeSet).options(
            joinedload(RangeSet.lab_organization)
        ).filter(
            RangeSet.tenant_id == self.tenant_id
        )
        
        # Apply filters
        if analyte_key:
            query = query.filter(RangeSet.analyte_key == analyte_key)
        
        if loinc_code:
            query = query.filter(RangeSet.loinc_code == loinc_code)
        
        if lab_org_id:
            query = query.filter(RangeSet.lab_org_id == lab_org_id)
        
        # Apply cursor pagination
        if cursor:
            try:
                cursor_id = uuid.UUID(cursor)
                query = query.filter(RangeSet.id > cursor_id)
            except ValueError:
                pass
        
        query = query.order_by(RangeSet.analyte_key, RangeSet.id)
        
        # Get limit + 1 to check for more results
        rangesets = query.limit(limit + 1).all()
        
        has_next = len(rangesets) > limit
        if has_next:
            rangesets = rangesets[:-1]
        
        next_cursor = str(rangesets[-1].id) if has_next and rangesets else None
        
        # Convert to response
        data = []
        for rangeset in rangesets:
            response = await self._convert_rangeset(rangeset)
            data.append(response)
        
        return RangesetList(
            data=data,
            pagination=PaginationResponse(
                next_cursor=next_cursor,
                has_next=has_next,
                limit=limit,
            )
        )
    
    async def create_loinc_mapping(self, request: CreateLoincMappingRequest) -> LoincMappingResponse:
        """Create or update LOINC mapping"""
        
        # Check for existing mapping
        existing = self.db.query(LoincMapping).filter(
            LoincMapping.tenant_id == self.tenant_id,
            LoincMapping.lab_code == request.lab_code,
            LoincMapping.loinc_code == request.loinc_code,
        ).first()
        
        if existing:
            # Update existing mapping
            existing.lab_name = request.lab_name
            existing.loinc_display = request.loinc_display
            existing.confidence = request.confidence
            existing.method_constraint = request.method_constraint
            existing.unit_constraint = request.unit_constraint
            
            self.db.commit()
            mapping = existing
        else:
            # Create new mapping
            mapping = LoincMapping(
                tenant_id=self.tenant_id,
                lab_code=request.lab_code,
                lab_name=request.lab_name,
                loinc_code=request.loinc_code,
                loinc_display=request.loinc_display,
                confidence=request.confidence,
                method_constraint=request.method_constraint,
                unit_constraint=request.unit_constraint,
            )
            
            self.db.add(mapping)
            self.db.commit()
            self.db.refresh(mapping)
        
        logger.info(
            "LOINC mapping created/updated",
            mapping_id=mapping.id,
            lab_code=request.lab_code,
            loinc_code=request.loinc_code,
            tenant_id=self.tenant_id
        )
        
        return LoincMappingResponse(
            mapping_id=mapping.id,
            lab_code=mapping.lab_code,
            lab_name=mapping.lab_name,
            loinc_code=mapping.loinc_code,
            loinc_display=mapping.loinc_display,
            confidence=mapping.confidence,
            method_constraint=mapping.method_constraint,
            unit_constraint=mapping.unit_constraint,
            created_at=mapping.created_at,
            validated_at=mapping.validated_at,
        )
    
    async def list_loinc_mappings(
        self,
        lab_code: Optional[str] = None,
        loinc_code: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> LoincMappingList:
        """List LOINC mappings"""
        
        query = self.db.query(LoincMapping).filter(
            LoincMapping.tenant_id == self.tenant_id
        )
        
        # Apply filters
        if lab_code:
            query = query.filter(LoincMapping.lab_code.ilike(f"%{lab_code}%"))
        
        if loinc_code:
            query = query.filter(LoincMapping.loinc_code == loinc_code)
        
        # Apply cursor pagination
        if cursor:
            try:
                cursor_id = uuid.UUID(cursor)
                query = query.filter(LoincMapping.id > cursor_id)
            except ValueError:
                pass
        
        query = query.order_by(LoincMapping.lab_code, LoincMapping.id)
        
        # Get limit + 1 to check for more results
        mappings = query.limit(limit + 1).all()
        
        has_next = len(mappings) > limit
        if has_next:
            mappings = mappings[:-1]
        
        next_cursor = str(mappings[-1].id) if has_next and mappings else None
        
        # Convert to response
        data = []
        for mapping in mappings:
            response = LoincMappingResponse(
                mapping_id=mapping.id,
                lab_code=mapping.lab_code,
                lab_name=mapping.lab_name,
                loinc_code=mapping.loinc_code,
                loinc_display=mapping.loinc_display,
                confidence=mapping.confidence,
                method_constraint=mapping.method_constraint,
                unit_constraint=mapping.unit_constraint,
                created_at=mapping.created_at,
                validated_at=mapping.validated_at,
            )
            data.append(response)
        
        return LoincMappingList(
            data=data,
            pagination=PaginationResponse(
                next_cursor=next_cursor,
                has_next=has_next,
                limit=limit,
            )
        )
    
    async def _convert_rangeset(self, rangeset: RangeSet) -> RangesetResponse:
        """Convert RangeSet model to response schema"""
        
        applies_to = {
            "age_min_years": rangeset.age_min_years,
            "age_max_years": rangeset.age_max_years,
            "sex": rangeset.sex,
            "pregnancy_status": rangeset.pregnancy_status,
            "method_name": rangeset.method_name,
        }
        
        lab_organization = None
        if rangeset.lab_organization:
            lab_organization = {
                "organization_id": rangeset.lab_organization.id,
                "name": rangeset.lab_organization.name,
                "identifier": rangeset.lab_organization.identifier,
                "org_type": rangeset.lab_organization.org_type,
            }
        
        return RangesetResponse(
            rangeset_id=rangeset.id,
            analyte_key=rangeset.analyte_key,
            loinc_code=rangeset.loinc_code,
            lab_organization=lab_organization,
            applies_to=applies_to,
            ref_low=rangeset.ref_low,
            ref_high=rangeset.ref_high,
            ref_text=rangeset.ref_text,
            unit_ucum=rangeset.unit_ucum,
            source=rangeset.source,
            confidence_level=rangeset.confidence_level,
            effective_period={
                "start": rangeset.effective_start,
                "end": rangeset.effective_end,
            } if rangeset.effective_start else None,
            created_at=rangeset.created_at,
        )