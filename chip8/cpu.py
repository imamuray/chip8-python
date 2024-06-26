import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from typing import TypeAlias

import screen
from memory import Memory
from register import Register8, Register16
from screen import Point, VirtualScreen

DEFAULT_PC_ADDRESS = 0x200
FONT_START_ADDRESS = 0x000


@dataclass
class Decoder:
    opcode: int

    def x_y(self) -> tuple[int, int]:
        """
        16ビットの opecode (0x_XY_) から X, Y を取得する。

        Returns:
            tuple[int, int]: X, Y
        """
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        return (x, y)

    def x_y_n(self) -> tuple[int, int, int]:
        """
        16ビットの opecode (0x_XYN) から X, Y, N を取得する。

        Returns:
            tuple[int, int, int]: X, Y, N
        """
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        n = self.opcode & 0x000F
        return (x, y, n)

    def x_nn(self) -> tuple[int, int]:
        """
        16ビットの opecode (0x_XNN) から X, NN を取得する。

        Returns:
            tuple[int, int]: X, NN
        """
        x = (self.opcode & 0x0F00) >> 8
        nn = self.opcode & 0x00FF
        return (x, nn)

    def nnn(self) -> int:
        """
        16ビットの opecode (0x_NNN) から NNN を取得する。


        Returns:
            int: NNN
        """
        return self.opcode & 0x0FFF

    def x_only(self) -> int:
        """
        16ビットの opecode (0x_X__) から X を取得する。


        Returns:
            int: X
        """
        return (self.opcode & 0x0F00) >> 8


class CPUState(Enum):
    RUNNING = auto()
    WAITING = auto()


KEY_MAP = {
    "1": 0x1,
    "2": 0x2,
    "3": 0x3,
    "4": 0xC,
    "q": 0x4,
    "w": 0x5,
    "e": 0x6,
    "r": 0xD,
    "a": 0x7,
    "s": 0x8,
    "d": 0x9,
    "f": 0xE,
    "z": 0xA,
    "x": 0x0,
    "c": 0xB,
    "v": 0xF,
}


def _get_key_value(key: str | None) -> int | None:
    match key:
        case None:
            return None
        case _:
            key_lowered = key.lower()
            if key_lowered not in KEY_MAP.keys():
                return None
            return KEY_MAP[key_lowered]


class Chip8CPU:
    def __init__(self, memory: Memory, screen: VirtualScreen) -> None:
        self.memory = memory
        self.screen = screen

        self.stack = [0] * 16
        self.rg_vs = [Register8() for _ in range(16)]
        self.rg_i = Register16()
        self.rg_pc = Register16(DEFAULT_PC_ADDRESS)
        self.rg_sp = Register8()
        self.rg_dt = Register8()
        self.rg_st = Register8()

        self.state = CPUState.RUNNING

        Instruction: TypeAlias = Callable[[Decoder], None]
        InstructionTable: TypeAlias = dict[int, Instruction]

        self.instructions_FFFF: InstructionTable = {
            0x00E0: self.clear_screen,
            0x00EE: self.return_from_subroutine,
        }

        self.instructions_F000: InstructionTable = {
            0x1000: self.jump_to_address,  # 1NNN - jp addr
            0x2000: self.call_subroutine,  # 2NNN - call addr
            0x3000: self.skip_if_vx_eq_value,  # 3XNN - se vx, nn
            0x4000: self.skip_if_vx_neq_value,  # 4XNN - sne vx, nn
            0x6000: self.set_value_to_vx,  # 6XNN - ld vx, nn
            0x7000: self.add_value_to_vx,  # 7XNN - add vx, nn
            0xA000: self.set_address_to_i,  # ANNN - ld i, addr
            0xB000: self.jump_to_v0_plus,  # BNNN - jp v0, addr
            0xC000: self.set_random_to_vx,  # CXNN - rnd vx, byte
            0xD000: self.draw_sprite,  # DXYN - drw vx, vy, nibble
        }

        self.instructions_F00F: InstructionTable = {
            0x5000: self.skip_if_vx_eq_vy,  # 5XY0 - se vx, vy
            0x8000: self.set_vy_value_to_vx,  # 8XY0 - ld vx, vy
            0x8001: self.logical_or_to_vx,  # 8XY1 - or vx, vy
            0x8002: self.logical_and_to_vx,  # 8XY2 - and vx, vy
            0x8003: self.xor_to_vx,  # 8XY3 - xor vx, vy
            0x8004: self.add_vy_value_to_vx,  # 8XY4 - add vx, vy
            0x8005: self.subtract_vy_value_from_vx,  # 8XY5 - sub vx, vy
            0x8006: self.right_shift,  # 8XY6 - shr vx {, vy}
            0x8007: self.subtract_vx_value_from_vy,  # 8XY7 - subn vy, vx
            0x800E: self.left_shift,  # 8XYE - shl vx {, vy}
            0x9000: self.skip_if_vx_neq_vy,  # 9XY0 - sen vx, vy
        }

        self.instructions_F0FF: InstructionTable = {
            0xF007: self.set_dt_value_to_vx,  # FX07 - ld vx, dt
            0xF00A: self.wait_for_key,  # FX0A - ld vx, key TODO
            0xF015: self.set_vx_value_to_dt,  # FX15 - ld dt, vx
            0xF018: self.set_vx_value_to_st,  # FX18 - ld st, vx
            0xF01E: self.add_vx_value_to_i,  # FX1E - add i, vx
            0xF029: self.set_font_address_to_i,  # FX29 - ld f, vx
            0xF033: self.bcd,  # FX33 - ld b, vx
            0xF055: self.save_vx,  # FX55 - ld [i], vx
            0xF065: self.load_vx,  # FX65 - ld vx, [i]
        }

        KeyboardInstruction: TypeAlias = Callable[[Decoder, str | None], None]
        self.keyboard_instructions: dict[int, KeyboardInstruction] = {
            0xE09E: self.skip_if_key_pressed,  # E09E - skp vx
            0xE0A1: self.skip_if_key_not_pressed,  # E0A1 - sknp vx
        }

    def __str__(self) -> str:
        return "\n".join(
            [
                f"vx: {','.join([f'[{i:x}]{v}' for i, v in enumerate(self.rg_vs)])}",
                f"i : {self.rg_i}",
                f"pc: {self.rg_pc}",
                f"sp: {self.rg_sp}",
                f"dt: {self.rg_dt}",
                f"st: {self.rg_st}",
                f"stack: {','.join([f'[{i:x}]{x:#x}' for i, x in enumerate(self.stack)])}",
            ]
        )

    def _get_opcode(self) -> int:
        """
        メモリから pc + 2 分読み込んで opcode を取得する。

        この関数実行後に pc は2インクリメントされる。

        Returns:
            int: opcode
        """
        program_counter = self.rg_pc.read()
        # メモリは8bitずつ入っているので1命令のために2回読み込む
        opcode = self.memory.read(program_counter) << 8 | self.memory.read(program_counter + 1)
        self.rg_pc.write(program_counter + 2)
        return opcode

    def execute_instruction(self, pressed_key: str | None = None) -> None:
        opcode = self._get_opcode()
        print(f"[DEBUG] pressed_key: {pressed_key}")
        print(f"[DEBUG] opecode: {opcode:04x}")

        decoder = Decoder(opcode)
        instructions_with_mask = [
            (self.instructions_FFFF, 0xFFFF),
            (self.instructions_F000, 0xF000),
            (self.instructions_F00F, 0xF00F),
            (self.instructions_F0FF, 0xF0FF),
        ]

        for instructions, mask in instructions_with_mask:
            match instructions.get(opcode & mask):
                case None:
                    pass
                case instruction:
                    instruction(decoder)
                    break

        match self.keyboard_instructions.get(opcode & 0xF0FF):
            case None:
                pass
            case keyboard_instruction:
                keyboard_instruction(decoder, pressed_key)

    def clear_screen(self, decoder: Decoder) -> None:
        self.screen.clear()

    def return_from_subroutine(self, decoder: Decoder) -> None:
        sp = self.rg_sp.read() - 1
        return_address = self.stack[sp]
        self.rg_pc.write(return_address)
        self.rg_sp.write(sp)

    def jump_to_address(self, decoder: Decoder) -> None:
        address = decoder.nnn()
        self.rg_pc.write(address)

    def call_subroutine(self, decoder: Decoder) -> None:
        subroutine_address = decoder.nnn()
        sp = self.rg_sp.read()
        self.stack[sp] = self.rg_pc.read()
        self.rg_sp.write(sp + 1)
        self.rg_pc.write(subroutine_address)

    def skip_if_vx_eq_value(self, decoder: Decoder) -> None:
        x, value = decoder.x_nn()
        if self.rg_vs[x].read() == value:
            self.rg_pc.write(self.rg_pc.read() + 2)

    def skip_if_vx_neq_value(self, decoder: Decoder) -> None:
        x, value = decoder.x_nn()
        if self.rg_vs[x].read() != value:
            self.rg_pc.write(self.rg_pc.read() + 2)

    def skip_if_vx_eq_vy(self, decoder: Decoder) -> None:
        x, y = decoder.x_y()
        if self.rg_vs[x].read() == self.rg_vs[y].read():
            self.rg_pc.write(self.rg_pc.read() + 2)

    def set_value_to_vx(self, decoder: Decoder) -> None:
        x, value = decoder.x_nn()
        self.rg_vs[x].write(value)

    def add_value_to_vx(self, decoder: Decoder) -> None:
        x, value = decoder.x_nn()
        self.rg_vs[x].write(self.rg_vs[x].read() + value)

    def set_vy_value_to_vx(self, decoder: Decoder) -> None:
        x, y = decoder.x_y()
        self.rg_vs[x].write(self.rg_vs[y].read())

    def logical_or_to_vx(self, decoder: Decoder) -> None:
        x, y = decoder.x_y()
        result = self.rg_vs[x].read() | self.rg_vs[y].read()
        self.rg_vs[x].write(result)

    def logical_and_to_vx(self, decoder: Decoder) -> None:
        x, y = decoder.x_y()
        result = self.rg_vs[x].read() & self.rg_vs[y].read()
        self.rg_vs[x].write(result)

    def xor_to_vx(self, decoder: Decoder) -> None:
        x, y = decoder.x_y()
        result = self.rg_vs[x].read() ^ self.rg_vs[y].read()
        self.rg_vs[x].write(result)

    def add_vy_value_to_vx(self, decoder: Decoder) -> None:
        # carry があったとき vf に 1 をセットする
        x, y = decoder.x_y()
        result = self.rg_vs[x].read() + self.rg_vs[y].read()
        carry = 1 if (result & 0x100) == 0x100 else 0
        self.rg_vs[x].write(result & 0xFF)
        self.rg_vs[0xF].write(carry)

    def subtract_vy_value_from_vx(self, decoder: Decoder) -> None:
        # 8XY5 - vx -= vy, if vx > vy then vf = 1 else vf = 0
        # vf は carry フラグと考えると加算のときと合う
        x, y = decoder.x_y()
        x_value = self.rg_vs[x].read()
        y_value = self.rg_vs[y].read()

        # 2の補数表現を使って vx - yv を計算
        # python のビット反転は -(x + 1) と同じ
        # https://docs.python.org/ja/3/reference/expressions.html#unary-arithmetic-and-bitwise-operations
        result = x_value + (~y_value & 0xFF) + 1
        carry = 1 if (result & 0x100) == 0x100 else 0
        self.rg_vs[x].write(result & 0xFF)
        self.rg_vs[0xF].write(carry)

    def right_shift(self, decoder: Decoder) -> None:
        # 8XY6 - vx >>= 1, vf には vx の最下位ビットを格納
        x, _ = decoder.x_y()
        x_value = self.rg_vs[x].read()

        rightmost_bit = x_value & 0x01
        result = x_value >> 1
        self.rg_vs[x].write(result & 0xFF)
        self.rg_vs[0xF].write(rightmost_bit)

    def subtract_vx_value_from_vy(self, decoder: Decoder) -> None:
        # 8XY7 - vx := vy - vx, if vy > vx then vf = 1 else vf = 0
        x, y = decoder.x_y()
        x_value = self.rg_vs[x].read()
        y_value = self.rg_vs[y].read()

        # 2の補数表現を使って vy - yx を計算
        # python のビット反転は -(x + 1) と同じ
        # https://docs.python.org/ja/3/reference/expressions.html#unary-arithmetic-and-bitwise-operations
        result = y_value + (~x_value & 0xFF) + 1
        carry = 1 if (result & 0x100) == 0x100 else 0
        self.rg_vs[x].write(result & 0xFF)
        self.rg_vs[0xF].write(carry)

    def left_shift(self, decoder: Decoder) -> None:
        # 8XYE - vx <<= 1, vf には vx の最上位ビットを格納
        x, _ = decoder.x_y()
        x_value = self.rg_vs[x].read()

        leftmost_bit = (x_value & 0x80) >> 7
        result = x_value << 1
        self.rg_vs[x].write(result & 0xFF)
        self.rg_vs[0xF].write(leftmost_bit)

    def skip_if_vx_neq_vy(self, decoder: Decoder) -> None:
        x, y = decoder.x_y()
        if self.rg_vs[x].read() != self.rg_vs[y].read():
            self.rg_pc.write(self.rg_pc.read() + 2)

    def set_address_to_i(self, decoder: Decoder) -> None:
        address = decoder.nnn()
        self.rg_i.write(address)

    def jump_to_v0_plus(self, decoder: Decoder) -> None:
        nnn = decoder.nnn()
        address = self.rg_vs[0].read() + nnn
        self.rg_pc.write(address)

    def set_random_to_vx(self, decoder: Decoder) -> None:
        x, nn = decoder.x_nn()
        value = random.randint(0, 255) & nn
        self.rg_vs[x].write(value)

    def draw_sprite(self, decoder: Decoder) -> None:
        # スプライトは幅8bit高さN
        x, y, n = decoder.x_y_n()
        address = self.rg_i.read()
        _bytes = [self.memory.read(i) for i in range(address, address + n)]
        x_value = self.rg_vs[x].read()
        y_value = self.rg_vs[y].read()
        sprite = screen.bytes_to_sprite(_bytes)
        collision_flag = self.screen.draw_sprite(Point(x_value, y_value), sprite)
        self.rg_vs[0xF].write(collision_flag)

    def skip_if_key_pressed(self, decoder: Decoder, pressed_key: str | None) -> None:
        x = decoder.x_only()
        x_value = self.rg_vs[x].read()
        match _get_key_value(pressed_key):
            case key_value if key_value == x_value:
                self.rg_pc.write(self.rg_pc.read() + 2)
            case _:
                return

    def skip_if_key_not_pressed(self, decoder: Decoder, pressed_key: str | None) -> None:
        x = decoder.x_only()
        x_value = self.rg_vs[x].read()
        match _get_key_value(pressed_key):
            case key_value if key_value != x_value:
                self.rg_pc.write(self.rg_pc.read() + 2)
            case _:
                return

    def set_dt_value_to_vx(self, decoder: Decoder) -> None:
        x = decoder.x_only()
        self.rg_vs[x].write(self.rg_dt.read())

    def wait_for_key(self, decoder: Decoder) -> None:
        # TODO
        pass

    def set_vx_value_to_dt(self, decoder: Decoder) -> None:
        x = decoder.x_only()
        self.rg_dt.write(self.rg_vs[x].read())

    def set_vx_value_to_st(self, decoder: Decoder) -> None:
        x = decoder.x_only()
        self.rg_st.write(self.rg_vs[x].read())

    def add_vx_value_to_i(self, decoder: Decoder) -> None:
        x = decoder.x_only()
        self.rg_i.write(self.rg_i.read() + self.rg_vs[x].read())

    def set_font_address_to_i(self, decoder: Decoder) -> None:
        x = decoder.x_only()
        x_value = self.rg_vs[x].read()
        # NOTE: font は1文字5バイトで順番に格納されているので、vxの値を5倍にする
        address = FONT_START_ADDRESS + (x_value & 0xF) * 5
        self.rg_i.write(address)

    def bcd(self, decoder: Decoder) -> None:
        x = decoder.x_only()
        x_value = self.rg_vs[x].read()
        address = self.rg_i.read()
        hundreds, tens, ones = x_value // 100, (x_value // 10) % 10, x_value % 10
        self.memory.write(address, hundreds)
        self.memory.write(address + 1, tens)
        self.memory.write(address + 2, ones)

    def save_vx(self, decoder: Decoder) -> None:
        target = decoder.x_only()
        address = self.rg_i.read()
        for i in range(0, target + 1):
            rg_x_value = self.rg_vs[i].read()
            self.memory.write(address + i, rg_x_value)

    def load_vx(self, decoder: Decoder) -> None:
        target = decoder.x_only()
        address = self.rg_i.read()
        for i in range(0, target + 1):
            value = self.memory.read(address + i)
            self.rg_vs[i].write(value)


def write_instruction(memory: Memory, address: int, code: int) -> int:
    first_half_code = (code & 0xFF00) >> 8
    second_half_code = code & 0x00FF
    memory.write(address, first_half_code)
    memory.write(address + 1, second_half_code)
    return address + 2


if __name__ == "__main__":
    import sys

    filename = sys.argv[1]

    memory = Memory()
    memory.load_fonts(FONT_START_ADDRESS)

    with open(filename, "rb") as f:
        for i, byte in enumerate(f.read()):
            memory.write(DEFAULT_PC_ADDRESS + i, byte)

    v_screen = VirtualScreen()
    cpu = Chip8CPU(memory, v_screen)

    while True:
        cpu.execute_instruction()
        print(cpu)
        screen.render_to_console(cpu.screen, is_border=True)
        time.sleep(0.1)
