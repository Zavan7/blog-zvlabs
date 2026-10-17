"""Dados que todo template precisa (cabeçalho).

English:
    Data every template needs (header).
"""

from typing import Any

from django.conf import settings
from django.http import HttpRequest
from django.utils.functional import SimpleLazyObject

from blog.models import Inscrito


def inscricao(request: HttpRequest) -> dict[str, Any]:
    """Disponibiliza a inscrição ativa da pessoa logada no cabeçalho.

    A consulta é preguiçosa: só roda se o template usar
    ``inscricao_ativa``. Páginas que não usam, como as do admin, não pagam
    a consulta.

    Args:
        request: requisição atual.

    Returns:
        ``{"inscricao_ativa": Inscrito}`` ou ``None`` quando a pessoa não
        está logada ou não está inscrita.

    English:
        Makes the logged-in person's active subscription available to the
        header.

        The query is lazy: it only runs if the template uses
        ``inscricao_ativa``. Pages that do not, like the admin ones, skip
        the query.

        Args:
            request: current request.

        Returns:
            ``{"inscricao_ativa": Inscrito}`` or ``None`` when the person
            is not logged in or not subscribed.
    """
    if not request.user.is_authenticated:
        return {"inscricao_ativa": None}
    usuario_id = request.user.pk
    return {
        "inscricao_ativa": SimpleLazyObject(
            lambda: Inscrito.objects.filter(
                usuario_id=usuario_id, ativo=True
            ).first()
        )
    }


def links(request: HttpRequest) -> dict[str, str]:
    """Disponibiliza o endereço do portfólio para o menu e o rodapé.

    Args:
        request: requisição atual.

    Returns:
        ``{"portfolio_url": str}``; vazio quando não configurado, e então
        o template esconde os links.

    English:
        Makes the portfolio address available to the menu and footer.

        Args:
            request: current request.

        Returns:
            ``{"portfolio_url": str}``; empty when not configured, and the
            template then hides the links.
    """
    return {"portfolio_url": settings.PORTFOLIO_URL}
