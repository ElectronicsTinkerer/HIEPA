
# Local imports
import Instructions
import Symbols

# Libraries
import re

re_symbol_table = {}
un_symbol_table = {}
SYMVALUNK = 0xffffffff

MAX_PASSES = 7

pc = -1
line_num = 0
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


def getsym(sym):
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
    
    print(f"[INFO] Unknown symbol '{sym}' on line {line_num}, going for another pass ...")
    needs_another_pass = True
    return SYMVALUNK

# Attempts to resolve a symbol. If successful, symbol is moved to re_symbol_table
def tryresolvesym(sym):
    global un_symbol_table
    global re_symbol_table

    if sym in re_symbol_table:
        return -1

    if sym not in un_symbol_table:
        print("[ERROR] Internal error, unable to find sym in unresolved table during resolution.\nContact someone (probably me) to fix this!")
        exit(-1)

    exp = un_symbol_table[sym].exp
    val = parsenum(exp)

    if val != SYMVALUNK:
        re_symbol_table[sym] = Symbols.Symbol(sym, val, exp)
        un_symbol_table.pop(sym)
        return 1

    return 0


def writerom8(addr, octet):
    if octet > 0xff or octet < 0:
        print(f"[WARN] Value outside range [0..0xff] on line {line_num}")
    global rom_offset
    global rom_contents
    rom_contents[addr-rom_offset] = octet


def writerom16(addr, word):
    if word > 0xffff or word < 0:
        print(f"[WARN] Value outside range [0..0xffff] on line {line_num}")
    writerom8(addr, word & 0x00ff)           # Lowbyte
    writerom8(addr+1, (word & 0xff00) >> 8)  # Highbyte


# Takes an instruction's address mode value and prints an error (and exits) if the address mode is not valid
# Returns the instruction's opcode value if valid
def checkreturnaddrmode(instruction_mode):
    global line_num
    # print(f"IS {(instruction_mode):04X}") # DEBUG
    if (instruction_mode < 0):
        print(f"[ERROR] Invalid addressing mode on line {line_num}")
        exit(-1)
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
    elif operand[0] in ["!", "|"]:
        mo = 1
        addr_mode_force = 2
    elif operand[0] == ">":
        mo = 1
        addr_mode_force = 3

    val = parsenum(operand[mo:])

    # Value contains an unresolved symbol, assume an addressing mode
    if val == SYMVALUNK:
        if addr_mode_force == 0:
            print(f"[WARN] Forward reference or unresolved symbol on line {line_num}, defaulting to absolute addressing")
        needs_another_pass = True

    returnbytes = []

    if (val < 0x000100 and val >= 0 and addr_mode_force == 0 and instruction_d != -1) or addr_mode_force == 1:
        returnbytes.append(checkreturnaddrmode(instruction_d))
        returnbytes.append(val & 0xff)
    elif (val < 0x010000 and val >= 0x000100 and addr_mode_force == 0 and instruction_a != -1) or addr_mode_force == 2 or (val == SYMVALUNK and instruction_a != -1):
        returnbytes.append(checkreturnaddrmode(instruction_a))
        returnbytes.append((val >> 8) & 0xff)
        returnbytes.append(val & 0xff)
    elif (val <= 0xffffff and val >= 0x010000 and addr_mode_force == 0 and instruction_l != -1) or addr_mode_force == 3:
        returnbytes.append(checkreturnaddrmode(instruction_l))
        returnbytes.append((val >> 16) & 0xff)
        returnbytes.append((val >> 8) & 0xff)
        returnbytes.append(val & 0xff)
    else:
        checkreturnaddrmode(-1)  # Error and exit

    return returnbytes

# Calculates the branch offset for an 8-bit relative operation
def calcrel8(from_addr, to_addr):
    global line_num

    offset = to_addr - from_addr

    if from_addr < to_addr:
        if offset > 0x7F:
            print(f"[ERROR] Branch out of range ({offset:02X} > +0x7F) on line {line_num}")
            exit(-1)
    else:
        if offset < -0x80:
            print(f"[ERROR] Branch out of ranve ({offset:02X} < -0x80) on line {line_num}")
            exit(-1)
    return offset & 0xFFFF


# Calculates the branch offset for an 16-bit relative operation
def calcrel16(from_addr, to_addr):
    global line_num

    offset = to_addr - from_addr

    if from_addr < to_addr:
        if offset > 0x7FFF:
            print(
                f"[ERROR] Branch out of range ({offset:04X} > +0x7FFF) on line {line_num}")
            exit(-1)
    else:
        if offset < -0x8000:
            print(
                f"[ERROR] Branch out of ranve ({offset:04X} < -0x8000) on line {line_num}")
            exit(-1)
    return offset & 0xFFFF


# Returns the value of the number contained in str. Whitespace padding is permitted
def parsenum(str):
    global re_symbol_table
    global line_num

    str = str.strip()
    if len(str) < 1:
        print(f"[ERROR] Expected operand on line {line_num}")
        exit(-1)

    shift = 0
    mask = 0xffffffff
    so = 0          # Selection Offset

    # Check for byte selection operators
    if str[0] == "<":
        so = 1
        mask = 0xff
    elif str[0] == ">":
        so = 1
        shift = 8
        mask = 0xff
    elif str[0] == "^":
        so = 1
        shift = 16
        mask = 0xff

    val = 0
    try:
        if str[so].isdigit():
            val = int(str, base=10)
        elif len(str) > so:
            if str[so] == "$":
                val = int(str[so+1:], base=16)
            elif str[so] == "%":
                val = int(str[so+1:], base=2)
            elif str[so].lower() == "&":
                val = int(str[so+1:], base=8)
            elif str[so] == "{":
                val = parsepostfixnum(str[so+1:])
            else:
                val = getsym(str)
        else:
            raise ValueError()
    except ValueError:
        print(f"[ERROR] Invalid number format on line {line_num} : {str}")
        exit(-1)

    return (val >> shift) & mask


# Returns the result of a prefix-notation expression. String must be terminated with "}"
def parsepostfixnum(str):
    global needs_another_pass
    global line_num

    str = str.strip()
   
    args = []

    try:
        # Go through elements
        for num in str.split(" "):

            # Check for end of expression
            if num == "}":
                val = args.pop()
                if len(args) != 0:
                    print(f"[ERROR] Extra symbols in expression on line {line_num}")
                    exit(-1)
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
            else:
                arg = parsenum(num)
                # print(f"arg: {arg} | num: {num}") # DEBUG
                
                # Still waiting for symbol value to be resolved, go for another pass
                if arg == SYMVALUNK:
                    needs_another_pass = True
                    return SYMVALUNK
                
                args.append(arg)
            
    except IndexError:
        print(f"[ERROR] Missing value or extra operation on line {line_num}")
        exit(-1)

    # TODO: IS THIS NEEDED?????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
    print(f"[ERROR] Unexpected end of expression on line {line_num}")
    exit(-1)


# Parses arguments to an instruction
def parseargs(i, line, sym):
    # print(f"ARGS: {line[i:]}")

    global al
    global xl
    global line_num
    global pc

    operand = line[i:].rsplit(';', 1)[0].strip() # Ignore comments (using rsplit)
    instruction = Instructions.INSTRUCTIONS[sym.upper()]

    # Implied
    if len(operand) == 0:
        return [ instruction.impd ]

    # Immediate addressing
    if operand[0] == "#":

        if instruction.immd == -1:
            checkreturnaddrmode(-1)  # Error and exti

        val = parsenum(operand[1:])

        returnbytes = [ instruction.immd, val & 0xff ]

        # Check if value is 8 or 16 bit
        if (instruction.reg == "A" and al) or (instruction.reg == "XY" and xl):
            returnbytes.append((val >> 8) & 0xff)
        elif val > 0xff:
            print(f"[WARN] Value is > 0xff with 8 bit reg on line {line_num}")

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
            return getopcodebytes(operand[1:match.span()[0]], instruction.idrcty, instruction.iabsy, -1)
        if re.search("\)$", operand):
            return getopcodebytes(operand[1:-1], instruction.idrct, instruction.iabs, -1)
        
        checkreturnaddrmode(-1)  # Error and exit
        
    # Indirect long
    if operand[0] == "[":

        match = re.search("]\W*,\W*(y|Y)$", operand)
        if match:
            return getopcodebytes(operand[1:match.span()[0]], instruction.ildrcty, -1, -1)
        elif re.search("]$", operand):
            return getopcodebytes(operand[1:-1], instruction.ildrct, instruction.ilabs, -1)
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
        return [ instruction.rel8, calcrel8(pc+2, parsenum(operand)) ]

    # Relative long
    if instruction.rel16 != -1:
        return [ instruction.rel16, calcrel16(pc+3, parsenum(operand)) ]

    # Block move
    match = re.search(",", operand)
    if match:
        src_bank = parsenum(operand[:match.span()[0]-1])
        des_bank = parsenum(operand[match.span()[1]:])
        return [instruction.srcdes, src_bank, des_bank ]
        pass

    # Operand must be an address:
    return getopcodebytes(operand, instruction.drct, instruction.absu, instruction.lng)


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
                tpc = parsenum(line[i+1:])
                if pc == -1:    # On first ORG statement, set ROM offset
                    rom_offset = tpc
                elif tpc > rom_offset + rom_size:
                    print(f"[ERROR] ORG directive outside of ROM area on line {line_num}")
                    exit(-1)
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
                nums = line[i+1:].split(",")

                # Go over all values on line
                for num in nums:
                    num = num.strip()

                    # Ignore comments
                    if num[0] == ";":
                        continue

                    # Here's a string literal
                    if num[0] == "\"":

                        for s in bytes(num[1:-1], "utf_8").decode("unicode_escape"):    # Only works with values [0..127]
                            writerom8(pc, ord(s))
                            pc += 1
                    
                    # Here's a direct number
                    else:
                        writerom8(pc, parsenum(num))
                        pc += 1

                i = len(line)   # Done with line

            # DataWord directive
            elif sym.lower() == "word":
                writerom16(pc, parsenum(line[i+1:]))
                pc += 2
                i = len(line)   # Done with line                
        
            # Equate
            elif sym.lower() == "equ":
                exp = line[i:].rsplit(';', 1)[0]
                val = parsenum(exp)
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
                print(f"Unknown: {sym}")  # DEBUG
                prev_sym = sym


            sym = ""

        elif c in [' ', '\t', '.']:
            # Whitespace resets symbol being parsed
            sym = ""
        else:
            # print("ERROR!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")  # DEBUG
            pass
        
        i += 1


def printsymtable():
    global re_symbol_table
    
    print("[INFO] Symbol table:")
    sorted_sym_table = sorted(re_symbol_table.keys())
    for sym in sorted_sym_table:
        val = re_symbol_table[sym].val
        if val == SYMVALUNK:
            print(f"     * {sym.ljust(24)}: ?????????")
        else:
            print(f"     * {sym.ljust(24)}: ${val&0xffffffff:08X}")


if __name__ == "__main__":

    rom_size = parsenum("$8000") # TODO: PARSE CLI ARG for rom size (error if not given)

    for i in range(rom_size):
        rom_contents.append(0)
    
    with open("test.asm", "r") as file:
        
        while pass_num < 2 or needs_another_pass:
            pass_num += 1
            line_num = 0
            needs_another_pass = False
            al = False
            xl = False
            print(f"[INFO] *** Starting pass #{pass_num} ***")

            for line in file.readlines():
                line_num += 1
                # if line.strip() != "": # DEBUG
                #     print(line) # DEBUG
                parseline(line)
                # print(f"PC: {pc}")  # DEBUG
                # print(f"ROM OFFSET: {rom_offset}")  # DEBUG
                # print(f"ROM SIZE: {rom_size}")  # DEBUG
            
            if pass_num == 1:
                rei = 0
                while rei <= MAX_PASSES and len(un_symbol_table) > 0:
                    unsymtbl = un_symbol_table.copy() # Shallow copy
                    for sym in unsymtbl:
                        tryresolvesym(sym)

                    if rei == MAX_PASSES and len(un_symbol_table) > 0:
                        print("[ERROR] Symbol resolver pass limit reached.")
                        exit(-1)

                    rei += 1

            if pass_num == MAX_PASSES:
                print("[ERROR] Allowable passes exhausted, check for recursive or undefined symbols")
                printsymtable()
                exit(-1)

            file.seek(0,0) # Go to start of file for next pass

    # Generate output binary
    with open("output.bin", "wb") as file:
        file.write(bytearray(rom_contents))

    print(f"[INFO] Total Passes: {pass_num}")
    
    printsymtable()

