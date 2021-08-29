
import Instructions
import Symbols

symbol_table = {}
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
a16 = False
xy16 = False


def addsym(sym, val):
    global symbol_table

    if (sym in symbol_table and symbol_table[sym].val == SYMVALUNK) or (sym not in symbol_table):
        symbol_table[sym] = Symbols.Symbol(sym, val)
        
def getsym(sym):
    global needs_another_pass
    global symbol_table
    global line_num

    if sym in symbol_table:
        print(f"Found symbol: {sym}") # DEBUG
        return symbol_table[sym].val
    
    print(f"[INFO] Unknown symbol '{sym}' on line {line_num}, going for another pass...")
    needs_another_pass = True
    return SYMVALUNK

def symexists(sym):
    global symbol_table
    return sym in symbol_table

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

# Returns the value of the number contained in str. Whitespace padding is permitted
def parsenum(str):
    global symbol_table

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
        elif len(str) > so+1:
            if str[so] == "$":
                val = int(str[so+1:], base=16)
            elif str[so] == "%":
                val = int(str[so+1:], base=2)
            elif str[so].lower() == "o":
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

# Returns the result of a prefix-notation expression. String must be enclosed in "{}"
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

    print(f"[ERROR] Unexpected end of expression on line {line_num}")
    exit(-1)

# Parses arguments to an instruction
def parseargs(i, line, sym):
    print(f"ARGS: {line[i:]}")

    global a16
    global xy16
    global line_num

    operand = line[i:].strip().rsplit(';', 1)[0] # Ignore comments (using rsplit)
    instruction = Instructions.INSTRUCTIONS[sym.upper()]

    # Immedant addressing
    if operand[0] == "#":

        if instruction.immd == -1:
            print(f"[ERROR] Illegal addressing mode on line {line_num}")
            exit(-1)

        val = parsenum(operand[1:])

        print(instruction.immd)

        returnbytes = [ instruction.immd, val & 0xff ]

        # Check if value is 8 or 16 bit
        if (instruction.reg == "A" and a16) or (instruction.reg == "XY" and xy16):
            returnbytes.append((val >> 8) & 0xff)
        elif val > 0xff:
            print(f"[WARN] Value is > 0xff with 8 bit reg on line {line_num}")

        return returnbytes
            
    if operand[0] == "(":
        pass

    # Operand is nust an address:




    # for form in Instructions.INSTRUCTION_FORMAT:
    #     if form.match(operand):
    #         print(f"Found arg format: {form.regex}")

    pass


# Parses a single line
def parseline(line):
    global pc
    global rom_size
    global rom_offset
    global symbol_table
    global line_num
    global pass_num
    global needs_another_pass
    global a16
    global xy16

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

            # First pass only finds the PC start address and ROM size
            elif pass_num == 1:

                # It is the ROM directive
                if sym.lower() == "rom":
                    if (rom_size != 0):
                        print(f"[ERROR] Unexpected ROM directive on line {line_num}")
                        exit(-1)

                    rom_size = parsenum(line[i+1:])
                    i = len(line)   # Done with line

            # All remaining passes then fill in data to the ROM array
            else:
                # Check for instrucions
                if sym.upper() in Instructions.INSTRUCTIONS:

                    print("YES, found instruction")  # DEBUG
                    for byte in parseargs(i, line, sym):
                        writerom8(pc, byte)
                        pc += 1

                # Ignore comments
                elif sym[0] == ";":
                    i = len(line)   # Done with line

                # If it's a label, append it to the table
                elif c == ":":
                    addsym(sym, pc)
                    print(f"Found Label: {sym} = ${pc:04X}")  # DEBUG

                # DataByte directive
                elif sym.lower() == "db":
                    
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
                elif sym.lower() == "dw":
                    writerom16(pc, parsenum(line[i+1:]))
                    pc += 2
                    i = len(line)   # Done with line                
            
                # Equate
                elif sym.lower() == "equ":
                    val = parsenum(line[i:].rsplit(';', 1)[0])
                    addsym(prev_sym, val)
                    i = len(line)   # Done with line

                # ROM directive, ignored on pass != 1
                elif sym.lower() == "rom":
                    i = len(line)   # Done with line

                # Register width directives
                elif sym.lower() == "a16":
                    a16 = True
                    i = len(line)   # Done with line
                elif sym.lower() == "xy16":
                    xy16 = True
                    i = len(line)   # Done with line
                elif sym.lower() == "axy16":
                    a16 = True
                    xy16 = True
                    i = len(line)   # Done with line
                elif sym.lower() == "a8":
                    a16 = False
                    i = len(line)   # Done with line
                elif sym.lower() == "xy8":
                    xy16 = False
                    i = len(line)   # Done with line
                elif sym.lower() == "axy8":
                    a16 = False
                    xy16 = False
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
            print("ERROR!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")  # DEBUG
        
        i += 1

def printsymtable():
    print("[INFO] Symbol table:")
    sorted(symbol_table.keys())
    for sym in symbol_table:
        val = symbol_table[sym].val
        if val == SYMVALUNK:
            print(f"     * {sym.ljust(24)}: ?????????")
        else:
            print(f"     * {sym.ljust(24)}: ${val&0xffffffff:08X}")


if __name__ == "__main__":
    
    with open("test.asm", "r") as file:
        
        while pass_num < 2 or needs_another_pass:
            pass_num += 1
            line_num = 0
            needs_another_pass = False
            a16 = False
            xy16 = False
            print(f"[INFO] *** Starting pass #{pass_num} ***")

            for line in file.readlines():
                line_num += 1
                if line.strip() != "": # DEBUG
                    print(line) # DEBUG
                parseline(line)
                # print(f"PC: {pc}")  # DEBUG
                # print(f"ROM OFFSET: {rom_offset}")  # DEBUG
                # print(f"ROM SIZE: {rom_size}")  # DEBUG
            
            if pass_num == 1:
                for i in range(rom_size):
                    rom_contents.append(0)

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

