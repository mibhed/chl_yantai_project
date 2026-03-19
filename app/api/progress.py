"""
训练进度流（Server-Sent Events）模块。

后端：
    from app.api.progress import progress_queue
    progress_queue.put({"stage": "training", "model": "RF", "pct": 45, "msg": "RF: R2=0.82..."})
    progress_queue.put({"stage": "done", "pct": 100})

前端 EventSource：
    const es = new EventSource('/api/training/stream')
    es.onmessage = e => { const d = JSON.parse(e.data); updateBar(d) }
"""

import queue
import threading
import uuid
from typing import Optional


# 每个 SSE 连接对应一个独立的 FIFO 队列
_active_queues: dict[str, queue.Queue] = {}
_lock = threading.Lock()


def create_stream_id() -> str:
    return uuid.uuid4().hex[:12]


def enqueue(stream_id: str, event: dict):
    with _lock:
        q = _active_queues.get(stream_id)
    if q is not None:
        try:
            q.put_nowait(event)
        except queue.Full:
            pass


def get_queue(stream_id: str) -> queue.Queue:
    with _lock:
        if stream_id not in _active_queues:
            _active_queues[stream_id] = queue.Queue(maxsize=200)
        return _active_queues[stream_id]


def close_stream(stream_id: str):
    with _lock:
        _active_queues.pop(stream_id, None)


def put_progress(stream_id: str, stage: str, pct: int,
                 msg: str = "", model: str = "", detail: str = ""):
    """
    向指定流推送一条进度事件。
    """
    enqueue(stream_id, {
        "stage": stage,
        "pct": min(max(pct, 0), 100),
        "msg": msg,
        "model": model,
        "detail": detail,
    })
