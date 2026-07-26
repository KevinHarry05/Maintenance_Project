#!/usr/bin/env python
"""
TASK 1: Diagnose Pydantic/pydantic-core Import Error
This script performs all diagnostics needed for Task 1
"""

import sys
import subprocess
from pathlib import Path

print("="*80)
print("TASK 1: DIAGNOSE PYDANTIC/PYDANTIC-CORE IMPORT ERROR")
print("="*80)

# 1.1 Check Python Version
print("\n1.1 Checking Python Version...")
print(f"Python Version: {sys.version}")
print(f"Python Executable: {sys.executable}")

version_tuple = sys.version_info
if version_tuple.major == 3 and version_tuple.minor >= 10:
    print("✓ Python version compatible (3.10+)")
else:
    print("✗ Python version too old (need 3.10+)")

# 1.2 Verify Virtual Environment
print("\n1.2 Verifying Virtual Environment...")
if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print(f"✓ Virtual environment detected")
    print(f"  venv path: {sys.prefix}")
else:
    print("✗ Not in virtual environment")

# 1.3 List Installed Pydantic Packages
print("\n1.3 Listing Installed Pydantic Packages...")
try:
    import pydantic
    print(f"✓ pydantic {pydantic.__version__} installed")
except ImportError as e:
    print(f"✗ pydantic import failed: {e}")

try:
    import pydantic_core
    print(f"✓ pydantic_core import successful")
except ImportError as e:
    print(f"✗ pydantic_core import failed: {e}")

# 1.4 Check pydantic-core Binary Extension
print("\n1.4 Checking pydantic-core Binary Extension...")
try:
    from pydantic_core import core
    print(f"✓ pydantic_core._pydantic_core binary loads successfully")
except ImportError as e:
    print(f"✗ pydantic_core._pydantic_core import failed: {e}")

# 1.5 Test Pydantic Import
print("\n1.5 Testing Pydantic Import...")
try:
    import pydantic
    print(f"✓ Pydantic import successful")
    print(f"  Version: {pydantic.__version__}")
except ImportError as e:
    print(f"✗ Pydantic import failed: {e}")

# 1.6 Test FastAPI Import
print("\n1.6 Testing FastAPI Import...")
try:
    import fastapi
    from fastapi import FastAPI
    print(f"✓ FastAPI import successful")
    print(f"  Version: {fastapi.__version__}")
except ImportError as e:
    print(f"✗ FastAPI import failed: {e}")

# 1.7 Test app.main import
print("\n1.7 Testing app.main Module Import...")
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from app.main import app
    print(f"✓ app.main import successful")
except Exception as e:
    print(f"✗ app.main import failed: {e}")

# Summary
print("\n" + "="*80)
print("DIAGNOSTIC SUMMARY")
print("="*80)
print("\nCheck the results above to identify issues:")
print("- If pydantic_core._pydantic_core fails: Binary extension missing/corrupt")
print("- If FastAPI fails: pydantic not loading correctly")
print("- If app.main fails: Check other import dependencies")
print("\nProceed to Task 2 to fix issues.")
