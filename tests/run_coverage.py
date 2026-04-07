#!/usr/bin/env python3
"""Run tests with coverage reporting."""

import subprocess
import sys
from pathlib import Path


def main():
    """Run pytest with coverage."""
    # Determine project root
    project_root = Path(__file__).parent.parent
    
    # Packages to measure coverage for
    source_packages = [
        "src/sdk",
        "app/api",
        "app/playout", 
        "app/analyzer",
        "app/worker",
        "app/api-client",
    ]
    
    # Build pytest command
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/unit",
        "--cov=src/sdk",
        "--cov=app/api",
        "--cov=app/playout",
        "--cov=app/analyzer",
        "--cov=app/worker",
        "--cov=app/api-client",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-branch",
        "-v",
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print(f"From directory: {project_root}")
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
