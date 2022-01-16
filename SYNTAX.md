# Syntax Overview for use in Assembly Files

**Postfix Notation**
EX: `{ arg1 arg2 + arg3 - }`
Rules:

* There MUST be whitespace on either side of each token in a postfix expression block

**Macros**
EX: `#define MAC ($12ff + OTHER_MAC) ; comment`
Rules:

* Comments at end of line are ignored
* `#define` is case insensitive

Hints:

* To avoid the parentheses around a macro from interfering with addressing mode detection (such as indirect addressing), a `~` may be placed directly before an opening parenthesis. EX: `#define MAC ~($12ff)`
