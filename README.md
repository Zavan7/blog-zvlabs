# Blog ZV Labs

Blog pessoal do Vitor, em Django. Projeto separado do Maestro, ligado ao portfólio ZV Labs por um botão.

**Versão atual:** em desenvolvimento (seção "Não lançado" do [CHANGELOG](CHANGELOG.md)).

## O que faz

- **Posts em Markdown**, com título, resumo, assuntos e data de publicação. A listagem filtra por assunto (`/?assunto=django`). O HTML gerado passa pelo `nh3`, que remove `<script>`, eventos e links `javascript:`.
- **Publicação só pelo dono**: posts são escritos no admin (`/admin/`) e só o superusuário pode criar, editar, publicar ou moderar.
- **Login só por OAuth 2.0** (Google e GitHub), com `django-allauth`. Não existe cadastro nem login com senha para leitores, e só entra quem tem e-mail verificado pelo provedor.
- **Comentários** só para quem está logado. Todo comentário nasce pendente e só aparece depois de aprovado no admin (ações "Aprovar" e "Rejeitar").
- **Inscrição por e-mail**: a pessoa logada clica em "Inscrever-se". A cada post publicado, cada inscrito recebe um e-mail com título, resumo, link e o link de cancelamento. O envio acontece uma única vez por post (`notificado_em`).

## Rodar localmente

Requisitos: [uv](https://docs.astral.sh/uv/) (ele instala o Python 3.14).

```bash
git clone https://github.com/Zavan7/blog-zvlabs.git
cd blog-zvlabs
uv sync
cp .env.example .env
```

Gere uma `SECRET_KEY` e cole no `.env`:

```bash
uv run python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

```bash
uv run manage.py migrate
uv run manage.py createsuperuser
uv run manage.py runserver
```

Abra `http://127.0.0.1:8000/admin/`, crie um assunto e um post com status "Publicado". Com `EMAIL_BACKEND=console`, os e-mails aparecem no terminal do `runserver`.

## Login com Google e GitHub

As credenciais ficam só no `.env`, nunca no código nem no banco.

**Google** ([console.cloud.google.com](https://console.cloud.google.com/) → APIs e serviços → Credenciais → Criar ID do cliente OAuth → Aplicativo da Web):

- URI de redirecionamento autorizado: `http://127.0.0.1:8000/contas/google/login/callback/`
- Copie o ID e a chave secreta para `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET`.

**GitHub** ([github.com/settings/developers](https://github.com/settings/developers) → New OAuth App):

- Homepage URL: `http://127.0.0.1:8000`
- Authorization callback URL: `http://127.0.0.1:8000/contas/github/login/callback/`
- Copie para `GITHUB_CLIENT_ID` e `GITHUB_CLIENT_SECRET`. O escopo `user:email` já está configurado.

Em produção, cadastre as mesmas rotas com o domínio real e `https://`.

O admin (`/admin/`) continua com o login próprio do Django, só para o superusuário.

## E-mail a cada post

1. Ao salvar no admin um post "Publicado" com data que já chegou, o e-mail sai depois do commit da transação.
2. Post agendado (data futura) é enviado pelo comando abaixo quando a data chegar. Em produção, agende no cron:

```bash
# troque /caminho/do/blog-zvlabs pela pasta real e SEU_USUARIO pelo seu usuário
*/15 * * * * cd /caminho/do/blog-zvlabs && /home/SEU_USUARIO/.local/bin/uv run manage.py notificar_posts
```

Para envio real, use `EMAIL_BACKEND=smtp` e preencha `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` e `DEFAULT_FROM_EMAIL` no `.env`. Com Gmail, use uma senha de app, não a senha da conta.

O link de cancelamento abre uma página de confirmação (o cancelamento é um POST), porque leitores de e-mail e antivírus visitam links sozinhos.

## Qualidade

```bash
uv run ruff format .
uv run ruff check .
uv run mypy .
uv run manage.py test
```

## Andamento

| Etapa | Situação |
|---|---|
| A. Projeto, app, `.env`, `.gitignore` | pronto |
| B. Models | pronto |
| C. Admin (posts, moderação, inscritos) | pronto |
| D. Listagem, filtro e página do post | pronto |
| E. Markdown seguro | pronto |
| F. Login social (Google e GitHub) | pronto (falta cadastrar as credenciais) |
| G. Inscrição e cancelamento | pronto |
| H. Comentários com moderação | pronto |
| I. E-mail ao publicar | pronto |
| J. Visual do front-end de referência | **pendente**: `docs/frontend/blog-zvlabs-v4.html` ainda não está no repositório; o CSS atual é provisório |
| K. Testes | 59 testes (models, serviços, views, admin, adapter) |
| L. Deploy e segurança | settings de produção prontos; falta hospedagem, HTTPS e SMTP |
| M. README, CHANGELOG, commit | pronto |
