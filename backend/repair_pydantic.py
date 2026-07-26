#!/usr/bin/env python
"""
TASK 2: Repair Pydantic Dependencies
Reinstalls pydantic and pydantic-core with correct versions
"""

import subprocess
import sys
import os

os.chdir(os.path.dirname(__file__))

print("=" * 80)
print("TASK 2: REPAIR PYDANTIC DEPENDENCIES")
print("=" * 80)

commands = [
    ("Upgrade pip", [sys.executable, "-m", "pip", "install", "--upgrade", "pip"]),
    ("Backup pip list", ["pip", "freeze", ">"]),  # Will redirect manually
    ("Uninstall pydantic", ["pip", "uninstall", "-y", "pydantic", "pydantic-core", "pydantic-settings"]),
    ("Clear pip cache", ["pip", "cache", "purge"]),
    ("Install pydantic-core 2.10.1", ["pip", "install", "--force-reinstall", "--no-cache-dir", "pydantic-core==2.10.1"]),
    ("Install pydantic 2.5.0", ["pip", "install", "--force-reinstall", "--no-cache-dir", "pydantic==2.5.0"]),
    ("Install requirements", ["pip", "install", "-r", "requirements.txt"]),
]

for desc, cmd in commands:
    print(f"\n{desc}...")
    try:
        result = subprocess.run(cmd, check=False, capture_output=False)
        if result.returncode != 0:
            print(f"Warning: {desc} returned code {result.returncode}")
    except Exception as e:
        print(f"Error during {desc}: {e}")

# Verification tests
print("\n" + "=" * 80)
print("VERIFICATION")
print("=" * 80)

tests = [
    ("pydantic import", "import pydantic; print(f'✓ pydantic {pydantic.__version__}')"),
    ("pydantic_core import", "from pydantic_core import core; print('✓ pydantic_core OK')"),
    ("fastapi import", "import fastapi; print('✓ fastapi OK')"),
]

for test_name, code in tests:
    print(f"\n{test_name}...")
    try:
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout.strip())
        else:
            print(f"✗ Failed: {result.stderr}")
    except Exception as e:
        print(f"✗ Error: {e}")

print("\n" + "=" * 80)
print("TASK 2 COMPLETE")
print("=" * 80)
