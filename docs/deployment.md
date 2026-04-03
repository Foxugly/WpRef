# Deployment

## Backend

Configuration attendue :

- `DJANGO_ENV=prod`
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL`
- `FRONTEND_BASE_URL`
- `EMAIL_BACKEND`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_TLS`
- `DEFAULT_FROM_EMAIL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `API_PAGE_SIZE`
- `DATA_UPLOAD_MAX_MEMORY_SIZE`
- `FILE_UPLOAD_MAX_MEMORY_SIZE`
- `MAX_UPLOAD_FILE_SIZE`
- `USE_DEEPL`
- `DEEPL_AUTH_KEY`
- `DEEPL_IS_FREE`

Recommandations production :

- reverse proxy HTTPS devant Django
- `SECURE_SSL_REDIRECT` actif
- cookies `Secure`
- HSTS actif
- base PostgreSQL recommandee
- stockage des medias hors filesystem local si plusieurs instances
- Redis pour le broker Celery
- worker Celery dedie pour traiter l outbox email
- `MAX_UPLOAD_FILE_SIZE` coherent avec le reverse proxy si upload media actif
- `API_PAGE_SIZE` stable entre acceptance et prod pour garder des reponses coherentes

Commandes minimales :

```bash
cd wpref
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py test
python manage.py check --deploy
python manage.py spectacular --file openapi.yaml
celery -A wpref worker -l info
```

Notes d exploitation :

- les emails backend sont emis dans la langue du destinataire
- une assignation de quiz cree aussi une alerte applicative non lue dans la langue du destinataire avec lien frontend direct vers le quiz
- `python manage.py process_outbound_email --limit 100` reste disponible pour du rattrapage, pas pour le flux nominal
- le worker Celery doit tourner en continu ; ne pas compter sur le process web pour envoyer les mails
- Redis est une dependance runtime du flux email
- si `USE_DEEPL=True`, la cle DeepL doit rester hors Git et etre geree comme un secret
- les erreurs transitoires DeepL sont retriees cote HTTP client puis remontees sous une forme applicative simple
- en prod, les refus `401/403` remontent en `WARNING`, le bruit de debug restant reserve au profil dev
- l admin Django permet l import/export de `Domain`, `Subject` et `Question` via `django-import-export`

Architecture email :

- application Django -> table `core_outboundemail`
- hook `transaction.on_commit(...)`
- tache Celery `deliver_outbound_emails_task`
- worker Celery -> SMTP Office 365

## Frontend

```bash
cd wpref-frontend
npm ci
npm test -- --watch=false
npm run build
npm run test:e2e
```

Le bundle de production est genere dans `wpref-frontend/dist/wpref-frontend`.

## Contrat API

Avant une release :

```bash
powershell -ExecutionPolicy Bypass -File .\scripts\sync-openapi.ps1
git diff -- wpref/openapi.yaml wpref-frontend/openapi.yaml wpref-frontend/src/app/api/generated
```
