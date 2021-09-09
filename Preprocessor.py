
import re

# Prepressor directive character
PREPROC_CHAR = '#'
PREPROC_MAX_RECUSION = 7
PREPROC_MAX_NEST = 7

# Preprocessor
pre_defines = {}  # DEFINE, VALUE
pre_recursion_count = 0


# Loads in includes
def preprocess(filename, parentfilename="", parentlinenum=-1):
    global pre_defines
    global pre_recursion_count

    if pre_recursion_count > PREPROC_MAX_RECUSION:
        print("[ERROR] Max preprocessor recusion limit reached, check for recursive includes.")
        exit(-1)
    pre_recursion_count += 1

    file_contents = []

    line_num = 0
    stack = [] # False for not included, True for included
    stack.append(True) # Start off including stuff


    try:
        with open(filename, "r") as file:

            for line in file.readlines():
                line = line.strip()
                line = line.split(';')[0] # Ignore comments

                line_num += 1

                # Ignore blank lines
                if line == "":
                    continue

                # ENDIF
                match = re.search(f"^{PREPROC_CHAR}\W*endif", line, flags=re.IGNORECASE)
                if match:
                    stack.pop()
                    if len(stack) < 1:
                        print(f"[ERROR] Extra '{PREPROC_CHAR}endif' encountered on line {line_num} of file '{filename}'")
                        exit(-1)
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
                        print(f"[ERROR] Encountered '{PREPROC_CHAR}undef' but macro '{macro}' not defined. Line {line_num} of '{filename}'")
                        exit(-1)
                    continue

                # Check for includes
                match = re.search(f"^{PREPROC_CHAR}\W*include", line, flags=re.IGNORECASE)
                if match:
                    inc_filename = line[match.span()[1]:].strip("\"<> \t")
                    for inc_line in preprocess(inc_filename, filename, line_num):
                        file_contents.append(inc_line)
                    continue

                # Found a define, add it to table
                match = re.search(f"^{PREPROC_CHAR}\W*define", line, flags=re.IGNORECASE)
                if match:
                    macro = line[match.span()[1]:].split(maxsplit=1)
                    if len(macro) == 0:
                        print(f"[ERROR] #define encountered with no macro specified on line {line_num} of '{filename}")
                        exit(-1)

                    macro_name = macro[0]
                    macro_val = ""
                    if len(macro) > 1:
                        macro_val = macro[1]

                    if macro_name not in pre_defines:
                        pre_defines[macro_name] = macro_val
                    else:
                        print(f"[ERROR] Redefinition of macro '{macro_name}' on line {line_num} of '{filename}'")
                        exit(-1)
                    continue

                # Nothing special, check for macros, expand them, and append line
                # REQUIRES python 3.7+ for dict key ordering (order keys were inserted into dict)
                define_keys = reversed(list(pre_defines.keys()))
                for macro_key in define_keys: 
                    line = line.replace(f"{macro_key}", pre_defines[macro_key])
                file_contents.append(line)


    except FileNotFoundError:
        if parentfilename != "":
            print(f"[ERROR] Included file '{filename}' on line {parentlinenum} of '{parentfilename}' not found.")
        else:
            print(f"[ERROR] File '{filename}' not found.")
        exit(-1)

    if len(stack) != 1:
        print(f"[ERROR] Unbalanced preprocessor macros in file '{filename}'.")
        exit(-1)

    return file_contents
