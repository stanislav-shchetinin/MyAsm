.data
question: "What is your name?", 0
hello_str: "Hello, ", 0
buffer: res 256

.text
_main:
    push question
    call output_str ;выводит строку, адрес которой сейчас на вершине
    push buffer
    call input_str
    push hello_str
    call output_str
    push buffer
    call output_str
    hlt


output_str:
    cycle_out:
        load
        jz ext_out
        output 1
        pop
        inc
        swap
        pop
        jmp cycle_out
    ext_out:
        pop       ;удаляет 0
        pop       ;удаляет адрес нуля
        ret

input_str:
    cycle_in:
        input 0
        push 10  ;если введен символ перевода строки (ascii '\n' == 0x0A), то ввод завершается
        sub
        jz ext_in
        pop       ;удаление результата sub
        pop       ;удаление 10
        store     ; |top1|top2|...|last| - интерпретирует top2 как адрес и записывает по нему значение top1
        pop
        inc
        swap
        pop
        jmp cycle_in

    ext_in:
        pop      ;удаление результата sub
        pop      ;удаление 10
        pop      ;удаление результата ввода (\n)
        pop      ;удаление текущего адреса в буффере
        ret
