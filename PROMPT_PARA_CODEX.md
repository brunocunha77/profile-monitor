# Prompt para iniciar o Profile Monitor

Copie e cole o texto abaixo em uma nova sessao do Codex ou em um agente que tenha acesso a este repositorio.

```text
Trabalhe no repositorio Profile Monitor. Seu objetivo e preparar e iniciar o ambiente LOCAL para monitoramento manual de perfis do Instagram. Nao altere a arquitetura, nao envie dados para producao e nao use credenciais existentes no Git, em logs ou em commits.

1. Leia README.md e docs/ENVIRONMENT.md antes de executar qualquer coleta.
2. Confira se existem Python 3.11+ e Node.js 20+ no ambiente.
3. Se ainda nao existir, crie .env a partir de .env.example. Nunca mostre nem registre valores secretos.
4. Peça ao operador para preencher manualmente no .env:
   - MONITOR_CONTROL_API_TOKEN: gere uma chave com pelo menos 32 caracteres;
   - COLLECTOR_USERNAME: conta coletora dedicada, sem @;
   - COLLECTOR_PASSWORD: senha dessa conta;
   - COLLECTOR_PROXY_URL: proxy HTTP fixo associado a essa conta;
   - MONITOR_SESSION_ROOT=./state;
   - DATABASE_URL: opcional. Vazio usa state/control.json local; sqlite:///./state/profile-monitor.sqlite3 usa SQLite; postgresql://... usa PostgreSQL;
   - MONITOR_WORKSPACE_ID: opcional. Use uma chave diferente por cliente quando compartilhar a mesma base.
   Para somente visualizar a interface, as tres variaveis COLLECTOR podem ficar vazias.
5. Instale as dependencias:
   - python -m pip install -r collector/requirements.txt
   - Se DATABASE_URL comecar com postgresql://, execute tambem python -m pip install -r collector/requirements-postgres.txt
   - cd web; npm install
6. Inicie e mantenha ativos em terminais separados:
   - python control_server.py
   - python collector/manager.py
   - cd web; npm run dev -- --host 127.0.0.1 --port 8081
7. Confirme que a API responde em http://127.0.0.1:3001/api/status e informe ao operador que o painel esta em http://127.0.0.1:8081.
8. Para testar coleta, espere o operador adicionar um perfil e clicar manualmente em coletar. Cada clique deve executar apenas uma rodada; nao implemente tentativas automaticas.
9. Se houver checkpoint, feedback, desafio ou erro de autenticacao do Instagram, pare a rodada e mostre o erro real. Nao tente contornar verificacoes, nao troque proxy automaticamente e nao repita o login.
10. Antes de encerrar, verifique a compilacao com cd web; npm run build e informe: processos ativos, URL local, o que foi validado e qualquer bloqueio real.

A primeira coleta de um alvo cria o baseline. Apenas coletas posteriores podem apontar novos seguidores, curtidas ou comentarios. Sinais de follow_observed e like sao observacoes dentro da janela configurada, nao uma afirmacao do horario exato da acao.

Sem DATABASE_URL, dados persistem na pasta state/ mesmo depois de desligar localhost. Com DATABASE_URL, dados persistem na base configurada e sao separados por MONITOR_WORKSPACE_ID.
```

## Observacao para ambientes cloud

O painel pode ser instalado em cloud, mas o fluxo descrito acima e deliberadamente local. Uma coleta real so deve ser iniciada quando a conta coletora, a sessao e o proxy configurados pertencerem ao operador e estiverem autorizados para aquele ambiente. Nao mova automaticamente uma sessao local para VPS ou cloud.