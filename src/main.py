import asyncio
import curses
import itertools
import os.path
import random
import time

from animation import fire
from curses_tools import draw_frame, get_frame_size, read_controls

STAR_SYMBOL = "+*.:"
STARS_COUNT = 100
STARS_ROW, STARS_COLUMN = 5, 2
TIC_TIMEOUT = 0.1
FRAMES_DIR = os.path.join("src", "frames")


async def blink(
        canvas,
        row: int,
        column: int,
        offset_tics: int,
        symbol: str = "*",
) -> None:
    for _ in range(offset_tics):
        await asyncio.sleep(0)

    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


def get_frames() -> list[str]:
    frame_files = [os.path.join(FRAMES_DIR, f) for f in os.listdir(FRAMES_DIR)]
    frames = []
    for filename in frame_files:
        with open(filename, "r") as f:
            frame = f.read()
            frames.append(frame)
            frames.append(frame)
    return frames


async def animate_spaceship(
        canvas: "curses.window",
        row: int,
        column: int,
        frames: list[str],
) -> None:
    prev_height, prev_width = row, column
    min_x, min_y = 1, 1
    max_x, max_y = canvas.getmaxyx()
    end_frame = None
    frame_cycle = itertools.cycle(frames)

    for frame in frame_cycle:
        delta_row, delta_column, space = read_controls(canvas)
        frame_rows, frame_columns = get_frame_size(frame)

        if (
                delta_column + frame_columns + prev_width > max_y - 1
                or prev_width + delta_column + 1 < min_y + 1
        ):
            delta_column = 0
        if (
                delta_row + frame_rows + prev_height > max_x - 1
                or prev_height + delta_row + 1 < min_x + 1
        ):
            delta_row = 0

        if end_frame:
            draw_frame(canvas, prev_height, prev_width, end_frame, negative=True)

        prev_height = new_row = prev_height + delta_row
        prev_width = new_column = prev_width + delta_column
        draw_frame(canvas, new_row, new_column, frame)

        end_frame = frame

        await asyncio.sleep(0)


def draw(canvas: "curses.window") -> None:
    curses.curs_set(False)
    canvas.nodelay(True)
    canvas.border()

    max_height, max_width = canvas.getmaxyx()
    corutines = []
    for _ in range(STARS_COUNT):
        row = random.randint(1, max_height - 2)
        col = random.randint(1, max_width - 2)
        symbol = random.choice(STAR_SYMBOL)
        corutines.append(blink(canvas, row, col, random.randint(0, STARS_COUNT), symbol))

    corutines.append(fire(canvas, max_height // 2, max_width // 2))

    frames = get_frames()
    corutines.append(animate_spaceship(canvas, max_height // 2, max_width // 2, frames))

    while True:
        for corutine in corutines.copy():
            try:
                corutine.send(None)
            except StopIteration:
                corutines.remove(corutine)
            canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)
