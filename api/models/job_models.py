"""Domain models for job management"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from api.models.api_models import JobStatus


@dataclass
class Job:
    """Job domain model"""
    job_id: str
    status: JobStatus
    created_at: datetime
    file_count: int
    progress_percent: int = 0
    current_stage: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    relationship_count: Optional[int] = None
    result_file_path: Optional[str] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> "Job":
        """Create Job from database row"""
        if row is None:
            return None

        return cls(
            job_id=row[0],
            status=JobStatus(row[1]),
            created_at=datetime.fromisoformat(row[2]) if isinstance(row[2], str) else row[2],
            started_at=datetime.fromisoformat(row[3]) if row[3] and isinstance(row[3], str) else row[3],
            completed_at=datetime.fromisoformat(row[4]) if row[4] and isinstance(row[4], str) else row[4],
            progress_percent=row[5] or 0,
            current_stage=row[6],
            error_message=row[7],
            file_count=row[8],
            relationship_count=row[9],
            result_file_path=row[10]
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress_percent": self.progress_percent,
            "current_stage": self.current_stage,
            "error_message": self.error_message,
            "file_count": self.file_count,
            "relationship_count": self.relationship_count,
            "result_file_path": self.result_file_path
        }


@dataclass
class UploadedFile:
    """Uploaded file domain model"""
    file_id: str
    job_id: str
    original_filename: str
    stored_filename: str
    file_path: str
    file_size: int
    uploaded_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_db_row(cls, row: tuple) -> "UploadedFile":
        """Create UploadedFile from database row"""
        if row is None:
            return None

        return cls(
            file_id=row[0],
            job_id=row[1],
            original_filename=row[2],
            stored_filename=row[3],
            file_path=row[4],
            file_size=row[5],
            uploaded_at=datetime.fromisoformat(row[6]) if isinstance(row[6], str) else row[6]
        )
