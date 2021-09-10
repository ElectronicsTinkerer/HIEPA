
import re # Regex Comparator

class Instruction:
    def __init__(self, mne, reg, immd=-1, absu=-1, lng=-1, drct=-1, impd=-1, idrcty=-1, ildrcty=-1, idrctx=-1, drctx=-1, drcty=-1, absx=-1, longx=-1, absy=-1, rel8=-1, rel16=-1, iabs=-1, idrct=-1, ildrct=-1, iabsx=-1, stacks=-1, istacksy=-1, srcdes=-1):
        self.mne = mne
        self.reg = reg # Register set (A or XY)
        self.immd=immd
        self.absu=absu
        self.lng=lng
        self.drct = drct
        self.impd = impd
        self.idrcty = idrcty
        self.ildrcty = ildrcty
        self.idrctx = idrctx
        self.drctx = drctx
        self.drcty = drcty
        self.absx = absx
        self.longx = longx
        self.absy = absy
        self.rel8 = rel8
        self.rel16 = rel16
        self.iabs = iabs
        self.idrct = idrct
        self.ildrct = ildrct
        self.iabsx = iabsx
        self.stacks = stacks
        self.istacksy = istacksy
        self.srcdes = srcdes

    def __eq__(self, other):
        if (type(other) == Instruction):
            return self.mne == other.mne
        else:
            return self.mne == other

    def __lt__(self, other):
        if (type(other) == Instruction):
            return self.mne < other.mne
        else:
            return self.mne < other

    def __containes__(self, key):
        return key == self.mne

INSTRUCTIONS = {
    #                   MNE         REG     #       a       al      d       A/imp   (d),y   [d],y   (d,x)   d,x     d,y     a,x     al,x    a,y     r       rl      (a)     (d)     [d]     (a,x)   d,s     (d,s),y xyz
    "ADC" : Instruction("ADC",      "A",    0x69,   0x6D,   0x6F,   0x65,   -1,     0x71,   0x77,   0x61,   0x75,   -1,     0x7D,   0x7F,   0x79,   -1,     -1,     -1,     0x72,   0x67,   -1,     0x63,   0x73,   -1  ),
    "AND" : Instruction("AND",      "A",    0x29,   0x2D,   0x2F,   0x25,   -1,     0x31,   0x37,   0x21,   0x35,   -1,     0x3D,   0x3F,   0x39,   -1,     -1,     -1,     0x32,   0x27,   -1,     0x23,   0x33,   -1  ),
    "ASL" : Instruction("ASL",      "A",    -1,     0x0E,   -1,     0x06,   0x0A,   -1,     -1,     -1,     -1,     0x16,   -1,     0x1E,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "BCC" : Instruction("BCC",      "S",    -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     0x90,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "BCS" : Instruction("BCS",      "S",    -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     0xB0,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  )
}
