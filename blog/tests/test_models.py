"""Testes dos models e da conversão de Markdown.

English:
    Model and Markdown conversion tests.
"""

from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from blog.models import Post
from blog.tests.base import criar_post, criar_usuario, inscrever
from blog.texto import (
    Conversao,
    ItemIndice,
    indice_markdown,
    renderizar_markdown,
)


class PostTests(TestCase):
    """Regras de visibilidade do post.

    English:
        Post visibility rules.
    """

    autor: User

    @classmethod
    def setUpTestData(cls):
        """Cria o autor.

        English:
            Creates the author.
        """
        cls.autor = criar_usuario("vitor", superuser=True)

    def test_publicados_inclui_post_com_data_passada(self):
        """Post publicado com data passada aparece para os leitores.

        English:
            A published post with a past date is shown to readers.
        """
        post = criar_post(self.autor)
        self.assertIn(post, Post.objects.publicados())
        self.assertTrue(post.esta_publicado)

    def test_publicados_exclui_rascunho(self):
        """Rascunho nunca aparece.

        English:
            A draft never shows up.
        """
        post = criar_post(self.autor, publicado=False)
        self.assertNotIn(post, Post.objects.publicados())
        self.assertFalse(post.esta_publicado)

    def test_publicados_exclui_post_agendado(self):
        """Post publicado com data futura fica agendado.

        English:
            A published post with a future date stays scheduled.
        """
        post = criar_post(
            self.autor, publicado_em=timezone.now() + timedelta(days=1)
        )
        self.assertNotIn(post, Post.objects.publicados())
        self.assertFalse(post.esta_publicado)

    def test_get_absolute_url_usa_slug(self):
        """O endereço do post usa o slug.

        English:
            The post address uses the slug.
        """
        post = criar_post(self.autor, slug="meu-post")
        self.assertEqual(post.get_absolute_url(), "/posts/meu-post/")

    def test_conteudo_html_renderiza_markdown(self):
        """O conteúdo em Markdown vira HTML.

        English:
            Markdown content becomes HTML.
        """
        post = criar_post(self.autor)
        self.assertIn("<strong>forte</strong>", post.conteudo_html)

    def test_converte_markdown_uma_vez(self):
        """HTML e índice saem da mesma conversão.

        English:
            HTML and index come from the same conversion.
        """
        post = criar_post(self.autor)
        with mock.patch(
            "blog.models.converter_markdown",
            return_value=Conversao(renderizar_markdown("Oi"), []),
        ) as conversor:
            self.assertIn("Oi", post.conteudo_html)
            self.assertEqual(post.indice, [])
        conversor.assert_called_once_with(post.conteudo)

    def test_clean_preenche_data_do_publicado(self):
        """Publicado sem data recebe a data de agora na validação.

        English:
            A published post without a date gets the current date on
            validation.
        """
        post = Post(status=Post.Status.PUBLICADO, publicado_em=None)
        antes = timezone.now()
        post.clean()
        self.assertIsNotNone(post.publicado_em)
        assert post.publicado_em is not None  # para o mypy
        self.assertGreaterEqual(post.publicado_em, antes)

    def test_clean_nao_mexe_no_rascunho(self):
        """Rascunho continua sem data.

        English:
            A draft stays without a date.
        """
        post = Post(status=Post.Status.RASCUNHO, publicado_em=None)
        post.clean()
        self.assertIsNone(post.publicado_em)

    def test_banco_recusa_publicado_sem_data(self):
        """A constraint barra o que passar por fora do formulário.

        English:
            The constraint blocks whatever bypasses the form.
        """
        with self.assertRaises(IntegrityError), transaction.atomic():
            criar_post(self.autor, publicado_em=None)


class LeituraTests(TestCase):
    """Estimativa de tempo de leitura.

    English:
        Reading time estimate.
    """

    autor: User

    @classmethod
    def setUpTestData(cls):
        """Cria o autor.

        English:
            Creates the author.
        """
        cls.autor = criar_usuario("vitor", superuser=True)

    def test_texto_curto_conta_um_minuto(self):
        """Nunca mostra zero minuto.

        English:
            Never shows zero minutes.
        """
        post = criar_post(self.autor, conteudo="Oi.")
        self.assertEqual(post.minutos_leitura, 1)

    def test_conta_pelas_palavras(self):
        """600 palavras a 200 por minuto dão 3 minutos.

        English:
            600 words at 200 per minute give 3 minutes.
        """
        post = criar_post(self.autor, conteudo="palavra " * 600)
        self.assertEqual(post.minutos_leitura, 3)


class MarkdownTests(TestCase):
    """Sanitização do HTML gerado.

    English:
        Sanitization of the generated HTML.
    """

    def test_remove_script(self):
        """Tag <script> é removida.

        English:
            The <script> tag is removed.
        """
        html = renderizar_markdown("Oi <script>alert(1)</script>")
        self.assertNotIn("<script", html)

    def test_remove_atributo_de_evento(self):
        """Atributos como onerror são removidos.

        English:
            Attributes such as onerror are removed.
        """
        html = renderizar_markdown('<img src="x.png" onerror="alert(1)">')
        self.assertNotIn("onerror", html)

    def test_remove_link_javascript(self):
        """Link com javascript: perde o destino.

        English:
            A javascript: link loses its target.
        """
        html = renderizar_markdown("[clique](javascript:alert(1))")
        self.assertNotIn("javascript:", html)

    def test_link_ganha_rel_noopener(self):
        """Links levam rel="noopener noreferrer".

        English:
            Links get rel="noopener noreferrer".
        """
        html = renderizar_markdown("[site](https://zvlabs.com.br)")
        self.assertIn('rel="noopener noreferrer"', html)

    def test_bloco_de_codigo(self):
        """Bloco cercado ganha moldura, linguagem e uma linha por span.

        English:
            Fenced block gets a frame, the language and one span per line.
        """
        html = renderizar_markdown("```python\na = 1\nb = 2\n```")
        self.assertIn('<figure class="codigo"', html)
        self.assertIn("<span>python</span>", html)
        self.assertIn("data-copiar", html)
        self.assertIn(
            '<span class="l">a = 1</span><span class="l">b = 2</span>', html
        )

    def test_bloco_sem_linguagem(self):
        """Bloco sem linguagem mostra o rótulo "código".

        English:
            A block without a language shows the "código" label.
        """
        html = renderizar_markdown("    x = 1")
        self.assertIn("<span>código</span>", html)

    def test_codigo_continua_escapado(self):
        """HTML dentro do bloco de código continua como texto.

        English:
            HTML inside a code block stays as text.
        """
        html = renderizar_markdown("```html\n<script>alert(1)</script>\n```")
        self.assertNotIn("<script", html)
        self.assertIn("&lt;script&gt;", html)


class IndiceTests(TestCase):
    """Índice "Neste post" a partir dos subtítulos.

    English:
        "In this post" index built from the headings.
    """

    def test_lista_titulos_de_secao(self):
        """``#`` e ``##`` entram na ordem do texto; ``###`` fica fora.

        English:
            ``#`` and ``##`` come in text order; ``###`` stays out.
        """
        texto = "# Título\n\n## O problema\n\n### Detalhe\n\n## A correção"
        self.assertEqual(
            indice_markdown(texto),
            [
                ItemIndice("secao-titulo", "Título"),
                ItemIndice("secao-o-problema", "O problema"),
                ItemIndice("secao-a-correcao", "A correção"),
            ],
        )

    def test_h1_do_texto_vira_h2(self):
        """O único ``<h1>`` da página é o título do post.

        English:
            The page's only ``<h1>`` is the post title.
        """
        html = renderizar_markdown("# Título\n\nTexto.")
        self.assertIn('<h2 id="secao-titulo">Título</h2>', html)
        self.assertNotIn("<h1", html)

    def test_h1_em_bloco_de_codigo_nao_muda(self):
        """Um ``<h1>`` escrito dentro de código continua como texto.

        English:
            An ``<h1>`` written inside code stays as text.
        """
        html = renderizar_markdown("```html\n<h1>Oi</h1>\n```")
        self.assertIn("&lt;h1&gt;Oi&lt;/h1&gt;", html)

    def test_ancora_nao_repete_id_da_pagina(self):
        """``## Comentários`` não ganha o id da seção de comentários.

        English:
            ``## Comentários`` does not get the comments section id.
        """
        html = renderizar_markdown("## Comentários")
        self.assertIn('id="secao-comentarios"', html)
        self.assertNotIn('id="comentarios"', html)

    def test_ancora_igual_a_do_html(self):
        """A âncora do índice é o id do ``<h2>`` renderizado.

        English:
            The index anchor is the id of the rendered ``<h2>``.
        """
        texto = "## Celery & on_commit"
        (item,) = indice_markdown(texto)
        self.assertEqual(item.titulo, "Celery & on_commit")
        self.assertIn(f'id="{item.ancora}"', renderizar_markdown(texto))

    def test_sem_subtitulos(self):
        """Texto sem ``##`` não gera índice.

        English:
            Text without ``##`` yields no index.
        """
        self.assertEqual(indice_markdown("Só um parágrafo."), [])


class InscritoTests(TestCase):
    """Representação do inscrito.

    English:
        Subscriber representation.
    """

    def test_str_mostra_email(self):
        """O inscrito aparece pelo e-mail.

        English:
            The subscriber shows up by e-mail.
        """
        inscrito = inscrever(criar_usuario("ana"))
        self.assertEqual(str(inscrito), "ana@exemplo.com")
