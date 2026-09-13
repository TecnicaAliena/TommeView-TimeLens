# Sostituzione delle librerie / Library replacement

## Italiano

TommeView usa PySide6 e moduli Qt sotto LGPLv3 e librerie FFmpeg sotto le
rispettive licenze LGPL. Le librerie sono file separati: le condizioni di
TommeView consentono la loro sostituzione con versioni compatibili e il reverse
engineering necessario per il debug delle modifiche alle librerie LGPL.

Per una distribuzione Windows basata sull'attuale pacchetto:

1. Chiudere TommeView. Aprire la cartella dell'app tramite le proprietà del
   collegamento Windows. L'installazione predefinita è nella cartella programmi
   dell'utente, non in Program Files.
2. Conservare una copia dell'intera cartella dell'app per poter ripristinare
   i file. Non cancellare video o annotazioni: le sessioni sono separate, in
   `%LOCALAPPDATA%\TommeView\sessions`.
3. Sostituire le librerie interessate nella copia dell'app. Qt e i relativi
   plugin si trovano in `_internal\PySide6`; i binding PySide6 e shiboken6
   si trovano nelle rispettive cartelle sotto `_internal`. Conservare la
   struttura delle directory e includere le dipendenze della propria build.
4. Usare build Windows x64 con ABI e runtime compatibili. I binding distribuiti
   sono PySide6/shiboken6 6.10.2 con Python 3.11; cambiare arbitrariamente versione
   principale di Qt o nomi delle DLL non garantisce compatibilità.
5. Avviare `TommeView.exe` nella copia modificata e verificare il funzionamento
   con un video di prova. Se necessario, ripristinare la copia di sicurezza.

FFmpeg per la riproduzione è nella cartella PySide6; quello per le acquisizioni
è separato sotto `_internal\tools\download\ffmpeg-shared`. Non scambiare le
DLL delle due build: usano versioni principali differenti. Aggiornamenti o
reinstallazioni possono sostituire i file modificati: conservare la propria copia.

Queste istruzioni descrivono la struttura del pacchetto e non attestano che una
specifica build modificata sia stata provata. Per versioni, licenze e sorgenti
consultare [i componenti](THIRD_PARTY_LICENSES.md) e [i riferimenti](SOURCE_REFERENCES.md).
Non è necessario pubblicare le proprie modifiche per il solo uso privato;
la loro eventuale distribuzione resta soggetta alle licenze applicabili.

## English

TommeView uses PySide6 and selected Qt modules under LGPLv3 and FFmpeg libraries
under their respective LGPL licenses. Libraries are separate files. TommeView's
terms permit replacement with compatible versions and reverse engineering to
debug modifications to LGPL libraries.

For a Windows distribution based on the current package:

1. Close TommeView and locate its application folder through the Windows
   shortcut properties. The default installation is per-user, not Program Files.
2. Back up the entire application folder. Do not delete videos or annotations;
   sessions are stored separately in `%LOCALAPPDATA%\TommeView\sessions`.
3. Replace the relevant libraries in a copy of the application. Qt and its
   plugins are under `_internal\PySide6`; PySide6 and shiboken6 bindings are in
   their respective folders under `_internal`. Preserve the directory layout
   and provide dependencies needed by your build.
4. Use Windows x64 builds with compatible ABIs and runtimes. The supplied
   bindings are PySide6/shiboken6 6.10.2 with Python 3.11. Arbitrary Qt major
   version changes or renamed DLLs are not guaranteed to work.
5. Run `TommeView.exe` from the modified copy and test with a sample video.
   Restore the backup if necessary.

Playback FFmpeg is under PySide6; acquisition FFmpeg is separate under
`_internal\tools\download\ffmpeg-shared`. Do not interchange their DLLs:
they use different major versions. Updates or reinstalls may replace modified
files, so retain your own copy.

These instructions describe the package layout, not a test of any particular
modified build. See [third-party components](THIRD_PARTY_LICENSES.md) and
[source references](SOURCE_REFERENCES.md). Private modifications do not require
publication merely because they are used privately; redistribution remains
subject to the applicable licenses.
