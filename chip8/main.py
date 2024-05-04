from dataclasses import dataclass


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

    def set_on(self, point: Point) -> None:
        self._pixels[point.y][point.x] = True

    def set_off(self, point: Point) -> None:
        self._pixels[point.y][point.x] = False

    def set_flip(self, point: Point) -> None:
        self._pixels[point.y][point.x] = not self._pixels[point.y][point.x]

    def set_value(self, point: Point, value: bool) -> None:
        self._pixels[point.y][point.x] = value

    @property
    def pixels(self) -> list[list[bool]]:
        return self._pixels


def write_splite(bitmap: Bitmap, point: Point, splite: Sprite) -> None:
    for y in range(splite.y_size):
        if point.y + y >= bitmap.HEIGHT:
            continue
        for x in range(splite.x_size):
            if point.x + x >= bitmap.WIDTH:
                continue
            bitmap.set_value(Point(point.x + x, point.y + y), splite.get_pixel(Point(x, y)))


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
    fonts = [ZERO, ONE, TWO, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE, A, B, C, D, E, F]

    for i in range(len(fonts)):
        x_offset = 8 * (i % 8)
        y_offset = 5 * (i // 8) + i // 8
        point = Point(x_offset, y_offset)
        splite = font_to_sprite(fonts[i])
        write_splite(bitmap, point, splite)

    draw_bitmap(bitmap, is_border=True)


if __name__ == "__main__":
    main()
