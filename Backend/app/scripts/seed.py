import asyncio
from datetime import date, datetime, timedelta, timezone
import uuid
from sqlalchemy import select
from app.core.db import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.cdss import AlertSeverity, CDSSRule
from app.models.diagnosis import ClinicalDiagnosis
from app.models.genomic import BiomarkerGenomicRecord
from app.models.medication import MedicationHistory
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.services.audit_service import AuditService
from app.services.cdss_engine import CDSSEngine


async def seed_data():
    async with AsyncSessionLocal() as db:
        print("--- Starting PM-CDSS Database Seeding ---")

        # 1. Seed Institutional Users
        users_data = [
            {
                "email": "admin@lmth.gov.zm",
                "password": "AdminPass123!",
                "full_name": "Dr. Mutale Mwila (Chief Medical Info Officer)",
                "role": UserRole.Administrator,
            },
            {
                "email": "clinician@lmth.gov.zm",
                "password": "ClinicianPass123!",
                "full_name": "Dr. Chileshe Bwalya (Consultant Cardiologist)",
                "role": UserRole.Clinician,
            },
            {
                "email": "lab@lmth.gov.zm",
                "password": "LabPass123!",
                "full_name": "Kondwani Phiri (Senior Genomic Technologist)",
                "role": UserRole.Lab_Officer,
            },
            {
                "email": "auditor@lmth.gov.zm",
                "password": "AuditorPass123!",
                "full_name": "Besa Musonda (Clinical Quality & Compliance Officer)",
                "role": UserRole.Auditor,
            },
        ]

        users = {}
        for u in users_data:
            stmt = select(User).where(User.email == u["email"])
            existing = (await db.execute(stmt)).scalar_one_or_none()
            if not existing:
                new_user = User(
                    email=u["email"],
                    hashed_password=get_password_hash(u["password"]),
                    full_name=u["full_name"],
                    role=u["role"],
                    is_active=True,
                )
                db.add(new_user)
                await db.commit()
                await db.refresh(new_user)
                users[u["role"]] = new_user
                print(f"Created user: {u['email']} [{u['role'].value}]")
            else:
                users[u["role"]] = existing
                print(f"Existing user: {u['email']} [{u['role'].value}]")

        admin_user = users[UserRole.Administrator]
        clinician_user = users[UserRole.Clinician]
        lab_user = users[UserRole.Lab_Officer]

        # 2. Seed Institutional Pharmacogenomic CDSS Rules
        rules_data = [
            {
                "rule_code": "PGX-CYP2C19-CLOPIDOGREL",
                "description": "Substantially decreased active metabolite formation resulting in diminished antiplatelet response and increased rate of major adverse cardiovascular events (MACE) and stent thrombosis.",
                "condition_expression": {
                    "drugs": ["Clopidogrel", "Plavix"],
                    "gene": "CYP2C19",
                    "phenotypes": ["Poor Metabolizer", "Intermediate Metabolizer"],
                    "alleles": ["*2/*2", "*2/*3", "*3/*3", "*1/*2", "*1/*3"],
                },
                "severity": AlertSeverity.CRITICAL,
                "recommendation": "Avoid clopidogrel. Consider alternative P2Y12 platelet inhibitor: Prasugrel (unless history of stroke/TIA) or Ticagrelor at standard dosing.",
                "clinical_reference": "CPIC Guideline for CYP2C19 and Clopidogrel Therapy (2022 Update); LMTH Clinical Protocol 4.2",
            },
            {
                "rule_code": "PGX-HLAB-ABACAVIR",
                "description": "Severe, life-threatening, multi-organ immunologic hypersensitivity reaction (HSR). Characterized by fever, rash, GI and respiratory symptoms.",
                "condition_expression": {
                    "drugs": ["Abacavir", "Ziagen", "Triumeq", "Kivexa"],
                    "gene": "HLA-B",
                    "phenotypes": ["Hypersensitivity Risk", "Positive"],
                    "alleles": ["*57:01", "*57:01 (Positive)"],
                },
                "severity": AlertSeverity.CRITICAL,
                "recommendation": "Abacavir is strictly contraindicated. Re-challenge is lethal. Select an alternative non-abacavir antiretroviral regimen (e.g. Tenofovir disoproxil fumarate or Tenofovir alafenamide).",
                "clinical_reference": "CPIC Guideline for HLA-B Genotype and Abacavir Dosing; WHO Antiretroviral Guidelines (LMTH Zambia)",
            },
            {
                "rule_code": "PGX-HLAB-ALLOPURINOL",
                "description": "High risk of severe cutaneous adverse reactions (SCAR), including Stevens-Johnson syndrome (SJS) and toxic epidermal necrolysis (TEN).",
                "condition_expression": {
                    "drugs": ["Allopurinol", "Zyloprim"],
                    "gene": "HLA-B",
                    "phenotypes": ["SCAR / SJS Risk", "Severe Cutaneous Risk", "Positive"],
                    "alleles": ["*58:01", "*58:01 (Positive)"],
                },
                "severity": AlertSeverity.CRITICAL,
                "recommendation": "Allopurinol is strictly contraindicated. Select an alternative xanthine oxidase inhibitor such as Febuxostat or Probenecid for urate lowering.",
                "clinical_reference": "CPIC Guideline for HLA-B*58:01 and Allopurinol (2015); LMTH Rheumatology Guidelines",
            },
            {
                "rule_code": "PGX-CYP2D6-CODEINE",
                "description": "In Ultra-Rapid Metabolizers, rapid conversion to morphine causes severe opioid toxicity and fatal respiratory depression. In Poor Metabolizers, lack of active metabolite causes therapeutic failure.",
                "condition_expression": {
                    "drugs": ["Codeine", "Codeine phosphate"],
                    "gene": "CYP2D6",
                    "phenotypes": ["Ultra-Rapid Metabolizer", "Poor Metabolizer"],
                    "alleles": ["*1xN/*1", "*2xN/*2", "*4/*4", "*5/*5"],
                },
                "severity": AlertSeverity.WARNING,
                "recommendation": "Avoid codeine. For Ultra-Rapid and Poor metabolizers, select non-opioid analgesic (e.g. Paracetamol, NSAIDs) or direct-acting opioids not metabolized by CYP2D6 (e.g. Morphine, Fentanyl) with cautious monitoring.",
                "clinical_reference": "CPIC Guideline for CYP2D6 and Codeine Therapy; LMTH Pain Management Protocol",
            },
            {
                "rule_code": "PGX-TPMT-AZATHIOPRINE",
                "description": "Accumulation of cytotoxic thioguanine nucleotides causing profound myelosuppression, severe pancytopenia, and fatal infection risk.",
                "condition_expression": {
                    "drugs": ["Azathioprine", "Imuran", "6-Mercaptopurine"],
                    "gene": "TPMT",
                    "phenotypes": ["Poor Metabolizer", "Intermediate Metabolizer"],
                    "alleles": ["*3A/*3A", "*3C/*3C", "*2/*3A"],
                },
                "severity": AlertSeverity.CRITICAL,
                "recommendation": "For Poor Metabolizers: consider alternative non-thiopurine immunosuppressant, or reduce dose by 90% (10% of standard dose) and monitor CBC thrice weekly.",
                "clinical_reference": "CPIC Guideline for Thiopurine Methyltransferase (TPMT) and Thiopurines; LMTH Hematology",
            },
            {
                "rule_code": "PGX-VKORC1-WARFARIN",
                "description": "Significantly decreased VKORC1 expression leading to extreme warfarin sensitivity and elevated INR, precipitating life-threatening hemorrhagic risk.",
                "condition_expression": {
                    "drugs": ["Warfarin", "Coumadin"],
                    "gene": "VKORC1",
                    "phenotypes": ["High Sensitivity", "Intermediate Sensitivity"],
                    "alleles": ["-1639G>A (AA)", "-1639G>A (AG)"],
                },
                "severity": AlertSeverity.WARNING,
                "recommendation": "Reduce initial warfarin loading dose by 30-50%. Perform frequent INR monitoring (e.g. days 3, 5, 7) or consider direct oral anticoagulants (DOACs: Apixaban, Rivaroxaban) if not contraindicated.",
                "clinical_reference": "CPIC Guideline for Pharmacogenetics-Guided Warfarin Dosing (2017); LMTH Cardiology",
            },
        ]

        for r in rules_data:
            stmt = select(CDSSRule).where(CDSSRule.rule_code == r["rule_code"])
            existing_rule = (await db.execute(stmt)).scalar_one_or_none()
            if not existing_rule:
                new_rule = CDSSRule(
                    rule_code=r["rule_code"],
                    description=r["description"],
                    condition_expression=r["condition_expression"],
                    severity=r["severity"],
                    recommendation=r["recommendation"],
                    clinical_reference=r["clinical_reference"],
                )
                db.add(new_rule)
                print(f"Created CDSS Rule: {r['rule_code']}")
        await db.commit()

        # 3. Seed Realistic Synthetic Patient Profiles
        patients_profiles = [
            {
                "mrn": "LMTH-CARD-2024-001",
                "first_name": "Mwape",
                "last_name": "Sakala",
                "dob": date(1968, 5, 14),
                "sex": "M",
                "contact": {"phone": "+260-977-123456", "address": "Plot 42, Woodlands, Lusaka", "emergency": "Chanda Sakala (Wife)"},
                "diagnoses": [
                    {"code": "I25.10", "desc": "Atherosclerotic heart disease with unstable angina"},
                    {"code": "I10", "desc": "Essential (primary) hypertension"},
                ],
                "medications": [
                    {"drug": "Clopidogrel", "dosage": "75 mg", "freq": "Once daily", "start": date.today() - timedelta(days=14)},
                    {"drug": "Atorvastatin", "dosage": "40 mg", "freq": "Once daily at bedtime", "start": date.today() - timedelta(days=14)},
                    {"drug": "Lisinopril", "dosage": "10 mg", "freq": "Once daily in morning", "start": date.today() - timedelta(days=90)},
                ],
                "genomics": [
                    {"gene": "CYP2C19", "variant": "*2/*2", "phenotype": "Poor Metabolizer", "date": date.today() - timedelta(days=3)},
                ],
            },
            {
                "mrn": "LMTH-ID-2024-082",
                "first_name": "Natasha",
                "last_name": "Tembo",
                "dob": date(1985, 11, 20),
                "sex": "F",
                "contact": {"phone": "+260-966-234567", "address": "House 12, Kabwata, Lusaka", "emergency": "Mulenga Tembo (Brother)"},
                "diagnoses": [
                    {"code": "B20", "desc": "Human immunodeficiency virus [HIV] disease"},
                    {"code": "A15.0", "desc": "Tuberculosis of lung, confirmed by sputum microscopy"},
                ],
                "medications": [
                    {"drug": "Abacavir", "dosage": "600 mg", "freq": "Once daily", "start": date.today() - timedelta(days=5)},
                    {"drug": "Lamivudine", "dosage": "300 mg", "freq": "Once daily", "start": date.today() - timedelta(days=5)},
                    {"drug": "Dolutegravir", "dosage": "50 mg", "freq": "Once daily", "start": date.today() - timedelta(days=5)},
                ],
                "genomics": [
                    {"gene": "HLA-B", "variant": "*57:01 (Positive)", "phenotype": "Hypersensitivity Risk", "date": date.today() - timedelta(days=2)},
                ],
            },
            {
                "mrn": "LMTH-RHEUM-2024-119",
                "first_name": "Kabwe",
                "last_name": "Chilufya",
                "dob": date(1974, 3, 8),
                "sex": "M",
                "contact": {"phone": "+260-955-345678", "address": "Stand 108, Chelstone, Lusaka", "emergency": "Mary Chilufya (Spouse)"},
                "diagnoses": [
                    {"code": "M10.0", "desc": "Idiopathic gouty arthritis with tophi"},
                    {"code": "N18.3", "desc": "Chronic kidney disease, Stage 3 (moderate)"},
                ],
                "medications": [
                    {"drug": "Allopurinol", "dosage": "300 mg", "freq": "Once daily after meals", "start": date.today() - timedelta(days=7)},
                    {"drug": "Colchicine", "dosage": "0.5 mg", "freq": "Twice daily", "start": date.today() - timedelta(days=7)},
                ],
                "genomics": [
                    {"gene": "HLA-B", "variant": "*58:01 (Positive)", "phenotype": "SCAR / SJS Risk", "date": date.today() - timedelta(days=4)},
                ],
            },
            {
                "mrn": "LMTH-ONC-2024-205",
                "first_name": "Chileshe",
                "last_name": "Mulenga",
                "dob": date(1991, 8, 12),
                "sex": "F",
                "contact": {"phone": "+260-971-456789", "address": "Chilenje South, Lusaka", "emergency": "Sampa Mulenga (Mother)"},
                "diagnoses": [
                    {"code": "C50.9", "desc": "Infiltrating duct carcinoma of breast"},
                    {"code": "G89.18", "desc": "Acute post-mastectomy pain"},
                ],
                "medications": [
                    {"drug": "Codeine phosphate", "dosage": "30 mg", "freq": "Every 6 hours PRN for severe pain", "start": date.today() - timedelta(days=2)},
                    {"drug": "Tamoxifen", "dosage": "20 mg", "freq": "Once daily", "start": date.today() - timedelta(days=60)},
                ],
                "genomics": [
                    {"gene": "CYP2D6", "variant": "*1xN/*1", "phenotype": "Ultra-Rapid Metabolizer", "date": date.today() - timedelta(days=10)},
                ],
            },
            {
                "mrn": "LMTH-GI-2024-340",
                "first_name": "Joseph",
                "last_name": "Banda",
                "dob": date(1980, 2, 28),
                "sex": "M",
                "contact": {"phone": "+260-978-567890", "address": "Plot 88, Rhodes Park, Lusaka", "emergency": "Tadalisika Banda (Sister)"},
                "diagnoses": [
                    {"code": "K50.0", "desc": "Crohn's disease of small intestine"},
                ],
                "medications": [
                    {"drug": "Azathioprine", "dosage": "150 mg", "freq": "Once daily", "start": date.today() - timedelta(days=6)},
                    {"drug": "Mesalamine", "dosage": "1000 mg", "freq": "Three times daily", "start": date.today() - timedelta(days=90)},
                ],
                "genomics": [
                    {"gene": "TPMT", "variant": "*3A/*3A", "phenotype": "Poor Metabolizer", "date": date.today() - timedelta(days=5)},
                ],
            },
            {
                "mrn": "LMTH-CARD-2024-412",
                "first_name": "Grace",
                "last_name": "Njobvu",
                "dob": date(1960, 9, 5),
                "sex": "F",
                "contact": {"phone": "+260-967-678901", "address": "Avondale, Lusaka", "emergency": "Dalitso Njobvu (Son)"},
                "diagnoses": [
                    {"code": "I48.0", "desc": "Paroxysmal atrial fibrillation"},
                    {"code": "I10", "desc": "Essential (primary) hypertension"},
                ],
                "medications": [
                    {"drug": "Warfarin", "dosage": "5 mg", "freq": "Once daily in evening", "start": date.today() - timedelta(days=4)},
                    {"drug": "Metoprolol succinate", "dosage": "50 mg", "freq": "Once daily", "start": date.today() - timedelta(days=120)},
                ],
                "genomics": [
                    {"gene": "VKORC1", "variant": "-1639G>A (AA)", "phenotype": "High Sensitivity", "date": date.today() - timedelta(days=3)},
                ],
            },
        ]

        patient_objs = []
        for p in patients_profiles:
            stmt = select(Patient).where(Patient.medical_record_number == p["mrn"])
            existing_p = (await db.execute(stmt)).scalar_one_or_none()
            if not existing_p:
                patient = Patient(
                    medical_record_number=p["mrn"],
                    first_name=p["first_name"],
                    last_name=p["last_name"],
                    dob=p["dob"],
                    sex=p["sex"],
                    contact_info=p["contact"],
                    created_at=datetime.now(timezone.utc) - timedelta(days=15),
                )
                db.add(patient)
                await db.commit()
                await db.refresh(patient)
                print(f"Created Patient: {patient.medical_record_number} - {patient.first_name} {patient.last_name}")

                # Diagnoses
                for d in p["diagnoses"]:
                    diag = ClinicalDiagnosis(
                        patient_id=patient.id,
                        icd10_code=d["code"],
                        description=d["desc"],
                        date_diagnosed=date.today() - timedelta(days=20),
                        clinician_id=clinician_user.id,
                    )
                    db.add(diag)

                # Medications
                for m in p["medications"]:
                    med = MedicationHistory(
                        patient_id=patient.id,
                        drug_name=m["drug"],
                        dosage=m["dosage"],
                        frequency=m["freq"],
                        start_date=m["start"],
                        active=True,
                    )
                    db.add(med)

                # Genomics
                for g in p["genomics"]:
                    gen = BiomarkerGenomicRecord(
                        patient_id=patient.id,
                        gene_symbol=g["gene"],
                        variant_allele=g["variant"],
                        phenotype=g["phenotype"],
                        test_date=g["date"],
                        verified_by_id=lab_user.id,
                    )
                    db.add(gen)

                await db.commit()
                patient_objs.append(patient)
            else:
                patient_objs.append(existing_p)

        # 4. Run CDSS Evaluation on each seeded patient to populate transparent alerts!
        print("\n--- Running CDSS Deterministic Evaluation on Seed Patients ---")
        for p in patient_objs:
            eval_result = await CDSSEngine.evaluate_patient(
                db=db,
                patient_id=p.id,
                evaluator_id=clinician_user.id,
                ip_address="127.0.0.1",
            )
            print(f"Evaluated {p.medical_record_number}: {eval_result['alerts_triggered_count']} alerts triggered.")

        # 5. Add initial audit log entries
        await AuditService.log_event(
            db=db,
            actor_id=admin_user.id,
            action="SYSTEM_INIT_SEED",
            resource="system",
            resource_id="LMTH-PMCDSS-V1",
            ip_address="127.0.0.1",
            details={"institution": "Levy Mwanawasa Teaching Hospital", "version": "1.0.0"},
        )

        print("\n=== PM-CDSS Seeding Successfully Completed! ===")


if __name__ == "__main__":
    asyncio.run(seed_data())
