from django.conf import settings
from django.apps import apps
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import QuerySet, Q

from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class CustomUser(AbstractUser):
    language = models.CharField(_("language"), max_length=8, choices=settings.LANGUAGES,
                                default=getattr(settings, "LANGUAGE_CODE", "en"))

    current_domain = models.ForeignKey(
        "domain.Domain",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="current_users",
    )

    # -------------------------
    # Helpers internes
    # -------------------------
    @staticmethod
    def _domain_model():
        # Évite les imports circulaires
        return apps.get_model("domain", "Domain")

    # -------------------------
    # Représentation
    # -------------------------
    def __str__(self):
        return self.get_display_name()

    def get_display_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name} ({self.username})"
        return self.username

    # -------------------------
    # Domain / permissions métier
    # -------------------------
    def can_manage_domain(self, domain) -> bool:
        """
        Retourne True si l'utilisateur peut "gérer" un Domain:
        - superuser => True
        - staff global => True (optionnel mais souvent souhaité)
        - owner du domain => True
        - membre de Domain.staff => True
        """
        if domain is None:
            return False

        if self.is_superuser or self.is_staff:
            return True

        # domain.owner_id est standard sur un ForeignKey
        if getattr(domain, "owner_id", None) == self.id:
            return True

        # Grâce à Domain.staff.related_name="managed_domains"
        # => self.managed_domains est disponible
        return self.managed_domains.filter(id=domain.id).exists()

    def get_manageable_domains(self, *, active_only: bool = False) -> QuerySet:
        """
        Retourne un QuerySet des domaines que le user peut gérer.
        Pour un staff global/superuser: tous les domaines.

        active_only=True => ne retourne que les domaines actifs.
        """
        Domain = self._domain_model()
        qs = Domain.objects.all()

        if active_only:
            qs = qs.filter(active=True)

        if self.is_superuser or self.is_staff:
            return qs.distinct()
        return qs.filter(Q(owner=self) | Q(staff=self)).distinct()

    def get_visible_domains(self, *, active_only: bool = True) -> QuerySet:
        """
        Alias "pratique": en général l’UI liste les domaines visibles/choisissables.
        Par défaut on ne montre que les domaines actifs.
        """
        return self.get_manageable_domains(active_only=active_only)

    def set_current_domain(self, domain, *, allow_none: bool = True, save: bool = True) -> None:
        """
        Setter sûr:
        - refuse un domain non gérable (sauf staff global/superuser via can_manage_domain)
        - allow_none permet de reset (domain=None)
        - save=True persiste en DB immédiatement
        """
        if domain is None:
            if not allow_none:
                raise ValueError("current_domain cannot be None.")
            self.current_domain = None
            if save:
                self.save(update_fields=["current_domain"])
            return

        if not self.can_manage_domain(domain):
            raise PermissionError("User cannot set this domain as current.")

        self.current_domain = domain
        if save:
            self.save(update_fields=["current_domain"])

    def ensure_current_domain_is_valid(self, *, auto_fix: bool = False, active_only: bool = True) -> bool:
        """
        Vérifie si current_domain est:
        - gérable par l'utilisateur
        - et (optionnel) actif

        Si auto_fix=True:
        - tente de mettre current_domain au premier domaine visible, sinon None
        """
        cd = self.current_domain
        if cd is None:
            if auto_fix:
                self.pick_default_current_domain(save=True, active_only=active_only)
            return True

        if active_only and hasattr(cd, "active") and cd.active is False:
            if auto_fix:
                self.pick_default_current_domain(save=True, active_only=active_only)
            return False

        if not self.can_manage_domain(cd):
            if auto_fix:
                self.pick_default_current_domain(save=True, active_only=active_only)
            return False

        return True

    def pick_default_current_domain(self, *, save: bool = True, active_only: bool = True):
        """
        Choisit un domaine par défaut :
        - premier domaine visible (actif si active_only=True)
        - sinon None
        """
        qs = self.get_visible_domains(active_only=active_only).order_by("translations__name", "id").distinct()
        domain = qs.first()
        self.current_domain = domain
        if save:
            self.save(update_fields=["current_domain"])
        return domain

    # -------------------------
    # Validation modèle
    # -------------------------
    def clean(self):
        """
        Validation côté modèle (utile en admin et parfois en tests).
        Interdit current_domain si non gérable, sauf staff global/superuser.
        """
        super().clean()

        if self.current_domain is None:
            return

        if not self.can_manage_domain(self.current_domain):
            raise ValidationError({"current_domain": "This domain is not manageable by the user."})

    # -------------------------
    # Qualité de vie (facultatif)
    # -------------------------
    @property
    def current_domain_id_safe(self):
        return self.current_domain_id  # None ou int

    @property
    def has_current_domain(self) -> bool:
        return self.current_domain_id is not None

