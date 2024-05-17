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

    def __str__(self) -> str:
        return "\n".join(["".join([f"{1 if pixel else 0}" for pixel in row]) for row in self.pixels])


def bytes_to_sprite(_bytes: list[int]) -> Sprite:
    pixels = []
    for byte in _bytes:
        bits = [bit == "1" for bit in f"{byte:08b}"]
        pixels.append(bits)
    return Sprite(8, len(_bytes), pixels)


class VirtualScreen:
    WIDTH: int = 64
    HEIGHT: int = 32

    def __init__(self) -> None:
        self._pixels = [[False] * self.WIDTH for _ in range(self.HEIGHT)]

    def set_bit(self, point: Point, value: bool) -> None:
        self._pixels[point.y][point.x] = value

    def xor_bit(self, point: Point, value: bool) -> None:
        self._pixels[point.y][point.x] ^= value

    @property
    def pixels(self) -> list[list[bool]]:
        return self._pixels

    def get_pixel(self, point: Point) -> bool:
        return self.pixels[point.y][point.x]

    def clear(self) -> None:
        self._pixels = [[False] * self.WIDTH for _ in range(self.HEIGHT)]

    def draw_sprite(self, point: Point, splite: Sprite) -> int:
        collision_flag = 0
        for y in range(splite.y_size):
            drow_y = point.y + y
            if drow_y >= self.HEIGHT:
                continue
            for x in range(splite.x_size):
                drow_x = point.x + x
                if drow_x >= self.WIDTH:
                    continue
                drow_point = Point(drow_x, drow_y)
                prev = self.get_pixel(drow_point)
                self.xor_bit(drow_point, splite.get_pixel(Point(x, y)))
                # もともとあったピクセルが消えた場合 collision_flag を立てる
                if prev and not self.get_pixel(drow_point):
                    collision_flag = 1
        return collision_flag


def render_to_console(screen: VirtualScreen, on_char: str = "█", off_char: str = " ", is_border: bool = False) -> None:
    border_horizontal = "─"
    border_vertical = "│"
    border_upper_left = "┌"
    border_lower_left = "└"
    border_upper_right = "┐"
    border_lower_right = "┘"

    horizontal_line = border_horizontal * screen.WIDTH
    if is_border:
        print(border_upper_left + horizontal_line + border_upper_right)

    for row_pixels in screen.pixels:
        line = "".join([on_char if pixel else off_char for pixel in row_pixels])
        if is_border:
            line = border_vertical + line + border_vertical
        print(line)

    if is_border:
        print(border_lower_left + horizontal_line + border_lower_right)
