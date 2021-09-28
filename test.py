
from Assembler import *

print(parseexp("{ $35 &7 (4 -(9*2)+2) - + } + $6 - ($4 * { 6 2 * } )+ $5"))
print(parseexp("5"))
print(parseexp("2+'A'-1"))


def testparseexp(string):

    string = string.strip()

    if string == "":
        return 0
    
