# Installazione / Installation

## Italiano

La release pubblica dell'installer è in preparazione: non è ancora disponibile.
Le istruzioni descrivono il pacchetto Windows candidato 1.6.3.

1. Quando disponibile, scarica `TommeViewSetup.exe` dalle Releases di questo repository.
2. Eseguilo e scegli italiano o inglese. Non occorre installare Python o VLC.
3. L'installazione è per il tuo utente, normalmente in `%LOCALAPPDATA%\Programs\TommeView`, senza privilegi amministrativi.
4. Scegli il collegamento sul desktop e le integrazioni desiderate: **Apri con**, voce contestuale e associazioni. Le associazioni predefinite sono facoltative e inizialmente deselezionate; Windows può richiedere una scelta esplicita in Apri con.
5. Avvia TommeView e apri un tuo video. Nessun video demo è incluso.

Piattaforma prevista: Windows 10/11 x64; per gli strumenti di acquisizione la build upstream indica Windows 10 22H2 come minimo supportato. Le prestazioni dipendono da video, codec e hardware.

Per aggiornare esegui il nuovo installer. Le annotazioni in `%LOCALAPPDATA%\TommeView\sessions` e i video acquisiti non vengono cancellati. La vecchia demo viene rimossa soltanto se coincide con l'originale.
Per disinstallare usa le impostazioni App di Windows: vengono rimosse l'app e le sue integrazioni, non le annotazioni e i video. Puoi salvare una copia delle annotazioni tramite **Informazioni > Apri cartella annotazioni**.

## English

The public installer is being prepared and is not yet available. These instructions
describe Windows candidate 1.6.3.

1. Once available, download `TommeViewSetup.exe` from this repository's Releases.
2. Run it and choose English or Italian. Python and VLC are not required.
3. Installation is per user, normally under `%LOCALAPPDATA%\Programs\TommeView`, without administrator privileges.
4. Choose desktop/Explorer integration options. Default file associations are optional and initially unchecked; Windows may require an explicit Open with selection.
5. Start TommeView and open your own video. No demo video is included.

Target platform: Windows 10/11 x64; the acquisition tool vendor specifies Windows
10 22H2 as its minimum supported version. Performance depends on codecs and hardware.

Run the next installer to upgrade. Sessions under `%LOCALAPPDATA%\TommeView\sessions`
and acquired videos are preserved. Only the byte-identical old demo is removed.
Uninstall through Windows Apps settings. Annotations and acquired videos remain;
back up annotations through **About > Open annotation folder**.
