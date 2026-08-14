# Nodes

This file is generated from declarations and dated route contracts.

## MATRIX POWER NODES - Kie Matrix API

- Node ID: `MATRIX_DatasetConfig`
- Provider routes:
  - `google/nano-banana-pro/edit` (kie.ai model `nano-banana-pro`)
    - Base price: `$0.09` (unconfirmed — see `_core/runtime.py` `price_provenance`; verify on the kie.ai dashboard before a live run)
    - Price formula: `{"total_price": base_price * (resolution = "4K" ? 4/3 : 1)}`
  - `google/nano-banana-2/edit` (kie.ai model `nano-banana-2`)
    - Base price: `$0.02` (unconfirmed, flat — see `_core/runtime.py` `price_provenance`; verify on the kie.ai dashboard before a live run)
    - Price formula: none (flat price at every resolution)
  - `openai/gpt-image-2/edit` (kie.ai model `gpt-image-2-image-to-image`)
    - Base price: `$0.03` (unconfirmed — see `_core/runtime.py` `price_provenance`; verify on the kie.ai dashboard before a live run)
    - Price formula: `{"total_price": base_price * (resolution = "2K" ? 5/3 : (resolution = "4K" ? 2 : 1))}`
- Maximum contract cost: `$0.120000`

### Widgets

- `model` — selects the provider route (required; string; allowed: `google/nano-banana-pro/edit`, `google/nano-banana-2/edit`, `openai/gpt-image-2/edit`).
- `aspect_ratio` — The aspect ratio of the generated media. (optional; string; allowed: `16:9`, `1:1`, `1:2`, `1:3`, `1:4`, `1:8`, `21:9`, `2:1`, `2:3`, `3:1`, `3:2`, `3:4`, `4:1`, `4:3`, `4:5`, `5:4`, `8:1`, `9:16`, `9:21`, `auto`).
- `output_format` — The format of the output image. (optional; string; default `png`; allowed: `jpg`, `png`; not used by `openai/gpt-image-2/edit`).
- `resolution` — The resolution of the output image. (optional; string; default `1K`; allowed: `1K`, `2K`, `4K`).
- `image_1` — required native ComfyUI `IMAGE` reference input.
- `image_2` … `image_14` — optional native `IMAGE` references; different dimensions remain independent and are never batched together.
- Provider key — frontend-only ingestion control backed by the ComfyUI user credential store; it is not a node input and cannot enter the workflow.
- `live` — off is dry run and sends nothing; on permits an admitted paid call.
- Spend bounds — derived automatically from provider facts and the declared run size.

## MATRIX POWER NODES - Dataset Image

- Node ID: `MATRIX_DatasetImage`
- Provider routes:
  - `google/nano-banana-pro/edit` (kie.ai model `nano-banana-pro`)
    - Base price: `$0.09` (unconfirmed — see `_core/runtime.py` `price_provenance`; verify on the kie.ai dashboard before a live run)
    - Price formula: `{"total_price": base_price * (resolution = "4K" ? 4/3 : 1)}`
  - `google/nano-banana-2/edit` (kie.ai model `nano-banana-2`)
    - Base price: `$0.02` (unconfirmed, flat — see `_core/runtime.py` `price_provenance`; verify on the kie.ai dashboard before a live run)
    - Price formula: none (flat price at every resolution)
  - `openai/gpt-image-2/edit` (kie.ai model `gpt-image-2-image-to-image`)
    - Base price: `$0.03` (unconfirmed — see `_core/runtime.py` `price_provenance`; verify on the kie.ai dashboard before a live run)
    - Price formula: `{"total_price": base_price * (resolution = "2K" ? 5/3 : (resolution = "4K" ? 2 : 1))}`
- Maximum contract cost: `$0.120000`

### Widgets

- `config` — immutable `MATRIX_API_CONFIG` input from the previous cell.
- `prompt` — this cell's independent image instruction.
- Generation identity — internal stable node ID; duplicate the prompt node only when deliberately authorizing a separate paid generation.
