from FileLine import FileLine
from Msg import *

import re
import os

# Prepressor directive character
PREPROC_CHAR = '#'
PREPROC_MAX_RECURSION = 7
PREPROC_MAX_NEST = 7

# Preprocessor
pre_defines = {}  # DEFINE, VALUE
pre_recursion_count = 0


# Loads in includes
def preprocess(filename, base_dir="", parentfilename="", parentlinenum=-1):
    global pre_defines
    global pre_recursion_count
    
    if pre_recursion_count > PREPROC_MAX_RECURSION:
        pmsg(ERROR, f"Max preprocessor recursion limit reached, check for recursive includes. Last file: {filename}, parent file: {parentfilename}")
    pre_recursion_count += 1

    file_contents = []

    line_num = 0
    in_multi_comment = False
    stack = [] # False for not included, True for included
    stack.append(True) # Start off including stuff


    try:
        chead, ctail = os.path.split(filename)
        phead, ptail = os.path.split(parentfilename)
        potential_child = os.path.join(phead, ctail)
        if os.path.isfile(potential_child): # Prefer local files over remote ones
            filename = potential_child
        with open(filename, "r") as file:

            for line in file.readlines():
                nomod_line = line # Non-modified line (for use in syntax warning/error messages)

                chr_index = 0
                in_quote = False
                while chr_index < len(line) and (in_quote or line[chr_index] != ';'):
                    if line[chr_index] == "\"" or line[chr_index] == "'":
                        in_quote = not in_quote
                    chr_index += 1
                line = line[:chr_index] # Ignore comments
                # line = line.split(';')[0] # Ignore comments

                line = line.strip()

                line_num += 1

                # Ignore blank lines
                if line == "":
                    continue

                # Other form of single-line comments uses '//'
                if line.startswith("//"):
                    continue

                # */ - MUST be at beginning of line
                if re.search(f"^\*/", line):
                    in_multi_comment = False
                    continue

                # /* - MUST be at beginning of line
                if re.search(f"^/\*", line):
                    if not line.endswith("*/"):
                        in_multi_comment = True
                    continue

                # Ignore anything within a multi-line comment
                if in_multi_comment:
                    continue

                # Remove end-of-line comments
                line = line.split("//")[0]

                # ENDIF
                match = re.search(f"^{PREPROC_CHAR}\W*endif", line, flags=re.IGNORECASE)
                if match:
                    stack.pop()
                    if len(stack) < 1:
                        pmsg(ERROR, f"Extra '{PREPROC_CHAR}endif' encountered on line {line_num} of file '{filename}'")
                    continue

                # IFDEF
                match = re.search(f"^{PREPROC_CHAR}\W*ifdef", line, flags=re.IGNORECASE)
                if match:
                    macro = line[match.span()[1]:].strip()
                    stack.append(macro in pre_defines) # True: exists, False: does not exist
                    continue

                # IFNDEF
                match = re.search(f"^{PREPROC_CHAR}\W*ifndef", line, flags=re.IGNORECASE)
                if match:
                    macro = line[match.span()[1]:].strip()
                    stack.append(macro not in pre_defines)
                    continue

                # Check if we should include this part (if stack says no, skip line)
                if not stack[-1]:
                    continue

                # UNDEF
                match = re.search(f"^{PREPROC_CHAR}\W*undef", line, flags=re.IGNORECASE)
                if match:
                    macro = line[match.span()[1]:].strip()
                    try:
                        pre_defines.pop(macro)
                    except KeyError:
                        pmsg(ERROR, f"Encountered '{PREPROC_CHAR}undef' but macro '{macro}' not defined. Line {line_num} of '{filename}'")
                    continue

                # Check for includes
                match = re.search(f"^{PREPROC_CHAR}\W*include", line, flags=re.IGNORECASE)
                if match:
                    inc_filename = line[match.span()[1]:].strip("\"<> \t")
                    head, tail = os.path.split(filename)
                    if base_dir != "":
                        head = base_dir
                    for inc_line in preprocess(os.path.join(head, inc_filename), parentfilename=filename, parentlinenum=line_num):
                        file_contents.append(inc_line)
                    continue

                # Found a define, add it to table
                match = re.search(f"^{PREPROC_CHAR}\W*define", line, flags=re.IGNORECASE)
                if match:
                    macro = line[match.span()[1]:].split(maxsplit=1)
                    if len(macro) == 0:
                        pmsg(ERROR, f"{PREPROC_CHAR}define encountered with no macro specified on line {line_num} of '{filename}")

                    macro_name = macro[0]
                    macro_val = ""
                    if len(macro) > 1:
                        macro_val = macro[1]

                    if macro_name not in pre_defines:
                        pre_defines[macro_name] = macro_val
                    else:
                        pmsg(ERROR, f"Redefinition of macro '{macro_name}' on line {line_num} of '{filename}'")
                    continue

                # Nothing special, check for macros, expand them, and append line
                # REQUIRES python 3.7+ for dict key ordering (order keys were inserted into dict)
                define_keys = reversed(list(pre_defines.keys()))
                for macro_key in define_keys:
                    line = line.replace(f"{macro_key}", pre_defines[macro_key])
                file_contents.append(FileLine(parentfilename=parentfilename, filename=filename, line_num=line_num, line=nomod_line.rstrip(), ppline=line))


    except FileNotFoundError:
        if parentfilename != "":
            pmsg(ERROR, f"Included file '{filename}' on line {parentlinenum} of '{parentfilename}' not found.")
        else:
            pmsg(ERROR, f"File '{filename}' not found.")
        exit(-1)

    if len(stack) != 1:
        pmsg(ERROR, f"Unbalanced preprocessor macros in file '{filename}'.")

    pre_recursion_count -= 1

    return file_contents
