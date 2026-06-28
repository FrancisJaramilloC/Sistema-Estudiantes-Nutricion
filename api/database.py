from decimal import Decimal
import boto3
from botocore.exceptions import ClientError
import config

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
    table_name = config.TASKS_TABLE
    try:
        table = db.Table(table_name)
        table.load()  # triggers exception if table does not exist
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            # Create the table
            table = db.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'task_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'task_id',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            table.wait_until_exists()
            return table
        else:
            raise e

def get_or_create_auditoria_table():
    db = get_dynamodb_resource()
    table_name = config.AUDITORIA_TABLE
    try:
        table = db.Table(table_name)
        table.load()  # triggers exception if table does not exist
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            # Create the table
            table = db.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'calculation_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'calculation_id',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            table.wait_until_exists()
            return table
        else:
            raise e

def get_or_create_users_table():
    db = get_dynamodb_resource()
    table_name = config.USERS_TABLE
    try:
        table = db.Table(table_name)
        table.load()  # triggers exception if table does not exist
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            # Create the table
            table = db.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'username',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'username',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            table.wait_until_exists()
            return table
        else:
            raise e

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
