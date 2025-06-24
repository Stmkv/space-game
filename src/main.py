import asyncio
import curses
import itertools
import os.path
import random
import time

from animation import fire, fly_garbage
from curses_tools import (
    draw_frame,
    get_frame_size,
    read_controls,
    get_frames,
    sleep,
    update_speed,
)

SPACESHIP_FRAME = ""
COROUTINES = []
STAR_SYMBOL = "+*.:"
STARS_COUNT = 100
STARS_ROW, STARS_COLUMN = 5, 2
TIC_TIMEOUT = 0.1
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STARSHIP_FRAMES_DIR = os.path.join(BASE_DIR, "frames", "starship")
GARBAGE_FRAMES_DIR = os.path.join(BASE_DIR, "frames", "garbage")


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

async def animate_spaceship(rocket_frames):
    global SPACESHIP_FRAME

    for frame in itertools.cycle(rocket_frames):
        SPACESHIP_FRAME = frame
        await sleep(2)


async def control_spaceship(
    canvas: "curses.window",
    row: int,
    column: int,
    frames: list[str],
) -> None:
    # Крайние точки карты
    min_x, min_y = 1, 1
    max_x, max_y = canvas.getmaxyx()

    global SPACESHIP_FRAME
    end_frame = SPACESHIP_FRAME

    frame_cycle = itertools.cycle(frames)
    # Начальная скорость корабля
    weight_speed = 0
    height_speed = 0

    for frame in frame_cycle:
        delta_row, delta_column, space = read_controls(canvas)
        frame_rows, frame_columns = get_frame_size(frame)

        weight_speed, height_speed = update_speed(weight_speed, height_speed, delta_row, delta_column)

        if column + delta_column + frame_columns > max_y or column + delta_column + 1 < min_y + 1:
            height_speed = 0
        if row + delta_row + frame_rows > max_x or row + delta_row + 1 < min_x + 1:
            weight_speed = 0
        if end_frame:
            draw_frame(canvas, row, column, end_frame, negative=True)

        row += weight_speed
        column += height_speed
        draw_frame(canvas, row, column, SPACESHIP_FRAME)

        end_frame = SPACESHIP_FRAME

        await asyncio.sleep(0)


async def fill_orbit_with_garbage(canvas, garbage_frames):
    max_width = canvas.getmaxyx()[1]

    while True:
        COROUTINES.append(
            fly_garbage(
                canvas, random.randint(1, max_width), random.choice(garbage_frames)
            )
        )
        await sleep(10)


def draw(canvas: "curses.window") -> None:
    curses.curs_set(False)
    canvas.nodelay(True)
    canvas.border()

    max_height, max_width = canvas.getmaxyx()
    for _ in range(STARS_COUNT):
        row = random.randint(1, max_height - 2)
        col = random.randint(1, max_width - 2)
        symbol = random.choice(STAR_SYMBOL)
        COROUTINES.append(
            blink(canvas, row, col, random.randint(0, STARS_COUNT), symbol)
        )

    COROUTINES.append(fire(canvas, max_height // 2, max_width // 2))

    starship_frames = get_frames(STARSHIP_FRAMES_DIR, repeat=2)
    garbage_frames = get_frames(GARBAGE_FRAMES_DIR)

    COROUTINES.append(
        control_spaceship(canvas, max_height // 2, max_width // 2, starship_frames)
    )
    COROUTINES.append(fill_orbit_with_garbage(canvas, garbage_frames))
    COROUTINES.append(animate_spaceship(starship_frames))

    while True:
        for corutine in COROUTINES.copy():
            try:
                corutine.send(None)
            except StopIteration:
                COROUTINES.remove(corutine)
            canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)
