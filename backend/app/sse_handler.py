import asyncio
import json
import logging
from typing import Dict, Set, AsyncGenerator

logger = logging.getLogger("nutria.sse")

_subscribers: Dict[str, Set[asyncio.Queue]] = {}
_lock = asyncio.Lock()


async def subscribe(device_id: str) -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue()
    async with _lock:
        if device_id not in _subscribers:
            _subscribers[device_id] = set()
        _subscribers[device_id].add(queue)
    logger.debug("[SSE] Suscrito a device=%s (total: %d)", device_id, len(_subscribers[device_id]))
    return queue


async def unsubscribe(device_id: str, queue: asyncio.Queue):
    async with _lock:
        if device_id in _subscribers and queue in _subscribers[device_id]:
            _subscribers[device_id].discard(queue)
            if not _subscribers[device_id]:
                del _subscribers[device_id]
            logger.debug("[SSE] Desuscrito de device=%s", device_id)


async def broadcast(device_id: str, data: dict):
    async with _lock:
        queues = _subscribers.get(device_id, set()).copy()
    if not queues:
        return
    payload = json.dumps(data, default=str)
    for queue in queues:
        try:
            queue.put_nowait(payload)
        except asyncio.QueueFull:
            logger.warning("[SSE] Cola llena para device=%s, descartando mensaje", device_id)


async def event_generator(device_id: str) -> AsyncGenerator[str, None]:
    queue = await subscribe(device_id)
    try:
        while True:
            try:
                data = await asyncio.wait_for(queue.get(), timeout=30)
                yield f"event: reading\ndata: {data}\n\n"
            except asyncio.TimeoutError:
                yield f"event: ping\ndata: {{{{}}}}\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        await unsubscribe(device_id, queue)
