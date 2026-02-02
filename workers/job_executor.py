"""Background job executor for relationship discovery"""
import threading
from typing import List
from loguru import logger

from src.main import RelationshipDiscovery
from storage.job_store import JobStore
from storage.result_store import ResultStore
from workers.progress_manager import DatabaseProgressCallback
from workers.websocket_manager import ws_manager
from api.models.api_models import JobStatus
import asyncio


# Thread pool for background jobs
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=3)


def execute_discovery_job(job_id: str, file_paths: List[str]):
    """
    Execute discovery job in background thread

    Args:
        job_id: Job identifier
        file_paths: List of file paths to analyze
    """
    job_store = JobStore()
    result_store = ResultStore()

    try:
        logger.info(f"Starting job {job_id} with {len(file_paths)} files")

        # Update status to running
        job_store.update_status(job_id, JobStatus.RUNNING)

        # Create progress callback
        progress_callback = DatabaseProgressCallback(job_id)

        # Create discovery instance
        discovery = RelationshipDiscovery()

        # Run discovery with progress tracking
        result = discovery.discover_relationships(
            file_paths=file_paths,
            output_file=None,  # We'll save it ourselves
            progress_callback=progress_callback
        )

        # Save result
        result_file_path = result_store.save_result(job_id, result)

        # Get relationship count
        relationship_count = len(result.get("relationships", []))

        # Update job status to completed
        job_store.update_status(
            job_id,
            JobStatus.COMPLETED,
            relationship_count=relationship_count,
            result_file_path=result_file_path
        )

        # Broadcast completion
        _broadcast_completion(job_id, relationship_count)

        logger.info(f"Job {job_id} completed successfully. Found {relationship_count} relationships")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)

        # Update job status to failed
        job_store.update_status(
            job_id,
            JobStatus.FAILED,
            error=str(e)
        )

        # Broadcast error
        _broadcast_error(job_id, str(e))


def _broadcast_completion(job_id: str, relationship_count: int):
    """Broadcast job completion via WebSocket"""
    try:
        # Create event loop if not exists
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run async broadcast
        if not loop.is_running():
            loop.run_until_complete(
                ws_manager.broadcast_completion(job_id, relationship_count)
            )
        else:
            asyncio.create_task(
                ws_manager.broadcast_completion(job_id, relationship_count)
            )
    except Exception as e:
        logger.error(f"Failed to broadcast completion: {e}")


def _broadcast_error(job_id: str, error_message: str):
    """Broadcast job error via WebSocket"""
    try:
        # Create event loop if not exists
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run async broadcast
        if not loop.is_running():
            loop.run_until_complete(
                ws_manager.broadcast_error(job_id, error_message)
            )
        else:
            asyncio.create_task(
                ws_manager.broadcast_error(job_id, error_message)
            )
    except Exception as e:
        logger.error(f"Failed to broadcast error: {e}")
