import os
from dotenv import load_dotenv

load_dotenv()

# AWS Configurations
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
DYNAMODB_ENDPOINT_URL = os.getenv("DYNAMODB_ENDPOINT_URL")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")

# AWS Cognito Configurations
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")
# Nombres de tablas (configurable por ambiente)
TASKS_TABLE = os.getenv("TASKS_TABLE", "tasks")
AUDITORIA_TABLE = os.getenv("AUDITORIA_TABLE", "Auditoria_Planes_Table")
USERS_TABLE = os.getenv("USERS_TABLE", "users_table")
