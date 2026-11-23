# Distribution notes

These are engineering release considerations, not legal advice or a legal
authorization to redistribute a particular build.

## Source license and bundled tools

TommeView's original source is GPL-3.0-or-later. Third-party components keep
their own licenses and obligations. In particular, the official Windows
standalone `yt-dlp.exe` bundles GPLv3+ components, while yt-dlp's upstream
source repository is Unlicense. TommeView invokes the tool as a separate
process; that architecture does not remove the need to retain the tool's notices,
licenses and corresponding-source delivery.

The download acknowledgement is informational only. It does not grant permission
to download from YouTube or any other service.

## External-service use

YouTube's terms and applicable law may limit downloads and automated access. A
video creator's authorization does not necessarily settle service-contract,
copyright or anti-circumvention questions. Do not add cookie import,
credential collection, bypasses or automatic tool updates without a separate
technical and legal review.

## FFmpeg and Qt

The package uses reviewed LGPL-oriented FFmpeg/Qt payloads with source and
notice references. Preserve the actual build configuration, notices,
library-replacement information and corresponding source delivery. A successful
technical build is not legal-compliance certification.

Before redistributing a modified installer, review the actual included files and
the current third-party terms. Keep the public source, license notices, build
instructions and release artifacts synchronized.
