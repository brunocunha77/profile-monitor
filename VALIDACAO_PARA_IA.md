# Prompt de verificacao local para a IA

Copie e cole o texto abaixo na mesma sessao de Codex ou Cloud depois da instalacao. Ele verifica se o Profile Monitor esta pronto para uso local. Nao publica nada, nao envia nada ao GitHub e nao precisa de permissao de escrita no repositorio.

```text
Faca uma verificacao LOCAL do Profile Monitor ja instalado. Nao execute coleta no Instagram, nao solicite senha novamente e nunca mostre qualquer segredo do .env. Nao execute git push, nao crie repositorio e nao publique nada.

Execute e informe um relatorio objetivo com APROVADO, ATENCAO ou BLOQUEADO para cada item:

1. Projeto: confirme que a pasta contem o Profile Monitor e que os arquivos README.md, .env.example, control_server.py e web/ existem.
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
8. Seguranca local: confirme que .env, state/, arquivos de sessao e bancos SQLite estao ignorados pelo Git. Isso e apenas uma verificacao; nao envie nada para repositorio algum.
9. Coleta: confirme que a coleta e manual, uma rodada por clique, e que checkpoint ou erro de autenticacao pausa a rodada sem repeticao automatica.

No final, entregue um resumo pronto para o usuario usar localmente, sem termos tecnicos desnecessarios e sem incluir credenciais, token, proxy, URL de banco ou logs sensiveis. Se algo falhar, diga a causa concreta e a proxima acao que a IA pode executar, sem pedir que o usuario edite arquivos ou use terminal.
```