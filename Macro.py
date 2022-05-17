# Handles the ASM macros and enums

from numpy import block
from FileLine import FileLine
from Msg import *
import re

ASM_MACRO_CHAR = '!'

class Macro:
    def __init__(self, name, lines, args):
        self.name = name
        self.lines = lines
        self.args = args


def process(lines):

    in_mac = False
    macs = []
    in_enum = False
    enum_val = 0
    enum_base = 0
    enum_name = None


    # Perform macro/enum search
    for line in lines:
        content = line.ppline

        # ENUM was found, update its contents
        if in_enum:
            if content == "}":  # Detect end of enum
                in_enum = False
                line.ismacdef = True
            else:               # Otherwise, change the line to be an "EQUate"
                # Detect non-valid symbol characters
                if not re.match(r"^[a-zA-Z0-9_\.]+$", content):
                    pmsg(ERROR, f"Invalid character in symbol name", line)
                else:
                    line.ppline = (
                        f"{enum_name + '.' if enum_name else ''}"
                        f"{line.ppline} .equ {str(enum_base) + ' + ' if enum_base != 0 else ''}{enum_val}"
                    )
                enum_val += 1

        # MACRO was found, update its contents
        if in_mac:
            line.ismacdef = True
            if content == "}":  # Detect end of macro
                in_mac = False
            else:               # Otherwise, add the line to the macro's contents
                macs[-1].lines.append(content)
            continue

        # Found an ENUM, add it to table
        match = re.search(f"^{ASM_MACRO_CHAR}\W*enum", content, flags=re.IGNORECASE)
        if match:
            enum_name = None
            enum_base = 0
            bargs = content[match.span()[1]:].split()

            if len(bargs) < 2:
                pmsg(ERROR, "Expected opening bracket for enum", line)

            # There's args for the enum, then the user specified an enum identifier
            len_bargs = len(bargs)
            if len_bargs > 1:
                found_bracket = False
                for i in range(len_bargs):
                    if found_bracket:
                        pmsg(ERROR, f"Unexpected token '{bargs[i]}' in enum definition", line)
                    elif i == len_bargs - 1 and bargs[i] != '{':
                        pmsg(ERROR, "Expected opening bracket for enum", line)
                    elif bargs[i] == '{':
                        found_bracket = True
                    elif bargs[i][0] == '=':
                        if enum_base != 0:
                            pmsg(ERROR, f"Unexpected token '{bargs[i]}' in enum definition", line)
                        if len(bargs[i]) < 2:
                            pmsg(ERROR, f"Enum base value assignment expected expression", line)
                        enum_base = bargs[i][1:]
                    else:
                        if enum_name != None:
                            pmsg(ERROR, f"Unexpected token '{bargs[i]}' in enum definition", line)

                        if bargs[i][0] == '@':
                            pmsg(WARN, "Enum name does not require '@'. Did you mean to use a macro?", line)
                        enum_name = bargs[i]

            if len_bargs == 1 and bargs[1] != '{':
                pmsg(ERROR, "Missing opening bracket on enum", line)

            in_enum = True
            enum_val = 0
            line.ismacdef = True
            continue

        # Found a MACRO, add it to table
        match = re.search(f"^{ASM_MACRO_CHAR}\W*macro", content, flags=re.IGNORECASE)
        if match:
            macro = content[match.span()[1]:].split(maxsplit=1)
            if len(macro) < 2:
                pmsg(ERROR, "Expected opening bracket for macro", line)

            bargs = macro[1].split()
            args = []
            # There's args for the macro, add them to the list
            len_bargs = len(bargs)
            if len_bargs > 1:
                found_bracket = False
                for i in range(len_bargs):
                    if found_bracket:
                        pmsg(ERROR, f"Unexpected token '{bargs[i]}' in macro definition", line)
                    elif i == len_bargs - 1 and bargs[i] != '{':
                        pmsg(ERROR, "Missing opening bracket on macro", line)
                    elif bargs[i] == '{':
                        found_bracket = True
                    elif bargs[i][0] != '@':
                        pmsg(ERROR, f"Expected @arg, not '{bargs[i]}', in macro definition", line)
                    else:
                        args.append(bargs[i])
            if len_bargs == 1 and macro[1] != '{':
                pmsg(ERROR, "Missing opening bracket on macro", line)
            in_mac = True
            macs.append(Macro(macro[0], [], args))
            line.ismacdef = True
            # print(macro[0], args)  # DEBUG
            continue

    # DEBUG
    # print("MACS FOUND")
    # for mac in macs:
    #     print(mac.name, mac.lines, mac.args)
    # END DEBUG

    # Perform macro/enum replacement
    new_lines = []
    mac_label_num = 0
    mac_stack = []
    mac_vars = {}
    for line in lines:
        new_lines.append(line)

        if line.ismacdef:   # Don't try replacement on macro definition lines (Can't have nested macros)
            continue

        content = line.ppline
        for mac in macs:
            # if line is a macro, perform a replacement
            if re.search(rf'\b{mac.name}\b', content):
                parts = content.split(maxsplit=1)
                macro = parts[0]
                # print(mac.args, len(mac.args), len(parts)) # DEBUG

                # Only handle argument substitution if the macro has arguments
                args = []
                if len(mac.args) > 0:
                    if len(parts) < 2:
                        pmsg(ERROR, f"Macro '{mac.name}' expected args but none were given", line)
                    else:
                        # args = parts[1].split() # ','
                        args = re.split("\s+(?![^\(]*\))", parts[1]) # Don't split on whitespace inside single level ()'s
                elif len(mac.args) == 0 and len(parts) > 1:
                    pmsg(ERROR, f"Macro '{mac.name}' expected no arguments but some were given", line)

                if len(args) != len(mac.args):
                    pmsg(ERROR, f"Macro '{mac.name}' expected {len(mac.args)} args, got {len(args)}", line)

                for i in range(len(args)):
                    args[i] = args[i].strip()
                    if ' ' in args[i]:
                        pmsg(WARN, f"Whitespace detected in macro argument '{args[i]}',\n\t this may not be the intended value", line)

                # We now have the args being passed, do the text replacement
                temp_lines = mac.lines.copy()
                for i in range(len(mac.lines)):
                    for j in range(len(mac.args)):
                        temp_lines[i] = re.sub(mac.args[j], repr(args[j])[1:-1], temp_lines[i]) # Note the (terrible) use of repr[1:-1]

                # Find local labels
                local_labels = {}
                for l in temp_lines: # Build up list of defined labels
                    matches = re.findall('__[a-zA-Z0-9_\.]*\W*:', l)
                    if matches:
                        for m in matches:
                            local_labels[m[:-1]] = f"{m[:-1]}_{mac_label_num}"
                            mac_label_num += 1

                # Handle naming of local labels
                for i in range(len(temp_lines)):
                    for l in local_labels.keys():
                        temp_lines[i] = re.sub(rf"\b{l}\b", local_labels[l], temp_lines[i])

                # Handle macro stack and conditional assembly operations
                block_level = 0
                block_use_stack = []
                for i in range(len(temp_lines)):
                    # MPEEK and MPEEK_KEY must come after MPOPD in the order of operations
                    # This is to guarantee the ability to substitute a peeked value into the
                    # other stack operators and for popd to substitute before the substitution
                    # performed by peek

                    # MPOPD - Macro Pop (and Don't care about key)
                    match = re.search(rf"{ASM_MACRO_CHAR}\bmpopd\b", temp_lines[i], flags=re.IGNORECASE)
                    if match:
                        if block_level == 0 or (block_level > 0 and block_use_stack[-1]):
                            args = temp_lines[i][match.span()[1]:].split()
                            if len(mac_stack) == 0:
                                pmsg(ERROR, "Attempted popa from empty macro stack", line)
                            else:
                                val = mac_stack.pop()   # Replace !mpop with a some string
                                s = str(list(val.values())[0])
                                if s == None:
                                    s = ""
                                temp_lines[i] = re.sub(rf"{ASM_MACRO_CHAR}\bmpopd\b", s, temp_lines[i])
                            # continue

                    # MPEEK - Get the top of stack without popping
                    match = re.search(rf"{ASM_MACRO_CHAR}\bmpeek\b", temp_lines[i], flags=re.IGNORECASE)
                    if match:
                        if len(mac_stack) == 0:
                            pmsg(ERROR, "Attempted peek from empty macro stack", line)
                        else:
                            val = mac_stack[-1]
                            temp_lines[i] = re.sub(rf"{ASM_MACRO_CHAR}\bmpeek\b", str(list(val.values())[0]), temp_lines[i])
                        # continue

                    # MPEEK_KEY - Get the top key on the stack without popping
                    match = re.search(rf"{ASM_MACRO_CHAR}\bmpeek_key\b", temp_lines[i], flags=re.IGNORECASE)
                    if match:
                        args = temp_lines[i][match.span()[1]:].split()
                        if len(mac_stack) == 0:
                            pmsg(ERROR, "Attempted peek key from empty macro stack", line)
                        else:
                            val = mac_stack[-1]
                            temp_lines[i] = re.sub(rf"{ASM_MACRO_CHAR}\bmpeek_key\b", str(list(val.keys())[0]), temp_lines[i])
                        # continue

                    # MPOP
                    match = re.search(rf"{ASM_MACRO_CHAR}\bmpop\b", temp_lines[i], flags=re.IGNORECASE)
                    if match:
                        if block_level == 0 or (block_level > 0 and block_use_stack[-1]):
                            args = temp_lines[i][match.span()[1]:].split()
                            if len(args) != 1:
                                pmsg(ERROR, f"Expected 1 argument to !mpop, got {len(args)}", line)
                            elif len(mac_stack) == 0:
                                pmsg(ERROR, "Attempted pop from empty macro stack", line)
                            else:
                                val = mac_stack.pop()
                                if not args[0] in val:
                                    pmsg(ERROR, f"Mismatched macro stack key identifier. Got '{args[0]}' but expected '{list(val.keys())[0]}'", line)
                                elif val[args[0]] == None: # No label given in mpush, don't convert line
                                    temp_lines[i] = f"{temp_lines[i][:match.span()[0]]}"
                                else:   # Replace !mpop with a label
                                    temp_lines[i] = f"{temp_lines[i][:match.span()[0]]}{val[args[0]]}"
                            continue

                    # MPUSH
                    match = re.search(rf"^{ASM_MACRO_CHAR}\bmpush\b", temp_lines[i], flags=re.IGNORECASE)
                    if match:
                        if block_level == 0 or (block_level > 0 and block_use_stack[-1]):
                            args = temp_lines[i][match.span()[1]:].split()
                            len_args = len(args)
                            if len_args < 1 or len_args > 2:
                                pmsg(ERROR, f"Expected 1-2 arguments for !mpush, got {len_args}", line)
                            else:
                                elem = {args[0]:None}
                                if len_args == 2:
                                    elem[args[0]] = args[1] # Assign value to label name
                                mac_stack.append(elem)
                                temp_lines[i] = ""
                            continue

                    # MTEST - Check the top of the stack without popping (basically an ASSERT)
                    match = re.search(rf"{ASM_MACRO_CHAR}\bmtest\b", temp_lines[i], flags=re.IGNORECASE)
                    if match:
                        if block_level == 0 or (block_level > 0 and block_use_stack[-1]):
                            args = temp_lines[i][match.span()[1]:].split()
                            if len(args) != 1:
                                pmsg(ERROR, f"Expected 1 argument to !mtest, got {len(args)}", line)
                            elif len(mac_stack) == 0:
                                pmsg(ERROR, "Attempted test on empty macro stack", line)
                            else:
                                val = mac_stack[-1]
                                if not args[0] in val:
                                    pmsg(ERROR, f"Mismatched macro stack key identifier. Got '{args[0]}' but expected '{list(val.keys())[0]}'", line)
                                else: # Hide line from assembler
                                    temp_lines[i] = ""
                            continue

                    # MROT - Rotate the top three elements on the macro stack ( 1 2 3 ==> 2 3 1)
                    match = re.search(rf"{ASM_MACRO_CHAR}\bmrot\b", temp_lines[i], flags=re.IGNORECASE)
                    if match:
                        if block_level == 0 or (block_level > 0 and block_use_stack[-1]):
                            args = temp_lines[i][match.span()[1]:].split()
                            if len(args) != 0:
                                pmsg(ERROR, f"Expected 0 arguments to !mrot, got {len(args)}", line)
                            elif len(mac_stack) < 3:
                                pmsg(ERROR, "Attempted rotate on short macro stack", line)
                            else:
                                val = mac_stack[-3]
                                mac_stack[-3] = mac_stack[-2]
                                mac_stack[-2] = mac_stack[-1]
                                mac_stack[-1] = val
                                temp_lines[i] = "" # Hide line from assembler
                            continue

                    # MSWAP - Swap the top two elements on the macro stack
                    match = re.search(rf"{ASM_MACRO_CHAR}\bmswap\b", temp_lines[i], flags=re.IGNORECASE)
                    if match:
                        if block_level == 0 or (block_level > 0 and block_use_stack[-1]):
                            args = temp_lines[i][match.span()[1]:].split()
                            if len(args) != 0:
                                pmsg(ERROR, f"Expected 0 arguments to !mswap, got {len(args)}", line)
                            elif len(mac_stack) < 2:
                                pmsg(ERROR, "Attempted swap on short macro stack", line)
                            else:
                                val = mac_stack[-1]
                                mac_stack[-1] = mac_stack[-2]
                                mac_stack[-2] = val
                                temp_lines[i] = "" # Hide line from assembler
                            continue

                    # MDUPI - Duplicate a stack item at an index to the top of the stack
                    match = re.search(rf"{ASM_MACRO_CHAR}\bmdupi\b", temp_lines[i], flags=re.IGNORECASE)
                    if match:
                        if block_level == 0 or (block_level > 0 and block_use_stack[-1]):
                            args = temp_lines[i][match.span()[1]:].split()
                            if len(args) != 1:
                                pmsg(ERROR, f"Expected 1 argument to !mdupi, got {len(args)}", line)
                            if not args[0].isdigit():
                                pmsg(ERROR, f"Expected base-10 number for !mdupi, got '{args[0]}'", line)
                            val = int(args[0], 10)
                            if len(mac_stack) < val+1:
                                pmsg(ERROR, "Attempted dupi on short macro stack", line)
                            else:
                                mac_stack.append(mac_stack[-val-1])
                                temp_lines[i] = "" # Hide line from assembler
                            continue

                    # MDROP - Remove the top element from the macro stack
                    match = re.search(rf"{ASM_MACRO_CHAR}\bmdrop\b", temp_lines[i], flags=re.IGNORECASE)
                    if match:
                        if block_level == 0 or (block_level > 0 and block_use_stack[-1]):
                            args = temp_lines[i][match.span()[1]:].split()
                            if len(args) != 0:
                                pmsg(ERROR, f"Expected 0 arguments to !mdrop, got {len(args)}", line)
                            elif len(mac_stack) == 0:
                                pmsg(ERROR, "Attempted drop from empty macro stack", line)
                            else:
                                mac_stack.pop()
                                temp_lines[i] = ""
                            continue

                    # MSTACKDUMP - Print the entire macro stack
                    match = re.search(rf"{ASM_MACRO_CHAR}\bmstackdump\b", temp_lines[i], flags=re.IGNORECASE)
                    if match:
                        if block_level == 0 or (block_level > 0 and block_use_stack[-1]):
                            args = temp_lines[i][match.span()[1]:].split()
                            if len(args) != 0:
                                pmsg(ERROR, f"Expected 0 arguments to !mstackdump, got {len(args)}", line)

                            dump_text = "MACRO STACK DUMP:\n"
                            for f in mac_stack:
                                key = str(list(f.keys())[0])
                                val = list(f.values())[0]
                                l = len(key)
                                dump_text += f"{key} {(16-l)*'.'} : {val}\n"

                            pmsg(INFO, dump_text, line)

                            temp_lines[i] = ""
                            continue

                    # IF
                    match = re.search(rf"^{ASM_MACRO_CHAR}\bif\b", temp_lines[i], flags=re.IGNORECASE)
                    if match:
                        args = temp_lines[i][match.span()[1]:].split()
                        len_args = len(args)
                        if len_args != 3:
                            print(args, temp_lines[i])
                            pmsg(ERROR, f"Expected 3 arguments to !if, got {len(args)}", line)
                        else:
                            block_level += 1
                            temp_lines[i] = ""
                            if block_level > 1 and not block_use_stack[-1]:
                                block_use_stack.append(False)
                            elif args[1] == "==":
                                if args[0] == args[2]:
                                    block_use_stack.append(True)
                                else:
                                    block_use_stack.append(False)
                            elif args[1] == "!=":
                                if args[0] != args[2]:
                                    block_use_stack.append(True)
                                else:
                                    block_use_stack.append(False)
                            else:
                                pmsg(ERROR, f"Unknown macro comparison operator '{args[1]}'", line)
                        continue

                    # IFVAR
                    match = re.search(rf"^{ASM_MACRO_CHAR}\bifvar\b", temp_lines[i], flags=re.IGNORECASE)
                    if match:
                        args = temp_lines[i][match.span()[1]:].split()
                        len_args = len(args)
                        if len_args != 3:
                            pmsg(ERROR, f"Expected 3 arguments to !ifvar, got {len(args)}", line)
                        else:
                            block_level += 1
                            temp_lines[i] = ""
                            if block_level > 1 and not block_use_stack[-1]:
                                block_use_stack.append(False)
                            else:
                                if args[0] not in mac_vars:
                                    pmsg(WARN, f"Unset macro variable '{args[0]}', defaulting to FALSE", line)
                                    block_use_stack.append(False)
                                else:
                                    if args[1] == "==":
                                        if mac_vars[args[0]] == args[2]:
                                            block_use_stack.append(True)
                                        else:
                                            block_use_stack.append(False)
                                    elif args[1] == "!=":
                                        if mac_vars[args[0]] != args[2]:
                                            block_use_stack.append(True)
                                        else:
                                            block_use_stack.append(False)
                                    else:
                                        pmsg(ERROR, f"Unknown macro comparison operator '{args[1]}'", line)
                        continue

                    # ENDIF
                    match = re.search(rf"^{ASM_MACRO_CHAR}\bendif", temp_lines[i], flags=re.IGNORECASE)
                    if match:
                        args = temp_lines[i][match.span()[1]:].split()
                        len_args = len(args)
                        if len_args != 0:
                            pmsg(ERROR, f"Expected 0 arguments to !endif, got {len(args)}", line)
                        elif block_level == 0:
                            pmsg(ERROR, f"Encountered end of block when not in block", line)
                        else:
                            block_level -= 1
                            block_use_stack.pop()
                            temp_lines[i] = ""
                        continue

                    # ELSE
                    match = re.search(rf"^{ASM_MACRO_CHAR}\belse", temp_lines[i], flags=re.IGNORECASE)
                    if match:
                        args = temp_lines[i][match.span()[1]:].split()
                        len_args = len(args)
                        if len_args != 0:
                            pmsg(ERROR, f"Expected 0 arguments to !else, got {len(args)}", line)
                        elif block_level == 0:
                            pmsg(ERROR, f"Encountered !else when not in block", line)
                        else:
                            temp_lines[i] = ""
                            if block_level == 1 or (block_level > 1 and block_use_stack[-2]):
                                # Invert the use stack value
                                val = not block_use_stack.pop()
                                block_use_stack.append(val)
                        continue

                    # FAIL
                    match = re.search(rf"^{ASM_MACRO_CHAR}\bfail", temp_lines[i], flags=re.IGNORECASE)
                    if match:
                        if block_level == 0 or (block_level > 0 and block_use_stack[-1]):
                            msg = temp_lines[i][match.span()[1]:].strip()
                            if msg != "":
                                pmsg(ERROR, f"Encountered !FAIL\n\tMessage: '{msg}'", line)
                            else:
                                pmsg(ERROR, f"Encountered !FAIL", line)

                    # WARN
                    match = re.search(rf"^{ASM_MACRO_CHAR}\bwarn", temp_lines[i], flags=re.IGNORECASE)
                    if match:
                        if block_level == 0 or (block_level > 0 and block_use_stack[-1]):
                            msg = temp_lines[i][match.span()[1]:].strip()
                            if msg != "":
                                pmsg(WARN, f"Encountered !WARN\n\tMessage: '{msg}'", line)
                            else:
                                pmsg(WARN, f"Encountered !WARN", line)
                            temp_lines[i] = ""
                            continue

                    # SETVAR
                    match = re.search(rf"^{ASM_MACRO_CHAR}\bsetvar", temp_lines[i], flags=re.IGNORECASE)
                    if match:
                        if block_level == 0 or (block_level > 0 and block_use_stack[-1]):
                            args = temp_lines[i][match.span()[1]:].split()
                            len_args = len(args)
                            if len_args != 2:
                                pmsg(ERROR, f"Expected 2 arguments to !setvar, got {len(args)}", line)
                            else:
                                mac_vars[args[0]] = args[1]
                                temp_lines[i] = ""

                    # MVARDUMP - Print all macro variables
                    match = re.search(rf"{ASM_MACRO_CHAR}\bmvardump\b", temp_lines[i], flags=re.IGNORECASE)
                    if match:
                        if block_level == 0 or (block_level > 0 and block_use_stack[-1]):
                            args = temp_lines[i][match.span()[1]:].split()
                            if len(args) != 0:
                                pmsg(ERROR, f"Expected 0 arguments to !mvardump, got {len(args)}", line)

                            dump_text = "MACRO VARIABLE DUMP:\n"
                            for (key, val) in mac_vars.items():
                                l = len(key)
                                dump_text += f"{key} {(16-l)*'.'} : {val}\n"

                            pmsg(INFO, dump_text, line)

                            temp_lines[i] = ""
                            continue

                    # Done checking for structure, now handle including of lines
                    if block_level > 0 and not block_use_stack[-1]:
                        temp_lines[i] = ""

                if block_level != 0:
                    pmsg(ERROR, "Unbalanced macro stack at end", line)

                # Get indentation level of original line (for listing file)
                indent = re.search("^\W*", line.line).span()[1]

                # Handle line replacement for returning to the assembler
                spacing = 32 # Spaces from start of indent block to mac expansion comment
                line.ismacdef = True # Ignore original line in assembler
                line.line = f";{line.line[1:]}"
                for l in temp_lines:
                    if l.strip() == "":
                        continue
                    tline = FileLine.dupfileline(line)
                    tline.ppline = l
                    ind = indent
                    spa = spacing
                    if l[:2] == "__":   # Unindent labels one level
                        ind -= 4
                        spa += 4
                    tline.line = f"{' '*ind}{l}{(spa - len(l))*' '}; MAC expansion of '{mac.name}'"
                    tline.ismacdef = False
                    new_lines.append(tline)

                break # Done with line, move on to the next

    # for line in new_lines:
    #     if not line.ismacdef: print(line.ppline)
    # exit(0)
    return new_lines