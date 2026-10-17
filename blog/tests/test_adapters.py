"""Testes do adapter de login social.

English:
    Social login adapter tests.
"""

from unittest import mock

from allauth.account.models import EmailAddress
from allauth.core.exceptions import ImmediateHttpResponse
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory, TestCase

from blog.adapters import ContaAdapter, ContaSocialAdapter


class AdapterTests(TestCase):
    """Só login social e só e-mail verificado.

    English:
        Social login only and verified e-mail only.
    """

    def setUp(self):
        """Monta uma requisição com suporte a mensagens.

        English:
            Builds a request with message support.
        """
        self.request = RequestFactory().get("/")
        self.request.session = SessionStore()
        # O middleware de mensagens não roda no RequestFactory.
        self.request._messages = FallbackStorage(self.request)  # type: ignore[attr-defined]

    def _sociallogin(self, *emails):
        """Simula o retorno do provedor com os e-mails informados.

        English:
            Simulates the provider response with the given e-mails.
        """
        sociallogin = mock.Mock()
        sociallogin.user = User(username="ana")
        sociallogin.email_addresses = list(emails)
        return sociallogin

    def test_cadastro_local_fechado(self):
        """Ninguém se cadastra com senha.

        English:
            Nobody signs up with a password.
        """
        self.assertFalse(ContaAdapter().is_open_for_signup(self.request))

    def test_cadastro_social_aberto(self):
        """Quem vem do Google ou do GitHub ganha conta na hora.

        English:
            Whoever comes from Google or GitHub gets an account right away.
        """
        adapter = ContaSocialAdapter()
        self.assertTrue(
            adapter.is_open_for_signup(self.request, self._sociallogin())
        )

    def test_email_nao_verificado_recusado(self):
        """Provedor sem e-mail verificado: login recusado.

        English:
            Provider without a verified e-mail: login refused.
        """
        login = self._sociallogin(
            EmailAddress(email="ana@exemplo.com", verified=False, primary=True)
        )
        with self.assertRaises(ImmediateHttpResponse):
            ContaSocialAdapter().pre_social_login(self.request, login)

    def test_sem_email_recusado(self):
        """Provedor sem e-mail nenhum: login recusado.

        English:
            Provider with no e-mail at all: login refused.
        """
        with self.assertRaises(ImmediateHttpResponse):
            ContaSocialAdapter().pre_social_login(
                self.request, self._sociallogin()
            )

    def test_usa_email_principal_verificado(self):
        """O e-mail da conta é o principal verificado.

        English:
            The account e-mail is the verified primary one.
        """
        login = self._sociallogin(
            EmailAddress(email="velho@exemplo.com", verified=False),
            EmailAddress(email="extra@exemplo.com", verified=True),
            EmailAddress(email="ana@exemplo.com", verified=True, primary=True),
        )
        ContaSocialAdapter().pre_social_login(self.request, login)
        self.assertEqual(login.user.email, "ana@exemplo.com")
        self.assertEqual(len(login.email_addresses), 1)
