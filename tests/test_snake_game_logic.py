import unittest
from random import Random

from snake_game_logic import (
    DOWN,
    GRID_HEIGHT,
    GRID_WIDTH,
    LEFT,
    RIGHT,
    GameState,
    create_initial_state,
    place_food,
    step_game,
    turn_direction,
)


class SnakeGameLogicTests(unittest.TestCase):
    def test_initial_state_spawns_three_segment_snake(self) -> None:
        state = create_initial_state(rng=Random(0))

        self.assertEqual(((8, 8), (7, 8), (6, 8)), state.snake)
        self.assertEqual(RIGHT, state.direction)
        self.assertNotIn(state.food, state.snake)

    def test_turn_direction_rejects_reverse_moves(self) -> None:
        self.assertEqual(RIGHT, turn_direction(RIGHT, "left"))
        self.assertEqual(DOWN, turn_direction(RIGHT, "down"))

    def test_step_moves_head_forward_and_keeps_length(self) -> None:
        state = GameState(
            snake=((3, 3), (2, 3), (1, 3)),
            direction=RIGHT,
            food=(10, 10),
        )

        next_state = step_game(state)

        self.assertEqual(((4, 3), (3, 3), (2, 3)), next_state.snake)
        self.assertEqual(0, next_state.score)
        self.assertFalse(next_state.game_over)

    def test_step_grows_snake_and_increments_score_when_food_eaten(self) -> None:
        state = GameState(
            snake=((3, 3), (2, 3), (1, 3)),
            direction=RIGHT,
            food=(4, 3),
        )

        next_state = step_game(state, rng=Random(0))

        self.assertEqual(((4, 3), (3, 3), (2, 3), (1, 3)), next_state.snake)
        self.assertEqual(1, next_state.score)
        self.assertNotIn(next_state.food, next_state.snake)

    def test_step_detects_wall_collision(self) -> None:
        state = GameState(
            snake=((GRID_WIDTH - 1, 4), (GRID_WIDTH - 2, 4), (GRID_WIDTH - 3, 4)),
            direction=RIGHT,
            food=(0, 0),
        )

        next_state = step_game(state)

        self.assertTrue(next_state.game_over)

    def test_step_detects_self_collision(self) -> None:
        state = GameState(
            snake=((4, 4), (4, 5), (5, 5), (5, 4)),
            direction=LEFT,
            food=(0, 0),
        )

        next_state = step_game(state, requested_direction="down")

        self.assertTrue(next_state.game_over)

    def test_food_placement_uses_only_open_cells(self) -> None:
        snake = tuple(
            (x, 0)
            for x in range(GRID_WIDTH)
        ) + tuple(
            (x, y)
            for y in range(1, GRID_HEIGHT)
            for x in range(GRID_WIDTH)
            if not (x == GRID_WIDTH - 1 and y == GRID_HEIGHT - 1)
        )

        food = place_food(snake, rng=Random(0))

        self.assertEqual((GRID_WIDTH - 1, GRID_HEIGHT - 1), food)


if __name__ == "__main__":
    unittest.main()
