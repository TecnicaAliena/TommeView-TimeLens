# Licenze e componenti di terze parti

TommeView distribuisce un programma Windows e componenti esterni. Questa pagina accompagna le release; i testi integrali sono nella cartella [`licenses/`](licenses/).

| Componente | Versione | Licenza / sorgente |
| --- | --- | --- |
| PySide6, PySide6-Essentials, PySide6-Addons, shiboken6 | 6.10.2 | Scelta TommeView: **LGPL-3.0-only**; SPDX del pacchetto `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`; decisione in `licenses/PySide6-LICENSE-DECISION.md`; avvisi Qt in `licenses/`; [Qt for Python](https://code.qt.io/pyside/pyside-setup/), tag `6.10.2` |
| FFmpeg shared / ffprobe | n8.1.2-51-g7ba069f4f1 | LGPL; [commit sorgente](https://github.com/FFmpeg/FFmpeg/tree/7ba069f4f1), [build BtbN](https://github.com/BtbN/FFmpeg-Builds/tree/autobuild-2026-09-09-14-51) |
| yt-dlp Windows executable | 2026.08.19 | Unlicense per il progetto principale e GPLv3+ per il binario standalone; [tag sorgente](https://github.com/yt-dlp/yt-dlp/tree/2026.08.19) |
| Deno | 2.9.6 | [tag sorgente](https://github.com/denoland/deno/tree/v2.9.6); avviso in `licenses/deno-LICENSE.md` |
| Renderer software OpenGL: Mesa / LLVM | 11.2.2 / 3.6.2 | Mesa: MIT e avvisi dei componenti; LLVM: University of Illinois/NCSA e avvisi dei componenti. Testi in [Mesa](licenses/Mesa-11.2.2-NOTICES.txt) e [LLVM](licenses/LLVM-3.6.2-NOTICES.txt). |

Le versioni e gli hash sono nel manifest `download-tools.json` incluso. La 1.6.2 include questa pagina, `licenses/` e [riferimenti ai sorgenti e verifiche aperte](SOURCE_REFERENCES.md). Il pacchetto locale non e ancora approvato per redistribuzione pubblica.

Qt Multimedia include inoltre FFmpeg 7.1.2 (LGPL-2.1-or-later), distinto dal FFmpeg esterno: testo in `licenses/LGPL-2.1.txt`, configurazione in `SOURCE_REFERENCES.md`. Il runtime Python 3.11.9 conserva il testo originale in `licenses/Python-LICENSE.txt`.

Gli [avvisi estesi Qt](licenses/Qt-SOURCE-NOTICES.txt) riportano attribuzioni e testi delle dipendenze presenti nei moduli sorgente Qt 6.10.2 raccolti. Comprendono anche strumenti, test e codice per altre piattaforme: non indicano che tutti questi componenti siano installati con TommeView.

## Verifica FFmpeg

Il binario usato è la variante shared: `--enable-shared --disable-static`, senza `--enable-gpl` né `--enable-nonfree`, e con `--disable-libx264` e `--disable-libx265`. L'output completo e l'hash sono in [`ffmpeg-build-config.txt`](ffmpeg-build-config.txt). Questa è evidenza della configurazione, non una certificazione legale o brevettuale.

La guida ufficiale FFmpeg raccomanda di rendere disponibile il sorgente corrispondente, le modifiche e le istruzioni di compilazione per la distribuzione LGPL: [FFmpeg Legal](https://ffmpeg.org/legal.html).

Per PySide6 abbiamo scelto LGPL-3.0-only dove disponibile. I testi ufficiali completi sono inclusi in [LGPL-3.0.txt](licenses/LGPL-3.0.txt) e [GPL-3.0.txt](licenses/GPL-3.0.txt): LGPLv3 incorpora il testo GPLv3 con permessi aggiuntivi. Questa scelta non cambia le licenze specifiche dei singoli moduli Qt o delle dipendenze e non assegna la GPL a TommeView.
