# QuizOnline

Monorepo contenant :

- [`quizonline-server/`](./quizonline-server) : backend Django REST
- [`quizonline-frontend/`](./quizonline-frontend) : frontend Angular

## Demarrage rapide

Backend :

```bash
cd quizonline-server
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Frontend :

```bash
cd quizonline-frontend
npm ci
npm start
```

## Qualite

Backend :

```bash
cd quizonline-server
python manage.py test
pytest
python manage.py spectacular --file openapi.yaml
```

Frontend :

```bash
cd quizonline-frontend
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

Variables backend notables :

- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `CELERY_TASK_ALWAYS_EAGER`
- `API_PAGE_SIZE`
- `DATA_UPLOAD_MAX_MEMORY_SIZE`
- `FILE_UPLOAD_MAX_MEMORY_SIZE`
- `MAX_UPLOAD_FILE_SIZE`
- `USE_DEEPL`
- `DEEPL_AUTH_KEY`
- `DEEPL_IS_FREE`

Admin backend :

- `django-import-export` est branché sur `Domain`, `Subject` et `Question`
- l import/export admin inclut les colonnes de traduction par langue (`name_fr`, `title_en`, etc.)

Variables d upload / pagination :

- `API_PAGE_SIZE` definit la taille de page par defaut des endpoints pagines
- `DATA_UPLOAD_MAX_MEMORY_SIZE` borne la taille totale d une requete uploadable en memoire
- `FILE_UPLOAD_MAX_MEMORY_SIZE` borne la taille d un fichier garde en memoire avant bascule fichier temporaire
- `MAX_UPLOAD_FILE_SIZE` borne la taille maximale acceptee pour `MediaAsset.file`

Les emails applicatifs passent par une outbox base de donnees traitee par Celery + Redis :

```bash
redis-server
cd quizonline-server
celery -A config worker -l info
```

Le traitement manuel de rattrapage reste disponible si necessaire :

```bash
cd quizonline-server
python manage.py process_outbound_email --limit 100
```

Tous les emails backend sont emis dans la langue du destinataire.
Quand un quiz est assigne a un utilisateur, il recoit aussi une alerte applicative dans sa langue avec un lien direct vers le quiz.

Architecture email :

- le code applicatif enfile un `OutboundEmail` en base
- `transaction.on_commit(...)` declenche une tache Celery
- le worker Celery lit l outbox et envoie le mail via le backend SMTP Django
- la commande `process_outbound_email` sert uniquement de rattrapage

Alertes quiz :

- le menu messages du frontend repose sur les `QuizAlertThread`
- une assignation de quiz cree une alerte applicative non lue pour le destinataire
- cette alerte contient un message localise et le lien frontend du quiz

DeepL :

- `USE_DEEPL=True` active DeepL pour les endpoints de traduction
- `USE_DEEPL=False` garde le backend de traduction simulé
- `DEEPL_IS_FREE=True` cible `api-free.deepl.com`
- en cas de timeout, rate limit ou erreur 5xx, le backend renvoie une erreur applicative propre sans exposer la reponse brute DeepL

Fichiers principaux :

- [`quizonline-server/config/settings.py`](./quizonline-server/config/settings.py)
- [`quizonline-server/config/settings_base.py`](./quizonline-server/config/settings_base.py)
- [`quizonline-server/config/settings_dev.py`](./quizonline-server/config/settings_dev.py)
- [`quizonline-server/config/settings_prod.py`](./quizonline-server/config/settings_prod.py)
- [`quizonline-server/config/celery.py`](./quizonline-server/config/celery.py)

## Documentation

- structure du depot : [`docs/repository-structure.md`](./docs/repository-structure.md)
- deploiement : [`docs/deployment.md`](./docs/deployment.md)
- checklist acceptance / production : [`docs/acceptance-checklist.md`](./docs/acceptance-checklist.md)
- contrat API backend : [`quizonline-server/openapi.yaml`](./quizonline-server/openapi.yaml)
- contrat API frontend : [`quizonline-frontend/openapi.yaml`](./quizonline-frontend/openapi.yaml)

## CI

La CI GitHub valide notamment :

- lint backend `ruff`
- tests backend decoupes par domaines fonctionnels
- `translation.tests`
- `makemigrations --check --dry-run`
- `check --deploy`
- lint frontend
- typecheck frontend
- unit tests frontend
- build frontend
- e2e frontend
- synchro OpenAPI / client genere

Logging :

- en `dev`, les logs applicatifs sont plus verbeux (`DEBUG`)
- en `prod`, les logs applicatifs restent a `INFO`
- les refus d acces `401/403` sont journalises en `WARNING`

## Principes

- le backend et le frontend restent decouples a l'execution
- le contrat partage passe par OpenAPI
- les artefacts locaux ne doivent pas etre commites
- la CI doit rester verte avant merge
