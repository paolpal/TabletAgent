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

## CasaOS

Il file `docker/compose.yml` include i metadati CasaOS, con `frontend` come servizio principale. La porta del collegamento segue `TABLET_AGENT_PORT` (predefinita `8088`). L’icona è servita dall’app; per impostazione predefinita usa `http://casaos.local:8088/icon-512.png` (con la porta configurata). Se `casaos.local` non è raggiungibile, imposta `CASAOS_ICON_URL` in `docker/.env` con l'indirizzo completo dell'icona, per esempio `http://192.168.1.10:8088/icon-512.png`. L'URL deve essere raggiungibile dalla dashboard e dai dispositivi che la visualizzano.

Il Compose usa build locali (`../frontend` e `../backend`): conserva l'intera repository sul server ed eseguilo dalla directory `docker/`. I metadati non trasformano la repository privata in un pacchetto App Store o in immagini pubbliche.

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
