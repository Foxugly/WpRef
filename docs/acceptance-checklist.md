# Acceptance Checklist

## Qualite

- `python manage.py test` vert
- `python manage.py check --deploy` vert en profil `prod`
- `npm test -- --watch=false` vert
- `npm run typecheck` vert
- `npm run build` vert
- `npm run test:e2e` vert

## Configuration

- `DJANGO_ENV=prod` verifie en environnement cible
- `SECRET_KEY` non par defaut
- `ALLOWED_HOSTS` non wildcard
- `CSRF_TRUSTED_ORIGINS` renseigne
- SMTP Office 365 configure
- `FRONTEND_BASE_URL` pointe vers le vrai frontend
- `CELERY_BROKER_URL` renseigne
- `CELERY_RESULT_BACKEND` renseigne
- `USE_DEEPL` coherent avec l environnement cible
- `DEEPL_AUTH_KEY` present uniquement si `USE_DEEPL=True`

## Donnees / exploitation

- migrations appliquees
- Redis disponible
- worker Celery demarre
- emails tests recus dans la bonne langue destinataire
- compte admin verifie
- stockage media valide
- sauvegarde base de donnees definie
- logs accessibles en environnement cible

## Flux critiques

- inscription + confirmation email
- mot de passe oublie
- assignation d un quiz
- reception de l alerte d assignation dans la langue du destinataire avec lien quiz
- passage d un quiz
- correction
- alertes quiz
- traduction DeepL si activee
