from collections.abc import Callable

from memory import Memory
from register import Register8, Register16

DEFAULT_PC_ADDRESS = 0x200


def _decode_x_y(opcode: int) -> tuple[int, int]:
    x = (opcode & 0x0F00) >> 8
    y = (opcode & 0x00F0) >> 4
    return (x, y)


def _decode_x_nn(opcode: int) -> tuple[int, int]:
    x = (opcode & 0x0F00) >> 8
    nn = opcode & 0x00FF
    return (x, nn)


def _decode_nnn(opcode: int) -> int:
    return opcode & 0x0FFF


# TODO: 各種命令に対応する関数名はあとでわかりやすいものに変える
class Chip8CPU:
    def __init__(self, memory: Memory) -> None:
        self.memory = memory
        self.stack = [0] * 16

        self.rg_vs = [Register8() for _ in range(16)]
        self.rg_i = Register16()
        self.rg_pc = Register16(DEFAULT_PC_ADDRESS)
        self.rg_sp = Register8()
        self.rg_dt = Register8()
        self.rg_st = Register8()

        self.op_table: dict[int, Callable] = {}

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

    def execute_instruction(self) -> None:
        opcode = self._get_opcode()
        print(f"[DEBUG] opecode: {opcode:04x}")

        match opcode:
            case 0x00E0:
                # TODO
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

            # ANNN
            case 0xA000:
                # TODO
                return

            # BNNN
            case 0xB000:
                # TODO
                return

            # CXNN
            case 0xC000:
                # TODO
                return

            # DXYN
            case 0xD000:
                # TODO
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
            # EX9E
            case 0xE09E:
                # TODO
                return

            # EXA1
            case 0xE0A1:
                # TODO
                return

            # FX07
            case 0xF007:
                # TODO
                return

            # FX0A
            case 0xF00A:
                # TODO
                return

            # FX15
            case 0xF015:
                # TODO
                return

            # FX18
            case 0xF018:
                # TODO
                return

            # FX1E
            case 0xF01E:
                # TODO
                return

            # FX29
            case 0xF029:
                # TODO
                return

            # FX33
            case 0xF033:
                # TODO
                return

            # FX55
            case 0xF055:
                # TODO
                return

            # FX65
            case 0xF065:
                # TODO
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
    memory = Memory()
    instructions = [
        0x2206,
        0x6101,
        0x8014,
        0x60FF,
        0x00EE,
    ]
    next_address = DEFAULT_PC_ADDRESS
    for code in instructions:
        next_address = write_instruction(memory, next_address, code)

    cpu = Chip8CPU(memory)
    print(cpu)
    for _ in range(len(instructions)):
        cpu.execute_instruction()
        print(cpu)
