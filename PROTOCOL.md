# Player WebSocket protocol (frozen)

This file is the freeze for the human web client. The Python server
(`game/server/application.py`) is authoritative. Do not rename fields.
Do not add keys that players must understand.

Admin HTTP is **not** part of this protocol. It lives on a separate port
and must not share the game WebSocket without an auth handshake that
game clients do not send.

## Transport

- Local: `ws://<host>:<port>/` (default port `8000`)
- Ngrok: `wss://<ngrok-host>/` with header `ngrok-skip-browser-warning: 1`
- Messages: UTF-8 JSON text frames
- One TCP connection per player. Server closes the socket if all slots are full.

## Handshake

Client sends first:

```json
{"nature": "human", "name": "Ana Silva"}
```

| Field    | Type   | Notes                                      |
|----------|--------|--------------------------------------------|
| `nature` | string | `"human"` or `"LLM"`                       |
| `name`   | string | Display / log name. Humans: `"Nome Sobrenome"` |

Server may send other JSON before the handshake reply (ignore until `"id"` is present).

Handshake reply (starts the session):

```json
{
  "id": 2,
  "timestamp": "14_09_02_34_00",
  "objects": {
    "P0": {
      "id": 0,
      "color": "blue",
      "pos": [[100, 200, 0, "hero"], [400, 300, 90, "z"]]
    },
    "P1": { "id": 1, "color": "pink", "pos": [] },
    "IoU": 0,
    "cycle_id": 1
  },
  "reset": false,
  "is_paused": true,
  "connected_players": 1,
  "total_players": 4
}
```

| Field                | Type    | Notes |
|----------------------|---------|--------|
| `id`                 | int     | Slot `0 .. playerNum-1`. Required to start. |
| `timestamp`          | string  | Session log folder id. |
| `objects`            | object  | See below. |
| `reset`              | bool    | Rebuild all local shapes from `objects`. |
| `is_paused`          | bool    | True while `connected_players < total_players`. No input, no sends. |
| `connected_players`  | int     | Fully identified clients. |
| `total_players`      | int     | From config (`playerNum`). |

`objects` keys:

- `P0` .. `P{n-1}`: `{ id, color, pos, mouse? }`
- `IoU`: number in **0..1** (HUD multiplies by 100)
- `cycle_id`: int

`pos` is an array of pieces. Each piece is **`[x, y, rz, type]`**:

| Index | Meaning | Notes |
|-------|---------|--------|
| 0     | `x`     | Canvas pixels, origin top-left |
| 1     | `y`     | Canvas pixels |
| 2     | `rz`    | Degrees. Visual rotation; play rotates by +90 clockwise |
| 3     | `type`  | `"generic"` \| `"hero"` \| `"ricky"` \| `"teewee"` \| `"z"` |

`color` is a palette key from `COLOR_CONFIG` / `config/color.yaml` (`blue`, `pink`, …), not an RGB triple.

## Play (client → server)

Sent every rendered frame while **not** paused, **not** in the 3s cycle banner, and local `pos` is non-empty.

```json
{"pos": [[120, 210, 90, "hero"], [400, 300, 90, "z"]], "cycle_id": 1, "mouse": [512, 388]}
```

| Field      | Type         | Notes |
|------------|--------------|--------|
| `pos`      | number[][]   | **Only this client's pieces**, each `[x,y,rz,type]`. Never wrap mouse inside `pos`. |
| `cycle_id` | int          | Must match the current cycle. Server ignores mismatches. |
| `mouse`    | [number, number] | Cursor in canvas pixels. |

**Wrong (do not send):** `"pos": [ pieces, mouse ]`.

## Broadcast (server → client)

Same envelope as the handshake minus `id` / `timestamp`:

```json
{
  "objects": { "P0": { "color": "blue", "pos": [...], "mouse": [0, 0] }, "IoU": 0.42, "cycle_id": 1 },
  "reset": false,
  "is_paused": false,
  "connected_players": 4,
  "total_players": 4
}
```

Apply rules (see `game/client/application.py`):

1. If `type === "shutdown"` → leave the session. This message has **no** `objects`.
2. If `reset === true` → discard all shapes, rebuild from `objects`, show the cycle banner for **3 seconds**, then continue. Local `cycle_id` comes from `objects.cycle_id`.
3. Else → keep local pieces; for every **other** player, copy `objects[Pn].pos[obj_id]` into `[x,y,rz]` (`pos` entry without `type`). Ignore missing keys/indexes.
4. HUD IoU = `objects.IoU` (0..1). Win / cycle on the **server** when IoU `>= 0.95`.

Keep the latest complete broadcast if messages queue; do not interpolate.

## Shutdown

```json
{"type": "shutdown"}
```

After this the server closes sockets. No further play messages.

## Local simulation (client authority for own pieces only)

Replicate `game/client/players/motion.py` and `game/client/screen.py`:

- Left mouse: drag the top-most **own** piece under the cursor (hit-test reverse draw order).
- Right mouse: start a +90° clockwise rotation (animated +10° per frame at 60 FPS until `rz % 90 === 0`).
- Own pieces cannot leave the screen (every transformed vertex inside `[0,width] × [0,height]`).
- Own pieces cannot overlap **each other**. Overlap with other players is allowed and required for scoring.
- Other players' pieces: alpha = config `transparency` (default 50/255). Own pieces: alpha 255. Draw own pieces last (on top).
- Transform: 2D rotation about `(x,y)` in degrees; vertex results truncated toward 0 (`int` / `Math.trunc`) to match Pygame.

Do **not** reimplement IoU, cycle generation, or overlap-guilt on the client.

## UI copy (Portuguese, exact)

| Screen           | Text |
|------------------|------|
| Identification   | Title `Identificação do Jogador`; labels `Nome:`, `Sobrenome:`; button `Continuar` (disabled until both fields non-empty). |
| Connecting       | `Rodada já completada aguarde sua vez` + animated dots. |
| Pause            | `Jogo pausado. Aguardando jogadores {n}/{total}.` |
| HUD              | `Objetivo Concluído: {iou * 100:.2f} %` |
| Cycle reset      | `Objetivo concluído, iniciando próximo ciclo` (3s) |
| Window title     | `Projeto de TCC - Gabriel - player: {id}` |

Default canvas: **1200×900**, background `rgb(255, 219, 187)`.

## Out of scope on the game socket

- Chat, voice, extra event names
- Admin commands, tokens, log download
- LLM screenshot / agent loops (Python `client.py --player LLM` only)
