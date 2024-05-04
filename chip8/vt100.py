ESCAPE = "\x1b"


def clear_screen() -> str:
    return f"{ESCAPE}[2J"


def return_cursor_to_home() -> str:
    return f"{ESCAPE}[H"
