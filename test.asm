
    org $800
    RoM %0001000000000000

firstvar    equ { myvar aprevar myothervar myvar * + - }
aprevar     equ { myvar 3 + }
myvar       equ $20     ; This is a comment
myothervar  .equ $30

mylabel:

    lda #$00

    .org o7754
    ldy #0
    xy16
    ldx #{ myvar 600 + }
    sta ($f050),y

    .dw { 5 myvar 2 * + myothervar - firstvar + }
    .db $40
    .dw $a0f5
    DB $0f, 50, "Hello!", $00
    
    adc #$2673
