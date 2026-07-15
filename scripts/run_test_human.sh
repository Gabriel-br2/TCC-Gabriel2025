#!/usr/bin/env bash
# Inicia o servidor e N clientes humanos conforme game.playerNum em game/shared/config.py.
# Uso: ./scripts/run_test_human.sh
# Encerre com Ctrl+C para parar o servidor e os clientes em background.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# --- venv ---
if [[ -f "$ROOT/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
elif [[ -f "$ROOT/venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/venv/bin/activate"
else
  echo "Erro: virtualenv não encontrado (.venv ou venv)." >&2
  exit 1
fi

PLAYER_NUM="$(python - <<'PY'
from game.shared.config import GAME_CONFIG

print(GAME_CONFIG["game"]["playerNum"])
PY
)"

if ! [[ "$PLAYER_NUM" =~ ^[1-9][0-9]*$ ]]; then
  echo "Erro: playerNum inválido em game/shared/config.py: '$PLAYER_NUM'" >&2
  exit 1
fi

SERVER_PID=""
CLIENT_PIDS=()

cleanup() {
  echo ""
  echo "Encerrando teste..."
  for pid in "${CLIENT_PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  if [[ -n "$SERVER_PID" ]]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

launch_client() {
  local name="$1"
  local cmd="cd '$ROOT' && source '${VIRTUAL_ENV}/bin/activate' && python client.py --player human --name '$name'"

  if command -v gnome-terminal >/dev/null 2>&1; then
    gnome-terminal --title="$name" -- bash -c "$cmd; exec bash"
  elif command -v konsole >/dev/null 2>&1; then
    konsole --new-tab -p tabtitle="$name" -e bash -c "$cmd; exec bash" &
  elif command -v xterm >/dev/null 2>&1; then
    xterm -title "$name" -e bash -c "$cmd; exec bash" &
  else
    bash -c "$cmd" &
    CLIENT_PIDS+=("$!")
  fi
}

echo "=== Teste: $PLAYER_NUM jogador(es) humano(s) (game/shared/config.py) ==="

echo "Iniciando servidor..."
python server.py &
SERVER_PID=$!
sleep 3

if ! kill -0 "$SERVER_PID" 2>/dev/null; then
  echo "Erro: servidor não iniciou." >&2
  exit 1
fi

echo "Iniciando $PLAYER_NUM cliente(s)..."
for ((i = 1; i <= PLAYER_NUM; i++)); do
  launch_client "Jogador $i"
  sleep 1
done

echo ""
echo "Servidor (PID $SERVER_PID) e $PLAYER_NUM cliente(s) em execução."
echo "Pressione Ctrl+C aqui para encerrar."

wait "$SERVER_PID" 2>/dev/null || true
