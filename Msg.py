
from colorama import Fore

# Message Levels
INFO = 0
WARN = 10
ERROR = 20

def pmsg(level, msg):
    if level == INFO:
        print(f"{Fore.CYAN}[INFO]{Fore.RESET} {msg}")
        return
    if level == WARN:
        print(f"{Fore.YELLOW}[WARN]{Fore.RESET} {msg}")
        return
    if level == ERROR:
        print(f"{Fore.RED}[ERROR]{Fore.RESET} {msg}")
        exit(-1)

