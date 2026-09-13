# Dependency source references — 1.6.2

Engineering audit dated 2026-09-13. This local release candidate is not cleared
for public redistribution. The links identify upstream sources, not a complete
corresponding-source delivery for every bundled dependency.

## Identified sources

- PySide6 / shiboken6 6.10.2: [official source directory](https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.10.2-src/).
- Qt 6.10.2: [official source directory](https://download.qt.io/official_releases/qt/6.10/6.10.2/single/).
- Acquisition FFmpeg: [commit 7ba069f4f11d126f52a740156dbab6476a8a865a](https://github.com/FFmpeg/FFmpeg/tree/7ba069f4f11d126f52a740156dbab6476a8a865a).
- BtbN recipes: [commit 847e5e1cacc2945ac46528d34d754bd36051680c](https://github.com/BtbN/FFmpeg-Builds/tree/847e5e1cacc2945ac46528d34d754bd36051680c), resolved from `autobuild-2026-09-09-14-51`.
- yt-dlp 2026.08.19: [commit 3a08beaf031ab68f966401ead017ac81fe8486cf](https://github.com/yt-dlp/yt-dlp/tree/3a08beaf031ab68f966401ead017ac81fe8486cf).
- Deno 2.9.6: [commit e518fbd66dda5debcbdefc0beb0b3756b37b64fa](https://github.com/denoland/deno/tree/e518fbd66dda5debcbdefc0beb0b3756b37b64fa).

The Qt directories and GitHub identifiers above were resolved upstream. Source
archives have not been rebuilt to establish reproducibility. Binary URLs and
archive hashes are in `download-tools.json`.

## Qt payload audit

The runtime DLL allowlist is Core, Gui, Multimedia, MultimediaWidgets, Network,
OpenGL, Qml, QmlMeta, QmlModels, QmlWorkerScript, Quick, Svg, Test and Widgets.
These are selected LGPL-capable Qt modules, not all of PySide6-Addons.
Qt Virtual Keyboard and its plugin are excluded because the
[Qt 6.10 licensing list](https://doc.qt.io/qt-6.10/licensing.html) lists it as
GPL-only for open-source use. Unused Qt PDF and its image plugin are also
excluded to reduce the payload; this does not mean Qt PDF is GPL-only.
New Qt DLL names fail the build until reviewed. DLLs remain separately replaceable.

Qt's separate multimedia FFmpeg reports **7.1.2**, LGPL 2.1 or later,
through `av_version_info` and `avcodec_license` in the PySide6 wheel.
This is not acquisition FFmpeg 8.1. Its configuration is:

```text
--prefix=/c/FFmpeg-n7.1.2/build/msvc/installed --disable-programs --disable-doc --disable-debug --enable-network --disable-lzma --enable-pic --disable-vulkan --disable-v4l2-m2m --disable-decoder=truemotion1 --enable-zlib --extra-cflags='-IC:/zlib-1.3.1/build/amd64' --extra-ldflags='-LIBPATH:C:/zlib-1.3.1/build/amd64' --toolchain=msvc --enable-shared --disable-static
```

## Public-release gates still open

1. Assemble reachable corresponding sources, patches and build instructions for
   actual binaries, including FFmpeg's statically incorporated dependencies,
   not just its core repository. BtbN lists binary assets and checksums;
   no complete dependency-source bundle was found in those release assets.
2. Resolve and preserve sources of dependencies in the Windows yt-dlp binary.
   Its core archive alone is insufficient. Retain full third-party notices;
   an upstream source offer is not automatically our distribution offer.
3. Complete Qt's third-party notice/source inventory (including FFmpeg 7.1.2,
   zlib, image libraries and software OpenGL) and Deno's embedded dependencies.
   Verify vendor patches and build recipes against distributed wheels.
4. Make required source access available alongside the eventual public download,
   and review final application terms for LGPL replacement/debugging rights.

No application source or private history has been published.
