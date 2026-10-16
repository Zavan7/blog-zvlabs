# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e versionamento semântico.

## [Não lançado]

### Adicionado

- Projeto Django 6.1 com `uv`, app `blog`, configuração por `.env`.
- Models `Assunto`, `Post`, `Comentario` e `Inscrito`.
- Listagem com título e resumo, filtro por assunto (`?assunto=`) e página do post.
- Markdown convertido com `markdown` e sanitizado com `nh3`.
- Login só por OAuth 2.0 (Google e GitHub) com `django-allauth`, aceitando apenas e-mail verificado.
- Comentários só para pessoas logadas, pendentes até aprovação no admin.
- Inscrição por e-mail com token de cancelamento e página de confirmação.
- E-mail aos inscritos a cada post publicado, uma vez por post, e comando `notificar_posts` para posts agendados.
- Admin restrito ao superusuário para publicar e moderar.
- Tema claro e noite e botão "Copiar" nos blocos de código.
- Testes de models, serviços, views, admin e adapter de login.

### Limitações conhecidas

- O visual ainda é provisório: falta aplicar o front-end de referência (etapa J).
- O envio de e-mail é síncrono; com muitos inscritos, salvar o post no admin fica mais lento.
