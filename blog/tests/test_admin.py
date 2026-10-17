"""Testes do admin: só o dono publica e modera.

English:
    Admin tests: only the owner publishes and moderates.
"""

from unittest.mock import patch

from django.contrib.auth.models import Permission, User
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from blog.models import Comentario, Post
from blog.tests.base import criar_post, criar_usuario, inscrever


class PublicacaoAdminTests(TestCase):
    """Publicação de posts pelo admin.

    English:
        Post publishing through the admin.
    """

    dono: User
    staff: User

    @classmethod
    def setUpTestData(cls):
        """Cria o dono, um staff comum e um inscrito.

        English:
            Creates the owner, a regular staff user and a subscriber.
        """
        cls.dono = criar_usuario("vitor", superuser=True)
        cls.staff = criar_usuario("staff")
        cls.staff.is_staff = True
        cls.staff.save()
        cls.staff.user_permissions.set(
            Permission.objects.filter(content_type__app_label="blog")
        )
        inscrever(criar_usuario("ana"))

    def _dados_post(self, **extra):
        """Dados do formulário de post do admin.

        English:
            Admin post form data.
        """
        dados = {
            "titulo": "Post novo",
            "slug": "post-novo",
            "resumo": "Resumo",
            "conteudo": "Texto",
            "status": Post.Status.PUBLICADO,
            "publicado_em_0": "",
            "publicado_em_1": "",
        }
        dados.update(extra)
        return dados

    def test_dono_publica_e_inscritos_recebem_email(self):
        """Salvar publicado define autor, data e envia o e-mail.

        English:
            Saving as published sets author and date and sends the e-mail.
        """
        self.client.force_login(self.dono)
        with self.captureOnCommitCallbacks(execute=True):
            resposta = self.client.post(
                reverse("admin:blog_post_add"), self._dados_post()
            )
        self.assertEqual(resposta.status_code, 302)
        post = Post.objects.get()
        self.assertEqual(post.autor, self.dono)
        self.assertIsNotNone(post.publicado_em)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["ana@exemplo.com"])

    def test_falha_no_envio_nao_quebra_o_admin(self):
        """SMTP fora do ar: o post é salvo e fica para o comando reenviar.

        English:
            SMTP down: the post is saved and left for the command to resend.
        """
        self.client.force_login(self.dono)
        with (
            patch(
                "django.core.mail.backends.locmem.EmailBackend.send_messages",
                side_effect=OSError("SMTP fora do ar"),
            ),
            self.assertLogs("blog.services", level="ERROR"),
            self.captureOnCommitCallbacks(execute=True),
        ):
            resposta = self.client.post(
                reverse("admin:blog_post_add"), self._dados_post()
            )
        self.assertEqual(resposta.status_code, 302)
        self.assertIsNone(Post.objects.get().notificado_em)

    def test_salvar_de_novo_nao_reenvia(self):
        """Editar um post já anunciado não manda outro e-mail.

        English:
            Editing an already announced post sends no new e-mail.
        """
        self.client.force_login(self.dono)
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(
                reverse("admin:blog_post_add"), self._dados_post()
            )
        post = Post.objects.get()
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(
                reverse("admin:blog_post_change", args=[post.pk]),
                self._dados_post(titulo="Título corrigido"),
            )
        self.assertEqual(len(mail.outbox), 1)

    def test_rascunho_nao_envia(self):
        """Rascunho salvo não notifica ninguém.

        English:
            A saved draft notifies nobody.
        """
        self.client.force_login(self.dono)
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(
                reverse("admin:blog_post_add"),
                self._dados_post(status=Post.Status.RASCUNHO),
            )
        self.assertEqual(mail.outbox, [])

    def test_staff_com_permissao_nao_publica(self):
        """Só o superusuário publica, mesmo com permissões do app.

        English:
            Only the superuser publishes, even with app permissions.
        """
        self.client.force_login(self.staff)
        resposta = self.client.post(
            reverse("admin:blog_post_add"), self._dados_post()
        )
        self.assertEqual(resposta.status_code, 403)
        self.assertFalse(Post.objects.exists())

    def test_leitor_nao_entra_no_admin(self):
        """Leitor comum é mandado ao login do admin.

        English:
            A regular reader is sent to the admin login.
        """
        self.client.force_login(criar_usuario("bia"))
        resposta = self.client.get(reverse("admin:blog_post_changelist"))
        self.assertEqual(resposta.status_code, 302)


class ModeracaoAdminTests(TestCase):
    """Aprovação de comentários pelo admin.

    English:
        Comment approval through the admin.
    """

    dono: User
    post: Post
    comentario: Comentario

    @classmethod
    def setUpTestData(cls):
        """Cria dono, post e comentário pendente.

        English:
            Creates the owner, a post and a pending comment.
        """
        cls.dono = criar_usuario("vitor", superuser=True)
        cls.post = criar_post(cls.dono)
        cls.comentario = Comentario.objects.create(
            post=cls.post, autor=criar_usuario("ana"), texto="Oi"
        )

    def test_acao_aprovar_publica_comentario(self):
        """A ação "aprovar" mostra o comentário na página do post.

        English:
            The "aprovar" action shows the comment on the post page.
        """
        self.client.force_login(self.dono)
        resposta = self.client.post(
            reverse("admin:blog_comentario_changelist"),
            {"action": "aprovar", "_selected_action": [self.comentario.pk]},
            follow=True,
        )
        self.assertContains(resposta, "1 comentário(s) aprovado(s).")
        pagina = self.client.get(self.post.get_absolute_url())
        self.assertContains(pagina, "Oi")
