import asyncio
import time
import curses


STARS_ROW, STARS_COLUMN = 5, 2


async def blink(canvas, row, column, symbol="*"):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)


def draw(canvas):
    curses.curs_set(False)  # Отключить символ курсора
    canvas.border()  # Нарисовать рамку

    corutines_draw_stars = [
        blink(canvas, STARS_ROW, STARS_COLUMN * indent) for indent in range(1, 6)
    ]
    while True:
        for corutine in corutines_draw_stars.copy():
            try:
                corutine.send(None)
            except StopIteration:
                break
            canvas.refresh()
        time.sleep(1)


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)
