from fastapi import APIRouter, HTTPException, Depends
from botocore.exceptions import ClientError
from app.database import get_or_create_table, convert_decimals
from app.auth import require_role

router = APIRouter()

@router.get("/admin/tasks")
async def get_all_tasks(user: dict = Depends(require_role(["Docentes"]))):
    table = get_or_create_table()
    try:
        response = table.scan()
        items = response.get("Items", [])
        return convert_decimals(items)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
