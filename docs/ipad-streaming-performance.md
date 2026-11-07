# Streaming su iPad mini originale

Ricerca: 6 novembre 2026. Obiettivo: ridurre il lavoro del browser durante le risposte in streaming mantenendo la compatibilità con il primo iPad mini.

## Cosa si può affermare

- Apple descrive l'iPad mini originale con chip A5 dual-core e schermo 1024 × 768, ma non specifica una frequenza sostenibile di aggiornamenti DOM o di eventi di streaming per una pagina web. [Specifiche Apple](https://support.apple.com/en-us/111978)
- La guida Apple per Safari su iOS raccomanda attenzione alle prestazioni JavaScript e la verifica delle funzionalità disponibili; la guida agli strumenti invita a misurare le prestazioni in Safari. [Contenuti compatibili con Safari](https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariWebContent/CreatingContentforSafarioniPhone/CreatingContentforSafarioniPhone.html), [strumenti Safari](https://developer.apple.com/documentation/webkit/optimizing-your-website-for-safari)
- Nello standard XMLHttpRequest attuale, i dati ricevuti vengono accumulati e gli eventi `readystatechange`/`progress` in ricezione sono normalmente distanziati di circa 50 ms; `responseText` è disponibile durante `loading`. Questo descrive lo standard attuale, **non** garantisce il comportamento esatto del vecchio Safari né dimostra che possa sostenere il rendering ogni 50 ms. [Standard XMLHttpRequest](https://xhr.spec.whatwg.org/#the-send()-method), [getter responseText](https://xhr.spec.whatwg.org/#the-responsetext-attribute)
- Il costo di rendering varia con grandezza e complessità dell'albero DOM e degli stili: non esiste quindi un tasso universale ricavabile dal solo modello del dispositivo. [Google, dimensione del DOM](https://developer.chrome.com/docs/lighthouse/performance/dom-size/)
- Le simulazioni delle dimensioni dello schermo non replicano esattamente il comportamento del dispositivo reale. [Apple, Responsive Design Mode](https://developer.apple.com/documentation/safari-developer-tools/responsive-design-mode)

## Applicazione al progetto

Prima dell'ottimizzazione, ogni evento di testo ricevuto chiama `showMessages`, ricostruendo tutti i messaggi e rieseguendo Markdown e formule anche sulla cronologia invariata. Con più messaggi o formule questo costo cresce, indipendentemente dal numero di byte effettivamente ricevuti.

Accorpare il testo in arrivo e aggiornare solo il messaggio corrente ogni 250–500 ms è un **punto di partenza sperimentale**, non un limite misurato dell'iPad. Separare il ritmo con cui si ricevono i dati da quello con cui si aggiorna il DOM; mostrare subito lo stato dell'agente e applicare sempre l'ultimo contenuto al completamento o in caso di errore. Se il problema fosse invece la quantità di dati o eventi sulla rete, il buffering del solo rendering client non la ridurrebbe: occorrerebbe anche raggruppare gli eventi lato server.

## Come misurare sul tablet

1. Usare una risposta riproducibile con testo lungo, Markdown, formule e blocchi di codice, oltre a una conversazione con molti messaggi già presenti.
2. Provare intervalli di 250, 500 e 1000 ms; confrontare ritardo percepito, continuità dello scorrimento, reattività dei pulsanti e completamento senza blocchi. Registrare lunghezza e contenuto della risposta e versione iOS.
3. Quando possibile, raccogliere un profilo temporale con Web Inspector collegato al dispositivo. La scelta finale deve basarsi sul tablet effettivo e può cambiare con le dimensioni dei messaggi.
