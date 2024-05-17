import random
import time
from enum import Enum, auto

import screen
from memory import Memory
from register import Register8, Register16
from screen import Point, VirtualScreen

DEFAULT_PC_ADDRESS = 0x200
FONT_START_ADDRESS = 0x000


def _decode_x_y(opcode: int) -> tuple[int, int]:
    x = (opcode & 0x0F00) >> 8
    y = (opcode & 0x00F0) >> 4
    return (x, y)


def _decode_x_y_n(opcode: int) -> tuple[int, int, int]:
    x = (opcode & 0x0F00) >> 8
    y = (opcode & 0x00F0) >> 4
    n = opcode & 0x000F
    return (x, y, n)


def _decode_x_nn(opcode: int) -> tuple[int, int]:
    x = (opcode & 0x0F00) >> 8
    nn = opcode & 0x00FF
    return (x, nn)


def _decode_nnn(opcode: int) -> int:
    return opcode & 0x0FFF


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
            int: _description_
        """
        program_counter = self.rg_pc.read()
        # メモリは8bitずつ入っているので1命令のために2回読み込む
        opcode = self.memory.read(program_counter) << 8 | self.memory.read(program_counter + 1)
        self.rg_pc.write(program_counter + 2)
        return opcode

    def execute_instruction(self, pressed_key: str | None = None) -> None:
        print(f"[DEBUG] key: {pressed_key}")
        # FX0A の処理
        # TODO: 実装見直し
        if self.state == CPUState.WAITING:
            if not pressed_key:
                return
            match _get_key_value(pressed_key):
                case None:
                    return
                case key_value:
                    self.rg_vs[self.prev_decoded_x].write(key_value)
                    self.state = CPUState.RUNNING
                    return

        opcode = self._get_opcode()
        print(f"[DEBUG] opecode: {opcode:04x}")

        match opcode:
            # 00E0 - clear screen
            case 0x00E0:
                self.screen.clear()
                return

            # 00EE - ret
            case 0x00EE:
                sp = self.rg_sp.read() - 1
                return_address = self.stack[sp]
                self.rg_pc.write(return_address)
                self.rg_sp.write(sp)
                return

            case _:
                pass

        match opcode & 0xF000:
            # 0NNN - サポートしない
            # case 0x0000:
            #     return

            # 1NNN - jump addr
            case 0x1000:
                address = _decode_nnn(opcode)
                self.rg_pc.write(address)
                return

            # 2NNN - call addr
            case 0x2000:
                subroutine_address = _decode_nnn(opcode)
                pc_address = self.rg_pc.read()
                sp = self.rg_sp.read()
                self.stack[sp] = pc_address
                self.rg_sp.write(sp + 1)
                self.rg_pc.write(subroutine_address)
                return

            # 3XNN - if vx == nn then skip next instruction else continue
            case 0x3000:
                x, nn = _decode_x_nn(opcode)
                if self.rg_vs[x].read() == nn:
                    self.rg_pc.write(self.rg_pc.read() + 2)
                return

            # 4XNN - if vx != nn then skip next instruction else continue
            case 0x4000:
                x, nn = _decode_x_nn(opcode)
                if self.rg_vs[x].read() != nn:
                    self.rg_pc.write(self.rg_pc.read() + 2)
                return

            # 6XNN - vx := NN
            case 0x6000:
                x, nn = _decode_x_nn(opcode)
                self.rg_vs[x].write(nn)
                return

            # 7XNN - vx += NN
            case 0x7000:
                x, nn = _decode_x_nn(opcode)
                x_value = self.rg_vs[x].read()
                self.rg_vs[x].write(x_value + nn)
                return

            # ANNN - i := NNN
            case 0xA000:
                address = _decode_nnn(opcode)
                self.rg_i.write(address)
                return

            # BNNN - jump to address v0 + NNN
            case 0xB000:
                nnn = _decode_nnn(opcode)
                v0 = self.rg_vs[0].read()
                address = v0 + nnn
                self.rg_pc.write(address)
                return

            # CXNN - vx := random & NN
            case 0xC000:
                x, nn = _decode_x_nn(opcode)
                value = random.randint(0, 255) & nn
                self.rg_vs[x].write(value)
                return

            # DXYN - draw sprite on screen
            # スプライトは幅8bit高さN
            case 0xD000:
                x, y, n = _decode_x_y_n(opcode)
                address = self.rg_i.read()
                _bytes = [self.memory.read(i) for i in range(address, address + n)]
                x_value = self.rg_vs[x].read()
                y_value = self.rg_vs[y].read()
                sprite = screen.bytes_to_sprite(_bytes)
                collision_flag = self.screen.draw_sprite(Point(x_value, y_value), sprite)
                self.rg_vs[0xF].write(collision_flag)
                return

            case _:
                pass

        match opcode & 0xF00F:
            # 5XY0 - if vx == vy then skip next instruction else continue
            case 0x5000:
                x, y = _decode_x_y(opcode)
                if self.rg_vs[x].read() == self.rg_vs[y].read():
                    self.rg_pc.write(self.rg_pc.read() + 2)
                return

            # 8XY0 - vx := vy
            case 0x8000:
                x, y = _decode_x_y(opcode)
                y_value = self.rg_vs[y].read()
                self.rg_vs[x].write(y_value)
                return

            # 8XY1 - vx |= vy
            case 0x8001:
                x, y = _decode_x_y(opcode)
                x_value = self.rg_vs[x].read()
                y_value = self.rg_vs[y].read()
                self.rg_vs[x].write(x_value | y_value)
                return

            # 8XY2 - vx &= vy
            case 0x8002:
                x, y = _decode_x_y(opcode)
                x_value = self.rg_vs[x].read()
                y_value = self.rg_vs[y].read()
                self.rg_vs[x].write(x_value & y_value)
                return

            # 8XY3 - vx ^= vy
            case 0x8003:
                x, y = _decode_x_y(opcode)
                x_value = self.rg_vs[x].read()
                y_value = self.rg_vs[y].read()
                self.rg_vs[x].write(x_value ^ y_value)
                return

            # 8XY4 - vx += vy, vf = 1 on carry
            case 0x8004:
                x, y = _decode_x_y(opcode)
                x_value = self.rg_vs[x].read()
                y_value = self.rg_vs[y].read()

                result = x_value + y_value
                carry = 1 if (result & 0x100) == 0x100 else 0
                self.rg_vs[x].write(result & 0xFF)
                self.rg_vs[0xF].write(carry)
                return

            # 8XY5 - vx -= vy, if vx > vy then vf = 1 else vf = 0
            # vf は carry フラグと考えると加算のときと合う
            case 0x8005:
                x, y = _decode_x_y(opcode)
                x_value = self.rg_vs[x].read()
                y_value = self.rg_vs[y].read()

                # 2の補数表現を使って vx - yv を計算
                # python のビット反転は -(x + 1) と同じ
                # https://docs.python.org/ja/3/reference/expressions.html#unary-arithmetic-and-bitwise-operations
                result = x_value + (~y_value & 0xFF) + 1
                carry = 1 if (result & 0x100) == 0x100 else 0
                self.rg_vs[x].write(result & 0xFF)
                self.rg_vs[0xF].write(carry)
                return

            # 8XY6 - vx >>= 1, vf には vx の最下位ビットを格納
            case 0x8006:
                x, _ = _decode_x_y(opcode)
                x_value = self.rg_vs[x].read()

                vf_value = x_value & 0x01
                result = x_value >> 1
                self.rg_vs[x].write(result & 0xFF)
                self.rg_vs[0xF].write(vf_value)
                return

            # 8XY7 - vx := vy - vx, if vy > vx then vf = 1 else vf = 0
            case 0x8007:
                x, y = _decode_x_y(opcode)
                x_value = self.rg_vs[x].read()
                y_value = self.rg_vs[y].read()

                # 2の補数表現を使って vy - yx を計算
                # python のビット反転は -(x + 1) と同じ
                # https://docs.python.org/ja/3/reference/expressions.html#unary-arithmetic-and-bitwise-operations
                result = y_value + (~x_value & 0xFF) + 1
                carry = 1 if (result & 0x100) == 0x100 else 0
                self.rg_vs[x].write(result & 0xFF)
                self.rg_vs[0xF].write(carry)
                return

            # 8XYE - vx <<= 1, vf には vx の最上位ビットを格納
            case 0x800E:
                x, _ = _decode_x_y(opcode)
                x_value = self.rg_vs[x].read()

                vf_value = (x_value & 0x80) >> 7
                result = x_value << 1
                self.rg_vs[x].write(result & 0xFF)
                self.rg_vs[0xF].write(vf_value)
                return

            # 9XY0 - if vx != vy then skip next instruction else continue
            case 0x9000:
                x, y = _decode_x_y(opcode)
                if self.rg_vs[x].read() != self.rg_vs[y].read():
                    self.rg_pc.write(self.rg_pc.read() + 2)
                return

            case _:
                pass

        match opcode & 0xF0FF:
            # EX9E - skp vx
            case 0xE09E:
                x, _ = _decode_x_nn(opcode)
                x_value = self.rg_vs[x].read()
                match _get_key_value(pressed_key):
                    case key_value if key_value == x_value:
                        self.rg_pc.write(self.rg_pc.read() + 2)
                    case _:
                        return

            # EXA1 - sknp vx
            case 0xE0A1:
                x, _ = _decode_x_nn(opcode)
                x_value = self.rg_vs[x].read()
                match _get_key_value(pressed_key):
                    case key_value if key_value != x_value:
                        self.rg_pc.write(self.rg_pc.read() + 2)
                    case _:
                        return

            # FX07 - vx := dt
            case 0xF007:
                x, _ = _decode_x_nn(opcode)
                dt_value = self.rg_dt.read()
                self.rg_vs[x].write(dt_value)
                return

            # FX0A - load key to vx
            case 0xF00A:
                x, _ = _decode_x_nn(opcode)
                self.state = CPUState.WAITING
                self.prev_decoded_x = x
                return

            # FX15 - dt := vx
            case 0xF015:
                x, _ = _decode_x_nn(opcode)
                x_value = self.rg_vs[x].read()
                self.rg_dt.write(x_value)
                return

            # FX18 - st := vx
            case 0xF018:
                x, _ = _decode_x_nn(opcode)
                x_value = self.rg_vs[x].read()
                self.rg_st.write(x_value)
                return

            # FX1E - i += vx
            case 0xF01E:
                x, _ = _decode_x_nn(opcode)
                x_value = self.rg_vs[x].read()
                i_value = self.rg_i.read()
                self.rg_i.write(i_value + x_value)
                return

            # FX29 - load font address from vx
            # vx に格納されている16進数の値を i に格納する
            case 0xF029:
                x, _ = _decode_x_nn(opcode)
                x_value = self.rg_vs[x].read()
                # NOTE: font は1文字5バイトで順番に格納されているので、vxの値を5倍にする
                address = FONT_START_ADDRESS + (x_value & 0xF) * 5
                self.rg_i.write(address)
                return

            # FX33 - bcd vx
            case 0xF033:
                x, _ = _decode_x_nn(opcode)
                x_value = self.rg_vs[x].read()
                address = self.rg_i.read()
                hundreds, tens, ones = x_value // 100, (x_value // 10) % 10, x_value % 10
                self.memory.write(address, hundreds)
                self.memory.write(address + 1, tens)
                self.memory.write(address + 2, ones)
                return

            # FX55 - save vx
            case 0xF055:
                target, _ = _decode_x_nn(opcode)
                address = self.rg_i.read()
                for i in range(0, target + 1):
                    rg_x_value = self.rg_vs[i].read()
                    self.memory.write(address + i, rg_x_value)
                return

            # FX65 - load vx
            case 0xF065:
                target, _ = _decode_x_nn(opcode)
                address = self.rg_i.read()
                for i in range(0, target + 1):
                    value = self.memory.read(address + i)
                    self.rg_vs[i].write(value)
                return

            case _:
                pass


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
