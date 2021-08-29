
class Instruction:
    def __init__(self, mne, absu=-1, absx=-1, absy=-1, iabs=-1, ilabs=-1, iabsx=-1, drct=-1, drctx=-1, drcty=-1, idrct=-1, ildrct=-1, idrctx=-1, idrcty=-1, ildrcty=-1, immd=-1, impd=-1, lng=-1, longx=-1, rel8=-1, rel16=-1, srcdes=-1, stacks=-1, istacksy=-1):
        self.mne = mne
        self.abs = absu
        self.absx = absx
        self.absy = absy
        self.iabs = iabs
        self.ilabs = ilabs
        self.iabsx = iabsx
        self.iabsx = iabsx
        self.drct = drct
        self.drctx = drctx
        self.drcty = drcty
        self.idrct = idrct
        self.ildrct = ildrct
        self.idrctx = idrctx
        self.idrcty = idrcty
        self.ildrcty = ildrcty
        self.immd = immd
        self.impd = impd
        self.long = lng
        self.longx = longx
        self.rel8 = rel8
        self.rel16 = rel16
        self.srcdes = srcdes
        self.stacks = stacks
        self.istacksy = istacksy

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

INSTRUCTION_SYNTAX = [              "a",        "a,x",      "a,y",      "(a)",      "[a]",      "(a,x)",    "b",        "b,x",      "b,y",      "(b)",      "[b]",      "(b,x)",    "(b),y",    "[b],y",        "#b",       "",     "l",    "l,x",      "r",        "e",        "b,b",      "b,s",      "(b,s),y" ]
INSTRUCTIONS = {
        #                Mnemonic   ABS         ABS,X       ABS,Y       (ABS)       [ABS]       (ABS,X)     DIRECT      DRCT,X      DRCT,Y      (DRCT)      [DRCT]      (DRCT,X)    (DRCT),Y    [DRCT],Y        IMMD        IMPD    LONG    LONG,X      REL8        REL16       SRC,DST     STACK,S     (STACK,S),Y 
    "ADC" : Instruction("ADC",      0x6D,       0x7D,       0x79,       -1,         -1,         -1,         0x65,       0x75,       -1,         0x72,       0x67,       0x61,       0x71,       0x77,           0x69,       -1,     0x6F,    0x7F,      -1,         -1,         -1,         0x63,       0x73        )
}
