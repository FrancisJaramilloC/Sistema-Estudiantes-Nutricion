import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
DYNAMODB_ENDPOINT_URL = os.getenv("DYNAMODB_ENDPOINT_URL")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")

COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID")

JWT_SECRET = os.getenv("JWT_SECRET", "nutria-secret-key-12345")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_EXTERNAL_HOST = os.getenv("MQTT_EXTERNAL_HOST", MQTT_HOST)
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "backend")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "backend_mqtt_2026")
MQTT_TOPIC_PREFIX = "dispositivos"
MQTT_PASSWD_FILE = "/mosquitto_data/passwd"
MOSQUITTO_CONTAINER = "mosquitto_nutricion"
