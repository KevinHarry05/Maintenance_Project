#!/usr/bin/env python
"""
Verification script to check if Python dependencies are installed
"""
import sys
import subprocess

def check_module(module_name, display_name=None):
    """Check if a module is installed and get its version"""
    if display_name is None:
        display_name = module_name
    
    try:
        module = __import__(module_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✓ {display_name}: {version}")
        return True
    except ImportError:
        print(f"✗ {display_name}: NOT INSTALLED")
        return False

def main():
    print("Checking Python Environment...")
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.executable}")
    print("\nChecking key dependencies:")
    print("-" * 50)
    
    # List of key modules to check
    modules_to_check = [
        ('pydantic', 'Pydantic'),
        ('pydantic_core', 'Pydantic Core'),
        ('pydantic_settings', 'Pydantic Settings'),
        ('fastapi', 'FastAPI'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('asyncpg', 'Asyncpg'),
        ('redis', 'Redis'),
        ('celery', 'Celery'),
        ('alembic', 'Alembic'),
        ('uvicorn', 'Uvicorn'),
    ]
    
    all_installed = True
    for module_name, display_name in modules_to_check:
        if not check_module(module_name, display_name):
            all_installed = False
    
    print("-" * 50)
    if all_installed:
        print("\n✓ All key dependencies are installed!")
        return 0
    else:
        print("\n✗ Some dependencies are missing!")
        print("\nTo install dependencies, run:")
        print("  pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
