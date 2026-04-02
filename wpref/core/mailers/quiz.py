from ._common import format_datetime, frontend_url, send_plaintext_email


def build_quiz_assignment_body(quiz) -> str:
    user = quiz.user
    template = quiz.quiz_template
    deadline = template.ended_at or quiz.ended_at
    deadline_line = f"Deadline : {format_datetime(deadline)}\n" if deadline else ""
    return (
        f"Bonjour {user.get_display_name()},\n\n"
        f"Un quiz vous a ete assigne : {template.title}\n"
        f"{deadline_line}"
        f"Lien : {frontend_url(f'/quiz/{quiz.id}')}\n"
    )


def send_quiz_assignment_email(quiz) -> None:
    user = getattr(quiz, "user", None)
    template = getattr(quiz, "quiz_template", None)
    if not user or not template or not getattr(user, "email", None):
        return
    send_plaintext_email(
        "WpRef - nouveau quiz a completer",
        build_quiz_assignment_body(quiz),
        [user.email],
    )


def build_quiz_completed_body(quiz) -> str:
    template = quiz.quiz_template
    creator = template.created_by
    user = quiz.user
    return (
        f"Bonjour {creator.get_display_name()},\n\n"
        f"{user.get_display_name()} a cloture le quiz \"{template.title}\".\n"
        f"Lien : {frontend_url(f'/quiz/{quiz.id}')}\n"
    )


def send_quiz_completed_email(quiz) -> None:
    template = getattr(quiz, "quiz_template", None)
    creator = getattr(template, "created_by", None) if template else None
    user = getattr(quiz, "user", None)
    if not creator or not user or creator.id == user.id or not getattr(creator, "email", None):
        return
    send_plaintext_email(
        "WpRef - quiz cloture",
        build_quiz_completed_body(quiz),
        [creator.email],
    )
