# Blog ZV Labs

Blog pessoal do Vitor, em um projeto Django **separado** do Maestro. Ele é ligado ao portfólio ZV Labs por um botão (a URL fica em `BLOG_URL` no `.env` do Maestro, não neste projeto).

## Como trabalhar comigo

- Fale em português do Brasil.
- Aula guiada: **uma etapa do roteiro por vez**. Depois do código, explique o porquê das decisões em poucas linhas, diga como testar, o que devo ver, e peça o resultado.
- Antes de mudar a arquitetura, proponha, explique o custo e deixe eu decidir.
- Placeholders em comandos (usuário, caminho) vêm marcados como "troque por ...".
- Erros: leia o traceback inteiro, aponte arquivo, linha e causa, e só então a correção.
- Ideia nova no meio de uma etapa não entra nela: anote para depois.

## Stack

Ubuntu, Python 3.14, `uv` (nunca `pip` direto), Django 6.1, SQLite em desenvolvimento, `django-allauth` para login social, `markdown` + `nh3` para o texto dos posts, `ruff` e `mypy` com `django-stubs`. Front-end com Django Templates e CSS puro.

## O que o blog faz

- Posts em Markdown, com título, resumo (descrição curta), assuntos (tags) e data de publicação. A listagem mostra título e resumo e filtra por assunto.
- Login **só por OAuth 2.0** (Google e GitHub). Não existe cadastro com senha.
- Inscrição: pessoa logada vira `Inscrito` (ligado ao `User`) com token de cancelamento. Todo e-mail traz o link de cancelar.
- Comentários: só logado, entram como pendentes e passam por moderação no admin.
- Ao publicar um post, os inscritos recebem e-mail com título, resumo e link. O envio acontece uma vez por post (`notificado_em`).

## Front-end de referência

`docs/frontend/blog-zvlabs-v4.html` é o modelo aprovado. Ele é a fonte do visual:

- O bloco `<style>` vira `static/blog/blog.css` (tokens em `:root`, tema claro e noite).
- As duas vistas (listagem e post) viram dois templates com `{% extends %}` de um `base.html`.
- O filtro por assunto vira `?assunto=django` resolvido no servidor.
- O painel de inscrição do cabeçalho envia POST para a rota de login social de cada provedor.
- O script de troca de vista e de filtro é só do protótipo e não entra no projeto. O de tema e o do botão "Copiar" ficam.
- Não mude o visual sem eu pedir.

## Convenções que valem sempre

1. Toda ação que altera dados é POST com `{% csrf_token %}`. Nunca link GET.
2. Rotas sempre pelo nome (`{% url %}`, `reverse`, `redirect("nome")`). Nomes de rota em inglês.
3. Permissão verificada na view. Esconder o botão é só aparência.
4. `on_delete` escolhido pelo significado: histórico usa `PROTECT`; referência opcional usa `SET_NULL`.
5. Opções fixas com `TextChoices`, valores em português sem acento.
6. Formulários com `ModelForm`. Campos que o backend define ficam fora de `fields`.
7. Segredos no `.env`; `.env` e `db.sqlite3` no `.gitignore`. Nunca coloque credenciais OAuth no código.
8. Templates com uma tag do Django por linha; `{% extends %}` na primeira linha.
9. Regra de negócio usada em mais de um lugar mora numa função de serviço, sem HTTP.
10. Toda ação dá feedback com `messages.success` ou `messages.error`, com o mesmo verbo do botão.
11. Aceitar só e-mail verificado pelo provedor; no GitHub pedir o escopo `user:email`. Cadastro local desligado.
12. Consultas sem N+1 (`select_related`, `prefetch_related`).
13. Commits em português, dizendo o que mudou e por quê.
14. **PEP 8, type hints e docstrings** em todo código Python: `ruff format`, `ruff check`, `mypy` sem erros; docstring estilo Google em português com a seção `English:` traduzida.
15. Testes de model e de view, incluindo os caminhos negativos (deslogado, sem permissão, 404). `uv run manage.py test` passando antes de cada commit.

## Roteiro (uma etapa por vez)

A. Projeto, app `blog`, `.env`, `.gitignore`
B. Models: `Post`, `Comentario` (ligado ao `User`), `Inscrito` (ligado ao `User`, token de cancelamento)
C. Admin: posts, moderação de comentários, inscritos
D. Listagem (título, resumo, filtro por assunto) e página do post
E. Markdown seguro (`markdown` + `nh3`)
F. Login social com `django-allauth` (Google e GitHub)
G. Inscrição e cancelamento por link
H. Comentários (só logado, moderação)
I. E-mail ao publicar
J. Visual final a partir do front-end de referência, tema e botão no Maestro
K. Testes
L. Deploy e segurança (HTTPS, `ALLOWED_HOSTS`, URIs de callback, SMTP)
M. README, CHANGELOG, commit

Etapa atual: **J** (A a I prontas na base inicial; falta aplicar o front-end de referência).
