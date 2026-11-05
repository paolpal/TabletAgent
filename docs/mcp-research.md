# MCP e concorrenza: note di ricerca

Ricerca sulle API ufficiali, 5 novembre 2026. I risultati sperimentali locali sono documentati separatamente dai riferimenti qui sotto.

## Collegare servizi MCP

- [LangChain MCP](https://docs.langchain.com/oss/python/langchain/mcp) documenta `langchain[mcp]>=1.4.0` e `MCPAdapter`: l'adattatore è asincrono, scopre i tool con `await adapter.list_tools()` e li restituisce come tool LangChain. L'interfaccia `langchain.mcp` è dichiarata **beta**.
- [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) accetta tool nel parametro `tools` di `create_deep_agent`. Nelle prove locali un tool MCP non supporta l'invocazione sincrona (`NotImplementedError`), mentre un Deep Agent con `astream()` lo usa correttamente. Il percorso attuale `agent.stream()` va quindi adattato prima di collegare tool MCP.
- Un URL HTTP(S) usa Streamable HTTP, un `Path` locale usa un processo stdio; un server FastMCP in-process permette prove senza rete. Per più server, `MCPConfig` aggiunge un prefisso ai nomi dei tool in base al nome del server, evitando collisioni. `ClientGroup` offre connessioni indipendenti per server, utili con autenticazioni o versioni del protocollo differenti. [Connessioni MCP](https://docs.langchain.com/oss/python/langchain/mcp/connections).
- `MCPAdapter` è un context manager asincrono: l'apertura connette il client e l'uscita lo rilascia. I tool ottenuti conservano il client e, secondo la documentazione, sono invocabili dopo l'uscita; normalmente ogni chiamata apre e chiude una sessione. Se una sessione deve rimanere attiva fra chiamate, il contesto va mantenuto aperto durante la richiesta all'agente. [Ciclo di vita](https://docs.langchain.com/oss/python/langchain/mcp/connections).
- Per servizi con credenziali, l'adattatore delega autenticazione a FastMCP: sono documentati bearer token e OAuth. I token appartengono al backend e non al codice servito al tablet. OAuth richiede un flusso di autorizzazione e, se si desidera conservarli tra esecuzioni, uno storage dei token. [Autenticazione](https://docs.langchain.com/oss/python/langchain/mcp/auth).
- I risultati possono comprendere testo, contenuti strutturati e blocchi multimediali: è necessario verificare come visualizzarli prima di considerarli tutti supportati dalla chat testuale attuale. [Output MCP](https://docs.langchain.com/oss/python/langchain/mcp/tools).

Per la configurazione iniziale sono preferibili server esplicitamente configurati dal gestore, timeout, errori per singolo servizio e un elenco dei tool esposti. Le azioni che modificano dati o dispositivi richiedono una progettazione esplicita dei permessi. I processi stdio eseguono codice sul server: configurarne solo di fidati.

## Uvicorn e accesso dal tablet

- Più worker Uvicorn sono processi distinti; FastAPI li documenta come un modo per sfruttare più core e aumentare la capacità. La loro presenza comporta anche più processi e memoria. [FastAPI: server workers](https://fastapi.tiangolo.com/deployment/server-workers/).
- Un solo processo non equivale a una sola richiesta alla volta: FastAPI può gestire attese in modo asincrono e sposta gli endpoint `def` in un threadpool. Le funzioni bloccanti chiamate direttamente da una funzione `async def`, invece, non vengono automaticamente spostate nel threadpool. [FastAPI: concorrenza](https://fastapi.tiangolo.com/async/).
- Nella configurazione di questa repo, `backend/Dockerfile` avvia Uvicorn senza `--workers`; il server di anteprima locale viene avviato separatamente. Per attribuire un problema al numero di worker occorre misurare la latenza e le risposte concorrenti mentre una richiesta all'agente è in corso, oltre a verificare la raggiungibilità dal tablet. Un test locale non dimostra da solo il comportamento della rete Wi-Fi o del browser del tablet.

## Risultati delle prove locali

- `cd backend && uv run pytest tests/test_mcp_experiment.py -q`: scoperta e chiamata di un tool su un server FastMCP in memoria e su un server locale Streamable HTTP; un Deep Agent di prova invoca il tool in streaming asincrono. Il modello è simulato, quindi il risultato non misura il comportamento dei modelli OpenRouter.
- `cd backend && uv run pytest tests/test_server_concurrency.py -q -s`: con un worker e una risposta simulata di 3 secondi, `/api/health` ha risposto in 0,030 secondi durante l'attesa. È una prova locale, non un test del Wi-Fi o di Safari sull'iPad.
- Il server di anteprima ascoltava su `0.0.0.0:8088`; il processo occupava circa 152 MiB di memoria residente al momento della misura. I log avevano registrato richieste del tablet con risposte HTTP 200.
- L'adattatore è una dipendenza **di sviluppo** per queste prove: nessun server MCP è stato ancora collegato alla chat operativa.
