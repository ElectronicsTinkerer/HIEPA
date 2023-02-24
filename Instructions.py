
import re # Regex Comparator

class Instruction:
    def __init__(self, mne, reg, immd=-1, absu=-1, lng=-1, drct=-1, impd=-1, idrcty=-1, ildrcty=-1, idrctx=-1, drctx=-1, drcty=-1, absx=-1, longx=-1, absy=-1, rel8=-1, rel16=-1, iabs=-1, idrct=-1, ildrct=-1, ilabs=-1, iabsx=-1, stacks=-1, istacksy=-1, srcdes=-1):
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
        self.ilabs = ilabs
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

    def __str__(self):
        return self.mne

INSTRUCTIONS = {
    #                   MNE         REG     #       a       al      d       A/imp   (d),y   [d],y   (d,x)   d,x     d,y     a,x     al,x    a,y     r       rl      (a)     (d)     [d]     [a]     (a,x)   d,s     (d,s),y xyz
    "ADC" : Instruction("ADC",      "A",    0x69,   0x6D,   0x6F,   0x65,   -1,     0x71,   0x77,   0x61,   0x75,   -1,     0x7D,   0x7F,   0x79,   -1,     -1,     -1,     0x72,   0x67,   -1,     -1,     0x63,   0x73,   -1  ),
    "AND" : Instruction("AND",      "A",    0x29,   0x2D,   0x2F,   0x25,   -1,     0x31,   0x37,   0x21,   0x35,   -1,     0x3D,   0x3F,   0x39,   -1,     -1,     -1,     0x32,   0x27,   -1,     -1,     0x23,   0x33,   -1  ),
    "ASL" : Instruction("ASL",      "A",    -1,     0x0E,   -1,     0x06,   0x0A,   -1,     -1,     -1,     -1,     0x16,   -1,     0x1E,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "BCC" : Instruction("BCC",      "S",    -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     0x90,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "BCS" : Instruction("BCS",      "S",    -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     0xB0,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "BEQ" : Instruction("BEQ",      "S",    -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     0xF0,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "BIT" : Instruction("BIT",      "A",    0x89,   0x2C,   -1,     0x24,   -1,     -1,     -1,     -1,     0x34,   -1,     0x3c,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "BMI" : Instruction("BMI",      "S",    -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     0x30,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "BNE" : Instruction("BNE",      "S",    -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     0xD0,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "BPL" : Instruction("BPL",      "S",    -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     0x10,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "BRA" : Instruction("BRA",      "S",    -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     0x80,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "BRK" : Instruction("BRK",      "S",    -1,     -1,     -1,     -1,     0x00,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "BRL" : Instruction("BRL",      "S",    -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     0x82,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "BVC" : Instruction("BVC",      "S",    -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     0x50,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "BVS" : Instruction("BVS",      "S",    -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     0x70,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "CLC" : Instruction("CLC",      "S",    -1,     -1,     -1,     -1,     0x18,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "CLD" : Instruction("CLD",      "S",    -1,     -1,     -1,     -1,     0xD8,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "CLI" : Instruction("CLI",      "S",    -1,     -1,     -1,     -1,     0x58,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "CLV" : Instruction("CLV",      "S",    -1,     -1,     -1,     -1,     0xB8,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "CMP" : Instruction("CMP",      "A",    0xC9,   0xCD,   0xCF,   0xC5,   -1,     0xD1,   0xD7,   0xC1,   0xD5,   -1,     0xDD,   0xDF,   0xD9,   -1,     -1,     -1,     0xD2,   0xC7,   -1,     -1,     0xC3,   0xD3,   -1  ),
    "COP" : Instruction("COP",      "S",    -1,     -1,     -1,     0x02,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "CPX" : Instruction("CPX",      "X",    0xE0,   0xEC,   -1,     0xE4,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "CPY" : Instruction("CPY",      "X",    0xC0,   0xCC,   -1,     0xC4,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "DEC" : Instruction("DEC",      "A",    -1,     0xCE,   -1,     0xC6,   0x3A,   -1,     -1,     -1,     0xD6,   -1,     0xDE,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "DEA" : Instruction("DEA",      "A",    -1,     -1,     -1,     -1,     0x3A,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "DEX" : Instruction("DEX",      "X",    -1,     -1,     -1,     -1,     0xCA,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "DEY" : Instruction("DEY",      "X",    -1,     -1,     -1,     -1,     0x88,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "EOR" : Instruction("EOR",      "A",    0x49,   0x4D,   0x4F,   0x45,   -1,     0x51,   0x57,   0x41,   0x55,   -1,     0x5D,   0x5F,   0x59,   -1,     -1,     -1,     0x52,   0x47,   -1,     -1,     0x43,   0x53,   -1  ),
    "INC" : Instruction("INC",      "A",    -1,     0xEE,   -1,     0xE6,   0x1A,   -1,     -1,     -1,     0xF6,   -1,     0xFE,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "INA" : Instruction("INA",      "A",    -1,     -1,     -1,     -1,     0x1A,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "INX" : Instruction("INX",      "X",    -1,     -1,     -1,     -1,     0xE8,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "INY" : Instruction("INY",      "X",    -1,     -1,     -1,     -1,     0xC8,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "JML" : Instruction("JML",      "S",    -1,     -1,     0x5C,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     0xDC,   -1,     -1,     -1,     -1  ),
    "JMP" : Instruction("JMP",      "S",    -1,     0x4C,   0x5C,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     0x6C,   -1,     -1,     0xDC,   0x7C,   -1,     -1,     -1  ),
    "JSL" : Instruction("JSL",      "S",    -1,     -1,     0x22,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "JSR" : Instruction("JSR",      "S",    -1,     0x20,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     0xFC,   -1,     -1,     -1  ),
    "LDA" : Instruction("LDA",      "A",    0xA9,   0xAD,   0xAF,   0xA5,   -1,     0xB1,   0xB7,   0xA1,   0xB5,   -1,     0xBD,   0xBF,   0xB9,   -1,     -1,     -1,     0xB2,   0xA7,   -1,     -1,     0xA3,   0xB3,   -1  ),
    "LDX" : Instruction("LDX",      "X",    0xA2,   0xAE,   -1,     0xA6,   -1,     -1,     -1,     -1,     -1,     0xB6,   -1,     -1,     0xBE,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "LDY" : Instruction("LDY",      "X",    0xA0,   0xAC,   -1,     0xA4,   -1,     -1,     -1,     -1,     0xB4,   -1,     0xBC,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "LSR" : Instruction("LSR",      "A",    -1,     0x4E,   -1,     0x46,   0x4A,   -1,     -1,     -1,     0x56,   -1,     0x5E,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "MVN" : Instruction("MVN",      "S",    -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     0x54),
    "MVP" : Instruction("MVP",      "S",    -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     0x44),
    "NOP" : Instruction("NOP",      "S",    -1,     -1,     -1,     -1,     0xEA,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "ORA" : Instruction("ORA",      "A",    0x09,   0x0D,   0x0F,   0x05,   -1,     0x11,   0x17,   0x01,   0x15,   -1,     0x1D,   0x1F,   0x19,   -1,     -1,     -1,     0x12,   0x07,   -1,     -1,     0x03,   0x13,   -1  ),
    "PEA" : Instruction("PEA",      "S",    -1,     0xF4,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "PEI" : Instruction("PEI",      "S",    -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     0xD4,   -1,     -1,     -1,     -1,     -1,     -1  ),
    "PER" : Instruction("PER",      "S",    -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     0x62,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "PHA" : Instruction("PHA",      "A",    -1,     -1,     -1,     -1,     0x48,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "PHB" : Instruction("PHB",      "S",    -1,     -1,     -1,     -1,     0x8B,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "PHD" : Instruction("PHD",      "S",    -1,     -1,     -1,     -1,     0x0B,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "PHK" : Instruction("PHK",      "S",    -1,     -1,     -1,     -1,     0x4B,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "PHP" : Instruction("PHP",      "S",    -1,     -1,     -1,     -1,     0x08,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "PHX" : Instruction("PHX",      "X",    -1,     -1,     -1,     -1,     0xDA,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "PHY" : Instruction("PHY",      "X",    -1,     -1,     -1,     -1,     0x5A,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "PLA" : Instruction("PLA",      "A",    -1,     -1,     -1,     -1,     0x68,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "PLB" : Instruction("PLB",      "S",    -1,     -1,     -1,     -1,     0xAB,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "PLD" : Instruction("PLD",      "S",    -1,     -1,     -1,     -1,     0x2B,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "PLP" : Instruction("PLP",      "S",    -1,     -1,     -1,     -1,     0x28,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "PLX" : Instruction("PLX",      "X",    -1,     -1,     -1,     -1,     0xFA,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "PLY" : Instruction("PLY",      "X",    -1,     -1,     -1,     -1,     0x7A,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "REP" : Instruction("REP",      "S",    0xC2,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "ROL" : Instruction("ROL",      "A",    -1,     0x2E,   -1,     0x26,   0x2A,   -1,     -1,     -1,     0x36,   -1,     0x3E,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "ROR" : Instruction("ROR",      "A",    -1,     0x6E,   -1,     0x66,   0x6A,   -1,     -1,     -1,     0x76,   -1,     0x7E,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "RTI" : Instruction("RTI",      "S",    -1,     -1,     -1,     -1,     0x40,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "RTL" : Instruction("RTL",      "S",    -1,     -1,     -1,     -1,     0x6B,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "RTS" : Instruction("RTS",      "S",    -1,     -1,     -1,     -1,     0x60,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "SBC" : Instruction("SBC",      "A",    0xE9,   0xED,   0xEF,   0xE5,   -1,     0xF1,   0xF7,   0xE1,   0xF5,   -1,     0xFD,   0xFF,   0xF9,   -1,     -1,     -1,     0xF2,   0xE7,   -1,     -1,     0xE3,   0xF3,   -1  ),
    "SEC" : Instruction("SEC",      "S",    -1,     -1,     -1,     -1,     0x38,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "SED" : Instruction("SED",      "S",    -1,     -1,     -1,     -1,     0xF8,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "SEI" : Instruction("SEI",      "S",    -1,     -1,     -1,     -1,     0x78,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "SEP" : Instruction("SEP",      "S",    0xE2,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "STA" : Instruction("STA",      "A",    -1,     0x8D,   0x8F,   0x85,   -1,     0x91,   0x97,   0x81,   0x95,   -1,     0x9D,   0x9F,   0x99,   -1,     -1,     -1,     0x92,   0x87,   -1,     -1,     0x83,   0x93,   -1  ),
    "STP" : Instruction("STP",      "S",    -1,     -1,     -1,     -1,     0xDB,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "STX" : Instruction("STX",      "X",    -1,     0x8E,   -1,     0x86,   -1,     -1,     -1,     -1,     -1,     0x96,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "STY" : Instruction("STY",      "X",    -1,     0x8C,   -1,     0x84,   -1,     -1,     -1,     -1,     0x94,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "STZ" : Instruction("STZ",      "A",    -1,     0x9C,   -1,     0x64,   -1,     -1,     -1,     -1,     0x74,   -1,     0x9E,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "TAX" : Instruction("TAX",      "A",    -1,     -1,     -1,     -1,     0xAA,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "TAY" : Instruction("TAY",      "A",    -1,     -1,     -1,     -1,     0xA8,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "TCD" : Instruction("TCD",      "S",    -1,     -1,     -1,     -1,     0x5B,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "TCS" : Instruction("TCS",      "S",    -1,     -1,     -1,     -1,     0x1B,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "TDC" : Instruction("TDC",      "S",    -1,     -1,     -1,     -1,     0x7B,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "TRB" : Instruction("TRB",      "A",    -1,     0x1C,   -1,     0x14,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "TSB" : Instruction("TSB",      "A",    -1,     0x0C,   -1,     0x04,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "TSC" : Instruction("TSC",      "A",    -1,     -1,     -1,     -1,     0x3B,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "TSX" : Instruction("TSX",      "X",    -1,     -1,     -1,     -1,     0xBA,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "TXA" : Instruction("TXA",      "A",    -1,     -1,     -1,     -1,     0x8A,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "TXS" : Instruction("TXS",      "X",    -1,     -1,     -1,     -1,     0x9A,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "TXY" : Instruction("TXY",      "X",    -1,     -1,     -1,     -1,     0x9B,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "TYA" : Instruction("TYA",      "X",    -1,     -1,     -1,     -1,     0x98,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "TYX" : Instruction("TYX",      "X",    -1,     -1,     -1,     -1,     0xBB,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "WAI" : Instruction("WAI",      "S",    -1,     -1,     -1,     -1,     0xCB,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "WDM" : Instruction("WDM",      "S",    -1,     -1,     -1,     -1,     0x42,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "XBA" : Instruction("XBA",      "S",    -1,     -1,     -1,     -1,     0xEB,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    "XCE" : Instruction("XCE",      "A",    -1,     -1,     -1,     -1,     0xFB,   -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1  ),
    #                   MNE         REG     #       a       al      d       A/imp   (d),y   [d],y   (d,x)   d,x     d,y     a,x     al,x    a,y     r       rl      (a)     (d)     [d]     [a]     (a,x)   d,s     (d,s),y xyz

    
    
}
