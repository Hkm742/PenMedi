from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.cdss import AlertInstance, AlertStatus
from app.models.diagnosis import ClinicalDiagnosis
from app.models.genomic import BiomarkerGenomicRecord
from app.models.medication import MedicationHistory
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate
from app.schemas.clinical import ClinicalDiagnosisCreate, MedicationHistoryCreate, MedicationHistoryUpdate
from app.schemas.genomic import BiomarkerGenomicRecordCreate
from app.services.audit_service import AuditService
from app.services.cdss_engine import CDSSEngine


class PatientService:
    @classmethod
    async def get_patients(
        cls,
        db: AsyncSession,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List patients with active alerts count."""
        query = select(Patient)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Patient.medical_record_number.ilike(search_term),
                    Patient.first_name.ilike(search_term),
                    Patient.last_name.ilike(search_term),
                )
            )

        # Count total
        count_query = select(func.count(Patient.id))
        if search:
            search_term = f"%{search.strip()}%"
            count_query = count_query.where(
                or_(
                    Patient.medical_record_number.ilike(search_term),
                    Patient.first_name.ilike(search_term),
                    Patient.last_name.ilike(search_term),
                )
            )

        total_res = await db.execute(count_query)
        total = total_res.scalar_one()

        query = (
            query.options(selectinload(Patient.alerts))
            .order_by(Patient.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        results = await db.execute(query)
        patients = results.scalars().all()

        output = []
        for p in patients:
            active_alerts = sum(1 for a in p.alerts if a.status == AlertStatus.TRIGGERED)
            output.append({
                "id": p.id,
                "medical_record_number": p.medical_record_number,
                "first_name": p.first_name,
                "last_name": p.last_name,
                "dob": p.dob,
                "sex": p.sex,
                "contact_info": p.contact_info,
                "created_at": p.created_at,
                "active_alerts_count": active_alerts,
            })

        return output, total

    @classmethod
    async def get_patient_detail(
        cls, db: AsyncSession, patient_id: uuid.UUID
    ) -> Optional[Patient]:
        """Fetch full patient chart including medications, diagnoses, genomics, and alerts."""
        query = (
            select(Patient)
            .where(Patient.id == patient_id)
            .options(
                selectinload(Patient.diagnoses),
                selectinload(Patient.medications),
                selectinload(Patient.genomic_records),
                selectinload(Patient.alerts).selectinload(AlertInstance.rule),
            )
        )
        res = await db.execute(query)
        return res.scalar_one_or_none()

    @classmethod
    async def create_patient(
        cls,
        db: AsyncSession,
        data: PatientCreate,
        creator_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> Patient:
        """Register a new patient record."""
        # Check if MRN already exists
        check = await db.execute(
            select(Patient).where(Patient.medical_record_number == data.medical_record_number)
        )
        if check.scalar_one_or_none():
            raise ValueError(f"Patient with MRN '{data.medical_record_number}' already exists.")

        patient = Patient(
            medical_record_number=data.medical_record_number,
            first_name=data.first_name,
            last_name=data.last_name,
            dob=data.dob,
            sex=data.sex,
            contact_info=data.contact_info or {},
            created_at=datetime.now(timezone.utc),
        )
        db.add(patient)
        await db.commit()
        await db.refresh(patient)

        await AuditService.log_event(
            db=db,
            actor_id=creator_id,
            action="PATIENT_CREATE",
            resource="patient",
            resource_id=str(patient.id),
            ip_address=ip_address,
            details={"mrn": patient.medical_record_number, "full_name": f"{patient.first_name} {patient.last_name}"},
        )
        return patient

    @classmethod
    async def add_diagnosis(
        cls,
        db: AsyncSession,
        patient_id: uuid.UUID,
        data: ClinicalDiagnosisCreate,
        clinician_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> ClinicalDiagnosis:
        diag = ClinicalDiagnosis(
            patient_id=patient_id,
            icd10_code=data.icd10_code,
            description=data.description,
            date_diagnosed=data.date_diagnosed,
            clinician_id=clinician_id,
        )
        db.add(diag)
        await db.commit()
        await db.refresh(diag)

        await AuditService.log_event(
            db=db,
            actor_id=clinician_id,
            action="DIAGNOSIS_ADD",
            resource="diagnosis",
            resource_id=str(diag.id),
            ip_address=ip_address,
            details={"patient_id": str(patient_id), "icd10_code": diag.icd10_code},
        )
        return diag

    @classmethod
    async def add_medication(
        cls,
        db: AsyncSession,
        patient_id: uuid.UUID,
        data: MedicationHistoryCreate,
        actor_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> MedicationHistory:
        med = MedicationHistory(
            patient_id=patient_id,
            drug_name=data.drug_name,
            dosage=data.dosage,
            frequency=data.frequency,
            start_date=data.start_date,
            end_date=data.end_date,
            active=data.active,
        )
        db.add(med)
        await db.commit()
        await db.refresh(med)

        await AuditService.log_event(
            db=db,
            actor_id=actor_id,
            action="MEDICATION_ADD",
            resource="medication",
            resource_id=str(med.id),
            ip_address=ip_address,
            details={"patient_id": str(patient_id), "drug_name": med.drug_name},
        )

        # Trigger automatic CDSS pharmacogenomic re-evaluation on new medication
        try:
            await CDSSEngine.evaluate_patient(
                db=db,
                patient_id=patient_id,
                evaluator_id=actor_id,
                ip_address=ip_address,
            )
        except Exception:
            pass

        return med

    @classmethod
    async def add_genomic_record(
        cls,
        db: AsyncSession,
        patient_id: uuid.UUID,
        data: BiomarkerGenomicRecordCreate,
        lab_officer_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> BiomarkerGenomicRecord:
        record = BiomarkerGenomicRecord(
            patient_id=patient_id,
            gene_symbol=data.gene_symbol.strip().upper(),
            variant_allele=data.variant_allele.strip(),
            phenotype=data.phenotype.strip(),
            test_date=data.test_date,
            verified_by_id=lab_officer_id,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)

        await AuditService.log_event(
            db=db,
            actor_id=lab_officer_id,
            action="GENOMICS_ADD",
            resource="genomic",
            resource_id=str(record.id),
            ip_address=ip_address,
            details={
                "patient_id": str(patient_id),
                "gene_symbol": record.gene_symbol,
                "variant_allele": record.variant_allele,
                "phenotype": record.phenotype,
            },
        )

        # Trigger automatic CDSS re-evaluation on new genomic record
        try:
            await CDSSEngine.evaluate_patient(
                db=db,
                patient_id=patient_id,
                evaluator_id=lab_officer_id,
                ip_address=ip_address,
            )
        except Exception:
            pass

        return record
