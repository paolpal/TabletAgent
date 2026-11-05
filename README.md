# Tablet Agent

Assistente per tablet meno recenti: interfaccia web senza framework, backend Python con FastAPI, Deep Agents, OpenRouter e cronologia SQLite.

## Struttura

- `frontend/`: HTML, CSS e JavaScript ES5; Nginx inoltra `/api` al backend.
- `backend/`: FastAPI, Deep Agents, SQLite; dipendenze e ambiente gestiti con `uv`.
- `docker/`: Compose e configurazione d'esempio.

## Avvio con Docker

Copia `docker/.env.example` in `docker/.env`. La modalità predefinita `AGENT_MODE=mock` risponde senza chiave. Per usare OpenRouter, imposta `AGENT_MODE=openrouter` e `OPENROUTER_API_KEY` (oppure `OPEN_ROUTER_KEY`); il modello predefinito è `openrouter/free`, modificabile con `OPENROUTER_MODEL`.

```sh
cp docker/.env.example docker/.env
# Per OpenRouter, modifica docker/.env con modalità e chiave
cd docker
docker compose up -d --build
```

Visita `http://IP_DEL_SERVER:8088` dalla rete locale. I messaggi sono conservati nel volume Docker `chats`.

## Sviluppo e test

Installa [uv](https://docs.astral.sh/uv/), poi:

```sh
cd backend
uv sync --locked
uv run pytest
```

## Stato del progetto

La chat usa Deep Agents con strumenti per data e ora, ricerca web e lettura di pagine pubbliche e il modello OpenRouter configurato, oppure risposte simulate in modalità mock. Selezione modello dall'interfaccia, fallback automatico, esecuzione di codice **non sono ancora implementati**. Il frontend è scritto per browser datati, ma la compatibilità va verificata sul vero iPad.

L'app iniziale non ha autenticazione né HTTPS: usala solo su una rete fidata, senza esporla su Internet. Le chat e la chiave API vanno protette insieme al server.

## Aggiungere alla schermata Home

Su iPad, apri l’indirizzo dell’app in Safari, tocca Condividi e scegli «Aggiungi a Home». Avviala dall’icona creata: si aprirà senza la barra degli indirizzi di Safari. Il server deve restare raggiungibile sulla rete locale.
