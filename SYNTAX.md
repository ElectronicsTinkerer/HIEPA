# Syntax Overview for use in Assembly Files

**Postfix Notation**
EX: `{ arg1 arg2 + arg3 - }`
Rules:

* There MUST be whitespace on either side of each token in a postfix expression block

**Preprocessor Macros**
EX: `#define MAC ($12ff + OTHER_MAC) ; comment`
Rules:

* Comments at end of line are ignored
* `#define` is case insensitive (all preprocessor directives are)

**Proper Assembler Macros**

Uses a very similar notation to ACME:
```
; Macro definition
!macro MAC_NAME @arg1 @arg2 {
    lda @arg1
    sta @arg2
}

; Macro usage
    MAC_NAME $50 $60

; Which will assemble as
    lda $50
    sta $60
```

Notes:
* Arguments are optional but must be prepended with a `@`. If there are no arguments, then just don't put them in the definition.
* Macro names must not have spaces
* Macros cannot contain other macros
* Macro expansion does support forward referenced macros
* Macros support local labels. Any labels defined in a macro that start with `__` are considered to be local to the macro's expansion

Want to use the assembler's internal macro stack?
```
; To push onto the stack, use !mpush
!macro MAC_1 {
    ; Stack: 1 2 3 4
    !mpush frame_name [label:]
    ; Stack 1 2 3 4 frame_name
}

; To pop off the stack, use !mpop
!macro MAC_2 {
    ; Stack: 1 2 3 4
    ; Below expands to `jmp 4`
    jmp !mpop frame_name
    ; Stack: 1 2 3
}

; To check if a macro is within another block, use !mtest
!macro MAC_3 {
    ; Stack: 1 2 3 4
    !mtest frame_name
    ; Stack: 1 2 3 4
}

; To peek the top value on the macro stack, use !mpeek
!macro MAC_35 {
    ; Stack: 1 2 3 4:val
    ; Below expands to `jmp val`
    jmp !mpeek
    ; Stack: 1 2 3 4
}

; To peek the top key on the macro stack, use !mpeek_key
!macro MAC_355 {
    ; Stack: 1 2 3 4
    ; below expands to `!if frame_name == 4`
    !if frame_name == !mpeek_key
        ; Stack: 1 2 3 4
        <code>
    !endif
}

; To swap the top two elements on the macro stack, use !mswap
!macro MAC_36 {
    ; Stack: 1 2 3 4
    !mswap
    ; Stack: 1 2 4 3
}

; To remove the top element from the stack without returning its value, use !mdrop
!macro MAC_37 {
    ; Stack: 1 2 3 4
    !mdrop
    ; Stack: 1 2 3
}

; To rotate the top three elements on the stack, use !mrot
!macro MAC_38 {
    ; Stack: 1 2 3 4
    !mrot
    ; Stack: 1 3 4 2
}

; To get a stack element value from an arbitrary index, use !mdupi
!macro MAC_39 {
    ; Stack: 1 2 3 4
    !mdupi 1
    ; Stack: 1 2 3 4 1
    !mdupi 0
    ; Stack: 1 2 3 4 1 1
}

; To print out the macro stack and macro variables during assembly, use !mdump
!macro MAC_40 {
    ; Stack: 1 2:__loop 3 x_val:val
    !mstackdump
    ; Output:
    ; MACRO STACK DUMP:
    ; 1 ................ : 
    ; 2 ................ : __loop
    ; 3 ................ : 
    ; x_val ............ : val
}
```

Want to use temporary assembler variables like #define, but better?
```
!macro MAC_4 {
    !setvar my_var <value>
}
!macro MAC_5 {
    !ifvar my_var == <test value>
        <some code>
    !endif
}
```

How about using conditional expansion of macros?
```
!macro MAC_6 @arg {
    !if @arg == A
        <some code>
    !else
        !ifvar my_var != XL      ; my_var is a macro variable, defined by !setvar
            <some other code>
        !else
            <finally, another option>
        !endif
    !endif
}
```

Need to check if a part of your if structures is reached when it shouldn't?
```
!macro MAC_7 @arg {
    !if @arg == INVALID_VALUE
        !fail [error message]
    !else
        !if @arg == MEH
            !warn The value was just meh.
        !endif
    !endif
}
```

How about viewing the currently defined macro variables?
```
!macro MAC_8 {
    ; Vars: AL:FALSE mem_size:1024
    !mvardump
    ; Output
    ; MACRO VARIABLE DUMP:
    ; AL ............... : FALSE
    ; mem_size ......... : 1024
    ; on line 90 of file myfile.asm
}
```

Notes:
* The stack processor has a check to ensure that a frame name popped off matches the one at the top of the stack
* An optional label can be pushed with a frame name. If provided, then `!mpop` will be replaced by that label's name. The same local label rules apply to this label as well.

**Assembler Enums**

Very similar to the assembler macros:
```
; Enum definition
!enum [ENUM_NAME] [=start_val] {
    UP
    LEFT
    DOWN
    RIGHT
}

; Enum usage with no name given
    lda #up
; If the enum has a name, then the enum's name must also be used
    lda #ENUM_NAME.UP
```

Notes:
* The enum name is optional but if specified, the name must be used to qualify the keys when using them.
* The base starting value is optional. If provided, it must:
  * Start with an `=`
  * Contain no whitespace (so postfix expressions are not allowed)
* If no base starting value is given, the enum will start from 0 and increment by 1 for each key. Otherwise, it will start with the base value and increment from that.

**Hints**

* To avoid the parentheses around a macro from interfering with addressing mode detection (such as indirect addressing), a `~` may be placed directly before an opening parenthesis. EX: `#define MAC ~($12ff)`
* `.byt` and `.byte` encode strings at UTF-8 but `.word` encodes data strings as UTF-16.
* To access the current PC, use `$`

**Number Formats**

| Base | Example   |
| ---- | --------- |
| 2    | %00110101 |
| 8    | &065      |
| 10   | 53        |
| 16   | $35       |

