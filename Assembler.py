
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
    
    print(f"[WARN] Unknown symbol '{sym}' on line {line_num}, going for another pass...")
    needs_another_pass = True
    return SYMVALUNK

def symexists(sym):
    global symbol_table
    return sym in symbol_table

def writerom8(addr, octet):
    if octet > 0xff or octet < 0:  # FIXME ----------------------------------------------------------------------------------
        print(f"[WARN] Value outside range [0..0xff] on line {line_num}")
    global rom_offset
    global rom_contents
    rom_contents[addr-rom_offset] = octet


def writerom16(addr, word):
    if word > 0xffff or word < 0:  # FIXME ----------------------------------------------------------------------------------
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

    try:
        if str[0].isdigit():
            return int(str, base=10)
        elif len(str) > 1:
            if str[0] == "$":
                return int(str[1:], base=16)
            elif str[0] == "%":
                return int(str[1:], base=2)
            elif str[0].lower() == "o":
                return int(str[1:], base=8)
            elif str[0] == "{":
                return parsepostfixnum(str[1:])
            return getsym(str)
        raise ValueError()
    except ValueError:
        print(f"[ERROR] Invalid number format on line {line_num} : {str}")
        exit(-1)

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
                args.append(num2 - num1) # CHECK ORDERING OF OPERANDS -------------------------------------------------------------------------
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
                print(f"arg: {arg} | num: {num}") # DEBUG
                
                # Still waiting for symbol value to be resolved, go for another pass
                if arg == SYMVALUNK:
                    needs_another_pass = True
                    return SYMVALUNK
                
                args.append(arg)

                print(args)
            
    except IndexError:
        print(f"[ERROR] Missing value or extra operation on line {line_num}")
        exit(-1)

    print(f"[ERROR] Unexpected end of expression on line {line_num}")
    exit(-1)

# Parses arguments to an instruction
def parseargs(i, line):
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

    line = line.strip()
    if (line == ""): 
        return 

    sym = ""
    prev_sym = ""

    i = 0
    while i < len(line):
        c = line[i]

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
                        print(
                            f"[ERROR] Unexpected ROM directive on line {line_num}")
                        exit(-1)

                    rom_size = parsenum(line[i+1:])
                    i = len(line)   # Done with line

            # All remaining passes then fill in data to the ROM array
            else:

                # Check for instrucions
                if sym.upper() in Instructions.INSTRUCTIONS:

                    print("YES, found instruction")  # DEBUG
                    parseargs(i, line)

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

                # Unknown
                else:
                    print("Unknown")  # DEBUG
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
        
        while pass_num < 3 or needs_another_pass:
            pass_num += 1
            line_num = 0
            needs_another_pass = False
            print(f"[INFO] *** Starting pass #{pass_num} ***")

            for line in file.readlines():
                line_num += 1
                print(line)
                parseline(line)
                print(f"PC: {pc}")  # DEBUG
                print(f"ROM OFFSET: {rom_offset}")  # DEBUG
                print(f"ROM SIZE: {rom_size}")  # DEBUG
            
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

