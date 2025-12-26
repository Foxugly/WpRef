import random
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


@dataclass(frozen=True)
class ApiPaths:
    token: str = "/api/token/"
    quiz_create_from_template: str = "/api/quiz/"
    quiz_start: str = "/api/quiz/{quiz_id}/start/"
    quiz_close: str = "/api/quiz/{quiz_id}/close/"
    quiz_details: str = "/api/quiz/{quiz_id}/"  # retrieve quiz + questions (si ton serializer les renvoie)
    quiz_answer: str = "/api/quiz/{quiz_id}/answer/"  # nested answers list/create


class ApiClient:
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.paths = ApiPaths()

    def set_bearer(self, token: str) -> None:
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def url(self, path: str, **kwargs) -> str:
        return f"{self.base_url}{path.format(**kwargs)}"

    def request_json(self, method: str, path: str, *, json: Optional[dict] = None, **kwargs) -> Dict[str, Any]:
        url = self.url(path, **kwargs)
        resp = self.session.request(method, url, json=json, timeout=self.timeout)

        # gestion d’erreur robuste
        if resp.status_code >= 400:
            # essayer de récupérer un message DRF
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise RuntimeError(f"{method} {url} -> {resp.status_code}: {detail}")

        # certaines routes peuvent renvoyer 204
        if resp.status_code == 204 or not resp.content:
            return {}

        return resp.json()

    # -------------------------
    # AUTH
    # -------------------------
    def login(self, username: str, password: str) -> str:
        data = self.request_json("POST", self.paths.token, json={"username": username, "password": password})
        access = data.get("access") or data.get("access_token")
        if not access:
            raise RuntimeError(f"Token response missing 'access': {data}")
        return access

    # -------------------------
    # QUIZ
    # -------------------------
    def create_quiz(self, quiz_template_id: int) -> Dict[str, Any]:
        return self.request_json("POST", self.paths.quiz_create_from_template,
                                 json={"quiz_template_id": quiz_template_id})

    def start_quiz(self, quiz_id: str) -> Dict[str, Any]:
        return self.request_json("POST", self.paths.quiz_start, quiz={})

    def close_quiz(self, quiz_id: str) -> Dict[str, Any]:
        return self.request_json("POST", self.paths.quiz_close, quiz_id=quiz_id)

    def quiz_details(self, quiz_id: str) -> Dict[str, Any]:
        return self.request_json("GET", self.paths.quiz_details, quiz_id=quiz_id)

    # -------------------------
    # ANSWERS
    # -------------------------
    def post_answer(self, quiz_id: str, *, question_order: int = None, question_id: int = None,
                    selected_options=None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"selected_options": selected_options or []}

        # tu acceptes question_order et/ou question_id (cohérence gérée serveur)
        if question_order is not None:
            payload["question_order"] = question_order
        if question_id is not None:
            payload["question_id"] = question_id

        return self.request_json("POST", self.paths.quiz_answer, json=payload, quiz_id=quiz_id)

    def list_answers(self, quiz_id: str) -> Dict[str, Any]:
        return self.request_json("GET", self.paths.quiz_answer, quiz_id=quiz_id)


def answer_quiz_randomly(api: ApiClient, quiz_id: str) -> None:
    """
    Exemple: récupère le quiz (qui contient 'questions'), choisit une option random par question,
    et poste la réponse via question_order (plus naturel pour ton UI).
    """
    details = api.quiz_details(quiz_id)
    questions = details.get("questions", [])

    if not questions:
        raise RuntimeError("Le endpoint quiz_details ne renvoie pas de champ 'questions'. Vérifie ton QuizSerializer.")

    for qq in questions:
        q = qq.get("question") or {}
        title = q.get("title", "Sans titre")
        options = q.get("answer_options", [])

        if not options:
            print(f" - {title}: pas d'options → skip")
            continue

        option_id = random.choice([o["id"] for o in options])
        order = qq.get("sort_order") or qq.get("question_order")  # selon ton serializer
        if not order:
            raise RuntimeError(f"Impossible de trouver sort_order/question_order pour {qq}")

        api.post_answer(quiz_id, question_order=order, selected_options=[option_id])
        print(f"✅ Answered order={order} ({title}) with option={option_id}")


def main():
    BASE_URL = "http://localhost:8000"
    SU_USERNAME = "admin"
    SU_PASSWORD = "SuperPassword123"
    U2_USERNAME = "user2"
    U2_PASSWORD = "SuperPassword123"

    api = ApiClient(BASE_URL, timeout=10.0)

    # login user (tu n’utilises pas admin ensuite, donc je le laisse optionnel)
    token_user = api.login(U2_USERNAME, U2_PASSWORD)
    api.set_bearer(token_user)

    # create quiz
    quiz = api.create_quiz(quiz_template_id=1)
    quiz_id = str(quiz["id"])
    print(f"🎯 Quiz created: id={quiz_id}")

    # start quiz
    started = api.request_json("POST", api.paths.quiz_start, quiz_id=quiz_id, json={})
    print(f"▶️ Quiz started: id={started['id']} max_questions={started.get('max_questions')}")

    # answer
    answer_quiz_randomly(api, quiz_id)

    # close
    closed = api.close_quiz(quiz_id)
    print("⏹️ Quiz closed: ")
    for k, v in closed.items():
        if k == "questions":
            print("questions")
            print(i for i in v)
        else:
            print(k, v)

    # details
    details = api.quiz_details(quiz_id)
    print(f"📊 details:")
    for k, v in details.items():
        if k == "questions":
            print("questions :")
            for dict_qquestion in v:
                for k_qquestion, v_qquestion in dict_qquestion.items():
                    if k_qquestion == "question":
                        print("\tquestion :")
                        for k_question, v_question in v_qquestion.items():
                            if k_question == "answer_options":
                                print("\t\tanswer_options :")
                                for answer in v_question:
                                    print(f"\t\t\t{answer}")
                            else:
                                print(f"\t\t{k_question} : {v_question}")
                    else:
                        print(f"\t{k_qquestion} : {v_qquestion}")
        else:
            print(f"{k} : {v}")

    # list answers
    answers = api.list_answers(quiz_id)
    print(f"🧾 Answers: {answers}")

    print("✅ terminé.")


if __name__ == "__main__":
    main()
