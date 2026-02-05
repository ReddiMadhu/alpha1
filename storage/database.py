"""SQLite database initialization and management"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from api.config import config
from loguru import logger


DATABASE_SCHEMA = """
-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    status TEXT CHECK(status IN ('pending', 'running', 'completed', 'failed', 'cancelled')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    progress_percent INTEGER DEFAULT 0 CHECK(progress_percent >= 0 AND progress_percent <= 100),
    current_stage TEXT,
    error_message TEXT,
    file_count INTEGER NOT NULL,
    relationship_count INTEGER,
    result_file_path TEXT
);

-- Uploaded files table
CREATE TABLE IF NOT EXISTS uploaded_files (
    file_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    stored_filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job progress logs table
CREATE TABLE IF NOT EXISTS job_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    stage TEXT NOT NULL,
    message TEXT,
    percent INTEGER CHECK(percent >= 0 AND percent <= 100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Preview sessions table
CREATE TABLE IF NOT EXISTS preview_sessions (
    preview_id TEXT PRIMARY KEY,
    status TEXT CHECK(status IN ('preview_ready', 'confirmed', 'cancelled')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_count INTEGER NOT NULL,
    total_duplicates_detected INTEGER DEFAULT 0
);

-- Preview files table
CREATE TABLE IF NOT EXISTS preview_files (
    file_id TEXT PRIMARY KEY,
    preview_id TEXT NOT NULL REFERENCES preview_sessions(preview_id) ON DELETE CASCADE,
    original_filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    dataframe_pickle_path TEXT,
    row_count INTEGER,
    column_count INTEGER,
    metadata_json TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_uploaded_files_job_id ON uploaded_files(job_id);
CREATE INDEX IF NOT EXISTS idx_job_progress_job_id ON job_progress(job_id);
CREATE INDEX IF NOT EXISTS idx_job_progress_timestamp ON job_progress(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_preview_files_preview_id ON preview_files(preview_id);
CREATE INDEX IF NOT EXISTS idx_preview_sessions_created_at ON preview_sessions(created_at DESC);
"""


def init_database():
    """Initialize the SQLite database with schema"""
    try:
        # Ensure directory exists
        db_path = Path(config.DATABASE_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Connect and create schema
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        conn.executescript(DATABASE_SCHEMA)
        conn.commit()
        conn.close()

        logger.info(f"Database initialized at {db_path}")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


@contextmanager
def get_db_connection():
    """
    Context manager for database connections

    Usage:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT ...")
            rows = cursor.fetchall()
    """
    conn = None
    try:
        conn = sqlite3.connect(
            config.DATABASE_PATH,
            check_same_thread=False,  # Allow usage from different threads
            timeout=30.0  # 30 second timeout
        )
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row  # Enable column access by name
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def execute_query(query: str, params: tuple = (), fetch_one: bool = False):
    """
    Execute a query and return results

    Args:
        query: SQL query string
        params: Query parameters
        fetch_one: If True, return single row; otherwise return all rows

    Returns:
        Single row (if fetch_one=True) or list of rows
    """
    with get_db_connection() as conn:
        cursor = conn.execute(query, params)
        if fetch_one:
            return cursor.fetchone()
        return cursor.fetchall()


def execute_update(query: str, params: tuple = ()):
    """
    Execute an INSERT/UPDATE/DELETE query

    Args:
        query: SQL query string
        params: Query parameters

    Returns:
        Number of affected rows
    """
    with get_db_connection() as conn:
        cursor = conn.execute(query, params)
        return cursor.rowcount


def cleanup_old_jobs(days: int = 7):
    """
    Delete jobs older than specified days

    Args:
        days: Number of days to keep jobs
    """
    query = """
        DELETE FROM jobs
        WHERE created_at < datetime('now', '-' || ? || ' days')
        AND status IN ('completed', 'failed', 'cancelled')
    """
    deleted = execute_update(query, (days,))
    logger.info(f"Cleaned up {deleted} old jobs")
    return deleted


def cleanup_old_previews(hours: int = 1):
    """
    Delete preview sessions older than specified hours

    Args:
        hours: Number of hours to keep previews (default 1 hour)
    """
    query = """
        DELETE FROM preview_sessions
        WHERE created_at < datetime('now', '-' || ? || ' hours')
    """
    deleted = execute_update(query, (hours,))
    logger.info(f"Cleaned up {deleted} old preview sessions")
    return deleted
