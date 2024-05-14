#!/usr/bin/python3

import logging
import sys

from isa import Opcode, read_code, read_data
from enum import Enum
from typing import List, Dict


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
    0b11000000001100000000000,
    0b1000000010100000000000,
    0b10000000010000000110000000000,
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
    0b1110000000010000000110100100000,
    # add
    0b1000000000100000000010,
    0b10001000010000100001000101,
    0b1110000000010000000110100100000,
    # sub
    0b1000000000100000000010,
    0b100001000010000100001000101,
    0b1110000000010000000110100100000,
    # mul
    0b1000000000100000000010,
    0b110001000010000100001000101,
    0b1110000000010000000110100100000,
    # div
    0b1000000000100000000010,
    0b1000001000010000100001000101,
    0b1110000000010000000110100100000,
    # inc
    0b1000000000100000000010,
    0b1010001000010000100001000101,
    0b1110000000010000000110100100000,
    # dec
    0b1000000000100000000010,
    0b1100001000010000100001000101,
    0b1110000000010000000110100100000,
    # load
    0b1000000000100001000011,
    0b1110000000010001000110100100100,
    # store
    0b1110000000010000000110000001000,
]


class DataPath:
    stack_registers: List[int] = None
    stack_pointer = None
    swap_register = None
    tos: int = None
    data_memory: List[int] = None
    result_alu = None
    cu_arg = None
    io_ports: Dict[int, List[str]] = None

    def __init__(self, data, stack_capacity, input_tokens: List[str]):
        self.data_memory = data
        self.stack_registers = [0] * stack_capacity
        self.stack_pointer = -1
        self.swap_register = 0
        self.tos = 0
        self.result_alu = 0
        self.cu_arg = 0
        self.io_ports = {0: input_tokens}  # 0 - input, 1 - output by default
        for num_port in range(1, 16):  # count of ports is 16
            self.io_ports[num_port] = []

    def latch_sp(self, sel: List[Signal]):

        if Signal.SEL_SP_NEXT in sel:
            assert self.stack_pointer < len(self.stack_registers), "stack capacity exceeded"
            self.stack_pointer += 1
        elif Signal.SEL_SP_PREV in sel:
            assert self.stack_pointer >= 0, "a negative stack pointer was received"
            self.stack_registers[self.stack_pointer] = 0
            self.stack_pointer -= 1

    def latch_swr(self):
        self.swap_register = self.tos

    def top_stack_regs(self) -> int:
        return self.stack_registers[self.stack_pointer]

    def latch_tos(self, sel: List[Signal]):
        if Signal.SEL_TOS_ALU in sel:
            self.tos = self.result_alu
        elif Signal.SEL_TOS_SREG in sel:
            self.tos = self.top_stack_regs()
        elif Signal.SEL_TOS_CU_ARG in sel:
            self.tos = self.cu_arg
        elif Signal.SEL_TOS_DATA_MEM in sel:
            self.tos = self.data_memory[self.tos]
        elif Signal.SEL_TOS_INPUT in sel:
            buffer = self.io_ports[self.cu_arg]
            if not buffer:
                raise EOFError()
            self.tos = ord(buffer[0])
            self.io_ports[self.cu_arg] = self.io_ports[self.cu_arg][1:]

    def write_dm(self):
        self.data_memory[self.top_stack_regs()] = self.tos

    def write_io(self):
        assert self.cu_arg in self.io_ports, "Invalid port"
        self.io_ports[self.cu_arg].append(chr(self.tos))

    def latch_sreg(self, sel: List[Signal]):
        if Signal.SEL_SREG_TOS in sel:
            self.stack_registers[self.stack_pointer] = self.tos
        elif Signal.SEL_SREG_SWR in sel:
            self.stack_registers[self.stack_pointer] = self.swap_register

    def alu_add(self):
        self.result_alu = self.tos + self.top_stack_regs()

    def alu_sub(self):
        self.result_alu = self.tos - self.top_stack_regs()

    def alu_mul(self):
        self.result_alu = self.tos * self.top_stack_regs()

    def alu_div(self):
        self.result_alu = self.tos // self.top_stack_regs()

    def alu_inc(self):
        self.result_alu = self.tos + 1

    def alu_dec(self):
        self.result_alu = self.tos - 1


class ControlUnit:
    program = None
    pc = None
    mpc = None
    data_path: DataPath = None
    call_stack = None
    scp = None
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

    def __init__(self, program, data_path: DataPath, call_stack_capacity):
        self.program = program
        self.pc = 0
        self.mpc = 0
        self.data_path = data_path
        self.call_stack = [0] * call_stack_capacity
        self.scp = -1
        self._tick = 0

    @staticmethod
    def __int_to_list_signals(mc: int) -> List[Signal]:
        signals: List[Signal] = []

        # add signals from latch_sp (0) to sel_pc (24)
        for i in range(25):
            mask = (1 << i)
            if (mc & mask) != 0:
                signals.append(Signal(mask))

        alu_mask = (1 << 25) + (1 << 26) + (1 << 27)
        if (mc & alu_mask) != 0:
            signals.append(Signal(mc & alu_mask))

        jmp_mask = (1 << 28) + (1 << 29) + (1 << 30)
        if (mc & jmp_mask) != 0:
            signals.append(Signal(mc & jmp_mask))

        return signals

    def tick(self):
        self._tick += 1

    def current_tick(self):
        return self._tick

    def latch_pc(self, sel: List[Signal]):
        tos = self.data_path.tos

        # First MUX
        if Signal.SEL_JS in sel and tos < 0 \
                or Signal.SEL_JNS in sel and tos >= 0 \
                or Signal.SEL_JZ in sel and tos == 0 \
                or Signal.SEL_JNZ in sel and tos != 0:
            sel.append(Signal.SEL_JMP)
        elif Signal.SEL_JS in sel \
                or Signal.SEL_JNS in sel \
                or Signal.SEL_JZ in sel \
                or Signal.SEL_JNZ in sel:
            sel.append(Signal.SEL_NEXT)

        # Second MUX
        if Signal.SEL_JMP in sel:
            self.pc = self.program[self.pc]["arg"]
        elif Signal.SEL_RET in sel:
            assert self.pc >= 0, "return with empty call stack"
            self.pc = self.call_stack[self.scp]
        elif Signal.SEL_NEXT in sel:
            self.pc += 1

    def latch_mpc(self, sel: List[Signal]):
        if Signal.SEL_MPC_ZERO in sel:
            self.mpc = 0
        elif Signal.SEL_MPC_NEXT in sel:
            self.mpc += 1
        elif Signal.SEL_MPC_OPCODE in sel:
            if Opcode.HLT is Opcode(self.program[self.pc]["opcode"]):
                raise StopIteration()
            self.mpc = self.opcode_to_mp[Opcode(self.program[self.pc]["opcode"])]

    def latch_scp(self, sel: List[Signal]):
        if Signal.SEL_SCP_NEXT in sel:
            assert self.scp < len(self.call_stack), "call stack capacity exceeded"
            self.scp += 1
        elif Signal.SEL_SCP_PREV in sel:
            assert self.scp >= 0, "a negative scp was received"
            self.scp -= 1

    def latch_callst(self):
        self.call_stack[self.scp] = self.pc + 1

    def execute_microprogram(self, mprogram: int):
        signals = self.__int_to_list_signals(mprogram)
        if Signal.ALU_SUM in signals:
            self.data_path.alu_add()
        if Signal.ALU_SUB in signals:
            self.data_path.alu_sub()
        if Signal.ALU_MUL in signals:
            self.data_path.alu_mul()
        if Signal.ALU_DIV in signals:
            self.data_path.alu_div()
        if Signal.ALU_INC in signals:
            self.data_path.alu_inc()
        if Signal.ALU_DEC in signals:
            self.data_path.alu_dec()
        if Signal.LATCH_SP in signals:
            self.data_path.latch_sp(signals)
        if Signal.LATCH_SWR in signals:
            self.data_path.latch_swr()
        if Signal.LATCH_TOS in signals:
            self.data_path.latch_tos(signals)
        if Signal.WRITE_DM in signals:
            self.data_path.write_dm()
        if Signal.WRITE_IO in signals:
            self.data_path.write_io()
        if Signal.LATCH_SREG in signals:
            self.data_path.latch_sreg(signals)
        if Signal.LATCH_MPC in signals:
            self.latch_mpc(signals)
        if Signal.LATCH_PC in signals:
            self.latch_pc(signals)
        if Signal.LATCH_SCP in signals:
            self.latch_scp(signals)
        if Signal.LATCH_CALLST in signals:
            self.latch_callst()

    def __repr__(self):
        state_repr = ("TICK: {:3} PC: {:3} MPC: {:3} TOS: {:3} SREG: {:3} SIZE_STACK: {:3}"
                      " ALU: {:3} SWR: {:3} ARG: {:3} CALL_STACK_TOP: {:3} SP: {}\n"
                      "STACK: {}\nOUTPUT: {}\nDATA: {}"
                      "\n-------------------------------------------------------------------------------------"
                      ).format(
            self._tick,
            self.pc,
            self.mpc,
            self.data_path.tos,
            self.data_path.top_stack_regs(),
            self.data_path.stack_pointer + 1,
            self.data_path.result_alu,
            self.data_path.swap_register,
            self.data_path.cu_arg,
            self.call_stack[self.scp] if self.scp != -1 else "EMPTY",
            self.data_path.stack_pointer,
            self.data_path.stack_registers,
            self.data_path.io_ports[1],
            self.data_path.data_memory
        )

        return state_repr


def simulation(code, data, input_tokens) -> (str, int):
    data_path = DataPath(data, 24, input_tokens)
    control_unit = ControlUnit(code, data_path, 16)
    logging.debug("%s", control_unit)
    try:
        while True:
            if control_unit.mpc == 0:
                data_path.cu_arg = control_unit.program[control_unit.pc]["arg"]
                logging.info("INSTRUCTION: %s, PC: %s",
                             Opcode(control_unit.program[control_unit.pc]["opcode"]).name,
                             control_unit.pc)
            mprogram = m_program[control_unit.mpc]
            control_unit.execute_microprogram(mprogram)
            control_unit.tick()
            logging.debug("%s", control_unit)
    except EOFError:
        logging.warning("Input buffer is empty!")
    except StopIteration:
        pass

    output_buffer = data_path.io_ports[1]
    logging.info("output_buffer: %s", repr("".join(output_buffer)))
    return "".join(output_buffer), control_unit.current_tick()


def main(code_file, data_file, input_file):
    code = read_code(code_file)
    data = read_data(data_file)
    with open(input_file, encoding="utf-8", errors='ignore') as file:
        input_text = file.read()
        input_token = []
        for char in input_text:
            input_token.append(char)

    output, ticks = simulation(
        code,
        data,
        input_token
    )

    print("".join(output))
    print("ticks:", ticks)


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG, filename="logs/machine.log", filemode="w")

    assert len(sys.argv) == 4, "Wrong arguments: machine.py <data_file> <code_file> <input_file>"
    _, data_file, code_file, input_file = sys.argv
    main(code_file, data_file, input_file)
