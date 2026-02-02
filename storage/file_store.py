"""File storage management for uploaded Excel files"""
import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from loguru import logger

from storage.database import get_db_connection
from api.models.job_models import UploadedFile
from api.config import config


class FileStore:
    """Manages uploaded file storage"""

    def __init__(self):
        # Ensure upload directory exists
        Path(config.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    def save_uploaded_file(
        self,
        job_id: str,
        original_filename: str,
        file_content: bytes
    ) -> UploadedFile:
        """
        Save an uploaded file

        Args:
            job_id: Job identifier
            original_filename: Original file name
            file_content: File content as bytes

        Returns:
            UploadedFile object
        """
        # Generate unique file ID and stored filename
        file_id = f"file_{uuid.uuid4().hex[:12]}"
        file_extension = Path(original_filename).suffix
        stored_filename = f"{file_id}_{original_filename}"

        # Create job-specific directory
        job_dir = Path(config.UPLOAD_DIR) / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = job_dir / stored_filename
        with open(file_path, 'wb') as f:
            f.write(file_content)

        file_size = len(file_content)

        # Store metadata in database
        uploaded_file = UploadedFile(
            file_id=file_id,
            job_id=job_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=str(file_path),
            file_size=file_size
        )

        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO uploaded_files
                (file_id, job_id, original_filename, stored_filename, file_path, file_size)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    uploaded_file.file_id,
                    uploaded_file.job_id,
                    uploaded_file.original_filename,
                    uploaded_file.stored_filename,
                    uploaded_file.file_path,
                    uploaded_file.file_size
                )
            )

        logger.info(f"Saved file {original_filename} for job {job_id} ({file_size} bytes)")
        return uploaded_file

    def get_job_files(self, job_id: str) -> List[UploadedFile]:
        """
        Get all files for a job

        Args:
            job_id: Job identifier

        Returns:
            List of UploadedFile objects
        """
        with get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT file_id, job_id, original_filename, stored_filename,
                       file_path, file_size, uploaded_at
                FROM uploaded_files
                WHERE job_id = ?
                ORDER BY uploaded_at
                """,
                (job_id,)
            ).fetchall()

        return [UploadedFile.from_db_row(tuple(row)) for row in rows]

    def get_job_file_paths(self, job_id: str) -> List[str]:
        """
        Get all file paths for a job

        Args:
            job_id: Job identifier

        Returns:
            List of file paths
        """
        files = self.get_job_files(job_id)
        return [f.file_path for f in files]

    def delete_job_files(self, job_id: str) -> int:
        """
        Delete all files for a job

        Args:
            job_id: Job identifier

        Returns:
            Number of files deleted
        """
        # Get all files for the job
        files = self.get_job_files(job_id)
        deleted_count = 0

        # Delete physical files
        for file in files:
            try:
                if os.path.exists(file.file_path):
                    os.remove(file.file_path)
                    deleted_count += 1
                    logger.debug(f"Deleted file {file.file_path}")
            except Exception as e:
                logger.error(f"Failed to delete file {file.file_path}: {e}")

        # Delete job directory if empty
        job_dir = Path(config.UPLOAD_DIR) / job_id
        if job_dir.exists():
            try:
                # Remove directory if empty or force remove
                if not any(job_dir.iterdir()):
                    job_dir.rmdir()
                else:
                    shutil.rmtree(job_dir)
                logger.debug(f"Deleted job directory {job_dir}")
            except Exception as e:
                logger.error(f"Failed to delete job directory {job_dir}: {e}")

        # Delete from database (cascade will handle this)
        with get_db_connection() as conn:
            conn.execute(
                "DELETE FROM uploaded_files WHERE job_id = ?",
                (job_id,)
            )

        logger.info(f"Deleted {deleted_count} files for job {job_id}")
        return deleted_count

    def validate_file(
        self,
        filename: str,
        file_size: int
    ) -> tuple[bool, Optional[str]]:
        """
        Validate uploaded file

        Args:
            filename: File name
            file_size: File size in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file extension
        file_extension = Path(filename).suffix.lower()
        if file_extension not in config.ALLOWED_EXTENSIONS:
            return False, f"Invalid file extension. Allowed: {', '.join(config.ALLOWED_EXTENSIONS)}"

        # Check file size
        max_size = config.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes
        if file_size > max_size:
            return False, f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds maximum ({config.MAX_FILE_SIZE_MB}MB)"

        return True, None


# Global file store instance
file_store = FileStore()
