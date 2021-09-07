
    org $800

firstvar    equ { myvar aprevar myothervar myvar * + - }
aprevar     equ { myvar 3 + }
myvar       equ $20     ; This is a comment
myothervar  .equ $30

mylabel:
lbl:
    lda #$00
lbl2:
    .org &7754
lbl3:
    ldy #0
    .xl
    ldx #{ firstvar 600 + }
    ldx #<$f001 ; This is another comment!
    sta ($f050),y
    asl !secondlabel

    .word { 5 myvar 2 * + myothervar - firstvar + }
    .byt $40
    .word $a0f5
    .byt $0f, 50, "Hello!", $00
    
secondlabel:
    adc #$2673
    adc ($63)
    ldx $29,Y
    adc [%10110101]
    asl <secondlabel
