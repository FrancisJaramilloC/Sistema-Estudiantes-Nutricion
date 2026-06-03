from enum import Enum
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import boto3
import config

router = APIRouter(prefix="/auth", tags=["Auth"])

class UserRole(str, Enum):
    ESTUDIANTES = "Estudiantes"
    DOCENTES = "Docentes"

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: UserRole  # Genera un dropdown en Swagger UI

class LoginRequest(BaseModel):
    username: str
    password: str

def get_cognito_client():
    kwargs = {"region_name": config.AWS_REGION}
    if config.AWS_ACCESS_KEY_ID:
        kwargs["aws_access_key_id"] = config.AWS_ACCESS_KEY_ID
    if config.AWS_SECRET_ACCESS_KEY:
        kwargs["aws_secret_access_key"] = config.AWS_SECRET_ACCESS_KEY
    if config.AWS_SESSION_TOKEN:
        kwargs["aws_session_token"] = config.AWS_SESSION_TOKEN
    return boto3.client('cognito-idp', **kwargs)

@router.post("/register")
def register(req: RegisterRequest):
    client = get_cognito_client()
    
    try:
        # 1. Registrar al usuario en el Cognito User Pool
        client.sign_up(
            ClientId=config.COGNITO_APP_CLIENT_ID,
            Username=req.username,
            Password=req.password,
            UserAttributes=[
                {'Name': 'email', 'Value': req.email}
            ]
        )
        
        # 2. Confirmar al usuario automáticamente
        client.admin_confirm_sign_up(
            UserPoolId=config.COGNITO_USER_POOL_ID,
            Username=req.username
        )
        
        # 3. Asignar el usuario al grupo seleccionado
        client.admin_add_user_to_group(
            UserPoolId=config.COGNITO_USER_POOL_ID,
            Username=req.username,
            GroupName=req.role.value
        )
        
        return {
            "message": f"Usuario '{req.username}' registrado, verificado y asignado al grupo '{req.role.value}' con éxito."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login(req: LoginRequest):
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
        return {
            "access_token": response['AuthenticationResult']['AccessToken'],
            "id_token": response['AuthenticationResult']['IdToken'],
            "expires_in": response['AuthenticationResult']['ExpiresIn']
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
