# Handles the ASM macros and enums

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
    in_enum = False
    enum_val = 0
    macs = []


    # Perform macro/enum search
    for line in lines:
        content = line.ppline

        # Detect end of macro
        if in_mac:
            line.ismacdef = True
            if content == "}":
                in_mac = False
            else:
                macs[-1].lines.append(content)
            continue

        # Found an ENUM, add it to table
        # match = re.search(f"^{ASM_MACRO_CHAR}\W*enum", content, flags=re.IGNORECASE)
        # if match:
        #     macro = content[match.span()[1]:].split(maxsplit=1)
        #     print(macro)
        #     in_enum = True
        #     continue


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
                    print(bargs[i])
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
            print(macro[0], args)  # DEBUG
            continue

    # DEBUG
    print("MACS FOUND")
    for mac in macs:
        print(mac.name, mac.lines, mac.args)
    # END DEBUG

    # Perform macro/enum replacement
    new_lines = []
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
                print(mac.args, len(mac.args), len(parts))

                # Only handle argument substitution if the macro has arguments
                args = []
                if len(mac.args) > 0:
                    if len(parts) < 2:
                        pmsg(ERROR, f"Macro '{mac.name}' expected args but none were given", line)
                    else:
                        args = parts[1].split(',')
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
                        temp_lines[i] = re.sub(mac.args[j], args[j], temp_lines[i])

                line.ismacdef = True # Ignore original line in assembler
                line.line = f";{line.line[1:]}"
                for l in temp_lines:
                    tline = FileLine.dupfileline(line)
                    tline.ppline = l
                    tline.line = f"    {l}{(20 - len(l))*' '}; MAC expansion of '{mac.name}'"
                    tline.ismacdef = False
                    new_lines.append(tline)

                break # Done with line, move on to the next
    # exit(0)
    return new_lines