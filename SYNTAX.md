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
```

Notes:
* Arguments are optional but must be prepended with a `@`. If there are no arguments, then just don't put them in the definition.
* Macro names must not have spaces
* Macros cannot contain other macros
* Macro expansion does support forward referenced macros


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

