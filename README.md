# WpRef

Monorepo contenant :

- [`wpref/`](./wpref) : backend Django REST
- [`wpref-frontend/`](./wpref-frontend) : frontend Angular

## Demarrage rapide

Backend :

```bash
cd wpref
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Frontend :

```bash
cd wpref-frontend
npm ci
npm start
```

## Qualite

Backend :

```bash
cd wpref
python manage.py test
python manage.py spectacular --file openapi.yaml
```

Frontend :

```bash
cd wpref-frontend
npm run typecheck
npm test -- --watch=false
npm run build
npm run test:e2e
```

Synchronisation du contrat API :

```bash
powershell -ExecutionPolicy Bypass -File .\scripts\sync-openapi.ps1
```

## Configuration

Le backend selectionne son profil via `DJANGO_ENV` :

- `dev` : configuration locale permissive
- `prod` : configuration durcie

En profil `prod`, les variables critiques (`SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL`, `FRONTEND_BASE_URL`, `DEFAULT_FROM_EMAIL`) sont obligatoires.

Les emails applicatifs passent par une outbox base de donnees et doivent etre traites via :

```bash
cd wpref
python manage.py process_outbound_email --limit 100
```

Fichiers principaux :

- [`wpref/wpref/settings.py`](./wpref/wpref/settings.py)
- [`wpref/wpref/settings_base.py`](./wpref/wpref/settings_base.py)
- [`wpref/wpref/settings_dev.py`](./wpref/wpref/settings_dev.py)
- [`wpref/wpref/settings_prod.py`](./wpref/wpref/settings_prod.py)

## Documentation

- structure du depot : [`docs/repository-structure.md`](./docs/repository-structure.md)
- deploiement : [`docs/deployment.md`](./docs/deployment.md)
- checklist acceptance / production : [`docs/acceptance-checklist.md`](./docs/acceptance-checklist.md)
- contrat API backend : [`wpref/openapi.yaml`](./wpref/openapi.yaml)
- contrat API frontend : [`wpref-frontend/openapi.yaml`](./wpref-frontend/openapi.yaml)

## Principes

- le backend et le frontend restent decouples a l'execution
- le contrat partage passe par OpenAPI
- les artefacts locaux ne doivent pas etre commites
- la CI doit rester verte avant merge
