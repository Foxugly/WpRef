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

Recommandations production :

- reverse proxy HTTPS devant Django
- `SECURE_SSL_REDIRECT` actif
- cookies `Secure`
- HSTS actif
- base PostgreSQL recommandee
- stockage des medias hors filesystem local si plusieurs instances
- worker ou cron pour traiter l outbox email

Commandes minimales :

```bash
cd wpref
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py test
python manage.py check --deploy
python manage.py spectacular --file openapi.yaml
python manage.py process_outbound_email --limit 100
```

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
