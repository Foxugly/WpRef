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

## Donnees / exploitation

- migrations appliquees
- outbox email traitee par un worker ou un cron
- compte admin verifie
- stockage media valide
- sauvegarde base de donnees definie
- logs accessibles en environnement cible

## Flux critiques

- inscription + confirmation email
- mot de passe oublie
- assignation d un quiz
- passage d un quiz
- correction
- alertes quiz
