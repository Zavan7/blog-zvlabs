"""Configurações do projeto Blog ZV Labs.

Todo valor que muda entre máquinas ou é segredo vem do ``.env``. O arquivo
``.env.example`` lista as chaves esperadas.

English:
    Settings for the Blog ZV Labs project.

    Every value that changes between machines or is a secret comes from
    ``.env``. The ``.env.example`` file lists the expected keys.
"""

import os
from pathlib import Path
from typing import Any

import django_stubs_ext
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Permite escrever ModelAdmin[Post] e ModelForm[Post] (tipos genéricos que o
# mypy entende) sem quebrar em tempo de execução.
django_stubs_ext.monkeypatch()

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(nome: str, padrao: str = "False") -> bool:
    """Lê uma variável de ambiente como booleano.

    ``os.getenv`` sempre devolve texto, e qualquer texto não vazio é
    verdadeiro. Por isso a comparação é feita contra valores aceitos.

    Args:
        nome: nome da variável.
        padrao: valor usado quando a variável não existe.

    Returns:
        ``True`` para ``true`` ou ``1`` (sem diferenciar maiúsculas).

    English:
        Reads an environment variable as a boolean.

        ``os.getenv`` always returns text, and any non-empty text is truthy.
        That is why the value is compared against accepted values.

        Args:
            nome: variable name.
            padrao: value used when the variable is missing.

        Returns:
            ``True`` for ``true`` or ``1`` (case-insensitive).
    """
    return os.getenv(nome, padrao).strip().lower() in ("true", "1")


def env_lista(nome: str, padrao: str = "") -> list[str]:
    """Lê uma variável de ambiente separada por vírgulas como lista.

    Args:
        nome: nome da variável.
        padrao: valor usado quando a variável não existe.

    Returns:
        Itens sem espaços nas pontas, ignorando os vazios.

    English:
        Reads a comma-separated environment variable as a list.

        Args:
            nome: variable name.
            padrao: value used when the variable is missing.

        Returns:
            Items stripped of surrounding spaces, ignoring empty ones.
    """
    return [
        item.strip()
        for item in os.getenv(nome, padrao).split(",")
        if item.strip()
    ]


SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    raise ImproperlyConfigured("Defina SECRET_KEY no arquivo .env.")

DEBUG = env_bool("DEBUG")
ALLOWED_HOSTS = env_lista("ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_lista("CSRF_TRUSTED_ORIGINS")

# Endereço público do blog, usado nos links dos e-mails (sem barra final).
# Fora do modo de desenvolvimento é obrigatório: sem ele os e-mails sairiam
# com links para 127.0.0.1.
SITE_URL = os.getenv("SITE_URL", "").strip().rstrip("/")
if not SITE_URL:
    if not DEBUG:
        raise ImproperlyConfigured("Defina SITE_URL no arquivo .env.")
    SITE_URL = "http://127.0.0.1:8000"

# Portfólio ZV Labs (Maestro), para o menu e o rodapé. Vazio esconde os links.
PORTFOLIO_URL = os.getenv("PORTFOLIO_URL", "").strip()

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.github",
    "blog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "zvblog.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "blog.context_processors.inscricao",
                "blog.context_processors.links",
            ],
        },
    },
]

WSGI_APPLICATION = "zvblog.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation."
        "MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation."
        "CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation."
        "NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Login social (django-allauth) ---------------------------------------
# Leitores entram só por OAuth 2.0 (Google e GitHub). Não existe cadastro
# nem login com senha para eles: SOCIALACCOUNT_ONLY desliga essas rotas.
# O admin continua com o login próprio do Django, só para o superusuário.

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

SOCIALACCOUNT_ONLY = True
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*"]
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_ADAPTER = "blog.adapters.ContaAdapter"

SOCIALACCOUNT_ADAPTER = "blog.adapters.ContaSocialAdapter"
# A verificação do e-mail é feita pelo provedor; o adapter recusa e-mail
# que o provedor não marcou como verificado.
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_EMAIL_REQUIRED = True
# Quem entrou pelo Google e depois entra pelo GitHub com o mesmo e-mail
# verificado cai na mesma conta (seguro porque só aceitamos verificado).
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = False
SOCIALACCOUNT_STORE_TOKENS = False
SOCIALACCOUNT_PROVIDERS: dict[str, dict[str, Any]] = {
    "google": {
        "APPS": [
            {
                "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
                "secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
            }
        ],
        "SCOPE": ["openid", "email", "profile"],
    },
    "github": {
        "APPS": [
            {
                "client_id": os.getenv("GITHUB_CLIENT_ID", ""),
                "secret": os.getenv("GITHUB_CLIENT_SECRET", ""),
            }
        ],
        "SCOPE": ["user:email"],
    },
}

LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "post_list"
ACCOUNT_LOGOUT_REDIRECT_URL = "post_list"

# --- E-mail ----------------------------------------------------------------
# Em desenvolvimento o e-mail aparece no terminal (console). Em produção,
# EMAIL_BACKEND=smtp e os dados do servidor SMTP vêm do .env.

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL", "Blog ZV Labs <nao-responda@localhost>"
)

if os.getenv("EMAIL_BACKEND", "console").strip().lower() == "smtp":
    MAILERS: dict[str, dict[str, Any]] = {
        "default": {
            "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "OPTIONS": {
                "host": os.getenv("EMAIL_HOST", ""),
                "port": int(os.getenv("EMAIL_PORT", "587")),
                "username": os.getenv("EMAIL_HOST_USER", ""),
                "password": os.getenv("EMAIL_HOST_PASSWORD", ""),
                "use_tls": env_bool("EMAIL_USE_TLS", "True"),
                "timeout": 30,
            },
        },
    }
else:
    MAILERS = {
        "default": {
            "BACKEND": "django.core.mail.backends.console.EmailBackend",
        },
    }

# --- Log ---------------------------------------------------------------------
# Mensagens do app (como a falha ao enviar e-mail aos inscritos) vão para o
# terminal, que o servidor de produção guarda (systemd, Docker).

LOGGING: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simples": {
            "format": "{asctime} {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simples",
        },
    },
    "loggers": {
        "blog": {"handlers": ["console"], "level": "INFO"},
    },
}

# --- Segurança em produção ---------------------------------------------------

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", "True")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
