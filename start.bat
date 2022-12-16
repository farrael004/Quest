@echo off


set VENV_DIR=venv
set PYTHON="%~dp0%VENV_DIR%\Scripts\Python.exe"
start cmd /k "%~dp0%VENV_DIR%\Scripts\activate.bat && streamlit run streamlit_app.py"

