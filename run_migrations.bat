@echo off
echo Running Django migrations...
cd /d "c:\Users\acer\Desktop\SMC_EcoDrop_1\SMC_EcoDrop"

echo Activating virtual environment...
call django-env\Scripts\activate.bat

echo Making migrations for core app...
django-env\Scripts\python.exe manage.py makemigrations core

echo Applying migrations...
django-env\Scripts\python.exe manage.py migrate

echo Setting up student IDs...
django-env\Scripts\python.exe manage.py fix_qr_codes

echo Done!
pause
