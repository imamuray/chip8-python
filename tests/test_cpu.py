import pytest

from chip8.cpu import DEFAULT_PC_ADDRESS, Chip8CPU
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


@pytest.mark.parametrize("registor,value", [(0x0, 0x10), (0xF, 0x10)])
def test_6XNN(registor: int, value: int):
    # 6XNN - vx := NN
    test_data = [0x60 | registor, value]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)
    cpu.rg_vs[registor].write(0x00)

    cpu.execute_instruction()
    assert cpu.rg_vs[registor].read() == value


@pytest.mark.parametrize("x,y,x_value,y_value", [(0x0, 0xF, 0x11, 0x22), (0xF, 0x0, 0x11, 0x22)])
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


@pytest.mark.parametrize("x,y,x_value,y_value,expect", [(0x0, 0xF, 0x11, 0xEE, 0xFF), (0xF, 0x0, 0x11, 0xEE, 0xFF)])
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


@pytest.mark.parametrize("x,y,x_value,y_value,expect", [(0x0, 0xF, 0x0F, 0xF1, 0x01), (0xF, 0x0, 0x0F, 0xF1, 0x01)])
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


@pytest.mark.parametrize("x,y,x_value,y_value,expect", [(0x0, 0xF, 0x0F, 0xFF, 0xF0), (0xF, 0x0, 0x0F, 0xFF, 0xF0)])
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
