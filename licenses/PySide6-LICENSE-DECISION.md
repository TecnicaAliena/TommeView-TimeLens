# PySide6 licensing decision

TommeView selects **LGPL-3.0-only** for PySide6 6.10.2, PySide6-Essentials, PySide6-Addons and shiboken6.

The package metadata offers `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`. The LGPL option is appropriate for TommeView because the application is not released under the GPL and uses the Qt runtime through dynamically loaded Windows DLLs. We do not statically link Qt into TommeView and we do not modify PySide6 or Qt.

For a public release, keep the Qt notices, provide the complete LGPLv3 text, and preserve the user's ability to replace the LGPL libraries with compatible versions. Do not add an EULA clause forbidding reverse engineering of the LGPL-covered parts. The official license text is available at <https://www.gnu.org/licenses/lgpl-3.0.html>.

The complete official texts are included as [LGPL-3.0.txt](LGPL-3.0.txt) and [GPL-3.0.txt](GPL-3.0.txt). LGPLv3 incorporates GPLv3 with additional permissions, so both texts are provided. Their presence does not license TommeView itself under GPL.

This selection applies where the distributed PySide6/Qt component offers LGPL. It does not override the individual licenses of Qt modules or bundled third-party components, which must be checked for the actual release. Corresponding library sources and replacement/relinking requirements remain separate from providing the license texts. It does not change the separate licenses of TommeView, yt-dlp, FFmpeg or Deno.
