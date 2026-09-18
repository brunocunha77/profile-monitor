# Configuracao de ambiente

Copie `.env.example` para `.env` na raiz. O `.env` e as sessoes locais sao ignorados pelo Git.

```powershell
Copy-Item .env.example .env
```

## Arquitetura local

| Processo | Porta | Comando |
| --- | --- | --- |
| Control API | `3001` | `python control_server.py` |
| Interface | `8081` | `cd web; npm install; npm run dev` |
| Manager de rodadas | sem porta | `python collector/manager.py` |

Abra `http://127.0.0.1:8081` no navegador. O manager e o Control API devem ficar no mesmo computador para que a rodada manual seja consumida.

## `.env` minimo para apenas abrir a interface

```env
MONITOR_PORT=3001
MONITOR_CONTROL_API_URL=http://127.0.0.1:3001
MONITOR_CONTROL_API_TOKEN=gere_uma_chave_aleatoria_com_32_ou_mais_caracteres
COLLECTOR_USERNAME=
COLLECTOR_PASSWORD=
COLLECTOR_PROXY_URL=
MONITOR_SESSION_ROOT=./state
```

Gere o token assim:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Sem conta, senha e proxy, a interface abre para navegar e cadastrar alvos, mas o botao de coleta permanece desabilitado.

## `.env` para rodadas manuais

```env
MONITOR_PORT=3001
MONITOR_CONTROL_API_URL=http://127.0.0.1:3001
MONITOR_CONTROL_API_TOKEN=uma_mesma_chave_aleatoria_com_32_ou_mais_caracteres
COLLECTOR_USERNAME=usuario_da_conta_coletora_sem_arroba
COLLECTOR_PASSWORD=senha_da_conta_coletora
COLLECTOR_PROXY_URL=http://usuario:senha@host:porta
MONITOR_SESSION_ROOT=./state
FOLLOWERS_WINDOW=80
RECENT_MEDIA_LIMIT=4
LIKERS_PER_MEDIA=30
PROFILE_ENRICHMENTS_PER_RUN=12
WORKER_DISCOVERY_SECONDS=5
```

| Variavel | Regra |
| --- | --- |
| `MONITOR_CONTROL_API_TOKEN` | Mesma chave no Control API e manager; nunca enviar ao Git. |
| `COLLECTOR_USERNAME` | Conta coletora dedicada, sem `@`. |
| `COLLECTOR_PASSWORD` | Senha da conta coletora. |
| `COLLECTOR_PROXY_URL` | URL do proxy fixo usado somente pela conta coletora. Nao registrar a URL em logs, commits ou tickets. |
| `MONITOR_SESSION_ROOT` | Pasta persistente da sessao e do baseline; nao apague entre rodadas. |
| Limites de coleta | Comece com os valores do exemplo e ajuste com cautela. |

## Operacao local

1. Preencha o `.env`.
2. Instale Python: `python -m pip install -r collector/requirements.txt`.
3. Em um terminal, execute `python control_server.py`.
4. Em outro terminal, execute `python collector/manager.py`.
5. Em um terceiro terminal, execute `cd web; npm install; npm run dev`.
6. No navegador, adicione e confirme um perfil.
7. Clique no icone de atualizar do perfil para solicitar **uma** rodada manual.

Cada clique cria uma unica rodada. O manager nao repete a rodada automaticamente. Em checkpoint, feedback ou erro de autenticacao, o coletor informa a pausa e a proxima tentativa deve ser uma nova acao manual depois de resolver a conta no aplicativo oficial.

A primeira coleta de cada alvo cria o baseline e nao deve ser interpretada como novos sinais. Somente comparacoes posteriores identificam novos seguidores, curtidas e comentarios dentro das janelas configuradas.
## Persistencia opcional em banco

Sem `DATABASE_URL`, o monitor usa o modo local e grava em `state/control.json`. Desligar os processos nao apaga dados: alvos, baseline, sinais e oportunidades continuam nessa pasta. Mantenha a pasta `state/` ao atualizar ou mover o projeto.

Para persistir fora da maquina, informe uma `DATABASE_URL`. O banco e opcional; a interface e a coleta local continuam funcionando sem ele.

### SQLite

Boa opcao para um unico operador que quer um arquivo de banco separado:

```env
DATABASE_URL=sqlite:///./state/profile-monitor.sqlite3
MONITOR_WORKSPACE_ID=local
```

### PostgreSQL

Use quando quiser uma base central ou mais de um workspace. Instale o driver adicional e use uma chave de workspace distinta para cada usuario/cliente:

```powershell
python -m pip install -r collector/requirements-postgres.txt
```

```env
DATABASE_URL=postgresql://usuario:senha@host:5432/profile_monitor
MONITOR_WORKSPACE_ID=cliente-exemplo
```

`MONITOR_WORKSPACE_ID` separa os dados dentro da mesma base. A URL da base e segredo: mantenha-a somente no `.env`, nunca no Git.
