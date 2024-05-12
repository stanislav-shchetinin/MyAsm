.data
buffer: 0
cnt: 0

.text
_main:
    push 10
    push 2
    push buffer
    push 8
    store
    swap
    pop

    cycle:
        push 4
        mul
        swap
        pop
        swap
        pop
        add
        push 4000000
        sub
        js ext
        pop
        pop
        swap
        pop
        swap
        pop
        swap
        add
        swap
        pop
        swap
        push buffer
        load
        swap
        pop
        swap
        push 0
        swap
        store
        swap
        pop
        jmp cycle

    ext:
        pop
        pop
        pop
        pop
        pop
        output 1
        hlt

cnt_digits:
    push 0
    add
    swap
    pop
    push 10
    swap
    div
    jz ext_cnt_digits
    swap
    pop
    swap pop
    push cnt
    load
    inc
    swap
    pop
    store
    pop
    pop
    jmp cnt_digits

ext_cnt_digits:
    pop
    pop
    pop
    ret

digits_on_stack:
    jz ext_digits_on_stack
    push 10
    swap
    div
    push
    mul
    swap
    pop
    swap
    pop
    swap
    sub
    swap
    swap
    pop
    swap
    pop
    swap
    div
    swap
    pop
    swap
    pop
    jmp digits_on_stack

ext_digits_on_stack:
    ret

print_int:
    push cnt
    load
    jz ext_print_int
    dec
    swap
    pop
    store
    pop
    pop
    output 1
    pop
    jmp print_int

ext_print_int:
    ret