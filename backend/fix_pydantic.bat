@echo off
call venv\Scripts\activate.bat
pip uninstall -y pydantic pydantic-core pydantic-settings
pip cache purge
pip install --force-reinstall pydantic-core==2.10.1
pip install --force-reinstall pydantic==2.5.0
pip install -r requirements.txt
python -c "import pydantic; print(f'pydantic {pydantic.__version__}')"
python -c "from pydantic_core import core; print('pydantic_core OK')"
python -c "import fastapi; print('fastapi OK')"
pause
