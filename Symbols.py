
class Symbol:
    def __init__(self, sym, val, exp):
        self.sym = sym 
        self.val = val
        self.exp = exp

    def __eq__(self, other):
        if (type(other) == Symbol):
            return self.sym == other.sym
        else:
            return self.sym == other

    def __lt__(self, other):
        if (type(other) == Symbol):
            return self.sym < other.sym
        else:
            return self.sym < other