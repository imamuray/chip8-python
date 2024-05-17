import select
import sys
import termios
import time
import tty

import screen
from cpu import DEFAULT_PC_ADDRESS, FONT_START_ADDRESS, Chip8CPU
from memory import Memory
from screen import VirtualScreen


class NonBlockingConsole:
    def __enter__(self):
        self.old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        return self

    def __exit__(self, type, value, traceback):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

    def get_data(self) -> str | None:
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            return sys.stdin.read(1)
        return None


def main() -> None:
    filename = sys.argv[1]

    memory = Memory()
    memory.load_fonts(FONT_START_ADDRESS)

    with open(filename, "rb") as f:
        for i, byte in enumerate(f.read()):
            memory.write(DEFAULT_PC_ADDRESS + i, byte)

    v_screen = VirtualScreen()
    cpu = Chip8CPU(memory, v_screen)

    with NonBlockingConsole() as nbc:
        while True:
            key_data = nbc.get_data()
            if key_data == "\x1b":
                break
            cpu.execute_instruction(key_data)
            print(cpu)
            screen.render_to_console(cpu.screen, is_border=True)
            time.sleep(0.05)


if __name__ == "__main__":
    main()
