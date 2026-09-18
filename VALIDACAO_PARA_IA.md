# Prompt de validacao para entrega

Copie e cole o texto abaixo na mesma sessao de Codex ou Cloud depois da instalacao. Ele serve para verificar o ambiente antes de entregar o acesso ao cliente.

```text
Faca uma validacao de entrega do Profile Monitor ja instalado. Nao execute coleta no Instagram, nao solicite senha novamente e nunca mostre qualquer segredo do .env.

Execute e informe um relatorio objetivo com APROVADO, ATENCAO ou BLOQUEADO para cada item:

1. Repositorio: confirme que a pasta atual e um clone valido de https://github.com/brunocunha77/profile-monitor.git e que nao existem mudancas locais inesperadas.
2. Ambiente: confirme Python 3.11+ e Node.js 20+.
3. Configuracao: verifique apenas a presenca das chaves MONITOR_CONTROL_API_TOKEN, MONITOR_SESSION_ROOT, DATABASE_URL e MONITOR_WORKSPACE_ID. Para coleta real, verifique apenas se COLLECTOR_USERNAME, COLLECTOR_PASSWORD e COLLECTOR_PROXY_URL estao preenchidos. Nunca mostre valores.
4. Persistencia: informe o modo configurado:
   - DATABASE_URL vazio: arquivo local state/control.json;
   - sqlite:///: SQLite;
   - postgresql://: PostgreSQL.
   Confirme que o caminho local state/ existe quando o modo for local ou SQLite.
5. Dependencias: execute python -m py_compile control_server.py storage.py e cd web; npm run build.
6. API: com o servidor em execucao, consulte http://127.0.0.1:3001/api/status e confirme resposta HTTP 200. Nao imprima o JSON inteiro se ele puder conter informacoes internas.
7. Interface: confirme que o processo web esta ativo e informe a URL acessivel do painel. Em Cloud, informe a URL de preview ou porta encaminhada fornecida pelo ambiente.
8. Seguranca operacional: confirme que .env, state/, arquivos de sessao e bancos SQLite estao ignorados pelo Git.
9. Coleta: confirme que a coleta e manual, uma rodada por clique, e que checkpoint ou erro de autenticacao pausa a rodada sem repeticao automatica.

No final, entregue um resumo pronto para encaminhar ao cliente, sem termos tecnicos desnecessarios e sem incluir credenciais, token, proxy, URL de banco ou logs sensiveis. Se algo falhar, diga a causa concreta e a proxima acao que a IA pode executar, sem pedir que o cliente edite arquivos ou use terminal.
```