"""Models do blog: assuntos, posts, comentários e inscritos.

English:
    Blog models: topics, posts, comments and subscribers.
"""

import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import SafeString

from blog.texto import ItemIndice, indice_markdown, renderizar_markdown

# Ritmo médio de leitura usado no "min de leitura".
PALAVRAS_POR_MINUTO = 200


class Assunto(models.Model):
    """Assunto (tag) usado para agrupar e filtrar posts.

    English:
        Topic (tag) used to group and filter posts.
    """

    nome = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        """Ordem alfabética e nomes no admin.

        English:
            Alphabetical order and admin names.
        """

        ordering = ["nome"]
        verbose_name = "assunto"
        verbose_name_plural = "assuntos"

    def __str__(self) -> str:
        """Retorna o nome do assunto.

        English:
            Returns the topic name.
        """
        return self.nome


class PostQuerySet(models.QuerySet["Post"]):
    """Consultas reutilizáveis de posts.

    English:
        Reusable post queries.
    """

    def publicados(self) -> PostQuerySet:
        """Filtra os posts publicados cuja data já chegou.

        Um post com data futura fica agendado: só aparece (e só notifica)
        quando a data chegar.

        Returns:
            Posts visíveis para os leitores.

        English:
            Filters published posts whose date has arrived.

            A post with a future date is scheduled: it only shows up (and
            only notifies) once the date arrives.

            Returns:
                Posts visible to readers.
        """
        return self.filter(
            status=Post.Status.PUBLICADO,
            publicado_em__lte=timezone.now(),
        )


class Post(models.Model):
    """Post escrito em Markdown, publicado só pelo dono do blog.

    English:
        Markdown post, published only by the blog owner.
    """

    class Status(models.TextChoices):
        """Situação editorial do post.

        English:
            Post editorial status.
        """

        RASCUNHO = "rascunho", "Rascunho"
        PUBLICADO = "publicado", "Publicado"

    titulo = models.CharField("título", max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    resumo = models.CharField(
        max_length=300,
        help_text="Descrição curta mostrada na listagem e no e-mail.",
    )
    conteudo = models.TextField(
        "conteúdo", help_text="Texto do post em Markdown."
    )
    assuntos = models.ManyToManyField(
        Assunto, related_name="posts", blank=True
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="posts",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.RASCUNHO
    )
    publicado_em = models.DateTimeField(
        "publicado em",
        null=True,
        blank=True,
        help_text="Data de publicação. No futuro, o post fica agendado.",
    )
    notificado_em = models.DateTimeField(
        "inscritos notificados em", null=True, blank=True, editable=False
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        """Mais recentes primeiro.

        English:
            Newest first.
        """

        ordering = ["-publicado_em", "-criado_em"]
        verbose_name = "post"
        verbose_name_plural = "posts"

    def __str__(self) -> str:
        """Retorna o título do post.

        English:
            Returns the post title.
        """
        return self.titulo

    def get_absolute_url(self) -> str:
        """Retorna o caminho da página do post.

        English:
            Returns the post page path.
        """
        return reverse("post_detail", kwargs={"slug": self.slug})

    @property
    def esta_publicado(self) -> bool:
        """Indica se o post já está visível para os leitores.

        English:
            Tells whether the post is already visible to readers.
        """
        return (
            self.status == self.Status.PUBLICADO
            and self.publicado_em is not None
            and self.publicado_em <= timezone.now()
        )

    @property
    def conteudo_html(self) -> SafeString:
        """Retorna o conteúdo convertido de Markdown para HTML seguro.

        English:
            Returns the content converted from Markdown to safe HTML.
        """
        return renderizar_markdown(self.conteudo)

    @property
    def indice(self) -> list[ItemIndice]:
        """Retorna os subtítulos ``##`` do post, para o índice lateral.

        English:
            Returns the post's ``##`` headings, for the side index.
        """
        return indice_markdown(self.conteudo)

    @property
    def minutos_leitura(self) -> int:
        """Estima o tempo de leitura em minutos (no mínimo 1).

        English:
            Estimates the reading time in minutes (at least 1).
        """
        palavras = len(self.conteudo.split())
        return max(1, round(palavras / PALAVRAS_POR_MINUTO))


class Comentario(models.Model):
    """Comentário de um leitor logado, publicado só depois de aprovado.

    O post usa ``CASCADE``: comentário é parte do post e não faz sentido
    sem ele. O autor usa ``PROTECT``: é histórico de quem escreveu.

    English:
        Comment by a logged-in reader, shown only after approval.

        The post uses ``CASCADE``: a comment is part of the post and makes
        no sense without it. The author uses ``PROTECT``: it is the record
        of who wrote it.
    """

    class Status(models.TextChoices):
        """Situação da moderação.

        English:
            Moderation status.
        """

        PENDENTE = "pendente", "Pendente"
        APROVADO = "aprovado", "Aprovado"
        REJEITADO = "rejeitado", "Rejeitado"

    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comentarios"
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="comentarios",
    )
    texto = models.TextField(max_length=3000)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDENTE
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    moderado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Ordem de leitura: mais antigos primeiro.

        English:
            Reading order: oldest first.
        """

        ordering = ["criado_em"]
        verbose_name = "comentário"
        verbose_name_plural = "comentários"

    def __str__(self) -> str:
        """Retorna autor e post do comentário.

        English:
            Returns the comment author and post.
        """
        return f"{self.autor} em {self.post}"


class Inscrito(models.Model):
    """Pessoa logada que quer receber e-mail a cada post novo.

    O ``token`` vai no link de cancelamento de todo e-mail, para cancelar
    sem precisar fazer login. Cancelar não apaga o registro: só desativa.

    English:
        Logged-in person who wants an e-mail for every new post.

        The ``token`` goes in the unsubscribe link of every e-mail, so the
        person can cancel without logging in. Cancelling does not delete
        the record: it only deactivates it.
    """

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inscricao",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    cancelado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Mais recentes primeiro.

        English:
            Newest first.
        """

        ordering = ["-criado_em"]
        verbose_name = "inscrito"
        verbose_name_plural = "inscritos"

    def __str__(self) -> str:
        """Retorna o e-mail do inscrito.

        English:
            Returns the subscriber e-mail.
        """
        return self.usuario.email

    def get_cancelar_url(self) -> str:
        """Retorna o caminho da página de cancelamento deste inscrito.

        English:
            Returns the unsubscribe page path for this subscriber.
        """
        return reverse("unsubscribe", kwargs={"token": self.token})
