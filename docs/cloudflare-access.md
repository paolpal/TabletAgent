# Prova di Cloudflare Access per Tablet Agent

Questa guida descrive una prova; non crea né modifica risorse Cloudflare e non espone la chat. Tablet Agent non ha un login proprio: tutte le conversazioni sono condivise.

## Preparazione

1. Scegliere un sottodominio dedicato e un indirizzo email autorizzato. Non inserire token, password o codici temporanei nella repo.
2. In Cloudflare Zero Trust, abilitare **One-time PIN** come metodo di accesso e creare un'applicazione **Self-hosted** per il sottodominio scelto. Aggiungere una policy **Allow** limitata all'indirizzo email scelto. Verificare che l'applicazione includa sia la pagina sia tutti i percorsi `/api/*` sullo stesso hostname.
3. Creare la policy Access **prima** di pubblicare il percorso del tunnel. Dove disponibile, abilitare **Protect with Access** nella configurazione del percorso del tunnel per la verifica del token. [Guida Cloudflare](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/).
4. Nel tunnel esistente o in uno dedicato, configurare il sottodominio come applicazione HTTP diretta al frontend di Tablet Agent. L'indirizzo di destinazione va valutato dal punto di vista del processo `cloudflared`: se gira sulla stessa macchina della preview, è `http://127.0.0.1:8088`; se gira su un altro host in LAN, è l'IP LAN della macchina con Tablet Agent e la porta `8088`. Il loopback `127.0.0.1` in un container o su un'altra macchina indica quel container o quella macchina, non automaticamente l'host di Tablet Agent.
5. La preview locale attuale è temporanea e usa un database in `/tmp`; per una prova duratura occorre prima avviare l'app con persistenza e indirizzo raggiungibile dal tunnel. L'indirizzo `192.168.1.160` è assegnato via DHCP e può cambiare.

## Verifica

- Aprire il sottodominio da una sessione senza cookie: deve comparire il login Access, anche per `/api/chats` e `/api/health`.
- Richiedere il codice per l'email autorizzata e provarlo da Safari sul vecchio iPad; aprire poi l'app dalla Home e verificare se conserva la sessione. Il funzionamento con questo dispositivo non è ancora verificato.
- Verificare che un'email non autorizzata non acceda e che, dopo il login, chat e streaming funzionino.
- Verificare che non esistano altri percorsi Internet non protetti verso il server. La protezione Cloudflare non si applica all'accesso diretto alla LAN: chi può raggiungere la porta locale può usare la chat, a meno di altre restrizioni.

Riferimenti: [PIN via email](https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/one-time-pin/), [pubblicazione app protetta](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/), [validazione dei token all'origine](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/).
