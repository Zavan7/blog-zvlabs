"""Conversão segura de Markdown para HTML.

O ``markdown`` gera o HTML e o ``nh3`` remove o que não está na lista de
permitidos (``<script>``, ``onclick``, ``javascript:``). Mesmo com só o dono
escrevendo posts, o HTML final é limpo: um texto colado de outro lugar pode
trazer código.

English:
    Safe Markdown to HTML conversion.

    ``markdown`` produces the HTML and ``nh3`` strips anything outside the
    allow list (``<script>``, ``onclick``, ``javascript:``). Even with only
    the owner writing posts, the final HTML is cleaned: text pasted from
    elsewhere may carry code.
"""

import markdown as md
import nh3
from django.utils.safestring import SafeString, mark_safe

EXTENSOES = ["extra", "sane_lists", "toc"]

TAGS_PERMITIDAS = {
    "a", "abbr", "blockquote", "br", "code", "dd", "del", "div", "dl",
    "dt", "em", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "img", "li",
    "ol", "p", "pre", "span", "strong", "sub", "sup", "table", "tbody",
    "td", "th", "thead", "tr", "ul",
}  # fmt: skip

ATRIBUTOS_PERMITIDOS = {
    "a": {"href", "title"},
    "img": {"src", "alt", "title", "width", "height"},
    "code": {"class"},
    "div": {"class"},
    "span": {"class"},
    "th": {"align"},
    "td": {"align"},
    "h1": {"id"},
    "h2": {"id"},
    "h3": {"id"},
    "h4": {"id"},
    "h5": {"id"},
    "h6": {"id"},
}


def renderizar_markdown(texto: str) -> SafeString:
    """Converte Markdown em HTML limpo, pronto para o template.

    Args:
        texto: conteúdo em Markdown.

    Returns:
        HTML sanitizado e marcado como seguro para o template.

    English:
        Converts Markdown into clean HTML, ready for the template.

        Args:
            texto: Markdown content.

        Returns:
            Sanitized HTML marked as safe for the template.
    """
    html = md.markdown(texto, extensions=EXTENSOES)
    limpo = nh3.clean(
        html,
        tags=TAGS_PERMITIDAS,
        attributes=ATRIBUTOS_PERMITIDOS,
        url_schemes={"http", "https", "mailto"},
        link_rel="noopener noreferrer",
    )
    return mark_safe(limpo)  # noqa: S308 - saída já sanitizada pelo nh3
