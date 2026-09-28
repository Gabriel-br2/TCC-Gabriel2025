import type { ClientConfig } from "./config";
import { rgb } from "./config";
import { pieceWorldVertices, tickRotation, type Piece } from "./shapes";

export function drawBoard(
  ctx: CanvasRenderingContext2D,
  config: ClientConfig,
  pieces: Piece[],
  iou: number,
  options?: { showHud?: boolean; showMice?: { color: string; x: number; y: number }[] },
): void {
  const { width, height } = config.screen;
  const bg = rgb(config.colors, "background");
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = `rgb(${bg[0]}, ${bg[1]}, ${bg[2]})`;
  ctx.fillRect(0, 0, width, height);

  for (const piece of pieces) {
    tickRotation(piece);
    drawPiece(ctx, piece);
  }

  if (options?.showMice) {
    for (const mouse of options.showMice) {
      const color = rgb(config.colors, mouse.color);
      ctx.beginPath();
      ctx.fillStyle = `rgba(${color[0]}, ${color[1]}, ${color[2]}, 0.9)`;
      ctx.arc(mouse.x, mouse.y, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "black";
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  }

  if (options?.showHud !== false) {
    ctx.fillStyle = "rgb(0, 0, 0)";
    ctx.font = "bold 18px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(
      `Objetivo Concluído: ${(iou * 100).toFixed(2)} %`,
      width / 2,
      25,
    );
  }
}

function drawPiece(ctx: CanvasRenderingContext2D, piece: Piece): void {
  const world = pieceWorldVertices(piece);
  if (world.length < 3) {
    return;
  }
  const [r, g, b, a] = piece.color;
  const alpha = a / 255;
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(world[0][0], world[0][1]);
  for (let i = 1; i < world.length; i += 1) {
    ctx.lineTo(world[i][0], world[i][1]);
  }
  ctx.closePath();
  ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha})`;
  ctx.fill();
  ctx.strokeStyle = `rgba(0, 0, 0, ${alpha})`;
  ctx.lineWidth = 1;
  ctx.stroke();
  ctx.restore();
}
