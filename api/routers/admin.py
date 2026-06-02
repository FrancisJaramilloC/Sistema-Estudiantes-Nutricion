from fastapi import APIRouter, HTTPException, Depends
from botocore.exceptions import ClientError
from database import get_or_create_table, convert_decimals
from auth import require_role

router = APIRouter()

@router.get("/admin/tasks")
async def get_all_tasks(user: dict = Depends(require_role(["Docentes"]))):
    """Endpoint administrativo exclusivo para Docentes. Escanea y retorna todas las tareas."""
    table = get_or_create_table()
    try:
        response = table.scan()
        items = response.get("Items", [])
        return convert_decimals(items)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
