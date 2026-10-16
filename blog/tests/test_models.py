"""Testes dos models e da conversão de Markdown.

English:
    Model and Markdown conversion tests.
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from blog.models import Post
from blog.tests.base import criar_post, criar_usuario
from blog.texto import renderizar_markdown


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
        """Bloco cercado vira <pre><code>.

        English:
            Fenced block becomes <pre><code>.
        """
        html = renderizar_markdown("```python\nprint('oi')\n```")
        self.assertIn("<pre><code", html)
