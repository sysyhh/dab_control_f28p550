; Stage C independent PARAMS copier, C28 EABI: XAR4=dst, ACC=n, XAR5=src.
; Admitted only for the four B1 parameter lengths (208,168,104,26).
; Destination advances four C28 words per uint32 payload; holes are untouched.
    .sect ".dab_npu_ramfunc:DAB_C_mem_write_fast"
    .global DAB_C_mem_write_fast
    .align 2
DAB_C_mem_write_fast: .asmfunc
    MOVL *SP++,XAR1
    CLRC SXM
    MOVL XAR7,ACC
    ANDB AL,#3
    MOVZ AR6,AL
    MOVL ACC,XAR7
    SFR ACC,2
    MOVZ AR7,AL
    CMPB AL,#0
    B C_copy_tail,EQ
    MOVB XAR0,#8
    MOVB XAR1,#12
    SUBB XAR7,#1
    RPTB C_copy_block_end,AR7
    MOVL ACC,*XAR5++
    MOVL *+XAR4[0],ACC
    MOVL ACC,*XAR5++
    MOVL *+XAR4[4],ACC
    MOVL ACC,*XAR5++
    MOVL *+XAR4[AR0],ACC
    MOVL ACC,*XAR5++
    MOVL *+XAR4[AR1],ACC
    ADDB XAR4,#16
C_copy_block_end:
C_copy_tail:
    MOV AL,AR6
    CMPB AL,#0
    B C_copy_done,EQ
    SUBB XAR6,#1
C_copy_one:
    MOVL ACC,*XAR5++
    MOVL *XAR4,ACC
    ADDB XAR4,#4
    BANZ C_copy_one,AR6--
C_copy_done:
    MOVL XAR1,*--SP
    LRETR
    .endasmfunc
