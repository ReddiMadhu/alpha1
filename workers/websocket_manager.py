"""WebSocket manager for broadcasting progress updates"""
from typing import Dict, Set
from fastapi import WebSocket
from loguru import logger
import json
from datetime import datetime


class WebSocketManager:
    """Manages WebSocket connections for real-time progress updates"""

    def __init__(self):
        # job_id -> set of connected websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()

        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()

        self.active_connections[job_id].add(websocket)
        logger.info(f"WebSocket connected for job {job_id}. Total connections: {len(self.active_connections[job_id])}")

    def disconnect(self, websocket: WebSocket, job_id: str):
        """Remove a WebSocket connection"""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)

            # Clean up empty connection sets
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

            logger.info(f"WebSocket disconnected for job {job_id}")

    async def send_message(self, websocket: WebSocket, message: dict):
        """Send message to a specific WebSocket"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")

    async def broadcast_to_job(self, job_id: str, message: dict):
        """Broadcast message to all connections for a specific job"""
        if job_id not in self.active_connections:
            return

        # Add timestamp
        message["timestamp"] = datetime.utcnow().isoformat()

        # Send to all connected clients
        disconnected = set()
        for websocket in self.active_connections[job_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to WebSocket: {e}")
                disconnected.add(websocket)

        # Clean up disconnected websockets
        for websocket in disconnected:
            self.disconnect(websocket, job_id)

    async def broadcast_progress(
        self,
        job_id: str,
        progress_percent: int,
        current_stage: str,
        message: str = ""
    ):
        """Broadcast progress update"""
        await self.broadcast_to_job(
            job_id,
            {
                "type": "progress",
                "job_id": job_id,
                "data": {
                    "progress_percent": progress_percent,
                    "current_stage": current_stage,
                    "message": message
                }
            }
        )

    async def broadcast_completion(self, job_id: str, relationship_count: int = 0):
        """Broadcast job completion"""
        await self.broadcast_to_job(
            job_id,
            {
                "type": "completed",
                "job_id": job_id,
                "data": {
                    "status": "completed",
                    "relationship_count": relationship_count,
                    "message": "Analysis completed successfully"
                }
            }
        )

    async def broadcast_error(self, job_id: str, error_message: str):
        """Broadcast job error"""
        await self.broadcast_to_job(
            job_id,
            {
                "type": "error",
                "job_id": job_id,
                "data": {
                    "status": "failed",
                    "error": error_message
                }
            }
        )

    def get_connection_count(self, job_id: str) -> int:
        """Get number of active connections for a job"""
        return len(self.active_connections.get(job_id, set()))


# Global WebSocket manager instance
ws_manager = WebSocketManager()
