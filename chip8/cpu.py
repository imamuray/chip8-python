from collections.abc import Callable

from memory import Memory
from register import Register8, Register16

DEFAULT_PC_ADDRESS = 0x200


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
                f"stack: {self.stack}",
            ]
        )

    def get_opcode(self) -> int:
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
        opcode = self.get_opcode()
        # TODO: とりあえず 8xxx 系の命令を作ってみる
        print(f"[DEBUG] opecode: {opcode:04x}")

        # NOTE: 8XYn としたときの X, Y
        opcode_x = (opcode & 0x0F00) >> 8
        opcode_y = (opcode & 0x00F0) >> 4
        opcode_nn = opcode & 0x00FF

        match opcode & 0xF000:
            case 0x6000:
                self.rg_vs[opcode_x].write(opcode_nn)
                return
            case _:
                pass

        match opcode & 0xF00F:
            # vx := vy
            case 0x8000:
                y = self.rg_vs[opcode_y].read()
                self.rg_vs[opcode_x].write(y)
                return
            # vx: |= yv
            case 0x8001:
                x = self.rg_vs[opcode_x].read()
                y = self.rg_vs[opcode_y].read()
                self.rg_vs[opcode_x].write(x | y)
                return
            # vx: &= yv
            case 0x8002:
                x = self.rg_vs[opcode_x].read()
                y = self.rg_vs[opcode_y].read()
                self.rg_vs[opcode_x].write(x & y)
                return
            # vx: ^= yv
            case 0x8003:
                x = self.rg_vs[opcode_x].read()
                y = self.rg_vs[opcode_y].read()
                self.rg_vs[opcode_x].write(x ^ y)
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
    instructions = [0x6001, 0x6102, 0x6203, 0x6F0F, 0x83F0, 0x8411, 0x8242, 0x6E07, 0x81E3]
    next_address = DEFAULT_PC_ADDRESS
    for code in instructions:
        next_address = write_instruction(memory, next_address, code)

    cpu = Chip8CPU(memory)
    print(cpu)
    for _ in range(len(instructions)):
        cpu.execute_instruction()
    print(cpu)
