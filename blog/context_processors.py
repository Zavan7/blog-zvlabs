"""Dados que todo template precisa (cabeçalho).

English:
    Data every template needs (header).
"""

from django.conf import settings
from django.http import HttpRequest

from blog.models import Inscrito


def inscricao(request: HttpRequest) -> dict[str, Inscrito | None]:
    """Disponibiliza a inscrição ativa da pessoa logada no cabeçalho.

    Args:
        request: requisição atual.

    Returns:
        ``{"inscricao_ativa": Inscrito}`` ou ``None`` quando a pessoa não
        está logada ou não está inscrita.

    English:
        Makes the logged-in person's active subscription available to the
        header.

        Args:
            request: current request.

        Returns:
            ``{"inscricao_ativa": Inscrito}`` or ``None`` when the person
            is not logged in or not subscribed.
    """
    if not request.user.is_authenticated:
        return {"inscricao_ativa": None}
    return {
        "inscricao_ativa": Inscrito.objects.filter(
            usuario_id=request.user.pk, ativo=True
        ).first()
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
