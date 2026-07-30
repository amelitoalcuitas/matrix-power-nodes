# Agent installation contract

The full release-level contract is `../../INSTALL_WITH_AI_AGENT.md`. Use that file when this pack
is distributed with the workflow. The minimum pack-only contract follows.

1. Resolve the ComfyUI root and verify `custom_nodes/` exists.
2. Place this repository at exactly `custom_nodes/matrix-power-nodes`.
3. Do **not** run pip install for this pack. `requirements.txt` is intentionally empty.
4. Do **not** modify or reinstall Torch, CUDA, NumPy, Pillow, aiohttp, or ComfyUI.
5. Verify rgthree-comfy is installed before loading the bundled workflow.
6. Restart ComfyUI through the installation's normal controlled launcher.
7. Confirm `/object_info` contains only `MATRIX_DatasetConfig` and `MATRIX_DatasetImage` from
   this pack.
8. Load `workflows/matrix-power-nodes-ai-dataset.json` in the UI and verify:
   - no missing node types;
   - config has no backend `api_key` input;
   - `live` is false;
   - all Load Image values are empty;
   - prompt cards expose only the prompt text widget, with no key or generation counter.
9. Do not perform a paid run unless the operator explicitly authorizes it.

Credential entry is loopback-only. For LAN, remote, container, or RunPod installs, use the
`WAVESPEED_API_KEY` server-process environment variable.

Never print, copy, inspect, or commit credential values. The WaveSpeed key control writes to the
ComfyUI user credential directory, not this repository or the workflow.
