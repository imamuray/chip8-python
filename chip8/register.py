from abc import ABC, abstractmethod


class Register(ABC):
    @abstractmethod
    def read(self) -> int:
        pass

    @abstractmethod
    def write(self, value: int) -> None:
        pass


class Register8(Register):
    def __init__(self, value: int = 0) -> None:
        self.value = value

    def __str__(self) -> str:
        return f"0x{self.value:02x}"

    def read(self) -> int:
        return self.value

    def write(self, value: int) -> None:
        self.value = 0xFF & value


class Register16(Register):
    def __init__(self, value: int = 0) -> None:
        self.value = value

    def __str__(self) -> str:
        return f"0x{self.value:04x}"

    def read(self) -> int:
        return self.value

    def write(self, value: int) -> None:
        self.value = 0xFFFF & value
