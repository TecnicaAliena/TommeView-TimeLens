# Third-party licenses and components

TommeView distributes a Windows application together with third-party
components. This page accompanies the releases; full texts are in
[`licenses/`](licenses/).

| Component | Version | License / source |
| --- | --- | --- |
| PySide6, PySide6-Essentials, PySide6-Addons, shiboken6 | 6.10.2 | TommeView selection: **LGPL-3.0-only**; package SPDX expression `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`; decision in `licenses/PySide6-LICENSE-DECISION.md`; Qt notices in `licenses/`; [Qt for Python](https://code.qt.io/pyside/pyside-setup/), tag `6.10.2` |
| Shared FFmpeg / ffprobe | n8.1.2-51-g7ba069f4f1 | LGPL; [source commit](https://github.com/FFmpeg/FFmpeg/tree/7ba069f4f1), [BtbN build](https://github.com/BtbN/FFmpeg-Builds/tree/autobuild-2026-09-09-14-51) |
| yt-dlp Windows executable | 2026.08.19 | Unlicense for the main project and GPLv3+ for the standalone binary; [source tag](https://github.com/yt-dlp/yt-dlp/tree/2026.08.19) |
| Deno | 2.9.6 | [source tag](https://github.com/denoland/deno/tree/v2.9.6); notice in `licenses/deno-LICENSE.md` |
| Software OpenGL renderer: Mesa / LLVM | 11.2.2 / 3.6.2 | Mesa: MIT and component notices; LLVM: University of Illinois/NCSA and component notices. Texts in [Mesa](licenses/Mesa-11.2.2-NOTICES.txt) and [LLVM](licenses/LLVM-3.6.2-NOTICES.txt). |

Versions and hashes are in the included `download-tools.json` manifest. Release
1.6.4 includes this page, `licenses/`, and the source-delivery assets described
in [source references](SOURCE_REFERENCES.md) and
[delivery instructions](SOURCE_DELIVERY.md).

Qt Multimedia also includes FFmpeg 7.1.2 (LGPL-2.1-or-later), separate from the
acquisition FFmpeg. Its text is in `licenses/LGPL-2.1.txt`; configuration is in
`SOURCE_REFERENCES.md`. Python 3.11.9 retains its original text in
`licenses/Python-LICENSE.txt`.

[Extended Qt notices](licenses/Qt-SOURCE-NOTICES.txt) preserve attributions and
texts from the Qt 6.10.2 source modules collected. They also cover tools, tests
and code for other platforms; they do not state that every listed component is
installed with TommeView.

[Apache-2.0 notices](licenses/Apache-DECLARED-NOTICES.txt) preserve the original
declarations and copyrights of the listed components alongside the
[full text](licenses/Apache-2.0.txt). The Apache-2.0 selection concerns those
components, not TommeView's original code.

[MIT and CC0 notices](licenses/MIT-CC0-DECLARED-NOTICES.txt) preserve package
declarations, published authors and original source headers where available.
The full texts are [MIT](licenses/MIT.txt) and [CC0-1.0](licenses/CC0-1.0.txt);
they do not change TommeView's license.

## FFmpeg configuration

The acquisition binary is the shared variant: `--enable-shared --disable-static`,
without `--enable-gpl` or `--enable-nonfree`, and with `--disable-libx264` and
`--disable-libx265`. The full output and hash are in
[`ffmpeg-build-config.txt`](ffmpeg-build-config.txt). This is configuration
evidence, not a legal or patent certification.

The official FFmpeg guidance recommends making corresponding source,
modifications and build instructions available for LGPL distribution:
[FFmpeg Legal](https://ffmpeg.org/legal.html).

Where offered by PySide6, TommeView selects LGPL-3.0-only. The complete official
texts are included in [LGPL-3.0.txt](licenses/LGPL-3.0.txt) and
[GPL-3.0.txt](licenses/GPL-3.0.txt); LGPLv3 incorporates GPLv3 with additional
permissions. This selection does not alter the specific licenses of individual
Qt modules or dependencies and does not license TommeView under the GPL.
