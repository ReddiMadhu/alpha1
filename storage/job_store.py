"""Job persistence and state management"""
from datetime import datetime
from typing import Optional, List
from loguru import logger

from storage.database import get_db_connection
from api.models.job_models import Job
from api.models.api_models import JobStatus


class JobStore:
    """Manages job persistence in SQLite database"""

    def create_job(self, job_id: str, file_count: int) -> Job:
        """
        Create a new job

        Args:
            job_id: Unique job identifier
            file_count: Number of files in job

        Returns:
            Created Job object
        """
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO jobs (job_id, status, file_count, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (job_id, JobStatus.PENDING.value, file_count, datetime.utcnow())
            )

        logger.info(f"Created job {job_id} with {file_count} files")
        return self.get_job(job_id)

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID

        Args:
            job_id: Job identifier

        Returns:
            Job object or None if not found
        """
        with get_db_connection() as conn:
            row = conn.execute(
                """
                SELECT job_id, status, created_at, started_at, completed_at,
                       progress_percent, current_stage, error_message,
                       file_count, relationship_count, result_file_path
                FROM jobs
                WHERE job_id = ?
                """,
                (job_id,)
            ).fetchone()

        if row:
            return Job.from_db_row(tuple(row))
        return None

    def list_jobs(
        self,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None
    ) -> tuple[List[Job], int]:
        """
        List jobs with pagination

        Args:
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            status: Filter by status (optional)

        Returns:
            Tuple of (jobs list, total count)
        """
        with get_db_connection() as conn:
            # Build query with optional status filter
            where_clause = "WHERE status = ?" if status else ""
            params = [status] if status else []

            # Get total count
            count_query = f"SELECT COUNT(*) FROM jobs {where_clause}"
            total = conn.execute(count_query, params).fetchone()[0]

            # Get paginated jobs
            query = f"""
                SELECT job_id, status, created_at, started_at, completed_at,
                       progress_percent, current_stage, error_message,
                       file_count, relationship_count, result_file_path
                FROM jobs
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            rows = conn.execute(query, params).fetchall()
            jobs = [Job.from_db_row(tuple(row)) for row in rows]

        return jobs, total

    def update_status(
        self,
        job_id: str,
        status: JobStatus,
        error: Optional[str] = None,
        relationship_count: Optional[int] = None,
        result_file_path: Optional[str] = None
    ):
        """
        Update job status

        Args:
            job_id: Job identifier
            status: New status
            error: Error message if failed
            relationship_count: Number of relationships found
            result_file_path: Path to result file
        """
        with get_db_connection() as conn:
            # Update job status
            update_fields = ["status = ?"]
            params = [status.value]

            if error is not None:
                update_fields.append("error_message = ?")
                params.append(error)

            if relationship_count is not None:
                update_fields.append("relationship_count = ?")
                params.append(relationship_count)

            if result_file_path is not None:
                update_fields.append("result_file_path = ?")
                params.append(result_file_path)

            # Set timestamps based on status
            if status == JobStatus.RUNNING:
                update_fields.append("started_at = ?")
                params.append(datetime.utcnow())
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                update_fields.append("completed_at = ?")
                params.append(datetime.utcnow())

            params.append(job_id)

            query = f"""
                UPDATE jobs
                SET {', '.join(update_fields)}
                WHERE job_id = ?
            """

            conn.execute(query, params)

        logger.info(f"Updated job {job_id} status to {status.value}")

    def update_progress(
        self,
        job_id: str,
        percent: int,
        stage: str,
        message: Optional[str] = None
    ):
        """
        Update job progress

        Args:
            job_id: Job identifier
            percent: Progress percentage (0-100)
            stage: Current stage name
            message: Optional progress message
        """
        with get_db_connection() as conn:
            # Update job progress
            conn.execute(
                """
                UPDATE jobs
                SET progress_percent = ?,
                    current_stage = ?
                WHERE job_id = ?
                """,
                (percent, stage, job_id)
            )

            # Insert progress log
            if message:
                conn.execute(
                    """
                    INSERT INTO job_progress (job_id, stage, message, percent)
                    VALUES (?, ?, ?, ?)
                    """,
                    (job_id, stage, message, percent)
                )

    def get_recent_progress_logs(
        self,
        job_id: str,
        limit: int = 10
    ) -> List[dict]:
        """
        Get recent progress logs for a job

        Args:
            job_id: Job identifier
            limit: Maximum number of logs to return

        Returns:
            List of progress log dictionaries
        """
        with get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT timestamp, stage, message, percent
                FROM job_progress
                WHERE job_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (job_id, limit)
            ).fetchall()

        return [
            {
                "timestamp": row[0],
                "stage": row[1],
                "message": row[2],
                "percent": row[3]
            }
            for row in rows
        ]

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job and all related data

        Args:
            job_id: Job identifier

        Returns:
            True if deleted, False if not found
        """
        with get_db_connection() as conn:
            # Foreign key cascade will delete related records
            cursor = conn.execute(
                "DELETE FROM jobs WHERE job_id = ?",
                (job_id,)
            )
            deleted = cursor.rowcount > 0

        if deleted:
            logger.info(f"Deleted job {job_id}")

        return deleted

    def job_exists(self, job_id: str) -> bool:
        """
        Check if job exists

        Args:
            job_id: Job identifier

        Returns:
            True if job exists
        """
        with get_db_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE job_id = ?",
                (job_id,)
            ).fetchone()[0]

        return count > 0
