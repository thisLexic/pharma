# Pharmacy Django Website 💊

This is used for managing the payroll, time-in/time-out, and government benefits (SSS, PhilHealth, PAGIBIG) of our pharmacy employees. It can also generate daily sales, expense, and payroll reports of our pharmacies. This was created for the use of our family business.

## Images of The Website

Login Page - where the users will login
![Login Page](https://raw.githubusercontent.com/thisLexic/pharma/main/site_images/login.png)

Home Page - the home page of the website where all other parts can be found
![Home Page](https://raw.githubusercontent.com/thisLexic/pharma/main/site_images/home-page.png)

Purchase List - List out all the purchases made by the pharmacies. It contains filters and search bars. This list view is also available for all the other parts of the website.
![Purchase List](https://raw.githubusercontent.com/thisLexic/pharma/main/site_images/purchases-list.png)

Payroll Report - Produce the payroll report of employees of the pharmacies. The report ability is also available for some of the other parts of the website.
![Payroll Report](https://raw.githubusercontent.com/thisLexic/pharma/main/site_images/payroll-report.jpg)

These images can also be found [here](https://github.com/thisLexic/pharma/tree/main/site_images).

# Coding

## Setup

source venv/bin/activate

## Add new fields to models/database (Local)

python3 manage.py makemigrations myapp
python3 manage.py migrate --fake myapp

add the new field/s to models.py

python3 manage.py makemigrations myapp
python3 manage.py migrate myapp

https://stackoverflow.com/questions/24311993/how-to-add-a-new-field-to-a-model-with-new-django-migrations

## Connecting/Copying to/from Server

ssh username@ip_address

COPY TO SERVER: scp local_path username@ip_address:remote_path

COPY TO LOCAL MACHINE: scp username@ip_address:remote_path local_path

## Updating the Server without Changing Database Schema

_backup your database_
_perform update on file/s_
service apache2 restart

## Updating the Server WITH Changing Database Schema

_backup your database_
_backup your files to be editted_
_double check differences bw new/old files_
_perform update on file/s_

source venv/bin/activate

python3 manage.py makemigrations myapp
python3 manage.py migrate --fake myapp

_perform update on file/s_
inluding adding the new field/s to models.py

python3 manage.py makemigrations myapp
python3 manage.py migrate myapp

service apache2 restart
