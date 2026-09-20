# TommeView TimeLens

[English](README.en.md) · [Manuale italiano](manuale.it.md) · [Installazione](INSTALLATION.md) · [Licenze](THIRD_PARTY_LICENSES.md)

![TommeView: video, tag e misurazione degli intervalli](images/tommeview.png)

*Schermata con un video sintetico di prova, non incluso nell'installer.*

### Osserva il video. Segna gli eventi. Misura i tempi.

TommeView è un lettore video per Windows pensato per l'analisi dei tempi nell'ingegneria: rallenta una sequenza, individua i momenti importanti e misura gli intervalli delle operazioni di una macchina. Assegna tag ai diversi processi e ritrova i risultati in una tabella esportabile in CSV.

## Perché TommeView

TommeView nasce da un'esigenza concreta del suo autore: dopo anni senza trovare un player che riunisse nel modo desiderato rallentamento, navigazione precisa e cronometraggio semplice degli intervalli, ha deciso di costruire lo strumento che gli mancava.

Nell'ingegneria, osservare il video di una macchina aiuta a valutarne le prestazioni reali: quanto dura una singola operazione, dove si concentrano i tempi morti e come si sovrappongono i diversi processi. Questo vale sia per le proprie macchine sia per confronti tecnici con quelle della concorrenza, utilizzando filmati di cui si dispone legittimamente.

Il jog avanti e indietro permette di individuare i passaggi da annotare; tag diverse distinguono le sequenze di eventi dei processi che lavorano in parallelo. Video, timeline e tabella restano nella stessa finestra, per passare dall'osservazione alla misura senza ricostruire ogni volta i riferimenti.

**Un lettore pensato non solo per guardare una macchina in funzione, ma per capire come impiega il suo tempo.**

Non è un sistema di riconoscimento automatico: sei tu a scegliere e descrivere gli eventi. È uno strumento per l'osservazione e l'annotazione manuale dei video.

Gli intervalli si riferiscono alla timeline del filmato. Per interpretarli come tempi della macchina occorre verificare che la registrazione non sia accelerata, rallentata o montata; la risoluzione temporale dipende anche dai fotogrammi disponibili e dalla scelta manuale degli eventi.

## Cosa puoi fare

- Aprire video locali, anche trascinandoli nella finestra.
- Riprodurre avanti e indietro, rallentare o accelerare dal 5% al 1000% e usare la rotella per il jog in pausa.
- Aggiungere dieci tag numeriche colorate, con descrizioni multilinea specifiche del video.
- Consultare tempi, intertempi e cumulati tra eventi della stessa tag; filtrare la tabella ed esportare in CSV.
- Ritrovare le annotazioni grazie al salvataggio automatico locale.
- Ruotare il video e passare allo schermo intero, con o senza l'interfaccia.
- Usare l'interfaccia in italiano o in inglese.
- Acquisire un singolo video YouTube, quando consentito, per analizzarlo come file locale.

## Comandi essenziali

| Comando | Azione |
| --- | --- |
| Spazio | Pausa / riprendi |
| 0–9 | Aggiungi una tag numerica |
| + / − | Aumenta / diminuisci la velocità |
| Ctrl + rotella | Modifica la velocità |
| Rotella, in pausa | Jog nel video |
| F10 / doppio clic sul video | Schermo intero solo video |
| F11 | Schermo intero con interfaccia |
| Esc | Esci dallo schermo intero |
| Tasto destro su una tag o una riga | Modifica la descrizione della tag |

## Installazione Windows

Il programma dispone di un installer per utente, senza necessità di installare Python o VLC. L'integrazione con **Apri con**, il menu contestuale e le associazioni dei file è configurabile durante l'installazione.

Scarica **TommeView 1.6.4** dalla pagina delle [release](https://github.com/TecnicaAliena/TommeView-TimeLens/releases). Gli asset sorgente delle dipendenze sono pubblicati separatamente dalla procedura di installazione: consulta [riferimenti](SOURCE_REFERENCES.md) e [istruzioni di consegna](SOURCE_DELIVERY.md).

Le licenze e i componenti di terze parti sono riepilogati in [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md), con gli avvisi nella cartella [`licenses/`](licenses/). Per PySide6 abbiamo scelto LGPL-3.0-only; la decisione e gli adempimenti sono descritti in [`licenses/PySide6-LICENSE-DECISION.md`](licenses/PySide6-LICENSE-DECISION.md). La configurazione FFmpeg verificata è in [`ffmpeg-build-config.txt`](ffmpeg-build-config.txt).

## Chi c'è dietro

Sono **Marco Tommesani**, autore di TommeView e presente su GitHub come **TecnicaAliena**.

Ho creato TommeView perché cercavo da anni un modo pratico per rallentare i video, muovermi nei punti da osservare e cronometrare gli intervalli tra le operazioni di una macchina. Ho sviluppato e affinato il programma attorno a questa esigenza: rendere più semplice l'analisi dei tempi, anche quando diversi processi si svolgono in parallelo.

## Sostieni il progetto

Se TommeView ti è utile, puoi offrirmi un caffè o una birra. È un sostegno volontario al creatore: grazie!

**[Sostieni Marco su PayPal](https://paypal.me/marcotomme)**

[1 €](https://paypal.me/marcotomme/1EUR) · [3 €](https://paypal.me/marcotomme/3EUR) · [10 €](https://paypal.me/marcotomme/10EUR)

I collegamenti aprono PayPal, un servizio esterno. Nessun pagamento viene elaborato da TommeView e nessuna donazione parte automaticamente.

## Video, dati e uso responsabile

Le annotazioni sono conservate localmente. L'acquisizione YouTube contatta servizi esterni e richiede di verificare condizioni del servizio, diritti e autorizzazioni. Un video pubblico o destinato a uso personale non è automaticamente autorizzato al download.

Il modulo aggiornato include un avviso e una conferma esplicita prima di avviare l'acquisizione. TommeView non è affiliato né approvato da YouTube. L'avviso non sostituisce gli obblighi previsti dalla legge.

## Segnalazioni e contributi

Per segnalare un problema, prepara la versione di TommeView, la versione di Windows e i passaggi necessari a riprodurlo. Evita di pubblicare video riservati, annotazioni personali, credenziali o altri dati sensibili.

Questo repository ospita presentazione e documentazione pubblica. Non contiene i sorgenti dell'applicazione né la cronologia del repository privato. Le licenze dei componenti esterni non attribuiscono automaticamente la stessa licenza a TommeView. Vedi [diritti e componenti esterni](RIGHTS.md).
