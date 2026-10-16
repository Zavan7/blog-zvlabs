"""Ponto de entrada WSGI do projeto, usado pelo servidor em produção.

Expõe a variável ``application`` que o servidor WSGI chama.

English:
    WSGI entry point of the project, used by the production server.

    Exposes the ``application`` variable that the WSGI server calls.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zvblog.settings")

application = get_wsgi_application()
