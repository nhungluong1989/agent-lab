from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

from snake_game_logic import GRID_HEIGHT, GRID_WIDTH

st.set_page_config(page_title="Snake", page_icon=":snake:", layout="centered")

CELL_SIZE = 22
BOARD_WIDTH = GRID_WIDTH * CELL_SIZE
BOARD_HEIGHT = GRID_HEIGHT * CELL_SIZE

st.title("Snake")
st.caption("Arrow keys or WASD to move. Space pauses. Enter restarts.")

game_config = {
    "gridWidth": GRID_WIDTH,
    "gridHeight": GRID_HEIGHT,
    "cellSize": CELL_SIZE,
    "tickMs": 140,
}

components.html(
    f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8" />
        <style>
          :root {{
            color-scheme: light;
            --bg: #f6f7fb;
            --panel: #ffffff;
            --border: #d7dbe7;
            --text: #1f2937;
            --muted: #667085;
            --snake: #1f7a4d;
            --snake-head: #16603c;
            --food: #d14343;
            --grid-a: #ffffff;
            --grid-b: #eef2f7;
          }}
          * {{
            box-sizing: border-box;
          }}
          body {{
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: var(--bg);
            color: var(--text);
          }}
          .wrap {{
            display: grid;
            gap: 12px;
            justify-items: center;
            padding: 8px 0 4px;
          }}
          .hud {{
            width: min(100%, {BOARD_WIDTH}px);
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            font-size: 14px;
          }}
          .score {{
            font-weight: 600;
          }}
          .status {{
            color: var(--muted);
          }}
          .board {{
            border: 1px solid var(--border);
            border-radius: 10px;
            overflow: hidden;
            background: var(--panel);
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
          }}
          canvas {{
            display: block;
            width: {BOARD_WIDTH}px;
            height: {BOARD_HEIGHT}px;
            max-width: 100%;
            background: var(--panel);
          }}
          .controls {{
            width: min(100%, 260px);
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            touch-action: manipulation;
          }}
          button {{
            border: 1px solid var(--border);
            background: var(--panel);
            color: var(--text);
            border-radius: 10px;
            padding: 10px 0;
            font: inherit;
            cursor: pointer;
          }}
          button.primary {{
            grid-column: span 3;
            font-weight: 600;
          }}
          .empty {{
            visibility: hidden;
          }}
        </style>
      </head>
      <body>
        <div class="wrap">
          <div class="hud">
            <div class="score" id="score">Score: 0</div>
            <div class="status" id="status">Running</div>
          </div>
          <div class="board">
            <canvas id="board" width="{BOARD_WIDTH}" height="{BOARD_HEIGHT}"></canvas>
          </div>
          <div class="controls">
            <div class="empty">.</div>
            <button data-dir="up">Up</button>
            <div class="empty">.</div>
            <button data-dir="left">Left</button>
            <button data-action="pause">Pause</button>
            <button data-dir="right">Right</button>
            <div class="empty">.</div>
            <button data-dir="down">Down</button>
            <div class="empty">.</div>
            <button class="primary" data-action="restart">Restart</button>
          </div>
        </div>
        <script>
          const config = {json.dumps(game_config)};
          const canvas = document.getElementById("board");
          const ctx = canvas.getContext("2d");
          const scoreEl = document.getElementById("score");
          const statusEl = document.getElementById("status");
          const theme = getComputedStyle(document.documentElement);
          const colors = {{
            gridA: theme.getPropertyValue("--grid-a").trim(),
            gridB: theme.getPropertyValue("--grid-b").trim(),
            snake: theme.getPropertyValue("--snake").trim(),
            snakeHead: theme.getPropertyValue("--snake-head").trim(),
            food: theme.getPropertyValue("--food").trim(),
          }};

          const directionMap = {{
            up: {{ x: 0, y: -1 }},
            down: {{ x: 0, y: 1 }},
            left: {{ x: -1, y: 0 }},
            right: {{ x: 1, y: 0 }},
          }};

          function opposite(a, b) {{
            return a.x + b.x === 0 && a.y + b.y === 0;
          }}

          function randInt(max) {{
            return Math.floor(Math.random() * max);
          }}

          function createInitialState() {{
            const midX = Math.floor(config.gridWidth / 2);
            const midY = Math.floor(config.gridHeight / 2);
            const snake = [
              {{ x: midX, y: midY }},
              {{ x: midX - 1, y: midY }},
              {{ x: midX - 2, y: midY }},
            ];
            return {{
              snake,
              direction: {{ ...directionMap.right }},
              nextDirection: {{ ...directionMap.right }},
              food: placeFood(snake),
              score: 0,
              gameOver: false,
              paused: false,
            }};
          }}

          function placeFood(snake) {{
            const occupied = new Set(snake.map((part) => `${{part.x}},${{part.y}}`));
            const open = [];
            for (let y = 0; y < config.gridHeight; y += 1) {{
              for (let x = 0; x < config.gridWidth; x += 1) {{
                const key = `${{x}},${{y}}`;
                if (!occupied.has(key)) {{
                  open.push({{ x, y }});
                }}
              }}
            }}
            return open[randInt(open.length)] || snake[0];
          }}

          let state = createInitialState();

          function setDirection(name) {{
            const candidate = directionMap[name];
            if (!candidate || opposite(candidate, state.direction)) {{
              return;
            }}
            state.nextDirection = {{ ...candidate }};
          }}

          function restart() {{
            state = createInitialState();
            render();
          }}

          function togglePause() {{
            if (state.gameOver) {{
              return;
            }}
            state.paused = !state.paused;
            render();
          }}

          function step() {{
            if (state.gameOver || state.paused) {{
              return;
            }}

            state.direction = {{ ...state.nextDirection }};
            const head = state.snake[0];
            const nextHead = {{
              x: head.x + state.direction.x,
              y: head.y + state.direction.y,
            }};

            const outOfBounds =
              nextHead.x < 0 ||
              nextHead.y < 0 ||
              nextHead.x >= config.gridWidth ||
              nextHead.y >= config.gridHeight;

            if (outOfBounds) {{
              state.gameOver = true;
              render();
              return;
            }}

            const ateFood = nextHead.x === state.food.x && nextHead.y === state.food.y;
            const body = ateFood ? state.snake : state.snake.slice(0, -1);
            if (body.some((part) => part.x === nextHead.x && part.y === nextHead.y)) {{
              state.gameOver = true;
              render();
              return;
            }}

            state.snake = [nextHead, ...state.snake];
            if (ateFood) {{
              state.score += 1;
              state.food = placeFood(state.snake);
            }} else {{
              state.snake.pop();
            }}
            render();
          }}

          function drawCell(x, y, color) {{
            const px = x * config.cellSize;
            const py = y * config.cellSize;
            ctx.fillStyle = color;
            ctx.fillRect(px + 1, py + 1, config.cellSize - 2, config.cellSize - 2);
          }}

          function renderBoard() {{
            for (let y = 0; y < config.gridHeight; y += 1) {{
              for (let x = 0; x < config.gridWidth; x += 1) {{
                ctx.fillStyle = (x + y) % 2 === 0 ? colors.gridA : colors.gridB;
                ctx.fillRect(
                  x * config.cellSize,
                  y * config.cellSize,
                  config.cellSize,
                  config.cellSize
                );
              }}
            }}

            drawCell(state.food.x, state.food.y, colors.food);
            state.snake.forEach((part, index) => {{
              drawCell(part.x, part.y, index === 0 ? colors.snakeHead : colors.snake);
            }});
          }}

          function render() {{
            renderBoard();
            scoreEl.textContent = `Score: ${{state.score}}`;
            if (state.gameOver) {{
              statusEl.textContent = "Game over";
            }} else if (state.paused) {{
              statusEl.textContent = "Paused";
            }} else {{
              statusEl.textContent = "Running";
            }}
          }}

          document.addEventListener("keydown", (event) => {{
            const key = event.key.toLowerCase();
            if (["arrowup", "arrowdown", "arrowleft", "arrowright", "w", "a", "s", "d", " ", "enter"].includes(key)) {{
              event.preventDefault();
            }}

            if (key === "arrowup" || key === "w") setDirection("up");
            if (key === "arrowdown" || key === "s") setDirection("down");
            if (key === "arrowleft" || key === "a") setDirection("left");
            if (key === "arrowright" || key === "d") setDirection("right");
            if (key === " ") togglePause();
            if (key === "enter") restart();
          }});

          document.querySelectorAll("button[data-dir]").forEach((button) => {{
            button.addEventListener("click", () => setDirection(button.dataset.dir));
          }});

          document.querySelector('[data-action="pause"]').addEventListener("click", togglePause);
          document.querySelector('[data-action="restart"]').addEventListener("click", restart);

          render();
          setInterval(step, config.tickMs);
        </script>
      </body>
    </html>
    """,
    height=640,
)
