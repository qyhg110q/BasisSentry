# BasisSentry

BasisSentry is a long-running monitoring service for Binance Spot vs USDⓈ-M perpetuals. It calculates real-time basis, detects spot order book walls (including wall removal vs wall eaten), records events, and exposes a local web UI for live monitoring.

## Features

- **Universe discovery** from Spot and USDⓈ-M exchangeInfo intersection.
- **Real-time basis engine** with rolling z-score and duration tracking.
- **Wall detection** from Spot depth20 with `WALL_APPEAR`, `WALL_GROW`, `WALL_MOVE`, `WALL_WEAKEN`, `WALL_REMOVE`, `WALL_EATEN`.
- **Event storage** as JSONL plus event packs for replay.
- **UI gateway** (FastAPI) with REST + WebSocket for live dashboards.
- **React UI** with dashboard, symbol detail, alerts, and event pack views.

## Requirements

- Python 3.11+
- Node.js 18+ (for the UI)

## Quick Start

### 1) Configure

Edit `config.yaml` to choose auto or manual symbols, thresholds, UI host/port, and other settings.

### 2) Run the backend + UI gateway

```bash
python -m app --config config.yaml
```

The UI gateway will be available at `http://127.0.0.1:8000` (configurable via `ui.host` and `ui.port`).

### 3) Dry-run (print universe + subscriptions)

```bash
python -m app --config config.yaml --dry-run
```

### 4) Run the UI

```bash
cd ui
npm install
npm run dev
```

Open `http://127.0.0.1:5173` to view the dashboard.

## REST API (UI gateway)

- `GET /api/v1/symbols` — list symbols and latest state summary.
- `GET /api/v1/state?symbol=XXX` — latest state for one symbol.
- `GET /api/v1/events?symbol=XXX&since=timestamp_ms&types=...` — recent events.
- `GET /api/v1/timeseries?symbol=XXX&range=5m|15m|1h|6h` — downsampled series.
- `GET /api/v1/event-packs` — list event packs.
- `GET /api/v1/event-packs/{id}` — fetch event pack records.

WebSocket stream:

- `ws://127.0.0.1:8000/ws/v1/stream`

Message types:

- `state_update` — batched symbol summaries (every second).
- `event` — immediate event payloads.

## Project Layout

```
app/              # backend services and engines
ui/               # React UI (Vite)
config.yaml       # configuration defaults
scripts/          # replay/report scripts
```

## Notes

- The backend respects proxy env vars for REST calls via `aiohttp.ClientSession(trust_env=True)`.
- Binance WebSocket limits apply; see `config.yaml` for stream caps.
- Events are recorded to `data/events.jsonl`, and event packs to `data/event_packs/`.
