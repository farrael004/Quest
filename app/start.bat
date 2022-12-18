@echo off

set VENV_DIR=venv
start cmd /k "%~dp0%VENV_DIR%\Scripts\activate.bat && streamlit run streamlit_app.py"

