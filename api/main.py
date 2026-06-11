from fastapi import FastAPI
from database import get_or_create_table, get_or_create_auditoria_table, get_or_create_users_table
from routers import health, plans, admin, auth, clinical

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Sistema Nutricional - API Productor")

# Configuración de CORS conforme a las políticas del PRD
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://3.134.114.180:3000",
        "http://18.216.159.136:3000"
    ],
    allow_origin_regex="https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar/verificar las tablas DynamoDB al iniciar el servidor
@app.on_event("startup")
def startup_event():
    get_or_create_table()
    get_or_create_auditoria_table()
    get_or_create_users_table()

# Incluir routers modulares (Legados y V1 requeridos por PRD)
app.include_router(health.router)

# Rutas estándar / legadas
app.include_router(plans.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(clinical.router)

# Rutas con prefijo /api/v1 requerido por contrato OpenAPI
app.include_router(plans.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(clinical.router, prefix="/api/v1")

