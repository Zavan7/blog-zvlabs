"""Views públicas do blog: listagem, post, comentário e inscrição.

Publicar posts e moderar comentários acontece só no admin, pelo dono do
blog. Toda ação que altera dados aqui é POST.

English:
    Public blog views: list, post, comment and subscription.

    Publishing posts and moderating comments only happen in the admin, by
    the blog owner. Every data-changing action here is POST.
"""

import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import (
    require_GET,
    require_http_methods,
    require_POST,
)

from blog import services
from blog.forms import ComentarioForm
from blog.models import Assunto, Comentario, Inscrito, Post
from blog.tipos import RequisicaoAutenticada


@require_GET
def post_list(request: HttpRequest) -> HttpResponse:
    """Lista os posts publicados, com filtro opcional por assunto.

    O filtro chega como ``?assunto=<slug>``. Assunto inexistente devolve
    404, para não mostrar uma lista vazia enganosa.

    Args:
        request: requisição atual.

    Returns:
        A página da listagem.

    English:
        Lists published posts, with an optional topic filter.

        The filter arrives as ``?assunto=<slug>``. An unknown topic returns
        404, so a misleading empty list is never shown.

        Args:
            request: current request.

        Returns:
            The list page.
    """
    posts = Post.objects.publicados().prefetch_related("assuntos")
    assunto_atual: Assunto | None = None
    slug = request.GET.get("assunto", "").strip()
    if slug:
        assunto_atual = get_object_or_404(Assunto, slug=slug)
        posts = posts.filter(assuntos=assunto_atual)
    assuntos = Assunto.objects.filter(
        posts__in=Post.objects.publicados()
    ).distinct()
    return render(
        request,
        "blog/post_list.html",
        {
            "posts": posts,
            "assuntos": assuntos,
            "assunto_atual": assunto_atual,
        },
    )


@require_GET
def post_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """Mostra um post publicado e seus comentários aprovados.

    Rascunho e post agendado devolvem 404, inclusive para quem adivinhar o
    endereço.

    Args:
        request: requisição atual.
        slug: identificador do post na URL.

    Returns:
        A página do post.

    Raises:
        Http404: se o post não existe ou não está publicado.

    English:
        Shows a published post and its approved comments.

        Drafts and scheduled posts return 404, even for someone who guesses
        the address.

        Args:
            request: current request.
            slug: post identifier in the URL.

        Returns:
            The post page.

        Raises:
            Http404: if the post does not exist or is not published.
    """
    post = get_object_or_404(Post.objects.publicados(), slug=slug)
    return _pagina_post(request, post, ComentarioForm())


@login_required
@require_POST
def comment_create(request: RequisicaoAutenticada, slug: str) -> HttpResponse:
    """Recebe um comentário e o deixa pendente de moderação.

    Args:
        request: requisição de uma pessoa logada.
        slug: identificador do post comentado.

    Returns:
        Redirecionamento para o post, ou a página do post com os erros do
        formulário.

    English:
        Receives a comment and leaves it awaiting moderation.

        Args:
            request: request from a logged-in person.
            slug: commented post identifier.

        Returns:
            Redirect to the post, or the post page with the form errors.
    """
    post = get_object_or_404(Post.objects.publicados(), slug=slug)
    form = ComentarioForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Não foi possível enviar o comentário.")
        return _pagina_post(request, post, form, status=400)
    services.comentar(post, request.user, form.cleaned_data["texto"])
    messages.success(
        request,
        "Comentário enviado. Ele aparece aqui depois de aprovado.",
    )
    return redirect(post)


@login_required
@require_POST
def subscribe(request: RequisicaoAutenticada) -> HttpResponse:
    """Inscreve a pessoa logada para receber os posts novos por e-mail.

    Args:
        request: requisição de uma pessoa logada.

    Returns:
        Redirecionamento para a página de origem ou para a listagem.

    English:
        Subscribes the logged-in person to receive new posts by e-mail.

        Args:
            request: request from a logged-in person.

        Returns:
            Redirect to the origin page or to the list.
    """
    if not request.user.email:
        messages.error(
            request, "Não foi possível inscrever: sua conta não tem e-mail."
        )
        return redirect("post_list")
    services.inscrever(request.user)
    messages.success(
        request,
        f"Inscrição feita. Os posts novos vão para {request.user.email}.",
    )
    return redirect(_voltar_para(request))


@require_http_methods(["GET", "POST"])
def unsubscribe(request: HttpRequest, token: uuid.UUID) -> HttpResponse:
    """Confirma (GET) e cancela (POST) a inscrição do link do e-mail.

    O link do e-mail abre uma página de confirmação em vez de cancelar
    direto, porque leitores de e-mail e antivírus visitam links sozinhos.

    Args:
        request: requisição atual (não precisa de login).
        token: token de cancelamento do inscrito.

    Returns:
        A página de confirmação, ou o redirecionamento após cancelar.

    Raises:
        Http404: se o token não existe.

    English:
        Confirms (GET) and cancels (POST) the subscription from the e-mail
        link.

        The e-mail link opens a confirmation page instead of cancelling
        right away, because mail readers and antivirus visit links on
        their own.

        Args:
            request: current request (no login needed).
            token: subscriber unsubscribe token.

        Returns:
            The confirmation page, or the redirect after cancelling.

        Raises:
            Http404: if the token does not exist.
    """
    if request.method == "POST":
        try:
            services.cancelar_inscricao(token)
        except services.InscricaoInexistente as erro:
            raise Http404("Inscrição não encontrada.") from erro
        messages.success(request, "Inscrição cancelada.")
        return redirect("post_list")
    inscrito = get_object_or_404(
        Inscrito.objects.select_related("usuario"), token=token
    )
    return render(
        request, "blog/unsubscribe_confirm.html", {"inscrito": inscrito}
    )


def _pagina_post(
    request: HttpRequest,
    post: Post,
    form: ComentarioForm,
    status: int = 200,
) -> HttpResponse:
    """Renderiza a página do post com os comentários aprovados.

    Usada pela página do post e pelo envio de comentário com erro, para
    as duas mostrarem a mesma coisa.

    Args:
        request: requisição atual.
        post: post publicado.
        form: formulário de comentário (vazio ou com erros).
        status: código HTTP da resposta.

    Returns:
        A página do post.

    English:
        Renders the post page with the approved comments.

        Used by the post page and by a comment submission with errors, so
        both show the same thing.

        Args:
            request: current request.
            post: published post.
            form: comment form (empty or with errors).
            status: HTTP status code of the response.

        Returns:
            The post page.
    """
    comentarios = post.comentarios.filter(
        status=Comentario.Status.APROVADO
    ).select_related("autor")
    return render(
        request,
        "blog/post_detail.html",
        {"post": post, "comentarios": comentarios, "form": form},
        status=status,
    )


def _voltar_para(request: HttpRequest) -> str:
    """Retorna o caminho de volta enviado pelo formulário, se for seguro.

    Só aceita caminhos internos (começando com uma ``/``), para o campo
    ``next`` não virar um redirecionamento para outro site.

    Args:
        request: requisição atual.

    Returns:
        O caminho informado, ou ``/``.

    English:
        Returns the way-back path sent by the form, if it is safe.

        Only internal paths (starting with a single ``/``) are accepted,
        so the ``next`` field cannot become a redirect to another site.

        Args:
            request: current request.

        Returns:
            The given path, or ``/``.
    """
    destino = request.POST.get("next", "")
    if destino.startswith("/") and not destino.startswith("//"):
        return destino
    return "/"
