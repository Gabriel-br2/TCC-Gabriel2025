import datetime
import math
import multiprocessing as mp
import os
import queue
import time
import traceback

import numpy as np


def _with_timestamp(save_path: str) -> str:
    base, ext = os.path.splitext(save_path)
    ext = ext or ".rrd"
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base}_{stamp}{ext}"


def _snapshot_objects(objects: dict) -> dict:
    snapshot = {}
    for player_name, player in objects.items():
        if not isinstance(player, dict):
            continue
        mouse = player.get("mouse")
        snapshot[player_name] = {
            "color": player["color"],
            "pos": [tuple(obj) for obj in player["pos"]],
            "mouse": tuple(mouse) if mouse is not None else None,
        }
    return snapshot


def _transform_points(models: dict, obj, scale: float = 1.0) -> list[tuple[float, float]]:
    model = models[obj[3]]
    theta = math.radians(obj[2] % 360)
    cos_t, sin_t = math.cos(theta), math.sin(theta)

    points = []
    for px, py in model:
        x = (px * cos_t - py * sin_t + obj[0]) * scale
        y = (px * sin_t + py * cos_t + obj[1]) * scale
        points.append((x, y))
    return points


def _render_panel(
    pygame_module,
    objects: dict,
    owner: str,
    models: dict,
    color_palette: dict,
    background_color: tuple,
    other_player_alpha: int,
    canvas,
    overlay,
    scale: float,
) -> np.ndarray:
    pygame = pygame_module
    canvas.fill(background_color)
    overlay.fill((0, 0, 0, 0))  # limpa a transparência sem realocar memória

    for player_name, player in objects.items():
        is_owner = player_name == owner
        color_rgb = color_palette[player["color"]]
        alpha = 255 if is_owner else other_player_alpha
        outline_width = 3 if is_owner else 1
        color_rgba = (*color_rgb[:3], alpha)

        for obj in player["pos"]:
            world_points = _transform_points(models, obj, scale)
            pygame.draw.polygon(overlay, color_rgba, world_points)
            pygame.draw.polygon(overlay, color_rgba, world_points, width=outline_width)

        mouse = player.get("mouse")
        if mouse is not None:
            mouse_point = (mouse[0] * scale, mouse[1] * scale)
            cursor_radius = 6 if is_owner else 4
            pygame.draw.circle(overlay, color_rgba, mouse_point, cursor_radius)
            pygame.draw.circle(overlay, (0, 0, 0, alpha), mouse_point, cursor_radius, width=1)

    canvas.blit(overlay, (0, 0))  # um único blit por painel, não um por objeto
    frame_array = pygame.surfarray.pixels3d(canvas)
    return np.transpose(frame_array, (1, 0, 2))  # (largura,altura,rgb) -> (altura,largura,rgb)


def _build_blueprint(rrb_module, player_names: list[str]):
    rrb = rrb_module
    panel_views = [
        rrb.Spatial2DView(
            origin=f"panel_{name}",
            name=name,
            contents=[f"panel_{name}/**"],
        )
        for name in player_names
    ]

    return rrb.Blueprint(
        rrb.Horizontal(
            rrb.Grid(*panel_views, grid_columns=2),
            rrb.TimeSeriesView(
                origin="metrics",
                name="Métricas",
                contents=["metrics/**"],
            ),
            column_shares=[3, 1],
        ),
        collapse_panels=True,
    )

BACKGROUND_COLOR = (250, 235, 215)
OTHER_PLAYER_ALPHA = 90


def _monitor_process_main(
    task_queue: "mp.Queue",
    width: int,
    height: int,
    models: dict,
    color_palette: dict,
    save_path: str,
    render_scale: float,
):
    import pygame
    import rerun as rr
    import rerun.blueprint as rrb

    pygame.init()

    rec = rr.RecordingStream("server_monitor")
    rec.spawn()
    rec.set_sinks(rr.GrpcSink(), rr.FileSink(save_path))

    render_width = max(1, round(width * render_scale))
    render_height = max(1, round(height * render_scale))

    blueprint_sent = False
    canvases: dict = {}
    overlays: dict = {}

    while True:
        item = task_queue.get()  
        if item is None:  
            break

        objects, iou, frame_idx, server_time = item

        try:
            if not blueprint_sent:
                player_names = list(objects.keys())
                rec.send_blueprint(_build_blueprint(rrb, player_names))

                for name in player_names:
                    canvases[name] = pygame.Surface((render_width, render_height))
                    overlays[name] = pygame.Surface((render_width, render_height), pygame.SRCALPHA)

                blueprint_sent = True

            rec.set_time("frame", sequence=frame_idx)
            rec.set_time("server_time", timestamp=server_time)

            for owner in objects:
                frame_array = _render_panel(
                    pygame, objects, owner, models, color_palette,
                    BACKGROUND_COLOR, OTHER_PLAYER_ALPHA,
                    canvases[owner], overlays[owner], render_scale,
                )
                rec.log(f"panel_{owner}/render", rr.Image(frame_array))

            rec.log("metrics/iou", rr.Scalars(iou))

            rec.flush()
        except Exception:
            traceback.print_exc()

    rec.flush()


class ServerMonitor:
    def __init__(
        self,
        screen_config: dict,
        color_palette: dict,
        models: dict,
        save_path: str = "results/match.rrd",
        log_hz: float = 30.0,
        queue_size: int = 4,
        render_scale: float = 0.5,
    ):
        self.color = color_palette
        self.models = models
        self.width = screen_config["screen"]["width"]
        self.height = screen_config["screen"]["height"]
        self._frame_idx = 0

        self._log_interval = 1.0 / log_hz if log_hz > 0 else 0.0
        self._last_log_time = None

        save_path = _with_timestamp(save_path)
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        self.save_path = save_path

        ctx = mp.get_context("spawn")

        self._queue: "mp.Queue" = ctx.Queue(maxsize=queue_size)

        self._process = ctx.Process(
            target=_monitor_process_main,
            args=(
                self._queue, self.width, self.height, self.models,
                self.color, save_path, render_scale,
            ),
            daemon=True,
        )
        self._process.start()


    def observe(self, objects: dict, iou: float, timestamp: float | None = None) -> bool:
        now = time.monotonic()
        if self._last_log_time is not None and (now - self._last_log_time) < self._log_interval:
            return True
        self._last_log_time = now

        snapshot = _snapshot_objects(objects)
        frame_idx = self._frame_idx
        server_time = timestamp if timestamp is not None else time.time()
        self._frame_idx += 1

        try:
            self._queue.put_nowait((snapshot, iou, frame_idx, server_time))
        except queue.Full:
            pass

        return True

    def close(self):
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        self._process.join(timeout=5)
        if self._process.is_alive():
            self._process.terminate()