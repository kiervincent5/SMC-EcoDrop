@echo off
echo Fixing Python environment and running migrations...
cd /d "C:\Users\Administrator\SMC_EcoDrop"

REM Try to run migration with current environment
echo Attempting migration with current environment...
django-env\Scripts\python.exe manage.py migrate

REM If that fails, try with system Python
echo If above failed, install Python system-wide and run:
echo python manage.py migrate

pause
