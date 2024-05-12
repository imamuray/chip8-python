import pytest

from chip8.cpu import DEFAULT_PC_ADDRESS, FONT_START_ADDRESS, Chip8CPU
from chip8.memory import Memory


def create_test_memory(data_list: list[int], start_address: int = DEFAULT_PC_ADDRESS) -> Memory:
    """
    アドレスの 0x0000 から data を書き込んだ Memory を返す。

    Args:
        data_list (list[int]): 8bitのデータのリスト
        start_address (int, optional): 書き込み開始アドレス. デフォルトは cpu.DEFAULT_PC_ADDRESS.

    Returns:
        Memory: data を書き込んだ Memory
    """
    memory = Memory()
    address = start_address
    for data in data_list:
        memory.write(address, data)
        address += 1

    return memory


def test_00EE():
    # 00EE - ret
    test_data = [0x00, 0xEE]
    start_address = 0x300
    memory = create_test_memory(test_data, start_address)
    cpu = Chip8CPU(memory)
    cpu.rg_pc.write(start_address)
    prev_sp = 1
    cpu.rg_sp.write(prev_sp)
    return_address = 0x222
    cpu.stack[prev_sp - 1] = return_address

    cpu.execute_instruction()
    assert cpu.rg_pc.read() == return_address
    assert cpu.rg_sp.read() == prev_sp - 1


def test_1NNN():
    # 1NNN - jump NNN
    test_data = [0x13, 0x33]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)

    cpu.execute_instruction()
    assert cpu.rg_pc.read() == 0x333


def test_2NNN():
    # 2NNN - call addr
    test_data = [0x23, 0x33]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    prev_pc = cpu.rg_pc.read()
    prev_sp = cpu.rg_sp.read()

    cpu.execute_instruction()
    assert cpu.rg_pc.read() == 0x333
    assert cpu.rg_sp.read() == prev_sp + 1
    # 1命令実行につきpcは2増える
    assert cpu.stack[prev_sp] == prev_pc + 2


@pytest.mark.parametrize(
    "x,op_value,x_value,start_address,expect",
    [
        (0x0, 0x10, 0x10, 0x200, 0x204),
        (0x0, 0x11, 0x10, 0x200, 0x202),
    ],
)
def test_3XNN(x: int, op_value: int, x_value: int, start_address: int, expect: int):
    # 3XNN - if vx == nn then skip next instruction else continue
    test_data = [0x30 | x, op_value]
    memory = create_test_memory(test_data, start_address)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[x].write(x_value)
    cpu.rg_pc.write(start_address)

    cpu.execute_instruction()
    assert cpu.rg_pc.read() == expect


@pytest.mark.parametrize(
    "x,op_value,x_value,start_address,expect",
    [
        (0x0, 0x10, 0x10, 0x200, 0x202),
        (0x0, 0x11, 0x10, 0x200, 0x204),
    ],
)
def test_4XNN(x: int, op_value: int, x_value: int, start_address: int, expect: int):
    # 4XNN - if vx != nn then skip next instruction else continue
    test_data = [0x40 | x, op_value]
    memory = create_test_memory(test_data, start_address)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[x].write(x_value)
    cpu.rg_pc.write(start_address)

    cpu.execute_instruction()
    assert cpu.rg_pc.read() == expect


@pytest.mark.parametrize(
    "x,y,x_value,y_value,start_address,expect",
    [
        (0x0, 0x1, 0x10, 0x10, 0x200, 0x204),
        (0x0, 0x1, 0x10, 0x11, 0x200, 0x202),
    ],
)
def test_5XY0(x: int, y: int, x_value: int, y_value: int, start_address: int, expect: int):
    # 5XY0 - if vx == vy then skip next instruction else continue
    test_data = [0x50 | x, 0x00 | (y << 4)]
    memory = create_test_memory(test_data, start_address)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[x].write(x_value)
    cpu.rg_vs[y].write(y_value)
    cpu.rg_pc.write(start_address)

    cpu.execute_instruction()
    assert cpu.rg_pc.read() == expect


@pytest.mark.parametrize(
    "registor,value",
    [
        (0x0, 0x10),
        (0xF, 0x10),
    ],
)
def test_6XNN(registor: int, value: int):
    # 6XNN - vx := NN
    test_data = [0x60 | registor, value]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[registor].write(0x00)

    cpu.execute_instruction()
    assert cpu.rg_vs[registor].read() == value


@pytest.mark.parametrize(
    "x,op_value,x_value,expect",
    [
        (0x0, 0x01, 0x02, 0x03),
        (0x0, 0xFF, 0x02, 0x01),
    ],
)
def test_7XNN(x: int, op_value: int, x_value: int, expect: int):
    # 7XNN - vx += NN
    test_data = [0x70 | x, op_value]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[x].write(x_value)

    cpu.execute_instruction()
    assert cpu.rg_vs[x].read() == expect


@pytest.mark.parametrize(
    "x,y,x_value,y_value",
    [
        (0x0, 0xF, 0x11, 0x22),
        (0xF, 0x0, 0x11, 0x22),
    ],
)
def test_8XY0(x: int, y: int, x_value: int, y_value: int):
    # 8XY0 - vx := vy
    test_data = [0x80 | x, 0x00 | (y << 4)]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[x].write(x_value)
    cpu.rg_vs[y].write(y_value)

    cpu.execute_instruction()
    assert cpu.rg_vs[x].read() == y_value
    assert cpu.rg_vs[y].read() == y_value


@pytest.mark.parametrize(
    "x,y,x_value,y_value,expect",
    [
        (0x0, 0xF, 0x11, 0xEE, 0xFF),
        (0xF, 0x0, 0x11, 0xEE, 0xFF),
    ],
)
def test_8XY1(x: int, y: int, x_value: int, y_value: int, expect: int):
    # 8XY1 - vx |= vy
    test_data = [0x80 | x, 0x01 | (y << 4)]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[x].write(x_value)
    cpu.rg_vs[y].write(y_value)

    cpu.execute_instruction()
    assert cpu.rg_vs[x].read() == expect
    assert cpu.rg_vs[y].read() == y_value


@pytest.mark.parametrize(
    "x,y,x_value,y_value,expect",
    [
        (0x0, 0xF, 0x0F, 0xF1, 0x01),
        (0xF, 0x0, 0x0F, 0xF1, 0x01),
    ],
)
def test_8XY2(x: int, y: int, x_value: int, y_value: int, expect: int):
    # 8XY2 - vx &= vy
    test_data = [0x80 | x, 0x02 | (y << 4)]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[x].write(x_value)
    cpu.rg_vs[y].write(y_value)

    cpu.execute_instruction()
    assert cpu.rg_vs[x].read() == expect
    assert cpu.rg_vs[y].read() == y_value


@pytest.mark.parametrize(
    "x,y,x_value,y_value,expect",
    [
        (0x0, 0xF, 0x0F, 0xFF, 0xF0),
        (0xF, 0x0, 0x0F, 0xFF, 0xF0),
    ],
)
def test_8XY3(x: int, y: int, x_value: int, y_value: int, expect: int):
    # 8XY3 - vx ^= vy
    test_data = [0x80 | x, 0x03 | (y << 4)]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[x].write(x_value)
    cpu.rg_vs[y].write(y_value)

    cpu.execute_instruction()
    assert cpu.rg_vs[x].read() == expect
    assert cpu.rg_vs[y].read() == y_value


@pytest.mark.parametrize(
    "x,y,x_value,y_value,expect_x,expect_f",
    [
        (0x0, 0x1, 0x01, 0x02, 0x03, 0x00),
        (0x0, 0x1, 0xFF, 0x01, 0x00, 0x01),
    ],
)
def test_8XY4(x: int, y: int, x_value: int, y_value: int, expect_x: int, expect_f):
    # 8XY4 - vx += vy, vf = 1 on carry
    test_data = [0x80 | x, 0x04 | (y << 4)]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[x].write(x_value)
    cpu.rg_vs[y].write(y_value)
    cpu.rg_vs[0xF].write(0x00)

    cpu.execute_instruction()
    assert cpu.rg_vs[x].read() == expect_x
    assert cpu.rg_vs[y].read() == y_value
    assert cpu.rg_vs[0xF].read() == expect_f


@pytest.mark.parametrize(
    "x,y,x_value,y_value,expect_x,expect_f",
    [
        (0x0, 0x1, 0x03, 0x01, 0x02, 0x01),
        (0x0, 0x1, 0x00, 0x01, 0xFF, 0x00),
    ],
)
def test_8XY5(x: int, y: int, x_value: int, y_value: int, expect_x: int, expect_f):
    # 8XY5 - vx -= vy, if vx > vy then vf = 1 else vf = 0
    test_data = [0x80 | x, 0x05 | (y << 4)]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[x].write(x_value)
    cpu.rg_vs[y].write(y_value)
    cpu.rg_vs[0xF].write(0x00)

    cpu.execute_instruction()
    assert cpu.rg_vs[x].read() == expect_x
    assert cpu.rg_vs[y].read() == y_value
    assert cpu.rg_vs[0xF].read() == expect_f


@pytest.mark.parametrize(
    "x,y,x_value,expect_x,expect_f",
    [
        (0x0, 0x1, 0x04, 0x02, 0x00),
        (0x0, 0x1, 0x05, 0x02, 0x01),
    ],
)
def test_8XY6(x: int, y: int, x_value: int, expect_x: int, expect_f):
    # 8XY6 - vx >>= 1, vf には vx の最下位ビットを格納
    test_data = [0x80 | x, 0x06 | (y << 4)]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[x].write(x_value)
    cpu.rg_vs[0xF].write(0x00)

    cpu.execute_instruction()
    assert cpu.rg_vs[x].read() == expect_x
    assert cpu.rg_vs[0xF].read() == expect_f


@pytest.mark.parametrize(
    "x,y,x_value,y_value,expect_x,expect_f",
    [
        (0x0, 0x1, 0x01, 0x03, 0x02, 0x01),
        (0x0, 0x1, 0x01, 0x00, 0xFF, 0x00),
    ],
)
def test_8XY7(x: int, y: int, x_value: int, y_value: int, expect_x: int, expect_f):
    # 8XY7 - vx := vy - vx, if vy > vx then vf = 1 else vf = 0
    test_data = [0x80 | x, 0x07 | (y << 4)]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[x].write(x_value)
    cpu.rg_vs[y].write(y_value)
    cpu.rg_vs[0xF].write(0x00)

    cpu.execute_instruction()
    assert cpu.rg_vs[x].read() == expect_x
    assert cpu.rg_vs[y].read() == y_value
    assert cpu.rg_vs[0xF].read() == expect_f


@pytest.mark.parametrize(
    "x,y,x_value,expect_x,expect_f",
    [
        (0x0, 0x1, 0x40, 0x80, 0x00),
        (0x0, 0x1, 0xC0, 0x80, 0x01),
    ],
)
def test_8XYE(x: int, y: int, x_value: int, expect_x: int, expect_f):
    # 8XYE - vx <<= 1, vf には vx の最上位ビットを格納
    test_data = [0x80 | x, 0x0E | (y << 4)]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[x].write(x_value)
    cpu.rg_vs[0xF].write(0x00)

    cpu.execute_instruction()
    assert cpu.rg_vs[x].read() == expect_x
    assert cpu.rg_vs[0xF].read() == expect_f


@pytest.mark.parametrize(
    "x,y,x_value,y_value,start_address,expect",
    [
        (0x0, 0x1, 0x10, 0x10, 0x200, 0x202),
        (0x0, 0x1, 0x10, 0x11, 0x200, 0x204),
    ],
)
def test_9XY0(x: int, y: int, x_value: int, y_value: int, start_address: int, expect: int):
    # 9XY0 - if vx != vy then skip next instruction else continue
    test_data = [0x90 | x, 0x00 | (y << 4)]
    memory = create_test_memory(test_data, start_address)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[x].write(x_value)
    cpu.rg_vs[y].write(y_value)
    cpu.rg_pc.write(start_address)

    cpu.execute_instruction()
    assert cpu.rg_pc.read() == expect


def test_ANNN():
    # ANNN - i := NNN
    test_data = [0xA3, 0x33]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    cpu.rg_i.write(0x00)

    cpu.execute_instruction()
    assert cpu.rg_i.read() == 0x333


def test_BNNN():
    # BNNN - jump to address v0 + NNN
    test_data = [0xB3, 0x00]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[0].write(0x33)

    cpu.execute_instruction()
    assert cpu.rg_pc.read() == 0x333


@pytest.mark.parametrize("times", range(10))
def test_CXNN(times):
    # CXNN - vx := random & NN
    test_data = [0xC0, 0x0F]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[0].write(0x00)

    cpu.execute_instruction()
    assert cpu.rg_vs[0].read() in range(0, 0x10)


def test_FX07():
    # FX07 - vx := dt
    test_data = [0xF0, 0x07]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    expect = 0x11
    cpu.rg_dt.write(expect)
    cpu.rg_vs[0].write(0x00)

    cpu.execute_instruction()
    assert cpu.rg_vs[0].read() == expect


def test_FX15():
    # FX15 - dt := vx
    test_data = [0xF0, 0x15]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    expect = 0x11
    cpu.rg_vs[0].write(expect)
    cpu.rg_dt.write(0x00)

    cpu.execute_instruction()
    assert cpu.rg_dt.read() == expect


def test_FX18():
    # FX18 - st := vx
    test_data = [0xF0, 0x18]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    expect = 0x11
    cpu.rg_vs[0].write(expect)
    cpu.rg_st.write(0x00)

    cpu.execute_instruction()
    assert cpu.rg_st.read() == expect


def test_FX1E():
    # FX1E - i += vx
    test_data = [0xF0, 0x1E]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[0].write(0x01)
    cpu.rg_i.write(0x02)

    cpu.execute_instruction()
    assert cpu.rg_i.read() == 0x03


def test_FX29():
    # FX29 - load font address from vx
    test_data = [0xF0, 0x29]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[0].write(0x2)
    cpu.rg_i.write(0x0000)
    expect = FONT_START_ADDRESS + 0x2 * 5

    cpu.execute_instruction()
    assert cpu.rg_i.read() == expect


def test_FX33():
    # FX33 - bcd vx
    test_data = [0xF0, 0x33]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[0].write(128)
    cpu.rg_i.write(0x300)

    cpu.execute_instruction()
    assert cpu.memory.read(0x300) == 1
    assert cpu.memory.read(0x301) == 2
    assert cpu.memory.read(0x302) == 8


def test_FX55():
    # FX55 - save vx
    test_data = [0xF2, 0x55]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    address = 0x300
    cpu.rg_i.write(address)
    cpu.rg_vs[0].write(0x11)
    cpu.rg_vs[1].write(0x22)
    cpu.rg_vs[2].write(0x33)

    cpu.execute_instruction()
    assert cpu.memory.read(address) == 0x11
    assert cpu.memory.read(address + 1) == 0x22
    assert cpu.memory.read(address + 2) == 0x33


def test_FX65():
    # FX65 - load vx
    test_data = [0xF2, 0x65]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    address = 0x300
    cpu.rg_i.write(address)
    cpu.memory.write(address, 0x11)
    cpu.memory.write(address + 1, 0x22)
    cpu.memory.write(address + 2, 0x33)

    cpu.execute_instruction()
    assert cpu.rg_vs[0].read() == 0x11
    assert cpu.rg_vs[1].read() == 0x22
    assert cpu.rg_vs[2].read() == 0x33


def test_call_and_ret():
    # test_data
    # 0x200: 2206: call 0x206
    # 0x202: 0000: nop
    # 0x204: 0000: nop
    # 0x206: 00EE: ret
    test_data = [0x22, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0xEE]
    start_address = 0x200
    memory = create_test_memory(test_data, start_address)
    cpu = Chip8CPU(memory)
    cpu.rg_pc.write(start_address)

    cpu.execute_instruction()  # call
    cpu.execute_instruction()  # ret
    assert cpu.rg_pc.read() == 0x202
