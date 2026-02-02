"""WebSocket endpoints for real-time progress updates"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from workers.websocket_manager import ws_manager
from storage.job_store import JobStore

router = APIRouter()
job_store = JobStore()


@router.websocket("/jobs/{job_id}/ws")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time job progress updates

    Connect to this endpoint to receive real-time updates about job progress.

    Message format:
    {
        "type": "progress" | "completed" | "error",
        "job_id": "job_abc123",
        "data": {...},
        "timestamp": "2024-01-29T10:30:00Z"
    }
    """
    # Check if job exists
    job = job_store.get_job(job_id)
    if not job:
        await websocket.close(code=4004, reason="Job not found")
        return

    # Connect WebSocket
    await ws_manager.connect(websocket, job_id)

    try:
        # Send initial status
        await websocket.send_json({
            "type": "connected",
            "job_id": job_id,
            "data": {
                "status": job.status.value,
                "progress_percent": job.progress_percent,
                "current_stage": job.current_stage
            }
        })

        # Keep connection alive and handle client messages
        while True:
            try:
                # Receive messages from client (for potential heartbeat/ping)
                data = await websocket.receive_json()

                # Handle ping/pong for keepalive
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected normally for job {job_id}")
                break
            except Exception as e:
                logger.error(f"WebSocket error for job {job_id}: {e}")
                break

    finally:
        # Clean up connection
        ws_manager.disconnect(websocket, job_id)
