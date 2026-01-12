import pathlib
from typing import Dict, Any, List, Optional

import requests
import yaml

# ============================================================
# CONFIG
# ============================================================

BASE_URL = "http://localhost:8000"  # ou "http://127.0.0.1:8000"
OPENAPI_PATH = "openapi.yaml"  # chemin vers ton fichier YAML

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "SuperPassword123"
ADMIN_EMAIL = "admin@example.com"
U2_USERNAME = "user2"
U2_EMAIL = "user2@example.com"
U2_PASSWORD = "SuperPassword123"

# ============================================================
# DONNÉES À CRÉER
# ============================================================

DOMAIN_DEF: List[Dict[str, str]] = [
    {
        "name": "Scrum",
        "description": "Plein de questions sur Scrum.",
    },
    {
        "name": "Django",
        "description": "Plein de question sur Django",
    },
]

SUBJECTS_DEF: List[Dict[str, str]] = [
    {
        "name": "Scrum – Bases",
        "description": "Fondamentaux du framework Scrum (événements, artefacts, piliers…).",
        "domain": "Scrum"
    },
    {
        "name": "Scrum – Rôles",
        "description": "Rôles Scrum : Scrum Master, Product Owner et Developers.",
        "domain": "Scrum"
    },
    {
        "name": "Django – Modèles & ORM",
        "description": "Modèles Django, ORM, migrations, relations.",
        "domain": "Django"
    },
    {
        "name": "Django – API REST",
        "description": "API REST avec Django REST Framework, sérialisation, vues, statuts HTTP.",
        "domain": "Django"
    },
]

# 20 questions : chaque question référence des "subject_names".
# Le script transforme subject_names → subject_ids.
QUESTIONS_DEF: List[Dict[str, Any]] = [
    # --- SCRUM (10 questions) ---
    {
        "title": "Quels sont les trois piliers de Scrum ?",
        "description": "Quels sont les trois piliers de Scrum ?",
        "explanation": "Les trois piliers de Scrum sont la Transparence, l’Inspection et l’Adaptation.",
        "allow_multiple_correct": True,
        "subject_names": ["Scrum – Bases"],
        "answer_options": [
            {"content": "Transparence", "is_correct": True, "sort_order": 1},
            {"content": "Inspection", "is_correct": True, "sort_order": 2},
            {"content": "Adaptation", "is_correct": True, "sort_order": 3},
            {"content": "Commandement", "is_correct": False, "sort_order": 4},
        ],
        "domain": "Scrum"
    },
    {
        "title": "Quelles sont les valeurs de Scrum ?",
        "description": "Quelles sont les valeurs de Scrum ?",
        "explanation": "Les valeurs sont : Engagement, Focus, Ouverture, Respect, Courage.",
        "allow_multiple_correct": True,
        "subject_names": ["Scrum – Bases"],
        "answer_options": [
            {"content": "Engagement", "is_correct": True, "sort_order": 1},
            {"content": "Focus", "is_correct": True, "sort_order": 2},
            {"content": "Obéissance", "is_correct": False, "sort_order": 3},
            {"content": "Respect", "is_correct": True, "sort_order": 4},
            {"content": "Ouverture", "is_correct": True, "sort_order": 5},
            {"content": "Courage", "is_correct": True, "sort_order": 6},
        ],
        "domain": "Scrum"
    },
    {
        "title": "Combien de rôles Scrum officiels le framework définit-il ?",
        "description": "Combien de rôles Scrum officiels le framework définit-il ?",
        "explanation": "Le Guide Scrum définit trois rôles : Scrum Master, Product Owner, Developers.",
        "allow_multiple_correct": False,
        "subject_names": ["Scrum – Bases", "Scrum – Rôles"],
        "answer_options": [
            {"content": "2", "is_correct": False, "sort_order": 1},
            {"content": "3", "is_correct": True, "sort_order": 2},
            {"content": "4", "is_correct": False, "sort_order": 3},
        ],
        "domain": "Scrum"
    },
    {
        "title": "Lesquels sont des rôles définis par Scrum ?",
        "description": "Lesquels sont des rôles définis par Scrum ?",
        "explanation": "Les seuls rôles Scrum sont Scrum Master, Product Owner et Developers.",
        "allow_multiple_correct": True,
        "subject_names": ["Scrum – Rôles"],
        "answer_options": [
            {"content": "Scrum Master", "is_correct": True, "sort_order": 1},
            {"content": "Product Owner", "is_correct": True, "sort_order": 2},
            {"content": "Developers", "is_correct": True, "sort_order": 3},
            {"content": "Project Manager", "is_correct": False, "sort_order": 4},
        ],
        "domain": "Scrum"
    },
    {
        "title": "Qui est responsable de maximiser la valeur du produit ?",
        "description": "Qui est responsable de maximiser la valeur du produit ?",
        "explanation": "Le Product Owner est responsable de maximiser la valeur du produit.",
        "allow_multiple_correct": False,
        "subject_names": ["Scrum – Rôles"],
        "answer_options": [
            {"content": "Le Scrum Master", "is_correct": False, "sort_order": 1},
            {"content": "Le Product Owner", "is_correct": True, "sort_order": 2},
            {"content": "Les Developers uniquement", "is_correct": False, "sort_order": 3},
        ],
        "domain": "Scrum"
    },
    {
        "title": "Laquelle de ces affirmations sur le Sprint Backlog est correcte ?",
        "description": "Laquelle de ces affirmations sur le Sprint Backlog est correcte ?",
        "explanation": "Le Sprint Backlog est un plan émergent pour le Sprint, détenu par les Developers.",
        "allow_multiple_correct": True,
        "subject_names": ["Scrum – Bases"],
        "answer_options": [
            {
                "content": "Le Sprint Backlog est détenu par les Developers.",
                "is_correct": True,
                "sort_order": 1,
            },
            {
                "content": "Le Sprint Backlog est un plan émergent pour atteindre l’objectif de Sprint.",
                "is_correct": True,
                "sort_order": 2,
            },
            {
                "content": "Le Sprint Backlog est figé dès le début du Sprint et ne peut plus changer.",
                "is_correct": False,
                "sort_order": 3,
            },
        ],
        "domain": "Scrum"
    },
    {
        "title": "Durée maximale recommandée pour la Daily Scrum ?",
        "description": "Durée maximale recommandée pour la Daily Scrum ?",
        "explanation": "La Daily Scrum est time-boxée à 15 minutes.",
        "allow_multiple_correct": False,
        "subject_names": ["Scrum – Bases"],
        "answer_options": [
            {"content": "15 minutes", "is_correct": True, "sort_order": 1},
            {"content": "30 minutes", "is_correct": False, "sort_order": 2},
            {"content": "1 heure", "is_correct": False, "sort_order": 3},
        ],
        "domain": "Scrum"
    },
    {
        "title": "Quand considère-t-on qu’un Sprint est terminé ?",
        "description": "Quand considère-t-on qu’un Sprint est terminé ?",
        "explanation": "Un Sprint est terminé lorsque la time-box est écoulée.",
        "allow_multiple_correct": False,
        "subject_names": ["Scrum – Bases"],
        "answer_options": [
            {
                "content": "Quand toutes les tâches du Sprint Backlog sont réalisées.",
                "is_correct": False,
                "sort_order": 1,
            },
            {
                "content": "Quand le Product Owner décide de l’arrêter.",
                "is_correct": False,
                "sort_order": 2,
            },
            {
                "content": "Quand la time-box du Sprint est écoulée.",
                "is_correct": True,
                "sort_order": 3,
            },
        ],
        "domain": "Scrum"
    },
    {
        "title": "Quel artefact contient l’Objectif de Produit (Product Goal) ?",
        "description": "Quel artefact contient l’Objectif de Produit (Product Goal) ?",
        "explanation": "L’Objectif de Produit est associé au Product Backlog.",
        "allow_multiple_correct": False,
        "subject_names": ["Scrum – Bases"],
        "answer_options": [
            {"content": "Le Sprint Backlog", "is_correct": False, "sort_order": 1},
            {"content": "Le Product Backlog", "is_correct": True, "sort_order": 2},
            {"content": "L’Incrément", "is_correct": False, "sort_order": 3},
        ],
        "domain": "Scrum"
    },
    {
        "title": "Lesquels de ces événements sont time-boxés dans Scrum ?",
        "description": "Lesquels de ces événements sont time-boxés dans Scrum ?",
        "explanation": "Tous les événements Scrum sont time-boxés.",
        "allow_multiple_correct": True,
        "subject_names": ["Scrum – Bases"],
        "answer_options": [
            {"content": "Sprint Planning", "is_correct": True, "sort_order": 1},
            {"content": "Daily Scrum", "is_correct": True, "sort_order": 2},
            {"content": "Sprint Review", "is_correct": True, "sort_order": 3},
            {"content": "Sprint Retrospective", "is_correct": True, "sort_order": 4},
        ],
        "domain": "Scrum"
    },

    # --- DJANGO (10 questions) ---
    {
        "title": "Que représente un modèle (Model) dans Django ?",
        "description": "Que représente un modèle (Model) dans Django ?",
        "explanation": "Un modèle représente la structure d’une table en base de données.",
        "allow_multiple_correct": False,
        "subject_names": ["Django – Modèles & ORM"],
        "answer_options": [
            {
                "content": "Une classe Python décrivant la structure d’une table de base de données.",
                "is_correct": True,
                "sort_order": 1,
            },
            {
                "content": "Un template HTML.",
                "is_correct": False,
                "sort_order": 2,
            },
            {
                "content": "Un fichier de configuration serveur.",
                "is_correct": False,
                "sort_order": 3,
            },
        ],
        "domain": "Django"
    },
    {
        "title": "Quel type de champ Django utiliser pour stocker un texte long ?",
        "description": "Quel type de champ Django utiliser pour stocker un texte long ?",
        "explanation": "TextField est adapté aux textes longs.",
        "allow_multiple_correct": False,
        "subject_names": ["Django – Modèles & ORM"],
        "answer_options": [
            {"content": "CharField", "is_correct": False, "sort_order": 1},
            {"content": "TextField", "is_correct": True, "sort_order": 2},
            {"content": "IntegerField", "is_correct": False, "sort_order": 3},
        ],
        "domain": "Django"
    },
    {
        "title": "Quelles instructions créent et sauvegardent un objet Django en base ?",
        "description": "Quelles instructions créent et sauvegardent un objet Django en base ?",
        "explanation": "On instancie le modèle puis on appelle save(), ou on utilise Model.objects.create().",
        "allow_multiple_correct": True,
        "subject_names": ["Django – Modèles & ORM"],
        "answer_options": [
            {
                "content": "obj = MonModel(...); obj.save()",
                "is_correct": True,
                "sort_order": 1,
            },
            {
                "content": "MonModel.objects.create(...)",
                "is_correct": True,
                "sort_order": 2,
            },
            {
                "content": "MonModel.save(obj)",
                "is_correct": False,
                "sort_order": 3,
            },
        ],
        "domain": "Django"
    },
    {
        "title": "Quelle commande applique les migrations en Django ?",
        "description": "Quelle commande applique les migrations en Django ?",
        "explanation": "La commande est `python manage.py migrate`.",
        "allow_multiple_correct": False,
        "subject_names": ["Django – Modèles & ORM"],
        "answer_options": [
            {"content": "python manage.py makemigrations", "is_correct": False, "sort_order": 1},
            {"content": "python manage.py migrate", "is_correct": True, "sort_order": 2},
            {"content": "python manage.py runserver", "is_correct": False, "sort_order": 3},
        ],
        "domain": "Django"
    },
    {
        "title": "Quels éléments sont typiquement impliqués dans une relation ManyToMany ?",
        "description": "",
        "explanation": "Une relation ManyToMany relie des instances de deux modèles via une table d’association.",
        "allow_multiple_correct": True,
        "subject_names": ["Django – Modèles & ORM"],
        "answer_options": [
            {
                "content": "Deux modèles liés et éventuellement un modèle intermédiaire.",
                "is_correct": True,
                "sort_order": 1,
            },
            {
                "content": "Un seul modèle et une clé primaire auto-incrémentée.",
                "is_correct": False,
                "sort_order": 2,
            },
            {
                "content": "Une table d’association gérée automatiquement ou via through=…",
                "is_correct": True,
                "sort_order": 3,
            },
        ],
        "domain": "Django"
    },
    {
        "title": "Quel est le rôle principal d’un serializer dans Django REST Framework ?",
        "description": "Quel est le rôle principal d’un serializer dans Django REST Framework ?",
        "explanation": "Les serializers transforment les instances de modèles en JSON (et inversement) et valident les données.",
        "allow_multiple_correct": True,
        "subject_names": ["Django – API REST"],
        "answer_options": [
            {
                "content": "Convertir les objets Python en représentations JSON.",
                "is_correct": True,
                "sort_order": 1,
            },
            {
                "content": "Valider les données d’entrée.",
                "is_correct": True,
                "sort_order": 2,
            },
            {
                "content": "Gérer le routage des URLs.",
                "is_correct": False,
                "sort_order": 3,
            },
        ],
        "domain": "Django"
    },
    {
        "title": "Quelles méthodes HTTP sont considérées comme 'safe' par DRF ?",
        "description": "Quelles méthodes HTTP sont considérées comme 'safe' par DRF ?",
        "explanation": "Les méthodes GET, HEAD et OPTIONS sont considérées comme safe.",
        "allow_multiple_correct": True,
        "subject_names": ["Django – API REST"],
        "answer_options": [
            {"content": "GET", "is_correct": True, "sort_order": 1},
            {"content": "HEAD", "is_correct": True, "sort_order": 2},
            {"content": "OPTIONS", "is_correct": True, "sort_order": 3},
            {"content": "POST", "is_correct": False, "sort_order": 4},
            {"content": "DELETE", "is_correct": False, "sort_order": 5},
        ],
        "domain": "Django"
    },
    {
        "title": "Quel code de statut HTTP correspond à 'Created' ?",
        "description": "Quel code de statut HTTP correspond à 'Created' ?",
        "explanation": "Le code 201 signifie que la ressource a été créée.",
        "allow_multiple_correct": False,
        "subject_names": ["Django – API REST"],
        "answer_options": [
            {"content": "200", "is_correct": False, "sort_order": 1},
            {"content": "201", "is_correct": True, "sort_order": 2},
            {"content": "204", "is_correct": False, "sort_order": 3},
        ],
        "domain": "Django"
    },
    {
        "title": "Pour s’authentifier via JWT, quelles informations sont envoyées au endpoint de login ?",
        "description": "Pour s’authentifier via JWT, quelles informations sont envoyées au endpoint de login ?",
        "explanation": "On envoie généralement username et password dans le corps de la requête POST.",
        "allow_multiple_correct": True,
        "subject_names": ["Django – API REST"],
        "answer_options": [
            {"content": "Le nom d’utilisateur", "is_correct": True, "sort_order": 1},
            {"content": "Le mot de passe", "is_correct": True, "sort_order": 2},
            {
                "content": "Le mot de passe en clair dans l’URL (query string)",
                "is_correct": False,
                "sort_order": 3,
            },
        ],
        "domain": "Django"
    },
    {
        "title": "Sur un endpoint detail d’un ModelViewSet DRF, quels verbes HTTP sont typiquement permis ?",
        "description": "Sur un endpoint detail d’un ModelViewSet DRF, quels verbes HTTP sont typiquement permis ?",
        "explanation": "Par défaut : GET, PUT, PATCH, DELETE (et HEAD/OPTIONS implicites).",
        "allow_multiple_correct": True,
        "subject_names": ["Django – API REST"],
        "answer_options": [
            {"content": "GET", "is_correct": True, "sort_order": 1},
            {"content": "PUT", "is_correct": True, "sort_order": 2},
            {"content": "PATCH", "is_correct": True, "sort_order": 3},
            {"content": "DELETE", "is_correct": True, "sort_order": 4},
            {"content": "CONNECT", "is_correct": False, "sort_order": 5},
        ],
        "domain": "Django"
    },
]

# 4 quiz : 2 en mode practice, 2 en mode exam
# question_indexes : indices dans la liste des questions (0-based)
QUIZZES_DEF: List[Dict[str, Any]] = [
    {
        "title": "Scrum Practice 1",
        "description": "Quiz d’entraînement sur les bases de Scrum.",
        "mode": "practice",
        "question_indexes": [0, 1, 2, 3, 4],
        "domain": "Scrum",
    },
    {
        "title": "Django Practice 1",
        "description": "Quiz d’entraînement sur Django (modèles et API).",
        "mode": "practice",
        "question_indexes": [10, 11, 12, 13, 14],
        "domain": "Django",
    },
    {
        "title": "Scrum Exam 1",
        "description": "Quiz d’examen sur Scrum.",
        "mode": "exam",
        "question_indexes": [5, 6, 7, 8, 9],
        "domain": "Scrum",
    },
    {
        "title": "Django Exam 1",
        "description": "Quiz d’examen sur Django.",
        "mode": "exam",
        "question_indexes": [15, 16, 17, 18, 19],
        "domain": "Django",
    },
]


def get_url(base_url, path):
    return base_url.rstrip("/") + path


# ============================================================
# UTILITAIRE : LIRE LES ENDPOINTS DANS LE YAML
# ============================================================

def load_openapi_paths(openapi_path: str) -> Dict[str, str]:
    """
    Lit le fichier OpenAPI (YAML) et essaie d'en déduire les chemins
    pour :
      - token
      - subject
      - question
      - quiz
      - user
    """
    path = pathlib.Path(openapi_path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier OpenAPI introuvable : {openapi_path}")

    with path.open("r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    paths = spec.get("paths", {})
    result = {
        "token": None,
        "subject": None,
        "question": None,
        "domain": None,
        "quiz": None,
        "user": None,
    }

    for p in paths.keys():
        if "token" in p and result["token"] is None:
            result["token"] = p
        if "/subject" in p and result["subject"] is None:
            result["subject"] = p
        if "/question" in p and result["question"] is None:
            result["question"] = p
        if "/domain" in p and result["domain"] is None:
            result["domain"] = p
        if "/quiz" in p and result["quiz"] is None:
            result["quiz"] = p
        if "/user" in p and result["user"] is None:
            result["user"] = p

    for key, value in result.items():
        if value is None:
            raise RuntimeError(f"Impossible de trouver le chemin '{key}' dans le fichier OpenAPI.")

    print("Chemins OpenAPI détectés :")
    for k, v in result.items():
        print(f" - {k}: {v}")

    return result


# ============================================================
# FONCTIONS UTILITAIRES REST
# ============================================================

def get_access_token(base_url: str, token_path: str) -> str:
    """Récupère un token JWT (SimpleJWT) pour l'admin."""
    url = get_url(base_url, token_path)
    payload = {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    resp = requests.post(url, json=payload)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Échec de l'authentification ({resp.status_code}): {resp.text}"
        )
    data = resp.json()
    access = data.get("access") or data.get("access_token")
    if not access:
        raise RuntimeError("Réponse token sans champ 'access': " + str(data))
    return access


def auth_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


# ============================================================
# SUBJECTS
# ============================================================

def find_subject_by_name(
        base_url: str,
        subject_path: str,
        token: str,
        name: str,
) -> Optional[Dict[str, Any]]:
    """
    Cherche un Subject par name via l'API :
      GET /api/subject/

    Compatible pagination (results / next).
    """
    headers = auth_headers(token)
    url = base_url.rstrip("/") + subject_path
    params = {}

    while url:
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Erreur lors de la recherche du Subject {name!r} "
                f"({resp.status_code}): {resp.text}"
            )

        data = resp.json()

        # DRF paginé ou non
        if isinstance(data, dict) and "results" in data:
            items = data["results"]
            next_url = data.get("next")
        else:
            items = data
            next_url = None

        for item in items:
            if item.get("name") == name:
                return item

        url = next_url

    return None


def create_subjects(
        base_url: str,
        subject_path: str,
        token: str,
        domain_by_name: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """
    Crée les 4 Subject via l'API, en évitant les doublons.
    Retourne un dict {name: subject_json}.
    """
    headers = auth_headers(token)
    result: Dict[str, Dict[str, Any]] = {}

    print("=== Création des subjects ===")
    for subj in SUBJECTS_DEF:
        name = subj["name"]
        description = subj.get("description", "")
        domain = domain_by_name[subj.get("domain")]
        # 1) On regarde s'il existe déjà
        existing = find_subject_by_name(base_url, subject_path, token, name)
        if existing:
            print(f" - Subject déjà existant: {existing['id']} {existing['name']}")
            result[name] = existing
            continue

        # 2) Sinon on le crée
        payload = {
            "name": name,
            "description": description,
            "domain": domain["id"],
        }
        url = get_url(base_url, subject_path)
        resp = requests.post(url, json=payload, headers=headers)
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Erreur création Subject {name!r} ({resp.status_code}): {resp.text}"
            )
        data = resp.json()
        result[name] = data
        print(f" - Subject créé: {data['id']} {data['name']}")

    return result


# ============================================================
# DOMAINS
# ============================================================

def find_domain_by_name(
        base_url: str,
        domain_path: str,
        token: str,
        name: str,
) -> Optional[Dict[str, Any]]:
    """
    Cherche un Subject par name via l'API :
      GET /api/subject/

    Compatible pagination (results / next).
    """
    headers = auth_headers(token)
    url = base_url.rstrip("/") + domain_path
    params = {}

    while url:
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Erreur lors de la recherche du Domain {name!r} "
                f"({resp.status_code}): {resp.text}"
            )

        data = resp.json()

        # DRF paginé ou non
        if isinstance(data, dict) and "results" in data:
            items = data["results"]
            next_url = data.get("next")
        else:
            items = data
            next_url = None

        for item in items:
            if item.get("name") == name:
                return item

        url = next_url

    return None


def create_domains(
        base_url: str,
        domain_path: str,
        token: str,
) -> Dict[str, Dict[str, Any]]:
    headers = auth_headers(token)
    result: Dict[str, Dict[str, Any]] = {}

    print("=== Création des domain ===")
    for subj in DOMAIN_DEF:
        name = subj["name"]
        description = subj.get("description", "")
        # 1) On regarde s'il existe déjà
        existing = find_domain_by_name(base_url, domain_path, token, name)
        if existing:
            print(f" - Domain déjà existant: {existing['id']} {existing['name']}")
            result[name] = existing
            continue

        # 2) Sinon on le crée
        payload = {
            "name": name,
            "description": description,
        }
        url = get_url(base_url, domain_path)
        resp = requests.post(url, json=payload, headers=headers)
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Erreur création Domain {name!r} ({resp.status_code}): {resp.text}"
            )
        data = resp.json()
        result[name] = data
        print(f" - Domain créé: {data['id']} {data['name']}")

    return result


# ============================================================
# QUESTIONS
# ============================================================

def find_question_by_title_and_subjects(
        base_url: str,
        question_path: str,
        token: str,
        title: str,
        subject_ids: List[int],
) -> Optional[Dict[str, Any]]:
    """
    Cherche une Question existante ayant le même title ET exactement le même set de subjects.
    GET /api/question/ puis filtrage côté client.

    Compatible pagination (results / next).
    """
    headers = auth_headers(token)
    url = get_url(base_url, question_path)
    params = {}
    wanted_subjects = set(subject_ids)
    while url:
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Erreur lors de la recherche de Question {title!r} ({resp.status_code}): {resp.text}"
            )

        data = resp.json()

        if isinstance(data, dict) and "results" in data:
            items = data["results"]
            next_url = data.get("next")
        else:
            items = data
            next_url = None

        for item in items:
            if item.get("title") != title:
                continue
            existing_subject_ids = {s["id"] for s in item.get("subjects", [])}
            if existing_subject_ids == wanted_subjects:
                return item

        url = next_url

    return None


def create_questions(
        base_url: str,
        question_path: str,
        token: str,
        subjects_by_name: Dict[str, Dict[str, Any]],
        domain_by_name: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Crée les 20 Question via l'API, en utilisant subject_ids et answer_options.
    Évite les doublons sur (title + set(subjects)).
    Retourne la liste des questions (dans le même ordre que QUESTIONS_DEF).
    """
    headers = auth_headers(token)
    created_questions: List[Dict[str, Any]] = []

    print("\n=== Création des questions ===")
    for idx, qdef in enumerate(QUESTIONS_DEF):
        subject_ids: List[int] = []
        for name in qdef.get("subject_names", []):
            subj = subjects_by_name.get(name)
            if not subj:
                raise RuntimeError(f"Sujet {name!r} introuvable lors de la création des questions.")
            subject_ids.append(subj["id"])
        domain = domain_by_name[qdef.get("domain")]
        title = qdef["title"]

        # 1) Chercher si la question existe déjà
        existing = find_question_by_title_and_subjects(
            base_url,
            question_path,
            token,
            title=title,
            subject_ids=subject_ids,
        )
        if existing:
            created_questions.append(existing)
            print(f" - Question déjà existante: id={existing['id']} title={existing['title']!r}")
            continue

        # 2) Sinon, on la crée
        payload = {
            "title": qdef["title"],
            "description": qdef.get("description", ""),
            "explanation": qdef.get("explanation", ""),
            "allow_multiple_correct": qdef["allow_multiple_correct"],
            "subject_ids": subject_ids,
            "answer_options": qdef["answer_options"],
            "domain": domain["id"],
        }
        url = base_url.rstrip("/") + question_path
        resp = requests.post(url, json=payload, headers=headers)
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Erreur création Question {idx} ({resp.status_code}): {resp.text}"
            )
        data = resp.json()
        created_questions.append(data)
        print(f" - Question {idx + 1:02d} créée: id={data['id']} title={data['title']!r}")

    return created_questions


def get_questions(
        base_url: str,
        question_path: str,
        token: str,
) -> List[Dict[str, Any]]:
    headers = auth_headers(token)
    questions: List[Dict[str, Any]] = []
    url = base_url.rstrip("/") + question_path
    resp = requests.get(url, headers=headers)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Erreur récupération Question ({resp.status_code}): {resp.text}"
        )
    data = resp.json()
    for i in data:
        questions.append(i)
    return questions


# ============================================================
# QUIZZES
# ============================================================

def find_quiz_by_title_and_mode(
        base_url: str,
        quiz_path: str,
        token: str,
        title: str,
        mode: str,
) -> Optional[Dict[str, Any]]:
    """
    Cherche un Quiz existant ayant le même title et le même mode.
    GET /api/quiz/ puis filtrage côté client.
    """
    headers = auth_headers(token)
    url = get_url(base_url, quiz_path)
    params = {}
    while url:
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Erreur lors de la recherche du Quiz {title!r} ({resp.status_code}): {resp.text}"
            )

        data = resp.json()
        if isinstance(data, dict) and "results" in data:
            items = data["results"]
            next_url = data.get("next")
        else:
            items = data
            next_url = None

        for item in items:
            if item.get("title") == title and item.get("mode") == mode:
                return item

        url = next_url

    return None


def create_quiz(
        base_url: str,
        quiz_path: str,
        token: str,
        title: str,
        description: str,
        mode: str,
        domain: str,
        max_questions: int = 5,
) -> Dict[str, Any]:
    """
    Crée un Quiz via l'API si nécessaire (title + mode).
    """
    print("CREATE_QUIZ")
    headers = auth_headers(token)

    # 1) Chercher si le quiz existe déjà
    existing = find_quiz_by_title_and_mode(
        base_url,
        quiz_path,
        token,
        title=title,
        mode=mode,
    )
    if existing:
        print(f" - Quiz déjà existant: id={existing['id']} slug={existing['slug']} title={existing['title']!r}")
        return existing

    # 2) Sinon, on le crée
    payload = {
        "title": title,
        "description": title,
        "max_questions": max_questions,
        "active": True,
        "mode": mode,
        "domain": domain,
    }
    url = get_url(base_url, quiz_path)
    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Erreur création Quiz {title!r} ({resp.status_code}): {resp.text}"
        )
    data = resp.json()
    print(f" - Quiz créé: id={data['id']} slug={data['slug']} title={data['title']!r}")
    return data


def add_question_to_quiz(
        base_url: str,
        quiz_path: str,
        token: str,
        quiz_id: int,
        question_id: int,
        sort_order: int,
        weight: int = 1,
) -> Dict[str, Any]:
    """
    Ajoute ou met à jour une question dans un quiz :
    POST /api/quiz/{slug}/add-question/
    (quiz_path est normalement le prefixe /api/quiz/)
    """
    print("ADD_QUESTION_TO_QUIZ")
    headers = auth_headers(token)
    url = f"{base_url.rstrip('/')}{quiz_path}{quiz_id}/question/"
    payload = {
        "question_id": question_id,
        "sort_order": sort_order,
        "weight": weight,
    }
    print(url)
    print(payload)
    resp = requests.post(url, json=payload, headers=headers)
    print(resp.status_code)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Erreur add-question quiz={quiz_id!r}, question={question_id} "
            f"({resp.status_code}): {resp.text}"
        )
    data = resp.json()
    print(
        f"   -> Question {question_id} ajoutée au quiz {quiz_id} "
        f"(sort_order={sort_order}, weight={weight})"
    )
    return data


def create_quizzes_and_attach_questions(
        base_url: str,
        quiz_path: str,
        token: str,
        created_questions: List[Dict[str, Any]],
        domain_by_name: List[Dict[str, Any]],
):
    """
    Crée les 4 quiz (2 practice, 2 exam) et ajoute 5 questions dans chacun.
    `created_questions` doit être dans l'ordre de QUESTIONS_DEF.
    """
    print("\n=== Création des quiz et affectation des questions ===")
    q_ids = [q["id"] for q in created_questions]

    for quiz_def in QUIZZES_DEF:
        title = quiz_def["title"]
        description = quiz_def["description"]
        mode = quiz_def["mode"]
        question_indexes = quiz_def["question_indexes"]
        domain = domain_by_name[quiz_def["domain"]]["id"]

        quiz = create_quiz(
            base_url,
            quiz_path,
            token,
            title,
            description,
            mode,
            domain,
            max_questions=len(question_indexes),
        )
        quiz_slug = quiz["slug"]
        quiz_id = quiz["id"]

        for i, q_idx in enumerate(question_indexes, start=1):
            question_id = q_ids[q_idx]
            add_question_to_quiz(
                base_url,
                quiz_path,
                token,
                quiz_id,
                question_id,
                sort_order=i,
                weight=1,
            )


def create_user(base_url: str, quiz_user: str, username: str, password: str, email: str):
    url = f"{base_url.rstrip('/')}{quiz_user}"
    payload = {
        "username": username,
        "first_name": username,
        "last_name": username,
        "email": email,
        "password": password,
    }
    resp = requests.post(url, json=payload)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Erreur création user {username!r} ({resp.status_code}): {resp.text}"
        )
    data = resp.json()
    print(f" - Quiz créé: id={data['id']} username={data['username']}")
    return data


# ============================================================
# MAIN
# ============================================================

def main():
    # 0) On récupère les chemins à partir du YAML
    print("=== Lecture des chemins depuis le fichier OpenAPI ===")
    paths = load_openapi_paths(OPENAPI_PATH)
    token_path = paths["token"]
    subject_path = paths["subject"]
    domain_path = paths["domain"]
    question_path = paths["question"]
    quiz_path = paths["quiz"]
    quiz_template_path = "/api/quiz/template/"
    quiz_user = paths["user"]

    # 1) Créer Superuser et users
    print("\n=== Création user2 ===")
    # --------------------------- CREATE USER 2 -----------------------------------
    # create_user(BASE_URL, quiz_user, U2_USERNAME, U2_PASSWORD, U2_EMAIL)
    print("utilisateur créé.\n")

    # 2) Authentification
    print("\n=== Authentification admin ===")
    token = get_access_token(BASE_URL, token_path)
    print("Token obtenu.\n")

    # 3) Subjects
    domains_by_name = create_domains(BASE_URL, domain_path, token)
    subjects_by_name = create_subjects(BASE_URL, subject_path, token, domains_by_name)

    # 4) Questions
    created_questions = create_questions(BASE_URL, question_path, token, subjects_by_name, domains_by_name)

    # 5) Quiz + mapping questions
    created_questions = get_questions(BASE_URL, question_path, token)
    if not len(created_questions):
        print("Pas de questions")
        return None
    create_quizzes_and_attach_questions(BASE_URL, quiz_template_path, token, created_questions, domains_by_name)

    # 6) user1 crée un QuizSession
    # qs = create_quizzsession(
    #    BASE_URL,
    #    quizsession_path,
    #    U2_USERNAME,
    #    U2_PASSWORD)
    # )
    print("\n✅ Import terminé : 4 subjects, 20 questions, 4 quiz créés.")


if __name__ == "__main__":
    main()
    print("\n✅ terminé.")
