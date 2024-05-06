import json
from collections import namedtuple
from typing import List, Dict
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

    def __str__(self) -> str:
        return str(self.value)


def int_to_bytes(integer: int) -> bytearray:
    res = []
    # Машинное слово 4 байта
    for _ in range(4):
        res.append(integer & 0xFF)
        integer = integer >> 8

    return bytearray(res)


def bytes_to_int(byte_arr: bytes) -> int:
    return (byte_arr[3] << 24) + (byte_arr[2] << 16) + (byte_arr[1] << 8) + byte_arr[0]


def write_code(filename, code):
    """Записать машинный код в файл."""
    with open(filename, "wb") as file:
        int_codes: List[int] = [(int(instr["opcode"]) << 24) + int(instr["arg"]) if "arg" in instr
                                else (int(instr["opcode"]) << 24) for instr in code]
        for x in int_codes:
            file.write(int_to_bytes(x))


def write_data(filename, data: Dict[str, List[int]]):
    with open(filename, "wb") as file:
        for arr in data.values():
            for x in arr:
                file.write(int_to_bytes(x))


def read_data(filename) -> List[int]:
    res = []
    with open(filename, "rb") as file:
        byte_content = file.read()
        ind = 0
        while ind < len(byte_content) / 4:
            res.append(bytes_to_int(byte_content[ind:ind + 4]))
            ind += 4
    return res


def read_code(filename) -> List[Dict[str, int]]:
    arr_int = read_data(filename)
    res = []
    for num, x in enumerate(arr_int):
        opcode = (x & (0xFF << 24)) >> 24
        arg = x & 0x00FFFFFF
        res.append({"index": num, "opcode": opcode, "arg": arg})
    return res