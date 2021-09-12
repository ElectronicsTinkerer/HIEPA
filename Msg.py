
# Message Levels
INFO = 0
WARN = 10
ERROR = 20

def pmsg(level, msg):
    if level == INFO:
        print(f"[INFO] {msg}")
        return
    if level == WARN:
        print(f"[WARN] {msg}")
        return
    if level == ERROR:
        print(f"[ERROR] {msg}")
        exit(-1)

