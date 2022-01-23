from colorama import Fore

# Message Levels
INFO = 0
WARN = 10
ERROR = 20

# Another PASS needed
APASS = True

def pmsg(level, msg, line=None, apass=False):
    if level == INFO:
        print(f"{Fore.CYAN}[INFO]{Fore.RESET} {msg}", end="")
    elif level == WARN:
        print(f"{Fore.YELLOW}[WARN]{Fore.RESET} {msg}", end="")
    elif level == ERROR:
        print(f"{Fore.RED}[ERROR]{Fore.RESET} {msg}", end="")

    if line:
        print(f" on line {line.line_num} of '{line.filename}':\n{line.line}")
        if apass:
            print(" Going for another pass ...")

    print()

    if level == ERROR:
        exit(-1)
