# TommeView 1.6.4 user manual

[Overview](README.en.md) · [Italian manual](manuale.it.md) · [Installation](INSTALLATION.md)

## Getting started

Open a local video with **Open video**, or drop it onto the window. Navigate to an
event and press a digit from 0 to 9. Use the same number for successive events
of one process and different numbers for processes running in parallel.

Measurements refer to the video's timeline. Edited or speed-altered footage may
not reflect real machine timing. Precision depends on available frames and
manual event selection; this is not certified metrology.

## Controls

| Control | Action |
| --- | --- |
| Space / single-click video | Pause or resume in the last direction |
| Left / right play triangle | Play backward / forward; click again to pause |
| Return-to-start button | Seek to the beginning |
| Wheel while paused | Jog over video, timeline or table |
| Wheel during playback | Scroll the table without pausing |
| Ctrl + wheel | Change speed by one step |
| + / − | Increase / decrease speed |
| Percentage selector | Select playback speed |
| 0–9 / numeric keypad / tag button | Mark the displayed frame |
| Timeline click / drag | Seek |
| Click table row | Jump to that marker |
| Right-click tag button | Edit its description |
| Right-click row | Edit description or delete that occurrence |
| F10 / double-click video | Video-only fullscreen |
| F11 | Fullscreen with controls |
| Escape | Exit fullscreen |
| Curved arrow buttons | Rotate by 90° |
| Volume slider / speaker | Volume / mute |
| Tag filter | Show one label or all labels |
| Sidebar button / divider | Show, hide or resize the table |
| Export | Export all labels to CSV, regardless of the filter |
| Trash | Clear current video's points after confirmation |
| Reset database | Clear all sessions after confirmation |
| IT / UK flags | Change and remember language |
| About (i) | Credits, annotation folder and marker import |

Player shortcuts do not intercept typing in dialogs. Descriptions support multiple
lines and apply to all occurrences of that label within this video. They appear
in the table and CSV, not the numeric overlay. Marker flashes remain in F10 mode.

## Speed, jog and reverse

Available speeds: 5, 10, 20, 25, 33, 50, 67, 75, 100, 125, 150, 175, 200, 250,
300, 400, 500, 600, 800 and 1000%. Normal speed is 100%. While paused, a standard
wheel notch moves 100 ms at 100%, 5 ms at 5%, or 1000 ms at 1000%. Wheel up moves
forward; down moves backward.

Reverse playback is silent and uses repeated seeks; smoothness and latency depend
on codec and hardware. It stops at the beginning; starting reverse there starts
from the end. Space remembers the last direction. Crossing a marker flashes its
number for about half a second; timeline seeking does not flash skipped markers.

## Table and CSV

Rows are sorted by timestamp. **Interval** is the time since the preceding marker
with the same number; the first shows `--`. **Cumulative** is elapsed time since
that label's first marker and starts at zero. Deleting a marker recalculates values.

CSV uses UTF-8 with BOM and semicolon separators, decimal commas in Italian and
decimal points in English. Multiline descriptions are quoted. Columns are **Flag,
Description, Time (s), Interval (s), Cumulative (s), Time (ms), Interval (ms),
Cumulative (ms)**. All labels are exported, regardless of the active filter.

## Sessions and backup

Sessions save automatically under `%LOCALAPPDATA%\TommeView\sessions`, keyed by
absolute video path. Moving or renaming the video selects a different session.
Format v3 stores markers, descriptions and rotation; v1/v2 remain readable.
Rotation never modifies the original video.

**About > Open annotation folder** opens files to back up. **Import markers**
imports older `data` or `sessions` folders without overwriting existing sessions.
Updates and uninstall preserve annotations.

Trash clears the current video's points while retaining descriptions and rotation.
Global reset clears all sessions, descriptions and rotations, preserves videos and
preferences, and prevents automatic restoration from old portable session copies.

## YouTube acquisition

Choose **Download from YouTube**, paste a single-video link, read the notice and
acknowledge that you checked downloading is permitted. Acknowledgement is not
remembered: changing the URL, finishing an attempt or closing clears it. Public
availability or personal use alone does not authorize downloading.

Choose a destination (default: Windows Videos folder, `TommeView/Acquisizioni`).
**Open video when finished** is initially checked. Cancel, open video and open
folder controls are available; playback remains usable during acquisition.

Selection prioritizes the highest accessible resolution, then FPS and quality,
with the best audio. Separate streams merge into MKV without re-encoding; an
already combined format may retain its container. Progress may restart for audio.

Playlists and ongoing live streams are excluded. No browser cookies or credentials
are imported; private content or service restrictions may prevent downloading.
Existing files are never overwritten. A `.source.json` sidecar stores URL, title,
ID and resolution. Cancellation/failure cleans only that job's staging directory;
a forced shutdown may leave a `.tommeview-download-*` directory.

## Command line

```powershell
.\TommeView.exe
.\TommeView.exe "C:\Videos\clip.mp4"
.\TommeView.exe --data-dir "C:\TommeViewData\sessions" "C:\Videos\clip.mp4"
```

`--data-dir` is the session directory; preferences live in its parent and automatic
legacy-session lookup is disabled. Paste YouTube links into the acquisition dialog,
not the CLI. `--demo` requires a separate fixture, not distributed. The executable
does not provide a console.

For problems, see [Support](SUPPORT.md). Do not submit confidential footage or personal data.
