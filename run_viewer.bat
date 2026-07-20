@echo off
cd /d "%~dp0"
call venv311\Scripts\activate.bat
set PYTHONPATH=src
python run_viewer.py
