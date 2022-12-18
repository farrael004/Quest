@echo off


cd ..
start cmd /k "cd venv\Scripts\ && activate.bat && cd ..\.. && cd conversation_settings && python _create_setting.py"