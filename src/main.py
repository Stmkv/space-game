import asyncio
import random
import time
import curses

from animation import fire

STAR_SYMBOL = "+*.:"
STARS_COUNT = 100
STARS_ROW, STARS_COLUMN = 5, 2
TIC_TIMEOUT = 0.1


async def blink(canvas, row, column, symbol="*"):
    for _ in range(random.randint(0, STARS_COUNT)):
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


def draw(canvas):
    curses.curs_set(False)
    canvas.border()

    max_height, max_width = canvas.getmaxyx()
    corutines = []
    for _ in range(STARS_COUNT):
        row = random.randint(1, max_height - 2)
        col = random.randint(1, max_width - 2)
        symbol = random.choice(STAR_SYMBOL)
        corutines.append(blink(canvas, row, col, symbol))

    corutine_fire = fire(canvas, max_height/ 2, max_width / 2)
    corutines.append(corutine_fire)
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
