section .text
_main:
    input 0
    cycle:
        jz ext
        input 0   ;считать с порта 0
        output 1  ;вывести на порт 1
        pop
        jmp cycle
    ext:
        pop
        hlt
