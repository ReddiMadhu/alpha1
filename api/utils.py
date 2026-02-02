"""Utility functions for the API"""
import uuid
from datetime import datetime


def generate_job_id() -> str:
    """
    Generate a unique job ID

    Returns:
        Unique job identifier in format: job_{timestamp}_{uuid}
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    return f"job_{timestamp}_{unique_id}"


def generate_file_id() -> str:
    """
    Generate a unique file ID

    Returns:
        Unique file identifier
    """
    return f"file_{uuid.uuid4().hex[:12]}"
