"""Testes das views públicas, incluindo os caminhos negativos.

English:
    Public view tests, including the negative paths.
"""

import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from blog.models import Assunto, Comentario, Inscrito, Post
from blog.tests.base import (
    criar_assunto,
    criar_post,
    criar_usuario,
    inscrever,
)


class ListagemTests(TestCase):
    """Listagem e filtro por assunto.

    English:
        List and topic filter.
    """

    autor: User
    django: Assunto
    rpa: Assunto
    post_django: Post
    post_rpa: Post

    @classmethod
    def setUpTestData(cls):
        """Cria posts com e sem assunto e um rascunho.

        English:
            Creates posts with different topics and a draft.
        """
        cls.autor = criar_usuario("vitor", superuser=True)
        cls.django = criar_assunto()
        cls.rpa = criar_assunto("RPA", "rpa")
        cls.post_django = criar_post(
            cls.autor, slug="sobre-django", titulo="Sobre Django"
        )
        cls.post_django.assuntos.add(cls.django)
        cls.post_rpa = criar_post(cls.autor, slug="sobre-rpa", titulo="RPA")
        cls.post_rpa.assuntos.add(cls.rpa)
        criar_post(
            cls.autor, slug="rascunho", titulo="Rascunho", publicado=False
        )

    def test_lista_titulo_e_resumo_dos_publicados(self):
        """A listagem mostra título e resumo, sem rascunhos.

        English:
            The list shows title and summary, without drafts.
        """
        resposta = self.client.get(reverse("post_list"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Sobre Django")
        self.assertContains(resposta, "Um resumo curto.")
        self.assertNotContains(resposta, "Rascunho")

    def test_filtra_por_assunto(self):
        """?assunto=django mostra só os posts do assunto.

        English:
            ?assunto=django shows only the topic's posts.
        """
        resposta = self.client.get(reverse("post_list"), {"assunto": "django"})
        self.assertContains(resposta, "Sobre Django")
        self.assertNotContains(resposta, "sobre-rpa/")

    def test_assunto_inexistente_404(self):
        """Assunto desconhecido devolve 404.

        English:
            Unknown topic returns 404.
        """
        resposta = self.client.get(reverse("post_list"), {"assunto": "nada"})
        self.assertEqual(resposta.status_code, 404)

    def test_sem_n_mais_1(self):
        """A listagem faz um número fixo de consultas.

        English:
            The list runs a fixed number of queries.
        """
        for i in range(5):
            post = criar_post(self.autor, slug=f"extra-{i}")
            post.assuntos.add(self.django)
        # 2 do allauth (um app por provedor no cabeçalho), assuntos do
        # filtro, posts e o prefetch dos assuntos: não cresce com os posts.
        with self.assertNumQueries(5):
            self.client.get(reverse("post_list"))


class DetalheTests(TestCase):
    """Página do post.

    English:
        Post page.
    """

    autor: User
    leitor: User
    post: Post
    rascunho: Post

    @classmethod
    def setUpTestData(cls):
        """Cria post, rascunho e comentários.

        English:
            Creates a post, a draft and comments.
        """
        cls.autor = criar_usuario("vitor", superuser=True)
        cls.leitor = criar_usuario("ana")
        cls.post = criar_post(cls.autor)
        cls.rascunho = criar_post(cls.autor, slug="rascunho", publicado=False)
        Comentario.objects.create(
            post=cls.post,
            autor=cls.leitor,
            texto="Comentário aprovado",
            status=Comentario.Status.APROVADO,
        )
        Comentario.objects.create(
            post=cls.post, autor=cls.leitor, texto="Comentário pendente"
        )

    def test_mostra_post_e_so_comentarios_aprovados(self):
        """Pendentes não aparecem.

        English:
            Pending comments are not shown.
        """
        resposta = self.client.get(self.post.get_absolute_url())
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "<strong>forte</strong>", html=True)
        self.assertContains(resposta, "Comentário aprovado")
        self.assertNotContains(resposta, "Comentário pendente")

    def test_rascunho_404(self):
        """Rascunho não abre, nem com o endereço certo.

        English:
            A draft does not open, even with the right address.
        """
        resposta = self.client.get(self.rascunho.get_absolute_url())
        self.assertEqual(resposta.status_code, 404)

    def test_post_inexistente_404(self):
        """Slug desconhecido devolve 404.

        English:
            Unknown slug returns 404.
        """
        resposta = self.client.get(
            reverse("post_detail", kwargs={"slug": "nao-existe"})
        )
        self.assertEqual(resposta.status_code, 404)

    def test_deslogado_nao_ve_formulario(self):
        """Quem não está logado vê o convite para entrar.

        English:
            A logged-out visitor sees the invitation to log in.
        """
        resposta = self.client.get(self.post.get_absolute_url())
        self.assertNotContains(resposta, 'name="texto"')

    def test_logado_ve_formulario(self):
        """Quem está logado vê o formulário.

        English:
            A logged-in user sees the form.
        """
        self.client.force_login(self.leitor)
        resposta = self.client.get(self.post.get_absolute_url())
        self.assertContains(resposta, 'name="texto"')

    def test_deslogado_ve_convite_de_inscricao(self):
        """Deslogado vê os botões de login social no fim do post.

        English:
            A logged-out visitor sees the social login buttons after the
            post.
        """
        resposta = self.client.get(self.post.get_absolute_url())
        self.assertContains(resposta, "Inscrever com GitHub")
        self.assertContains(resposta, "Entrar com Google")

    def test_inscrito_nao_ve_convite_de_inscricao(self):
        """Quem já é inscrito não vê o convite no fim do post.

        English:
            An existing subscriber does not see the invitation after the
            post.
        """
        inscrever(self.leitor)
        self.client.force_login(self.leitor)
        resposta = self.client.get(self.post.get_absolute_url())
        self.assertNotContains(resposta, "Receba o próximo por e-mail")
        self.assertContains(resposta, "Cancelar inscrição")

    def test_mostra_indice_e_leitura(self):
        """Post com ``##`` mostra o índice e o tempo de leitura.

        English:
            A post with ``##`` shows the index and the reading time.
        """
        post = criar_post(
            self.autor, slug="com-indice", conteudo="## O problema\n\nTexto."
        )
        resposta = self.client.get(post.get_absolute_url())
        self.assertContains(
            resposta,
            '<a class="indice-link" href="#o-problema">O problema</a>',
            html=True,
        )
        self.assertContains(resposta, "1 min")

    @override_settings(PORTFOLIO_URL="")
    def test_sem_portfolio_esconde_link(self):
        """Sem ``PORTFOLIO_URL``, o link do portfólio some.

        English:
            Without ``PORTFOLIO_URL``, the portfolio link is hidden.
        """
        resposta = self.client.get(self.post.get_absolute_url())
        self.assertNotContains(resposta, "Voltar ao portfólio")

    @override_settings(PORTFOLIO_URL="https://zvlabs.com.br/")
    def test_com_portfolio_mostra_link(self):
        """Com ``PORTFOLIO_URL``, menu e rodapé apontam para ele.

        English:
            With ``PORTFOLIO_URL``, menu and footer point to it.
        """
        resposta = self.client.get(self.post.get_absolute_url())
        self.assertContains(resposta, 'href="https://zvlabs.com.br/"', count=2)


class VizinhosTests(TestCase):
    """Navegação para o post anterior e o próximo.

    English:
        Navigation to the previous and next posts.
    """

    autor: User
    antigo: Post
    meio: Post
    novo: Post

    @classmethod
    def setUpTestData(cls):
        """Cria três posts publicados, um rascunho e um agendado.

        English:
            Creates three published posts, a draft and a scheduled one.
        """
        cls.autor = criar_usuario("vitor", superuser=True)
        agora = timezone.now()
        cls.antigo = criar_post(
            cls.autor,
            slug="antigo",
            titulo="Post antigo",
            publicado_em=agora - timedelta(days=3),
        )
        cls.meio = criar_post(
            cls.autor,
            slug="meio",
            titulo="Post do meio",
            publicado_em=agora - timedelta(days=2),
        )
        cls.novo = criar_post(
            cls.autor,
            slug="novo",
            titulo="Post novo",
            publicado_em=agora - timedelta(days=1),
        )
        criar_post(
            cls.autor, slug="rascunho", titulo="Rascunho", publicado=False
        )
        criar_post(
            cls.autor,
            slug="agendado",
            titulo="Agendado",
            status=Post.Status.PUBLICADO,
            publicado_em=agora + timedelta(days=1),
        )

    def test_meio_tem_anterior_e_proximo(self):
        """O post do meio aponta para os dois vizinhos.

        English:
            The middle post points to both neighbours.
        """
        resposta = self.client.get(self.meio.get_absolute_url())
        self.assertEqual(resposta.context["anterior"], self.antigo)
        self.assertEqual(resposta.context["proximo"], self.novo)

    def test_mais_novo_ignora_agendado_e_rascunho(self):
        """Agendado e rascunho nunca viram "próximo post".

        English:
            Scheduled and draft posts never become the "next post".
        """
        resposta = self.client.get(self.novo.get_absolute_url())
        self.assertEqual(resposta.context["anterior"], self.meio)
        self.assertIsNone(resposta.context["proximo"])
        self.assertNotContains(resposta, "Agendado")

    def test_mais_antigo_nao_tem_anterior(self):
        """O primeiro post não tem anterior.

        English:
            The first post has no previous one.
        """
        resposta = self.client.get(self.antigo.get_absolute_url())
        self.assertIsNone(resposta.context["anterior"])
        self.assertNotContains(resposta, "Post anterior")


class ComentarTests(TestCase):
    """Envio de comentários.

    English:
        Comment submission.
    """

    autor: User
    leitor: User
    post: Post
    rascunho: Post
    url: str

    @classmethod
    def setUpTestData(cls):
        """Cria autor, leitor, post e rascunho.

        English:
            Creates the author, a reader, a post and a draft.
        """
        cls.autor = criar_usuario("vitor", superuser=True)
        cls.leitor = criar_usuario("ana")
        cls.post = criar_post(cls.autor)
        cls.rascunho = criar_post(cls.autor, slug="rascunho", publicado=False)
        cls.url = reverse("comment_create", kwargs={"slug": "primeiro-post"})

    def test_deslogado_e_redirecionado_ao_login(self):
        """Deslogado não comenta.

        English:
            A logged-out visitor cannot comment.
        """
        resposta = self.client.post(self.url, {"texto": "Oi"})
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse("account_login"), resposta["Location"])
        self.assertFalse(Comentario.objects.exists())

    def test_logado_cria_comentario_pendente(self):
        """O comentário nasce pendente, com o autor logado.

        English:
            The comment is born pending, with the logged-in author.
        """
        self.client.force_login(self.leitor)
        resposta = self.client.post(self.url, {"texto": "Muito bom"})
        self.assertRedirects(resposta, self.post.get_absolute_url())
        comentario = Comentario.objects.get()
        self.assertEqual(comentario.autor, self.leitor)
        self.assertEqual(comentario.status, Comentario.Status.PENDENTE)

    def test_nao_aceita_status_forjado(self):
        """Mandar status=aprovado no POST não aprova nada.

        English:
            Sending status=aprovado in the POST approves nothing.
        """
        self.client.force_login(self.leitor)
        self.client.post(self.url, {"texto": "Oi", "status": "aprovado"})
        self.assertEqual(
            Comentario.objects.get().status, Comentario.Status.PENDENTE
        )

    def test_texto_vazio_400(self):
        """Comentário vazio volta com erro.

        English:
            An empty comment comes back with an error.
        """
        self.client.force_login(self.leitor)
        resposta = self.client.post(self.url, {"texto": ""})
        self.assertEqual(resposta.status_code, 400)
        self.assertFalse(Comentario.objects.exists())

    def test_get_nao_permitido(self):
        """Comentar só por POST.

        English:
            Commenting only via POST.
        """
        self.client.force_login(self.leitor)
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 405)

    def test_rascunho_404(self):
        """Não dá para comentar rascunho.

        English:
            A draft cannot be commented on.
        """
        self.client.force_login(self.leitor)
        resposta = self.client.post(
            reverse("comment_create", kwargs={"slug": "rascunho"}),
            {"texto": "Oi"},
        )
        self.assertEqual(resposta.status_code, 404)


class InscricaoViewTests(TestCase):
    """Inscrição e cancelamento pelo site.

    English:
        Subscription and cancellation through the site.
    """

    def setUp(self):
        """Cria o leitor.

        English:
            Creates the reader.
        """
        self.leitor = criar_usuario("ana")

    def test_deslogado_nao_inscreve(self):
        """Deslogado é mandado ao login.

        English:
            A logged-out visitor is sent to login.
        """
        resposta = self.client.post(reverse("subscribe"))
        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(Inscrito.objects.exists())

    def test_logado_inscreve(self):
        """POST cria a inscrição e volta para a página de origem.

        English:
            POST creates the subscription and returns to the origin page.
        """
        self.client.force_login(self.leitor)
        resposta = self.client.post(reverse("subscribe"), {"next": "/"})
        self.assertRedirects(resposta, "/")
        self.assertTrue(Inscrito.objects.get(usuario=self.leitor).ativo)

    def test_next_externo_ignorado(self):
        """Next para outro site não é seguido.

        English:
            A next pointing to another site is not followed.
        """
        self.client.force_login(self.leitor)
        resposta = self.client.post(
            reverse("subscribe"), {"next": "//malicioso.com"}
        )
        self.assertEqual(resposta["Location"], "/")

    def test_inscrever_por_get_nao_permitido(self):
        """Inscrever só por POST.

        English:
            Subscribing only via POST.
        """
        self.client.force_login(self.leitor)
        resposta = self.client.get(reverse("subscribe"))
        self.assertEqual(resposta.status_code, 405)

    def test_link_do_email_so_confirma(self):
        """GET no link de cancelamento não cancela: pede confirmação.

        English:
            GET on the unsubscribe link does not cancel: it asks for
            confirmation.
        """
        inscrito = inscrever(self.leitor)
        resposta = self.client.get(inscrito.get_cancelar_url())
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "ana@exemplo.com")
        inscrito.refresh_from_db()
        self.assertTrue(inscrito.ativo)

    def test_post_cancela_sem_login(self):
        """POST no link cancela, mesmo deslogado.

        English:
            POST on the link cancels, even when logged out.
        """
        inscrito = inscrever(self.leitor)
        resposta = self.client.post(inscrito.get_cancelar_url())
        self.assertRedirects(resposta, reverse("post_list"))
        inscrito.refresh_from_db()
        self.assertFalse(inscrito.ativo)

    def test_token_inexistente_404(self):
        """Token desconhecido devolve 404 no GET e no POST.

        English:
            Unknown token returns 404 on GET and POST.
        """
        url = reverse("unsubscribe", kwargs={"token": uuid.uuid4()})
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url).status_code, 404)
