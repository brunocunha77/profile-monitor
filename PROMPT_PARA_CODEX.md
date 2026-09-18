# Prompt para iniciar o Profile Monitor pelo chat

Copie e cole todo o texto abaixo em uma nova sessao do Codex ou Cloud. O operador final deve interagir somente pelo chat: nao deve editar arquivos, usar terminal ou abrir codigo.

```text
Prepare o Profile Monitor para uso LOCAL. O operador final nao vai editar .env, usar terminal, nem abrir codigo. Conduza tudo pelo chat e execute os comandos no ambiente disponivel.

Primeiro, clone o repositorio e entre na pasta:

git clone https://github.com/brunocunha77/profile-monitor.git
cd profile-monitor

Leia README.md e docs/ENVIRONMENT.md antes de executar uma coleta.

## Regra de interacao

Faca uma entrevista curta pelo chat. Pergunte apenas o que ainda nao estiver configurado e uma pergunta por vez. O operador deve responder no chat; voce deve gravar cada valor no .env local sem mostrar, repetir, incluir em logs ou commitar segredos. Nunca peça ao operador para abrir ou editar um arquivo.

Pergunte, nesta ordem:

1. A pessoa quer apenas abrir a interface agora ou configurar uma coleta real?
2. Se configurar coleta real: qual e o usuario da conta coletora, sem @?
3. Qual e a senha da conta coletora?
4. Qual e a URL completa do proxy HTTP fixo dessa conta, no formato http://usuario:senha@host:porta?
5. Ela quer persistencia apenas naquele computador ou uma base externa?
6. Se escolher base externa: qual e a DATABASE_URL e qual identificador deve ser usado em MONITOR_WORKSPACE_ID? Nao mostre a URL depois de recebida.

Gere MONITOR_CONTROL_API_TOKEN localmente com pelo menos 32 caracteres. Crie ou atualize .env a partir de .env.example usando as respostas. Para modo apenas interface, deixe COLLECTOR_USERNAME, COLLECTOR_PASSWORD e COLLECTOR_PROXY_URL vazios. Para persistencia local, deixe DATABASE_URL vazio. Use MONITOR_SESSION_ROOT=./state.

Instale as dependencias:

- python -m pip install -r collector/requirements.txt
- Se DATABASE_URL comecar com postgresql://, execute tambem python -m pip install -r collector/requirements-postgres.txt
- cd web; npm install; cd ..

Inicie e mantenha ativos os processos necessarios:

- python control_server.py
- python collector/manager.py
- cd web; npm run dev -- --host 127.0.0.1 --port 8081

Verifique que a API responde em http://127.0.0.1:3001/api/status. Informe ao operador somente a URL pronta do painel: http://127.0.0.1:8081. Se estiver em Cloud e essa URL nao puder ser acessada pelo operador, use o mecanismo de preview/porta encaminhada do ambiente e entregue a URL publica ou de preview gerada pelo ambiente.

Para testar coleta, explique no chat como adicionar um perfil e clicar manualmente em coletar na tela. Cada clique deve executar uma unica rodada; nao implemente tentativas automaticas.

Se houver checkpoint, feedback, desafio ou erro de autenticacao do Instagram, pare a rodada, mostre o erro real de forma compreensivel e diga qual acao manual o operador precisa tomar na propria conta. Nao tente contornar verificacoes, nao troque proxy automaticamente e nao repita o login.

Antes de encerrar, execute cd web; npm run build. Informe no chat: URL do painel, modo de persistencia usado, processos ativos, o que foi validado e qualquer bloqueio real. Nunca mostre senha, token, proxy ou DATABASE_URL.

A primeira coleta de um alvo cria o baseline. Apenas coletas posteriores podem apontar novos seguidores, curtidas ou comentarios. Sem DATABASE_URL, os dados persistem na pasta state/ mesmo depois de desligar localhost. Com DATABASE_URL, persistem na base configurada e sao separados por MONITOR_WORKSPACE_ID.
```

## Limite do chat comum

Esse fluxo requer Codex, Claude Code ou Cloud com permissao para clonar repositorios, criar arquivos e iniciar processos. Um chat sem acesso ao ambiente local nao consegue instalar ou executar o projeto sozinho.