"""
Security validation helpers for BD Intelligence System.
Prevents path traversal, SQL injection, and command injection attacks.
"""

import re
from pathlib import Path
from typing import Optional, List


class SecurityValidationError(ValueError):
    """Raised when security validation fails."""
    pass


def validate_file_path(
    file_path: str,
    allowed_directories: Optional[List[Path]] = None,
    allowed_extensions: Optional[List[str]] = None
) -> Path:
    """
    Validate file path to prevent path traversal and command injection.
    
    Args:
        file_path: User-provided file path
        allowed_directories: List of allowed base directories (default: project outputs/)
        allowed_extensions: List of allowed file extensions (default: .csv, .json)
    
    Returns:
        Resolved absolute Path object
    
    Raises:
        SecurityValidationError: If path is invalid or outside allowed directories
    
    Examples:
        >>> validate_file_path("outputs/jobs.csv")
        PosixPath('/path/to/project/outputs/jobs.csv')
        
        >>> validate_file_path("../../etc/passwd")
        SecurityValidationError: Path traversal detected
    """
    if not file_path or not isinstance(file_path, str):
        raise SecurityValidationError("File path must be a non-empty string")
    
    # Block obvious path traversal patterns
    if ".." in file_path or file_path.startswith("/"):
        raise SecurityValidationError("Path traversal detected: ../ or absolute paths not allowed")
    
    # Block special characters that could enable command injection
    if any(char in file_path for char in [";", "|", "&", "`", "$", "(", ")", "<", ">"]):
        raise SecurityValidationError(f"Invalid characters in file path: {file_path}")
    
    # Resolve to absolute path
    try:
        resolved_path = Path(file_path).resolve()
    except (OSError, ValueError) as e:
        raise SecurityValidationError(f"Invalid file path: {e}")
    
    # Default allowed directory: project outputs/
    if allowed_directories is None:
        project_root = Path(__file__).parent.parent.parent
        allowed_directories = [
            project_root / "outputs",
            project_root / "data",
            project_root / "Engine1_Scraper" / "data" / "apify",
        ]
    
    # Check if resolved path is within allowed directories
    path_allowed = any(
        str(resolved_path).startswith(str(allowed_dir.resolve()))
        for allowed_dir in allowed_directories
    )
    
    if not path_allowed:
        raise SecurityValidationError(
            f"File path outside allowed directories: {resolved_path}"
        )
    
    # Validate file extension if specified
    if allowed_extensions:
        if resolved_path.suffix not in allowed_extensions:
            raise SecurityValidationError(
                f"File extension {resolved_path.suffix} not allowed. "
                f"Allowed: {', '.join(allowed_extensions)}"
            )
    
    return resolved_path


def validate_table_name(table_name: str, allowed_tables: Optional[List[str]] = None) -> str:
    """
    Validate SQL table name to prevent SQL injection.
    
    Args:
        table_name: User-provided table name
        allowed_tables: Whitelist of allowed table names (optional)
    
    Returns:
        Validated table name
    
    Raises:
        SecurityValidationError: If table name contains invalid characters
    
    Examples:
        >>> validate_table_name("jobs")
        'jobs'
        
        >>> validate_table_name("jobs; DROP TABLE users;")
        SecurityValidationError: Invalid table name
    """
    if not table_name or not isinstance(table_name, str):
        raise SecurityValidationError("Table name must be a non-empty string")
    
    # Allow only alphanumeric and underscore (standard SQL identifier pattern)
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        raise SecurityValidationError(
            f"Invalid table name: {table_name}. "
            "Only alphanumeric characters and underscores allowed."
        )
    
    # Check against whitelist if provided
    if allowed_tables is not None and table_name not in allowed_tables:
        raise SecurityValidationError(
            f"Table '{table_name}' not in allowed list: {', '.join(allowed_tables)}"
        )
    
    return table_name


def validate_column_name(column_name: str) -> str:
    """
    Validate SQL column name to prevent SQL injection.
    
    Args:
        column_name: User-provided column name
    
    Returns:
        Validated column name
    
    Raises:
        SecurityValidationError: If column name contains invalid characters
    """
    if not column_name or not isinstance(column_name, str):
        raise SecurityValidationError("Column name must be a non-empty string")
    
    # Allow alphanumeric, underscore, and dot (for qualified names like table.column)
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_.]*$', column_name):
        raise SecurityValidationError(
            f"Invalid column name: {column_name}. "
            "Only alphanumeric characters, underscores, and dots allowed."
        )
    
    return column_name


# Commonly used table whitelist for BD Intelligence system
BD_ALLOWED_TABLES = [
    "jobs",
    "programs",
    "contacts",
    "companies",
    "opportunities",
    "call_notes",
    "notes",
    "Note",
    "activity",
    "activities",
    "Candidate",
    "ClientContact",
    "relationships",
    "embeddings",
    "metadata",
]
