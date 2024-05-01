#!/usr/bin/python3
"""Транслятор Asm в машинный код.
"""

import sys

from isa import Opcode, write_code
from typing import List, Dict
from itertools import chain


def get_num_str_declaration_data(text: List[str]) -> int:
    num_str_decl_section: int = -1

    for index, line in enumerate(text):
        if ".data" in line:
            assert num_str_decl_section == -1, "Section .data can be declared at most once"
            num_str_decl_section = index

    return num_str_decl_section


def remove(s: str, indexes: List[int]) -> str:
    new_s: str = ""
    for ind, x in enumerate(s):
        if not (ind in indexes):
            new_s += x
    return new_s


def remove_double_comma(s: str) -> str:
    new_s = ""
    last_is_comma: bool = False
    for x in s:
        if x == ',' and not last_is_comma:
            new_s += x
            last_is_comma = True
        elif x != ',':
            new_s += x
            last_is_comma = False
    return new_s


def get_integers(data: str, ind_chars_in_quotes: List[int]) -> List[int]:
    int_data = remove(data, ind_chars_in_quotes)
    # Могут появиться после удаления две запятые подряд - их надо почистить
    int_data = remove_double_comma(int_data)
    # Удаление комментариев
    int_data = int_data.split(';')[0].strip()
    int_data = list(filter(None, int_data.split(',')))
    int_data = [int(x) for x in int_data]
    for x in int_data:
        assert -(1 << 31) <= x <= (1 << 31) - 1, "Integer must take values in the segment [-2^31; 2^31 - 1]"
    return int_data


def get_codes_from_data(data: str) -> List[int]:
    in_quotes: bool = False
    # Массив, в котором хранятся индексы элементов, взятых в кавычки (включая кавычки)
    # Нужен, чтобы после первого прохода по данным в метке, очистить данные от строк
    ind_chars_in_quotes: List[int] = [[]]
    # Массив, в котором элемент является List[int] длины строки,
    # если в исходном тексте на этом месте была строка (каждый int это код элемента в ASCII),
    # или длины 1, если в исходном тексте это было просто число
    list_codes: List[List[int]] = [[]]
    for index, x in enumerate(data):
        if x == '"':
            in_quotes = not in_quotes
            ind_chars_in_quotes.append(index)
        elif in_quotes:
            list_codes[-1].append(ord(x))
            ind_chars_in_quotes.append(index)
        elif x == ',':
            list_codes.append([])

    int_data = get_integers(data, ind_chars_in_quotes)
    ind_list_codes = 0
    for x in int_data:
        cur_list = list_codes[ind_list_codes]
        while cur_list:
            ind_list_codes += 1
            cur_list = list_codes[ind_list_codes]
        cur_list.append(x)

    # Выпрямление list_codes в один лист
    return list(chain.from_iterable(list_codes))


def get_data(text: List[str]) -> Dict[str, List[int]]:
    num_str_decl_section: int = get_num_str_declaration_data(text)
    label2data: Dict[str, List[int]] = dict()
    for i in range(num_str_decl_section + 1, len(text)):
        line: str = text[i].strip()
        if ".text" in line:
            break
        if not line:
            continue

        label, data = line.split(':', 1)
        label = label.strip()

        assert label not in label2data, "Redefinition label: \"{}\"".format(label)

        label2data[label] = get_codes_from_data(data)
    return label2data


def translate(text: str):
    text = text.split('\n')
    labels_of_data = get_data(text)
    print(labels_of_data)


def main(source, target):
    """Функция запуска транслятора. Параметры -- исходный и целевой файлы."""
    with open(source, encoding="utf-8") as f:
        source = f.read()

    code = translate(source)

    # write_code(target, code)
    # print("source LoC:", len(source.split("\n")), "code instr:", len(code))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator_asm.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
