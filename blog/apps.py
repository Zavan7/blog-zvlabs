"""Configuração do app blog.

English:
    Blog app configuration.
"""

from django.apps import AppConfig


class BlogConfig(AppConfig):
    """Registra o app blog no Django.

    English:
        Registers the blog app in Django.
    """

    name = "blog"
    verbose_name = "Blog"
