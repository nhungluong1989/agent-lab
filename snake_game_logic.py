from __future__ import annotations

from dataclasses import dataclass, replace
from random import Random

GRID_WIDTH = 16
GRID_HEIGHT = 16

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

DIRECTION_BY_NAME = {
    "up": UP,
    "down": DOWN,
    "left": LEFT,
    "right": RIGHT,
}

OPPOSITE_DIRECTIONS = {
    UP: DOWN,
    DOWN: UP,
    LEFT: RIGHT,
    RIGHT: LEFT,
}


@dataclass(frozen=True)
class GameState:
    snake: tuple[tuple[int, int], ...]
    direction: tuple[int, int]
    food: tuple[int, int]
    score: int = 0
    game_over: bool = False


def create_initial_state(
    *,
    width: int = GRID_WIDTH,
    height: int = GRID_HEIGHT,
    rng: Random | None = None,
) -> GameState:
    center_x = width // 2
    center_y = height // 2
    snake = (
        (center_x, center_y),
        (center_x - 1, center_y),
        (center_x - 2, center_y),
    )
    food = place_food(snake, width=width, height=height, rng=rng)
    return GameState(snake=snake, direction=RIGHT, food=food, score=0, game_over=False)


def turn_direction(
    current_direction: tuple[int, int], next_direction: str | None
) -> tuple[int, int]:
    if next_direction is None:
        return current_direction

    normalized = next_direction.lower()
    if normalized not in DIRECTION_BY_NAME:
        return current_direction

    candidate = DIRECTION_BY_NAME[normalized]
    if candidate == OPPOSITE_DIRECTIONS[current_direction]:
        return current_direction
    return candidate


def step_game(
    state: GameState,
    *,
    width: int = GRID_WIDTH,
    height: int = GRID_HEIGHT,
    requested_direction: str | None = None,
    rng: Random | None = None,
) -> GameState:
    if state.game_over:
        return state

    direction = turn_direction(state.direction, requested_direction)
    head_x, head_y = state.snake[0]
    next_head = (head_x + direction[0], head_y + direction[1])

    if not (0 <= next_head[0] < width and 0 <= next_head[1] < height):
        return replace(state, direction=direction, game_over=True)

    ate_food = next_head == state.food
    body_to_check = state.snake if ate_food else state.snake[:-1]
    if next_head in body_to_check:
        return replace(state, direction=direction, game_over=True)

    if ate_food:
        next_snake = (next_head, *state.snake)
        next_score = state.score + 1
        next_food = place_food(next_snake, width=width, height=height, rng=rng)
    else:
        next_snake = (next_head, *state.snake[:-1])
        next_score = state.score
        next_food = state.food

    return GameState(
        snake=next_snake,
        direction=direction,
        food=next_food,
        score=next_score,
        game_over=False,
    )


def place_food(
    snake: tuple[tuple[int, int], ...],
    *,
    width: int = GRID_WIDTH,
    height: int = GRID_HEIGHT,
    rng: Random | None = None,
) -> tuple[int, int]:
    generator = rng or Random()
    occupied = set(snake)
    available = [
        (x, y)
        for y in range(height)
        for x in range(width)
        if (x, y) not in occupied
    ]
    if not available:
        return snake[0]
    return available[generator.randrange(len(available))]
