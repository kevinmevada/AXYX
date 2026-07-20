@echo off
cd /d "%~dp0"
set PYTHONPATH=src
set QT_API=pyside6
"venv311\Scripts\python.exe" run_axyx.py
