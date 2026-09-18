# Profile Monitor

Servico independente para monitorar sinais publicos de perfis do Instagram escolhidos por cada workspace.

## Limites operacionais

- Uma conta coletora e um proxy fixo por workspace.
- A coleta e manual: uma rodada, um alvo por vez.
- A conta e pausada imediatamente em checkpoint, feedback ou erro de autenticacao.
- Sessao, SQLite e credenciais nunca entram no Git.
- `follow_observed` e `like` indicam primeira observacao dentro da janela; nao afirmam o horario exato da acao.

## Dashboard local

Execute `python control_server.py` e abra `http://127.0.0.1:8081`. A tela permite cadastrar alvos e solicitar uma rodada manual. Ela nao inicia o collector sem o manager e as variaveis configuradas.

Veja [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md), inclusive a persistência opcional em SQLite ou PostgreSQL para preencher `.env`. Para entregar o repositório a outro operador ou iniciar em uma nova sessão sem editar arquivos, use [PROMPT_PARA_CODEX.md](PROMPT_PARA_CODEX.md).

## Contrato da Control API

O monitor nao depende do Sales OS. Ele precisa de uma Control API que disponibilize:

- `POST /v1/workers/claim`: devolve rodadas manuais pendentes e credenciais de execucao pelo canal interno autenticado.
- `GET {webhook_url}/targets`: devolve alvos ativos da rodada.
- `PATCH {webhook_url}/targets/:id/status`: recebe status e metadados coletados.
- `POST {webhook_url}`: recebe sinais coletados.
- `PATCH {webhook_url}/connection`: recebe inicio, conclusao, checkpoint ou erro da rodada.

O Sales OS pode implementar esse contrato por adaptador HTTP, mas nao faz parte deste repositorio.

## Desenvolvimento

1. Copie `.env.example` para `.env` e preencha somente um ambiente de teste autorizado.
2. Instale `pip install -r collector/requirements.txt`.
3. Execute `python control_server.py` para o painel ou `python collector/manager.py` para consumir rodadas manuais.
4. Nunca use contas, proxies, cookies ou arquivos de sessao de producao no Git.
