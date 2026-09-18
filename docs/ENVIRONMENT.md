# Configuracao de ambiente

Crie um arquivo `.env` na raiz do repositorio copiando `.env.example`. Ele nunca deve ser enviado ao Git.

```powershell
Copy-Item .env.example .env
```

## Para abrir somente o dashboard local

Para navegar e testar o fluxo da tela, preencha apenas estas variaveis. Nao informe senha, proxy nem conta coletora nesta etapa.

```env
MONITOR_PORT=8081
MONITOR_CONTROL_API_URL=http://127.0.0.1:8081
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

O dashboard permite cadastrar perfis e solicitar uma rodada. Sem o manager, a solicitacao permanece como `requested` e nenhuma coleta externa e executada.

## Para habilitar uma coleta manual controlada

| Variavel | Uso | Como preencher |
| --- | --- | --- |
| `MONITOR_CONTROL_API_TOKEN` | Autentica manager e Control API. | Use a mesma chave aleatoria do servidor e do manager. |
| `COLLECTOR_USERNAME` | Conta coletora autorizada. | Nome de usuario sem `@`. |
| `COLLECTOR_PASSWORD` | Credencial da conta coletora. | Senha da conta. Nunca cole em documentacao, logs ou commits. |

## Variaveis de rede e execucao

| Variavel | Uso | Preenchimento local |
| --- | --- | --- |
| `MONITOR_PORT` | Porta do dashboard/Control API. | `8081`, exceto se ja estiver ocupada. |
| `MONITOR_CONTROL_API_URL` | URL usada pelo manager. | `http://127.0.0.1:8081` no local. |
| `COLLECTOR_PROXY_URL` | Proxy fixo da conta coletora. | Deixe vazio em demonstracao; em producao use a URL fornecida pelo provedor sem expo-la. |
| `MONITOR_SESSION_ROOT` | Diretorio de sessoes e baseline. | `./state` no local; volume Docker em producao. |
| `COLLECTOR_STATE_DIR` | Diretorio do worker por conta. | `./state/client-1` para teste local. |
| `COLLECTOR_TARGET_IDS` | Alvo da rodada manual. | Deixe vazio; o manager preenche durante a rodada. |
| `FOLLOWERS_WINDOW` | Tamanho da janela observada. | Comece com `80`. |
| `RECENT_MEDIA_LIMIT` | Publicacoes recentes por rodada. | Comece com `4`. |
| `LIKERS_PER_MEDIA` | Curtidas observadas por publicacao. | Comece com `30`. |
| `PROFILE_ENRICHMENTS_PER_RUN` | Perfis detalhados por rodada. | Comece com `12`. |

## Rodar localmente

1. Copie `.env.example` para `.env`.
2. Para somente visualizar o painel, mantenha usuario, senha e proxy vazios.
3. Instale dependencias: `pip install -r collector/requirements.txt`.
4. Inicie o Control Plane: `python control_server.py`.
5. Abra `http://127.0.0.1:8081`.
6. Para uma coleta manual, preencha as credenciais no `.env` e inicie o manager: `python collector/manager.py`.

O manager nao deve ser iniciado sem as variaveis obrigatorias. A interface nao mostra senha, token ou URL de proxy.
