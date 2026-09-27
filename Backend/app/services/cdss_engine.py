from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.cdss import AlertInstance, AlertSeverity, AlertStatus, CDSSRule
from app.models.genomic import BiomarkerGenomicRecord
from app.models.medication import MedicationHistory
from app.models.patient import Patient
from app.services.audit_service import AuditService


class CDSSEngine:
    @staticmethod
    def _normalize_string(val: Optional[str]) -> str:
        return val.strip().lower() if val else ""

    @classmethod
    async def evaluate_patient(
        cls,
        db: AsyncSession,
        patient_id: uuid.UUID,
        evaluator_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate active medications against genomic biomarker records
        using transparent, deterministic pharmacogenomic rules.
        """
        # Fetch patient with active medications and genomic records
        patient_query = (
            select(Patient)
            .where(Patient.id == patient_id)
            .options(
                selectinload(Patient.medications),
                selectinload(Patient.genomic_records),
                selectinload(Patient.alerts).selectinload(AlertInstance.rule),
            )
        )
        patient_res = await db.execute(patient_query)
        patient = patient_res.scalar_one_or_none()

        if not patient:
            raise ValueError(f"Patient with ID {patient_id} not found")

        active_meds = [m for m in patient.medications if m.active]
        genomic_records = patient.genomic_records

        # Load all registered CDSS rules
        rules_query = select(CDSSRule)
        rules_res = await db.execute(rules_query)
        rules = rules_res.scalars().all()

        new_alerts: List[AlertInstance] = []

        # Map existing active alert rule IDs to avoid duplicate unacknowledged alerts
        existing_active_rule_ids = {
            a.rule_id
            for a in patient.alerts
            if a.status == AlertStatus.TRIGGERED
        }

        # Evaluate rules against active medications & genomic markers
        for rule in rules:
            cond = rule.condition_expression
            target_drugs = [cls._normalize_string(d) for d in cond.get("drugs", [])]
            target_gene = cls._normalize_string(cond.get("gene", ""))
            target_phenotypes = [cls._normalize_string(p) for p in cond.get("phenotypes", [])]
            target_alleles = [cls._normalize_string(a) for a in cond.get("alleles", [])]

            # 1. Match medication
            matched_med = None
            for med in active_meds:
                med_name_clean = cls._normalize_string(med.drug_name)
                # Check direct or substring match
                for target_drug in target_drugs:
                    if target_drug in med_name_clean or med_name_clean in target_drug:
                        matched_med = med
                        break
                if matched_med:
                    break

            if not matched_med:
                continue

            # 2. Match genomic record
            matched_genomic = None
            for gr in genomic_records:
                gene_clean = cls._normalize_string(gr.gene_symbol)
                if gene_clean != target_gene:
                    continue

                phenotype_clean = cls._normalize_string(gr.phenotype)
                allele_clean = cls._normalize_string(gr.variant_allele)

                # Check phenotype match
                pheno_match = any(tp in phenotype_clean or phenotype_clean in tp for tp in target_phenotypes) if target_phenotypes else False
                
                # Check allele match
                allele_match = any(ta in allele_clean or allele_clean in ta for ta in target_alleles) if target_alleles else False

                if pheno_match or allele_match:
                    matched_genomic = gr
                    break

            # 3. If both drug & genomic criteria match, trigger alert
            if matched_med and matched_genomic:
                # If an unacknowledged alert for this rule already exists, don't duplicate
                if rule.id in existing_active_rule_ids:
                    continue

                evidence = {
                    "drug_name": matched_med.drug_name,
                    "dosage": matched_med.dosage,
                    "frequency": matched_med.frequency,
                    "gene_symbol": matched_genomic.gene_symbol,
                    "variant_allele": matched_genomic.variant_allele,
                    "phenotype": matched_genomic.phenotype,
                    "matched_at": datetime.now(timezone.utc).isoformat(),
                    "clinical_reference": rule.clinical_reference,
                }

                alert = AlertInstance(
                    patient_id=patient.id,
                    rule_id=rule.id,
                    severity=rule.severity,
                    message=f"Pharmacogenomic Interaction Detected: {matched_med.drug_name} in patient with {matched_genomic.gene_symbol} ({matched_genomic.phenotype}). {rule.description}",
                    evidence_data=evidence,
                    triggered_at=datetime.now(timezone.utc),
                    status=AlertStatus.TRIGGERED,
                )
                db.add(alert)
                new_alerts.append(alert)

        if new_alerts:
            await db.commit()
            for a in new_alerts:
                await db.refresh(a)

        # Audit log the CDSS evaluation event
        await AuditService.log_event(
            db=db,
            actor_id=evaluator_id,
            action="CDSS_EVALUATION",
            resource="patient",
            resource_id=str(patient_id),
            ip_address=ip_address,
            details={
                "patient_mrn": patient.medical_record_number,
                "active_meds_count": len(active_meds),
                "biomarkers_count": len(genomic_records),
                "new_alerts_triggered": len(new_alerts),
            },
        )

        # Reload all alerts for the patient with rule details
        all_alerts_query = (
            select(AlertInstance)
            .where(AlertInstance.patient_id == patient_id)
            .options(selectinload(AlertInstance.rule))
            .order_by(AlertInstance.triggered_at.desc())
        )
        all_alerts_res = await db.execute(all_alerts_query)
        all_alerts = all_alerts_res.scalars().all()

        return {
            "patient_id": patient.id,
            "evaluated_at": datetime.now(timezone.utc),
            "evaluated_medications_count": len(active_meds),
            "evaluated_biomarkers_count": len(genomic_records),
            "alerts_triggered_count": len(new_alerts),
            "alerts": all_alerts,
            "disclaimer": (
                "Strict decision-support guidance only for qualified clinicians. "
                "Does not autonomously diagnose or prescribe. Final clinical judgment rests with the treating clinician."
            ),
        }

    @classmethod
    async def acknowledge_alert(
        cls,
        db: AsyncSession,
        alert_id: uuid.UUID,
        clinician_id: uuid.UUID,
        clinician_note: str,
        override: bool = False,
        ip_address: Optional[str] = None,
    ) -> AlertInstance:
        """
        Record explicit clinician review and acknowledgment of a CDSS alert.
        """
        query = (
            select(AlertInstance)
            .where(AlertInstance.id == alert_id)
            .options(selectinload(AlertInstance.rule), selectinload(AlertInstance.patient))
        )
        res = await db.execute(query)
        alert = res.scalar_one_or_none()

        if not alert:
            raise ValueError(f"Alert with ID {alert_id} not found")

        alert.acknowledged_by_id = clinician_id
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.clinician_note = clinician_note
        alert.status = AlertStatus.OVERRIDDEN if override else AlertStatus.ACKNOWLEDGED

        await db.commit()
        await db.refresh(alert)

        # Audit log the acknowledgment
        await AuditService.log_event(
            db=db,
            actor_id=clinician_id,
            action="ALERT_ACKNOWLEDGED" if not override else "ALERT_OVERRIDDEN",
            resource="alert",
            resource_id=str(alert.id),
            ip_address=ip_address,
            details={
                "patient_id": str(alert.patient_id),
                "rule_id": str(alert.rule_id),
                "severity": alert.severity.value,
                "clinician_note": clinician_note,
                "override": override,
            },
        )

        return alert
