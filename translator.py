#!/usr/bin/python3
"""Транслятор Asm в машинный код.
"""
from __future__ import annotations

import sys
from itertools import chain

from isa import Opcode, write_code, write_data


def find_substring_row(text: list[str], substr) -> int:
    num_str_decl_section: int = -1

    for index, line in enumerate(text):
        if substr in line:
            assert num_str_decl_section == -1, "Section .data can be declared at most once"
            num_str_decl_section = index

    return num_str_decl_section


def remove(s: str, indexes: list[int]) -> str:
    new_s: str = ""
    for ind, x in enumerate(s):
        if ind not in indexes:
            new_s += x
    return new_s


def remove_double_comma(s: str) -> str:
    new_s = ""
    last_is_comma: bool = False
    for x in s:
        if x == "," and not last_is_comma:
            new_s += x
            last_is_comma = True
        elif x != ",":
            new_s += x
            last_is_comma = False
    return new_s


def make_reservation(data):
    for i in range(len(data)):
        if "res" in data[i]:
            cnt = int(data[i].replace("res", ""))
            data[i] = [0] * cnt
    return data


def get_integers(data: str, ind_chars_in_quotes: list[int]):
    int_data = remove(data, ind_chars_in_quotes)
    # Могут появиться после удаления две запятые подряд - их надо почистить
    int_data = remove_double_comma(int_data)
    # Удаление комментариев
    int_data = int_data.split(";")[0].strip()
    # все res x заменить на x нулей
    int_data = make_reservation(int_data.split(","))
    int_data = list(filter(lambda s: s != " " and s != "", int_data))
    int_data = [x if isinstance(x, list) else int(x) for x in int_data]
    for x in int_data:
        if not isinstance(x, list):
            assert -(1 << 23) <= x <= (1 << 23) - 1, "Integer must take values in the segment [-2^23; 2^23 - 1]"
    return int_data


def str2list_int(data: str) -> (list[list[int] | int], list[int]):
    in_quotes: bool = False
    # Массив, в котором хранятся индексы элементов, взятых в кавычки (включая кавычки)
    # Нужен, чтобы после первого прохода по данным в метке, очистить данные от строк
    ind_chars_in_quotes: list[int] = [[]]
    # Массив, в котором элемент является List[int] длины строки,
    # если в исходном тексте на этом месте была строка (каждый int это код элемента в ASCII),
    # или длины 1, если в исходном тексте это было просто число
    list_codes: list[list[int]] = [[]]
    for index, x in enumerate(data):
        if x == '"':
            in_quotes = not in_quotes
            ind_chars_in_quotes.append(index)
        elif in_quotes:
            list_codes[-1].append(ord(x))
            ind_chars_in_quotes.append(index)
        elif x == ",":
            list_codes.append([])

    return list_codes, ind_chars_in_quotes


def get_codes_from_data(data: str) -> list[int]:
    list_codes, ind_chars_in_quotes = str2list_int(data)

    int_data = get_integers(data, ind_chars_in_quotes)
    ind_list_codes = 0
    for x in int_data:
        cur_list = list_codes[ind_list_codes]
        while cur_list:
            ind_list_codes += 1
            cur_list = list_codes[ind_list_codes]

        if isinstance(x, list):
            for el in x:
                cur_list.append(el)
        else:
            cur_list.append(x)
    # Выпрямление list_codes в один лист
    return list(chain.from_iterable(list_codes))


def get_data(text: list[str]) -> dict[str, list[int]]:
    num_str_decl_section: int = find_substring_row(text, ".data")
    label2data: dict[str, list[int]] = dict()
    for i in range(num_str_decl_section + 1, len(text)):
        line: str = text[i].strip()
        if ".text" in line:
            break
        if not line:
            continue

        label, data = line.split(":", 1)
        label = label.strip()

        assert label not in label2data, 'Redefinition label: "{}"'.format(label)

        label2data[label] = get_codes_from_data(data)
    return label2data


def name2opcode() -> dict[str, Opcode]:
    return {
        "push": Opcode.PUSH,
        "pop": Opcode.POP,
        "jmp": Opcode.JMP,
        "jz": Opcode.JZ,
        "jnz": Opcode.JNZ,
        "js": Opcode.JS,
        "jns": Opcode.JNS,
        "call": Opcode.CALL,
        "ret": Opcode.RET,
        "input": Opcode.INPUT,
        "output": Opcode.OUTPUT,
        "inc": Opcode.INC,
        "dec": Opcode.DEC,
        "add": Opcode.ADD,
        "sub": Opcode.SUB,
        "mul": Opcode.MUL,
        "div": Opcode.DIV,
        "load": Opcode.LOAD,
        "store": Opcode.STORE,
        "swap": Opcode.SWAP,
        "hlt": Opcode.HLT,
    }


def cmd_with_args():
    return {
        Opcode.PUSH,
        Opcode.JMP,
        Opcode.JZ,
        Opcode.JNZ,
        Opcode.JS,
        Opcode.JNS,
        Opcode.CALL,
        Opcode.INPUT,
        Opcode.OUTPUT,
    }


def get_meaningful_token(line: str) -> str:
    return line.split(";", 1)[0].strip()


def translate_stage_1(text: list[str]) -> (dict[str, int], list[dict[str, Opcode | str]]):
    code: list[dict[str, Opcode | str]] = []
    labels: dict[str, int] = {}
    num_str_decl_section: int = find_substring_row(text, ".text")
    for ind in range(num_str_decl_section + 1, len(text)):
        raw_line = text[ind]
        token = get_meaningful_token(raw_line)
        if token == "" or ".data" in token:
            continue

        pc = len(code)
        if token.endswith(":"):  # токен содержит метку
            label = token.strip(":")
            assert label not in labels, "Redefinition of label: {}".format(label)
            labels[label] = pc
        elif " " in token:  # токен содержит инструкцию с операндом (отделены пробелом)
            sub_tokens = token.split(" ")
            assert len(sub_tokens) == 2, "Invalid instruction: {}".format(token)
            mnemonic, arg = sub_tokens
            opcode = name2opcode().get(mnemonic)
            assert opcode in cmd_with_args(), "{} must have zero argument".format(Opcode(opcode).name)
            code.append({"index": pc, "opcode": opcode, "arg": arg})
        else:  # токен содержит инструкцию без операндов
            opcode = name2opcode().get(token)
            assert opcode not in cmd_with_args(), "{} must have one argument".format(Opcode(opcode).name)
            code.append({"index": pc, "opcode": opcode})

    return labels, code


def translate_stage_2(labels: dict[str, int], code: list[dict[str, str | int]]):
    for instruction in code:
        if "arg" in instruction:
            if instruction["opcode"] in {Opcode.INPUT, Opcode.OUTPUT, Opcode.PUSH}:
                continue

            label = instruction["arg"]
            assert label in labels, "Label not defined: " + label
            instruction["arg"] = labels[label]
    return code


def translate_code(text: list[str]) -> list[dict[str, Opcode | str | int]]:
    labels, code = translate_stage_1(text)
    return translate_stage_2(labels, code)


def get_labels_to_num(labels2data: dict[str, list[int]]) -> dict[str, int]:
    labels2num: dict[str, int] = {}
    cur_num = 0
    for label, data in labels2data.items():
        labels2num[label] = cur_num
        cur_num += len(data)
    return labels2num


def is_number(s: str) -> bool:
    if len(s) <= 1:
        return s.isdigit()
    return s.isdigit() or (s[1::].isdigit() and s[0] in {"+", "-"})


def replace_push_arg(
    code: list[dict[str, Opcode | str | int]], labels2data: dict[str, list[int]]
) -> list[dict[str, Opcode | int]]:
    labels2num: dict[str, int] = get_labels_to_num(labels2data)
    for instruction in code:
        if instruction["opcode"] is Opcode.PUSH and not is_number(instruction["arg"]):
            instruction["arg"] = labels2num[instruction["arg"]]
        elif instruction["opcode"] is Opcode.PUSH and is_number(instruction["arg"]):
            instruction["arg"] = int(instruction["arg"])
    return code


def translate(text: str) -> (dict[str, list[int]], list[dict[str, Opcode | int]]):
    text = text.splitlines()
    labels2data = get_data(text)
    code = replace_push_arg(translate_code(text), labels2data)
    return labels2data, code


def main(source_file, target_data_file, target_program_file):
    with open(source_file, encoding="utf-8", errors="ignore") as f:
        source = f.read()

    data, code = translate(source)
    write_data(target_data_file, data)
    write_code(target_program_file, code)
    print("source LoC:", len(source.split("\n")), "code instr:", len(code))


if __name__ == "__main__":
    assert len(sys.argv) == 4, "Wrong arguments: translator.py <input_file> <target_data_file> " "<target_program_file>"
    _, source_file, target_data_file, target_program_file = sys.argv
    main(source_file, target_data_file, target_program_file)
