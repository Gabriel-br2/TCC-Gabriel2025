"""Authenticated operator HTTP API. Does not share the game WebSocket."""

from __future__ import annotations

import logging
import os
import secrets
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from aiohttp import web

if TYPE_CHECKING:
    from game.server.application import GameServer

ALLOWED_LOG_FILES = frozenset(
    {"game_events.jsonl", "game_metadata.json", "game_players.jsonl"}
)
LOG_ROOT = Path("LOGS")
ADMIN_PORT_DEFAULT = 8001
WEB_DIST = Path("web/dist")


def ensure_admin_token() -> str:
    token = os.environ.get("ADMIN_TOKEN", "").strip()
    if token:
        return token
    token = secrets.token_urlsafe(24)
    os.environ["ADMIN_TOKEN"] = token
    logging.info("Admin token (set ADMIN_TOKEN to pin it): %s", token)
    return token


def _check_admin(request: web.Request) -> None:
    expected = request.app["admin_token"]
    header = request.headers.get("Authorization", "")
    token = ""
    if header.startswith("Bearer "):
        token = header.removeprefix("Bearer ").strip()
    if not token:
        token = request.query.get("token", "").strip()
    if not expected or token != expected:
        raise web.HTTPUnauthorized(text="Unauthorized")


@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        response: web.StreamResponse = web.Response()
    else:
        try:
            response = await handler(request)
        except web.HTTPException as exc:
            response = exc
    origin = request.headers.get("Origin", "*")
    response.headers["Access-Control-Allow-Origin"] = origin or "*"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


def _json(data: Any, status: int = 200) -> web.Response:
    return web.json_response(data, status=status)


async def public_config(request: web.Request) -> web.Response:
    server: GameServer = request.app["game_server"]
    host = request.headers.get("Host", "localhost")
    return _json(server.public_client_config(host))


async def admin_status(request: web.Request) -> web.Response:
    _check_admin(request)
    server: GameServer = request.app["game_server"]
    reveal = request.query.get("reveal", "0") in {"1", "true", "yes"}
    snapshot = await server.get_snapshot(reveal_names=reveal)
    return _json(snapshot)


async def admin_config(request: web.Request) -> web.Response:
    _check_admin(request)
    server: GameServer = request.app["game_server"]
    return _json(server.operator_config())


async def admin_shutdown(request: web.Request) -> web.Response:
    _check_admin(request)
    server: GameServer = request.app["game_server"]
    await server.shutdown()
    return _json({"ok": True})


async def admin_logs_index(request: web.Request) -> web.Response:
    _check_admin(request)
    sessions = []
    if LOG_ROOT.is_dir():
        for path in sorted(LOG_ROOT.iterdir(), reverse=True):
            if not path.is_dir():
                continue
            files = [
                name
                for name in ALLOWED_LOG_FILES
                if (path / name).is_file()
            ]
            sessions.append({"id": path.name, "files": files})
    return _json({"sessions": sessions})


async def admin_log_file(request: web.Request) -> web.Response:
    _check_admin(request)
    session_id = request.match_info["session"]
    filename = request.match_info["filename"]
    if filename not in ALLOWED_LOG_FILES:
        raise web.HTTPForbidden(text="Unknown log file")
    if "/" in session_id or "\\" in session_id or ".." in session_id:
        raise web.HTTPBadRequest(text="Invalid session id")
    path = (LOG_ROOT / session_id / filename).resolve()
    try:
        path.relative_to(LOG_ROOT.resolve())
    except ValueError as exc:
        raise web.HTTPForbidden(text="Invalid path") from exc
    if not path.is_file():
        raise web.HTTPNotFound(text="Log not found")
    return web.FileResponse(path, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


def build_admin_app(game_server: GameServer) -> web.Application:
    token = ensure_admin_token()
    app = web.Application(middlewares=[cors_middleware])
    app["game_server"] = game_server
    app["admin_token"] = token

    app.router.add_get("/api/public/config", public_config)
    app.router.add_get("/api/admin/status", admin_status)
    app.router.add_get("/api/admin/config", admin_config)
    app.router.add_post("/api/admin/shutdown", admin_shutdown)
    app.router.add_get("/api/admin/logs", admin_logs_index)
    app.router.add_get("/api/admin/logs/{session}/{filename}", admin_log_file)
    app.router.add_route("OPTIONS", "/api/{path:.*}", lambda _request: web.Response())

    dist = WEB_DIST
    if dist.is_dir():
        app.router.add_get("/", lambda _r: web.FileResponse(dist / "index.html"))
        admin_html = dist / "admin.html"
        if admin_html.is_file():
            app.router.add_get("/admin", lambda _r: web.FileResponse(admin_html))
            app.router.add_get("/admin.html", lambda _r: web.FileResponse(admin_html))
        app.router.add_static("/assets", dist / "assets", show_index=False)

    return app


async def start_admin_site(game_server: GameServer) -> web.AppRunner:
    port = int(os.environ.get("ADMIN_PORT", ADMIN_PORT_DEFAULT))
    bind = os.environ.get("ADMIN_BIND", "0.0.0.0")
    app = build_admin_app(game_server)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, bind, port)
    await site.start()
    logging.info("Admin HTTP on http://%s:%s (panel: /admin.html)", bind, port)
    logging.info("Game WebSocket remains on port %s (unchanged protocol)", game_server._settings.server_port)
    return runner
