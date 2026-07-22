import os
import boto3
import bcrypt
from botocore.exceptions import ClientError

def seed():
    # Usamos la variable de entorno o localhost:8001 si se corre desde el host
    endpoint_url = os.getenv("DYNAMODB_ENDPOINT_URL", "http://localhost:8001")
    region_name = "us-east-2"
    aws_access_key_id = "mock"
    aws_secret_access_key = "mock"

    db = boto3.resource(
        'dynamodb',
        endpoint_url=endpoint_url,
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )

    table_name = "users_table"
    
    try:
        table = db.Table(table_name)
        table.load()
        print(f"Conectado a la tabla '{table_name}' en {endpoint_url}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"Creando tabla '{table_name}'...")
            table = db.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': 'username', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'username', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            table.wait_until_exists()
            print(f"Tabla '{table_name}' creada exitosamente.")
        else:
            print(f"Error al conectar/crear tabla: {e}")
            return

    # Usuarios a registrar
    usuarios = [
        # Usuarios iniciales
        {
            "username": "docente_gabriel",
            "nombre": "Dr. Gabriel Jaramillo",
            "email": "gabriel.jaramillo@nutria.edu.ec",
            "password": "Password123*",
            "role": "Docentes",
            "cedula": "1712345678",
            "fecha_nacimiento": "1980-05-15"
        },
        {
            "username": "ana",
            "nombre": "Ana Maria Gomez",
            "email": "ana.gomez@nutria.edu.ec",
            "password": "Password123*",
            "role": "Estudiantes",
            "cedula": "1723456789",
            "fecha_nacimiento": "2002-09-21"
        },
        {
            "username": "carlos",
            "nombre": "Carlos Alberto Perez",
            "email": "carlos.perez@nutria.edu.ec",
            "password": "Password123*",
            "role": "Estudiantes",
            "cedula": "1734567890",
            "fecha_nacimiento": "2001-03-12"
        },
        {
            "username": "sofia",
            "nombre": "Sofia Valentina Rodriguez",
            "email": "sofia.rodriguez@nutria.edu.ec",
            "password": "Password123*",
            "role": "Estudiantes",
            "cedula": "1745678901",
            "fecha_nacimiento": "2003-11-30"
        },
        # 20 Usuarios adicionales (mezcla de estudiantes y docentes)
        {
            "username": "juan",
            "nombre": "Juan Diaz",
            "email": "juan.diaz@nutria.edu.ec",
            "password": "Password123*",
            "role": "Estudiantes",
            "cedula": "1756789012",
            "fecha_nacimiento": "2002-04-10"
        },
        {
            "username": "lucia",
            "nombre": "Lucia Silva",
            "email": "lucia.silva@nutria.edu.ec",
            "password": "Password123*",
            "role": "Estudiantes",
            "cedula": "1767890123",
            "fecha_nacimiento": "2003-08-18"
        },
        {
            "username": "diego",
            "nombre": "Diego Torres",
            "email": "diego.torres@nutria.edu.ec",
            "password": "Password123*",
            "role": "Estudiantes",
            "cedula": "1778901234",
            "fecha_nacimiento": "2001-12-05"
        },
        {
            "username": "elena",
            "nombre": "Elena Mendoza",
            "email": "elena.mendoza@nutria.edu.ec",
            "password": "Password123*",
            "role": "Estudiantes",
            "cedula": "1789012345",
            "fecha_nacimiento": "2002-06-25"
        },
        {
            "username": "mateo",
            "nombre": "Mateo Castro",
            "email": "mateo.castro@nutria.edu.ec",
            "password": "Password123*",
            "role": "Estudiantes",
            "cedula": "1790123456",
            "fecha_nacimiento": "2001-07-14"
        },
        {
            "username": "valeria",
            "nombre": "Valeria Ortiz",
            "email": "valeria.ortiz@nutria.edu.ec",
            "password": "Password123*",
            "role": "Estudiantes",
            "cedula": "1701234567",
            "fecha_nacimiento": "2003-02-28"
        },
        {
            "username": "adrian",
            "nombre": "Adrian Ruiz",
            "email": "adrian.ruiz@nutria.edu.ec",
            "password": "Password123*",
            "role": "Estudiantes",
            "cedula": "1713579246",
            "fecha_nacimiento": "2002-10-09"
        },
        {
            "username": "camila",
            "nombre": "Camila Flores",
            "email": "camila.flores@nutria.edu.ec",
            "password": "Password123*",
            "role": "Estudiantes",
            "cedula": "1724680135",
            "fecha_nacimiento": "2003-05-22"
        },
        {
            "username": "nicolas",
            "nombre": "Nicolas Romero",
            "email": "nicolas.romero@nutria.edu.ec",
            "password": "Password123*",
            "role": "Estudiantes",
            "cedula": "1735791246",
            "fecha_nacimiento": "2001-09-17"
        },
        {
            "username": "daniela",
            "nombre": "Daniela Herrera",
            "email": "daniela.herrera@nutria.edu.ec",
            "password": "Password123*",
            "role": "Estudiantes",
            "cedula": "1746802357",
            "fecha_nacimiento": "2002-01-30"
        },
        {
            "username": "santiago",
            "nombre": "Santiago Medina",
            "email": "santiago.medina@nutria.edu.ec",
            "password": "Password123*",
            "role": "Estudiantes",
            "cedula": "1757913468",
            "fecha_nacimiento": "2001-11-12"
        },
        {
            "username": "isabella",
            "nombre": "Isabella Vargas",
            "email": "isabella.vargas@nutria.edu.ec",
            "password": "Password123*",
            "role": "Estudiantes",
            "cedula": "1768024579",
            "fecha_nacimiento": "2003-07-07"
        },
        {
            "username": "alejandro",
            "nombre": "Alejandro Rios",
            "email": "alejandro.rios@nutria.edu.ec",
            "password": "Password123*",
            "role": "Estudiantes",
            "cedula": "1779135680",
            "fecha_nacimiento": "2002-08-24"
        },
        {
            "username": "mariana",
            "nombre": "Mariana Acosta",
            "email": "mariana.acosta@nutria.edu.ec",
            "password": "Password123*",
            "role": "Estudiantes",
            "cedula": "1780246791",
            "fecha_nacimiento": "2003-03-15"
        },
        {
            "username": "sebastian",
            "nombre": "Sebastian Mora",
            "email": "sebastian.mora@nutria.edu.ec",
            "password": "Password123*",
            "role": "Estudiantes",
            "cedula": "1791357802",
            "fecha_nacimiento": "2001-05-04"
        },
        {
            "username": "docente_luisa",
            "nombre": "Dra. Luisa Martinez",
            "email": "luisa.martinez@nutria.edu.ec",
            "password": "Password123*",
            "role": "Docentes",
            "cedula": "1702468135",
            "fecha_nacimiento": "1975-12-19"
        },
        {
            "username": "docente_ricardo",
            "nombre": "Dr. Ricardo Alarcon",
            "email": "ricardo.alarcon@nutria.edu.ec",
            "password": "Password123*",
            "role": "Docentes",
            "cedula": "1713579246",
            "fecha_nacimiento": "1983-09-08"
        },
        {
            "username": "docente_patricia",
            "nombre": "Dra. Patricia Cueva",
            "email": "patricia.cueva@nutria.edu.ec",
            "password": "Password123*",
            "role": "Docentes",
            "cedula": "1724680357",
            "fecha_nacimiento": "1978-04-26"
        },
        {
            "username": "docente_hugo",
            "nombre": "Dr. Hugo Paredes",
            "email": "hugo.paredes@nutria.edu.ec",
            "password": "Password123*",
            "role": "Docentes",
            "cedula": "1735791468",
            "fecha_nacimiento": "1985-02-14"
        },
        {
            "username": "docente_beatriz",
            "nombre": "Dra. Beatriz Sanchez",
            "email": "beatriz.sanchez@nutria.edu.ec",
            "password": "Password123*",
            "role": "Docentes",
            "cedula": "1746802579",
            "fecha_nacimiento": "1981-07-22"
        }
    ]

    for u in usuarios:
        print(f"Procesando usuario '{u['username']}'...")
        hashed = bcrypt.hashpw(u["password"].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        try:
            table.put_item(Item={
                "username": u["username"],
                "nombre": u["nombre"],
                "email": u["email"],
                "password": hashed,
                "role": u["role"],
                "cedula": u["cedula"],
                "fecha_nacimiento": u["fecha_nacimiento"]
            })
            print(f"  -> Usuario '{u['username']}' registrado con rol '{u['role']}'")
        except Exception as ex:
            print(f"  -> Error al insertar '{u['username']}': {ex}")

    print("\nProceso de inicialización completado.")

if __name__ == "__main__":
    seed()
