.text
_main:
    cycle:
        input 0   ;считать с порта 0
        jz ext
        output 1  ;вывести на порт 1
        pop
        jmp cycle
    ext:
        hlt
