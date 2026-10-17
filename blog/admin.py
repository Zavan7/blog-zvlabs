"""Admin do blog: publicação de posts, moderação de comentários, inscritos.

Só o superusuário (o dono do blog) mexe em posts e comentários, mesmo que
outra conta receba acesso ao admin no futuro.

English:
    Blog admin: post publishing, comment moderation, subscribers.

    Only the superuser (the blog owner) touches posts and comments, even if
    another account is given admin access in the future.
"""

from typing import Any

from django.contrib import admin, messages
from django.db.models import Count, Model, Q, QuerySet
from django.forms import ModelForm
from django.http import HttpRequest
from django.utils import timezone

from blog import services
from blog.models import Assunto, Comentario, Inscrito, Post


class SoDonoAdmin(admin.ModelAdmin[Any]):
    """Libera o model só para o superusuário.

    English:
        Grants access to the model only to the superuser.
    """

    def has_module_permission(self, request: HttpRequest) -> bool:
        """Mostra o model no admin só para o superusuário.

        English:
            Shows the model in the admin only to the superuser.
        """
        return request.user.is_superuser

    def has_view_permission(
        self, request: HttpRequest, obj: Model | None = None
    ) -> bool:
        """Permite ver só ao superusuário.

        English:
            Allows viewing only to the superuser.
        """
        return request.user.is_superuser

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Permite criar só ao superusuário.

        English:
            Allows creating only to the superuser.
        """
        return request.user.is_superuser

    def has_change_permission(
        self, request: HttpRequest, obj: Model | None = None
    ) -> bool:
        """Permite alterar só ao superusuário.

        English:
            Allows changing only to the superuser.
        """
        return request.user.is_superuser

    def has_delete_permission(
        self, request: HttpRequest, obj: Model | None = None
    ) -> bool:
        """Permite apagar só ao superusuário.

        English:
            Allows deleting only to the superuser.
        """
        return request.user.is_superuser


@admin.register(Assunto)
class AssuntoAdmin(SoDonoAdmin):
    """Cadastro de assuntos.

    English:
        Topic registry.
    """

    list_display = ["nome", "slug"]
    prepopulated_fields = {"slug": ["nome"]}
    search_fields = ["nome"]


@admin.register(Post)
class PostAdmin(SoDonoAdmin):
    """Escrita e publicação de posts.

    Ao salvar um post publicado com data que já chegou, os inscritos
    recebem o e-mail (uma única vez por post, depois do commit).

    English:
        Post writing and publishing.

        When a published post whose date has arrived is saved, subscribers
        get the e-mail (only once per post, after commit).
    """

    list_display = [
        "titulo",
        "status",
        "publicado_em",
        "notificado_em",
        "qtd_comentarios_pendentes",
    ]
    list_filter = ["status", "assuntos"]
    search_fields = ["titulo", "resumo", "conteudo"]
    prepopulated_fields = {"slug": ["titulo"]}
    filter_horizontal = ["assuntos"]
    date_hierarchy = "publicado_em"
    readonly_fields = ["notificado_em", "criado_em", "atualizado_em"]
    fields = [
        "titulo",
        "slug",
        "resumo",
        "conteudo",
        "assuntos",
        "status",
        "publicado_em",
        "notificado_em",
        "criado_em",
        "atualizado_em",
    ]
    actions = ["publicar_agora"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Post]:
        """Lista os posts já com a contagem de pendentes, sem N+1.

        English:
            Lists posts with the pending count already loaded, without N+1.
        """
        return (
            super()
            .get_queryset(request)
            .annotate(
                pendentes=Count(
                    "comentarios",
                    filter=Q(comentarios__status=Comentario.Status.PENDENTE),
                )
            )
        )

    @admin.display(description="Comentários pendentes")
    def qtd_comentarios_pendentes(self, obj: Post) -> int:
        """Retorna quantos comentários do post esperam moderação.

        English:
            Returns how many post comments await moderation.
        """
        return int(getattr(obj, "pendentes", 0))

    def save_model(
        self,
        request: HttpRequest,
        obj: Post,
        form: ModelForm[Post],
        change: bool,
    ) -> None:
        """Define o autor e agenda o e-mail aos inscritos.

        O autor nunca vem do formulário: é sempre quem está logado. A data
        de publicação que faltar já foi preenchida pelo ``Post.clean``.

        English:
            Sets the author and schedules the e-mail to subscribers.

            The author never comes from the form: it is always the
            logged-in user. A missing publication date was already filled
            in by ``Post.clean``.
        """
        if not change:
            obj.autor = request.user  # type: ignore[assignment]
        super().save_model(request, obj, form, change)
        services.agendar_notificacao(obj)

    @admin.action(description="Publicar agora")
    def publicar_agora(
        self, request: HttpRequest, queryset: QuerySet[Post]
    ) -> None:
        """Publica os posts escolhidos com a data de agora.

        English:
            Publishes the chosen posts with the current date.
        """
        rascunhos = list(queryset.exclude(status=Post.Status.PUBLICADO))
        agora = timezone.now()
        for post in rascunhos:
            post.status = Post.Status.PUBLICADO
            post.publicado_em = agora
            post.save(update_fields=["status", "publicado_em"])
            services.agendar_notificacao(post)
        self.message_user(
            request,
            f"{len(rascunhos)} post(s) publicado(s).",
            messages.SUCCESS,
        )


@admin.register(Comentario)
class ComentarioAdmin(SoDonoAdmin):
    """Moderação de comentários.

    English:
        Comment moderation.
    """

    list_display = ["autor", "post", "trecho", "status", "criado_em"]
    list_filter = ["status", "criado_em"]
    search_fields = ["texto", "autor__email", "post__titulo"]
    list_select_related = ["autor", "post"]
    readonly_fields = ["post", "autor", "texto", "criado_em", "moderado_em"]
    fields = ["post", "autor", "texto", "status", "criado_em", "moderado_em"]
    actions = ["aprovar", "rejeitar"]

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Comentário só nasce pelo site, nunca pelo admin.

        English:
            Comments are only created on the site, never in the admin.
        """
        return False

    @admin.display(description="Comentário")
    def trecho(self, obj: Comentario) -> str:
        """Retorna os primeiros 80 caracteres do comentário.

        English:
            Returns the first 80 characters of the comment.
        """
        return obj.texto[:80]

    def save_model(
        self,
        request: HttpRequest,
        obj: Comentario,
        form: ModelForm[Comentario],
        change: bool,
    ) -> None:
        """Registra a data da moderação quando o status muda.

        English:
            Records the moderation date when the status changes.
        """
        if "status" in form.changed_data:
            obj.moderado_em = timezone.now()
        super().save_model(request, obj, form, change)

    @admin.action(description="Aprovar comentários selecionados")
    def aprovar(
        self, request: HttpRequest, queryset: QuerySet[Comentario]
    ) -> None:
        """Aprova os comentários escolhidos.

        English:
            Approves the chosen comments.
        """
        total = services.moderar_comentarios(
            queryset, Comentario.Status.APROVADO
        )
        self.message_user(
            request, f"{total} comentário(s) aprovado(s).", messages.SUCCESS
        )

    @admin.action(description="Rejeitar comentários selecionados")
    def rejeitar(
        self, request: HttpRequest, queryset: QuerySet[Comentario]
    ) -> None:
        """Rejeita os comentários escolhidos.

        English:
            Rejects the chosen comments.
        """
        total = services.moderar_comentarios(
            queryset, Comentario.Status.REJEITADO
        )
        self.message_user(
            request, f"{total} comentário(s) rejeitado(s).", messages.SUCCESS
        )


@admin.register(Inscrito)
class InscritoAdmin(SoDonoAdmin):
    """Consulta de inscritos (a inscrição nasce e é cancelada pelo site).

    English:
        Subscriber lookup (subscriptions are created and cancelled on the
        site).
    """

    list_display = ["usuario", "email", "ativo", "criado_em", "cancelado_em"]
    list_filter = ["ativo"]
    search_fields = ["usuario__email"]
    list_select_related = ["usuario"]
    readonly_fields = ["usuario", "token", "criado_em", "cancelado_em"]

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Inscrição só nasce pelo site, com o consentimento da pessoa.

        English:
            Subscriptions are only created on the site, with consent.
        """
        return False

    @admin.display(description="E-mail")
    def email(self, obj: Inscrito) -> str:
        """Retorna o e-mail do inscrito.

        English:
            Returns the subscriber e-mail.
        """
        return obj.usuario.email
