from fastapi import FastAPI
from database import get_or_create_table
from routers import health, plans, admin, auth

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Sistema Nutricional - API Productor")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite cualquier origen (IP local, IP pública de EC2, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar/verificar la tabla DynamoDB al iniciar el servidor
@app.on_event("startup")
def startup_event():
    get_or_create_table()

# Incluir routers modulares
app.include_router(health.router)
app.include_router(plans.router)
app.include_router(admin.router)
app.include_router(auth.router)
