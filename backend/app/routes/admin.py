from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError
from app.database import get_or_create_table, convert_decimals, get_dynamodb_resource
from app.auth import require_role
from app import config

router = APIRouter()

class UpdateUserRoleRequest(BaseModel):
    role: str

def is_local_mode():
    return not config.COGNITO_USER_POOL_ID or config.COGNITO_USER_POOL_ID.startswith("mock") or config.COGNITO_USER_POOL_ID == ""

def get_cognito_client():
    kwargs = {"region_name": config.AWS_REGION}
    if config.AWS_ACCESS_KEY_ID:
        kwargs["aws_access_key_id"] = config.AWS_ACCESS_KEY_ID
    if config.AWS_SECRET_ACCESS_KEY:
        kwargs["aws_secret_access_key"] = config.AWS_SECRET_ACCESS_KEY
    if config.AWS_SESSION_TOKEN:
        kwargs["aws_session_token"] = config.AWS_SESSION_TOKEN
    return boto3.client('cognito-idp', **kwargs)

@router.get("/admin/tasks")
async def get_all_tasks(user: dict = Depends(require_role(["Docentes"]))):
    table = get_or_create_table()
    try:
        response = table.scan()
        items = response.get("Items", [])
        return convert_decimals(items)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/users")
async def get_all_users(user: dict = Depends(require_role(["Docentes"]))):
    if is_local_mode():
        try:
            db = get_dynamodb_resource()
            table = db.Table("users_table")
            response = table.scan()
            items = response.get("Items", [])
            # Mask passwords for security
            for item in items:
                if "password" in item:
                    del item["password"]
            return convert_decimals(items)
        except ClientError as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        client = get_cognito_client()
        try:
            response = client.list_users(
                UserPoolId=config.COGNITO_USER_POOL_ID
            )
            users = []
            for cognito_user in response.get("Users", []):
                attrs = {attr["Name"]: attr["Value"] for attr in cognito_user.get("Attributes", [])}
                username = cognito_user["Username"]
                
                # Fetch groups/role
                try:
                    groups_response = client.admin_list_groups_for_user(
                        Username=username,
                        UserPoolId=config.COGNITO_USER_POOL_ID
                    )
                    groups = [g["GroupName"] for g in groups_response.get("Groups", [])]
                except Exception:
                    groups = []
                
                role = "Estudiantes"
                if "Docentes" in groups:
                    role = "Docentes"
                elif "Estudiantes" in groups:
                    role = "Estudiantes"
                
                users.append({
                    "username": username,
                    "email": attrs.get("email", ""),
                    "nombre": attrs.get("name", ""),
                    "cedula": attrs.get("profile", ""),
                    "fecha_nacimiento": attrs.get("birthdate", ""),
                    "role": role,
                    "status": cognito_user.get("UserStatus", "UNKNOWN")
                })
            return users
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.delete("/admin/users/{username}")
async def delete_user(username: str, user: dict = Depends(require_role(["Docentes"]))):
    # Don't let users delete themselves
    current_username = user.get("username") or user.get("sub")
    if username == current_username:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario administrador.")
        
    if is_local_mode():
        try:
            db = get_dynamodb_resource()
            table = db.Table("users_table")
            
            # Check if user exists
            chk = table.get_item(Key={"username": username})
            if "Item" not in chk:
                raise HTTPException(status_code=404, detail="Usuario no encontrado.")
                
            table.delete_item(Key={"username": username})
            return {"message": f"Usuario '{username}' eliminado con éxito localmente."}
        except ClientError as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        client = get_cognito_client()
        try:
            client.admin_delete_user(
                UserPoolId=config.COGNITO_USER_POOL_ID,
                Username=username
            )
            return {"message": f"Usuario '{username}' eliminado con éxito de Cognito."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.put("/admin/users/{username}/role")
async def update_user_role(username: str, req: UpdateUserRoleRequest, user: dict = Depends(require_role(["Docentes"]))):
    if req.role not in ["Docentes", "Estudiantes"]:
        raise HTTPException(status_code=400, detail="Rol inválido. Debe ser 'Docentes' o 'Estudiantes'.")
        
    current_username = user.get("username") or user.get("sub")
    if username == current_username:
        raise HTTPException(status_code=400, detail="No puedes modificar tu propio rol administrador.")
        
    if is_local_mode():
        try:
            db = get_dynamodb_resource()
            table = db.Table("users_table")
            response = table.get_item(Key={"username": username})
            if "Item" not in response:
                raise HTTPException(status_code=404, detail="Usuario no encontrado.")
            table.update_item(
                Key={"username": username},
                UpdateExpression="SET #role = :role",
                ExpressionAttributeNames={"#role": "role"},
                ExpressionAttributeValues={":role": req.role}
            )
            return {"message": f"Rol de '{username}' actualizado a '{req.role}' con éxito."}
        except ClientError as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        client = get_cognito_client()
        try:
            # Remove from relevant groups
            for grp in ["Docentes", "Estudiantes"]:
                try:
                    client.admin_remove_user_from_group(
                        UserPoolId=config.COGNITO_USER_POOL_ID,
                        Username=username,
                        GroupName=grp
                    )
                except Exception:
                    pass
            # Add to the new group
            client.admin_add_user_to_group(
                UserPoolId=config.COGNITO_USER_POOL_ID,
                Username=username,
                GroupName=req.role
            )
            return {"message": f"Rol de '{username}' actualizado a '{req.role}' en Cognito."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

