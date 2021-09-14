
#include "test/emma-2/hw.inc"

; Base of the ROM
    ;* = INIT_ROM_BASE
    ORG INIT_ROM_BASE

rom_base:

    /* Future jump table */

    ;org { INIT_ROM_BASE $200 + }
    org $f000
    
reset:
    sei                     ; Disable IRQs
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
    lda #{ ROM_SIZE 1 - }   ; Size of ROM
    mvp 0, 0                ; Stay in bank

    .as
    .xs
    sep #$30               ; 8-bit mode

;    lda #%10101010         ; Setup CA/B2 to pulse output mode
;    sta $ff400c

;    lda #$00               ; Spit something to the lower VIA ports to switch out of PRIVOVR mode (to full system mode)
;    sta { $ff4000 2 + }
;    sta $ff4000
 
;    stz $00
;    stz $01
;delay:
;    dec $00
;    bne delay
;    dec $01
;    bne delay
    
    lda #%01000000         ; Free running T1 mode
    sta $ff400b            ; ACR
    lda #%11000000         ; Enable T1 interrupts
    sta $ff400e            ; IER
    
    .al
    rep #$20
    lda #9997              ; Jiffy timer = 100Hz
    sta $ff4004            ; VIA0 T1 TCL/TCH
    
    .as
    sep #$20
    
    
loop:
    nop
    jmp loop
    
loop_int:
    nop
    jmp loop_int
    
    
/*
 * RESET VECTORS
 */
    
int_cop:
int_cop_n:
int_irq:
int_irq_n:
int_brk_n:
int_abt:
int_abt_n:
    jmp loop_int
int_nmi:
int_nmi_n:
    .as
    sep #$30               ; Reset back to 8 bit regs
    pha
    lda #%11000000
    sta $ff400d            ; Read T1 low order counter to clear interrupt
    pla
    rts
    
    ORG $ffe4
    .word int_cop_n
    .word int_brk_n
    .word int_abt_n
    .word int_nmi_n
    .word 0
    .word int_irq_n
    
    .word 0,0
    .word int_cop
    .word 0
    .word int_abt
    .word int_nmi
    .word reset
    .word int_irq