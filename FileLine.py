class FileLine:
    def __init__(self, parentfilename, filename, line_num, line, ppline, rawbytes=[], addr_mode=0, pc=-1, ismacdef=False):
        self.parentfilename = parentfilename
        self.filename = filename
        self.line_num = line_num
        self.line = line
        self.ppline = ppline
        self.rawbytes = rawbytes
        self.addr_mode = addr_mode
        self.pc = pc
        self.ismacdef = ismacdef

    @classmethod
    def dupfileline(cls, line):
        return cls(line.parentfilename,
                   line.filename,
                   line.line_num,
                   line.line,
                   line.ppline,
                   line.rawbytes,
                   line.addr_mode,
                   line.pc,
                   line.ismacdef)

    def __str__(self):
        return self.line