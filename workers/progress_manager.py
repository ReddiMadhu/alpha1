"""Progress manager for tracking and broadcasting job progress"""
import asyncio
from typing import Optional
from loguru import logger

from src.progress_callback import ProgressCallback, Stage
from storage.job_store import JobStore
from workers.websocket_manager import ws_manager


class DatabaseProgressCallback(ProgressCallback):
    """Progress callback that persists to database and broadcasts via WebSocket"""

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.job_store = JobStore()
        self.current_stage: Optional[Stage] = None
        self.total_items: int = 0
        self.current_items: int = 0
        self.base_percent: int = 0

    def set_stage(self, stage: Stage, total_items: int) -> None:
        """Set current processing stage"""
        self.current_stage = stage
        self.total_items = total_items
        self.current_items = 0
        self.base_percent = self._calculate_base_percent(stage)

        message = f"Starting {stage.stage_name}"

        # Update database
        self.job_store.update_progress(
            self.job_id,
            self.base_percent,
            stage.stage_name,
            message
        )

        # Broadcast via WebSocket (async)
        self._broadcast_progress(self.base_percent, stage.stage_name, message)

        logger.info(f"Job {self.job_id}: {message} ({self.base_percent}%)")

    def increment(self, message: str = "") -> None:
        """Increment progress within current stage"""
        self.current_items += 1
        percent = self._calculate_percent()

        # Update database
        self.job_store.update_progress(
            self.job_id,
            percent,
            self.current_stage.stage_name if self.current_stage else "",
            message
        )

        # Broadcast via WebSocket
        self._broadcast_progress(
            percent,
            self.current_stage.stage_name if self.current_stage else "",
            message
        )

        if message:
            logger.debug(f"Job {self.job_id}: {message} ({percent}%)")

    def update(self, stage: Stage, percent: int, message: str = "") -> None:
        """Direct progress update"""
        # Update database
        self.job_store.update_progress(
            self.job_id,
            percent,
            stage.stage_name,
            message
        )

        # Broadcast via WebSocket
        self._broadcast_progress(percent, stage.stage_name, message)

        if message:
            logger.info(f"Job {self.job_id}: {message} ({percent}%)")

    def _calculate_base_percent(self, stage: Stage) -> int:
        """Calculate base percentage for stage start"""
        total_before = 0
        for s in Stage:
            if s == stage:
                break
            total_before += s.weight
        return total_before

    def _calculate_percent(self) -> int:
        """Calculate current percentage within stage"""
        if self.total_items == 0 or not self.current_stage:
            return self.base_percent

        stage_progress = (self.current_items / self.total_items) * self.current_stage.weight
        return min(100, int(self.base_percent + stage_progress))

    def _broadcast_progress(self, percent: int, stage: str, message: str):
        """Broadcast progress update via WebSocket (sync wrapper for async)"""
        try:
            # Create event loop if not exists
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run async broadcast in loop
            if loop.is_running():
                # If loop is already running, schedule task
                asyncio.create_task(
                    ws_manager.broadcast_progress(
                        self.job_id,
                        percent,
                        stage,
                        message
                    )
                )
            else:
                # Run in current loop
                loop.run_until_complete(
                    ws_manager.broadcast_progress(
                        self.job_id,
                        percent,
                        stage,
                        message
                    )
                )
        except Exception as e:
            logger.error(f"Failed to broadcast progress: {e}")
