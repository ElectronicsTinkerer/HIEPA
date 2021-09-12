
#include "test/emma-2/hw.inc"

; Base of the ROM
    ;* = INIT_ROM_BASE
    ORG INIT_ROM_BASE

rom_base:
    clc                     ; Switch to native mode
    xce
    
    lda #$ff                ; Set HWPID to 0 so that we can write to the BANK0-RAM
    sta { $ff4000 3 + }
    lda #$00
    sta { $ff4000 1 + }

    .al               ; 16-bit accumulator and indicies
    .xl
    rep #$30

    ldx #INIT_ROM_BASE      ; Where to start copying
    ldy #INIT_RAM_BASE      ;
    lda #ROM_SIZE           ; Size of ROM
    mvp 0 , 0                 ; Stay in bank

    .as
    .xs
    sep #$30               ; 8-bit mode

    lda #%10101010         ; Setup CA/B2 to pulse output mode
    sta $ff400c

    lda #$00               ; Spit something to the lower VIA ports to switch out of PRIVOVR mode (to full system mode)
    sta { $ff4000 2 + }
    sta $ff4000
    
    
loop:
    nop
    jmp loop


    .byt "Hello!",$00
    
    
    ORG $FFFC
    .byt <rom_base, >rom_base