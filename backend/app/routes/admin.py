import bcrypt
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from app.database import get_or_create_table, convert_decimals, get_dynamodb_resource, get_or_create_audit_log_table
from boto3.dynamodb.conditions import Attr
from app.auth import require_role
from app import config
from app.audit import log_user_event

router = APIRouter()

class UpdateUserRoleRequest(BaseModel):
    role: str

class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str
    nombre: str
    cedula: str
    fecha_nacimiento: str

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
    actor_id = user.get("username") or user.get("sub")
    current_username = actor_id
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
            log_user_event(actor_id, "DELETE_USER", username, "Eliminado por administrador")
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
            log_user_event(actor_id, "DELETE_USER", username, "Eliminado por administrador (Cognito)")
            return {"message": f"Usuario '{username}' eliminado con éxito de Cognito."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.put("/admin/users/{username}/role")
async def update_user_role(username: str, req: UpdateUserRoleRequest, user: dict = Depends(require_role(["Docentes"]))):
    if req.role not in ["Docentes", "Estudiantes"]:
        raise HTTPException(status_code=400, detail="Rol inválido. Debe ser 'Docentes' o 'Estudiantes'.")
        
    actor_id = user.get("username") or user.get("sub")
    current_username = actor_id
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
            log_user_event(actor_id, "UPDATE_ROLE", username, f"Rol cambiado a {req.role}")
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

@router.get("/admin/audit/login-events")
async def get_login_audit_events(user: dict = Depends(require_role(["Docentes"]))):
    """
    Devuelve los últimos eventos de inicio de sesión (exitosos y fallidos)
    registrados en la tabla audit_log, ordenados del más reciente al más antiguo.
    """
    try:
        table = get_or_create_audit_log_table()
        response = table.scan()
        items = response.get("Items", [])
        items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return convert_decimals(items[:50])
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/audit/all")
async def get_all_audit_events(
    event_type: Optional[str] = Query(None, description="Filtrar por tipo de evento"),
    usuario: Optional[str] = Query(None, description="Filtrar por usuario/actor"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (ISO 8601)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (ISO 8601)"),
    limite: int = Query(100, ge=1, le=500),
    user: dict = Depends(require_role(["Docentes"])),
):
    """
    Panel de auditoría ampliado (RNF9): retorna todos los eventos del sistema
    con filtros por tipo, usuario y rango de fechas.
    """
    try:
        table = get_or_create_audit_log_table()
        response = table.scan()
        items = response.get("Items", [])

        if event_type:
            items = [i for i in items if i.get("event_type", "").upper() == event_type.upper()]
        if usuario:
            items = [i for i in items if usuario.lower() in i.get("username", "").lower()]
        if fecha_desde:
            items = [i for i in items if i.get("timestamp", "") >= fecha_desde]
        if fecha_hasta:
            items = [i for i in items if i.get("timestamp", "") <= fecha_hasta]

        items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return convert_decimals(items[:limite])
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/create-user", status_code=201)
async def admin_create_user(
    req: CreateUserRequest,
    user: dict = Depends(require_role(["Docentes"])),
):
    """
    Endpoint protegido para que el administrador cree cuentas con cualquier rol.
    Solo accesible con rol Docentes (admin) autenticado vía backend (RF - Seguridad).
    """
    if req.role not in ["Docentes", "Estudiantes"]:
        raise HTTPException(status_code=400, detail="Rol inválido. Debe ser 'Docentes' o 'Estudiantes'.")

    actor_id = user.get("username", user.get("sub", "unknown"))

    if is_local_mode():
        try:
            db = get_dynamodb_resource()
            table = db.Table("users_table")

            existing = table.get_item(Key={"username": req.username})
            if "Item" in existing:
                raise HTTPException(status_code=400, detail=f"El usuario '{req.username}' ya existe.")

            hashed_password = bcrypt.hashpw(req.password.encode('utf-8'), bcrypt.gensalt())

            table.put_item(Item={
                "username": req.username,
                "email": req.email,
                "password": hashed_password.decode('utf-8'),
                "role": req.role,
                "nombre": req.nombre,
                "cedula": req.cedula,
                "fecha_nacimiento": req.fecha_nacimiento,
            })

            log_user_event(actor_id, "CREATE_USER", req.username, f"Rol: {req.role}")

            return {"message": f"Usuario '{req.username}' creado con rol '{req.role}' por administrador."}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        client = get_cognito_client()
        try:
            client.admin_create_user(
                UserPoolId=config.COGNITO_USER_POOL_ID,
                Username=req.username,
                TemporaryPassword=req.password,
                UserAttributes=[
                    {'Name': 'email', 'Value': req.email},
                    {'Name': 'name', 'Value': req.nombre},
                    {'Name': 'birthdate', 'Value': req.fecha_nacimiento},
                    {'Name': 'profile', 'Value': req.cedula},
                ]
            )
            client.admin_set_user_password(
                UserPoolId=config.COGNITO_USER_POOL_ID,
                Username=req.username,
                Password=req.password,
                Permanent=True
            )
            client.admin_add_user_to_group(
                UserPoolId=config.COGNITO_USER_POOL_ID,
                Username=req.username,
                GroupName=req.role
            )

            log_user_event(actor_id, "CREATE_USER", req.username, f"Rol: {req.role}")

            return {"message": f"Usuario '{req.username}' creado con rol '{req.role}' en Cognito."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
