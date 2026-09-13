# Manuale TommeView 1.6.3

[Presentazione](README.md) · [English manual](manual.en.md) · [Installazione](INSTALLATION.md)

## Primo utilizzo

Apri un video locale con **Apri video** o trascinalo sulla finestra.
Portati su un evento, premi un numero da 0 a 9 e assegna la stessa tag alle
occorrenze successive dello stesso processo. La tabella calcola gli intervalli
tra tag uguali; usa tag diverse per processi paralleli.

I tempi appartengono alla timeline del video. Filmati montati o a velocità alterata
non rappresentano necessariamente i tempi reali della macchina. La precisione
dipende dai fotogrammi disponibili e dalla scelta manuale degli eventi.

## Comandi

| Comando | Funzione |
| --- | --- |
| Spazio / clic singolo sul video | Pausa o ripresa nell'ultima direzione |
| Triangolo sinistro / destro | Riproduzione indietro / avanti; altro clic per pausa |
| Pulsante torna all'inizio | Vai all'inizio |
| Rotella in pausa | Jog avanti/indietro su video, timeline o tabella |
| Rotella durante la riproduzione | Scorre la tabella, senza fermare il video |
| Ctrl + rotella | Cambia la velocità di uno scatto |
| + / − | Aumenta / diminuisci la velocità |
| Selettore percentuale | Seleziona direttamente la velocità |
| 0–9 / tastierino / pulsante tag | Inserisce la tag sul fotogramma mostrato |
| Clic / trascinamento timeline | Cerca una posizione nel video |
| Clic su riga della tabella | Vai al momento della tag |
| Tasto destro sul pulsante tag | Modifica la descrizione della tag |
| Tasto destro sulla riga | Modifica descrizione o elimina quell'occorrenza |
| F10 / doppio clic sul video | Schermo intero solo video |
| F11 | Schermo intero con interfaccia |
| Esc | Esce dallo schermo intero |
| Frecce curve | Ruota il video di 90° |
| Cursore volume / altoparlante | Volume / muto |
| Filtro tag | Mostra una sola etichetta o tutte |
| Pulsante pannello / divisore | Mostra, nasconde o ridimensiona la tabella |
| Esporta | Esporta tutte le tag in CSV, anche quelle nascoste dal filtro |
| Cestino | Cancella i punti del video dopo conferma |
| Reset database | Cancella tutte le sessioni dopo conferma |
| Bandiere IT / UK | Cambia lingua e ricorda la scelta |
| Informazioni (i) | Crediti, cartella annotazioni e importazione flag |

Le scorciatoie del player non intercettano il testo digitato nei dialoghi.
Le descrizioni possono essere multilinea e valgono per tutte le occorrenze
della stessa tag nello stesso video. Compaiono nella tabella e nel CSV, non
nell'overlay numerico. In F10 resta il lampeggio delle tag attraversate.

## Velocità, jog e riproduzione inversa

Velocità disponibili: 5, 10, 20, 25, 33, 50, 67, 75, 100, 125, 150, 175, 200,
250, 300, 400, 500, 600, 800 e 1000%. Il 100% è la velocità normale.
In pausa, uno scatto standard di rotella corrisponde a 100 ms al 100%, 5 ms al
5% e 1000 ms al 1000%. Verso l'alto avanza, verso il basso arretra.

La riproduzione inversa è senza audio e usa ricerche successive nel video:
fluidità e latenza dipendono dal codec e dall'hardware. Si ferma all'inizio;
avviandola dall'inizio parte dalla fine. Spazio ricorda l'ultima direzione.
Attraversare una tag durante la riproduzione ne mostra il numero per circa
mezzo secondo; spostarsi con la timeline non lampeggia tutte le tag saltate.

## Tabella ed esportazione

Le righe sono ordinate per tempo. **Intertempo** misura la differenza rispetto
alla tag precedente dello stesso numero; la prima mostra `--`. **Cumulato**
misura il tempo trascorso dalla prima tag dello stesso numero e parte da zero.
Eliminando un punto, i risultati vengono ricalcolati.

Il CSV usa UTF-8 con BOM, separatore punto e virgola, virgola decimale in italiano
e punto in inglese. Le descrizioni multilinea sono racchiuse tra virgolette.
Colonne: **Flag, Descrizione, Tempo (s), Intertempo (s), Cumulato (s), Tempo (ms),
Intertempo (ms), Cumulato (ms)**. Include tutte le etichette, indipendentemente dal filtro.

## Annotazioni e backup

Salvataggio automatico in `%LOCALAPPDATA%\TommeView\sessions`, associato al
percorso assoluto del video. Spostare o rinominare il file cambia la sessione
associata. Il formato v3 conserva tag, descrizioni e rotazione; i formati v1/v2
restano leggibili. La rotazione non modifica il video originale.

**Informazioni > Apri cartella annotazioni** apre i file da salvare come backup.
**Importa flag** importa una vecchia cartella `data` o `sessions` senza sovrascrivere
sessioni già presenti. Aggiornamento e disinstallazione preservano le annotazioni.

Il cestino cancella i punti del video corrente ma conserva descrizioni e rotazione.
Il reset globale cancella sessioni, descrizioni e rotazioni di tutti i video;
conserva video e preferenze e impedisce il recupero automatico delle vecchie copie.

## Acquisizione YouTube

Apri **Scarica da YouTube**, inserisci il collegamento a un singolo video, leggi
l'avviso e conferma di aver verificato che il download sia consentito. La conferma
non viene ricordata e si azzera cambiando URL, alla fine del tentativo o chiudendo.
Un video pubblico o l'uso personale non autorizzano automaticamente il download.

Scegli la destinazione (predefinita: cartella Video di Windows, `TommeView/Acquisizioni`).
**Apri il video al termine** è inizialmente attivo. Sono disponibili annullamento,
apertura del video e della cartella. Il player resta utilizzabile durante il download.

Il programma preferisce la massima risoluzione accessibile, poi FPS e qualità,
con l'audio migliore. I flussi separati vengono uniti in MKV senza ricodifica;
un formato già combinato può mantenere il contenitore originale. Il progresso
può ripartire quando viene scaricato l'audio.

Playlist e dirette in corso sono escluse. Non vengono importati cookie o credenziali:
contenuti privati o restrizioni del servizio possono impedire l'acquisizione.
Non vengono sovrascritti file esistenti. Il file `.source.json` conserva URL,
titolo, ID e risoluzione. Annullamento ed errori puliscono solo la propria cartella
temporanea; uno spegnimento forzato può lasciare una cartella `.tommeview-download-*`.

## Riga di comando

```powershell
.\TommeView.exe
.\TommeView.exe "C:\Videos\clip.mp4"
.\TommeView.exe --data-dir "C:\TommeViewData\sessions" "C:\Videos\clip.mp4"
```

`--data-dir` è la cartella delle sessioni; le preferenze vengono salvate nella
cartella padre e la ricerca automatica delle vecchie sessioni viene disabilitata.
Gli URL YouTube vanno nel dialogo, non nella riga di comando. `--demo` richiede
una fixture separata, non distribuita. L'eseguibile non dispone di console.

Per problemi consulta [Supporto](SUPPORT.md). Non inviare video riservati o dati personali.
