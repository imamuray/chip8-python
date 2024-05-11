MAX_SIZE = 4096


class Memory:
    def __init__(self) -> None:
        self.memory = bytearray(MAX_SIZE)

    def read(self, address: int) -> int:
        return self.memory[address]

    def write(self, address: int, value: int) -> None:
        self.memory[address] = 0xFF & value
