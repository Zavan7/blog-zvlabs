# Blog ZV Labs

Blog pessoal do Vitor, em Django. Projeto separado do Maestro, ligado ao portfólio ZV Labs por um botão.

**Versão atual:** em desenvolvimento (seção "Não lançado" do [CHANGELOG](CHANGELOG.md)).

## O que faz

- **Posts em Markdown**, com título, resumo, assuntos e data de publicação. A listagem destaca o post mais novo, mostra o tempo de leitura e filtra por assunto (`/?assunto=django`).
- **Página do post** com ficha (autor, data, leitura, assuntos), índice "Neste post", navegação para o post anterior e o próximo, e blocos de código com linguagem, linhas numeradas e botão "Copiar".
- **Markdown seguro**: o HTML passa pelo `nh3`, que remove `<script>`, eventos e links `javascript:`. Um `#` no texto vira `<h2>` (o `<h1>` da página é o título do post), e os subtítulos ganham ids com o prefixo `secao-` para não repetir ids da página.
- **Publicação só pelo dono**: posts são escritos no admin (`/admin/`) e só o superusuário pode criar, editar, publicar ou moderar. Post publicado sem data recebe a data de agora, e o banco recusa um post publicado sem data.
- **Login só por OAuth 2.0** (Google e GitHub), com `django-allauth`. Não existe cadastro nem login com senha para leitores, e só entra quem tem e-mail verificado pelo provedor.
- **Comentários** só para quem está logado. Todo comentário nasce pendente e só aparece depois de aprovado no admin (ações "Aprovar" e "Rejeitar").
- **Inscrição por e-mail**: a pessoa logada clica em "Inscrever". A cada post publicado, cada inscrito recebe um e-mail com título, resumo, link e o link de cancelamento. O envio acontece uma única vez por post (`notificado_em`).
- **Visual** do front-end de referência ([docs/frontend/blog-zvlabs-v4.html](docs/frontend/blog-zvlabs-v4.html)), com tema dia e noite e link para o portfólio no menu e no rodapé.

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

### Variáveis do `.env`

A lista completa está no [.env.example](.env.example). As que mais importam:

| Variável | Para quê |
|---|---|
| `SECRET_KEY` | Obrigatória. Sem ela o projeto não sobe. |
| `DEBUG` | `True` só em desenvolvimento. |
| `SITE_URL` | Endereço público, usado nos links dos e-mails. Obrigatório com `DEBUG=False`. |
| `PORTFOLIO_URL` | Link do portfólio no menu e no rodapé. Vazio esconde os links. |
| `GOOGLE_*`, `GITHUB_*` | Credenciais OAuth (veja abaixo). |
| `EMAIL_*` | `console` em desenvolvimento, `smtp` em produção. |

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

Se o SMTP falhar, o post continua salvo, o erro vai para o log (terminal) e `notificado_em` volta a vazio. O comando `notificar_posts` tenta de novo na próxima rodada.

O link de cancelamento abre uma página de confirmação (o cancelamento é um POST), porque leitores de e-mail e antivírus visitam links sozinhos.

## Qualidade

```bash
uv run ruff format .
uv run ruff check .
uv run mypy .
uv run manage.py test
```

Cobertura dos testes:

```bash
uv run coverage run manage.py test
uv run coverage report --include="blog/*" --omit="blog/tests/*,blog/migrations/*"
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
| J. Visual do front-end de referência | pronto neste repositório; falta o botão no Maestro (`BLOG_URL` no `.env` de lá) |
| K. Testes | 93 testes, 100% de cobertura no app `blog` |
| L. Deploy e segurança | settings de produção prontos; falta hospedagem, HTTPS, SMTP e cron |
| M. README, CHANGELOG, commit | em andamento |

## Pendências técnicas

### Etapa L (deploy e segurança)

- [ ] Hospedagem com HTTPS, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` e `SITE_URL` com o domínio real.
- [ ] `SECURE_HSTS_SECONDS` maior que zero, depois de confirmar que o HTTPS funciona.
- [ ] SMTP de verdade (`EMAIL_BACKEND=smtp`), para o `manage.py check --deploy` passar sem erros.
- [ ] Cron do `notificar_posts`, sem o qual os posts agendados não notificam.
- [ ] Definir como servir os arquivos estáticos (WhiteNoise ou servidor web) e se o SQLite fica em produção.
- [ ] Content Security Policy (nativa no Django 6). Falta tratar o script inline do tema, no `<head>` do `base.html`.
- [ ] `List-Unsubscribe-Post: List-Unsubscribe=One-Click` (exigido por Gmail e Yahoo), com uma rota POST de cancelamento direto.
- [ ] URIs de callback do OAuth cadastradas com o domínio real.

### Decisões em aberto

- [ ] Limite de comentários pendentes por pessoa (hoje não há).
- [ ] Fontes Geist hospedadas no próprio blog, em vez do Google Fonts (privacidade/LGPD; mexe no visual).
- [ ] Guardar os minutos de leitura num campo, para a listagem não carregar o texto inteiro de cada post (precisa de migração).

### Limites aceitos

- O envio é marcado por post, não por inscrito: se o SMTP cair no meio da lista, quem já recebeu recebe de novo na próxima tentativa. Com poucos inscritos o risco é pequeno; se crescer, a saída é um registro de envio por inscrito.
- O envio de e-mail é síncrono: com muitos inscritos, salvar o post no admin fica mais lento.
