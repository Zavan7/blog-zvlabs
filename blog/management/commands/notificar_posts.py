"""Comando que envia o e-mail dos posts publicados ainda não anunciados.

Rode pelo cron (por exemplo, a cada 15 minutos) para cobrir os posts
agendados com data futura.

English:
    Command that sends the e-mail of published posts not yet announced.

    Run it from cron (for example, every 15 minutes) to cover posts
    scheduled with a future date.
"""

from typing import Any

from django.core.management.base import BaseCommand

from blog.services import notificar_pendentes


class Command(BaseCommand):
    """Notifica os inscritos sobre posts publicados e não anunciados.

    English:
        Notifies subscribers about published, unannounced posts.
    """

    help = "Envia e-mail aos inscritos sobre posts ainda não anunciados."

    def handle(self, *args: Any, **options: Any) -> None:
        """Executa o envio e informa quantos e-mails saíram.

        Args:
            *args: argumentos posicionais (não usados).
            **options: opções do comando (não usadas).

        English:
            Runs the sending and reports how many e-mails went out.

            Args:
                *args: positional arguments (unused).
                **options: command options (unused).
        """
        enviados = notificar_pendentes()
        self.stdout.write(
            self.style.SUCCESS(f"{enviados} e-mail(s) enviados.")
        )
