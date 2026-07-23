import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse

from app.database import get_dynamodb_resource, convert_decimals
from app.auth import get_current_user, require_role
from app.session_analysis import group_sessions, analyze_session
from app.sse_handler import event_generator

logger = logging.getLogger("nutria.sessions")
router = APIRouter(tags=["sessions"])


@router.get("/devices/{device_id}/sessions")
def list_sessions(
    device_id: str,
    limit: int = Query(default=200, le=1000),
    user: dict = Depends(get_current_user),
):
    db = get_dynamodb_resource()
    heart_table = db.Table("heart_rate_readings")

    response = heart_table.query(
        KeyConditionExpression="device_id = :did",
        ExpressionAttributeValues={":did": device_id},
        ScanIndexForward=False,
        Limit=limit,
    )
    items = response.get("Items", [])
    items = [convert_decimals(item) for item in items]

    raw_groups = group_sessions(items)

    sessions = []
    for group in reversed(raw_groups):
        analysis = analyze_session(group)
        if analysis:
            analysis["device_id"] = device_id
            sessions.append(analysis)

    return {
        "device_id": device_id,
        "sessions": sessions,
        "total_sessions": len(sessions),
    }


@router.get("/devices/{device_id}/sessions/current")
def current_session(
    device_id: str,
    user: dict = Depends(get_current_user),
):
    db = get_dynamodb_resource()
    heart_table = db.Table("heart_rate_readings")

    response = heart_table.query(
        KeyConditionExpression="device_id = :did",
        ExpressionAttributeValues={":did": device_id},
        ScanIndexForward=False,
        Limit=100,
    )
    items = response.get("Items", [])
    items = [convert_decimals(item) for item in items]

    raw_groups = group_sessions(items)
    if not raw_groups:
        return {"device_id": device_id, "session": None, "latest_reading": None}

    latest_group = raw_groups[-1]
    analysis = analyze_session(latest_group)
    analysis["device_id"] = device_id

    latest = items[0] if items else None
    analysis["latest_reading"] = {
        "bpm": latest["bpm"],
        "timestamp": latest["timestamp"],
        "reading_id": latest.get("reading_id", ""),
    } if latest else None

    return {
        "device_id": device_id,
        "session": analysis,
    }


@router.get("/devices/readings/stream")
async def stream_readings(
    device_id: str = Query(..., description="ID del dispositivo a monitorear"),
    user: dict = Depends(get_current_user),
):
    return StreamingResponse(
        event_generator(device_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
