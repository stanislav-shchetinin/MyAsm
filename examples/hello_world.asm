.data
hello_str: "Hello, world!", 0

.text
_main:
    push hello_str
    cycle:
        load      ;загружаю на вершину стэка значение по адресу вершины стэка
        jz ext    ;если на вершине 0, то переход
        pop       ;убрал ноль
        output 1  ;вывод по порту 1 (порт для вывода), 0 - порт для ввода
        pop       ;убрал букву
        inc       ;увеличил на один адрес
        jmp cycle ;безусловный переход

    ext:
        hlt       ;завершение
