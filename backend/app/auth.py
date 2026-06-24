import jwt
import logging
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app import config

logger = logging.getLogger("nutria.monitoring")

security = HTTPBearer()

jwks_client = None
if config.COGNITO_USER_POOL_ID and not config.COGNITO_USER_POOL_ID.startswith("mock") and config.COGNITO_USER_POOL_ID != "":
    jwks_url = f"https://cognito-idp.{config.AWS_REGION}.amazonaws.com/{config.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    try:
        jwks_client = jwt.PyJWKClient(jwks_url)
    except Exception:
        jwks_client = None

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        return payload
    except Exception:
        pass

    if jwks_client and config.COGNITO_USER_POOL_ID:
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=config.COGNITO_APP_CLIENT_ID,
                issuer=f"https://cognito-idp.{config.AWS_REGION}.amazonaws.com/{config.COGNITO_USER_POOL_ID}"
            )
            return payload
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Token JWT inválido: {str(e)}")

    if token == "mock-teacher-token":
        return {"username": "docente_prueba", "cognito:groups": ["Docentes"]}
    elif token == "mock-student-token":
        return {"username": "estudiante_prueba", "cognito:groups": ["Estudiantes"]}

    raise HTTPException(status_code=401, detail="Token de sesión no válido o expirado localmente.")

def require_role(allowed_groups: list):
    def dependency(user: dict = Depends(get_current_user)):
        groups = user.get("cognito:groups", [])
        if not groups:
            groups = ["Estudiantes"]
        if not any(g in allowed_groups for g in groups):
            email = user.get("email", "desconocido")
            logger.warning(
                "[SECURITY ALERT] Intento de acceso no autorizado por rol "
                "a funciones clínicas. Origen: %s",
                email,
            )
            raise HTTPException(
                status_code=403,
                detail=f"Acceso denegado. Se requiere pertenecer a uno de los grupos: {allowed_groups}"
            )
        return user
    return dependency
