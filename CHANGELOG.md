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
- Visual do front-end de referência: post em destaque na listagem, ficha do post, índice "Neste post", tempo de leitura, navegação anterior/próximo e blocos de código com moldura.
- Link para o portfólio no menu e no rodapé (`PORTFOLIO_URL`).
- Constraint `post_publicado_tem_data` (migração `0002`): o banco recusa post publicado sem data.
- Log do app `blog` no terminal (`LOGGING`).
- `coverage` como dependência de desenvolvimento.

### Alterado

- A data de publicação que faltar é preenchida em `Post.clean()`, e não mais no admin.
- Um `#` no texto do post vira `<h2>` e entra no índice; o único `<h1>` da página é o título.
- Os ids dos subtítulos levam o prefixo `secao-` (por exemplo `#secao-o-problema`).
- O Markdown é convertido uma vez por página (HTML e índice juntos).
- A consulta da inscrição no cabeçalho só roda quando o template a usa.
- `SITE_URL` é obrigatório com `DEBUG=False`.

### Corrigido

- O campo `next` da inscrição aceitava `/\site`, que o navegador trata como outro domínio (redirecionamento aberto). Agora usa `url_has_allowed_host_and_scheme`.
- Um subtítulo como `## Comentários` repetia o id `#comentarios` da página.
- Posts publicados juntos ("Publicar agora") pulavam um ao outro na navegação anterior/próximo.
- Falha de SMTP ao publicar virava erro 500 no admin; agora vai para o log e o comando `notificar_posts` reenvia.

### Limitações conhecidas

- O envio de e-mail é síncrono; com muitos inscritos, salvar o post no admin fica mais lento.
- O envio é marcado por post: se o SMTP cair no meio, quem já recebeu recebe de novo.
