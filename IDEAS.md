# Ideas and suggestions

This is the public list for improvements suggested for TommeView. It is a place
to discuss needs, not a promise that an idea will be implemented. The current
release is intentionally feature-complete for its original manual timing use.

## Under consideration

| Idea | Status | Notes |
| --- | --- | --- |
| GPU-backed video presentation | Deferred | Investigate keeping video frames on the GPU where possible, while retaining the existing local annotation workflow, overlays, fullscreen modes and a compatible fallback. This concerns presentation, not replacing the current automatic hardware-decoding choice made by Qt/FFmpeg. Performance must be measured on high-resolution/high-frame-rate video before changing the player. |

## Suggest an improvement

Open a [feature request](https://github.com/TecnicaAliena/TommeView-TimeLens/issues/new?template=feature_request.md) and include:

- the problem you are trying to solve;
- the workflow or type of video involved;
- what you expect TommeView to do; and
- any constraints that matter (for example, accuracy, speed, keyboard use or
  preserving existing annotations).

Please do not attach confidential footage, personal annotations, credentials or
copyrighted material that you are not allowed to share. Suggestions are reviewed
for usefulness, compatibility with the focused timing-analysis workflow, data
preservation and maintenance cost.

For reproducible faults, use the [bug report](https://github.com/TecnicaAliena/TommeView-TimeLens/issues/new?template=bug_report.md)
instead.
