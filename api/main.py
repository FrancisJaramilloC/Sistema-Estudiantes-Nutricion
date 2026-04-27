from fastapi import FastAPI
import sys
from pathlib import Path

# Agregar el directorio actual a sys.path para que los imports funcionen en Docker
sys.path.insert(0, str(Path(__file__).parent))

from config import API_TITLE, API_VERSION
from routes import api_router

# Crear la aplicación FastAPI
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description="API Productor para el Sistema Nutricional Distribuido"
)

# Incluir todos los routers
app.include_router(api_router)

# Punto de entrada si se ejecuta directamente
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
