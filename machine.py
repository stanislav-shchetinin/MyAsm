#!/usr/bin/python3

import logging
import sys

from isa import Opcode, read_code, read_data
from enum import Enum
from typing import List, Dict


# sel_pc_next -> sel_next

class Signal(int, Enum):
    LATCH_SP = 1
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


m_program = [
    # Instruction Fetch
    0b100000000100000000000,
    # push
    0b1000000000100001000001,
    0b1000000000101000100000,
    0b1110000000011000000110000000100,
    # jmp
    0b10001000010000000110000000000,
    # jz
    0b1000001000010000000110000000000,
    # jnz
    0b1010001000010000000110000000000,
    # js
    0b100001000010000000110000000000,
    # jns
    0b110001000010000000110000000000,
    # call
    0b10000011000000001100000000000,
    0b1000000010100000000000,
    0b1000010000000110000000000,
    # ret
    0b1100001001000000000110000000000,
    0b100010000001100000000000,
    # input
    0b1000000000100001000001,
    0b1000000000101000100000,
    0b1110000000010100000110000000100,
    # output
    0b1110000000010000000110000010000,
    # pop
    0b1000000100100000000100,
    0b1110000000010000000110010000001,
    # swap
    0b1000000100100000000110,
    0b1110000000010000000100100100000,
    # add
    0b1000000000100000000010,
    0b10001000010000100001000100,
    0b1110000000010000000110100100000,
    # sub
    0b1000000000100000000010,
    0b100001000010000100001000100,
    0b1110000000010000000110100100000,
    # mul
    0b1000000000100000000010,
    0b110001000010000100001000100,
    0b1110000000010000000110100100000,
    # div
    0b1000000000100000000010,
    0b1000001000010000100001000100,
    0b1110000000010000000110100100000,
    # inc
    0b1000000000100000000010,
    0b1010001000010000100001000100,
    0b1110000000010000000110100100000,
    # dec
    0b1000000000100000000010,
    0b1100001000010000100001000100,
    0b1110000000010000000110100100000,
    # load
    0b1000001000100001000011,
    0b1110000000010000000110100100000,
    # store
    0b1110000000010000000110000001000,
]


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

    program_counter = None

    data_path = None

    _tick = None

    opcode_to_mp = {
        Opcode.PUSH: 1,
        Opcode.JMP: 4,
        Opcode.JZ: 5,
        Opcode.JNZ: 6,
        Opcode.JS: 7,
        Opcode.JNS: 8,
        Opcode.CALL: 9,
        Opcode.RET: 12,
        Opcode.INPUT: 14,
        Opcode.OUTPUT: 17,
        Opcode.POP: 18,
        Opcode.SWAP: 20,
        Opcode.ADD: 22,
        Opcode.SUB: 25,
        Opcode.MUL: 28,
        Opcode.DIV: 31,
        Opcode.INC: 34,
        Opcode.DEC: 37,
        Opcode.LOAD: 40,
        Opcode.STORE: 42
    }

    def __init__(self, program, data_path):
        self.program = program
        self.program_counter = 0
        self.data_path = data_path
        self._tick = 0

    def tick(self):
        self._tick += 1

    def current_tick(self):
        return self._tick



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
