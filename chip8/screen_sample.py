import time
from dataclasses import dataclass

import vt100


@dataclass
class Point:
    x: int
    y: int


@dataclass
class Sprite:
    x_size: int
    y_size: int
    pixels: list[list[bool]]

    def get_pixel(self, point: Point) -> bool:
        return self.pixels[point.y][point.x]


Font = tuple[int, int, int, int, int]

ZERO: Font = (0xF0, 0x90, 0x90, 0x90, 0xF0)
ONE: Font = (0x20, 0x60, 0x20, 0x20, 0x70)
TWO: Font = (0xF0, 0x10, 0xF0, 0x80, 0xF0)
THREE: Font = (0xF0, 0x10, 0xF0, 0x10, 0xF0)
FOUR: Font = (0x90, 0x90, 0xF0, 0x10, 0x10)
FIVE: Font = (0xF0, 0x80, 0xF0, 0x10, 0xF0)
SIX: Font = (0xF0, 0x80, 0xF0, 0x90, 0xF0)
SEVEN: Font = (0xF0, 0x10, 0x20, 0x40, 0x40)
EIGHT: Font = (0xF0, 0x90, 0xF0, 0x90, 0xF0)
NINE: Font = (0xF0, 0x90, 0xF0, 0x10, 0xF0)
A: Font = (0xF0, 0x90, 0xF0, 0x90, 0x90)
B: Font = (0xE0, 0x90, 0xE0, 0x90, 0xE0)
C: Font = (0xF0, 0x80, 0x80, 0x80, 0xF0)
D: Font = (0xE0, 0x90, 0x90, 0x90, 0xE0)
E: Font = (0xF0, 0x80, 0xF0, 0x80, 0xF0)
F: Font = (0xF0, 0x80, 0xF0, 0x80, 0x80)


def font_to_sprite(font: Font) -> Sprite:
    pixels = []
    for byte in font:
        bits = [bit == "1" for bit in f"{byte:08b}"]
        pixels.append(bits)
    return Sprite(8, 5, pixels)


class Bitmap:
    WIDTH: int = 64
    HEIGHT: int = 32

    def __init__(self) -> None:
        self._pixels = [[False] * self.WIDTH for _ in range(self.HEIGHT)]

    def write_bit(self, point: Point) -> None:
        self._pixels[point.y][point.x] = True

    def delete_bit(self, point: Point) -> None:
        self._pixels[point.y][point.x] = False

    def flip_bit(self, point: Point) -> None:
        self._pixels[point.y][point.x] = not self._pixels[point.y][point.x]

    def set_bit(self, point: Point, value: bool) -> None:
        self._pixels[point.y][point.x] = value

    @property
    def pixels(self) -> list[list[bool]]:
        return self._pixels

    def write_splite(self, point: Point, splite: Sprite) -> None:
        for y in range(splite.y_size):
            if point.y + y >= self.HEIGHT:
                continue
            for x in range(splite.x_size):
                if point.x + x >= self.WIDTH:
                    continue
                self.set_bit(Point(point.x + x, point.y + y), splite.get_pixel(Point(x, y)))


def draw_bitmap(bitmap: Bitmap, on_char: str = "█", off_char: str = " ", is_border: bool = False) -> None:
    border_horizontal = "─"
    border_vertical = "│"
    border_upper_left = "┌"
    border_lower_left = "└"
    border_upper_right = "┐"
    border_lower_right = "┘"

    horizontal_line = border_horizontal * bitmap.WIDTH
    if is_border:
        print(border_upper_left + horizontal_line + border_upper_right)

    for row_pixels in bitmap.pixels:
        line = "".join([on_char if pixel else off_char for pixel in row_pixels])
        if is_border:
            line = border_vertical + line + border_vertical
        print(line)

    if is_border:
        print(border_lower_left + horizontal_line + border_lower_right)


def main():
    bitmap = Bitmap()
    # bitmap.set_on(Point(0, 0))
    # bitmap.set_on(Point(63, 0))
    # bitmap.set_on(Point(0, 31))
    # bitmap.set_on(Point(63, 31))
    # bitmap.set_on(Point(64 // 2, 32 // 2))
    fonts = [
        font_to_sprite(font) for font in [ZERO, ONE, TWO, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE, A, B, C, D, E, F]
    ]

    reset_screen = vt100.clear_screen() + vt100.return_cursor_to_home()

    while True:
        for i in range(len(fonts)):
            x_offset = 8 * (i % 8)
            y_offset = 5 * (i // 8) + i // 8
            point = Point(x_offset, y_offset)
            splite = fonts[i]
            bitmap.write_splite(point, splite)

        seconds = int(time.time() % 10)
        bitmap.write_splite(Point(0, 25), fonts[seconds])

        print(reset_screen, end="")
        draw_bitmap(bitmap, is_border=True)
        time.sleep(0.1)


if __name__ == "__main__":
    main()
