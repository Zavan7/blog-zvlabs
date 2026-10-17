"""Regras de negócio do blog, sem HTTP.

Views, admin e o comando ``notificar_posts`` chamam estas funções. Quando a
regra recusa, levanta uma exceção própria e cada chamador traduz a recusa
(mensagem na tela, linha no terminal).

English:
    Blog business rules, with no HTTP.

    Views, the admin and the ``notificar_posts`` command call these
    functions. When a rule refuses, it raises its own exception and each
    caller translates the refusal (on-screen message, terminal line).
"""

import logging
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import QuerySet
from django.template.loader import render_to_string
from django.utils import timezone

from blog.models import Comentario, Inscrito, Post

logger = logging.getLogger(__name__)


class InscricaoInexistente(Exception):
    """O token de cancelamento não corresponde a nenhum inscrito.

    English:
        The unsubscribe token does not match any subscriber.
    """


class ComentarioRecusado(Exception):
    """O comentário não pode ser criado (post não publicado).

    English:
        The comment cannot be created (post not published).
    """


def inscrever(usuario: User) -> Inscrito:
    """Inscreve o usuário para receber e-mail a cada post novo.

    Se a pessoa já foi inscrita e cancelou, a inscrição é reativada com um
    token novo, para o link de cancelamento antigo deixar de valer.

    Args:
        usuario: pessoa logada que pediu a inscrição.

    Returns:
        A inscrição ativa.

    English:
        Subscribes the user to get an e-mail for every new post.

        If the person subscribed before and cancelled, the subscription is
        reactivated with a new token, so the old unsubscribe link stops
        working.

        Args:
            usuario: logged-in person who asked to subscribe.

        Returns:
            The active subscription.
    """
    inscrito, criado = Inscrito.objects.get_or_create(usuario=usuario)
    if not criado and not inscrito.ativo:
        inscrito.ativo = True
        inscrito.cancelado_em = None
        inscrito.token = uuid.uuid4()
        inscrito.save(update_fields=["ativo", "cancelado_em", "token"])
    return inscrito


def cancelar_inscricao(token: uuid.UUID) -> Inscrito:
    """Cancela a inscrição dona do token.

    Cancelar duas vezes não é erro: o segundo clique só confirma.

    Args:
        token: token do link de cancelamento.

    Returns:
        A inscrição, agora inativa.

    Raises:
        InscricaoInexistente: se nenhum inscrito tem esse token.

    English:
        Cancels the subscription that owns the token.

        Cancelling twice is not an error: the second click only confirms.

        Args:
            token: unsubscribe link token.

        Returns:
            The subscription, now inactive.

        Raises:
            InscricaoInexistente: if no subscriber has this token.
    """
    try:
        inscrito = Inscrito.objects.get(token=token)
    except Inscrito.DoesNotExist as erro:
        raise InscricaoInexistente from erro
    if inscrito.ativo:
        inscrito.ativo = False
        inscrito.cancelado_em = timezone.now()
        inscrito.save(update_fields=["ativo", "cancelado_em"])
    return inscrito


def comentar(post: Post, autor: User, texto: str) -> Comentario:
    """Cria um comentário pendente de moderação.

    Args:
        post: post comentado.
        autor: pessoa logada que escreveu.
        texto: texto já validado pelo formulário.

    Returns:
        O comentário criado, com status ``PENDENTE``.

    Raises:
        ComentarioRecusado: se o post não está publicado.

    English:
        Creates a comment awaiting moderation.

        Args:
            post: commented post.
            autor: logged-in person who wrote it.
            texto: text already validated by the form.

        Returns:
            The created comment, with status ``PENDENTE``.

        Raises:
            ComentarioRecusado: if the post is not published.
    """
    if not post.esta_publicado:
        raise ComentarioRecusado("Post não publicado.")
    return Comentario.objects.create(post=post, autor=autor, texto=texto)


def moderar_comentarios(
    comentarios: QuerySet[Comentario], status: Comentario.Status
) -> int:
    """Aprova ou rejeita comentários de uma vez.

    Args:
        comentarios: comentários escolhidos no admin.
        status: ``APROVADO`` ou ``REJEITADO``.

    Returns:
        Quantos comentários mudaram de status.

    English:
        Approves or rejects comments in bulk.

        Args:
            comentarios: comments chosen in the admin.
            status: ``APROVADO`` or ``REJEITADO``.

        Returns:
            How many comments changed status.
    """
    return comentarios.exclude(status=status).update(
        status=status, moderado_em=timezone.now()
    )


def _montar_email(post: Post, inscrito: Inscrito) -> EmailMultiAlternatives:
    """Monta o e-mail de post novo para um inscrito.

    Cada e-mail é individual porque leva o link de cancelamento daquele
    inscrito, e para um inscrito não ver o endereço dos outros.

    Args:
        post: post publicado.
        inscrito: destinatário.

    Returns:
        A mensagem pronta, com versão em texto e em HTML.

    English:
        Builds the new-post e-mail for one subscriber.

        Each e-mail is individual because it carries that subscriber's
        unsubscribe link, and so no subscriber sees the others' addresses.

        Args:
            post: published post.
            inscrito: recipient.

        Returns:
            The ready message, with text and HTML versions.
    """
    contexto = {
        "post": post,
        "post_url": settings.SITE_URL + post.get_absolute_url(),
        "cancelar_url": settings.SITE_URL + inscrito.get_cancelar_url(),
    }
    mensagem = EmailMultiAlternatives(
        subject=f"Post novo no Blog ZV Labs: {post.titulo}",
        body=render_to_string("blog/email/novo_post.txt", contexto),
        to=[inscrito.usuario.email],
        headers={"List-Unsubscribe": f"<{contexto['cancelar_url']}>"},
    )
    mensagem.attach_alternative(
        render_to_string("blog/email/novo_post.html", contexto), "text/html"
    )
    return mensagem


def notificar_inscritos(post: Post) -> int:
    """Envia o e-mail do post a todos os inscritos ativos, uma única vez.

    O post é "reivindicado" com um ``UPDATE ... WHERE notificado_em IS
    NULL``: se duas chamadas correrem juntas (admin e comando agendado),
    só uma consegue marcar e enviar. Se o envio falhar, a marca é desfeita
    para a próxima tentativa.

    Limite aceito: se o SMTP cair no meio da lista, quem já recebeu recebe
    de novo na próxima tentativa, porque o envio é marcado por post e não
    por inscrito. Com poucos inscritos o risco é pequeno; se crescer, a
    saída é um registro de envio por inscrito.

    Args:
        post: post a anunciar.

    Returns:
        Quantos e-mails foram enviados (0 se o post não está publicado ou
        já foi notificado).

    English:
        Sends the post e-mail to every active subscriber, only once.

        The post is "claimed" with an ``UPDATE ... WHERE notificado_em IS
        NULL``: if two calls run together (admin and scheduled command),
        only one manages to mark and send. If sending fails, the mark is
        undone for the next attempt.

        Accepted limit: if SMTP drops midway through the list, whoever
        already got it gets it again on the next attempt, because sending
        is marked per post, not per subscriber. With few subscribers the
        risk is small; if it grows, the fix is a per-subscriber send record.

        Args:
            post: post to announce.

        Returns:
            How many e-mails were sent (0 if the post is not published or
            was already notified).
    """
    agora = timezone.now()
    reivindicado = (
        Post.objects.publicados()
        .filter(pk=post.pk, notificado_em__isnull=True)
        .update(notificado_em=agora)
    )
    if not reivindicado:
        return 0

    inscritos = Inscrito.objects.filter(ativo=True).select_related("usuario")
    mensagens = [
        _montar_email(post, inscrito)
        for inscrito in inscritos
        if inscrito.usuario.email
    ]
    try:
        with mail.mailers.default as conexao:
            enviados = conexao.send_messages(mensagens) or 0
    except Exception:
        Post.objects.filter(pk=post.pk).update(notificado_em=None)
        logger.exception("Falha ao notificar inscritos do post %s", post.pk)
        raise
    post.notificado_em = agora
    logger.info("Post %s notificado a %s inscritos", post.pk, enviados)
    return enviados


def agendar_notificacao(post: Post) -> None:
    """Agenda a notificação para depois do commit da transação atual.

    Assim o e-mail só sai se o post foi mesmo salvo, e o link do e-mail
    nunca aponta para um post que ainda não existe no banco.

    Com ``robust=True``, uma falha no envio fica no log em vez de virar
    erro 500 para quem salvou: o post já está gravado, ``notificado_em``
    volta a vazio e o comando ``notificar_posts`` tenta de novo.

    Args:
        post: post recém-salvo.

    English:
        Schedules the notification for after the current transaction
        commits.

        This way the e-mail only goes out if the post was really saved, and
        the e-mail link never points to a post not yet in the database.

        With ``robust=True``, a sending failure goes to the log instead of
        becoming a 500 error for whoever saved: the post is already stored,
        ``notificado_em`` goes back to empty and the ``notificar_posts``
        command tries again.

        Args:
            post: freshly saved post.
    """
    if post.esta_publicado and post.notificado_em is None:
        transaction.on_commit(lambda: notificar_inscritos(post), robust=True)


def notificar_pendentes() -> int:
    """Notifica todos os posts publicados que ainda não foram anunciados.

    Usado pelo comando ``notificar_posts``, que cobre os posts agendados
    (data futura no momento em que foram salvos).

    Returns:
        Total de e-mails enviados.

    English:
        Notifies every published post not yet announced.

        Used by the ``notificar_posts`` command, which covers scheduled
        posts (future date when they were saved).

        Returns:
            Total e-mails sent.
    """
    pendentes = Post.objects.publicados().filter(notificado_em__isnull=True)
    return sum(notificar_inscritos(post) for post in pendentes)
