import os
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch

import boto3
import pytest
from fastapi.testclient import TestClient

os.environ.pop("DYNAMODB_ENDPOINT_URL", None)
os.environ["COGNITO_USER_POOL_ID"] = "mock_pool_id"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["JWT_SECRET"] = "test-secret-key-for-unit-tests"
os.environ["SKIP_AUTO_SEED"] = "1"
os.environ["MQTT_HOST"] = "localhost"

from app.main import app


class FakeDynamoTable:
    def __init__(self):
        self._items: Dict[str, Dict[str, Any]] = {}

    def put_item(self, Item: dict, **kwargs):
        key = self._extract_key(Item)
        self._items[key] = Item

    def get_item(self, Key: dict, **kwargs):
        key = self._extract_dict_key(Key)
        item = self._items.get(key)
        return {"Item": item} if item is not None else {}

    def update_item(self, Key: dict, UpdateExpression: str = "",
                    ExpressionAttributeValues: dict = None,
                    ExpressionAttributeNames: dict = None, **kwargs):
        key = self._extract_dict_key(Key)
        if key in self._items and ExpressionAttributeValues:
            item = self._items[key]
            expr = UpdateExpression.replace("SET ", "").replace("set ", "")
            parts = expr.split(",")
            for part in parts:
                part = part.strip()
                if " = " in part:
                    field_expr, value_alias = part.split(" = ")
                    field_expr = field_expr.strip()
                    value_alias = value_alias.strip()
                    if ExpressionAttributeNames:
                        for name_alias, name in ExpressionAttributeNames.items():
                            field_expr = field_expr.replace(name_alias, name)
                    if value_alias in ExpressionAttributeValues:
                        item[field_expr] = ExpressionAttributeValues[value_alias]

    def delete_item(self, Key: dict, **kwargs):
        key = self._extract_dict_key(Key)
        self._items.pop(key, None)

    def scan(self, FilterExpression=None, ExpressionAttributeValues=None, **kwargs):
        items = list(self._items.values())
        if FilterExpression is not None and ExpressionAttributeValues:
            filter_val = list(ExpressionAttributeValues.values())[0]
            expr = FilterExpression
            if expr:
                parts = expr.split("=")
                if len(parts) >= 1:
                    field_name = parts[0].strip()
                    filtered = []
                    for item in items:
                        v = item.get(field_name)
                        if v is not None and str(v) == str(filter_val):
                            filtered.append(item)
                    items = filtered
        return {"Items": items}

    def query(self, KeyConditionExpression: str = "",
              ExpressionAttributeValues: dict = None,
              ScanIndexForward: bool = True,
              Limit: int = 100, IndexName: str = None, **kwargs):
        items = list(self._items.values())
        if IndexName == 'categoria-index' and ExpressionAttributeValues:
            cat_val = list(ExpressionAttributeValues.values())[0]
            items = [i for i in items if i.get("categoria") == cat_val]
        elif ExpressionAttributeValues:
            vals = list(ExpressionAttributeValues.values())
            if len(vals) >= 1:
                items = [i for i in items if vals[0] in str(i.get("device_id", "")) or vals[0] in str(i.get("student_id", ""))]
        items = items[:Limit]
        return {"Items": items}

    def load(self):
        pass

    def _extract_key(self, item: dict) -> str:
        for key_attr in ["sugerencia_id", "plan_id", "task_id", "username", "device_id",
                         "calculation_id", "student_id", "code", "id"]:
            if key_attr in item:
                return str(item[key_attr])
        return str(id(item))

    def _extract_dict_key(self, key_dict: dict) -> str:
        for val in key_dict.values():
            return str(val)
        return ""


_fake_tables: Dict[str, FakeDynamoTable] = {}


def _get_fake_table(name: str) -> FakeDynamoTable:
    if name not in _fake_tables:
        _fake_tables[name] = FakeDynamoTable()
    return _fake_tables[name]


class MockDynamoDBResource:
    def Table(self, name: str):
        table = _get_fake_table(name)
        mock_table = MagicMock()
        mock_table.put_item.side_effect = table.put_item
        mock_table.get_item.side_effect = table.get_item
        mock_table.update_item.side_effect = table.update_item
        mock_table.delete_item.side_effect = table.delete_item
        mock_table.scan.side_effect = table.scan
        mock_table.query.side_effect = table.query
        mock_table.load.side_effect = table.load
        return mock_table


_original_boto3_resource = boto3.resource


def _mock_boto3_resource(service: str, **kwargs):
    if service == "dynamodb":
        return MockDynamoDBResource()
    return _original_boto3_resource(service, **kwargs)


@pytest.fixture(scope="function", autouse=True)
def mock_dynamodb():
    _fake_tables.clear()
    patcher = patch("boto3.resource", _mock_boto3_resource)
    patcher.start()

    patcher_mqtt_start = patch("app.mqtt_handler.start_mqtt_client")
    patcher_mqtt_start.start()
    patcher_mqtt_stop = patch("app.mqtt_handler.stop_mqtt_client")
    patcher_mqtt_stop.start()
    patcher_mqtt_sync = patch("app.mqtt_handler.sync_all_devices_to_mosquitto")
    patcher_mqtt_sync.start()
    patcher_sync_device = patch("app.mqtt_handler.sync_device_to_mosquitto")
    patcher_sync_device.start()
    patcher_sync_device_routes = patch("app.routes.devices.sync_device_to_mosquitto")
    patcher_sync_device_routes.start()

    yield
    patcher_sync_device_routes.stop()
    patcher_sync_device.stop()
    patcher_mqtt_sync.stop()
    patcher_mqtt_stop.stop()
    patcher_mqtt_start.stop()
    patcher.stop()


@pytest.fixture
def client() -> Generator:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def teacher_token() -> str:
    return "mock-teacher-token"


@pytest.fixture
def student_token() -> str:
    return "mock-student-token"


@pytest.fixture
def auth_header_teacher(teacher_token: str) -> dict:
    return {"Authorization": f"Bearer {teacher_token}"}


@pytest.fixture
def auth_header_student(student_token: str) -> dict:
    return {"Authorization": f"Bearer {student_token}"}
