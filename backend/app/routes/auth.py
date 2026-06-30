import secrets
from enum import Enum
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import bcrypt
import boto3
import jwt as pyjwt
import datetime
from app import config
from app.database import get_dynamodb_resource, get_or_create_reset_tokens_table, get_or_create_audit_log_table
from app.monitoring import log_login_event
import uuid

router = APIRouter(prefix="/auth", tags=["Auth"])

class UserRole(str, Enum):
    ESTUDIANTES = "Estudiantes"
    DOCENTES = "Docentes"

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: UserRole
    nombre: str
    cedula: str
    fecha_nacimiento: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    username: str
    reset_token: str
    new_password: str

def get_cognito_client():
    kwargs = {"region_name": config.AWS_REGION}
    if config.AWS_ACCESS_KEY_ID:
        kwargs["aws_access_key_id"] = config.AWS_ACCESS_KEY_ID
    if config.AWS_SECRET_ACCESS_KEY:
        kwargs["aws_secret_access_key"] = config.AWS_SECRET_ACCESS_KEY
    if config.AWS_SESSION_TOKEN:
        kwargs["aws_session_token"] = config.AWS_SESSION_TOKEN
    return boto3.client('cognito-idp', **kwargs)

def is_local_mode():
    return not config.COGNITO_USER_POOL_ID or config.COGNITO_USER_POOL_ID.startswith("mock") or config.COGNITO_USER_POOL_ID == ""

def record_login_attempt(username: str, success: bool, reason: str = ""):
    """
    Registra un intento de inicio de sesión (exitoso o fallido) en la
    tabla audit_log para su posterior visualización en el panel de auditoría.
    """
    try:
        audit_table = get_or_create_audit_log_table()
        audit_table.put_item(Item={
            "username": username,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "event_id": str(uuid.uuid4()),
            "event_type": "LOGIN_SUCCESS" if success else "LOGIN_FAILED",
            "success": success,
            "reason": reason
        })
    except Exception:
        pass

@router.post("/register", status_code=201)
def register(req: RegisterRequest):
    if is_local_mode():
        try:
            db = get_dynamodb_resource()
            table = db.Table("users_table")

            response = table.get_item(Key={"username": req.username})
            if "Item" in response:
                raise HTTPException(status_code=400, detail=f"El nombre de usuario '{req.username}' ya está registrado.")

            response_email = table.scan(
                FilterExpression="email = :email",
                ExpressionAttributeValues={":email": req.email}
            )
            if response_email.get("Items"):
                raise HTTPException(status_code=400, detail=f"El correo electrónico '{req.email}' ya está registrado.")

            response_cedula = table.scan(
                FilterExpression="cedula = :cedula",
                ExpressionAttributeValues={":cedula": req.cedula}
            )
            if response_cedula.get("Items"):
                raise HTTPException(status_code=400, detail=f"La cédula '{req.cedula}' ya está registrada.")

            hashed_password = bcrypt.hashpw(req.password.encode('utf-8'), bcrypt.gensalt())

            table.put_item(Item={
                "username": req.username,
                "email": req.email,
                "password": hashed_password.decode('utf-8'),
                "role": req.role.value,
                "nombre": req.nombre,
                "cedula": req.cedula,
                "fecha_nacimiento": req.fecha_nacimiento
            })

            return {"message": f"Usuario '{req.username}' registrado localmente y asignado al rol '{req.role.value}' con éxito."}
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=400, detail=f"Error en registro local: {str(e)}")

    client = get_cognito_client()
    try:
        client.sign_up(
            ClientId=config.COGNITO_APP_CLIENT_ID,
            Username=req.username,
            Password=req.password,
            UserAttributes=[
                {'Name': 'email', 'Value': req.email},
                {'Name': 'name', 'Value': req.nombre},
                {'Name': 'birthdate', 'Value': req.fecha_nacimiento},
                {'Name': 'profile', 'Value': req.cedula}
            ]
        )
        client.admin_confirm_sign_up(
            UserPoolId=config.COGNITO_USER_POOL_ID,
            Username=req.username
        )
        client.admin_add_user_to_group(
            UserPoolId=config.COGNITO_USER_POOL_ID,
            Username=req.username,
            GroupName=req.role.value
        )
        return {"message": f"Usuario '{req.username}' registrado, verificado y asignado al grupo '{req.role.value}' con éxito."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login(req: LoginRequest):
    if is_local_mode():
        try:
            db = get_dynamodb_resource()
            table = db.Table("users_table")

            response = table.get_item(Key={"username": req.username})
            if "Item" not in response:
                record_login_attempt(req.username, success=False, reason="Usuario no encontrado")
                raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos.")

            user = response["Item"]
            stored_password = user["password"]

            if not bcrypt.checkpw(req.password.encode('utf-8'), stored_password.encode('utf-8')):
                record_login_attempt(req.username, success=False, reason="Contraseña incorrecta")
                raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos.")

            payload = {
                "sub": user["username"],
                "username": user["username"],
                "name": user["nombre"],
                "email": user["email"],
                "birthdate": user["fecha_nacimiento"],
                "profile": user["cedula"],
                "cognito:groups": [user["role"]],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=config.JWT_EXPIRATION_HOURS)
            }

            token = pyjwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)

            log_login_event(user["username"])
            record_login_attempt(user["username"], success=True)

            return {
                "access_token": token,
                "id_token": token,
                "expires_in": config.JWT_EXPIRATION_HOURS * 3600
            }
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=400, detail=f"Error en login local: {str(e)}")

    client = get_cognito_client()
    try:
        response = client.initiate_auth(
            ClientId=config.COGNITO_APP_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': req.username,
                'PASSWORD': req.password
            }
        )
        log_login_event(req.username)
        return {
            "access_token": response['AuthenticationResult']['AccessToken'],
            "id_token": response['AuthenticationResult']['IdToken'],
            "expires_in": response['AuthenticationResult']['ExpiresIn']
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    if is_local_mode():
        try:
            db = get_dynamodb_resource()
            users_table = db.Table("users_table")

            response = users_table.scan(
                FilterExpression="email = :email",
                ExpressionAttributeValues={":email": req.email}
            )
            items = response.get("Items", [])
            if not items:
                raise HTTPException(status_code=404, detail="No existe una cuenta asociada a ese correo.")

            user = items[0]
            username = user["username"]

            reset_token = secrets.token_urlsafe(32)
            expires_at = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat()

            reset_table = get_or_create_reset_tokens_table()
            reset_table.put_item(Item={
                "username": username,
                "reset_token": reset_token,
                "expires_at": expires_at
            })

            return {
                "message": "Si el correo está registrado, recibirás un enlace para restablecer tu contraseña.",
                "reset_token": reset_token,
                "username": username
            }
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=400, detail=f"Error al solicitar recuperación: {str(e)}")

    client = get_cognito_client()
    try:
        client.forgot_password(
            ClientId=config.COGNITO_APP_CLIENT_ID,
            Username=req.email
        )
        return {"message": "Si el correo está registrado, recibirás un código de verificación."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest):
    if is_local_mode():
        try:
            db = get_dynamodb_resource()
            users_table = db.Table("users_table")

            response = users_table.get_item(Key={"username": req.username})
            if "Item" not in response:
                raise HTTPException(status_code=404, detail="Usuario no encontrado.")

            reset_table = get_or_create_reset_tokens_table()
            token_response = reset_table.get_item(Key={"username": req.username})
            if "Item" not in token_response:
                raise HTTPException(status_code=400, detail="No se ha solicitado un restablecimiento de contraseña.")

            stored_token = token_response["Item"]["reset_token"]
            expires_at = token_response["Item"]["expires_at"]

            if stored_token != req.reset_token:
                raise HTTPException(status_code=400, detail="El código de restablecimiento no es válido.")

            expires = datetime.datetime.fromisoformat(expires_at)
            if datetime.datetime.utcnow() > expires:
                reset_table.delete_item(Key={"username": req.username})
                raise HTTPException(status_code=400, detail="El código de restablecimiento ha expirado. Solicita uno nuevo.")

            hashed_password = bcrypt.hashpw(req.new_password.encode('utf-8'), bcrypt.gensalt())
            users_table.update_item(
                Key={"username": req.username},
                UpdateExpression="SET #pw = :pw",
                ExpressionAttributeNames={"#pw": "password"},
                ExpressionAttributeValues={":pw": hashed_password.decode('utf-8')}
            )

            reset_table.delete_item(Key={"username": req.username})

            return {"message": "Contraseña restablecida con éxito. Ya puedes iniciar sesión."}
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=400, detail=f"Error al restablecer contraseña: {str(e)}")

    client = get_cognito_client()
    try:
        client.confirm_forgot_password(
            ClientId=config.COGNITO_APP_CLIENT_ID,
            Username=req.username,
            ConfirmationCode=req.reset_token,
            Password=req.new_password
        )
        return {"message": "Contraseña restablecida con éxito. Ya puedes iniciar sesión."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
