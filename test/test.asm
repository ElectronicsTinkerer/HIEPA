
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
!macro INDEX_8 @g {
    .xs
    sep #$20
    per @g
}

!enum _test =(5+6) {
    l1
    l2
    l3
}

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
    
secondlabel:
    adc #$2673
    adc ($63)
    ldx $29,Y
    adc [%10110101]
    adc __FOO__
    asl <secondlabel
    INDEX_8 secondlabel
    nop
    bra $
    xba
    asl _test.l1