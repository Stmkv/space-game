import asyncio
import curses
import itertools
import os.path
import random
import time

from curses_tools import (
    draw_frame,
    get_frame_size,
    read_controls,
    get_frames,
    sleep,
    update_speed,
    Obstacle,
    explode
)

STAR_SYMBOL = "+*.:"
STARS_COUNT = 100
STARS_ROW, STARS_COLUMN = 5, 2
TIC_TIMEOUT = 0.1
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STARSHIP_FRAMES_DIR = os.path.join(BASE_DIR, "frames", "starship")
GARBAGE_FRAMES_DIR = os.path.join(BASE_DIR, "frames", "garbage")
GAME_OVER_FRAMES_DIR = os.path.join(BASE_DIR, "frames", "game_over")
YEAR = 1957
PHRASES = {
    1957: "First Sputnik",
    1961: "Gagarin flew!",
    1969: "Armstrong got on the moon!",
    1971: "First orbital space station Salute-1",
    1981: "Flight of the Shuttle Columbia",
    1998: 'ISS start building',
    2011: 'Messenger launch to Mercury',
    2020: "Take the plasma gun! Shoot the garbage!",
}


async def blink(
        canvas,
        row: int,
        column: int,
        offset_tics: int,
        symbol: str = "*",
) -> None:
    await sleep(offset_tics)

    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)

        canvas.addstr(row, column, symbol)
        await sleep(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)

        canvas.addstr(row, column, symbol)
        await sleep(3)


async def fly_garbage(canvas, column, garbage_frame, state, speed=1, ):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    obstacle_row_size, obstacle_column_size = get_frame_size(garbage_frame)
    garbage_obstacle_frame = Obstacle(row, column, obstacle_row_size, obstacle_column_size)
    state["obstacles"].append(garbage_obstacle_frame)

    await sleep(1)
    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
        garbage_obstacle_frame.row += speed

        for obstacle in state["obstacles_in_last_collision"]:
            if garbage_obstacle_frame is obstacle:
                state["obstacles"].remove(garbage_obstacle_frame)
                await explode(canvas, row, column)
                return


async def animate_spaceship(rocket_frames, state):
    for frame in itertools.cycle(rocket_frames):
        state["spaceship_frame"] = frame
        await sleep(2)


async def fire(canvas, start_row, start_column, state, rows_speed=-1, columns_speed=0):
    """Display animation of gun shot. Direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed

        for obstacle in state["obstacles"]:
            obj_corner = row, column
            if obstacle.has_collision(*obj_corner):
                state["obstacles_in_last_collision"].append(obstacle)
                return None


def get_garbage_delay_tics(year):
    if year < 1961:
        return None
    elif year < 1969:
        return 20
    elif year < 1981:
        return 14
    elif year < 1995:
        return 10
    elif year < 2010:
        return 8
    elif year < 2020:
        return 6
    else:
        return 2


async def control_spaceship(
        canvas: "curses.window",
        row: int,
        column: int,
        frames: list[str],
        state: dict,
) -> None:
    # Крайние точки карты
    min_x, min_y = 1, 1
    max_x, max_y = canvas.getmaxyx()

    end_frame = state["spaceship_frame"]

    frame_cycle = itertools.cycle(frames)
    # Начальная скорость корабля
    weight_speed = 0
    height_speed = 0

    for frame in frame_cycle:
        delta_row, delta_column, space_pressed = read_controls(canvas)
        frame_rows, frame_columns = get_frame_size(frame)

        if space_pressed and YEAR >= 2020:
            state["coroutines"].append(fire(canvas, row - 1, column + 2, state))

        weight_speed, height_speed = update_speed(
            weight_speed, height_speed, delta_row, delta_column
        )

        if (
                column + delta_column + frame_columns > max_y
                or column + delta_column + 1 < min_y + 1
        ):
            height_speed = 0
        if row + delta_row + frame_rows > max_x or row + delta_row + 1 < min_x + 1:
            weight_speed = 0
        if end_frame:
            draw_frame(canvas, row, column, end_frame, negative=True)

        row += weight_speed
        column += height_speed
        draw_frame(canvas, row, column, state["spaceship_frame"])

        for obstacle in state["obstacles"]:
            obj_corner = row, column
            if obstacle.has_collision(*obj_corner):
                show_game_over(canvas, end_frame, row, column, max_x, max_y)
                return

        end_frame = state["spaceship_frame"]

        await asyncio.sleep(0)


def show_game_over(canvas, end_frame, row, column, max_x, max_y):
    draw_frame(canvas, row, column, end_frame, negative=True)

    game_over_frames = get_frames(GAME_OVER_FRAMES_DIR)
    game_over = random.choice(game_over_frames)
    game_over_x, game_over_y = get_frame_size(game_over)
    draw_frame(
        canvas,
        max_x // 2 - game_over_x // 2,
        max_y // 2 - game_over_y // 2,
        game_over
    )


async def fill_orbit_with_garbage(canvas, garbage_frames, state):
    max_width = canvas.getmaxyx()[1]

    while True:
        debris_spawn_rate = get_garbage_delay_tics(YEAR)
        if not debris_spawn_rate:
            await sleep(1)
            continue
        await sleep(debris_spawn_rate)
        state["coroutines"].append(
            fly_garbage(
                canvas, random.randint(1, max_width), random.choice(garbage_frames), state
            )
        )


async def show_phrase(canvas):
    while True:
        try:
            draw_frame(canvas, 0, 0, f'{YEAR}: {PHRASES[YEAR]}')
        except KeyError:
            try:
                draw_frame(canvas, 0, 0, f'{YEAR - 1}: {PHRASES[YEAR - 1]}', negative=True)
            except KeyError:
                pass
            draw_frame(canvas, 0, 0, f'{YEAR}')
        await sleep(1)


async def change_year():
    global YEAR

    while True:
        await sleep(5)
        YEAR += 1


def draw(canvas: "curses.window") -> None:
    curses.curs_set(False)
    canvas.nodelay(True)

    max_height, max_width = canvas.getmaxyx()

    state = {
        "obstacles": [],
        "obstacles_in_last_collision": [],
        "coroutines": [],
        "spaceship_frame": "",
        "year": 1957,
    }

    for _ in range(STARS_COUNT):
        row = random.randint(1, max_height - 2)
        col = random.randint(1, max_width - 2)
        symbol = random.choice(STAR_SYMBOL)
        state["coroutines"].append(
            blink(canvas, row, col, random.randint(0, STARS_COUNT), symbol)
        )

    starship_frames = get_frames(STARSHIP_FRAMES_DIR, repeat=2)
    garbage_frames = get_frames(GARBAGE_FRAMES_DIR)

    state["coroutines"].append(
        control_spaceship(canvas, max_height // 2, max_width // 2, starship_frames, state)
    )
    state["coroutines"].append(fill_orbit_with_garbage(canvas, garbage_frames, state))
    state["coroutines"].append(animate_spaceship(starship_frames, state))
    state["coroutines"].append(show_phrase(canvas))
    state["coroutines"].append(change_year())

    while True:
        for corutine in state["coroutines"].copy():
            try:
                corutine.send(None)
            except StopIteration:
                state["coroutines"].remove(corutine)
            canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)
