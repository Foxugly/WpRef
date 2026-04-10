from rest_framework.throttling import AnonRateThrottle
from rest_framework.throttling import UserRateThrottle


class TokenObtainRateThrottle(AnonRateThrottle):
    scope = "token_obtain"


class PasswordResetRateThrottle(AnonRateThrottle):
    scope = "password_reset"


class PasswordResetConfirmRateThrottle(AnonRateThrottle):
    scope = "password_reset_confirm"


class EmailConfirmRateThrottle(AnonRateThrottle):
    scope = "email_confirm"


class QuizAnswerRateThrottle(UserRateThrottle):
    scope = "quiz_answer"
