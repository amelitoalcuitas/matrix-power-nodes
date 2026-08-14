"""Compiler-owned deployment runtime; regenerate instead of hand-editing."""
from __future__ import annotations

import hashlib
import json
from functools import partial
from pathlib import Path
import threading
import time


RUNTIME_CONTRACTS = {'kie': {'auth': 'bearer',
               'auth_prefix': '',
               'base_url': 'https://api.kie.ai',
               'env_names': ('KIE_API_KEY', 'MATRIX_KIE_KEY'),
               'max_download_bytes': 31457200,
               'provider_fact': {'fetched': '2026-08-14T00:00:00+00:00',
                                 'generator': 'hand-authored from docs.kie.ai (createTask, recordInfo, '
                                              'file-stream-upload) plus third-party pricing research; NOT '
                                              'machine-fetched by src/tools/fetch_routes.py the way the '
                                              'wavespeed contract was. The submit/poll/task_id/upload-url '
                                              'field paths were confirmed against live docs.kie.ai pages. '
                                              'Per-resolution pricing for nano-banana-2 and gpt-image-2 could '
                                              'NOT be confirmed on kie.ai\'s own pricing page (blocked by the '
                                              'fetcher) and is a conservative estimate from third-party '
                                              'aggregator research -- see each route\'s price_provenance. '
                                              'Verify against the account dashboard before trusting these as '
                                              'a hard spend ceiling.',
                                 'lifecycle': {'_note': 'Lifecycle paths appear in no model schema '
                                                        '- they are provider knowledge and live '
                                                        'here exactly once. upload_max_bytes is '
                                                        'the PLATFORM cap; a route may cap lower, '
                                                        'which is why routes carry their own '
                                                        'limits.',
                                               '_note_response_envelope': 'Every kie.ai job-API response '
                                                                          'wraps its payload under a top-level '
                                                                          '"data" object: {"code","msg","data": '
                                                                          '{...}}. task_id_path/status_path/'
                                                                          'error_path/outputs_path below all '
                                                                          'start with "data." for that reason.',
                                               '_note_result_json': 'recordInfo returns "resultJson" as a '
                                                                    'JSON-encoded STRING, not a nested object '
                                                                    '(e.g. "{\\"resultUrls\\":[...]}"). '
                                                                    'outputs_path reaches through it as '
                                                                    'data.resultJson.resultUrls; the dotted-path '
                                                                    'walkers in poll_task and media_image_out '
                                                                    'were extended to json.loads a string value '
                                                                    'mid-traversal to support this.',
                                               '_note_submit_wrap': 'kie.ai has ONE fixed submit URL for every '
                                                                    'model (unlike wavespeed, which routes by '
                                                                    'URL path) and expects the body shaped as '
                                                                    '{"model": <literal>, "input": {...fields}}. '
                                                                    'submit_wrap_field names the body key that '
                                                                    'should hold the route payload; '
                                                                    'flow_api_media wraps it using each route\'s '
                                                                    'own "model" literal before submitting.',
                                               '_note_upload_host': 'The file-upload API lives on a DIFFERENT '
                                                                    'host than the job API — kieai.redpandaai.co, '
                                                                    'not api.kie.ai — confirmed live on '
                                                                    '2026-08-14 after api.kie.ai/api/file-stream-'
                                                                    'upload 404\'d in production (an earlier '
                                                                    'fetch of docs.kie.ai had wrongly reported '
                                                                    'api.kie.ai here, conflating it with the '
                                                                    'job-API OpenAPI server default). The '
                                                                    'template below is a literal absolute URL for '
                                                                    'that reason, not {base_url}-relative.',
                                               'balance': 'GET {base_url}/api/v1/chat/credit',
                                               'download_max_bytes': 31457200,
                                               'error_path': 'data.failMsg',
                                               'outputs_path': 'data.resultJson.resultUrls',
                                               'poll': 'GET '
                                                       '{base_url}/api/v1/jobs/recordInfo?taskId={task_id}',
                                               'status_done': ['success'],
                                               'status_failed': ['fail'],
                                               'status_path': 'data.state',
                                               'status_queued': ['waiting', 'queuing'],
                                               'submit': 'POST {base_url}/api/v1/jobs/createTask',
                                               'submit_wrap_field': 'input',
                                               'task_id_path': 'data.taskId',
                                               'upload': 'POST https://kieai.redpandaai.co/api/file-stream-upload',
                                               'upload_extra_fields': {'uploadPath': 'matrix-power-nodes'},
                                               'upload_max_bytes': 31457200,
                                               'upload_retention_days': 1,
                                               'upload_url_paths': ('data.downloadUrl',
                                                                     'downloadUrl',
                                                                     'data.url',
                                                                     'url')},
                                 'provider': 'kie',
                                 'routes': {'google/nano-banana-2/edit': {'api_path': '/api/v1/jobs/createTask',
                                                                          'model': 'nano-banana-2',
                                                                          'fields': {'aspect_ratio': {'default': 'auto',
                                                                                                       'description': 'The aspect ratio of the generated media.',
                                                                                                       'enum': ['16:9',
                                                                                                                '1:1',
                                                                                                                '1:4',
                                                                                                                '1:8',
                                                                                                                '21:9',
                                                                                                                '2:3',
                                                                                                                '3:2',
                                                                                                                '3:4',
                                                                                                                '4:1',
                                                                                                                '4:3',
                                                                                                                '4:5',
                                                                                                                '5:4',
                                                                                                                '8:1',
                                                                                                                '9:16',
                                                                                                                'auto'],
                                                                                                       'type': 'string'},
                                                                                     'image_input': {'description': 'List of URLs of input reference images for editing. Up to 14 images.',
                                                                                                      'type': 'array'},
                                                                                     'output_format': {'default': 'jpg',
                                                                                                        'description': 'The format of the output image.',
                                                                                                        'enum': ['jpg', 'png'],
                                                                                                        'type': 'string'},
                                                                                     'prompt': {'description': 'The positive prompt for the generation.',
                                                                                                'type': 'string'},
                                                                                     'resolution': {'default': '1K',
                                                                                                    'description': 'The resolution of the output image.',
                                                                                                    'enum': ['1K', '2K', '4K'],
                                                                                                    'type': 'string'}},
                                                                          'formula': None,
                                                                          'price': 0.02,
                                                                          'price_provenance': {'fetched': '2026-08-14T00:00:00+00:00',
                                                                                               'field': 'base_price',
                                                                                               'source': 'UNCONFIRMED -- kie.ai marketing page advertises '
                                                                                                         '"from $0.04" and third-party aggregator research put it '
                                                                                                         'near $0.02/image; kie.ai\'s own pricing page could not '
                                                                                                         'be fetched. No confirmed per-resolution breakdown exists, '
                                                                                                         'so this is treated as a flat price (formula=None). Verify '
                                                                                                         'on the kie.ai dashboard before a live run.'},
                                                                          'required': ['prompt', 'image_input'],
                                                                          'type': 'image-to-image'},
                                            'google/nano-banana-pro/edit': {'api_path': '/api/v1/jobs/createTask',
                                                                            'model': 'nano-banana-pro',
                                                                            'fields': {'aspect_ratio': {'default': '1:1',
                                                                                                         'description': 'The aspect ratio of the generated media.',
                                                                                                         'enum': ['16:9',
                                                                                                                  '1:1',
                                                                                                                  '21:9',
                                                                                                                  '2:3',
                                                                                                                  '3:2',
                                                                                                                  '3:4',
                                                                                                                  '4:3',
                                                                                                                  '4:5',
                                                                                                                  '5:4',
                                                                                                                  '9:16',
                                                                                                                  'auto'],
                                                                                                         'type': 'string'},
                                                                                       'image_input': {'description': 'List of URLs of input reference images for editing. Up to 8 images.',
                                                                                                        'type': 'array'},
                                                                                       'output_format': {'default': 'png',
                                                                                                          'description': 'The format of the output image.',
                                                                                                          'enum': ['png', 'jpg'],
                                                                                                          'type': 'string'},
                                                                                       'prompt': {'description': 'The positive prompt for the generation.',
                                                                                                  'type': 'string'},
                                                                                       'resolution': {'default': '1K',
                                                                                                      'description': 'The resolution of the output image.',
                                                                                                      'enum': ['1K', '2K', '4K'],
                                                                                                      'type': 'string'}},
                                                                            'formula': '{"total_price": base_price * (resolution = "4K" ? 4/3 : 1)}',
                                                                            'price': 0.09,
                                                                            'price_provenance': {'fetched': '2026-08-14T00:00:00+00:00',
                                                                                                 'field': 'base_price',
                                                                                                 'source': 'Third-party aggregator research (aifreeapi.com), corroborated '
                                                                                                           'across independent sources at $0.09 for 1K/2K and $0.12 for 4K '
                                                                                                           '-- NOT scraped directly from kie.ai\'s own pricing page (blocked). '
                                                                                                           'Verify on the kie.ai dashboard before a live run.'},
                                                                            'required': ['prompt', 'image_input'],
                                                                            'type': 'image-to-image'},
                                            'openai/gpt-image-2/edit': {'api_path': '/api/v1/jobs/createTask',
                                                                        'model': 'gpt-image-2-image-to-image',
                                                                        'fields': {'aspect_ratio': {'default': 'auto',
                                                                                                     'description': 'The aspect ratio of the generated image. Auto-detected from input image if not specified.',
                                                                                                     'enum': ['16:9',
                                                                                                              '1:1',
                                                                                                              '1:2',
                                                                                                              '1:3',
                                                                                                              '21:9',
                                                                                                              '2:1',
                                                                                                              '2:3',
                                                                                                              '3:1',
                                                                                                              '3:2',
                                                                                                              '3:4',
                                                                                                              '4:3',
                                                                                                              '4:5',
                                                                                                              '5:4',
                                                                                                              '9:16',
                                                                                                              '9:21',
                                                                                                              'auto'],
                                                                                                     'type': 'string'},
                                                                                   'input_urls': {'description': 'List of URLs of input images for editing. Up to 16 images.',
                                                                                                   'type': 'array'},
                                                                                   'prompt': {'description': 'The positive prompt for the generation.',
                                                                                              'type': 'string'},
                                                                                   'resolution': {'default': '1K',
                                                                                                  'description': 'The resolution of the output image.',
                                                                                                  'enum': ['1K', '2K', '4K'],
                                                                                                  'type': 'string'}},
                                                                        'formula': '{"total_price": base_price * (resolution = "2K" ? 5/3 : (resolution = "4K" ? 2 : 1))}',
                                                                        'price': 0.03,
                                                                        'price_provenance': {'fetched': '2026-08-14T00:00:00+00:00',
                                                                                             'field': 'base_price',
                                                                                             'source': 'UNCONFIRMED for kie.ai specifically -- no kie.ai-specific price could be '
                                                                                                       'located. Uses general GPT-Image-2 market pricing ($0.03/$0.05/$0.06 for '
                                                                                                       '1K/2K/4K) as a conservative placeholder. Verify on the kie.ai dashboard '
                                                                                                       'before a live run; this route\'s route_max_costs may be wrong.'},
                                                                        'required': ['prompt', 'input_urls'],
                                                                        'type': 'image-to-image'}}},
               'route_max_costs': {'google/nano-banana-2/edit': 0.02,
                                   'google/nano-banana-pro/edit': 0.12,
                                   'openai/gpt-image-2/edit': 0.06}}}
_PACK_ID = '19c3b69ab6cb840d'
_WRITE_LOCK = threading.Lock()
_CACHES = {}


class _SilentProgress:
    def update_absolute(self, value, total):
        return None


def _state_root():
    try:
        import folder_paths
        root = Path(folder_paths.get_user_directory())
    except (ImportError, AttributeError):
        root = Path(__file__).resolve().parent / "_state"
    return root / "matrix-compiled" / _PACK_ID


def _credential_root():
    try:
        import folder_paths
        return Path(folder_paths.get_user_directory()) / "credentials"
    except (ImportError, AttributeError):
        return _state_root() / "credentials"


def _comfy_context(live):
    if not live:
        return _SilentProgress(), (lambda event, payload: None), ""
    try:
        from comfy.utils import ProgressBar
        from server import PromptServer
    except ImportError as exc:
        raise RuntimeError("live execution requires the ComfyUI runtime") from exc
    server = PromptServer.instance
    prompt_id = str(getattr(server, "last_prompt_id", "") or "")
    if not prompt_id:
        raise RuntimeError("live execution has no ComfyUI prompt id")

    def send_status(event, payload):
        return server.send_sync(event, payload, getattr(server, "client_id", None))

    return ProgressBar(1), send_status, prompt_id


def _cache(provider):
    if provider not in _CACHES:
        from .cache_semantic import SemanticCache
        _CACHES[provider] = SemanticCache(_state_root() / provider / "cache")
    return _CACHES[provider]


def _persist(provider, node_id, prompt_id):
    path = _state_root() / provider / "submissions.jsonl"

    def persist(record):
        entry = {
            "node_id": node_id,
            "prompt_id": prompt_id,
            "record": dict(record),
        }
        line = json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n"
        with _WRITE_LOCK:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(line)

    return persist


def _path(value, dotted):
    for part in dotted.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _auth_headers(contract, credential):
    if contract["auth"] == "bearer":
        return {"Authorization": "Bearer " + credential}
    header_name = contract["auth"].split(":", 1)[1]
    return {header_name: contract["auth_prefix"] + credential}


async def _upload_large_file(
    data,
    filename,
    content_type,
    *,
    credential,
    auth_headers,
    lifecycle,
    base_url,
    deadline,
    request_timeout,
):
    from .errors_taxonomy import EmptyOrMalformedSuccessError
    from .media_image_in import RemoteAsset
    from .transport_http import HttpResponse, request

    template = lifecycle.get("upload")
    if not isinstance(template, str) or not template:
        raise EmptyOrMalformedSuccessError("provider fact has no upload endpoint")
    try:
        method, endpoint = template.split(None, 1)
    except ValueError as exc:
        raise EmptyOrMalformedSuccessError(
            "provider upload endpoint must declare method and URL"
        ) from exc
    method = method.upper()
    if method != "POST":
        raise EmptyOrMalformedSuccessError(
            "binary upload endpoint must use POST"
        )
    boundary = "----MatrixCompiled" + hashlib.sha256(data).hexdigest()[:24]
    safe_name = Path(str(filename)).name.replace('"', "")
    extra_parts = [
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field_name}"\r\n\r\n'
            f"{field_value}\r\n"
        ).encode("utf-8")
        for field_name, field_value in lifecycle.get("upload_extra_fields", {}).items()
    ]
    prefix = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{safe_name}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("ascii")
    body = b"".join(extra_parts) + prefix + data + f"\r\n--{boundary}--\r\n".encode("ascii")
    headers = dict(auth_headers(credential))
    headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    response = await request(
        method,
        endpoint.format(base_url=base_url),
        deadline=deadline,
        request_timeout=request_timeout,
        headers=headers,
        data=body,
    )
    if not isinstance(response, HttpResponse):
        raise EmptyOrMalformedSuccessError("upload transport returned no HTTP response")
    try:
        decoded = json.loads(response.body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EmptyOrMalformedSuccessError("upload response was not valid JSON") from exc
    url_paths = lifecycle.get("upload_url_paths") or ("data.download_url", "data.url", "url")
    url = None
    for dotted in url_paths:
        url = _path(decoded, dotted)
        if url:
            break
    if not isinstance(url, str) or not url.startswith(("https://", "http://")):
        raise EmptyOrMalformedSuccessError("upload response contained no usable URL")
    retention = int(lifecycle.get("upload_retention_days", 0))
    if retention < 1:
        raise EmptyOrMalformedSuccessError("provider fact has no upload retention")
    return RemoteAsset(remote_id=url, url=url, expires_at=time.time() + retention * 86400)


def build_runtime(
    node_id,
    provider,
    route_ids,
    inputs,
    *,
    run_operations=1,
    instance_id=None,
):
    """Build every flow.api-media dependency without adding a node widget."""
    try:
        contract = RUNTIME_CONTRACTS[provider]
    except KeyError as exc:
        raise RuntimeError(f"compiled pack has no runtime for provider {provider!r}") from exc
    live = bool(inputs.get("live", False))
    selected_route = str(inputs.get("model") or tuple(route_ids)[0])
    try:
        operation_ceiling = float(contract["route_max_costs"][selected_route])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(
            f"compiled pack has no automatic cost bound for route {selected_route!r}"
        ) from exc
    if int(run_operations) < 1:
        raise RuntimeError("run_operations must be at least one")
    actual_node_id = str(instance_id or node_id)
    progress_bar, send_status, prompt_id = _comfy_context(live)
    make_headers = lambda credential: _auth_headers(contract, credential)
    return {
        "auth_headers": make_headers,
        "base_url": contract["base_url"],
        "credential_root": _credential_root(),
        "env_names": contract["env_names"],
        "max_download_bytes": contract["max_download_bytes"],
        "persist": _persist(provider, actual_node_id, prompt_id),
        "node_id": actual_node_id,
        "node_type": str(node_id),
        "progress_bar": progress_bar,
        "prompt_id": prompt_id,
        "provider_fact": contract["provider_fact"],
        "per_operation_ceiling": operation_ceiling,
        "route_ids": tuple(route_ids),
        "run_id": prompt_id or node_id,
        "run_ceiling": operation_ceiling * int(run_operations),
        "max_in_flight": 1,
        "upload_request_timeout": 300,
        "semantic_cache": _cache(provider),
        "send_status": send_status,
        "upload_large_file": partial(_upload_large_file, auth_headers=make_headers),
    }


__all__ = ["RUNTIME_CONTRACTS", "build_runtime"]
