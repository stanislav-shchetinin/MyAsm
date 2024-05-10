#!/usr/bin/python3

import logging
import sys

from isa import Opcode, read_code, read_data
from enum import Enum
from typing import List, Dict


class Signal(int, Enum):
    LATCH_SP = 0
    LATCH_SWR = (1 << 1)
    LATCH_TOS = (1 << 2)
    WRITE_DM = (1 << 3)
    WRITE_IO = (1 << 4)
    LATCH_SREG = (1 << 5)
    SEL_SP_NEXT = (1 << 6)
    SEL_SP_PREV = (1 << 7)
    SEL_SREG_SWR = (1 << 8)
    SEL_SREG_TOS = (1 << 9)
    LATCH_PC = (1 << 10)
    LATCH_MPC = (1 << 11)
    LATCH_SCP = (1 << 12)
    LATCH_CALLST = (1 << 13)
    SEL_TOS_SREG = (1 << 14)
    SEL_TOS_DATA_MEM = (1 << 15)
    SEL_TOS_ALU = (1 << 16)
    SEL_TOS_INPUT = (1 << 17)
    SEL_TOS_CU_ARG = (1 << 18)
    SEL_MPC_ZERO = (1 << 19)
    SEL_MPC_OPCODE = (1 << 20)
    SEL_MPC_NEXT = (1 << 21)
    SEL_SCP_NEXT = (1 << 22)
    SEL_SCP_PREV = (1 << 23)
    SEL_PC = (1 << 24)
    ALU_SUM = (1 << 25)
    ALU_SUB = (1 << 26)
    ALU_MUL = (1 << 25) + (1 << 26)
    ALU_DIV = (1 << 27)
    ALU_INC = (1 << 27) + (1 << 25)
    ALU_DEC = (1 << 27) + (1 << 26)
    SEL_JMP = (1 << 28)
    SEL_JS = (1 << 29)
    SEL_JNS = (1 << 29) + (1 << 28)
    SEL_JZ = (1 << 30)
    SEL_JNZ = (1 << 30) + (1 << 28)
    SEL_RET = (1 << 30) + (1 << 29)
    SEL_NEXT = (1 << 30) + (1 << 29) + (1 << 28)


class DataPath:
    stack_registers: List[int] = None
    stack_pointer = None
    swap_register = None
    tos = None
    data_memory: List[int] = None
    io_controller = None
    result_alu = None
    cu_arg = None
    io_ports: Dict[int, List[str]] = None

    def __init__(self, data_file, stack_capacity, input_tokens: List[str]):
        self.data_memory = read_data(data_file)
        self.stack_registers = [0] * stack_capacity
        self.stack_pointer = 0
        self.swap_register = 0
        self.tos = 0
        self.result_alu = 0
        self.cu_arg = 0
        self.io_ports = {0: input_tokens}  # 0 - input, 1 - output by default
        for num_port in range(1, 16):  # count of ports is 16
            self.io_ports[num_port] = []

    def latch_sp(self, sel: List[Signal]):

        if Signal.SEL_SP_NEXT in sel:
            self.stack_pointer += 1
            assert self.stack_pointer < len(self.stack_registers), "stack capacity exceeded"
        elif Signal.SEL_SP_PREV in sel:
            self.stack_pointer -= 1
            assert self.stack_pointer < 0, "a negative stack pointer was received"

    def latch_swr(self):
        self.swap_register = self.tos

    def __top_stack_regs(self) -> int:
        return self.stack_registers[self.stack_pointer]

    def latch_tos(self, sel: List[Signal]):
        if Signal.SEL_TOS_ALU in sel:
            self.tos = self.result_alu
        elif Signal.SEL_TOS_SREG in sel:
            self.tos = self.__top_stack_regs()
        elif Signal.SEL_TOS_CU_ARG in sel:
            self.tos = self.cu_arg
        elif Signal.SEL_TOS_DATA_MEM in sel:
            self.tos = self.data_memory[self.__top_stack_regs()]
        elif Signal.SEL_TOS_INPUT in sel:
            buffer = self.io_ports[self.cu_arg]
            assert buffer, "attempt to read an empty buffer"
            self.tos = buffer[0]
            buffer.pop()

    def write_dm(self):
        self.data_memory[self.__top_stack_regs()] = self.tos

    def write_io(self):
        assert self.cu_arg in self.io_ports, "Invalid port"
        self.io_ports[self.cu_arg].append(chr(self.tos))

    def latch_sreg(self):
        self.stack_registers[self.stack_pointer] = self.tos

    def alu_add(self):
        self.result_alu = self.tos + self.__top_stack_regs()

    def alu_sub(self):
        self.result_alu = self.tos - self.__top_stack_regs()

    def alu_mul(self):
        self.result_alu = self.tos * self.__top_stack_regs()

    def alu_div(self):
        self.result_alu = self.tos / self.__top_stack_regs()

    def alu_inc(self):
        self.result_alu += 1

    def alu_dec(self):
        self.result_alu -= 1

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
