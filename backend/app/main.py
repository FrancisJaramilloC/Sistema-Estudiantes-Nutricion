from fastapi import FastAPI
from fastapi.responses import Response
from app.database import get_or_create_table, get_or_create_auditoria_table, get_or_create_users_table, get_or_create_reset_tokens_table, get_or_create_devices_table, get_or_create_heart_rate_table, get_or_create_pairing_codes_table
from app.routes import health, plans, admin, auth, clinical, devices
from app.monitoring import SecurityMonitoringMiddleware
from app.cors import PermissiveCORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

app = FastAPI(title="NUTRIA - API Motor Antropométrico")

app.add_middleware(SecurityMonitoringMiddleware)
# Middleware CORS más externo: refleja el Origin en todas las respuestas,
# incluyendo preflight OPTIONS y respuestas de error.
app.add_middleware(PermissiveCORSMiddleware)


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
    get_or_create_pairing_codes_table()

app.include_router(health.router)
app.include_router(plans.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(clinical.router)
app.include_router(devices.router)

app.include_router(plans.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(clinical.router, prefix="/api/v1")
app.include_router(devices.router, prefix="/api/v1")
