# Changelog

## 1.6.6

- Add per-video zoom and speed areas with labeled timeline lanes ([#4](https://github.com/TecnicaAliena/TommeView-TimeLens/issues/4)). Start from the playhead with a five-second proposal, or link both boundaries to a numeric tag with exactly two markers. Drag an area's center to move it or either edge to resize it.
- Edit marker times from the table to move linked area boundaries. Additional points with the same label leave existing links intact.
- Add context-menu editing and deletion, with independent real-time zoom transitions defaulting to 0.2 seconds each.
- Save playback areas with the session while retaining v1–v3 session import and the existing marker CSV format.

## 1.6.5

- Check the official stable yt-dlp release at startup in the background. Verify its SHA-256 and save newer builds in a per-user cache.
- YouTube acquisition uses the newest verified local copy available when the download starts. Offline or failed checks leave the existing copy usable.
- Add `--no-yt-dlp-update` for launches that should skip the network check.
- Build the Windows executable and installer directly from the public source tree.

## 1.6.4

- Add a localized LGPL notice and an Open licenses button to the About dialog.
- Include application terms, library replacement instructions, expanded third-party notices and source-delivery references in the Windows package.

## 1.6.3

- Stop bundling the 15,467,610-byte demo video. Keep the reproducible source fixture for development.
- Remove the old installed demo on upgrade only when its SHA256 matches the original; preserve user replacements and other files.
- Packaged self-tests accept `TOMMEVIEW_TEST_VIDEO`; installer tests supply the repository fixture externally and verify both demo cleanup and preservation.

## 1.6.2

- Complete the public draft's official LGPLv3/GPLv3 license texts, record download provenance and hashes, and clarify that PySide6's LGPL selection does not override individual module licenses or corresponding-source obligations. License texts and source-reference audit are included in the installer. Public source-delivery gates remain open.

- Add an Italian/English YouTube notice and terms link directly in the acquisition form. Require an unchecked-by-default acknowledgement before starting; reset on URL changes, completion/failure/cancellation and close, without persisting acceptance. Guard the start handler as well as the button.
- Extend offline acquisition UI checks for the acknowledgement gate, link changes, completion, cancellation and reopening. The rebuilt 1.6.2 installer includes this change.

- Exclude unused Qt Virtual Keyboard (GPL-only open-source module) and PDF plugins; fail builds on unreviewed Qt DLLs. Upgrade removes only their four known files. Package only distributable docs, excluding the internal launch plan.
- Document GPU-backed video presentation as a deferred development idea; no runtime or installer changes.

## 1.6.1

- Use pinned shared FFmpeg/ffprobe libraries and an explicit download-tool payload allowlist; exclude unused ffplay and vendor HTML documentation, retaining licenses and all application features.
- Remove only enumerated obsolete 1.6.0 vendor files during upgrades; preserve unknown files and user data.
- Prefer native Windows file dialogs for video opening, CSV export and session import, as already done for acquisition folders.
- Add payload, tool-resolution and dialog-policy regressions; document redistribution licensing separately from YouTube terms. Public legal compliance has not been certified.

## 1.6.0

- Synchronize Italian/English feature and command references, CLI/data-directory behavior, CSV columns and v3 migration notes; update developer and troubleshooting guides.
- Record user acceptance of YouTube downloading separately from the 32 automated tests and packaged/installer checks. The agent's earlier public test video was unavailable; no successful-video URL or resolution was supplied.

- Add non-modal YouTube acquisition with configurable destination, progress, cancellation and optional automatic local playback.
- Prefer maximum available resolution, then FPS/quality, and best audio; merge without re-encoding using separate FFmpeg tools.
- Preserve existing files, isolate temporary downloads, and save a small source metadata sidecar.
- Reject arbitrary sites, playlists and ongoing live streams; do not import browser credentials or user downloader configuration.
- Add pinned, SHA256-verified yt-dlp/EJS, Deno and FFmpeg tool preparation and packaging; retain upstream notices.
- Add offline backend and UI regression checks; keep acquisition preferences separate from language and annotation data.

## 1.5.0

- Add F10/double-click video-only fullscreen, retain numeric marker flashes, and restore the previous layout with Escape.
- Add per-video label descriptions, multiline input from tag buttons/table rows, a wrapping table column, and CSV export.
- Save descriptions in session format v3 while reading v1/v2.
- Integrate the selected video/timeline icon in the application, Windows executable, and installer.
- Isolate packaging dependencies and bundle Qt's matching VC runtime to avoid startup DLL conflicts.
- Verify 12 model/localization tests and real-decoder smoke tests including description input and fullscreen restoration.

## 1.4.0

- Add per-user installer options for Windows Open with registration, an explicit video context-menu command, and optional default associations for supported video extensions.
- Preserve drag-and-drop opening in the app and document dropping videos onto the window, executable, or shortcut.
- Restore previous extension associations on uninstall when TommeView is still the active association.

## 1.3.0

- Add Ctrl+wheel playback-speed changes over the video, timeline and marker table, while retaining + and - keyboard controls.

## 1.2.0

- Add silent, clock-driven reverse playback at the selected speed, with reverse marker flashes.
- Keep the last direction when pausing/resuming with Space; use separate forward/reverse buttons.
- Use the wheel for proportional jog while paused and table scrolling during either playback direction.
- Accumulate fractional wheel motion, support pixel deltas, and clamp jog targets to video bounds.
- Lower minimum speed to 5% and retain the 1000% maximum.
- Narrow the sidebar and arrange label buttons in two rows with compact table headers.
- Add real-decoder tests for reverse speeds, direction changes, wheel routing and jog scaling.

## 1.1.0

- Add clockwise and counterclockwise 90-degree rotation controls with vector arrow icons.
- Persist per-video rotation alongside markers; migrate existing v1 sessions on save.
- Add confirmed clearing of active-video markers and confirmed database reset for all videos.
- Prevent automatic legacy-session recovery after a database reset.
- Add cumulative same-label intervals to the marker table and CSV export.
- Add Italian and English localization, flag selectors, persistent language settings, and a bilingual installer.
- Limit preview image conversions to approximately 60 per second while retaining media timestamps and marker crossing detection.
- Document iPhone HEVC and 240 FPS limitations and timestamp-preserving conversion workflows.
- Validate rotation pixels, persistence, destructive-action cancellation, localization and a synthetic 240 FPS MOV.

## 1.0.0

- Initial Windows player with timestamp overlays, markers, intervals, speed controls, session autosave and installer.
