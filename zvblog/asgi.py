"""Ponto de entrada ASGI do projeto, usado pelo servidor em produção.

Expõe a variável ``application`` que o servidor ASGI chama.

English:
    ASGI entry point of the project, used by the production server.

    Exposes the ``application`` variable that the ASGI server calls.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zvblog.settings")

application = get_asgi_application()
