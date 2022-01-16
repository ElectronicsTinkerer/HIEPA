
from colorama import Fore

# Message Levels
INFO = 0
WARN = 10
ERROR = 20

def pmsg(level, msg, line=None):
    if level == INFO:
        print(f"{Fore.CYAN}[INFO]{Fore.RESET} {msg}", end="")
    elif level == WARN:
        print(f"{Fore.YELLOW}[WARN]{Fore.RESET} {msg}", end="")
    elif level == ERROR:
        print(f"{Fore.RED}[ERROR]{Fore.RESET} {msg}", end="")
    
    if line:
        print(f" on line {line['line_num']} of '{line['fn']}':\n{line['line']}\n Going for another pass ...\n")
    else:
        print()

    if level == ERROR:
        exit(-1)

