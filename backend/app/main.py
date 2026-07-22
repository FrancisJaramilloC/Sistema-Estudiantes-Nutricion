from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from app.database import (
    get_or_create_table, get_or_create_auditoria_table,
    get_or_create_users_table, get_or_create_reset_tokens_table,
    get_or_create_devices_table, get_or_create_heart_rate_table,
    get_or_create_alimentos_table, get_or_create_planes_table,
    get_or_create_pacientes_table, get_or_create_sugerencias_table,
    get_or_create_audit_log_table, seed_alimentos_if_empty, seed_users_if_empty,
)
from app.routes import health, plans, admin, auth, clinical, devices, alimentos, plan_nutricional, sugerencia
from app.monitoring import SecurityMonitoringMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

app = FastAPI(title="NUTRIA - API Motor Antropométrico")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex="https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityMonitoringMiddleware)


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.on_event("startup")
def startup_event():
    get_or_create_table()
    get_or_create_auditoria_table()
    get_or_create_users_table()
    get_or_create_reset_tokens_table()
    get_or_create_devices_table()
    get_or_create_heart_rate_table()
    get_or_create_alimentos_table()
    get_or_create_planes_table()
    get_or_create_pacientes_table()
    get_or_create_sugerencias_table()
    get_or_create_audit_log_table()
    seed_users_if_empty()
    seed_alimentos_if_empty()

app.include_router(health.router)
app.include_router(plans.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(clinical.router)
app.include_router(devices.router)
app.include_router(alimentos.router)
app.include_router(plan_nutricional.router)
app.include_router(sugerencia.router)

app.include_router(plans.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(clinical.router, prefix="/api/v1")
app.include_router(devices.router, prefix="/api/v1")
app.include_router(alimentos.router, prefix="/api/v1")
app.include_router(plan_nutricional.router, prefix="/api/v1")
app.include_router(sugerencia.router, prefix="/api/v1")
