from django.contrib.auth import get_user_model
from django.db import transaction

from core.mailers import send_password_reset_email, send_registration_confirmation_email
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from .tokens import resolve_user_from_uid, token_is_valid

User = get_user_model()


def register_user(serializer):
    user = serializer.save()
    send_registration_confirmation_email(user)
    return user


def request_password_reset(email: str, request) -> None:
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        return

    user.must_change_password = True
    user.save(update_fields=["must_change_password"])
    send_password_reset_email(user)


def revoke_user_refresh_tokens(user) -> None:
    outstanding_tokens = OutstandingToken.objects.filter(user=user)
    for token in outstanding_tokens:
        BlacklistedToken.objects.get_or_create(token=token)


def confirm_password_reset(uid: str, token: str, new_password: str):
    user = resolve_user_from_uid(uid)
    if not token_is_valid(user, token):
        return None

    with transaction.atomic():
        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])
        revoke_user_refresh_tokens(user)
    return user


def confirm_email(uid: str, token: str):
    user = resolve_user_from_uid(uid)
    if not token_is_valid(user, token):
        return None

    if not user.email_confirmed:
        user.email_confirmed = True
        user.save(update_fields=["email_confirmed"])
    return user


def change_password(user, old_password: str, new_password: str) -> bool:
    if not user.check_password(old_password):
        return False

    with transaction.atomic():
        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])
        revoke_user_refresh_tokens(user)
    return True
