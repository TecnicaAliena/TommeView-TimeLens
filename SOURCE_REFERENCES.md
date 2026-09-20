# Dependency sources — TommeView 1.6.4

The TommeView application source code is private and is **not** part of this
delivery. This page concerns only the third-party software distributed with the
Windows package.

The release named `v1.6.4` provides six `TommeView-dependency-sources-…` ZIP
assets, together with their SHA-256 hashes. The complete asset list, each
upstream URL, version/commit and archive hash is in
[dependency-source-inventory.json](dependency-source-inventory.json). The
assets contain 1,944 checksum-verified upstream source archives and no project
source, private history, credentials, annotations or user videos.

Download every part before relying on the source delivery. Each ZIP has a
`SOURCE-INDEX.json` which maps its members to upstream URLs, commits and hashes.
The archives are deliberately separate from the installer so that installing
TommeView does not require several gigabytes of source code.

## Main components

- PySide6 / shiboken6 6.10.2 and Qt 6.10.2 source archives, including the Qt
  Multimedia FFmpeg 7.1.2 libraries used by playback.
- Acquisition FFmpeg built from commit
  [`7ba069f4f11d126f52a740156dbab6476a8a865a`](https://github.com/FFmpeg/FFmpeg/tree/7ba069f4f11d126f52a740156dbab6476a8a865a)
  and BtbN build recipes from commit
  [`847e5e1cacc2945ac46528d34d754bd36051680c`](https://github.com/BtbN/FFmpeg-Builds/tree/847e5e1cacc2945ac46528d34d754bd36051680c).
- yt-dlp 2026.08.19, Deno 2.9.6, their pinned published dependencies, and the
  native sources used by the bundled acquisition tools.
- Mesa 11.2.2 and LLVM 3.6.2 source archives corresponding to Qt's included
  software OpenGL renderer; the renderer evidence and notices are in
  [`licenses/`](licenses/).

The packages are source archives, not prebuilt replacements and not a promise
that every archive can be rebuilt identically in a particular environment.
They preserve the source delivery and attribution evidence for the versions
released with TommeView 1.6.4. See [third-party licenses](THIRD_PARTY_LICENSES.md),
[library replacement instructions](LIBRARY_REPLACEMENT.md) and
[application terms](APPLICATION_LICENSE.txt).
