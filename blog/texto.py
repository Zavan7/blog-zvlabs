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

import html
import re
from typing import Any, NamedTuple

import markdown as md
import nh3
from django.utils.html import escape
from django.utils.safestring import SafeString, mark_safe
from markdown.extensions.toc import slugify

EXTENSOES = ["extra", "sane_lists", "toc"]

# Os ids dos subtítulos levam um prefixo para não repetir ids da página
# (``#comentarios``, ``#posts``, ``#conteudo``) quando o post tem um
# ``## Comentários``, por exemplo.
PREFIXO_ANCORA = "secao-"


def _ancora(valor: str, separador: str) -> str:
    """Gera o id de um subtítulo: o slug padrão do ``toc`` com prefixo.

    Args:
        valor: texto do subtítulo.
        separador: separador de palavras do ``toc``.

    Returns:
        O id, por exemplo ``secao-o-problema``.

    English:
        Builds a heading id: the ``toc`` default slug with a prefix.

        Args:
            valor: heading text.
            separador: ``toc`` word separator.

        Returns:
            The id, for example ``secao-o-problema``.
    """
    return PREFIXO_ANCORA + slugify(valor, separador)


CONFIG_EXTENSOES = {"toc": {"slugify": _ancora}}

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

# Bloco de código já sanitizado: <pre><code class="language-x">.
BLOCO_DE_CODIGO = re.compile(
    r'<pre><code(?: class="(?P<classe>[^"]*)")?>(?P<codigo>.*?)</code></pre>',
    re.DOTALL,
)
LINGUAGEM = re.compile(r"language-([\w+#-]+)")
# Abertura e fechamento de <h1> no HTML já limpo (ver converter_markdown).
TITULO_H1 = re.compile(r"<(/?)h1\b")


class ItemIndice(NamedTuple):
    """Uma entrada do índice "Neste post".

    English:
        One entry of the "In this post" table of contents.
    """

    ancora: str
    titulo: str


class Conversao(NamedTuple):
    """Resultado da conversão: HTML do post e itens do índice.

    English:
        Conversion result: post HTML and index items.
    """

    html: SafeString
    indice: list[ItemIndice]


def converter_markdown(texto: str) -> Conversao:
    """Converte Markdown em HTML limpo e monta o índice, numa só passada.

    O ``<h1>`` da página é o título do post, então um ``#`` no texto vira
    ``<h2>``, como um ``##``. A troca roda depois do ``nh3``, sobre tags
    que ele já validou (o código vem escapado e não casa).

    Args:
        texto: conteúdo em Markdown.

    Returns:
        HTML sanitizado (marcado como seguro) e os itens do índice.

    English:
        Converts Markdown into clean HTML and builds the index, in a single
        pass.

        The page ``<h1>`` is the post title, so a ``#`` in the text becomes
        ``<h2>``, like a ``##``. The swap runs after ``nh3``, on tags it has
        already validated (code comes escaped and does not match).

        Args:
            texto: Markdown content.

        Returns:
            Sanitized HTML (marked as safe) and the index items.
    """
    conversor = md.Markdown(
        extensions=EXTENSOES, extension_configs=CONFIG_EXTENSOES
    )
    bruto = conversor.convert(texto)
    limpo = nh3.clean(
        bruto,
        tags=TAGS_PERMITIDAS,
        attributes=ATRIBUTOS_PERMITIDOS,
        url_schemes={"http", "https", "mailto"},
        link_rel="noopener noreferrer",
    )
    sem_h1 = TITULO_H1.sub(r"<\1h2", limpo)
    com_codigo = BLOCO_DE_CODIGO.sub(_moldurar_codigo, sem_h1)
    tokens: list[dict[str, Any]] = getattr(conversor, "toc_tokens", [])
    return Conversao(
        mark_safe(com_codigo),  # noqa: S308 - saída já sanitizada pelo nh3
        _titulos_de_secao(tokens),
    )


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
    return converter_markdown(texto).html


def indice_markdown(texto: str) -> list[ItemIndice]:
    """Lista os títulos de seção (``#`` e ``##``) do post, na ordem do texto.

    As âncoras são as mesmas que a extensão ``toc`` põe nos ``<h2>`` de
    :func:`renderizar_markdown`, então os links do índice chegam neles.

    Args:
        texto: conteúdo em Markdown.

    Returns:
        Âncora e título de cada seção.

    English:
        Lists the post's section headings (``#`` and ``##``), in text order.

        The anchors are the same ones the ``toc`` extension puts on the
        ``<h2>`` of :func:`renderizar_markdown`, so the index links reach
        them.

        Args:
            texto: Markdown content.

        Returns:
            Anchor and title of each section.
    """
    return converter_markdown(texto).indice


def _titulos_de_secao(tokens: list[dict[str, Any]]) -> list[ItemIndice]:
    """Percorre a árvore do ``toc`` e devolve os títulos que viram ``<h2>``.

    Args:
        tokens: árvore ``toc_tokens`` da extensão ``toc``.

    Returns:
        Os itens de nível 1 e 2, na ordem do texto.

    English:
        Walks the ``toc`` tree and returns the headings that become
        ``<h2>``.

        Args:
            tokens: ``toc_tokens`` tree from the ``toc`` extension.

        Returns:
            The level-1 and level-2 items, in text order.
    """
    itens: list[ItemIndice] = []
    for token in tokens:
        if token["level"] <= 2:
            # O toc entrega o nome já escapado; o template escapa de novo.
            itens.append(ItemIndice(token["id"], html.unescape(token["name"])))
        itens.extend(_titulos_de_secao(token["children"]))
    return itens


def _moldurar_codigo(achado: re.Match[str]) -> str:
    """Põe um bloco de código na moldura do front-end de referência.

    Cada linha vira um ``<span class="l">`` (o CSS numera) e o topo mostra
    a linguagem e o botão "Copiar". Roda depois do ``nh3``: o conteúdo já
    está escapado e só esta marcação fixa é acrescentada.

    Args:
        achado: bloco ``<pre><code>`` encontrado no HTML limpo.

    Returns:
        O bloco com moldura, topo e linhas numeradas.

    English:
        Wraps a code block in the reference front-end frame.

        Each line becomes a ``<span class="l">`` (CSS numbers it) and the
        top shows the language and the "Copy" button. Runs after ``nh3``:
        the content is already escaped and only this fixed markup is added.

        Args:
            achado: ``<pre><code>`` block found in the clean HTML.

        Returns:
            The framed block, with top bar and numbered lines.
    """
    linguagem = LINGUAGEM.search(achado["classe"] or "")
    rotulo = escape(linguagem[1]) if linguagem else "código"
    linhas = achado["codigo"].removesuffix("\n").split("\n")
    corpo = "".join(f'<span class="l">{linha}</span>' for linha in linhas)
    return (
        '<figure class="codigo">'
        f'<figcaption class="codigo-topo"><span>{rotulo}</span>'
        '<button class="codigo-copiar" type="button" data-copiar hidden>'
        "Copiar</button></figcaption>"
        f'<pre class="codigo-bloco"><code>{corpo}</code></pre>'
        "</figure>"
    )
