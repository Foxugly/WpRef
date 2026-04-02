from ._common import build_user_token_link, frontend_url, send_plaintext_email


def build_registration_confirmation_body(user) -> str:
    confirmation_link = build_user_token_link("/user/confirm-email", user)
    return (
        f"Bonjour {user.get_display_name()},\n\n"
        "Merci pour votre inscription sur WpRef.\n"
        f"Confirmez votre adresse email : {confirmation_link}\n\n"
        f"Connexion : {frontend_url('/login')}\n"
    )


def send_registration_confirmation_email(user) -> None:
    if not getattr(user, "email", None):
        return
    send_plaintext_email(
        "WpRef - confirmez votre inscription",
        build_registration_confirmation_body(user),
        [user.email],
    )


def build_password_reset_body(user) -> str:
    reset_link = build_user_token_link("/user/reset-password", user)
    return (
        f"Bonjour {user.get_display_name()},\n\n"
        "Vous avez demande la reinitialisation de votre mot de passe.\n"
        f"Reinitialisez votre mot de passe : {reset_link}\n\n"
        f"Connexion : {frontend_url('/login')}\n"
    )


def send_password_reset_email(user) -> None:
    if not getattr(user, "email", None):
        return
    send_plaintext_email(
        "WpRef - reinitialisation du mot de passe",
        build_password_reset_body(user),
        [user.email],
    )
