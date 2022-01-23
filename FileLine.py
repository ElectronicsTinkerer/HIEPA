
class FileLine:
    def __init__(self, parentfilename, filename, line_num, line, ppline, rawbytes=[], addr_mode=0, pc=-1):
        self.parentfilename = parentfilename
        self.filename = filename
        self.line_num = line_num
        self.line = line
        self.ppline = ppline
        self.rawbytes = rawbytes
        self.addr_mode = addr_mode
        self.pc = pc
    def __str__(self):
        return self.line