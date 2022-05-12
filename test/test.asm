
    org $800
;#define OO
firstvar    .equ { myvar aprevar myothervar myvar * + - }
aprevar     .equ { myvar 3 + }
myvar       .equ $20     ; This is a comment
myothervar  .equ $30
    INDEX_16

!macro INDEX_16 {
    .xl
    rep #$20
}
!macro INDEX_8 {
    .xs
    sep #$20
}
!macro BRANCH_TEST @temp {
    inc @temp
    beq __mac_done
    inx
__mac_done:
}
!macro LD_A @val {
    lda #@val
}

!enum _test =(5+6) {
    l1
    l2
    l3
}

!macro IF_EQ {
    !mpush if __end_if:
    bne __end_if
}
!macro END_IF {
    !mpop if
}
!macro BEGIN_AGAIN {
__begin_again:
    !mpush begin_again __begin_again
}

!macro AGAIN {
    jmp !mpop begin_again
}
!macro IN_IF {
    !mpeek if
}

!macro POP @reg {
    !if @reg == A
        pla
    !else 
        !if @reg == X
            plx
    !else
        !if @reg == Y
            ply
    !else
        !fail           ; Invalid reg, halt assembly
    !endif
    !endif
    !endif
}

!macro VAR_SET {
    !setvar MyVar HELLO
}

!macro VAR_IF {
    !ifvar MyVar != HELLO
        nop
    !else
        !ifvar otherVar == Yes
            lda #$0f
        !else
            ldx <$
        !endif
    !endif
}

!macro PUSHPOP {
    !mpush go __go
    !mtest go
    jmp !mpeek go
__go:
;    !mpop __go
} 

    VAR_SET
    POP A
    VAR_IF
    PUSHPOP
mylabel:
lbl:
    lda #$00
lbl2:
    .org &7754
lbl3:
    ldy #0
; #include "test/myotherfile.asm"
#define AM 60
# define XYM 90
#define  __FOO__ { { AM } { XYM } * }
    .xl
    ldx #{ firstvar 600 + }
    ldx #<$f001 ; This is another comment!
    ; sta ($f050),y ; This line should give an invalid address mode error
    asl !secondlabel

    ; lda ( $3000, x ) ; Should also give an invalid address mode error

    .word { 5 myvar 2 * + myothervar - firstvar + }
    .byt $ 
    .word $a0f5
    .byt $0f, 50, "Hello!", $00
    .word secondlabel
    .byte secondlabel
    .byt "\\> prompt"   ; Depreciation warning if onle single '\'
    lda #secondlabel
    lda secondlabel
    INDEX_16
    ldx #$ffff+2
    ldx #1+secondlabel
secondlabel:
    adc #$2673
    adc ($63)
    ldx $29,Y
    adc [%10110101]
    adc __FOO__
    asl <secondlabel
    INDEX_8
    nop
    bra $
    xba
    asl _test.l1
    BRANCH_TEST $00
    BRANCH_TEST %00
    BRANCH_TEST $00
    BRANCH_TEST $ab

    lda ($05),x         ; Should throw warning about potentially invalid addressing mode
    lda ~($05),x        ; Should not throw warning about potentially invalid addressing mode
    lda $05,x           ; Should assemble to the same as the above two liens

    ; clc 5               ; Invalid addressing mode
    jmp 5               ; jmp does not have a dp mode, make sure abs is assumed
    ; ldx #'-'

    BEGIN_AGAIN
        IF_EQ
            lda #50
            IN_IF
        END_IF
        ; IN_IF           ; SHould throw a mismatched stack key identifier error
        nop
    AGAIN
