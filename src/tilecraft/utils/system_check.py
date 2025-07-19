"""
System dependency verification utilities.
"""

import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class DependencyCheck:
    """Result of a dependency check."""
    name: str
    available: bool
    version: Optional[str] = None
    path: Optional[str] = None
    error: Optional[str] = None
    installation_help: Optional[str] = None


class SystemVerifier:
    """Verify system dependencies for Tilecraft."""

    def __init__(self):
        """Initialize system verifier."""
        self.results = {}

    def verify_all_dependencies(self) -> dict[str, DependencyCheck]:
        """
        Verify all required system dependencies.

        Returns:
            Dictionary of dependency names to check results
        """
        dependencies = [
            "python",
            "tippecanoe", 
            "osmium",
            "gdal",
        ]
        
        for dep in dependencies:
            self.results[dep] = self._verify_dependency(dep)
        
        return self.results

    def _verify_dependency(self, name: str) -> DependencyCheck:
        """Verify a specific dependency."""
        if name == "python":
            return self._check_python()
        elif name == "tippecanoe":
            return self._check_tippecanoe()
        elif name == "osmium":
            return self._check_osmium()
        elif name == "gdal":
            return self._check_gdal()
        else:
            return DependencyCheck(
                name=name,
                available=False,
                error=f"Unknown dependency: {name}"
            )

    def _check_python(self) -> DependencyCheck:
        """Check Python version and basic functionality."""
        try:
            version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            
            # Check minimum version (3.9+)
            if sys.version_info < (3, 9):
                return DependencyCheck(
                    name="python",
                    available=False,
                    version=version,
                    path=sys.executable,
                    error=f"Python {version} is too old. Tilecraft requires Python 3.9+",
                    installation_help="Please upgrade to Python 3.9 or later"
                )
            
            return DependencyCheck(
                name="python",
                available=True,
                version=version,
                path=sys.executable
            )
            
        except Exception as e:
            return DependencyCheck(
                name="python",
                available=False,
                error=f"Error checking Python: {e}"
            )

    def _check_tippecanoe(self) -> DependencyCheck:
        """Check tippecanoe availability and version."""
        try:
            # Check if tippecanoe is in PATH
            tippecanoe_path = shutil.which("tippecanoe")
            if not tippecanoe_path:
                return DependencyCheck(
                    name="tippecanoe",
                    available=False,
                    error="tippecanoe not found in PATH",
                    installation_help=(
                        "Install tippecanoe:\n"
                        "  • macOS: brew install tippecanoe\n"
                        "  • Ubuntu/Debian: apt install tippecanoe\n"
                        "  • From source: https://github.com/felt/tippecanoe#installation"
                    )
                )
            
            # Check version and functionality
            result = subprocess.run(
                ["tippecanoe", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return DependencyCheck(
                    name="tippecanoe",
                    available=False,
                    path=tippecanoe_path,
                    error=f"tippecanoe version check failed: {result.stderr}",
                    installation_help="tippecanoe may be corrupted. Try reinstalling."
                )
            
            # Extract version from output
            version_line = result.stdout.strip()
            version = version_line.split()[-1] if version_line else "unknown"
            
            return DependencyCheck(
                name="tippecanoe",
                available=True,
                version=version,
                path=tippecanoe_path
            )
            
        except subprocess.TimeoutExpired:
            return DependencyCheck(
                name="tippecanoe",
                available=False,
                error="tippecanoe version check timed out",
                installation_help="tippecanoe may be corrupted. Try reinstalling."
            )
        except Exception as e:
            return DependencyCheck(
                name="tippecanoe",
                available=False,
                error=f"Error checking tippecanoe: {e}",
                installation_help="Install tippecanoe: https://github.com/felt/tippecanoe#installation"
            )

    def _check_osmium(self) -> DependencyCheck:
        """Check osmium Python package availability."""
        try:
            # Try to import osmium
            import osmium
            
            # Get version if available
            version = getattr(osmium, '__version__', None)
            if not version:
                # Try to get version from osmium-tool if available
                osmium_tool_path = shutil.which("osmium")
                if osmium_tool_path:
                    try:
                        result = subprocess.run(
                            ["osmium", "--version"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            version = result.stdout.strip().split()[-1]
                    except Exception:
                        pass
            
            return DependencyCheck(
                name="osmium",
                available=True,
                version=version or "unknown"
            )
            
        except ImportError as e:
            return DependencyCheck(
                name="osmium",
                available=False,
                error=f"osmium Python package not found: {e}",
                installation_help=(
                    "Install osmium:\n"
                    "  • pip install osmium\n"
                    "  • conda install -c conda-forge osmium-tool\n"
                    "  • Note: Requires libosmium C++ library"
                )
            )
        except Exception as e:
            return DependencyCheck(
                name="osmium",
                available=False,
                error=f"Error checking osmium: {e}"
            )

    def _check_gdal(self) -> DependencyCheck:
        """Check GDAL availability."""
        try:
            # Try to import GDAL
            from osgeo import gdal
            
            # Get version
            version = gdal.VersionInfo("RELEASE_NAME")
            
            # Basic functionality test
            gdal.UseExceptions()
            
            return DependencyCheck(
                name="gdal",
                available=True,
                version=version
            )
            
        except ImportError as e:
            return DependencyCheck(
                name="gdal",
                available=False,
                error=f"GDAL Python bindings not found: {e}",
                installation_help=(
                    "Install GDAL:\n"
                    "  • pip install gdal\n"
                    "  • conda install -c conda-forge gdal\n"
                    "  • macOS: brew install gdal\n"
                    "  • Ubuntu/Debian: apt install gdal-bin python3-gdal"
                )
            )
        except Exception as e:
            return DependencyCheck(
                name="gdal",
                available=False,
                error=f"Error checking GDAL: {e}"
            )

    def get_summary(self) -> dict:
        """Get a summary of all dependency checks."""
        if not self.results:
            self.verify_all_dependencies()
        
        available = sum(1 for result in self.results.values() if result.available)
        total = len(self.results)
        
        return {
            "total_dependencies": total,
            "available_dependencies": available,
            "missing_dependencies": total - available,
            "all_available": available == total,
            "critical_missing": [
                name for name, result in self.results.items()
                if not result.available and name in ["tippecanoe", "osmium"]
            ],
            "results": self.results
        }

    def print_status(self, verbose: bool = False) -> None:
        """Print dependency status in human-readable format."""
        if not self.results:
            self.verify_all_dependencies()
        
        print("🔍 Tilecraft System Dependencies Check")
        print("=" * 50)
        
        for name, result in self.results.items():
            status = "✅" if result.available else "❌"
            version_info = f" (v{result.version})" if result.version else ""
            print(f"{status} {name.ljust(12)}{version_info}")
            
            if verbose and result.path:
                print(f"    Path: {result.path}")
            
            if not result.available:
                if result.error:
                    print(f"    Error: {result.error}")
                if result.installation_help:
                    print(f"    Help: {result.installation_help}")
                print()
        
        summary = self.get_summary()
        print(f"\nSummary: {summary['available_dependencies']}/{summary['total_dependencies']} dependencies available")
        
        if not summary["all_available"]:
            print("\n⚠️  Some dependencies are missing. Tilecraft may not function correctly.")
            if summary["critical_missing"]:
                print(f"Critical missing: {', '.join(summary['critical_missing'])}")
        else:
            print("\n🎉 All dependencies are available!")

    def can_run_tilecraft(self) -> tuple[bool, list[str]]:
        """
        Check if Tilecraft can run with current dependencies.
        
        Returns:
            Tuple of (can_run, list_of_missing_critical_deps)
        """
        if not self.results:
            self.verify_all_dependencies()
        
        critical_deps = ["tippecanoe", "osmium"]
        missing_critical = [
            name for name in critical_deps
            if name in self.results and not self.results[name].available
        ]
        
        return len(missing_critical) == 0, missing_critical


def verify_system_dependencies(verbose: bool = False) -> bool:
    """
    Convenient function to verify all system dependencies.
    
    Args:
        verbose: Whether to print detailed information
        
    Returns:
        True if all critical dependencies are available
    """
    verifier = SystemVerifier()
    verifier.verify_all_dependencies()
    
    if verbose:
        verifier.print_status(verbose=True)
    
    can_run, missing = verifier.can_run_tilecraft()
    return can_run