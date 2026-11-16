# seedess-sdk

Official Seedess SDK for Python.

**Server-side only.** The SDK uses a secret API key (`key_…`) to create and control streams.
Never ship it in a browser or a mobile app. Playback uses the separate `@seedess/*-p2p`
packages and a per-stream public token (`pk_…`).

## Install

```bash
pip install seedess-sdk
```

Python 3.9+.

## Use

```python
import os
from seedess_sdk import Seedess

seedess = Seedess(os.environ["SEEDESS_API_KEY"])

stream = seedess.create_stream(
    "https://origin.example/master.m3u8",
    id="demo",
    live=True,
)

print(stream["publicToken"])
print(stream["playback"]["master"])
```

Pass only the public token and stream id to the page:

```python
return {"stream": stream["id"], "token": stream["publicToken"]}
```

## Methods

| Method | HTTP | Purpose |
| --- | --- | --- |
| `create_stream(url, id=..., title=..., live=...)` | `POST /api/v1/streams` | Ingest a manifest, mint the public token. |
| `get_stream(id)` | `GET /api/v1/streams/:id` | Status, variants, segment count. |
| `list_streams()` | `GET /api/v1/streams` | All streams in the tenant. |
| `refresh_stream(id)` | `POST /api/v1/streams/:id/refresh` | Pull new live segments. |
| `disable_peers(id)` | `POST /api/v1/streams/:id/kill` | CDN only; playback continues. |
| `enable_peers(id)` | `POST /api/v1/streams/:id/revive` | Re-enable peer delivery. |
| `get_metrics(id)` | `GET /api/v1/streams/:id/metrics` | Offload and delivery counters. |
| `send_telemetry(...)` | `POST /api/v1/telemetry` | One session batch (public, rate limited). |

`request(method, path, body=None, auth=True)` is available for routes without a helper.

## Errors

```python
from seedess_sdk import SeedessError

try:
    seedess.create_stream(url)
except SeedessError as error:
    print(error.status, error.code, error.message)
```

## Links

- Docs: https://seedess.com/docs/
- API: https://seedess.com/docs/api/
- Libraries: https://seedess.com/docs/libraries/

## License

MIT.
