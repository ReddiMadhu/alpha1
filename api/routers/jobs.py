"""Job management API endpoints"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from typing import List, Optional
from loguru import logger

from api.models.api_models import (
    JobCreateResponse,
    JobStatusResponse,
    JobResultResponse,
    JobListResponse,
    JobListItem,
    JobDeleteResponse,
    JobStatus,
    ErrorResponse
)
from api.utils import generate_job_id
from api.config import config
from storage.job_store import JobStore
from storage.file_store import FileStore
from storage.result_store import ResultStore

# Import job executor (will create next)
from workers.job_executor import execute_discovery_job

router = APIRouter()

# Initialize stores
job_store = JobStore()
file_store = FileStore()
result_store = ResultStore()


@router.post("/", response_model=JobCreateResponse, status_code=201)
async def create_job(
    files: List[UploadFile] = File(..., description="Excel files to analyze (1-5 files)"),
    background_tasks: BackgroundTasks = None
):
    """
    Create a new relationship discovery job

    Upload 1-5 Excel files for analysis. The job will be processed in the background.
    Use the returned job_id to check status and retrieve results.
    """
    try:
        # Validate file count
        if len(files) < 1:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INVALID_FILE_COUNT",
                        "message": "At least 1 file is required",
                        "details": {"min_files": 1}
                    }
                }
            )

        if len(files) > config.MAX_FILES_PER_JOB:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "TOO_MANY_FILES",
                        "message": f"Maximum {config.MAX_FILES_PER_JOB} files allowed",
                        "details": {
                            "max_files": config.MAX_FILES_PER_JOB,
                            "provided": len(files)
                        }
                    }
                }
            )

        # Generate job ID
        job_id = generate_job_id()

        # Validate and save files
        file_paths = []
        for file in files:
            # Read file content
            content = await file.read()
            file_size = len(content)

            # Validate file
            is_valid, error_msg = file_store.validate_file(file.filename, file_size)
            if not is_valid:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": {
                            "code": "INVALID_FILE",
                            "message": error_msg,
                            "details": {"filename": file.filename}
                        }
                    }
                )

            # Save file
            uploaded_file = file_store.save_uploaded_file(
                job_id=job_id,
                original_filename=file.filename,
                file_content=content
            )
            file_paths.append(uploaded_file.file_path)

        # Create job in database
        job = job_store.create_job(job_id=job_id, file_count=len(files))

        # Schedule background job
        background_tasks.add_task(
            execute_discovery_job,
            job_id=job_id,
            file_paths=file_paths
        )

        logger.info(f"Created job {job_id} with {len(files)} files")

        return JobCreateResponse(
            job_id=job.job_id,
            status=job.status,
            created_at=job.created_at,
            file_count=job.file_count,
            message="Job created successfully and processing started"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create job: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "JOB_CREATION_FAILED",
                    "message": "Failed to create job",
                    "details": str(e)
                }
            }
        )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get job status and progress

    Returns current status, progress percentage, and processing stage.
    """
    job = job_store.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "JOB_NOT_FOUND",
                    "message": f"Job {job_id} not found",
                    "details": {"job_id": job_id}
                }
            }
        )

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress_percent=job.progress_percent,
        current_stage=job.current_stage,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        file_count=job.file_count,
        relationships_found=job.relationship_count,
        error=job.error_message
    )


@router.get("/{job_id}/result", response_model=JobResultResponse)
async def get_job_result(job_id: str):
    """
    Get job analysis results

    Returns the full JSON report if the job is completed.
    Returns 202 Accepted if the job is still running.
    """
    job = job_store.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "JOB_NOT_FOUND",
                    "message": f"Job {job_id} not found",
                    "details": {"job_id": job_id}
                }
            }
        )

    # If job is still running, return 202 Accepted
    if job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
        return JSONResponse(
            status_code=202,
            content={
                "job_id": job.job_id,
                "status": job.status.value,
                "progress_percent": job.progress_percent,
                "message": "Job is still processing"
            }
        )

    # If job failed, return error
    if job.status == JobStatus.FAILED:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "JOB_FAILED",
                    "message": "Job execution failed",
                    "details": {
                        "job_id": job_id,
                        "error": job.error_message
                    }
                }
            }
        )

    # Job completed - return result
    result = result_store.get_result(job_id)

    if not result:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "RESULT_NOT_FOUND",
                    "message": "Job completed but result not found",
                    "details": {"job_id": job_id}
                }
            }
        )

    return JobResultResponse(
        job_id=job.job_id,
        status=job.status,
        result=result,
        completed_at=job.completed_at,
        message=None
    )


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    limit: int = Query(20, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """
    List all jobs with pagination

    Returns paginated list of jobs, optionally filtered by status.
    """
    try:
        jobs, total = job_store.list_jobs(limit=limit, offset=offset, status=status)

        job_items = [
            JobListItem(
                job_id=job.job_id,
                status=job.status,
                created_at=job.created_at,
                completed_at=job.completed_at,
                file_count=job.file_count,
                relationships_found=job.relationship_count,
                progress_percent=job.progress_percent
            )
            for job in jobs
        ]

        return JobListResponse(
            total=total,
            limit=limit,
            offset=offset,
            jobs=job_items
        )

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "LIST_JOBS_FAILED",
                    "message": "Failed to list jobs",
                    "details": str(e)
                }
            }
        )


@router.delete("/{job_id}", response_model=JobDeleteResponse)
async def delete_job(job_id: str):
    """
    Delete a job and all associated files

    Cancels the job if it's running and deletes all uploaded files and results.
    """
    job = job_store.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "JOB_NOT_FOUND",
                    "message": f"Job {job_id} not found",
                    "details": {"job_id": job_id}
                }
            }
        )

    try:
        # Delete files
        files_deleted = 0
        if config.DELETE_FILES_ON_JOB_DELETE:
            files_deleted = file_store.delete_job_files(job_id)
            result_store.delete_result(job_id)

        # Delete job from database
        job_store.delete_job(job_id)

        logger.info(f"Deleted job {job_id}")

        return JobDeleteResponse(
            message=f"Job {job_id} deleted successfully",
            job_id=job_id,
            files_deleted=files_deleted
        )

    except Exception as e:
        logger.error(f"Failed to delete job {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "DELETE_FAILED",
                    "message": "Failed to delete job",
                    "details": str(e)
                }
            }
        )


# Import JSONResponse for 202 status
from fastapi.responses import JSONResponse
