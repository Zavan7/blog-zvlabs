"""Adapters do django-allauth: só login social, só e-mail verificado.

English:
    django-allauth adapters: social login only, verified e-mail only.
"""

from allauth.account.adapter import DefaultAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from django.contrib import messages
from django.http import HttpRequest
from django.shortcuts import redirect


class ContaAdapter(DefaultAccountAdapter):
    """Fecha o cadastro local (com senha).

    English:
        Closes local sign-up (with password).
    """

    def is_open_for_signup(self, request: HttpRequest) -> bool:
        """Recusa todo cadastro local.

        Args:
            request: requisição atual.

        Returns:
            Sempre ``False``.

        English:
            Refuses every local sign-up.

            Args:
                request: current request.

            Returns:
                Always ``False``.
        """
        return False


class ContaSocialAdapter(DefaultSocialAccountAdapter):
    """Aceita cadastro por Google e GitHub, só com e-mail verificado.

    English:
        Accepts sign-up through Google and GitHub, only with a verified
        e-mail.
    """

    def is_open_for_signup(
        self, request: HttpRequest, sociallogin: SocialLogin
    ) -> bool:
        """Permite o cadastro automático vindo do provedor.

        Args:
            request: requisição atual.
            sociallogin: dados devolvidos pelo provedor.

        Returns:
            Sempre ``True``.

        English:
            Allows automatic sign-up coming from the provider.

            Args:
                request: current request.
                sociallogin: data returned by the provider.

            Returns:
                Always ``True``.
        """
        return True

    def pre_social_login(
        self, request: HttpRequest, sociallogin: SocialLogin
    ) -> None:
        """Recusa o login quando o provedor não confirmou o e-mail.

        Sem isso, alguém poderia criar uma conta no provedor com o e-mail de
        outra pessoa, sem confirmar, e entrar no blog no lugar dela.

        Args:
            request: requisição atual.
            sociallogin: dados devolvidos pelo provedor.

        Raises:
            ImmediateHttpResponse: redireciona para a listagem com erro.

        English:
            Refuses the login when the provider did not confirm the e-mail.

            Without this, someone could create a provider account with
            another person's e-mail, without confirming it, and log into
            the blog as them.

            Args:
                request: current request.
                sociallogin: data returned by the provider.

            Raises:
                ImmediateHttpResponse: redirects to the list with an error.
        """
        verificados = [e for e in sociallogin.email_addresses if e.verified]
        if not verificados:
            messages.error(
                request,
                "Não foi possível entrar: o provedor não confirmou "
                "o seu e-mail.",
            )
            raise ImmediateHttpResponse(redirect("post_list"))
        # Usa o e-mail verificado (de preferência o principal) na conta.
        principal = next((e for e in verificados if e.primary), verificados[0])
        sociallogin.user.email = principal.email
        sociallogin.email_addresses = [principal]
