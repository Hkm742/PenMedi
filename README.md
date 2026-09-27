# Personalized Medicine Clinical Decision Support System (PM-CDSS)

> **Institution**: Levy Mwanawasa Teaching Hospital (LMTH), Zambia  
> **Project**: Cavendish University Zambia — Sindayigaya Saidi Joslin  
> **Domain**: Personalized Medicine & Pharmacogenomic Clinical Decision Support  
> **Core Clinical Directive**: PM-CDSS is strictly a **decision-support tool** to assist qualified clinicians; it **never** autonomously diagnoses or prescribes.

---

## 1. System Architecture

```text
pm-cdss/
├── docker-compose.yml           # Multi-service container orchestration (Postgres, Backend, Frontend)
├── .env.example                 # Documented environment configuration
├── .env                         # Local runtime credentials
├── Backend/
│   ├── Dockerfile               # Multi-stage Astral `uv` slim container
│   ├── pyproject.toml           # Backend dependencies (FastAPI, SQLAlchemy 2.0, Alembic, etc.)
│   ├── alembic/                 # Async Alembic migrations
│   └── app/
│       ├── api/v1/              # Domain REST API routes (Auth, Patients, Clinical, Genomics, CDSS, Audit)
│       ├── core/                # Pydantic Settings, async SQLAlchemy engine, JWT & Passlib security
│       ├── models/              # Relational models (User, Patient, Diagnosis, Medication, Genomic, CDSS, Audit)
│       ├── schemas/             # Pydantic v2 validation schemas
│       ├── services/            # Deterministic CDSS engine, immutable Audit service, Patient workflows
│       └── scripts/seed.py      # Realistic synthetic clinical profiles & CPIC guideline rules
└── Frontend/
    ├── Dockerfile               # Multi-stage Bun builder + Nginx static server
    ├── package.json             # Vue 3, PrimeVue 4, Pinia, Vue Router, Lucide, Axios
    ├── vite.config.ts           # Vite bundler with API reverse proxy
    └── src/
        ├── assets/main.css      # "Less is More" Flat UI Clinical Design System
        ├── components/          # AppNavbar, Clinical components
        ├── views/               # Login, Dashboard, PatientDetail, LabIngest, RuleEngine, Audit, Users
        ├── stores/              # Pinia stores (Auth with RBAC, Clinical & CDSS workflows)
        └── services/api.ts      # Axios instance with JWT bearer injection and 401 refresh flow
```

---

## 2. Role-Based Access Control (RBAC) & Preconfigured Accounts

The system enforces strict RBAC with least-privilege principles at both the FastAPI dependency level (`require_role(...)`) and Vue Router navigation guards.

| Role | Name & Designation | Hospital Email | Password | Access Scope |
| :--- | :--- | :--- | :--- | :--- |
| **`Clinician`** | Dr. Chileshe Bwalya *(Consultant Cardiologist)* | `clinician@lmth.gov.zm` | `ClinicianPass123!` | Patient charts, diagnosis/medication entry, CDSS alert review & signing |
| **`Administrator`** | Dr. Mutale Mwila *(Chief Medical Info Officer)* | `admin@lmth.gov.zm` | `AdminPass123!` | Full user management, role provisioning, system rules, audit inspection |
| **`Lab_Officer`** | Kondwani Phiri *(Senior Genomic Technologist)* | `lab@lmth.gov.zm` | `LabPass123!` | Genetic biomarker sequencing ingestion & verification |
| **`Auditor`** | Besa Musonda *(Quality & Compliance Officer)* | `auditor@lmth.gov.zm` | `AuditorPass123!` | Read-only inspection of immutable event logs with SHA-256 hashes *(No patient chart access)* |

---

## 3. Pharmacogenomic Rules & Clinical Guidelines

The transparent decision support engine evaluates deterministic interactions based on international CPIC (Clinical Pharmacogenetics Implementation Consortium) and DPWG guidelines:

1. **CYP2C19 vs. Clopidogrel (Plavix)**:
   - *Phenotypes*: Poor Metabolizer (*2/*2, *2/*3, *3/*3), Intermediate Metabolizer (*1/*2)
   - *Mechanism*: Diminished bioactivation of prodrug leading to platelet hyperreactivity, MACE, and stent thrombosis.
   - *Recommendation*: Avoid Clopidogrel; prescribe Prasugrel or Ticagrelor.
2. **HLA-B\*57:01 vs. Abacavir**:
   - *Phenotypes*: Hypersensitivity Risk (*57:01 Positive)
   - *Mechanism*: Severe, potentially fatal multi-organ immunologic hypersensitivity reaction.
   - *Recommendation*: Abacavir strictly contraindicated; re-challenge is lethal. Select Tenofovir-based regimen.
3. **HLA-B\*58:01 vs. Allopurinol**:
   - *Phenotypes*: Severe Cutaneous Adverse Reaction Risk (*58:01 Positive)
   - *Mechanism*: Stevens-Johnson syndrome (SJS) and toxic epidermal necrolysis (TEN).
   - *Recommendation*: Allopurinol contraindicated; prescribe Febuxostat.
4. **CYP2D6 vs. Codeine**:
   - *Phenotypes*: Ultra-Rapid Metabolizer (*1xN/*1), Poor Metabolizer (*4/*4)
   - *Mechanism*: Ultra-rapid conversion precipitates fatal respiratory depression; poor metabolizers experience analgesia failure.
   - *Recommendation*: Avoid Codeine; prescribe non-CYP2D6 analgesic (Morphine/Fentanyl or non-opioids).
5. **TPMT vs. Azathioprine / 6-Mercaptopurine**:
   - *Phenotypes*: Poor Metabolizer (*3A/*3A), Intermediate Metabolizer
   - *Mechanism*: Severe cytotoxic accumulation resulting in profound myelosuppression and fatal pancytopenia.
   - *Recommendation*: Reduce standard dose by 90% or prescribe non-thiopurine immunosuppressant.
6. **VKORC1 vs. Warfarin**:
   - *Phenotypes*: High Sensitivity (-1639G>A / AA genotype)
   - *Mechanism*: Exaggerated anticoagulant response and elevated INR; high hemorrhagic stroke risk.
   - *Recommendation*: Reduce initial loading dose by 30-50% with intensified INR monitoring or DOAC.

---

## 4. Local Development Quickstart

### Prerequisites
- Docker & Docker Compose
- `uv` (Astral Python toolchain)
- `bun` (JavaScript runtime & package manager)

### Step 1: Clone & Configure Environment
```bash
cp .env.example .env
```

### Step 2: Start PostgreSQL Database Container
```bash
docker compose up -d postgres
```

### Step 3: Run Alembic Migrations & Seed Data
```bash
cd Backend
uv run alembic upgrade head
uv run python -m app.scripts.seed
```

### Step 4: Start Backend Dev Server
```bash
cd Backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*API Documentation available at: `http://localhost:8000/api/v1/docs`*

### Step 5: Start Frontend Dev Server
```bash
cd Frontend
bun install
bun run dev
```
*Frontend Application accessible at: `http://localhost:5173`*

---

## 5. Production Containerization

Run the full production stack:
```bash
docker compose up -d --build
```
- **PostgreSQL**: Internal container network persistence on named volume `pm_cdss_pgdata`.
- **FastAPI Backend**: Multi-stage Python 3.12 slim runtime on port 8000.
- **Frontend**: Multi-stage Bun build served via Nginx on port 3000 with gzip compression and reverse proxy routing.
