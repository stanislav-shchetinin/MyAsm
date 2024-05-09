#!/usr/bin/python3

import logging
import sys

from isa import Opcode, read_code, read_data
from enum import Enum

class Singnals(int, Enum):
    A = 1
    B = 1

class DataPath:
    stack_registers = None
    stack_pointer = None
    swap_register = None
    tos = None
    data_memory = None
    io_controller = None

    def __init__(self, data_file, stack_capacity):
        self.data_memory = read_data(data_file)
        self.stack_registers = [0] * stack_capacity
        self.stack_pointer = 0
        self.swap_register = 0
        self.tos = 0

    def latch_sp(self, sel: SelectSP):
        assert sel in {
            SelectSP.NEXT,
            SelectSP.PREV
        }, "internal error, incorrect selector: {}".format(sel)

        if sel == SelectSP.NEXT:
            self.stack_pointer += 1
            assert self.stack_pointer < len(self.stack_registers), "stack capacity exceeded"
        elif sel == SelectSP.PREV:
            self.stack_pointer -= 1
            assert self.stack_pointer < 0, "a negative stack pointer was received"

    def latch_swr(self):
        self.swap_register = self.tos


class ControlUnit:
    program = None
    "Память команд."

    program_counter = None
    "Счётчик команд. Инициализируется нулём."

    data_path = None
    "Блок обработки данных."

    _tick = None
    "Текущее модельное время процессора (в тактах). Инициализируется нулём."

    def __init__(self, program, data_path):
        self.program = program
        self.program_counter = 0
        self.data_path = data_path
        self._tick = 0

    def tick(self):
        """Продвинуть модельное время процессора вперёд на один такт."""
        self._tick += 1

    def current_tick(self):
        """Текущее модельное время процессора (в тактах)."""
        return self._tick

    def signal_latch_program_counter(self, sel_next):
        """Защёлкнуть новое значение счётчика команд.

        Если `sel_next` равен `True`, то счётчик будет увеличен на единицу,
        иначе -- будет установлен в значение аргумента текущей инструкции.
        """
        if sel_next:
            self.program_counter += 1
        else:
            instr = self.program[self.program_counter]
            assert "arg" in instr, "internal error"
            self.program_counter = instr["arg"]

    def decode_and_execute_control_flow_instruction(self, instr, opcode):
        """Декодировать и выполнить инструкцию управления потоком исполнения. В
        случае успеха -- вернуть `True`, чтобы перейти к следующей инструкции.
        """
        if opcode is Opcode.HALT:
            raise StopIteration()

        if opcode is Opcode.JMP:
            addr = instr["arg"]
            self.program_counter = addr
            self.tick()

            return True

        if opcode is Opcode.JZ:
            addr = instr["arg"]

            self.data_path.signal_latch_acc()
            self.tick()

            if self.data_path.zero():
                self.signal_latch_program_counter(sel_next=False)
            else:
                self.signal_latch_program_counter(sel_next=True)
            self.tick()

            return True

        return False

    def decode_and_execute_instruction(self):
        """Основной цикл процессора. Декодирует и выполняет инструкцию.

        Обработка инструкции:

        1. Проверить `Opcode`.

        2. Вызвать методы, имитирующие необходимые управляющие сигналы.

        3. Продвинуть модельное время вперёд на один такт (`tick`).

        4. (если необходимо) повторить шаги 2-3.

        5. Перейти к следующей инструкции.

        Обработка функций управления потоком исполнения вынесена в
        `decode_and_execute_control_flow_instruction`.
        """
        instr = self.program[self.program_counter]
        opcode = instr["opcode"]

        if self.decode_and_execute_control_flow_instruction(instr, opcode):
            return

        if opcode in {Opcode.RIGHT, Opcode.LEFT}:
            self.data_path.signal_latch_data_addr(opcode.value)
            self.signal_latch_program_counter(sel_next=True)
            self.tick()

        elif opcode in {Opcode.INC, Opcode.DEC, Opcode.INPUT}:
            self.data_path.signal_latch_acc()
            self.tick()

            self.data_path.signal_wr(opcode.value)
            self.signal_latch_program_counter(sel_next=True)
            self.tick()

        elif opcode is Opcode.PRINT:
            self.data_path.signal_latch_acc()
            self.tick()

            self.data_path.signal_output()
            self.signal_latch_program_counter(sel_next=True)
            self.tick()

    def __repr__(self):
        """Вернуть строковое представление состояния процессора."""
        state_repr = "TICK: {:3} PC: {:3} ADDR: {:3} MEM_OUT: {} ACC: {}".format(
            self._tick,
            self.program_counter,
            self.data_path.data_address,
            self.data_path.data_memory[self.data_path.data_address],
            self.data_path.acc,
        )

        instr = self.program[self.program_counter]
        opcode = instr["opcode"]
        instr_repr = str(opcode)

        if "arg" in instr:
            instr_repr += " {}".format(instr["arg"])

        if "term" in instr:
            term = instr["term"]
            instr_repr += "  ('{}'@{}:{})".format(term.symbol, term.line, term.pos)

        return "{} \t{}".format(state_repr, instr_repr)


def simulation(code, input_tokens, data_memory_size, limit):
    """Подготовка модели и запуск симуляции процессора.

    Длительность моделирования ограничена:

    - количеством выполненных инструкций (`limit`);

    - количеством данных ввода (`input_tokens`, если ввод используется), через
      исключение `EOFError`;

    - инструкцией `Halt`, через исключение `StopIteration`.
    """
    data_path = DataPath(data_memory_size, input_tokens)
    control_unit = ControlUnit(code, data_path)
    instr_counter = 0

    logging.debug("%s", control_unit)
    try:
        while instr_counter < limit:
            control_unit.decode_and_execute_instruction()
            instr_counter += 1
            logging.debug("%s", control_unit)
    except EOFError:
        logging.warning("Input buffer is empty!")
    except StopIteration:
        pass

    if instr_counter >= limit:
        logging.warning("Limit exceeded!")
    logging.info("output_buffer: %s", repr("".join(data_path.output_buffer)))
    return "".join(data_path.output_buffer), instr_counter, control_unit.current_tick()


def main(code_file, input_file):
    """Функция запуска модели процессора. Параметры -- имена файлов с машинным
    кодом, с данными и с входными данными для симуляции.
    """
    code = read_code(code_file)
    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)

    output, instr_counter, ticks = simulation(
        code,
        input_tokens=input_token,
        data_memory_size=100,
        limit=1000,
    )

    print("".join(output))
    print("instr_counter: ", instr_counter, "ticks:", ticks)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 4, "Wrong arguments: machine.py <code_file> <data_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)
