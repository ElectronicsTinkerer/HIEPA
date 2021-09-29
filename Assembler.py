
# Local imports
import Instructions
import Preprocessor
import Symbols
import Msg
from Msg import *

# Libraries
import csv
import re
import sys, getopt


# CLI options
ignore_info_msg = False # NOT IMPLEMENTED
ignore_warn_msg = False  # NOT IMPLEMENTED

# Assembler
re_symbol_table = {}
un_symbol_table = {}
SYMVALUNK = 0xffffffff
# MATH_OPS = ("+", "-", "*", "/", "%", "<<", ">>", "|", "&", "^")
MATH_OPS = ("+", "-", "*", "/")
MATH_ALT_OPS = ("%", "|", "&", "^")

MAX_PASSES = 7

pc = -1
line_num = 0
file_contents = []
rom_size = 0
rom_offset = 0
rom_contents = []
pass_num = 0
needs_another_pass = False

# For reg widths
al = False
xl = False

def addsym(sym, val, exp):
    global re_symbol_table
    global un_symbol_table

    if val == SYMVALUNK:
        un_symbol_table[sym] = Symbols.Symbol(sym, val, exp)
    else:
        re_symbol_table[sym] = Symbols.Symbol(sym, val, exp)

        if sym in un_symbol_table:
            un_symbol_table.pop(sym)


def getsym(sym, internal=False):
    # print("SYM: ", sym)
    global needs_another_pass
    global re_symbol_table
    global un_symbol_table
    global line_num

    if sym in re_symbol_table:
        # print(f"Found resolved symbol: {sym}") # DEBUG
        return re_symbol_table[sym].val

    elif sym in un_symbol_table:
        # print(f"Found unresolved symbol: {sym}") # DEBUG
        return un_symbol_table[sym].val
    
    if not internal:
        if not (ignore_info_msg and pass_num == 1):
            pmsg(INFO, f"Unknown symbol '{sym}', going for another pass ... '{file_contents[line_num-1]}'")
        needs_another_pass = True
    return SYMVALUNK


# Returns true if a symbol is in one of the symbol tables
def issym(sym):
    global re_symbol_table
    global un_symbol_table
    return (sym in re_symbol_table) or (sym in un_symbol_table)

# Attempts to resolve a symbol. If successful, symbol is moved to re_symbol_table
def tryresolvesym(sym):
    global un_symbol_table
    global re_symbol_table

    if sym in re_symbol_table:
        return -1

    if sym not in un_symbol_table:
        pmsg(ERROR, f"Internal error, unable to find sym '{sym}' in unresolved table during resolution.\nContact someone (probably me or your neighbor) to fix this!")

    exp = un_symbol_table[sym].exp
    val = parseexp(exp)

    if val != SYMVALUNK:
        re_symbol_table[sym] = Symbols.Symbol(sym, val, exp)
        un_symbol_table.pop(sym)
        return 1

    return 0


def writerom8(addr, octet):
    if octet > 0xff or octet < 0:
        if not (ignore_warn_msg and pass_num == 1):
            pmsg(WARN, f"Value outside range [0..0xff] on line '{file_contents[line_num-1]}'")
    global rom_offset
    global rom_contents
    global rom_size
    if addr >= rom_offset + rom_size:
        pmsg(ERROR, f"Data placed outside of ROM area. Line: '{file_contents[line_num-1]}'")
    rom_contents[addr-rom_offset] = octet


def writerom16(addr, word):
    if word > 0xffff or word < 0:
        if not (ignore_warn_msg and pass_num == 1):
            pmsg(WARN, f"Value outside range [0..0xffff] on line '{file_contents[line_num-1]}'")
    writerom8(addr, word & 0x00ff)           # Lowbyte
    writerom8(addr+1, (word & 0xff00) >> 8)  # Highbyte


# Takes an instruction's address mode value and prints an error (and exits) if the address mode is not valid
# Returns the instruction's opcode value if valid
def checkreturnaddrmode(instruction_mode):
    global line_num
    # print(f"IS {(instruction_mode):04X}") # DEBUG
    if (instruction_mode < 0):
        pmsg(ERROR, f"Invalid addressing mode on line '{file_contents[line_num-1]}'")
    return instruction_mode


# Takes a string and returns the bytes for an instruction based on its addressing mode for an address or immediate data
def getopcodebytes(operand, instruction_d, instruction_a, instruction_l):
    global line_num
    global needs_another_pass

    mo = 0
    addr_mode_force = 0
    if operand[0] == "<":
        mo = 1
        addr_mode_force = 1
    elif operand[0] in ["!"]:#, "|"]: # Not using '|' since it is used for bitwise OR
        mo = 1
        addr_mode_force = 2
    elif operand[0] == ">":
        mo = 1
        addr_mode_force = 3

    # print(operand[mo:])
    val = parseexp(operand[mo:])

    returnbytes = []

    if (val < 0x000100 and val >= 0 and addr_mode_force == 0 and instruction_d != -1) \
            or addr_mode_force == 1 \
            or (val == SYMVALUNK and instruction_a == -1 and instruction_d != -1):
        returnbytes.append(checkreturnaddrmode(instruction_d))
        returnbytes.append(val & 0xff)
    elif (val < 0x010000 and val >= 0x000100 and addr_mode_force == 0 and instruction_a != -1) \
            or addr_mode_force == 2 \
            or (val == SYMVALUNK and instruction_a != -1) \
            or (instruction_d == -1 and instruction_a != -1 and instruction_l == -1): # TODO: Need to tell assembler to force addressing mode on next pass
        returnbytes.append(checkreturnaddrmode(instruction_a))
        returnbytes.append(val & 0xff)
        returnbytes.append((val >> 8) & 0xff)
    elif (val <= 0xffffff and val >= 0x010000 and addr_mode_force == 0 and instruction_l != -1) \
            or addr_mode_force == 3:
        returnbytes.append(checkreturnaddrmode(instruction_l))
        returnbytes.append(val & 0xff)
        returnbytes.append((val >> 8) & 0xff)
        returnbytes.append((val >> 16) & 0xff)
    else:
        checkreturnaddrmode(-1)  # Error and exit

    # Value contains an unresolved symbol, assume an addressing mode
    if val == SYMVALUNK:
        if addr_mode_force == 0 and (val == SYMVALUNK and instruction_a != -1):
            if not (ignore_warn_msg and pass_num == 1):
                pmsg(WARN, f"Forward reference or unresolved symbol, defaulting to absolute addressing. '{file_contents[line_num-1]}'")
        needs_another_pass = True

    return returnbytes

# Calculates the branch offset for an 8-bit relative operation
def calcrel8(from_addr, to_addr):
    global line_num

    offset = to_addr - from_addr

    if from_addr < to_addr:
        if offset > 0x7F:
            pmsg(ERROR, f"Branch out of range ({offset:02X} > +0x7F) on line '{file_contents[line_num-1]}'")
    else:
        if offset < -0x80:
            pmsg(ERROR, f" Branch out of range ({offset:02X} < -0x80) on line '{file_contents[line_num-1]}'")
    return offset & 0xFF


# Calculates the branch offset for an 16-bit relative operation
def calcrel16(from_addr, to_addr):
    global line_num

    offset = to_addr - from_addr

    if from_addr < to_addr:
        if offset > 0x7FFF:
            pmsg(ERROR,
                 f"Branch out of range ({offset:04X} > +0x7FFF) on line '{file_contents[line_num-1]}'")
    else:
        if offset < -0x8000:
            pmsg(ERROR,
                 f"Branch out of range ({offset:04X} < -0x8000) on line '{file_contents[line_num-1]}'")
    return offset & 0xFFFF


# Returns the value of the number contained in str. Whitespace padding is permitted
def parsenum(string):
    global re_symbol_table
    global line_num
    # print(f"PARSENUM: '{string}'")
    string = string.strip()
    if len(string) < 1:
        pmsg(ERROR, f"Expected operand on line '{file_contents[line_num-1]}'")

    shift = 0
    mask = 0xffffffff
    so = 0          # Selection Offset

    # Check for byte selection operators
    if string[0] == "<":
        so = 1
        mask = 0xff
    elif string[0] == ">":
        so = 1
        shift = 8
        mask = 0xff
    elif string[0] == "^":
        so = 1
        shift = 16
        mask = 0xff

    val = 0
    try:
        if string[so].isdigit():
            val = int(string, base=10)
        elif len(string) > so: # and (not strcontains(string, MATH_OPS) or strcontains(string, ["{", "}"])):
            if string[so] == "$":
                val = int(string[so+1:], base=16)
            elif string[so] == "%":
                val = int(string[so+1:], base=2)
            elif string[so]== "&":
                val = int(string[so+1:], base=8)
            # elif string[so] == "{":
            #     val = parsepostfixnum(string[so+1:])
            # elif string[so] == "(":
            #     val = parseexp(string[so:], True)
            elif string[so] == "'" or string[so] == "\"":
                if len(string) > so + 3 and string[so+1] == "\\":
                    val = ord(escapestr(string[so+1:])[0])
                elif len(string) > so + 2:
                    val = ord(string[so+1])
                else:
                    pmsg(ERROR, f"Expression missing closing character on line '{file_contents[line_num-1]}'")
            else:
                val = getsym(string)
        # else:
        #     val = parseexp(string, string[0] == "(")
        else:
            raise ValueError()
        
    except ValueError:
        pmsg(ERROR, f"Invalid number format '{string}' on line '{file_contents[line_num-1]}'")


    # print(f"RET VAL: {(val >> shift) & mask:08x} | STR: '{string}'")
    return (val >> shift) & mask


# Preforms an operation on a string and accumulator, returns the resuls.
# ONLY for use by the parseexp() function
def performop(op, current_str, accumulator):
    # print(f"PerformOP: '{current_str}'")
    # if i < len(str)-1 and ((character == "<" and str[i] == "<") or (character == ">" and str[i] == ">")):
    if op in [">", "<"]:
        op = 2 * op
    
    arg = 0

    if current_str == "":
        return accumulator
    else:
        arg = parsenum(current_str)

        # Still waiting for symbol value to be resolved, go for another pass
        if arg == SYMVALUNK:
            needs_another_pass = True
            return SYMVALUNK
    
    if op == "+":
        return accumulator + parsenum(current_str)
    elif op == "-":
        return accumulator - parsenum(current_str)
    elif op == "*":
        return accumulator * parsenum(current_str)
    elif op == "/":
        return accumulator / parsenum(current_str)
    elif op == "%":
        return accumulator % parsenum(current_str)
    elif op == ">>":
        return accumulator >> parsenum(current_str)
    elif op == "<<":
        return accumulator << parsenum(current_str)
    elif op == "|": # Bitwise OR
        return accumulator | parsenum(current_str)
    elif op == "&":
        return accumulator & parsenum(current_str)
    elif op == "^":
        return accumulator ^ parsenum(current_str)
    elif op == "":
        return parsenum(current_str)

    pmsg(ERROR, f"Unknown operator '{op}' on line '{file_contents[line_num-1]}'")


# Returns true if a character is an operation in a string
def containsop(string, op):
    if op in ("+", "-", "*", "/", "<<", ">>"):
        return op in string
    elif op == "%":
        pass


# Parses a normal expression. Expression ends on a non symbol, ',', or ')' character
def parseexp(string, starts_with_paren=False):
    global needs_another_pass
    global line_num
    global pass_num

    string = string.strip()

    accumulator = getsym(string, True)
    if (accumulator != SYMVALUNK or issym(string)):
            return accumulator

    string += "\n"

    accumulator = 0
    next_op = ""
    current_str = ""
    num_parens = 0
    # op_shift = False

    i = 0
    while i < len(string):
        character = string[i]
        if character != "\n" and character.strip() == "" and not (i > 0 and string[i-1] in ("'", '"')):
            i += 1
            continue

        # op_shift = False
        # if i < len(string)-1 and ((character == "<" and string[i+1] == "<") or (character == ">" and string[i+1] == ">")):
        #     op_shift = True
        #     i += 1

        # Check for end of expression
        if i == len(string) - 1:
            accumulator = performop(next_op, current_str, accumulator)
            if accumulator == SYMVALUNK:
                return SYMVALUNK
            if character == ")":
                num_parens -= 1
            if num_parens != 0:
                pmsg(
                    ERROR, f"Unexpected end of expression on line '{file_contents[line_num-1]}'")
            # print(f"STR: '{string}'\n\tFINAL VALUE: ${accumulator&0xffffffff:08X}")
            return accumulator

        # Perform operations on numbers
        if character in MATH_OPS or (character in MATH_ALT_OPS and i < len(string)-1 and string[i+1].strip() == "") \
            or (character in (">", "<") and i < len(string)-1 and string[i+1] in (">", "<")):

            accumulator = performop(next_op, current_str, accumulator)
            if accumulator == SYMVALUNK:
                return SYMVALUNK
            next_op = character
            current_str = ""
            if character in (">", "<"):
                i += 1

        elif character == "(" and not (i == 0 and starts_with_paren):
            
            current_str = ""
            bcnt = 0
            isave = i
            while i < len(string) and not (string[i] == ")" and bcnt == 1):
                if string[i] == "(":
                    bcnt += 1
                elif string[i] == ")":
                    bcnt -= 1
                i += 1
            
            subxpr = string[isave:i+1]
            next_val = parseexp(subxpr, True)
            accumulator = performop(next_op, str(next_val), accumulator)

            if accumulator == SYMVALUNK:
                return SYMVALUNK
            if i == len(string):
                pmsg(ERROR, f"Expression missing terminating character '{string}' on line '{file_contents[line_num-1]}'")
        elif character == "(":
            num_parens += 1
        elif character == ")":
            num_parens -= 1
        elif character == "{":
            subxpr = string[i+1:]
            next_val = parsepostfixnum(subxpr)
            accumulator = performop(next_op, str(next_val), accumulator)
            if accumulator == SYMVALUNK:
                return SYMVALUNK
            current_str = ""
            bcnt = 0
            while i < len(string) and not (string[i] == "}" and bcnt == 1):
                if string[i] == "{":
                    bcnt += 1
                elif string[i] == "}":
                    bcnt -= 1
                i += 1
            if i == len(string):
                pmsg(ERROR, f"Expression missing terminating character '{string}' on line '{file_contents[line_num-1]}'")
        else:
            current_str += character

        i += 1

    pmsg(ERROR, f"Unexpected end of expression on line '{file_contents[line_num-1]}'")


# Returns the result of a prefix-notation expression. String must be terminated with "}"
def parsepostfixnum(string):
    global needs_another_pass
    global line_num

    # print("POSTFIX: ", string)
    string = string.strip()
   
    args = []

    try:
        # Go through elements
        #for num in str.split(" ")
        nums = string.split(" ")
        i = 0
        while i < len(nums):
            num = nums[i]
            if len(num) == 0:
                i += 1
                continue

            # Check for end of expression
            if num == "}":
                val = args.pop()
                if len(args) != 0:
                    pmsg(ERROR, f"Extra symbols in expression on line '{file_contents[line_num-1]}'")
                return val
            
            # Perform operations on numbers

            if num == "+":
                args.append(args.pop() + args.pop())
            elif num == "-":
                num1 = args.pop()
                num2 = args.pop()
                args.append(num2 - num1)
            elif num == "*":
                args.append(args.pop() * args.pop())
            elif num == "/":
                num1 = args.pop()
                num2 = args.pop()
                args.append(num2 / num1)
            elif num == "%":
                num1 = args.pop()
                num2 = args.pop()
                args.append(num2 % num1)
            elif num == ">>":
                num1 = args.pop()
                num2 = args.pop()
                args.append(num2 >> num1)
            elif num == "<<":
                num1 = args.pop()
                num2 = args.pop()
                args.append(num2 << num1)
            elif num == "|":
                args.append(args.pop() | args.pop())
            elif num == "&":
                args.append(args.pop() & args.pop())
            elif num == "^":
                args.append(args.pop() ^ args.pop())
            elif "(" in num:
                bcnt = 0
                isave = i
                while i < len(nums) and not (")" in nums[i] and bcnt == 1):
                    if "(" in nums[i]:
                        bcnt += 1
                    elif ")" in nums[i]:
                        bcnt -= 1
                    i += 1
                subxpr = " ".join(nums[isave:i+1])
                # print("SUBXPE: ", subxpr)
                arg = parseexp(subxpr, True)
                args.append(arg)

                if i == len(nums):
                    pmsg(ERROR, f"Expression missing terminating character '{string}'")
            elif "{" in num:
                subxpr = " ".join(nums[i+1:])
                arg = parsepostfixnum(subxpr)
                args.append(arg)
                bcnt = 0
                while i < len(nums) and not ("}" in nums[i] and bcnt == 1):
                    if "{" in nums[i]:
                        bcnt += 1
                    elif "}" in nums[i]:
                        bcnt -= 1
                    i += 1
                if i == len(nums):
                    pmsg(ERROR, f"Expression missing terminating character '{string}'")
            elif num in ("'", '"'):
                arg = ord(' '[0])
                args.append(arg)
                i += 1
            else:
                arg = parseexp(num)
                # print(f"arg: {arg} | num: {num}") # DEBUG
                
                # Still waiting for symbol value to be resolved, go for another pass
                if arg == SYMVALUNK:
                    needs_another_pass = True
                    return SYMVALUNK
                
                args.append(arg)

            i += 1
            
    except IndexError:
        pmsg(ERROR, f"Missing value or extra operation on line '{file_contents[line_num-1]}'")

    pmsg(ERROR, f"Unexpected end of expression on line '{file_contents[line_num-1]}'")


# Parses arguments to an instruction
def parseargs(i, line, sym):
    # print(f"ARGS: {line[i:]}")

    global al
    global xl
    global line_num
    global pc

    operand = line[i:].strip()
    instruction = Instructions.INSTRUCTIONS[sym.upper()]

    # Implied
    if len(operand) == 0:
        return [ instruction.impd ]

    # Immediate addressing
    if operand[0] == "#":

        if instruction.immd == -1:
            checkreturnaddrmode(-1)  # Error and exti

        val = parseexp(operand[1:])

        returnbytes = [ instruction.immd, val & 0xff ]

        # Check if value is 8 or 16 bit
        if (instruction.reg == "A" and al) or (instruction.reg == "X" and xl):
            returnbytes.append((val >> 8) & 0xff)
        elif val > 0xff:
            if not (ignore_warn_msg and pass_num == 1 ):
                pmsg(WARN, f"Value is > 0xff with 8 bit reg on line '{file_contents[line_num-1]}'")

        return returnbytes
            
    # Indirect
    if operand[0] == "(":

        match = re.search(",\W*(x|X)\W*\)$", operand)
        if match:
            return getopcodebytes(operand[1:match.span()[0]], instruction.idrctx, instruction.iabsx, -1)
        match = re.search(",\W*(s|S)\W*\)\W*,\W*(y|Y)$", operand)
        if match:
            return getopcodebytes(operand[1:match.span()[0]], instruction.istacksy, -1, -1)
        match = re.search("\)\W*,\W*(y|Y)$", operand)
        if match:
            return getopcodebytes(operand[1:match.span()[0]], instruction.idrcty, -1, -1)
        if re.search("\)$", operand):
            return getopcodebytes(operand[1:-1], instruction.idrct, instruction.iabs, -1)
        
        #checkreturnaddrmode(-1)  # Error and exit
        if not (ignore_warn_msg and pass_num == 1):
            pmsg(WARN, f"Potentially invalid addressing mode specified: '{file_contents[line_num-1]}'")
        
        
    # Indirect long
    if operand[0] == "[":

        match = re.search("]\W*,\W*(y|Y)$", operand)
        if match:
            return getopcodebytes(operand[1:match.span()[0]], instruction.ildrcty, -1, -1)
        elif re.search("]$", operand):
            return getopcodebytes(operand[1:-1], instruction.ildrct, -1, -1)
        else:
            checkreturnaddrmode(-1)  # Error and exit
        
    # Y-indexed
    match = re.search(",\W*(y|Y)$", operand)
    if match:
        return getopcodebytes(operand[:match.span()[0]], instruction.drcty, instruction.absy, -1)
    
    # X-indexed
    match = re.search(",\W*(x|X)$", operand)
    if match:
        return getopcodebytes(operand[:match.span()[0]], instruction.drctx, instruction.absx, instruction.longx)

    # Stack addressing
    match = re.search(",\W*(s|S)$", operand)
    if match:
        return getopcodebytes(operand[:match.span()[0]], instruction.stacks, -1, -1)

    # Relative addressing
    if instruction.rel8 != -1:
        to_addr = parseexp(operand)
        if to_addr == SYMVALUNK:
            to_addr = pc+2
        return [ instruction.rel8, calcrel8(pc+2, to_addr) ]

    # Relative long
    if instruction.rel16 != -1:
        to_addr = parseexp(operand)
        if to_addr == SYMVALUNK:
            to_addr = pc+3
        return [ instruction.rel16, calcrel16(pc+3, to_addr) ]

    # Block move
    match = re.search(",", operand)
    if match:
        src_bank = parseexp(operand[:match.span()[0]])
        des_bank = parseexp(operand[match.span()[1]:])
        return [instruction.srcdes, des_bank, src_bank ]
        pass

    # Operand must be an address:
    return getopcodebytes(operand, instruction.drct, instruction.absu, instruction.lng)


# Escapes a string
def escapestr(string):
    return string.replace("\\r", "\r") \
                .replace("\\n", "\n") \
                .replace("\\t", "\t") \
                .replace("^G", chr(7)) \
                .replace("^H", chr(8)) \
                .replace("^I", chr(9)) \
                .replace("^J", chr(0xA)) \
                .replace("^L", chr(0xC)) \
                .replace("^M", chr(0xD)) \
                .replace("^[", chr(0x1B)) \
                .replace("ESC[", chr(0x1B))


# Parses a string and returns a list of comma-separated elements
def parsecsv(str):

    i = 0
    s = 0
    iq = False
    vals = []

    while i < len(str):
        if (str[i] == "," and not iq) or i == len(str)-1:
            if i == len(str)-1:
                i += 1
            if str[s:i].strip() != "":
                vals.append(escapestr(str[s:i].strip()))
                s = i + 1
            
        elif str[i] == "\"":
            iq = not iq
        elif str[i] == "\\" and len(str) > i+1 and str[i+1] == "\"":
            i += 1
        i += 1

    return vals  
        

# Parses a single line
def parseline(line):
    global pc
    global rom_size
    global rom_offset
    global re_symbol_table
    global line_num
    global pass_num
    global needs_another_pass
    global al
    global xl

    line = line.strip()
    if (line == ""): 
        return 

    sym = ""
    prev_sym = ""

    i = 0
    while i <= len(line):
        if i < len(line):
            c = line[i]
        else: 
            c = ""

        # print(f"Char: {c}\tSymbol: {sym}")
        if c.isalnum() or c == '_':
            sym += c
        elif len(sym) > 0:

            # It is the ORG directive, chnge the PC
            if sym.lower() == "org":
                tpc = parseexp(line[i+1:])
                if pc == -1:    # On first ORG statement, set ROM offset
                    rom_offset = tpc
                elif tpc > rom_offset + rom_size:
                    pmsg(ERROR, f"ORG directive outside of ROM area on line '{file_contents[line_num-1]}'")
                pc = tpc        # Update PC location
                i = len(line)   # Done with line

            # Check for instrucions
            elif sym.upper() in Instructions.INSTRUCTIONS:

                # print("YES, found instruction")  # DEBUG
                for byte in parseargs(i, line, sym):
                    writerom8(pc, byte)
                    pc += 1

                i = len(line)   # Done with line

            # Ignore comments
            elif sym[0] == ";":
                i = len(line)   # Done with line

            # If it's a label, append it to the table
            elif c == ":":
                addsym(sym, pc, pc)
                # print(f"Found Label: {sym} = ${pc:04X}")  # DEBUG

            # DataByte directive
            elif sym.lower() == "byt":
                
                # Allow comma-delimited values
                nums = parsecsv(line[i+1:])

                # Go over all values on line
                for num in nums:
                    num = num.strip()

                    # Here's a string literal
                    if num[0] == "\"":

                        for s in bytes(num[1:-1], "utf_8").decode("unicode_escape"):    # Only works with values [0..127]
                            writerom8(pc, ord(s))
                            pc += 1
                    
                    # Here's a direct number
                    else:
                        writerom8(pc, parseexp(num))
                        pc += 1

                i = len(line)   # Done with line

            # DataWord directive
            elif sym.lower() == "word":
                
                # Allow comma-delimited values
                nums = parsecsv(line[i+1:])

                # Go over all values on line
                for num in nums:
                    num = num.strip()

                    # Here's a string literal
                    if num[0] == "\"":

                        # Only works with values [0..127]?
                        for s in bytes(num[1:-1], "utf_16").decode("unicode_escape"):
                            writerom16(pc, ord(s))
                            pc += 2

                    # Here's a direct number
                    else:
                        writerom16(pc, parseexp(num))
                        pc += 2

                i = len(line)   # Done with line
        
            # Equate
            elif sym.lower() == "equ":
                exp = line[i:]
                val = parseexp(exp)
                addsym(prev_sym, val, exp)
                i = len(line)   # Done with line

            # ROM directive, ignored on pass != 1
            elif sym.lower() == "rom":
                i = len(line)   # Done with line

            # Register width directives
            elif sym.lower() == "al":
                al = True
                i = len(line)   # Done with line
            elif sym.lower() == "xl":
                xl = True
                i = len(line)   # Done with line
            elif sym.lower() == "as":
                al = False
                i = len(line)   # Done with line
            elif sym.lower() == "xs":
                xl = False
                i = len(line)   # Done with line

            # Unknown
            else:
                if prev_sym != "":
                    pmsg(ERROR, f"Unknown symbol '{prev_sym}' on line '{file_contents[line_num-1]}'")
                prev_sym = sym


            sym = ""

        elif c in [' ', '\t', '.']:
            # Whitespace resets symbol being parsed
            sym = ""
        else:
            # print("ERROR!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")  # DEBUG
            pass
        
        i += 1


def printhelp():
    print("               ==== HELP! ====                ")
    print("")
    print("Usage: $ Assembler.py [options]")
    print("")
    print("  -r, --rom <value>    Set the ROM size")
    print("  -a, --asm <filename> Set input filename")
    print("  -o, --out <filename> Set output binary name")
    print("  --o64                Generate o64 format file")
    print("  -i, --ignoreinfo     Ignore info messages on pass 1")
    print("  -w, --ignorewarn     Ignore warnings on pass 1")
    print("")


def printsymtable():
    global re_symbol_table
    
    pmsg(INFO, "Symbol table:")
    sorted_sym_table = sorted(re_symbol_table.keys())
    for sym in sorted_sym_table:
        val = re_symbol_table[sym].val
        if val == SYMVALUNK:
            print(f"     * {sym.ljust(25)}: ?????????")
        else:
            print(f"     * {sym.ljust(25)}: ${val&0xffffffff:08X}")


if __name__ == "__main__":
    argv = sys.argv[1:]

    print("HIEPA: The Highly InEfficient Python Assembler")
    print("              for the 65816 CPU               ")
    print("            Zach Baldwin Fall 2021            ")
    print("")

    if len(sys.argv) == 1:
        printhelp()
        exit(-2)

    format_o64 = False
    rom_size = parseexp("$8000")
    out_file = "output.bin"
    in_file = ""

    try:
        opts, args = getopt.getopt(argv, "r:a:o:iw", ["rom=", "asm=", "out=", "ignoreinfo", "ignorewarn", "o64"])
    except getopt.GetoptError:
        printhelp()
        exit(-2)
    for opt, arg in opts:
        if opt == "--o64":
            format_o64 = True
        elif opt in ("-r", "--rom"):
            rom_size = parseexp(arg)
        elif opt in ("-o", "--out"):
            out_file = arg
        elif opt in ("-i", "--ignoreinfo"):
            ignore_info_msg = True
        elif opt in ("-w", "--ignorewarn"):
            ignore_warn_msg = True
        elif opt in ("-a", "--asm"):
            in_file = arg
        else:
            pmsg(ERROR, "Unknown option. Run without arguments for help menu.")

    if in_file == "":
        printhelp()
        pmsg(ERROR, "I need an input file!")

    if rom_size < 1:
        printhelp()
        pmsg(ERROR, "Rom size must be > 0")

    pmsg(INFO, f"ROM SIZE: {rom_size} bytes.")

    for i in range(rom_size):
        rom_contents.append(0)

    file_contents = Preprocessor.preprocess(in_file)  # Stores the lines of source
    
    while pass_num < 2 or needs_another_pass:
        pass_num += 1
        line_num = 0
        needs_another_pass = False
        al = False
        xl = False
        pmsg(INFO, f"*** Starting pass #{pass_num} ***")

        for line in file_contents:
            line_num += 1
            parseline(line)
        
        if pass_num == 1:
            rei = 0
            while rei <= MAX_PASSES and len(un_symbol_table) > 0:
                unsymtbl = un_symbol_table.copy() # Shallow copy
                for sym in unsymtbl:
                    tryresolvesym(sym)

                if rei == MAX_PASSES and len(un_symbol_table) > 0:
                    pmsg(ERROR, "Symbol resolver pass limit reached.")

                rei += 1

        if pass_num == MAX_PASSES:
            printsymtable()
            pmsg(ERROR, "Allowable passes exhausted, check for recursive or undefined symbols")

    # Generate output binary
    with open(out_file, "wb") as file:
        if format_o64:
            file.write(bytearray([rom_offset & 0xff, (rom_offset >> 8) & 0xff]))
        file.write(bytearray(rom_contents))

    pmsg(INFO, f"Total Passes: {pass_num}")
    
    printsymtable()

    print("=================> DONE! <=================")

