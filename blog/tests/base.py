"""Fábricas de dados comuns aos testes.

English:
    Data factories shared by the tests.
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone

from blog.models import Assunto, Inscrito, Post


def criar_usuario(nome="leitor", email=None, superuser=False):
    """Cria um usuário (comum ou superusuário) com e-mail.

    English:
        Creates a user (regular or superuser) with an e-mail.
    """
    email = email or f"{nome}@exemplo.com"
    if superuser:
        return User.objects.create_superuser(nome, email, "senha-forte-123")
    return User.objects.create_user(nome, email, "senha-forte-123")


def criar_post(autor, slug="primeiro-post", publicado=True, **extra):
    """Cria um post publicado (data no passado) ou rascunho.

    English:
        Creates a published post (past date) or a draft.
    """
    dados = {
        "titulo": "Primeiro post",
        "slug": slug,
        "resumo": "Um resumo curto.",
        "conteudo": "# Olá\n\nTexto **forte**.",
        "autor": autor,
    }
    if publicado:
        dados["status"] = Post.Status.PUBLICADO
        dados["publicado_em"] = timezone.now() - timedelta(minutes=1)
    dados.update(extra)
    return Post.objects.create(**dados)


def criar_assunto(nome="Django", slug="django"):
    """Cria um assunto.

    English:
        Creates a topic.
    """
    return Assunto.objects.create(nome=nome, slug=slug)


def inscrever(usuario, ativo=True):
    """Cria uma inscrição para o usuário.

    English:
        Creates a subscription for the user.
    """
    return Inscrito.objects.create(usuario=usuario, ativo=ativo)
