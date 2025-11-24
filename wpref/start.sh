rm db.sqlite3
python.exe manage.py makemigrations
python.exe manage.py migrate
python.exe manage.py test
python.exe manage.py runscript create_users
python.exe manage.py runserver
python.exe data.py
python.exe quiz.py

