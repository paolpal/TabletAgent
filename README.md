# Tablet Agent

Assistente per tablet meno recenti: interfaccia web senza framework, backend Python con FastAPI, Deep Agents, OpenRouter e cronologia SQLite.

## Struttura

- `frontend/`: HTML, `js/`, `css/`, `assets/` e librerie in `vendor/`; Nginx inoltra `/api` al backend. Markdown e formule TeX (`$...$`, `$$...$$`, `\(...\)` e `\[...\]`) sono renderizzati anche senza CDN.
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

Il file `docker/compose.yml` include i metadati CasaOS, con `frontend` come servizio principale. La porta del collegamento segue `TABLET_AGENT_PORT` (predefinita `8088`). Per l’icona, copia `frontend/icon-512.png` in `/var/lib/casaos/www/img/tablet-agent.png` sul server CasaOS: il portale la servirà come `/img/tablet-agent.png`, anche quando è aperto da un altro dispositivo. `CASAOS_ICON_URL` consente di usare un indirizzo alternativo quando l'ambiente che legge il Compose lo fornisce.

Il Compose usa build locali (`../frontend` e `../backend`): conserva l'intera repository sul server ed eseguilo dalla directory `docker/`. I metadati non trasformano la repository privata in un pacchetto App Store o in immagini pubbliche.

Lo streaming raggruppa i frammenti per circa 350 ms e il frontend aggiorna solo il messaggio corrente. `STREAM_BUFFER_MS` permette di cambiare l'intervallo lato server (50–2000 ms); il ritmo di aggiornamento dell'interfaccia resta indipendente. Il valore va verificato sul tablet: vedi `docs/ipad-streaming-performance.md`. I blocchi di codice con linguaggio indicato sono colorati con Prism.

## Sviluppo e test

Installa [uv](https://docs.astral.sh/uv/), poi:

```sh
cd backend
uv sync --locked
uv run pytest
```

Per avviare in locale backend e frontend sulla stessa porta: `backend/.venv/bin/uvicorn --app-dir backend local:app --host 0.0.0.0 --port 8088`. Viene letto il `.env` nella radice e, se è presente una chiave OpenRouter, viene usato il modello configurato.

## Stato del progetto

La chat usa Deep Agents con strumenti per data e ora, ricerca web e lettura di pagine pubbliche e il modello OpenRouter configurato, oppure risposte simulate in modalità mock. Selezione modello dall'interfaccia, fallback automatico, esecuzione di codice **non sono ancora implementati**. Il frontend è scritto per browser datati, ma la compatibilità va verificata sul vero iPad.

L'app iniziale non ha autenticazione né HTTPS: usala solo su una rete fidata, senza esporla su Internet. Le chat e la chiave API vanno protette insieme al server.

## Aggiungere alla schermata Home

Su iPad, apri l’indirizzo dell’app in Safari, tocca Condividi e scegli «Aggiungi a Home». Avviala dall’icona creata: si aprirà senza la barra degli indirizzi di Safari. Il server deve restare raggiungibile sulla rete locale.
