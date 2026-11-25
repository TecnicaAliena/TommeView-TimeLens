# YouTube acquisition / Acquisizione YouTube

Applies to TommeView 1.6.5. User controls are listed in the Italian and English guides. See also [public distribution considerations](distribution.md).

The user confirmed successful YouTube downloading after testing the implementation. This acceptance is separate from automated tests: the agent's earlier public fixture `BaW_jenozKc` returned unavailable. No URL or resolution was supplied for the successful test, so it does not establish universal video/format availability or an independent maximum-resolution comparison.

The downloader is independent of Qt playback. `acquisition.py` validates and normalizes single-video YouTube URLs, invokes external tools without a shell, prioritizes `res,fps,quality,br` with `bv*+ba/b`, and publishes a completed local file plus a small provenance sidecar. No transcoding or resolution cap is requested. Service availability and device codec performance still apply.

`acquisition_ui.py` uses a QThread, keeping playback responsive. Cancellation terminates only the process tree created by that job (including a running FFmpeg merger). Closing the app waits for cancellation before destroying the worker. Each job owns a unique staging directory inside its destination; cleanup never targets the destination itself. File publishing uses no-overwrite hard links, with exclusive-copy fallback on non-NTFS volumes. Repeated downloads receive numbered filenames.

## Dependencies and reproducibility

Since 1.6.2: the link form displays a localized notice and a browser link to YouTube's terms. An initially unchecked acknowledgement gates both the Download button and its handler, before tool lookup, preference writes or job startup. Acceptance is not persisted; changing the URL, finishing any job or closing the form clears it. The notice is informational, not a blanket liability waiver or a determination of legal compliance. The 1.6.1 installer predates this change; 1.6.2 includes it.

The default destination is Windows Videos/TommeView/Acquisizioni, remembered in `acquisition-preferences.json` beside language preferences. One job runs at a time; progress refers to the current stream and may restart for audio. A completed download has a `.source.json` sidecar containing source URL, ID, title, width, height and FPS when available. No full extractor metadata or browser credentials are retained. With `--data-dir`, acquisition preferences use that session directory's parent. Shutdown cancels work before disposing of the worker; a forced crash can leave the unique staging directory for manual inspection.

- yt-dlp Windows standalone 2026.08.19 (includes EJS scripts): https://github.com/yt-dlp/yt-dlp
- Deno 2.9.6: https://github.com/denoland/deno
- FFmpeg LGPL shared Windows build n8.1.2-51-g7ba069f4f1, BtbN autobuild-2026-09-09-14-51: https://github.com/BtbN/FFmpeg-Builds/releases/tag/autobuild-2026-09-09-14-51
- EJS requirements: https://github.com/yt-dlp/yt-dlp/wiki/EJS
- Stream-copy documentation: https://ffmpeg.org/ffmpeg.html#Streamcopy

`download-tools.json` pins archive URLs and SHA256 values published by the release API. `prepare-download-tools.ps1` downloads and checks archives before extraction. `tools/download` is ignored by Git and included as data in frozen builds, keeping external runtime DLLs away from Qt. Upstream notices are retained next to the tools; preserve them when distributing. FFmpeg source revision is `7ba069f4f1`, available from https://github.com/FFmpeg/FFmpeg/tree/7ba069f4f1 ; build recipes and dependency sources are documented in https://github.com/BtbN/FFmpeg-Builds . Redistributors must satisfy the licenses of the particular binaries and their dependencies, including corresponding-source obligations.

TommeView checks the official stable yt-dlp release on GitHub in a background thread at each normal startup. It checks the Windows asset size and SHA-256 from the release metadata before publishing it atomically under `%LOCALAPPDATA%\TommeView\tools\yt-dlp`. The cache is per user and is retained on uninstall. Each acquisition uses the newest local copy available when it starts. Network errors, invalid updates and offline launches can use the last cached copy or the bundled version. Launch with `--no-yt-dlp-update` to skip the network check. The updater needs no GitHub account or YouTube credentials.

The installer continues to include the pinned tools and their notices. Deno and FFmpeg change through releases of TommeView. For a change to the bundled tools, update the manifest and notices together, prepare tools in a clean directory, run tests and rebuild. User yt-dlp configuration, external EJS components, user plugins and browser cookies remain disabled.

## Validation

External executables are copied as DATA entries at COLLECT time, not analyzed as Qt dependencies. `download_payload.py` allows only required binaries, shared DLLs, manifest and notices; never package the whole vendor archive. FFmpeg tools resolve only under `ffmpeg-shared`, preventing old static developer caches from shadowing them. Keep all shared DLLs together and isolated from Qt. ffplay and vendor HTML manuals are excluded; Deno, yt-dlp, demo and licenses remain. Upgrades remove enumerated obsolete 1.6.0 vendor files, never recursively deleting folders or unknown files. `acquisition_tool_checks.py` exercises startup, Deno evaluation and local audio/video merging in source and packaged self-tests. Windows child process environments normalize case, reset PyInstaller inheritance and exclude unrelated PATH DLLs.

Also run `python -m pytest test_download_payload.py -q` to verify packaging exclusions, required notices/libraries, shared-tool resolution and native-dialog policy.

Run `python -m pytest test_acquisition.py test_model.py test_localization.py -q` and `python smoke_test.py`. Acquisition UI checks are offline and included in `--self-test`; they cover success, auto-open, preference persistence and cancellation on close. Backend tests cover URL rejection, quality arguments, output containment, duplicate names, sidecars and cleanup. They do not establish YouTube network availability. Live checks must be reported separately, use an authorized test video, and never alter personal acquisitions. Packaged builds should also exercise bundled tool versions, merging and the installer regression suite.
