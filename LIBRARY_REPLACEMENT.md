# Library replacement

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
