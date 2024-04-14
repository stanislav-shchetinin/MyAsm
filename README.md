# Translator + processor model for Assembler

- Щетинин Станислав Владимирович. Группа: P3208
- ` asm | stack | harv | mc | instr | binary | stream | port | cstr | prob2 | cache `
- Усложнение - кэш
- instr -> tick - т.к. взял вариант с усложнением
  
## Язык программирования
``` ebnf
<program> ::= <section_data> <section_text> | <section_text> <section_data> | <section_text>

<section_data> ::= "section .data\n" <declaration>*
<section_text> ::= "section .text\n" (<label> | <instruction>)*

<declaration> ::= <label> (<array> | <reserve>)
<instruction> ::= <label_arg_command> | <number_arg_command> | <without_arg_command>

<label> ::= (<name> ":" (" ")*) | (<name> ":" (" ")* "\n")

<array> ::= (<array_element> "," (" ")*)* <array_element>+
<reserve> ::= "res" (" ")+ <number>
<array_element> ::= ("\"" <any_ascii> "\"" | <number>)

<label_arg_command> ::= ("push" | "jmp" 
| "jz" | "jnz" | "js" | "jns" | "call") (" ")+ <label>

<number_arg_command> ::= ("push" | "cmp" | "input" | "output") (" ")+ <number>
<without_arg_command> ::= ("inc" | "hlt" | "pop" | "swap" | "add" | "sub" | "mul" | "div" | "ret" | "load" | "store")

<number> ::= [-2^64; 2^64 - 1]
<name> ::= (<letter_or_>)+
<letter_or_> ::= <letter> | ("_")
<letter> ::= [a-z] | [A-Z]
``` 

### Hello, world
```asm
section .data
hello_str: "Hello, world!"

section .text
_main:
    push hello_str
    cycle:
        load      ;загружаю на вершину стэка значение по адресу вершины стэка
        cmp 0     ;вычитаю из вершины стэка 0 - результат на вершине стэка
        jz ext    ;если на вершине 0, то переход
        pop       ;убрал ноль
        output 1  ;вывод по порту 1 (порт для вывода), 0 - порт для ввода
        pop       ;убрал букву
        inc       ;увеличил на один адрес
        jmp cycle ;безусловный переход
    
    ext:
        pop       ;убрал 0
        pop       ;убрал адрес нуля в памяти
        hlt       ;завершение

```

### cat

```asm
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

```

### Hello, Alice!

``` asm
section .data
question: "What is your name?", 0
hello_str: "Hello, ", 0
buffer: res 256

section .text
_main:
    push question
    call print_str ;выводит строку, адрес которой сейчас на вершине
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
        cmp 0
        jz ext_out
        pop
        output 1
        pop
        inc
        jmp cycle_out
    ext_out:
        pop       ;удаляет 0
        pop       ;удаляет адрес нуля
        ret

input_str:
    cycle_in:
        input 0
        cmp '\n'  ;если введен символ перевода строки, то ввод завершается
        jz ext_in
        pop       ;удаление результата cmp
        store     ; |top1|top2|...|last| - интерпретирует top2 как адрес и записывает по нему значение top1
        pop
        inc
        jmp cycle_in
    
    ext_in:
        pop      ;удаление результата cmp
        pop      ;удаление результата ввода (\n)
        pop      ;удаление текущего адреса в буффере
        ret

```

### prob2
Посчитать сумму четных чисел Фибоначчи до 4 миллионов.  

С помощью несложных математических выкладок поймем, что каждое третье число Фибоначчи, начиная с 2 - четное и других четных нет. А также, что текущее четное число Фибоначчи можно выразить из предыдущих по формуле: $$F_n = 4 \cdot F_{n - 3} + F_{n - 6}$$  

Тогда для каждой итерации cycle будем поддерживать следующий инвариант

```
     _____        _____
0:  |     |      |     | 
    |  8  |      |  8  |  <---- F_{n - 3}
    |_____|      |_____|
                 |     |
       ^         |  2  |  <---- F_{n - 6}
       |         |_____|
       |         |     |
                 | 10  |  <---- текущая сумма
    F_{n - 3}    |_____|        

```

Когда происходит jmp в ext, машина находится в следующем состоянии:

```
     _____        _____
0:  |     |      |     | 
    |  8  |      | 34  |  <---- F_{n}
    |_____|      |_____|
                 |     |
       ^         | 32  |  <---- промежуточный рез-т
       |         |_____|
       |         |     |
                 |  2  |  <---- F_{n - 6}
    F_{n - 3}    |_____|
                 |     |
                 | 10  |  <---- сумма на пред. шаге    
                 |_____|

```

``` asm
section .text
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
        cmp 4000000
        jns ext
        pop     ;удаляем результат cmp
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
```