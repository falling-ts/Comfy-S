---
name: comfyui-workflow-runner
description: |
  Run local ComfyUI workflows headlessly through the HTTP API without touching the browser: convert a
  saved workflow JSON into the API prompt format, refresh a FallingTS Markdown data table from its md file
  (equivalent to clicking that node's refresh button), submit to /prompt, poll /history to completion, and
  verify the produced artifact by probing it and extracting frames. Use whenever a workflow must be
  executed or re-run autonomously, when a prompt or model edited inside an md data table has to actually
  take effect, or when a render needs objective inspection (duration, fps, audio presence, motion,
  continuity). Also carries measured findings on H3 scene video: which reference/prompt variants actually
  win, rotation speed ceilings, and the OrbitSheets parameter recipe. And measured findings on H3 shot
  order and timing: why prose cannot pin a shot's position in ref2video mode, and the frame-anchoring
  recipe — with its node-wiring and layout caveats — that can. Not for authoring prompt text or for
  developing custom nodes.
---

# ComfyUI Workflow Runner

Drive the local ComfyUI at `http://127.0.0.1:8188` from scripts: **edit source data → refresh the
data-table node → submit → inspect the artifact**. No browser, no manual Run click, no frontend state
to sync by hand.

## When to use this

- A workflow must be run and its output checked, and the user is not going to click Run for you.
- A prompt living in a `stories/**/*.md` data table was just edited — the workflow JSON still holds the
  **old** text until something refreshes it.
- An A/B comparison or regression check needs real renders plus quantitative inspection.
- A shot's **order, position or duration** is wrong in the output and the prompt's time codes are being
  ignored — see `references/h3-shot-order-anchoring.md`.

## The core insight (why nothing needs clicking)

`FallingTSMarkDownTable.execute(data, id)` consumes only the **control state** `data`
(`{md_path, fields, selected}`) that the frontend serializes into the workflow. It never reads the md
file itself. The frontend's refresh button merely calls `GET /fallingts_mdtable/read?path=...` and writes
the returned rows back into that state. Calling the same endpoint and constructing `data` yourself is
therefore equivalent — and needs no browser at all.

## Procedure

1. **Convert and refresh**
   `python scripts/workflow-to-prompt.py "<glob>" --refresh-md --dump prompt.json`
   Confirm the node count, and that the mdtable prompt length changed to the new value (a stale length
   means the refresh did not happen and you would silently re-run the previous prompt).
2. **Dry-run check** — inspect a few critical nodes (loaders, sampler, sigma shift, the data table)
   before spending GPU time. `--dump` then read the JSON.
3. **Submit** — add `--submit`. The script posts to `/prompt`, polls `/history/<id>`, and prints the
   output filenames it produced.
4. **Verify the artifact** — never trust "success" alone; probe it and look at it:
   - `ffmpeg -i file.mp4` → duration, resolution, fps, **and whether an audio stream exists at all**
   - contact sheet: `ffmpeg -y -i f.mp4 -vf "fps=1/N,scale=640:-1,tile=4x2" -frames:v 1 grid.png`
   - read `grid.png` as an image, then judge content, continuity and consistency
   - motion: `python scripts/motion-profile.py f.mp4 [--crop w:h:x:y]` — per-second median of the
     blurred frame difference. Do **not** rely on `pblack` alone to decide whether a subject moved;
     under H3's heavy grain it saturates (see `references/output-verification.md` §3).
   - when the workflow has frame anchors, extract the anchored frames and compare them against the
     reference images one by one (`references/h3-shot-order-anchoring.md` §4.4).
5. **Save a preview to `output/`** — the preview nodes only write `temp/`; the plugin's save endpoint
   turns the cached media into a real file (`comfyui-headless-control` has the endpoint table).

## Pitfalls (each cost a real debugging round)

- **`widgets_values` includes widgets that were converted into inputs.** A connected widget still occupies
  its slot in the array, so zip against the **full** widget list and *then* skip the linked ones. Filtering
  first shifts everything — `PreviewImageSave.format` silently receives `filename_suffix`'s value. This
  fails **silently**, because the wrong value is still a valid value.
- **Prefer `widgets_values_named` over positional `widgets_values`, and watch dynamic sub-widgets.**
  A `COMFY_DYNAMICCOMBO_V3` child (e.g. `BlockSparseAttention`'s `selection.tau`, `SaveVideo`'s
  `format.codec`) is absent from `/object_info` but still occupies a slot in `widgets_values`, shifting every
  later widget by one — and it is *also* a required API input keyed `<parent>.<child>`. Getting this wrong
  twice in a row is easy: position-zip sends `start_percent=1.3` / `min_tokens=""` (rejected by range and
  enum checks), while dropping it sends nothing and gets `Required input is missing: tau`. Map by name, and
  inject dynamic children whose parent is in the widget table.
- **`Reroute` does not exist in the API graph.** Resolve every downstream reference through it to the real
  source node, or those inputs lose their link entirely.
- **`MarkdownNote` / `Note` are frontend-only** — skip them.
- **`mode: 4` (bypass) and `mode: 2` (mute)** nodes need explicit handling; the script currently skips them
  and reports it, which is safe for verification but means bypassed nodes will not appear in the prompt.
- **Execution cache**: resubmitting a byte-identical graph returns from cache in seconds. Change the seed
  (or the prompt) for A/B runs, or you will "measure" a 5-second render that never ran.
- **`--refresh-md` injects into the API payload only — it does not write the workflow file back.** The
  mdtable snapshot on disk stays stale, so the next F5 (or any frontend save) shows the old prompt. To make
  the file agree with the md, `GET /fallingts_mdtable/read` and write the result back into **both**
  `widgets_values[0]` and `widgets_values_named.data` (the two mirrors must stay identical).
- **New custom nodes need a ComfyUI restart** before they appear in `/object_info`.
- **`LOAD_3D` 是控件、`LOAD3D_CAMERA` 是可连线端口。** `PreviewGaussianSplat` /
  `SaveGaussianSplat` / `Load3D` 的 3D 视口状态(`viewport_state` / `image`)住在 `widgets_values` 里,
  漏掉会报 `Required input is missing: viewport_state`;无头运行没有前端状态,注入空字典 `{}` 即可
  (节点自己退回默认相机)。反过来 `RenderSplat.camera_info` / `PreviewGaussianSplat.camera_info`
  是**可连线端口**(类型名 `LOAD3D_CAMERA`),当成控件会静默丢链接 —— 机位就一直是默认相机。
- **动态下拉必须"父项 + 子项"一起进 prompt。** V3 执行期用 `build_nested_inputs` 把
  `"mode": "orbit"` + `"mode.yaw": <值或连线>` 收成 `{"mode": {"mode": ..., "yaw": ...}}`。
  子控件被连线时若把父控件一起跳过,子项会原样变 kwarg,报
  `CreateCameraInfo.execute() got an unexpected keyword argument 'mode.yaw'`。
- A killed run leaves no artifact; check `/history` for `execution_error` messages rather than assuming
  the script failed.

## Files

- `scripts/workflow-to-prompt.py` — workflow JSON → API prompt, md refresh, submit and poll.
- `scripts/list-recent-outputs.py` — map recent runs to their output files (temp preview vs saved output).
- `scripts/motion-profile.py` — per-second motion curve: gaussian-blurred frame-difference avg / median /
  max, with an optional ROI crop; the reliable way to tell whether a subject actually moved.
- `scripts/motion-frame-profile.py` — per-frame profile of one window (global + each ROI + a static control
  region): use it to find the shot cut, pick a window that neither take has cut inside, and compare
  `ROI ÷ control` across reruns instead of raw values.
- `scripts/verify-anchor-snapping.py` — OrbitSheets reference-board "anchor snapping" hypothesis test.
- `scripts/set-md-selected-id.py` / `scripts/show-md-cell.py` — align a workflow's selected row with the md
  and print one row's cells.
- `references/workflow-to-prompt.md` — conversion rules and the full pitfall list.
- `references/mdtable-refresh.md` — FallingTS mdtable state shape, endpoints, and refresh mechanism.
- `references/output-verification.md` — probing, contact sheets, and motion/audio analysis recipes,
  including why `pblack` cannot see subject motion under H3 grain.
- `references/media-analysis-toolchain.md` — the offline video/audio analysis chain this workspace uses
  (locate artifact → ffprobe → frame grabs/contact sheets → SenseVoiceSmall transcript + emotion + event,
  loudness/rhythm/spectrum), its capability limits (no speaker diarization, no track ID, gender is a heuristic)
  and the four traps; full source and upgrade list in `docs\视频音频分析工具链.md`.
- `references/h3-scene-generation.md` — **measured findings for H3 scene video**: the variant performance
  table, why a single anchor image beats multi-image references, five prompt rules (positive phrasing,
  fixed camera, one action per shot, never describe the reference's own layout, and unambiguous object
  nouns — `notebook` gets rendered as a second laptop), rotation speed ceilings,
  the OrbitSheets parameter recipe and its limits, plus the parameter-editing and frame-extraction traps.
- `references/h3-shot-order-anchoring.md` — **measured findings for H3 shot order and timing**: four
  prose-only rounds that all moved the shot to the wrong place, why Ref2VA reference images carry no time
  position, the `FallingTSH3AddGuide` wiring recipe (frame indices, equal-image double anchors) **kept as an
  opt-in — results look better without the anchors**, and the
  pitfalls (`vae` required, negation still unreliable, one unavoidably unsatisfiable layout rule, hardcoded
  frame indices, snapshot not written back by `--refresh-md`).
