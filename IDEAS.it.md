# Idee e suggerimenti

Questa è la lista pubblica dei possibili miglioramenti per TommeView. Serve a
raccogliere e discutere esigenze reali, non costituisce una promessa di rilascio.
La versione attuale è volutamente completa per il suo uso originario: l'analisi
manuale dei tempi su video.

## In valutazione

| Idea | Stato | Note |
| --- | --- | --- |
| Visualizzazione video supportata dalla GPU | Rinviata | Valutare di mantenere i fotogrammi sulla GPU quando possibile, senza perdere annotazioni locali, overlay, schermo intero e fallback compatibile. Riguarda la visualizzazione, non sostituisce la scelta automatica di decodifica hardware di Qt/FFmpeg. Prima di intervenire sul player occorrono misure su video ad alta risoluzione e alto frame rate. |

## Proponi un miglioramento

Apri una [richiesta di funzionalità](https://github.com/TecnicaAliena/TommeView-TimeLens/issues/new?template=feature_request.md)
indicando:

- il problema che vuoi risolvere;
- il flusso di lavoro o il tipo di video coinvolto;
- il comportamento atteso da TommeView; e
- i vincoli importanti, per esempio precisione, velocità, tastiera o
  conservazione delle annotazioni esistenti.

Non allegare filmati riservati, annotazioni personali, credenziali o materiale
protetto da copyright che non sei autorizzato a condividere. Le proposte vengono
valutate per utilità, coerenza con l'analisi dei tempi, conservazione dei dati e
costo di manutenzione.

Per problemi riproducibili usa invece la [segnalazione bug](https://github.com/TecnicaAliena/TommeView-TimeLens/issues/new?template=bug_report.md).
