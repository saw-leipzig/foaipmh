"""Fedora OAI-PMH Django app config."""

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class FedoraOAIPMHConfig(AppConfig):
    """Fedora OAI-PMH app config."""

    name = "foaipmh"
    verbose_name = _("Fedora OAI-PMH")
    verbose_name_plural = _("Fedora OAI-PMHs")
