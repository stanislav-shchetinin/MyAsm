# Translator + processor model for Assembler

- Щетинин Станислав Владимирович. Группа: P3208
- ` asm | stack | harv | mc | tick | binary | stream | port | cstr | prob2 | cache `
- Базовый вариант
- instr -> tick - т.к. микрокод
  
## Язык программирования
### Синтаксис:
``` ebnf
<program> ::= <section_data> <section_text> | <section_text> <section_data> | <section_text>

<section_data> ::= ".data\n" <declaration>*
<section_text> ::= ".text\n" (<label> | <instruction>)*

<declaration> ::= <label> (<array> | <reserve>)
<instruction> ::= <label_arg_command> | <number_arg_command> | <without_arg_command>

<label> ::= (<name> ":" (" ")*) | (<name> ":" (" ")* "\n")

<array> ::= (<array_element> "," (" ")*)* <array_element>+
<reserve> ::= "res" (" ")+ <number>
<array_element> ::= ("\"" <any_ascii> "\"" | <number>)

<label_arg_command> ::= ("push" | "jmp" 
| "jz" | "jnz" | "js" | "jns" | "call") (" ")+ <label>

<number_arg_command> ::= ("push" | "input" | "output") (" ")+ <number>
<without_arg_command> ::= ("inc" | "hlt" | "pop" | "swap" | "add" | "sub" | "mul" | "div" | "ret" | "load" | "store")

<number> ::= [-2^32; 2^32 - 1]
<name> ::= (<letter_or_>)+
<letter_or_> ::= <letter> | ("_")
<letter> ::= [a-z] | [A-Z]
``` 

### Семантика:  

- `.text` -- секция, в которой все последующие слова, интерпретируются, как инструкции или их аргументы или комментарии или метки;
- `.data` -- секция, в которой инициализируются или резервируются сегменты памяти для пользовательских данных;
- `label` -- метка, которая является указателем на адрес памяти инструкции за ней (если метка в section .text) или является указателем на первый элемент зарезервированого сегмента памяти (если метка в section .data);
- `res n` -- оператор, который пишется после объяления метки в секции данных, обозначающий, что необходимо зарезервировать n байт памяти под эту метку;
- `push n` -- кладет значение n на вершину стэка. Если n - метка, то кладет, адрес, который она описывает, если n - число, то кладет n. ВАЖНО: так как у меня гарвардская архитектура, push label я могу выполнять только для label из Data Memory;
- `pop` -- удаляет верхний элемент со стэка;
- `jmp label` -- команда безусловного перехода. Устанавливает следующую команду, как ту, на которую указывает label - из Program Memory; 
- `jz label` -- если на вершине стэка 0, то выполняет `jmp`, иначе переход к следующей команде;
- `jnz label` -- если на вершине стэка не 0, то выполняет `jmp`, иначе переход к следующей команде;
- `js label` -- если на вершине стэка отрицательное число, то выполняет `jmp`, иначе переход к следующей команде;
- `jns label` -- если на вершине стэка не отрицательное число, то выполняет `jmp`, иначе переход к следующей команде;
- `call label` -- сохраняет на стэке вызывов адрес следующей команды и переходит к выполнению инструкции за label;
- `ret` -- устанавливает следующую команду, как ту, что лежит на верху стэка вызовов и удаляет элемент с верхушки стэка вызовов;
- `input n` -- считвает один символ из порта n и записывает его на верх стэка;
- `output n` -- записывает в порт n значение из верхушки стэка;
- `inc` -- увеличивает значение верхушки стэка на 1;
- `dec` -- уменьшает значение верхушки стэка на 1;
- `hlt` -- завершение программы;
- `swap` -- меняет местами значение на вершине стэка и значение  следующее после вершины стэка;
- `add` -- складывает значение на вершине стэка и значение  следующее после вершины стэка, результат помещает на вершину стэка;
- `sub` -- вычитает значение на вершине стэка и значение  следующее после вершины стэка, результат помещает на вершину стэка;
- `mul` -- перемножает значение на вершине стэка и значение  следующее после вершины стэка, результат помещает на вершину стэка;
- `div` -- делит значение на вершине стэка и значение  следующее после вершины стэка, результат помещает на вершину стэка;
- `load` -- интерпретирует значение на вершине стэка, как адрес по которому из памяти загружает значение на вершину стэка
- `store` -- интерпретирует значение следующее после вершины стэка, как адрес по которому нужно записать значение на вершине стэка

В программе не может быть дублирующихся меток.
Метка памяти данных задается на той же строке, что и данные:
``` asm 
hello_world: "Hello, world!", 0
```

Метка памяти команд задается на строке предшетсвующей инструкции, на которую указывает метка:
```
foo:
    push 10
    ...
```

### Область видимости

В любом месте секции .text доступен стэк и операции над его верхними значениями

### Типизация, виды литералов

Литералы могут быть представлены в виде чисел и меток (в последствии интерпретируются как числа), в секции .data можно объявлять строки. Типизация отсутсвует, так как пользователь языка может интерпретировать любые данные как захочет и может с ними выполнить любые из возможных операций.

## Организация памяти

- Гарвардская архитектура
- Резмер машинного слова:
  - Память данных - 32 бит;
  - Память команд - 32 бит.
- Адресации:
  - Прямая абсолютная (например, `push label`)
  - Косвенная (у команд `load`, `store` один из операндов является указателем на ячейку памяти)

```
       Registers
+------------------------------+
| TOS                          |
+------------------------------+
| Stack Registers              |
|    ...                       |
+------------------------------+
| SP, SWR, SCP, PC, mPC        |
+------------------------------+

       Program memory
+------------------------------+
| 00 : instruction 1           |
|   ...                        |
|  n : instruction n           |
+------------------------------+

          Data memory
+------------------------------+
| 00  : array 1                |
|    ...                       |
|  n  : array 2                |
|    ...                       |
+------------------------------+

```

- Для работы с регистрами отведена память, организованная в виде стека. Программист на прямую имеет доступ к `TOS`, верхушке `Stack Registers`,заранее инициализированной памяти в `Data Memory`, а также, используя различные условные и безусловный переходы, может изменять `PC`;
- Память данных разделена на массивы - разделение определяет пользователь, именуя каждый массив лейблом;
- Массив может состоять из строк, чисел и свободного места (заполнено нулями), зарезервированного на определенное количество байт. Все данные в массивах и все массивы идут последовательно;
- Инструкции хранятся в `Program Memory`;
- Для операндов пользователю отводится 24 бита, т.к. оставшиеся 8 бит занимает опкод;
- Используя команду `push number` литерал используется при помощи непосредственной адресации;   
- Используя команду `store` литерал будет загружен в статическую память;

## Система команд

**Особенности процессора:**
- Машинное слово -- знаковое 32-ух битное число;
- Доступ памяти осуществляется через указатель на вершине `Stack Register`. Установить можно при помощи `push label`;
- Устройство ввода-вывод: port-mapped
- Поток управления: 
  - Инкрементирования `PC`;
  - Условный/безусловный переход;
  - Адрес из вершины `Call Stack`.


Из транслятора выходят команды в формате: 8 бит на опкод + 24 на аргумент. В Control Unit опкод команды переводится в микрокод (отображение команды в опкод можно посмотреть в [isa.py](./isa.py))

**Набор инструкций:**
| Номер  | Название команды   | Сигналы                                                                     |
|--------|--------------------|-----------------------------------------------------------------------------|
| 0      | Instruction Fetch  | sel_mpc_opcode, latch_mpc                                                   |
| 1      | push               | sel_sp_next, latch_sp, sel_mpc_next, latch_mpc                              |
| 2      |                    | sel_sreg_tos, latch_sreg, sel_mpc_next, latch_mpc                           |
| 3      |                    | sel_tos_cu_arg, latch_tos, sel_pc_next, latch_pc, sel_mpc_zero, latch_mpc   |
| 4      | jmp                | sel_jmp, sel_pc, latch_pc, sel_mpc_zero, latch_mpc                          |
| 5      | jz                 | sel_jz, sel_pc, latch_pc,  sel_mpc_zero, latch_mpc                          |
| 6      | jnz                | sel_jnz, sel_pc, latch_pc,  sel_mpc_zero, latch_mpc                         |
| 7      | js                 | sel_js, sel_pc, latch_pc,  sel_mpc_zero, latch_mpc                          |
| 8      | jns                | sel_jns, sel_pc, latch_pc,  sel_mpc_zero, latch_mpc                         |
| 9      | call               | sel_scp_next, latch_scp, sel_mpc_next, latch_mpc                            |
| 10     |                    | latch_callst, sel_mpc_next, latch_mpc                                       |
| 11     |                    | sel_jmp, latch_pc, sel_mpc_zero, latch_mpc                                  |
| 12     | ret                | sel_ret, sel_pc, latch_pc, sel_mpc_next, latch_mpc                          |
| 13     |                    | sel_scp_prev, latch_scp, sel_mpc_zero, latch_mpc                            |
| 14     | input              | sel_sp_next, latch_sp, sel_mpc_next, latch_mpc                              |
| 15     |                    | sel_sreg_tos, latch_sreg, sel_mpc_next, latch_mpc                           |
| 16     |                    | sel_tos_input, latch_tos, sel_pc_next, latch_pc, sel_mpc_zero, latch_mpc    |
| 17     | output             | write_io, sel_pc_next, latch_pc, sel_mpc_zero, latch_mpc                    |
| 18     | pop                | sel_tos_sreg, latch_tos, sel_mp_next, latch_mpc                             |
| 19     |                    | sel_sp_prev, latch_sp, sel_pc_next, latch_pc, sel_mpc_zero, latch_mpc       |
| 20     | swap               | latch_swr, sel_tos_sreg, latch_tos, sel_mpc_next, latch_mpc                 |
| 21     |                    | sel_sreg_swr, latch_sreg, sel_pc_next, sel_mpc_zero, latch_pc, latch_mpc    |
| 22     | add                | latch_swr, sel_mpc_next, latch_mpc                                          |
| 23     |                    | alu_add, sel_tos_alu, latch_tos, sel_sp_next, latch_sp, sel_mpc_next,latch_mpc |
| 24     |                    | sel_sreg_swr, latch_sreg, sel_pc_next, latch_pc, sel_mpc_zero, latch_mpc    |
| 25     | sub                | latch_swr, sel_mpc_next, latch_mpc                                          |
| 26     |                    | alu_sub, sel_tos_alu, latch_tos, sel_sp_next, latch_sp, sel_mpc_next,latch_mpc |
| 27     |                    | sel_sreg_swr, latch_sreg, sel_pc_next, latch_pc, sel_mpc_zero, latch_mpc    |
| 28     | mul                | latch_swr, sel_mpc_next, latch_mpc                                          |
| 29     |                    | alu_mul, sel_tos_alu, latch_tos, sel_sp_next, latch_sp, sel_mpc_next,latch_mpc |
| 30     |                    | sel_sreg_swr, latch_sreg, sel_pc_next, latch_pc, sel_mpc_zero, latch_mpc    |
| 31     | div                | latch_swr, sel_mpc_next, latch_mpc                                          |
| 32     |                    | alu_div, sel_tos_alu, latch_tos, sel_sp_next, latch_sp, sel_mpc_next,latch_mpc |
| 33     |                    | sel_sreg_swr, latch_sreg, sel_pc_next, latch_pc, sel_mpc_zero, latch_mpc    |
| 34     | inc                | latch_swr, sel_mpc_next, latch_mpc                                          |
| 35     |                    | alu_inc, sel_tos_alu, latch_tos, sel_sp_next, latch_sp, sel_mpc_next,latch_mpc |
| 36     |                    | sel_sreg_swr, latch_sreg, sel_pc_next, latch_pc, sel_mpc_zero, latch_mpc    |
| 37     | dec                | latch_swr, sel_mpc_next, latch_mpc                                          |
| 38     |                    | alu_dec, sel_tos_alu, latch_tos, sel_sp_next, latch_sp, sel_mpc_next,latch_mpc |
| 39     |                    | sel_sreg_swr, latch_sreg, sel_pc_next, latch_pc, sel_mpc_zero, latch_mpc    |
| 40     | load               | latch_swr, sel_next_sp, latch_sp, sel_mpc_next, latch_mpc |
| 41     |                    | sel_sreg_swr, sel_tos_data_mem, latch_tos, latch_sreg, sel_pc_next, latch_pc, sel_mpc_zero, latch_mpc    |
| 42     | store              | write_dm, sel_pc_next, latch_pc, sel_mpc_zero, latch_mpc                    |

**Сопоставление сигнала биту в машинном слове:**

| Номер бита |           Сигнал |
|------------|------------------|
|          0 |         latch_sp |
|          1 |        latch_swr |
|          2 |        latch_tos |
|          3 |         write_dm |
|          4 |         write_io |
|          5 |       latch_sreg |
|          6 |      sel_sp_next |
|          7 |      sel_sp_prev |
|          8 |     sel_sreg_swr |
|          9 |     sel_sreg_tos |
|         10 |         latch_pc |
|         11 |        latch_mpc |
|         12 |        latch_scp |
|         13 |     latch_callst |
|         14 |     sel_tos_sreg |
|         15 | sel_tos_data_mem |
|         16 |      sel_tos_alu |
|         17 |    sel_tos_input |
|         18 |   sel_tos_cu_arg |
|         19 |     sel_mpc_zero |
|         20 |   sel_mpc_opcode |
|         21 |     sel_mpc_next |
|         22 |     sel_scp_next |
|         23 |     sel_scp_prev |
|         24 |           sel_pc |
|         25 |              alu |
|         26 |                  |
|         27 |                  |
|         28 |         jmp_type |
|         29 |                  |
|         30 |                  |

В сумме сигналов в Data Path и Control Unit = **37**  
Если операции ALU кодировать не 6-ю битами (для кажой операции один бит, где 1 - есть сигнал 0 - нет), а 3-мя битами (`000` - нет сигнала, `001` - сумма, `010` - вычитание, `011` - умножение, `100` - деление, `101` - инкремент, `110` - декремент), и sel_jmp_type кодировать 3-мя битами, а не 7-ю (`000` - нет сигнала, `001` - sel_jmp, `010` - sel_js, `011` - sel_jns, `100` - sel_jz, `101` - sel_jnz, `110` - sel_ret, `111` - sel_next) то получится, что необходимо **30** бит для кодирования микроинструкции

## Транслятор

Интерфейс командной строки: `python3 translator.py <input_file> <target_data_file> <target_program_file>`

Первый аргумент - путь до файла с исходным кодом, второй аргумент - путь до файла, куда будут записаны массивы данных, инициализированные в пользовательской программе, в бианрном виде, третий аргумент - путь до файла, куда будут записаны инструкции в бинарном виде.  
Немного видоизменил интерфейс командной строки в связи с Гарвардской архитектурой процессора.

Реализация транслятора: [translator.py](./translator.py)

Трансляция секции `.data`:
- Реализована в `get_data`;
- Сначала определяется место в коде, где объявлена секция `.data`;
- Потом лейбл отделяется от данных;
- В `get_codes_from_data` данные преобразуются в последовательность байт:
  - Функция `str2list_int` возвращает массив, в котором строка представляется как массив байт, на позициях одиночных чисел и резервирования - пустые массивы;
  - Функция `get_integers` удалят из данных строки возвращает массив одиночных чисел и резервированной памяти;
  - Далее на пустые места вставляются одиночные числа и массивы резервирования
  - В конце все данные выпрямляются в один итоговый массив
  
Трансляция секции `.text`:
- `translate_stage_1`: инструкции разбиваются на токены, запоминаются номера лейблов. Возвращается высокоуровневая структура, описывающая инструкции;
-`translate_stage_2`: в джампы подставляются номера инструкций в зависимости от лейбла;
- `replace_push_arg`: в `psuh label` заменяются лейблы на адреса в памяти (т.к. Гарвардская архитектура, то 2 и 3 этапы разделены)
- Код из высокоурвневой структуры переводится в бинарный вид в функции `write_code`, определенной в `isa.py`

Правила:
- Не более одного определения секций `.data` и `.text`
- Одиночные числа, объявленные в `.data` должны принимать значения [-2^31; 2^31 - 1];
- Лейбл в секции `.data` задается на той же строке, что и данные. Данные задаются на одной строке;
- Лейбл в секции `.text` задается перед инструкцией, на которую он указывает;
- На одной строке до одной инструкции;

## Модель процессора

Интерфейс командной строки: `python3 machine.py <data_file> <code_file> <input_file>`

Реализация: [machine.py](./machine.py)

### DataPath

![alt text](schemes/DataPath.svg "DataPath")

Регистры:  
- `TOS` -- top of the stack - значение вершины стэка;
- `SP` -- stack pointer - указатель в `Stack Registers` на верхний элемент (не учитывая `TOS`);
- `SWR` -- swap register - регистр, предназначеный для быстрого выполнения операции `swap`. При выполнении `swap` из `TOS` идет значение в `SWR`. Просходит защелкивание `SWR`. Далее переходят данные из `Stack Registers` в `TOS` и защелкиваются там. После этого на вершине `Stack Registers` защелкиваются данные из `SWR`;

Сигналы:
- Защелки:  
  - `latch_sp` -- защелкнуть регистр `sp`. Данные приходят из мультиплексора, который выбирает между увеличить указатель на 1 или уменьшить на 1 в зависимости от типа действия над стэком (push/pop);
  - `latch_swr` -- защелкнуть swap register;
  - `latch_tos` -- защелкнуть top of the stack. В регистр `tos` данные могу прийти из:
    - `ALU`;
    - верхушки `Stack Registers` - например, при `swap`;
    - `Data Memoey` - считывание из памяти;
    - `I/O` - данные из записи.
  - `write_dm` -- запись в `Data Memory`, адрес, по которому будет произведена запись берется из верхушки `Stack Registers`, значение - из `TOS`;   
  - `write_io` -- запись данных из `TOS` в один из портов `I/O`
  - `latch_sreg` -- защелкнуть верхушку `Stack Registers`.
- Мультиплексор:
  - sel_sp -- выбор значения в `sp`: `sel_sp_next`, `sel_sp_prev`
  - sel_tos -- выбор значения в `tos`: `sel_tos_sreg`, `sel_tos_data_mem`, `sel_tos_alu`, `sel_tos_input`, `sel_tos_cu_arg`
  - sel_sreg -- выбор значения в верхушку `Stack Registers`: `sel_sreg_swr`, `sel_sreg_tos`
- ALU:
  - `alu_add` -- складывает правый и левый вход
  - `alu_sub` -- вычитвает и- правого входа левый
  - `alu_mul` -- умножает правый вход на левый
  - `alu_div` -- делит правый вход на левый
  - `alu_inc` -- увеличивает правый вход на 1 (левый игнорирует)
  - `alu_dec` -- уменьшает правый вход на 1 (левый игнорирует)

На схеме используются красные линии, которыми я хотел показать логическую связь двух компонентов (при этом физически они не связаны)

## Control Unit
![alt text](schemes/ControlUnit.svg "ControlUnit")

Регистры:
- `PC` -- program counter - регистр, являющийся указтелем на текущую инструкцию в `Program Memory`
- `mPC` -- регистр, являющийся указателем на текущую микропрограммную инструкцию
- `SCP` -- регистр, указывающий на верхушку стека вызовов

Сигналы:
- Защелки:
  - `latch_pc`
  - `latch_mpc`
  - `latch_scp`
  - `latch_callst` -- защелкнуть верхушку `Call Stack`.
- Мультиплексор:
  - sel_mpc -- выбор значения mPC, полученное из opcode, или 0 (выборка команд), или следующая инструкция микрокода: `sel_mpc_zero`, `sel_mpc_opcode`, `sel_mpc_next`
  - sel_jmp_type -- выбор перехода в соответсвии с микропрограммой и TOS (знак, ноль): `sel_jmp`, `sel_js`, `sel_jns`, `sel_jz`, `sel_jnz`, `sel_ret`, `sel_next`
  - sel_scp -- передвинуть указатель на позицию вверх или в низ в зависимости от операции (push/pop): `sel_scp_next`, `sel_scp_prev`
  - `sel_pc` -- выбор следующей команды

## Тестирование

Тестирование реализовано через golden тесты.  
Директория с тестами: [golden](./golden/)  
Исполняемый файл: [golden_test.py](./golden_test.py)

**CI:**

``` yml
name: Python CI

on:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.9

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Run tests and collect coverage
        run: |
          poetry run coverage run -m pytest .
          poetry run coverage report -m
        env:
          CI: true

  lint:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Check code formatting with Ruff
        run: poetry run ruff format --check .

      - name: Run Ruff linters
        run: poetry run ruff check .
```

### Hello, world
```asm
.data
hello_str: "Hello, world!", 0

.text
_main:
    push hello_str
    cycle:
        load      ;загружаю на вершину стэка значение по адресу вершины стэка
        jz ext    ;если на вершине 0, то переход
        output 1  ;вывод по порту 1 (порт для вывода), 0 - порт для ввода
        pop       ;убрал букву
        inc
        swap
        pop
        jmp cycle ;безусловный переход

    ext:
        hlt       ;завершение

```

### cat

```asm
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
```

### Hello, Alice!

``` asm
.data
question: "What is your name?", 10, 0
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

``` asm
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
```