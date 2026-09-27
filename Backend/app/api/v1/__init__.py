from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.patients import router as patients_router
from app.api.v1.clinical import router as clinical_router
from app.api.v1.genomics import router as genomics_router
from app.api.v1.cdss import router as cdss_router
from app.api.v1.audit import router as audit_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(patients_router)
api_router.include_router(clinical_router)
api_router.include_router(genomics_router)
api_router.include_router(cdss_router)
api_router.include_router(audit_router)
