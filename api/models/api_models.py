"""Pydantic models for API requests and responses"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ==================== Preview Models ====================

class ColumnPreview(BaseModel):
    """Preview metadata for a single column"""
    name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="Inferred data type")
    null_count: int = Field(..., description="Number of null values")
    unique_count: int = Field(..., description="Number of unique values")
    sample_values: List[Any] = Field(..., description="Sample values (first 5)")


class DuplicateGroupInfo(BaseModel):
    """Information about a duplicate column group"""
    group_id: str = Field(..., description="Unique group identifier")
    detection_type: str = Field(..., description="Detection algorithm used")
    similarity_score: float = Field(..., description="Similarity score (0-100)")
    columns: List[str] = Field(..., description="List of duplicate column names")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    recommendation: str = Field(..., description="Recommended action")


class FilePreview(BaseModel):
    """Preview metadata for a single file"""
    file_id: str = Field(..., description="File identifier")
    original_filename: str = Field(..., description="Original file name")
    row_count: int = Field(..., description="Number of rows")
    column_count: int = Field(..., description="Number of columns")
    columns: List[ColumnPreview] = Field(..., description="Column previews")
    duplicate_groups: List[DuplicateGroupInfo] = Field(default_factory=list, description="Detected duplicate groups")


class JobPreviewResponse(BaseModel):
    """Response for preview creation"""
    preview_id: str = Field(..., description="Unique preview identifier")
    status: str = Field(..., description="Preview status")
    created_at: datetime = Field(..., description="Creation timestamp")
    file_count: int = Field(..., description="Number of files")
    files: List[FilePreview] = Field(..., description="File previews")
    total_duplicates_detected: int = Field(..., description="Total duplicate groups across all files")
    message: str = Field(..., description="Response message")


class FileColumnSelection(BaseModel):
    """User's column selection for a single file"""
    file_id: str = Field(..., description="File identifier")
    columns_to_delete: List[str] = Field(default_factory=list, description="Columns to delete")


class JobConfirmRequest(BaseModel):
    """Request to confirm preview and start processing"""
    file_selections: List[FileColumnSelection] = Field(..., description="Column selections for each file")


class JobConfirmResponse(BaseModel):
    """Response after confirming preview"""
    job_id: str = Field(..., description="Created job identifier")
    status: JobStatus = Field(..., description="Job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    file_count: int = Field(..., description="Number of files")
    columns_removed: int = Field(..., description="Total columns removed")
    message: str = Field(..., description="Response message")


class PreviewDeleteResponse(BaseModel):
    """Response for preview deletion"""
    message: str = Field(..., description="Deletion confirmation message")
    preview_id: str = Field(..., description="Deleted preview identifier")
    files_deleted: int = Field(default=0, description="Number of files deleted")


# ==================== Existing Job Models ====================

class JobCreateOptions(BaseModel):
    """Options for job creation"""
    enable_llm: bool = Field(default=True, description="Enable LLM validation")
    output_format: str = Field(default="json", description="Output format (currently only json)")


class JobCreateResponse(BaseModel):
    """Response for job creation"""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    file_count: int = Field(..., description="Number of files uploaded")
    message: str = Field(default="Job created successfully", description="Response message")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_abc123xyz",
                "status": "pending",
                "created_at": "2024-01-29T10:30:00Z",
                "file_count": 3,
                "message": "Job created successfully"
            }
        }


class JobStatusResponse(BaseModel):
    """Response for job status query"""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    progress_percent: int = Field(default=0, description="Overall progress percentage (0-100)", ge=0, le=100)
    current_stage: Optional[str] = Field(None, description="Current processing stage")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    file_count: int = Field(..., description="Number of files in job")
    relationships_found: Optional[int] = Field(None, description="Number of relationships discovered")
    error: Optional[str] = Field(None, description="Error message if job failed")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_abc123xyz",
                "status": "running",
                "progress_percent": 45,
                "current_stage": "llm_validation",
                "created_at": "2024-01-29T10:30:00Z",
                "started_at": "2024-01-29T10:30:05Z",
                "completed_at": None,
                "file_count": 3,
                "relationships_found": 8,
                "error": None
            }
        }


class JobResultResponse(BaseModel):
    """Response for job result query"""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    result: Optional[Dict[str, Any]] = Field(None, description="Analysis result (full JSON report)")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    message: Optional[str] = Field(None, description="Message if result not ready")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_abc123xyz",
                "status": "completed",
                "result": {"report_metadata": {}, "relationships": []},
                "completed_at": "2024-01-29T10:32:00Z",
                "message": None
            }
        }


class JobListItem(BaseModel):
    """Single job in job list response"""
    job_id: str
    status: JobStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    file_count: int
    relationships_found: Optional[int] = None
    progress_percent: int = 0


class JobListResponse(BaseModel):
    """Response for job list query"""
    total: int = Field(..., description="Total number of jobs")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Offset for pagination")
    jobs: List[JobListItem] = Field(..., description="List of jobs")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 42,
                "limit": 20,
                "offset": 0,
                "jobs": [
                    {
                        "job_id": "job_abc123xyz",
                        "status": "completed",
                        "created_at": "2024-01-29T10:30:00Z",
                        "completed_at": "2024-01-29T10:32:00Z",
                        "file_count": 3,
                        "relationships_found": 12,
                        "progress_percent": 100
                    }
                ]
            }
        }


class JobDeleteResponse(BaseModel):
    """Response for job deletion"""
    message: str = Field(..., description="Deletion confirmation message")
    job_id: str = Field(..., description="Deleted job identifier")
    files_deleted: int = Field(default=0, description="Number of files deleted")


class ProgressLogItem(BaseModel):
    """Single progress log entry"""
    timestamp: datetime
    stage: str
    message: str
    percent: int


class JobProgressResponse(BaseModel):
    """Detailed progress response"""
    job_id: str
    progress_percent: int
    current_stage: Optional[str] = None
    recent_logs: List[ProgressLogItem] = Field(default_factory=list, description="Recent progress logs")


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: Dict[str, Any] = Field(..., description="Error details")

    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": "File size exceeds 100MB limit",
                    "details": {
                        "max_size_mb": 100,
                        "actual_size_mb": 150
                    }
                }
            }
        }


class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str = Field(..., description="Message type (progress, completed, error)")
    job_id: str = Field(..., description="Job identifier")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "progress",
                "job_id": "job_abc123xyz",
                "data": {
                    "progress_percent": 45,
                    "current_stage": "llm_validation",
                    "message": "Validating relationship 5/10"
                },
                "timestamp": "2024-01-29T10:31:30Z"
            }
        }
