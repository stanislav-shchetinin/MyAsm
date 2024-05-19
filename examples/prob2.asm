.data
buffer: 0

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
        push -1
        swap
        call digits_on_stack
        call print_int
        hlt

digits_on_stack:
    jz ext_digits_on_stack
    push 10
    swap
    div
    push 10
    mul
    swap
    pop
    swap
    pop
    swap
    sub
    swap
    pop
    swap
    push 10
    swap
    div
    swap
    pop
    swap
    pop
    jmp digits_on_stack

ext_digits_on_stack:
    pop
    ret

print_int:
    js ext_print_int
    push 48                 ; ascii '0'
    add
    output 1
    pop                     ; result add
    pop                     ; 48
    pop                     ; digit
    pop                     ; 10 - implementation detail
    jmp print_int

ext_print_int:
    ret