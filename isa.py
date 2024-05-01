import json
from collections import namedtuple
from enum import Enum


class Opcode(int, Enum):
    PUSH = 0x00
    POP = 0x01

    JMP = 0x02
    JZ = 0x03
    JNZ = 0x04
    JS = 0x05
    JNS = 0x06

    CALL = 0x07
    RET = 0x08

    INPUT = 0x09
    OUTPUT = 0x0A

    INC = 0x0B
    DEC = 0x0C
    ADD = 0x0D
    SUB = 0x0E
    MUL = 0x0F
    DIV = 0x10

    LOAD = 0x11
    STORE = 0x12
    SWAP = 0x13

    HLT = 0x14

    def __str__(self) -> int:
        return int(self.value)


def write_code(filename, code):
    """Записать машинный код в файл."""
    with open(filename, "w", encoding="utf-8") as file:
        # Почему не: `file.write(json.dumps(code, indent=4))`?
        # Чтобы одна инструкция была на одну строку.
        buf = []
        for instr in code:
            buf.append(json.dumps(instr))
        file.write("[" + ",\n ".join(buf) + "]")


def read_code(filename):
    """Прочесть машинный код из файла.

    Так как в файле хранятся не только простейшие типы (`Opcode`, `Term`), мы
    также выполняем конвертацию в объекты классов вручную (возможно, следует
    переписать через `JSONDecoder`, но это скорее усложнит код).

    """
    with open(filename, encoding="utf-8") as file:
        code = json.loads(file.read())

    for instr in code:
        # Конвертация строки в Opcode
        instr["opcode"] = Opcode(instr["opcode"])

        # Конвертация списка term в класс Term
        if "term" in instr:
            assert len(instr["term"]) == 3
            instr["term"] = Term(instr["term"][0], instr["term"][1], instr["term"][2])

    return code
