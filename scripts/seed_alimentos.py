#!/usr/bin/env python3
"""
Script de migración/seed para cargar la base de datos de alimentos (RF9, RF12, RNF14, RES2).
Lee el JSON generado por extract_alimentos.py y carga la colección alimentos en DynamoDB.

Ejecución:
    python -m scripts.seed_alimentos

Requisitos: Los alimentos fueron extraídos del PDF "Tabla de composición de los alimentos SF"
de la Universidad San Francisco de Quito (USFQ), Diciembre 2021.
"""
import json
import os
import sys
import boto3
from decimal import Decimal
from botocore.exceptions import ClientError

# Agregar el directorio padre al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import get_dynamodb_resource

JSON_PATH = os.path.join(os.path.dirname(__file__), "alimentos_usfq.json")
TABLE_NAME = "alimentos"


def load_json_alimentos():
    """Carga el archivo JSON de alimentos."""
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def convert_to_decimal(obj):
    """Convierte floats a Decimal para DynamoDB."""
    if isinstance(obj, list):
        return [convert_to_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(round(obj, 4)))
    return obj


def seed_alimentos():
    """Carga los alimentos en DynamoDB."""
    alimentos = load_json_alimentos()
    print(f"Total de alimentos en JSON: {len(alimentos)}")

    db = get_dynamodb_resource()
    
    # Verificar/crear tabla
    try:
        table = db.Table(TABLE_NAME)
        table.load()
        print(f"Tabla '{TABLE_NAME}' existe.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"Creando tabla '{TABLE_NAME}'...")
            table = db.create_table(
                TableName=TABLE_NAME,
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
            print(f"Tabla '{TABLE_NAME}' creada.")
        else:
            raise

    # Cargar alimentos
    exitosos = 0
    errores = 0
    with table.batch_writer() as batch:
        for alimento in alimentos:
            item = convert_to_decimal(alimento)
            try:
                batch.put_item(Item=item)
                exitosos += 1
            except Exception as e:
                print(f"Error cargando {alimento.get('id')}: {e}")
                errores += 1

    print(f"\nResultado:")
    print(f"  Alimentos cargados exitosamente: {exitosos}")
    print(f"  Errores: {errores}")

    # Verificar carga
    try:
        response = table.scan(Select='COUNT')
        total_db = response.get('Count', 0)
        print(f"  Total en DynamoDB: {total_db}")
    except Exception:
        pass


if __name__ == "__main__":
    seed_alimentos()
