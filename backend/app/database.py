from decimal import Decimal
import boto3
from botocore.exceptions import ClientError
from app import config

def get_dynamodb_resource():
    kwargs = {"region_name": config.AWS_REGION}
    if config.DYNAMODB_ENDPOINT_URL:
        kwargs["endpoint_url"] = config.DYNAMODB_ENDPOINT_URL
    if config.AWS_ACCESS_KEY_ID:
        kwargs["aws_access_key_id"] = config.AWS_ACCESS_KEY_ID
    if config.AWS_SECRET_ACCESS_KEY:
        kwargs["aws_secret_access_key"] = config.AWS_SECRET_ACCESS_KEY
    if config.AWS_SESSION_TOKEN:
        kwargs["aws_session_token"] = config.AWS_SESSION_TOKEN
    return boto3.resource('dynamodb', **kwargs)

def get_or_create_table():
    db = get_dynamodb_resource()
    table_name = "tasks"
    try:
        table = db.Table(table_name)
        table.load()
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            table = db.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': 'task_id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'task_id', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            table.wait_until_exists()
            return table
        else:
            raise e

def get_or_create_auditoria_table():
    db = get_dynamodb_resource()
    table_name = "Auditoria_Planes_Table"
    try:
        table = db.Table(table_name)
        table.load()
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            table = db.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': 'calculation_id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'calculation_id', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            table.wait_until_exists()
            return table
        else:
            raise e

def get_or_create_users_table():
    db = get_dynamodb_resource()
    table_name = "users_table"
    try:
        table = db.Table(table_name)
        table.load()
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            table = db.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': 'username', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'username', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            table.wait_until_exists()
            return table
        else:
            raise e

def get_or_create_reset_tokens_table():
    db = get_dynamodb_resource()
    table_name = "reset_tokens"
    try:
        table = db.Table(table_name)
        table.load()
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            table = db.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': 'username', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'username', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            table.wait_until_exists()
            return table
        else:
            raise e

def get_or_create_devices_table():
    db = get_dynamodb_resource()
    table_name = "devices"
    try:
        table = db.Table(table_name)
        table.load()
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            table = db.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': 'device_id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'device_id', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            table.wait_until_exists()
            return table
        else:
            raise e

def get_or_create_heart_rate_table():
    db = get_dynamodb_resource()
    table_name = "heart_rate_readings"
    try:
        table = db.Table(table_name)
        table.load()
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            table = db.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'student_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'student_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            table.wait_until_exists()
            return table
        else:
            raise e

def get_or_create_audit_log_table():
    db = get_dynamodb_resource()
    table_name = "audit_log"
    try:
        table = db.Table(table_name)
        table.load()
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            table = db.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'username', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'username', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            table.wait_until_exists()
            return table
        else:
            raise e

def get_or_create_alimentos_table():
    db = get_dynamodb_resource()
    table_name = "alimentos"
    try:
        table = db.Table(table_name)
        table.load()
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            table = db.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[
                    {'AttributeName': 'id', 'AttributeType': 'S'},
                    {'AttributeName': 'categoria', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[{
                    'IndexName': 'categoria-index',
                    'KeySchema': [{'AttributeName': 'categoria', 'KeyType': 'HASH'}],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
                }],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            table.wait_until_exists()
            return table
        else:
            raise e

def get_or_create_planes_table():
    db = get_dynamodb_resource()
    table_name = "planes_alimenticios"
    try:
        table = db.Table(table_name)
        table.load()
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            table = db.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': 'plan_id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'plan_id', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            table.wait_until_exists()
            return table
        else:
            raise e

def get_or_create_pacientes_table():
    db = get_dynamodb_resource()
    table_name = "pacientes"
    try:
        table = db.Table(table_name)
        table.load()
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            table = db.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': 'paciente_id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'paciente_id', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            table.wait_until_exists()
            return table
        else:
            raise e

def get_or_create_sugerencias_table():
    db = get_dynamodb_resource()
    table_name = "sugerencias_planes"
    try:
        table = db.Table(table_name)
        table.load()
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            table = db.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': 'sugerencia_id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'sugerencia_id', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            table.wait_until_exists()
            return table
        else:
            raise e

def seed_alimentos_if_empty():
    import json
    import os
    if os.getenv("SKIP_AUTO_SEED") == "1":
        return
    table = get_or_create_alimentos_table()
    try:
        response = table.scan(Select='COUNT')
        count = response.get('Count', 0)
    except Exception:
        count = 0
    if count > 0:
        return
    json_path = os.path.join(os.path.dirname(__file__), "alimentos_usfq.json")
    if not os.path.exists(json_path):
        print("[SEED] Archivo alimentos_usfq.json no encontrado, omitiendo seed.")
        return
    with open(json_path, "r", encoding="utf-8") as f:
        alimentos = json.load(f)
    def convert_to_decimal(obj):
        if isinstance(obj, list):
            return [convert_to_decimal(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: convert_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, float):
            return Decimal(str(round(obj, 4)))
        return obj
    exitosos = 0
    errores = 0
    with table.batch_writer() as batch:
        for alimento in alimentos:
            item = convert_to_decimal(alimento)
            try:
                batch.put_item(Item=item)
                exitosos += 1
            except Exception as e:
                print(f"[SEED] Error cargando {alimento.get('id')}: {e}")
                errores += 1
    print(f"[SEED] Alimentos cargados: {exitosos} exitosos, {errores} errores")


def seed_users_if_empty():
    import os
    if os.getenv("SKIP_AUTO_SEED") == "1":
        return
    import bcrypt
    table = get_or_create_users_table()
    try:
        response = table.get_item(Key={"username": "docente_gabriel"})
        if "Item" in response:
            return
    except Exception:
        pass
    usuarios = [
        {"username": "docente_gabriel", "nombre": "Dr. Gabriel Jaramillo", "email": "gabriel.jaramillo@nutria.edu.ec", "password": "Password123*", "role": "Docentes", "cedula": "1712345678", "fecha_nacimiento": "1980-05-15"},
        {"username": "ana", "nombre": "Ana Maria Gomez", "email": "ana.gomez@nutria.edu.ec", "password": "Password123*", "role": "Estudiantes", "cedula": "1723456789", "fecha_nacimiento": "2002-09-21"},
        {"username": "carlos", "nombre": "Carlos Alberto Perez", "email": "carlos.perez@nutria.edu.ec", "password": "Password123*", "role": "Estudiantes", "cedula": "1734567890", "fecha_nacimiento": "2001-03-12"},
        {"username": "sofia", "nombre": "Sofia Valentina Rodriguez", "email": "sofia.rodriguez@nutria.edu.ec", "password": "Password123*", "role": "Estudiantes", "cedula": "1745678901", "fecha_nacimiento": "2003-11-30"},
        {"username": "juan", "nombre": "Juan Diaz", "email": "juan.diaz@nutria.edu.ec", "password": "Password123*", "role": "Estudiantes", "cedula": "1756789012", "fecha_nacimiento": "2002-04-10"},
        {"username": "lucia", "nombre": "Lucia Silva", "email": "lucia.silva@nutria.edu.ec", "password": "Password123*", "role": "Estudiantes", "cedula": "1767890123", "fecha_nacimiento": "2003-08-18"},
        {"username": "diego", "nombre": "Diego Torres", "email": "diego.torres@nutria.edu.ec", "password": "Password123*", "role": "Estudiantes", "cedula": "1778901234", "fecha_nacimiento": "2001-12-05"},
        {"username": "elena", "nombre": "Elena Mendoza", "email": "elena.mendoza@nutria.edu.ec", "password": "Password123*", "role": "Estudiantes", "cedula": "1789012345", "fecha_nacimiento": "2002-06-25"},
        {"username": "mateo", "nombre": "Mateo Castro", "email": "mateo.castro@nutria.edu.ec", "password": "Password123*", "role": "Estudiantes", "cedula": "1790123456", "fecha_nacimiento": "2001-07-14"},
        {"username": "valeria", "nombre": "Valeria Ortiz", "email": "valeria.ortiz@nutria.edu.ec", "password": "Password123*", "role": "Estudiantes", "cedula": "1701234567", "fecha_nacimiento": "2003-02-28"},
        {"username": "adrian", "nombre": "Adrian Ruiz", "email": "adrian.ruiz@nutria.edu.ec", "password": "Password123*", "role": "Estudiantes", "cedula": "1713579246", "fecha_nacimiento": "2002-10-09"},
        {"username": "camila", "nombre": "Camila Flores", "email": "camila.flores@nutria.edu.ec", "password": "Password123*", "role": "Estudiantes", "cedula": "1724680135", "fecha_nacimiento": "2003-05-22"},
        {"username": "nicolas", "nombre": "Nicolas Romero", "email": "nicolas.romero@nutria.edu.ec", "password": "Password123*", "role": "Estudiantes", "cedula": "1735791246", "fecha_nacimiento": "2001-09-17"},
        {"username": "daniela", "nombre": "Daniela Herrera", "email": "daniela.herrera@nutria.edu.ec", "password": "Password123*", "role": "Estudiantes", "cedula": "1746802357", "fecha_nacimiento": "2002-01-30"},
        {"username": "santiago", "nombre": "Santiago Medina", "email": "santiago.medina@nutria.edu.ec", "password": "Password123*", "role": "Estudiantes", "cedula": "1757913468", "fecha_nacimiento": "2001-11-12"},
        {"username": "isabella", "nombre": "Isabella Vargas", "email": "isabella.vargas@nutria.edu.ec", "password": "Password123*", "role": "Estudiantes", "cedula": "1768024579", "fecha_nacimiento": "2003-07-07"},
        {"username": "alejandro", "nombre": "Alejandro Rios", "email": "alejandro.rios@nutria.edu.ec", "password": "Password123*", "role": "Estudiantes", "cedula": "1779135680", "fecha_nacimiento": "2002-08-24"},
        {"username": "mariana", "nombre": "Mariana Acosta", "email": "mariana.acosta@nutria.edu.ec", "password": "Password123*", "role": "Estudiantes", "cedula": "1780246791", "fecha_nacimiento": "2003-03-15"},
        {"username": "sebastian", "nombre": "Sebastian Mora", "email": "sebastian.mora@nutria.edu.ec", "password": "Password123*", "role": "Estudiantes", "cedula": "1791357802", "fecha_nacimiento": "2001-05-04"},
        {"username": "docente_luisa", "nombre": "Dra. Luisa Martinez", "email": "luisa.martinez@nutria.edu.ec", "password": "Password123*", "role": "Docentes", "cedula": "1702468135", "fecha_nacimiento": "1975-12-19"},
        {"username": "docente_ricardo", "nombre": "Dr. Ricardo Alarcon", "email": "ricardo.alarcon@nutria.edu.ec", "password": "Password123*", "role": "Docentes", "cedula": "1713579246", "fecha_nacimiento": "1983-09-08"},
        {"username": "docente_patricia", "nombre": "Dra. Patricia Cueva", "email": "patricia.cueva@nutria.edu.ec", "password": "Password123*", "role": "Docentes", "cedula": "1724680357", "fecha_nacimiento": "1978-04-26"},
        {"username": "docente_hugo", "nombre": "Dr. Hugo Paredes", "email": "hugo.paredes@nutria.edu.ec", "password": "Password123*", "role": "Docentes", "cedula": "1735791468", "fecha_nacimiento": "1985-02-14"},
        {"username": "docente_beatriz", "nombre": "Dra. Beatriz Sanchez", "email": "beatriz.sanchez@nutria.edu.ec", "password": "Password123*", "role": "Docentes", "cedula": "1746802579", "fecha_nacimiento": "1981-07-22"},
    ]
    exitosos = 0
    for u in usuarios:
        try:
            hashed = bcrypt.hashpw(u["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            table.put_item(Item={
                "username": u["username"], "nombre": u["nombre"], "email": u["email"],
                "password": hashed, "role": u["role"], "cedula": u["cedula"],
                "fecha_nacimiento": u["fecha_nacimiento"],
            })
            exitosos += 1
        except Exception as e:
            print(f"[SEED] Error al insertar usuario '{u['username']}': {e}")
    print(f"[SEED] Usuarios cargados: {exitosos}/{len(usuarios)}")

def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    return obj
