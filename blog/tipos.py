"""Tipos auxiliares para o mypy.

English:
    Helper types for mypy.
"""

from django.contrib.auth.models import User
from django.http import HttpRequest


class RequisicaoAutenticada(HttpRequest):
    """Requisição de uma view protegida por login.

    No ``HttpRequest`` comum, ``request.user`` pode ser anônimo. Atrás do
    ``@login_required`` nunca é; este tipo diz isso ao mypy.

    English:
        Request of a login-protected view.

        In a plain ``HttpRequest``, ``request.user`` may be anonymous.
        Behind ``@login_required`` it never is; this type tells mypy so.
    """

    user: User
