# Installation

These instructions describe the public TommeView 1.6.4 Windows package.

1. Download `TommeViewSetup-1.6.4.exe` from this repository's Releases page.
2. Run it and choose English or Italian. Python and VLC are not required.
3. Installation is per user, normally under `%LOCALAPPDATA%\Programs\TommeView`,
   without administrator privileges.
4. Choose the desktop and Explorer integration options you want: **Open with**,
   a context-menu entry, and optional default file associations. Default
   associations are initially unchecked; Windows may require an explicit
   selection in **Open with**.
5. Start TommeView and open a video you are allowed to use. No demo video is
   included in the installer.

## System requirements

Windows 10/11 x64 is the target platform. The acquisition-tool vendor lists
Windows 10 22H2 as its minimum supported version. Playback performance depends
on the video, codec and hardware.

## Updating and uninstalling

Run a newer installer to update TommeView. Sessions in
`%LOCALAPPDATA%\TommeView\sessions` and acquired videos are preserved. An old
demo file is removed only when it is byte-identical to the original fixture.

Uninstall through Windows **Apps** settings. The application and its Explorer
integration are removed; annotations and acquired videos remain. Back up
annotations through **About > Open annotation folder**.
