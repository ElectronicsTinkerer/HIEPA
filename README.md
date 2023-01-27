# HIEPA: The Highly InEfficient Python Assembler (for the 65816)

## Features

HIEPA is a semi-advanced macro assembler for the 65816 CPU, written in python. Among its features are:

* Hidden symbols (start with an `_`)
* Symbol table export as an includable header
* Include files
* Preprocessor `ifdef/ifndef /end` guards
* Preprocessor `define/undef`
* Binary, octal, decimal, hexadecimal number bases
* Infix and postfix expressions
* Enums
* An advanced assembly macro preprocessor including:
  - A stack available to the programmer with forth-like operations
  - Warning and failure message macros
  - Local label support (dynamic name generation)
  - Arbitrary number of macro arguments
* C-style comments
* And probably a few other things

## Syntax

Syntax is documented in the `SYNTAX.md` file. Basic assembly similar to other assemblers such as XA65 or DASM since that is what I started writing assembly with.

## License

See `LICENSE`

## Contributing and Disclaimers

Most of the testing has been done in the form of “it assembles the OS for my computer just fine…” and as such, I make absolutely no guarantee that the content generated by the software will be “correct.” Ideally, a series of proper test files should be written with expected output files to compare against. 

With that said, if you or a friend (or foe) find a bug or implement a feature (such as those listed in the `TODO` file) then submit an issue or PR.
