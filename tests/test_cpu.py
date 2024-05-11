from chip8.cpu import DEFAULT_PC_ADDRESS, Chip8CPU
from chip8.memory import Memory


def create_test_memory(data_list: list[int], start_address: int = DEFAULT_PC_ADDRESS) -> Memory:
    """
    アドレスの 0x0000 から data を書き込んだ Memory を返す。

    Args:
        data_list (list[int]): 8bitのデータのリスト

    Returns:
        Memory: data を書き込んだ Memory
    """
    memory = Memory()
    address = start_address
    for data in data_list:
        memory.write(address, data)
        address += 1

    return memory


def test_6XNN():
    test_data = [0x60, 0x01]
    memory = create_test_memory(test_data)
    cpu = Chip8CPU(memory)

    # 初期状態の確認
    assert cpu.rg_vs[0].read() == 0x00
    cpu.execute_instruction()
    assert cpu.rg_vs[0].read() == 0x01
