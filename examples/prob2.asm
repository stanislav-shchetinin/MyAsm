.text
_main:
    push 10
    push 2
    push 0
    push 8
    store       ; 1 - адрес, по которому записано 8
    swap        ; поменять местами первые два элемента стэка
    pop         ; удалить 0

    cycle:
        push 4
        mul     ;переменожить два значения на верхушке стэка и результат положить наверх
        swap
        pop
        swap
        pop
        add     ;сложить два числа и результат на вершину
        push 4000000
        sub
        js ext
        pop     ;удаляем результат sub
        pop     ;удаляем 4000000
        push 0
        load
        pop
        swap
        push 0
        swap
        store
        swap
        pop
        pop
        swap
        pop
        swap
        pop
        swap
        push 0
        load
        swap
        pop
        add
        swap
        pop
        swap
        pop
        swap
        push 0
        load
        swap pop
        jmp cycle
    ext:
        pop
        pop
        pop
        output 1
        pop
        hlt