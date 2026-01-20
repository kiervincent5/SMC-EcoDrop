@echo off
cd /d "C:\Users\Administrator\SMC_EcoDrop"
call django-env\Scripts\activate.bat
python manage.py migrate
pause
