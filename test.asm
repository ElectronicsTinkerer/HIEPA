
    org $800
    RoM %0001000000000000

firstvar    equ { myvar aprevar myothervar myvar * + - }
aprevar     equ { myvar 3 + }
myvar       equ $20     ; This is a comment
myothervar  .equ $30

mylabel:
lbl:
    lda #$00
lbl2:
    .org o7754
lbl3:
    ldy #0
    xy16
    ldx #{ myvar 600 + }
    ldx <$f001 ; This is another comment!
    sta ($f050),y

    .dw { 5 myvar 2 * + myothervar - firstvar + }
    .db $40
    .dw $a0f5
    DB $0f, 50, "Hello!", $00
    
secondlabel:
    adc #$2673
    adc ($63)
    ldx $29,Y
    adc [%10110101]
    asl <secondlabel
