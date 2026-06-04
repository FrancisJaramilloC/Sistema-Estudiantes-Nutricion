import jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import config

security = HTTPBearer()

jwks_client = None
if config.COGNITO_USER_POOL_ID:
    jwks_url = f"https://cognito-idp.{config.AWS_REGION}.amazonaws.com/{config.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    jwks_client = jwt.PyJWKClient(jwks_url)

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    
    # Modo local / Mock (si no está configurado Cognito real en el entorno)
    if not config.COGNITO_USER_POOL_ID:
        if token == "mock-teacher-token":
            return {"username": "docente_prueba", "cognito:groups": ["Docentes"]}
        elif token == "mock-student-token":
            return {"username": "estudiante_prueba", "cognito:groups": ["Estudiantes"]}
        else:
            # Por defecto si no se pasa token especial en local, asumimos Estudiantes
            return {"username": "usuario_local", "cognito:groups": ["Estudiantes"]}
            
    # Validación real de firmas JWT de AWS Cognito en la Nube
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

def require_role(allowed_groups: list):
    def dependency(user: dict = Depends(get_current_user)):
        groups = user.get("cognito:groups", [])
        if not groups:
            groups = ["Estudiantes"]
        if not any(g in allowed_groups for g in groups):
            raise HTTPException(
                status_code=403, 
                detail=f"Acceso denegado. Se requiere pertenecer a uno de los grupos: {allowed_groups}"
            )
        return user
    return dependency
