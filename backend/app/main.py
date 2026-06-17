from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_or_create_table, get_or_create_auditoria_table, get_or_create_users_table
from app.routes import health, plans, admin, auth, clinical

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

@app.on_event("startup")
def startup_event():
    get_or_create_table()
    get_or_create_auditoria_table()
    get_or_create_users_table()

app.include_router(health.router)
app.include_router(plans.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(clinical.router)

app.include_router(plans.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(clinical.router, prefix="/api/v1")
