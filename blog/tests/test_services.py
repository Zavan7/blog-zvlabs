"""Testes da camada de serviço.

English:
    Service layer tests.
"""

import uuid
from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from blog import services
from blog.models import Comentario, Inscrito, Post
from blog.tests.base import criar_post, criar_usuario, inscrever


@override_settings(SITE_URL="https://blog.exemplo.com")
class NotificarInscritosTests(TestCase):
    """Envio do e-mail de post novo.

    English:
        New-post e-mail sending.
    """

    autor: User
    ana: Inscrito
    bia: Inscrito
    cancelado: Inscrito

    @classmethod
    def setUpTestData(cls):
        """Cria autor, dois inscritos ativos e um cancelado.

        English:
            Creates the author, two active subscribers and a cancelled one.
        """
        cls.autor = criar_usuario("vitor", superuser=True)
        cls.ana = inscrever(criar_usuario("ana"))
        cls.bia = inscrever(criar_usuario("bia"))
        cls.cancelado = inscrever(criar_usuario("caio"), ativo=False)

    def test_envia_um_email_por_inscrito_ativo(self):
        """Cada inscrito ativo recebe o seu e-mail; o cancelado não.

        English:
            Each active subscriber gets an e-mail; the cancelled one does not.
        """
        post = criar_post(self.autor)
        enviados = services.notificar_inscritos(post)
        self.assertEqual(enviados, 2)
        destinos = sorted(m.to[0] for m in mail.outbox)
        self.assertEqual(destinos, ["ana@exemplo.com", "bia@exemplo.com"])

    def test_email_tem_titulo_resumo_link_e_cancelamento(self):
        """O e-mail traz título, resumo, link do post e de cancelamento.

        English:
            The e-mail has title, summary, post link and unsubscribe link.
        """
        post = criar_post(self.autor)
        services.notificar_inscritos(post)
        email = next(m for m in mail.outbox if m.to == ["ana@exemplo.com"])
        self.assertIn(post.titulo, email.subject)
        self.assertIn(post.resumo, email.body)
        self.assertIn(
            "https://blog.exemplo.com/posts/primeiro-post/", email.body
        )
        cancelar = f"https://blog.exemplo.com{self.ana.get_cancelar_url()}"
        self.assertIn(cancelar, email.body)
        self.assertIn(cancelar, email.extra_headers["List-Unsubscribe"])

    def test_envia_uma_vez_so(self):
        """A segunda chamada não reenvia nada.

        English:
            The second call resends nothing.
        """
        post = criar_post(self.autor)
        services.notificar_inscritos(post)
        self.assertEqual(services.notificar_inscritos(post), 0)
        self.assertEqual(len(mail.outbox), 2)
        post.refresh_from_db()
        self.assertIsNotNone(post.notificado_em)

    def test_nao_envia_rascunho(self):
        """Rascunho não notifica.

        English:
            A draft does not notify.
        """
        post = criar_post(self.autor, publicado=False)
        self.assertEqual(services.notificar_inscritos(post), 0)
        self.assertEqual(mail.outbox, [])

    def test_nao_envia_post_agendado(self):
        """Post com data futura só notifica quando a data chegar.

        English:
            A post with a future date only notifies when the date arrives.
        """
        post = criar_post(
            self.autor, publicado_em=timezone.now() + timedelta(hours=1)
        )
        self.assertEqual(services.notificar_inscritos(post), 0)

    def test_falha_no_envio_desfaz_a_marca(self):
        """Se o SMTP falha, o post volta a ficar pendente de notificação.

        English:
            If SMTP fails, the post goes back to pending notification.
        """
        post = criar_post(self.autor)
        with (
            mock.patch(
                "django.core.mail.backends.locmem.EmailBackend.send_messages",
                side_effect=OSError("SMTP fora do ar"),
            ),
            self.assertLogs("blog.services", level="ERROR"),
            self.assertRaises(OSError),
        ):
            services.notificar_inscritos(post)
        post.refresh_from_db()
        self.assertIsNone(post.notificado_em)

    def test_notificar_pendentes_cobre_agendado_que_chegou(self):
        """O comando pega posts publicados ainda não anunciados.

        English:
            The command picks published posts not yet announced.
        """
        criar_post(self.autor)
        criar_post(self.autor, slug="rascunho", publicado=False)
        self.assertEqual(services.notificar_pendentes(), 2)

    def test_agendar_notificacao_envia_apos_commit(self):
        """O e-mail sai só depois do commit.

        English:
            The e-mail only goes out after commit.
        """
        post = criar_post(self.autor)
        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            services.agendar_notificacao(post)
        self.assertEqual(mail.outbox, [])
        self.assertEqual(len(callbacks), 1)
        callbacks[0]()
        self.assertEqual(len(mail.outbox), 2)


class InscricaoTests(TestCase):
    """Inscrição e cancelamento.

    English:
        Subscription and cancellation.
    """

    def setUp(self):
        """Cria o leitor.

        English:
            Creates the reader.
        """
        self.usuario = criar_usuario("ana")

    def test_inscrever_cria_inscricao_ativa(self):
        """Inscrever cria uma inscrição ativa com token.

        English:
            Subscribing creates an active subscription with a token.
        """
        inscrito = services.inscrever(self.usuario)
        self.assertTrue(inscrito.ativo)
        self.assertIsInstance(inscrito.token, uuid.UUID)

    def test_inscrever_duas_vezes_nao_duplica(self):
        """A segunda inscrição reaproveita a primeira.

        English:
            The second subscription reuses the first one.
        """
        services.inscrever(self.usuario)
        services.inscrever(self.usuario)
        self.assertEqual(Inscrito.objects.count(), 1)

    def test_reinscrever_troca_o_token(self):
        """Quem cancelou e voltou ganha um token novo.

        English:
            Whoever cancelled and came back gets a new token.
        """
        inscrito = services.inscrever(self.usuario)
        token_antigo = inscrito.token
        services.cancelar_inscricao(token_antigo)
        novo = services.inscrever(self.usuario)
        self.assertTrue(novo.ativo)
        self.assertNotEqual(novo.token, token_antigo)

    def test_cancelar_desativa(self):
        """Cancelar desativa e registra a data.

        English:
            Cancelling deactivates and records the date.
        """
        inscrito = services.inscrever(self.usuario)
        services.cancelar_inscricao(inscrito.token)
        inscrito.refresh_from_db()
        self.assertFalse(inscrito.ativo)
        self.assertIsNotNone(inscrito.cancelado_em)

    def test_cancelar_token_inexistente(self):
        """Token desconhecido levanta InscricaoInexistente.

        English:
            Unknown token raises InscricaoInexistente.
        """
        with self.assertRaises(services.InscricaoInexistente):
            services.cancelar_inscricao(uuid.uuid4())


class ComentarioServiceTests(TestCase):
    """Criação e moderação de comentários.

    English:
        Comment creation and moderation.
    """

    autor: User
    leitor: User
    post: Post

    @classmethod
    def setUpTestData(cls):
        """Cria autor, leitor e post.

        English:
            Creates the author, a reader and a post.
        """
        cls.autor = criar_usuario("vitor", superuser=True)
        cls.leitor = criar_usuario("ana")
        cls.post = criar_post(cls.autor)

    def test_comentario_nasce_pendente(self):
        """Comentário novo fica pendente.

        English:
            A new comment stays pending.
        """
        comentario = services.comentar(self.post, self.leitor, "Ótimo!")
        self.assertEqual(comentario.status, Comentario.Status.PENDENTE)

    def test_comentario_em_rascunho_recusado(self):
        """Não dá para comentar post não publicado.

        English:
            An unpublished post cannot be commented on.
        """
        rascunho = criar_post(self.autor, slug="r", publicado=False)
        with self.assertRaises(services.ComentarioRecusado):
            services.comentar(rascunho, self.leitor, "Oi")

    def test_moderar_aprova_e_registra_data(self):
        """Aprovar muda o status e registra a data.

        English:
            Approving changes the status and records the date.
        """
        services.comentar(self.post, self.leitor, "Oi")
        total = services.moderar_comentarios(
            Comentario.objects.all(), Comentario.Status.APROVADO
        )
        self.assertEqual(total, 1)
        comentario = Comentario.objects.get()
        self.assertEqual(comentario.status, Comentario.Status.APROVADO)
        self.assertIsNotNone(comentario.moderado_em)

    def test_post_status_choices(self):
        """Valores das choices em português sem acento.

        English:
            Choice values in Portuguese without accents.
        """
        self.assertEqual(Post.Status.PUBLICADO, "publicado")
