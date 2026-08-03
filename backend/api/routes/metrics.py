"""Metrics endpoint for monitoring."""

import time
from collections import defaultdict
from threading import Lock

from fastapi import APIRouter

router = APIRouter(prefix="/metrics", tags=["metrics"])

_metrics_lock = Lock()
_metrics: dict[str, int] = defaultdict(int)
_start_time = time.time()


def track_metric(metric_name: str) -> None:
    """Increment a metric counter."""
    with _metrics_lock:
        _metrics[metric_name] += 1


@router.get("")
async def get_metrics() -> dict:
    """Get application metrics."""
    with _metrics_lock:
        metrics = dict(_metrics)

    uptime_seconds = time.time() - _start_time

    return {
        "uptime_seconds": round(uptime_seconds, 2),
        "uptime_human": _format_uptime(uptime_seconds),
        "metrics": metrics,
    }


@router.post("/{metric_name}")
async def increment_metric(metric_name: str) -> dict:
    """Increment a custom metric."""
    track_metric(metric_name)
    return {"success": True, "metric": metric_name}


def _format_uptime(seconds: float) -> str:
    """Format uptime as human readable string."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")

    return " ".join(parts)
