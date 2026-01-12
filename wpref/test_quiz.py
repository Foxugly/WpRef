import random
from typing import Dict, Any, List

import requests

BASE_URL = "http://localhost:8000"

# --- identifiants de test ---
SU_USERNAME = "admin"
SU_PASSWORD = "SuperPassword123"

USER_USERNAME = "user2"
USER_PASSWORD = "SuperPassword123"

# --- endpoints ---
PATH_TOKEN = "/api/token/"

PATH_QUESTION = "/api/question/"  # QuestionViewSet
PATH_QUIZ_TEMPLATE = "/api/quiz/template/"  # QuizTemplateViewSet
PATH_QUIZ_TEMPLATE_CREATE = "/api/quiz/"
PATH_QUIZ_START = "/api/quiz/{q_id}/start/"
PATH_QUIZ_TEMPLATE_ADD_QUESTION = "/api/quiz/template/{qt_id}/question/"

PATH_QUIZ_QUESTION = "/api/quiz/{quiz_id}/answer/"
PATH_QUIZ_ANSWER = "/api/quiz/{quiz_id}/answer/"  # QuizQuestionAnswerViewSet (nested)
PATH_QUIZ_CLOSE = "/api/quiz/{quiz_id}/close/"


# ============================================================
# Helpers
# ============================================================

def get_url(path: str) -> str:
    return BASE_URL.rstrip("/") + path


def get_access_token(username: str, password: str) -> str:
    """Récupère un token JWT (SimpleJWT)."""
    url = get_url(PATH_TOKEN)
    resp = requests.post(url, json={"username": username, "password": password})
    if resp.status_code != 200:
        raise RuntimeError(f"Auth failed for {username}: {resp.status_code} {resp.text}")
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
# 1. Créer des Questions
# ============================================================

def create_question_as_admin(token: str, title: str, content: str, options: List[Dict[str, Any]],
                             media: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Crée une Question avec quelques AnswerOptions.
    On suppose un serializer de type :

    QuestionSerializer:
      - title (str)
      - content (str)
      - active (bool)
      - answer_options: [{ "content": "...", "is_correct": bool }, ...]

    Adapte si ton API est différente.
    """
    url = get_url(PATH_QUESTION)
    payload = {
        "title": title,
        "content": content,
        "active": True,
        "answer_options": options,
        "media": media,
    }
    resp = requests.post(url, json=payload, headers=auth_headers(token))
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Erreur création question: {resp.status_code} {resp.text}")
    data = resp.json()
    print(f"[Question] créée: id={data['id']} title={data['title']}")
    return data


# ============================================================
# 2. Créer un QuizTemplate + lier des questions
# ============================================================

def create_quiz_template_as_admin(token: str, title: str, max_questions: int) -> Dict[str, Any]:
    """
    Crée un QuizTemplate (modèle de quiz).
    """
    url = get_url(PATH_QUIZ_TEMPLATE)
    payload = {
        "title": title,
        "mode": "practice",
        "description": "Quiz de démo généré par script",
        "max_questions": max_questions,
        "permanent": True,
        "active": True,
        "with_duration": True,
        "duration": 10,
    }
    resp = requests.post(url, json=payload, headers=auth_headers(token))
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Erreur création QuizTemplate: {resp.status_code} {resp.text}")
    data = resp.json()
    print(f"[QuizTemplate] créé: id={data['id']} title={data['title']}")
    return data


def add_question_to_quiz_template_as_admin(token: str, quiz_template_id: int, question_id: int, sort_order: int,
                                           weight: int = 1) -> Dict[str, Any]:
    """
    Ajoute une QuizQuestion à un QuizTemplate via :
    POST /api/quiz/template/{qt_id}/questions/

    Payload attendu côté backend (en cohérence avec QuizQuestionSerializer) :
      { "question_id": <id>, "sort_order": <int>, "weight": <int> }
    """
    path = PATH_QUIZ_TEMPLATE_ADD_QUESTION.format(qt_id=quiz_template_id)
    url = get_url(path)
    payload = {
        "question_id": question_id,
        "sort_order": sort_order,
        "weight": weight,
    }
    resp = requests.post(url, json=payload, headers=auth_headers(token))
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Erreur ajout question au QuizTemplate: {resp.status_code} {resp.text}")
    data = resp.json()
    print(f"[QuizQuestion] ajoutée au template {quiz_template_id}: qquestion_id={data['id']}")
    return data


# ============================================================
# 3. Créer & démarrer un Quiz (session utilisateur)
# ============================================================

def start_quiz_from_template(token: str, quiz_template_id: int) -> Dict[str, Any]:
    """
    Crée et démarre un Quiz (session) pour l'utilisateur courant à partir d'un QuizTemplate :
    POST /api/quiz/template/{qt_id}/start/
    """
    path = PATH_QUIZ_TEMPLATE_CREATE
    url = get_url(path)
    resp = requests.post(url, json={"quiz_template_id": quiz_template_id}, headers=auth_headers(token))
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Erreur start quiz from template {quiz_template_id}: {resp.status_code} {resp.text}")
    data = resp.json()
    print(data)
    quiz_id = data["id"]
    path = PATH_QUIZ_START.format(q_id=quiz_id)  # /api/quiz/{id}/start/
    url = get_url(path)
    resp = requests.post(url, json={}, headers=auth_headers(token))
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Erreur start quiz from template {quiz_template_id}: {resp.status_code} {resp.text}")
    data = resp.json()
    print(f"[Quiz] session créée & démarrée: id={data['id']}")
    return data


# ============================================================
# 4. Récupérer les questions d'un QuizTemplate
# ============================================================

def get_quiz_question(token: str, quiz_id: int) -> Dict[str, Any]:
    """
    GET /api/quiz/{id}/details/

    On suppose que le serializer renvoie :
      - quiz_questions: [
            {
              "id": <qquestion_id>,
              "question": <question_id>,
              "question_title": "...",
              "sort_order": 1,
              "weight": 1
            },
            ...
        ]
    """
    url = get_url(PATH_QUIZ_QUESTION.format(quiz_id=quiz_id))
    print(url)
    resp = requests.get(url, headers=auth_headers(token))
    if resp.status_code != 200:
        raise RuntimeError(f"Erreur get QuizTemplate: {resp.status_code} {resp.text}")
    data = resp.json()
    print("[get_quiz_question]")
    print(data)
    return data


def get_question_detail(token: str, quiz_id: int, question_order: int) -> Dict[str, Any]:
    """
    GET /api/question/{id}/

    On suppose que la réponse contient :
      - answer_options: [
            { "id": ..., "content": "...", "is_correct": bool },
            ...
        ]
    """
    payload = {
        "question_order": question_order,
    }
    url = get_url(PATH_QUIZ_QUESTION.format(quiz_id=quiz_id))  # TODO intégrer quiz_id
    resp = requests.get(url, payload=payload, headers=auth_headers(token))
    if resp.status_code != 200:
        raise RuntimeError(f"Erreur get Question {question_order}: {resp.status_code} {resp.text}")
    return resp.json()


# ============================================================
# 5. Répondre aux questions : POST /api/quiz/{quiz_id}/answer/
# ============================================================

def answer_one_question(token: str, quiz_id: int, qquestion_id: int, question_order: int, selected_option_id: int) -> \
        Dict[str, Any]:
    """
    Envoie une réponse pour une question de ce quiz.

    On suppose que le QuizQuestionAnswerSerializer attend :
      {
        "qquestion": <qquestion_id>,
        "question_order": <int>,
        "selected_options": [<answer_option_id>]
      }
    """
    path = PATH_QUIZ_ANSWER.format(quiz_id=quiz_id)
    url = get_url(path)
    payload = {
        "qquestion": qquestion_id,
        "question_order": question_order,
        "selected_options": [selected_option_id],
    }
    resp = requests.post(url, json=payload, headers=auth_headers(token))
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Erreur envoi réponse (quiz={quiz_id}, qquestion={qquestion_id}): "
            f"{resp.status_code} {resp.text}"
        )
    data = resp.json()
    print(f"[Answer] enregistrée pour quiz={quiz_id}, question_order={question_order}")
    return data


def answer_all_questions_randomly(token: str, quiz_id: int) -> None:
    """
    Stratégie simple pour la démo :
      - On lit le détail du QuizTemplate pour récupérer les quiz_questions
      - Pour chaque QuizQuestion :
          - on récupère la Question + ses AnswerOptions
          - on choisit une option au hasard
          - on appelle POST /api/quiz/{quiz_id}/answer/
    """
    quiz_questions = get_quiz_question(token, quiz_id)
    print(f"Le template contient {len(quiz_questions)} questions.")

    for i, qq in enumerate(quiz_questions, start=1):
        print(qq)
        qquestion_id = qq["id"]
        question_id = qq["question"]
        question_detail = get_question_detail(token, quiz_id, i)
        options = question_detail.get("answer_options", [])

        if not options:
            print(f"⚠ Pas d'options pour question {question_id}, on saute.")
            continue

        option_ids = [opt["id"] for opt in options]
        selected_option_id = random.choice(option_ids)

        print(f"Question {i}: {qq['question_title']}")
        for opt in options:
            mark = "(choisie)" if opt["id"] == selected_option_id else ""
            print(f"  - [{opt['id']}] {opt['content']} {mark}")

        answer_one_question(
            token=token,
            quiz_id=quiz_id,
            qquestion_id=qquestion_id,
            question_order=i,
            selected_option_id=selected_option_id,
        )


# ============================================================
# 6. Clôturer le quiz
# ============================================================

def close_quiz(token: str, quiz_id: int) -> Dict[str, Any]:
    path = PATH_QUIZ_CLOSE.format(quiz_id=quiz_id)
    url = get_url(path)
    resp = requests.post(url, json={}, headers=auth_headers(token))
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Erreur close quiz {quiz_id}: {resp.status_code} {resp.text}")
    data = resp.json()
    print(f"[Quiz] clôturé: id={quiz_id}")
    return data


# ============================================================
# MAIN DEMO
# ============================================================

def main():
    # 1) Récupérer les tokens
    admin_token = get_access_token(SU_USERNAME, SU_PASSWORD)
    user_token = get_access_token(USER_USERNAME, USER_PASSWORD)

    # 2) Créer quelques questions (en admin)
    q1 = create_question_as_admin(
        admin_token,
        title="Capital de la Belgique ?",
        content="Quelle est la capitale de la Belgique ?",
        options=[
            {"content": "Bruxelles", "is_correct": True},
            {"content": "Anvers", "is_correct": False},
            {"content": "Liège", "is_correct": False},
        ],
        media=[
            {"kind": "external", "external_url": "https://new.example.com", "sort_order": 1},
            {"kind": "external", "external_url": "https://www.google.com", "sort_order": 2},
            {"kind": "external", "external_url": "https://www.yahoo.com", "sort_order": 3},
        ],
    )
    q2 = create_question_as_admin(
        admin_token,
        title="2 + 2 = ?",
        content="Combien font 2 + 2 ?",
        options=[
            {"content": "3", "is_correct": False},
            {"content": "4", "is_correct": True},
            {"content": "5", "is_correct": False},
        ],
        media=[]
    )

    # 3) Créer un QuizTemplate
    qt = create_quiz_template_as_admin(
        admin_token,
        title="Quiz de démo",
        max_questions=2,
    )
    qt_id = qt["id"]

    # 4) Ajouter les questions au QuizTemplate
    add_question_to_quiz_template_as_admin(admin_token, qt_id, q1["id"], sort_order=1, weight=1)
    add_question_to_quiz_template_as_admin(admin_token, qt_id, q2["id"], sort_order=2, weight=1)

    # 5) Créer & démarrer un Quiz pour l'utilisateur "user2"
    quiz = start_quiz_from_template(user_token, qt_id)
    quiz_id = quiz["id"]
    print(f"Quiz session id = {quiz_id}")

    # 6) Répondre aux questions (au hasard)
    answer_all_questions_randomly(user_token, quiz_id)

    # 7) Clôturer le quiz
    close_quiz(user_token, quiz_id)

    print("\n✅ Script terminé.")


if __name__ == "__main__":
    main()
