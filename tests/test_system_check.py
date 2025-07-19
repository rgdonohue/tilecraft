"""
Tests for system dependency verification.
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tilecraft.utils.system_check import DependencyCheck, SystemVerifier, verify_system_dependencies


class TestDependencyCheck:
    """Tests for DependencyCheck dataclass."""

    def test_dependency_check_available(self):
        """Test dependency check for available dependency."""
        check = DependencyCheck(
            name="test",
            available=True,
            version="1.0.0",
            path="/usr/bin/test"
        )
        
        assert check.name == "test"
        assert check.available is True
        assert check.version == "1.0.0"
        assert check.path == "/usr/bin/test"
        assert check.error is None
        assert check.installation_help is None

    def test_dependency_check_missing(self):
        """Test dependency check for missing dependency."""
        check = DependencyCheck(
            name="missing",
            available=False,
            error="Not found",
            installation_help="Install with: pip install missing"
        )
        
        assert check.name == "missing"
        assert check.available is False
        assert check.error == "Not found"
        assert check.installation_help == "Install with: pip install missing"


class TestSystemVerifier:
    """Tests for SystemVerifier class."""

    def test_initialization(self):
        """Test system verifier initialization."""
        verifier = SystemVerifier()
        assert verifier.results == {}

    def test_python_check_success(self):
        """Test successful Python version check."""
        verifier = SystemVerifier()
        result = verifier._check_python()
        
        assert result.name == "python"
        assert result.available is True
        assert result.version is not None
        assert result.path is not None
        assert result.error is None

    @patch("shutil.which")
    def test_tippecanoe_missing(self, mock_which):
        """Test tippecanoe check when not installed."""
        mock_which.return_value = None
        
        verifier = SystemVerifier()
        result = verifier._check_tippecanoe()
        
        assert result.name == "tippecanoe"
        assert result.available is False
        assert result.error == "tippecanoe not found in PATH"
        assert "Install tippecanoe" in result.installation_help

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_tippecanoe_available(self, mock_which, mock_run):
        """Test tippecanoe check when available."""
        mock_which.return_value = "/usr/bin/tippecanoe"
        mock_run.return_value = Mock(
            returncode=0,
            stdout="tippecanoe 1.36.0"
        )
        
        verifier = SystemVerifier()
        result = verifier._check_tippecanoe()
        
        assert result.name == "tippecanoe"
        assert result.available is True
        assert result.version == "1.36.0"
        assert result.path == "/usr/bin/tippecanoe"

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_tippecanoe_version_check_fails(self, mock_which, mock_run):
        """Test tippecanoe check when version command fails."""
        mock_which.return_value = "/usr/bin/tippecanoe"
        mock_run.return_value = Mock(
            returncode=1,
            stderr="Command failed"
        )
        
        verifier = SystemVerifier()
        result = verifier._check_tippecanoe()
        
        assert result.name == "tippecanoe"
        assert result.available is False
        assert "version check failed" in result.error

    def test_osmium_missing(self):
        """Test osmium check when not installed."""
        with patch.dict('sys.modules', {'osmium': None}):
            # Force import error
            verifier = SystemVerifier()
            
            # Mock the import to raise ImportError
            original_import = __builtins__['__import__']
            
            def mock_import(name, *args, **kwargs):
                if name == 'osmium':
                    raise ImportError("No module named 'osmium'")
                return original_import(name, *args, **kwargs)
            
            with patch('builtins.__import__', side_effect=mock_import):
                result = verifier._check_osmium()
            
            assert result.name == "osmium"
            assert result.available is False
            assert "osmium Python package not found" in result.error
            assert "pip install osmium" in result.installation_help

    def test_gdal_missing(self):
        """Test GDAL check when not installed."""
        verifier = SystemVerifier()
        
        # Mock the import to raise ImportError
        original_import = __builtins__['__import__']
        
        def mock_import(name, *args, **kwargs):
            if name == 'osgeo':
                raise ImportError("No module named 'osgeo'")
            return original_import(name, *args, **kwargs)
        
        with patch('builtins.__import__', side_effect=mock_import):
            result = verifier._check_gdal()
        
        assert result.name == "gdal"
        assert result.available is False
        assert "GDAL Python bindings not found" in result.error
        assert "pip install gdal" in result.installation_help

    def test_verify_all_dependencies(self):
        """Test verifying all dependencies."""
        verifier = SystemVerifier()
        results = verifier.verify_all_dependencies()
        
        assert "python" in results
        assert "tippecanoe" in results
        assert "osmium" in results
        assert "gdal" in results
        
        # All should be DependencyCheck instances
        for result in results.values():
            assert isinstance(result, DependencyCheck)

    def test_get_summary(self):
        """Test getting dependency summary."""
        verifier = SystemVerifier()
        verifier.results = {
            "test1": DependencyCheck("test1", available=True),
            "test2": DependencyCheck("test2", available=False),
            "tippecanoe": DependencyCheck("tippecanoe", available=False),
        }
        
        summary = verifier.get_summary()
        
        assert summary["total_dependencies"] == 3
        assert summary["available_dependencies"] == 1
        assert summary["missing_dependencies"] == 2
        assert summary["all_available"] is False
        assert "tippecanoe" in summary["critical_missing"]

    def test_can_run_tilecraft(self):
        """Test checking if Tilecraft can run."""
        verifier = SystemVerifier()
        verifier.results = {
            "python": DependencyCheck("python", available=True),
            "tippecanoe": DependencyCheck("tippecanoe", available=True),
            "osmium": DependencyCheck("osmium", available=True),
            "gdal": DependencyCheck("gdal", available=False),
        }
        
        can_run, missing = verifier.can_run_tilecraft()
        
        assert can_run is True  # GDAL missing is not critical
        assert missing == []

    def test_cannot_run_tilecraft_missing_critical(self):
        """Test checking when critical dependencies are missing."""
        verifier = SystemVerifier()
        verifier.results = {
            "python": DependencyCheck("python", available=True),
            "tippecanoe": DependencyCheck("tippecanoe", available=False),
            "osmium": DependencyCheck("osmium", available=False),
            "gdal": DependencyCheck("gdal", available=True),
        }
        
        can_run, missing = verifier.can_run_tilecraft()
        
        assert can_run is False
        assert "tippecanoe" in missing
        assert "osmium" in missing

    def test_unknown_dependency(self):
        """Test checking unknown dependency."""
        verifier = SystemVerifier()
        result = verifier._verify_dependency("unknown")
        
        assert result.name == "unknown"
        assert result.available is False
        assert "Unknown dependency" in result.error


class TestVerifySystemDependencies:
    """Tests for convenience function."""

    @patch.object(SystemVerifier, 'can_run_tilecraft')
    def test_verify_system_dependencies_success(self, mock_can_run):
        """Test successful dependency verification."""
        mock_can_run.return_value = (True, [])
        
        result = verify_system_dependencies(verbose=False)
        assert result is True

    @patch.object(SystemVerifier, 'can_run_tilecraft')
    def test_verify_system_dependencies_failure(self, mock_can_run):
        """Test failed dependency verification."""
        mock_can_run.return_value = (False, ["tippecanoe"])
        
        result = verify_system_dependencies(verbose=False)
        assert result is False