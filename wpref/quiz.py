import random
from typing import Dict, Any

import requests

BASE_URL = "http://localhost:8000"  # ou "http://127.0.0.1:8000"

U2_USERNAME = "user2"
U2_EMAIL = "user2@example.com"
U2_PASSWORD = "SuperPassword123"

path_token = "/api/token/"
path_quiz_creation = "/api/quiz/<SLUG>/start/"
# On utilise maintenant /attempt/ aussi bien pour GET (question + état) que pour POST (réponse)
path_quiz_attempt = "/api/quiz/<QUIZ_ID>/attempt/<QUESTION_ORDER>/"
path_quiz_close = "/api/quiz/<QUIZ_ID>/close/"
path_quiz_summary = "/api/quiz/<QUIZ_ID>/summary/"

def get_json_credential(username, password):
    return {"username": username, "password": password}

def get_url(base_url, path):
    return base_url.rstrip("/") + path

def get_access_token(base_url: str, token_path: str) -> str:
    """Récupère un token JWT (SimpleJWT) du user2."""
    url = get_url(base_url, token_path)
    resp = requests.post(url, json=get_json_credential(U2_USERNAME, U2_PASSWORD))
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
# CREATE QUIZ
# ============================================================

def create_quiz_session(base_url: str, token: str, quiz_slug: str) -> Dict[str, Any]:
    headers = auth_headers(token)
    print("=== Création du quiz ===")
    url = base_url.rstrip("/") + path_quiz_creation.replace("<SLUG>", quiz_slug)
    json_dict = {}
    resp = requests.post(url, json=json_dict, headers=headers)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Erreur création quiz {quiz_slug!r} ({resp.status_code}): {resp.text}"
        )
    data = resp.json()
    print(f" - quiz créé: {data['id']})")
    return data


# ============================================================
# QUESTIONS (GET via /attempt/)
# ============================================================

def get_quiz_question(base_url: str, token: str, quiz_id: str, question_i: int) -> Dict[str, Any]:
    """
    Récupère la question + options + is_selected (+ is_correct si applicable)
    via GET /api/quiz/<QUIZ_ID>/attempt/<QUESTION_ORDER>/
    """
    headers = auth_headers(token)
    url = base_url.rstrip("/") + path_quiz_attempt.replace("<QUIZ_ID>", quiz_id).replace(
        "<QUESTION_ORDER>", str(question_i)
    )
    resp = requests.get(url, headers=headers)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Erreur réception question {quiz_id!r}/{question_i}/  ({resp.status_code}): {resp.text}"
        )
    return resp.json()

def get_quiz_session_question(base_url: str, token: str, quiz_id: str,question_i: int):
    data = get_quiz_question(base_url, token, quiz_id, question_i)
    print(f"{data['title']}")
    for a in data["options"]:
        print(a)
        line = f"[{a['id']}] {a['content']}"
        if "is_correct" in a and a["is_correct"]:
            line += "  (CORRECT)"
        if a.get("is_selected"):
            line += "  [YOU]"
        print(line)


def set_quiz_question_response(base_url: str, token: str, quiz_id: str, question_i: int, option_id: int) -> Dict[str, Any]:
    """
    Envoie la réponse pour une question via POST /attempt/,
    en respectant ton API : { "selected_option_ids": [<id>] }
    """
    headers = auth_headers(token)
    url = base_url.rstrip("/") + path_quiz_attempt.replace("<QUIZ_ID>", quiz_id).replace(
        "<QUESTION_ORDER>", str(question_i)
    )
    print(url)
    payload = {
        "selected_option_ids": [option_id]
    }
    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Erreur réponse question {quiz_id!r}/{question_i}/  ({resp.status_code}): {resp.text}"
        )
    return resp.json()


def answer_to_quiz_session_questions(base_url: str, token: str, quiz_id: str, n_questions: int) -> bool:
    """
    Pour chaque question, on récupère la question + options,
    on choisit une réponse aléatoire et on la poste.
    """
    print("answer_to_quiz_session_questions")
    print(base_url)
    print(token)
    print(quiz_id)
    print(n_questions)
    for i in range(n_questions):
        data = get_quiz_question(base_url, token, quiz_id, i + 1)
        print(f"Question {i + 1}/{n_questions} : {data['title']}")
        answers = []
        for a in data["options"]:
            print(f"[{a['id']}] {a['content']}")
            answers.append(a["id"])
        option_id = random.choice(answers)
        set_quiz_question_response(base_url, token, quiz_id, i + 1, option_id)
        get_quiz_session_question(base_url, token, quiz_id, i + 1)
    return True


# ============================================================
# CLOSE + SUMMARY + REVIEW
# ============================================================

def close_quiz_session(base_url: str, token: str, quiz_id: str) -> Dict[str, Any]:
    headers = auth_headers(token)
    url = base_url.rstrip("/") + path_quiz_close.replace("<QUIZ_ID>", quiz_id)
    print(url)
    resp = requests.post(url, headers=headers)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Erreur close question {quiz_id!r}  ({resp.status_code}): {resp.text}"
        )
    return resp.json()


def get_summary_quiz_session(base_url: str, token: str, quiz_id: str) -> Dict[str, Any]:
    headers = auth_headers(token)
    url = base_url.rstrip("/") + path_quiz_summary.replace("<QUIZ_ID>", quiz_id)
    print(url)
    resp = requests.get(url, headers=headers)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Erreur summary question {quiz_id!r}  ({resp.status_code}): {resp.text}"
        )
    return resp.json()


def get_quiz_session_questions(base_url: str, token: str, quiz_id: str, n_questions: int):
    """
    Relit toutes les questions (après clôture par exemple),
    pour afficher aussi les bonnes réponses (is_correct) si dispo.
    """
    for i in range(n_questions):
        print(f"Question {i + 1}/{n_questions}")
        get_quiz_session_question(base_url, token, quiz_id, i+1)


# ============================================================
# MAIN
# ============================================================

def main():
    # 1) Authentification
    print("\n=== Création quiz ===")
    token = get_access_token(BASE_URL, path_token)
    print("Token:", token)

    # 2) Démarrer une session de quiz pour le slug donné
    data = create_quiz_session(BASE_URL, token, "django-exam-1")
    quiz_session_id = data["id"]
    n_questions = data["n_questions"]
    print(data)
    print("quiz créé.\n")

    # 3) Répondre aux questions
    answer_to_quiz_session_questions(BASE_URL, token, quiz_session_id, n_questions)

    # 4) Clôturer
    data = close_quiz_session(BASE_URL, token, quiz_session_id)
    print("Close:", data)

    # 5) Résumé
    data = get_summary_quiz_session(BASE_URL, token, quiz_session_id)
    print("Summary:", data)

    # 6) Relire les questions + réponses + corrections
    get_quiz_session_questions(BASE_URL, token, quiz_session_id, n_questions)

    print("\n✅ terminé.")


if __name__ == "__main__":
    main()
