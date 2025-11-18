rm db.sqlite3
python.exe manage.py makemigrations
python.exe manage.py migrate
DJANGO_SUPERUSER_USERNAME=admin \
DJANGO_SUPERUSER_EMAIL=admin@example.com \
DJANGO_SUPERUSER_PASSWORD=SuperPassword123 \
python manage.py createsuperuser --noinput
echo "MAKE USERS"
python.exe manage.py shell < make_users.py
#POWERSHELL type .\make_user.py | python.exe .\manage.py shell
python.exe manage.py runserver

