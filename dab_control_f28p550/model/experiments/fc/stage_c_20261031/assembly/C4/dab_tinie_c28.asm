;***************************************************************
;* TMS320C2000 G3 C/C++ Codegen                               PC v22.6.2.LTS *
;* Date/Time created: Sat Oct 31 14:47:26 2026                 *
;***************************************************************
	.compiler_opts --abi=eabi --float_support=fpu32 --hll_source=on --mem_model:code=flat --mem_model:data=large --object_format=elf --silicon_errata_fpu1_workaround=on --silicon_version=28 --symdebug:dwarf --symdebug:dwarf_version=4 
	.asg	XAR2, FP

$C$DW$CU	.dwtag  DW_TAG_compile_unit
	.dwattr $C$DW$CU, DW_AT_name("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c")
	.dwattr $C$DW$CU, DW_AT_producer("TI TMS320C2000 G3 C/C++ Codegen PC v22.6.2.LTS Copyright (c) 1996-2018 Texas Instruments Incorporated")
	.dwattr $C$DW$CU, DW_AT_TI_version(0x01)
	.dwattr $C$DW$CU, DW_AT_comp_dir("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8")

$C$DW$1	.dwtag  DW_TAG_subprogram
	.dwattr $C$DW$1, DW_AT_name("Interrupt_disable")
	.dwattr $C$DW$1, DW_AT_linkage_name("Interrupt_disable")
	.dwattr $C$DW$1, DW_AT_declaration
	.dwattr $C$DW$1, DW_AT_external
	.dwattr $C$DW$1, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\interrupt.h")
	.dwattr $C$DW$1, DW_AT_decl_line(0x1dc)
	.dwattr $C$DW$1, DW_AT_decl_column(0x01)
$C$DW$2	.dwtag  DW_TAG_formal_parameter
	.dwattr $C$DW$2, DW_AT_type(*$C$DW$T$20)

	.dwendtag $C$DW$1


$C$DW$3	.dwtag  DW_TAG_subprogram
	.dwattr $C$DW$3, DW_AT_name("Interrupt_enable")
	.dwattr $C$DW$3, DW_AT_linkage_name("Interrupt_enable")
	.dwattr $C$DW$3, DW_AT_declaration
	.dwattr $C$DW$3, DW_AT_external
	.dwattr $C$DW$3, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\interrupt.h")
	.dwattr $C$DW$3, DW_AT_decl_line(0x1c9)
	.dwattr $C$DW$3, DW_AT_decl_column(0x01)
$C$DW$4	.dwtag  DW_TAG_formal_parameter
	.dwattr $C$DW$4, DW_AT_type(*$C$DW$T$20)

	.dwendtag $C$DW$3

	.bss	||dab_npu_loaded_ins||,2,1,1
$C$DW$5	.dwtag  DW_TAG_variable
	.dwattr $C$DW$5, DW_AT_name("dab_npu_loaded_ins")
	.dwattr $C$DW$5, DW_AT_linkage_name("dab_npu_loaded_ins")
	.dwattr $C$DW$5, DW_AT_type(*$C$DW$T$22)
	.dwattr $C$DW$5, DW_AT_location[DW_OP_addr ||dab_npu_loaded_ins||]
	.dwattr $C$DW$5, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c")
	.dwattr $C$DW$5, DW_AT_decl_line(0x9c)
	.dwattr $C$DW$5, DW_AT_decl_column(0x18)

	.bss	||dab_npu_loaded_ins_count||,2,1,1
$C$DW$6	.dwtag  DW_TAG_variable
	.dwattr $C$DW$6, DW_AT_name("dab_npu_loaded_ins_count")
	.dwattr $C$DW$6, DW_AT_linkage_name("dab_npu_loaded_ins_count")
	.dwattr $C$DW$6, DW_AT_type(*$C$DW$T$20)
	.dwattr $C$DW$6, DW_AT_location[DW_OP_addr ||dab_npu_loaded_ins_count||]
	.dwattr $C$DW$6, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c")
	.dwattr $C$DW$6, DW_AT_decl_line(0x9d)
	.dwattr $C$DW$6, DW_AT_decl_column(0x11)


$C$DW$7	.dwtag  DW_TAG_subprogram
	.dwattr $C$DW$7, DW_AT_name("__enable_interrupts")
	.dwattr $C$DW$7, DW_AT_linkage_name("__enable_interrupts")
	.dwattr $C$DW$7, DW_AT_type(*$C$DW$T$11)
	.dwattr $C$DW$7, DW_AT_declaration
	.dwattr $C$DW$7, DW_AT_external
	.dwendtag $C$DW$7


$C$DW$8	.dwtag  DW_TAG_subprogram
	.dwattr $C$DW$8, DW_AT_name("__disable_interrupts")
	.dwattr $C$DW$8, DW_AT_linkage_name("__disable_interrupts")
	.dwattr $C$DW$8, DW_AT_type(*$C$DW$T$11)
	.dwattr $C$DW$8, DW_AT_declaration
	.dwattr $C$DW$8, DW_AT_external
	.dwendtag $C$DW$8


$C$DW$9	.dwtag  DW_TAG_subprogram
	.dwattr $C$DW$9, DW_AT_name("__eallow")
	.dwattr $C$DW$9, DW_AT_linkage_name("__eallow")
	.dwattr $C$DW$9, DW_AT_declaration
	.dwattr $C$DW$9, DW_AT_external
	.dwendtag $C$DW$9


$C$DW$10	.dwtag  DW_TAG_subprogram
	.dwattr $C$DW$10, DW_AT_name("__edis")
	.dwattr $C$DW$10, DW_AT_linkage_name("__edis")
	.dwattr $C$DW$10, DW_AT_declaration
	.dwattr $C$DW$10, DW_AT_external
	.dwendtag $C$DW$10

	.sblock	".bss"
;	E:\Software_Download\ti\ccs2020\ccs\tools\compiler\ti-cgt-c2000_22.6.2.LTS\bin\opt2000.exe C:\\Users\\SY\\AppData\\Local\\Temp\\{13AD9498-3D91-4E87-95D0-F7CA510D298B} C:\\Users\\SY\\AppData\\Local\\Temp\\{D4F94409-B431-4243-84EC-632508759913} 
;	E:\Software_Download\ti\ccs2020\ccs\tools\compiler\ti-cgt-c2000_22.6.2.LTS\bin\acia2000.exe -@C:\\Users\\SY\\AppData\\Local\\Temp\\{B94FF590-6151-4828-A522-FCDA7EF524D9} 
	.sect	".text:TI_NPU_init"
	.clink
	.global	||TI_NPU_init||

$C$DW$11	.dwtag  DW_TAG_subprogram
	.dwattr $C$DW$11, DW_AT_name("TI_NPU_init")
	.dwattr $C$DW$11, DW_AT_low_pc(||TI_NPU_init||)
	.dwattr $C$DW$11, DW_AT_high_pc(0x00)
	.dwattr $C$DW$11, DW_AT_linkage_name("TI_NPU_init")
	.dwattr $C$DW$11, DW_AT_external
	.dwattr $C$DW$11, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c")
	.dwattr $C$DW$11, DW_AT_decl_line(0xee)
	.dwattr $C$DW$11, DW_AT_decl_column(0x06)
	.dwattr $C$DW$11, DW_AT_TI_max_frame_size(-2)
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 239,column 1,is_stmt,address ||TI_NPU_init||,isa 0

	.dwfde $C$DW$CIE, ||TI_NPU_init||

;***************************************************************
;* FNAME: TI_NPU_init                   FR SIZE:   0           *
;*                                                             *
;* FUNCTION ENVIRONMENT                                        *
;*                                                             *
;* FUNCTION PROPERTIES                                         *
;*                            0 Parameter,  0 Auto,  0 SOE     *
;***************************************************************

||TI_NPU_init||:
	.dwcfi	cfa_offset, -2
	.dwcfi	save_reg_to_mem, 26, 0
;*** 240	-----------------------    dab_npu_loaded_ins = NULL;
;*** 241	-----------------------    dab_npu_loaded_ins_count = 0uL;
;** 1453	-----------------------    __eallow();  // [5]
;** 1454	-----------------------    *(volatile unsigned long *)0x5d226uL = *(volatile unsigned long *)0x5d226uL&0xfffeffffuL;  // [5]
;** 1458	-----------------------    asm(" RPT #54 || NOP");  // [5]
;** 1459	-----------------------    __edis();  // [5]
;** 1169	-----------------------    __eallow();  // [4]
;** 1174	-----------------------    *(volatile unsigned long *)0x5d33auL |= 1uL;  // [4]
;** 1175	-----------------------    __edis();  // [4]
;*** 246	-----------------------    asm(" RPT #54 || NOP");
;*** 249	-----------------------    *(volatile unsigned long *)0x54028uL |= 1uL;
;*** 379	-----------------------    *(volatile unsigned *)0xce1uL = 256u;  // [3]
;***  	-----------------------    return;
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 240,column 5,is_stmt,isa 0
        MOVB      XAR6,#0               ; [CPU_ALU] |240| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 241,column 5,is_stmt,isa 0
        MOVB      ACC,#0                ; [CPU_ALU] |241| 
        MOVW      DP,#||dab_npu_loaded_ins|| ; [CPU_ARAU] 
        MOVL      @||dab_npu_loaded_ins_count||,ACC ; [CPU_ALU] |241| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 240,column 5,is_stmt,isa 0
        MOVL      @||dab_npu_loaded_ins||,XAR6 ; [CPU_ALU] |240| 
	.dwpsn	file "E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h",line 1453,column 5,is_stmt,isa 0
        EALLOW    ; [CPU_ALU] |1453| 
	.dwpsn	file "E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h",line 1454,column 5,is_stmt,isa 0
        MOVL      XAR4,#381478          ; [CPU_ARAU] |1454| 
        MOVL      ACC,*+XAR4[0]         ; [CPU_ALU] |1454| 
        AND       AH,#65534             ; [CPU_ALU] |1454| 
        MOVL      *+XAR4[0],ACC         ; [CPU_ALU] |1454| 
 RPT #54 || NOP
	.dwpsn	file "E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h",line 1169,column 5,is_stmt,isa 0
        EALLOW    ; [CPU_ALU] |1169| 
	.dwpsn	file "E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h",line 1174,column 5,is_stmt,isa 0
        MOVB      ACC,#1                ; [CPU_ALU] |1174| 
        MOVL      XAR4,#381754          ; [CPU_ARAU] |1174| 
        OR        *+XAR4[0],AL          ; [CPU_ALU] |1174| 
        OR        *+XAR4[1],AH          ; [CPU_ALU] |1174| 
	.dwpsn	file "E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h",line 1175,column 5,is_stmt,isa 0
        EDIS      ; [CPU_ALU] |1175| 
 RPT #54 || NOP
        SPM       #0                    ; [CPU_ALU] 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 249,column 5,is_stmt,isa 0
        MOVL      XAR4,#344104          ; [CPU_ARAU] |249| 
	.dwpsn	file "E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\interrupt.h",line 379,column 5,is_stmt,isa 0
        MOVL      XAR6,#256             ; [CPU_ALU] |379| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 249,column 5,is_stmt,isa 0
        OR        *+XAR4[0],AL          ; [CPU_ALU] |249| 
        OR        *+XAR4[1],AH          ; [CPU_ALU] |249| 
	.dwpsn	file "E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\interrupt.h",line 379,column 5,is_stmt,isa 0
        MOV       *(0:0x0ce1),AR6       ; [CPU_ALU] |379| 
$C$DW$12	.dwtag  DW_TAG_TI_branch
	.dwattr $C$DW$12, DW_AT_low_pc(0x00)
	.dwattr $C$DW$12, DW_AT_TI_return

        LRETR     ; [CPU_ALU] 
        ; return occurs ; [] 
	.dwattr $C$DW$11, DW_AT_TI_end_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c")
	.dwattr $C$DW$11, DW_AT_TI_end_line(0xfc)
	.dwattr $C$DW$11, DW_AT_TI_end_column(0x01)
	.dwendentry
	.dwendtag $C$DW$11

	.sect	".dab_npu_ramfunc:TINIE_start"
	.clink
	.global	||TINIE_start||

$C$DW$13	.dwtag  DW_TAG_subprogram
	.dwattr $C$DW$13, DW_AT_name("TINIE_start")
	.dwattr $C$DW$13, DW_AT_low_pc(||TINIE_start||)
	.dwattr $C$DW$13, DW_AT_high_pc(0x00)
	.dwattr $C$DW$13, DW_AT_linkage_name("TINIE_start")
	.dwattr $C$DW$13, DW_AT_external
	.dwattr $C$DW$13, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c")
	.dwattr $C$DW$13, DW_AT_decl_line(0xd2)
	.dwattr $C$DW$13, DW_AT_decl_column(0x06)
	.dwattr $C$DW$13, DW_AT_TI_max_frame_size(-2)
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 211,column 1,is_stmt,address ||TINIE_start||,isa 0

	.dwfde $C$DW$CIE, ||TINIE_start||

;***************************************************************
;* FNAME: TINIE_start                   FR SIZE:   0           *
;*                                                             *
;* FUNCTION ENVIRONMENT                                        *
;*                                                             *
;* FUNCTION PROPERTIES                                         *
;*                            0 Parameter,  0 Auto,  0 SOE     *
;***************************************************************

||TINIE_start||:
;* AR4   assigned to mmrs
$C$DW$14	.dwtag  DW_TAG_variable
	.dwattr $C$DW$14, DW_AT_name("mmrs")
	.dwattr $C$DW$14, DW_AT_type(*$C$DW$T$49)
	.dwattr $C$DW$14, DW_AT_location[DW_OP_reg12]

	.dwcfi	cfa_offset, -2
	.dwcfi	save_reg_to_mem, 26, 0
;*** 218	-----------------------    *(mmrs = (volatile unsigned long *)0x54120uL) = 1uL;
;***  	-----------------------    return;
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 218,column 5,is_stmt,isa 0
        MOVB      ACC,#1                ; [CPU_ALU] |218| 
        MOVL      XAR4,#344352          ; [CPU_ARAU] |218| 
        MOVL      *+XAR4[0],ACC         ; [CPU_ALU] |218| 
$C$DW$15	.dwtag  DW_TAG_TI_branch
	.dwattr $C$DW$15, DW_AT_low_pc(0x00)
	.dwattr $C$DW$15, DW_AT_TI_return

        LRETR     ; [CPU_ALU] 
        ; return occurs ; [] 
	.dwattr $C$DW$13, DW_AT_TI_end_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c")
	.dwattr $C$DW$13, DW_AT_TI_end_line(0xdb)
	.dwattr $C$DW$13, DW_AT_TI_end_column(0x01)
	.dwendentry
	.dwendtag $C$DW$13

	.sect	".dab_npu_ramfunc:TINIE_mem_write"
	.clink

$C$DW$16	.dwtag  DW_TAG_subprogram
	.dwattr $C$DW$16, DW_AT_name("TINIE_mem_write")
	.dwattr $C$DW$16, DW_AT_low_pc(||TINIE_mem_write||)
	.dwattr $C$DW$16, DW_AT_high_pc(0x00)
	.dwattr $C$DW$16, DW_AT_linkage_name("TINIE_mem_write")
	.dwattr $C$DW$16, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c")
	.dwattr $C$DW$16, DW_AT_decl_line(0x68)
	.dwattr $C$DW$16, DW_AT_decl_column(0x0d)
	.dwattr $C$DW$16, DW_AT_TI_max_frame_size(-4)
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 105,column 1,is_stmt,address ||TINIE_mem_write||,isa 0

	.dwfde $C$DW$CIE, ||TINIE_mem_write||
$C$DW$17	.dwtag  DW_TAG_formal_parameter
	.dwattr $C$DW$17, DW_AT_name("dst")
	.dwattr $C$DW$17, DW_AT_type(*$C$DW$T$49)
	.dwattr $C$DW$17, DW_AT_location[DW_OP_reg12]

$C$DW$18	.dwtag  DW_TAG_formal_parameter
	.dwattr $C$DW$18, DW_AT_name("num")
	.dwattr $C$DW$18, DW_AT_type(*$C$DW$T$20)
	.dwattr $C$DW$18, DW_AT_location[DW_OP_reg0]

$C$DW$19	.dwtag  DW_TAG_formal_parameter
	.dwattr $C$DW$19, DW_AT_name("src")
	.dwattr $C$DW$19, DW_AT_type(*$C$DW$T$22)
	.dwattr $C$DW$19, DW_AT_location[DW_OP_reg14]


;***************************************************************
;* FNAME: TINIE_mem_write               FR SIZE:   2           *
;*                                                             *
;* FUNCTION ENVIRONMENT                                        *
;*                                                             *
;* FUNCTION PROPERTIES                                         *
;*                            0 Parameter,  0 Auto,  2 SOE     *
;***************************************************************

||TINIE_mem_write||:
;* AL    assigned to $O$K9
$C$DW$20	.dwtag  DW_TAG_variable
	.dwattr $C$DW$20, DW_AT_name("$O$K9")
	.dwattr $C$DW$20, DW_AT_type(*$C$DW$T$10)
	.dwattr $C$DW$20, DW_AT_location[DW_OP_reg0]

;* AR4   assigned to $O$L1
$C$DW$21	.dwtag  DW_TAG_variable
	.dwattr $C$DW$21, DW_AT_name("$O$L1")
	.dwattr $C$DW$21, DW_AT_type(*$C$DW$T$10)
	.dwattr $C$DW$21, DW_AT_location[DW_OP_reg12]

;* AR7   assigned to dst
$C$DW$22	.dwtag  DW_TAG_variable
	.dwattr $C$DW$22, DW_AT_name("dst")
	.dwattr $C$DW$22, DW_AT_type(*$C$DW$T$49)
	.dwattr $C$DW$22, DW_AT_location[DW_OP_reg18]

;* AR7   assigned to num
$C$DW$23	.dwtag  DW_TAG_variable
	.dwattr $C$DW$23, DW_AT_name("num")
	.dwattr $C$DW$23, DW_AT_type(*$C$DW$T$21)
	.dwattr $C$DW$23, DW_AT_location[DW_OP_reg18]

;* AR5   assigned to src
$C$DW$24	.dwtag  DW_TAG_variable
	.dwattr $C$DW$24, DW_AT_name("src")
	.dwattr $C$DW$24, DW_AT_type(*$C$DW$T$22)
	.dwattr $C$DW$24, DW_AT_location[DW_OP_reg14]

;* AR6   assigned to count_by_1
$C$DW$25	.dwtag  DW_TAG_variable
	.dwattr $C$DW$25, DW_AT_name("count_by_1")
	.dwattr $C$DW$25, DW_AT_type(*$C$DW$T$10)
	.dwattr $C$DW$25, DW_AT_location[DW_OP_reg16]

	.dwcfi	cfa_offset, -2
	.dwcfi	save_reg_to_mem, 26, 0
;*** 107	-----------------------    count_by_1 = (int)num&3;
;*** 108	-----------------------    if ( (K$9 = (int)(num>>2)) <= 0 || K$9 == 0 ) goto g7;
        MOVL      XAR7,ACC              ; [CPU_ALU] |105| 
        CLRC      SXM                   ; [CPU_ALU] 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 107,column 18,is_stmt,isa 0
        MOV       AL,AR7                ; [CPU_ALU] |107| 
        MOVL      *SP++,XAR1            ; [CPU_ALU] 
	.dwcfi	save_reg_to_mem, 7, 2
	.dwcfi	cfa_offset, -4
        ANDB      AL,#0x03              ; [CPU_ALU] |107| 
        MOVZ      AR6,AL                ; [CPU_ALU] |107| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 108,column 3,is_stmt,isa 0
        MOVL      ACC,XAR7              ; [CPU_ALU] |108| 
        SFR       ACC,2                 ; [CPU_ALU] |108| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 105,column 1,is_stmt,isa 0
        MOVL      XAR7,XAR4             ; [CPU_ALU] |105| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 108,column 3,is_stmt,isa 0
        CMPB      AL,#0                 ; [CPU_ALU] |108| 
        B         ||$C$L3||,LEQ         ; [CPU_ALU] |108| 
        ; branchcc occurs ; [] |108| 
        CMPB      AL,#0                 ; [CPU_ALU] |108| 
        B         ||$C$L3||,EQ          ; [CPU_ALU] |108| 
        ; branchcc occurs ; [] |108| 
;*** 112	-----------------------    if ( K$9 < 2 ) goto g5;
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 112,column 7,is_stmt,isa 0
        CMPB      AL,#2                 ; [CPU_ALU] |112| 
        B         ||$C$L2||,LT          ; [CPU_ALU] |112| 
        ; branchcc occurs ; [] |112| 
;***  	-----------------------    L$1 = (K$9>>1)-1;
;***  	-----------------------    #pragma MUST_ITERATE(1, 16383, 1)
;***  	-----------------------    // LOOP BELOW UNROLLED BY FACTOR(2)
;***  	-----------------------    #pragma LOOP_FLAGS(4102u)
;***	-----------------------g4:
;*** 112	-----------------------    *dst = *src++;
;*** 113	-----------------------    dst[2] = *src++;
;*** 114	-----------------------    dst[4] = *src++;
;*** 115	-----------------------    dst[6] = *src++;
;*** 112	-----------------------    *(dst += 8) = *src++;
;*** 113	-----------------------    dst[2] = *src++;
;*** 114	-----------------------    dst[4] = *src++;
;*** 115	-----------------------    dst[6] = *src++;
;*** 116	-----------------------    dst += 8;
;*** 117	-----------------------    if ( (--L$1) != (-1) ) goto g4;
        MOV       AH,AL                 ; [CPU_ALU] 
        ASR       AH,1                  ; [CPU_ALU] 
        ADDB      AH,#-1                ; [CPU_ALU] 
        MOVZ      AR4,AH                ; [CPU_ALU] 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 117,column 5,is_stmt,isa 0
        RPTB      ||$C$L2||,AR4         ; [CPU_ALU] |117| 
        ; repeat block starts ; [] 
||$C$L1||:    
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 112,column 7,is_stmt,isa 0
        MOVL      P,*XAR5++             ; [CPU_ALU] |112| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 114,column 7,is_stmt,isa 0
        MOVB      XAR1,#8               ; [CPU_ALU] |114| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 112,column 7,is_stmt,isa 0
        MOVL      *+XAR7[0],P           ; [CPU_ALU] |112| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 115,column 7,is_stmt,isa 0
        MOVB      XAR0,#12              ; [CPU_ALU] |115| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 113,column 7,is_stmt,isa 0
        MOVL      P,*XAR5++             ; [CPU_ALU] |113| 
        MOVL      *+XAR7[4],P           ; [CPU_ALU] |113| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 114,column 7,is_stmt,isa 0
        MOVL      P,*XAR5++             ; [CPU_ALU] |114| 
        MOVL      *+XAR7[AR1],P         ; [CPU_ALU] |114| 
        MOVB      XAR1,#8               ; [CPU_ALU] |114| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 115,column 7,is_stmt,isa 0
        MOVL      P,*XAR5++             ; [CPU_ALU] |115| 
        MOVL      *+XAR7[AR0],P         ; [CPU_ALU] |115| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 112,column 7,is_stmt,isa 0
        ADDB      XAR7,#16              ; [CPU_ALU] |112| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 115,column 7,is_stmt,isa 0
        MOVB      XAR0,#12              ; [CPU_ALU] |115| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 112,column 7,is_stmt,isa 0
        MOVL      P,*XAR5++             ; [CPU_ALU] |112| 
        MOVL      *+XAR7[0],P           ; [CPU_ALU] |112| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 113,column 7,is_stmt,isa 0
        MOVL      P,*XAR5++             ; [CPU_ALU] |113| 
        MOVL      *+XAR7[4],P           ; [CPU_ALU] |113| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 114,column 7,is_stmt,isa 0
        MOVL      P,*XAR5++             ; [CPU_ALU] |114| 
        MOVL      *+XAR7[AR1],P         ; [CPU_ALU] |114| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 115,column 7,is_stmt,isa 0
        MOVL      P,*XAR5++             ; [CPU_ALU] |115| 
        MOVL      *+XAR7[AR0],P         ; [CPU_ALU] |115| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 116,column 9,is_stmt,isa 0
        ADDB      XAR7,#16              ; [CPU_ALU] |116| 
        ; repeat block ends ; [] 
||$C$L2||:    
;***	-----------------------g5:
;***  	-----------------------    if ( !(K$9&1) ) goto g7;
        TBIT      AL,#0                 ; [CPU_ALU] 
        B         ||$C$L3||,NTC         ; [CPU_ALU] 
        ; branchcc occurs ; [] 
; Peeled loop iterations for unrolled loop:
;*** 112	-----------------------    *dst = *src;
;*** 113	-----------------------    dst[2] = src[1];
;*** 114	-----------------------    dst[4] = src[2];
;*** 115	-----------------------    dst[6] = src[3];
;*** 116	-----------------------    dst += 8;
;*** 115	-----------------------    src += 4;
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 112,column 7,is_stmt,isa 0
        MOVL      ACC,*+XAR5[0]         ; [CPU_ALU] |112| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 114,column 7,is_stmt,isa 0
        MOVB      XAR1,#8               ; [CPU_ALU] |114| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 112,column 7,is_stmt,isa 0
        MOVL      *+XAR7[0],ACC         ; [CPU_ALU] |112| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 115,column 7,is_stmt,isa 0
        MOVB      XAR0,#12              ; [CPU_ALU] |115| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 113,column 7,is_stmt,isa 0
        MOVL      ACC,*+XAR5[2]         ; [CPU_ALU] |113| 
        MOVL      *+XAR7[4],ACC         ; [CPU_ALU] |113| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 114,column 7,is_stmt,isa 0
        MOVL      ACC,*+XAR5[4]         ; [CPU_ALU] |114| 
        MOVL      *+XAR7[AR1],ACC       ; [CPU_ALU] |114| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 115,column 7,is_stmt,isa 0
        MOVL      ACC,*+XAR5[6]         ; [CPU_ALU] |115| 
        ADDB      XAR5,#8               ; [CPU_ALU] |115| 
        MOVL      *+XAR7[AR0],ACC       ; [CPU_FPU] |115| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 116,column 9,is_stmt,isa 0
        ADDB      XAR7,#16              ; [CPU_ALU] |116| 
||$C$L3||:    
;***	-----------------------g7:
;*** 119	-----------------------    if ( count_by_1 <= 0 ) goto g11;
        MOV       AL,AR6                ; [CPU_ALU] 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 119,column 3,is_stmt,isa 0
        B         ||$C$L5||,LEQ         ; [CPU_ALU] |119| 
        ; branchcc occurs ; [] |119| 
;*** 121	-----------------------    if ( (--count_by_1) == (-1) ) goto g11;
;***  	-----------------------    #pragma MUST_ITERATE(1, 32767, 1)
;***  	-----------------------    #pragma LOOP_FLAGS(4096u)
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 121,column 5,is_stmt,isa 0
        SUBB      XAR6,#1               ; [CPU_ARAU] |121| 
        CMP       AR6,#-1               ; [CPU_ALU] |121| 
        B         ||$C$L5||,EQ          ; [CPU_ALU] |121| 
        ; branchcc occurs ; [] |121| 
||$C$L4||:    
;***	-----------------------g10:
;*** 123	-----------------------    *dst = *src++;
;*** 123	-----------------------    dst += 2;
;*** 125	-----------------------    if ( (--count_by_1) != (-1) ) goto g10;
;***	-----------------------g11:
;***  	-----------------------    return;
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 123,column 7,is_stmt,isa 0
        MOVL      ACC,*XAR5++           ; [CPU_ALU] |123| 
        MOVL      *+XAR7[0],ACC         ; [CPU_ALU] |123| 
        ADDB      XAR7,#4               ; [CPU_ALU] |123| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 125,column 5,is_stmt,isa 0
        BANZ      ||$C$L4||,AR6--       ; [CPU_ALU] |125| 
        ; branchcc occurs ; [] |125| 
||$C$L5||:    
        MOVL      XAR1,*--SP            ; [CPU_ALU] 
	.dwcfi	cfa_offset, -2
	.dwcfi	restore_reg, 7
$C$DW$26	.dwtag  DW_TAG_TI_branch
	.dwattr $C$DW$26, DW_AT_low_pc(0x00)
	.dwattr $C$DW$26, DW_AT_TI_return

        LRETR     ; [CPU_ALU] 
        ; return occurs ; [] 
	.dwattr $C$DW$16, DW_AT_TI_end_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c")
	.dwattr $C$DW$16, DW_AT_TI_end_line(0x7f)
	.dwattr $C$DW$16, DW_AT_TI_end_column(0x01)
	.dwendentry
	.dwendtag $C$DW$16

	.sect	".dab_npu_ramfunc:write_configMMR"
	.clink

$C$DW$27	.dwtag  DW_TAG_subprogram
	.dwattr $C$DW$27, DW_AT_name("write_configMMR")
	.dwattr $C$DW$27, DW_AT_low_pc(||write_configMMR||)
	.dwattr $C$DW$27, DW_AT_high_pc(0x00)
	.dwattr $C$DW$27, DW_AT_linkage_name("write_configMMR")
	.dwattr $C$DW$27, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c")
	.dwattr $C$DW$27, DW_AT_decl_line(0x82)
	.dwattr $C$DW$27, DW_AT_decl_column(0x0d)
	.dwattr $C$DW$27, DW_AT_TI_max_frame_size(-4)
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 131,column 1,is_stmt,address ||write_configMMR||,isa 0

	.dwfde $C$DW$CIE, ||write_configMMR||
$C$DW$28	.dwtag  DW_TAG_formal_parameter
	.dwattr $C$DW$28, DW_AT_name("layer")
	.dwattr $C$DW$28, DW_AT_type(*$C$DW$T$33)
	.dwattr $C$DW$28, DW_AT_location[DW_OP_reg12]


;***************************************************************
;* FNAME: write_configMMR               FR SIZE:   2           *
;*                                                             *
;* FUNCTION ENVIRONMENT                                        *
;*                                                             *
;* FUNCTION PROPERTIES                                         *
;*                            0 Parameter,  0 Auto,  2 SOE     *
;***************************************************************

||write_configMMR||:
;* AL    assigned to $O$C1
$C$DW$29	.dwtag  DW_TAG_variable
	.dwattr $C$DW$29, DW_AT_name("$O$C1")
	.dwattr $C$DW$29, DW_AT_type(*$C$DW$T$56)
	.dwattr $C$DW$29, DW_AT_location[DW_OP_reg0]

;* AR4   assigned to layer
$C$DW$30	.dwtag  DW_TAG_variable
	.dwattr $C$DW$30, DW_AT_name("layer")
	.dwattr $C$DW$30, DW_AT_type(*$C$DW$T$34)
	.dwattr $C$DW$30, DW_AT_location[DW_OP_reg12]

;* AR6   assigned to mmrs
$C$DW$31	.dwtag  DW_TAG_variable
	.dwattr $C$DW$31, DW_AT_name("mmrs")
	.dwattr $C$DW$31, DW_AT_type(*$C$DW$T$49)
	.dwattr $C$DW$31, DW_AT_location[DW_OP_reg16]

	.dwcfi	cfa_offset, -2
	.dwcfi	save_reg_to_mem, 26, 0
;*** 134	-----------------------    *(mmrs = (volatile unsigned long *)0x5412cL) = *((*layer).mmrs+6L);
;*** 135	-----------------------    mmrs[4] = *((*layer).mmrs+10L);
;*** 136	-----------------------    mmrs[10] = *((*layer).mmrs+16L);
;*** 137	-----------------------    mmrs[12] = *((*layer).mmrs+18L);
;*** 138	-----------------------    mmrs[18] = *((*layer).mmrs+24L);
;*** 139	-----------------------    mmrs[30] = *((*layer).mmrs+36L);
;*** 140	-----------------------    mmrs[36] = *((*layer).mmrs+42L);
;*** 141	-----------------------    mmrs[42] = *((*layer).mmrs+48L);
;*** 142	-----------------------    mmrs[44] = *((*layer).mmrs+50L);
;*** 143	-----------------------    mmrs[48] = *((*layer).mmrs+54L);
;*** 148	-----------------------    mmrs[2] = (unsigned long)(*layer).in_fmap>>17&0xffffcfffuL|(unsigned long)(*layer).out_fmap>>1&0xcfff0000uL;
;*** 149	-----------------------    mmrs[52] = (unsigned long)(*layer).in_fmap>>1&0xffffuL;
;*** 150	-----------------------    mmrs[54] = (unsigned long)(*layer).out_fmap>>1&0xffffuL;
;*** 151	-----------------------    C$1 = (*layer).residual_fmap;
;*** 151	-----------------------    if ( C$1 == NULL ) goto g3;
        MOVL      *SP++,XAR1            ; [CPU_ALU] 
	.dwcfi	save_reg_to_mem, 7, 2
	.dwcfi	cfa_offset, -4
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 134,column 5,is_stmt,isa 0
        MOVL      XAR5,*+XAR4[6]        ; [CPU_ALU] |134| 
        MOVL      XAR6,#344364          ; [CPU_ARAU] |134| 
        MOVL      ACC,*+XAR5[6]         ; [CPU_ALU] |134| 
        MOVL      *+XAR6[0],ACC         ; [CPU_ALU] |134| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 135,column 5,is_stmt,isa 0
        MOVB      ACC,#10               ; [CPU_ALU] |135| 
        ADDL      ACC,*+XAR4[6]         ; [CPU_ALU] |135| 
        MOVL      XAR5,ACC              ; [CPU_ALU] |135| 
        MOVB      XAR0,#8               ; [CPU_ALU] |135| 
        MOVL      ACC,*+XAR5[0]         ; [CPU_ALU] |135| 
        MOVL      *+XAR6[AR0],ACC       ; [CPU_ALU] |135| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 136,column 5,is_stmt,isa 0
        MOVB      ACC,#16               ; [CPU_ALU] |136| 
        ADDL      ACC,*+XAR4[6]         ; [CPU_ALU] |136| 
        MOVL      XAR5,ACC              ; [CPU_ALU] |136| 
        MOVB      XAR0,#20              ; [CPU_ALU] |136| 
        MOVL      ACC,*+XAR5[0]         ; [CPU_ALU] |136| 
        MOVL      *+XAR6[AR0],ACC       ; [CPU_ALU] |136| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 137,column 5,is_stmt,isa 0
        MOVB      ACC,#18               ; [CPU_ALU] |137| 
        ADDL      ACC,*+XAR4[6]         ; [CPU_ALU] |137| 
        MOVL      XAR5,ACC              ; [CPU_ALU] |137| 
        MOVB      XAR0,#24              ; [CPU_ALU] |137| 
        MOVL      ACC,*+XAR5[0]         ; [CPU_ALU] |137| 
        MOVL      *+XAR6[AR0],ACC       ; [CPU_ALU] |137| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 138,column 5,is_stmt,isa 0
        MOVB      ACC,#24               ; [CPU_ALU] |138| 
        ADDL      ACC,*+XAR4[6]         ; [CPU_ALU] |138| 
        MOVL      XAR5,ACC              ; [CPU_ALU] |138| 
        MOVB      XAR0,#36              ; [CPU_ALU] |138| 
        MOVL      ACC,*+XAR5[0]         ; [CPU_ALU] |138| 
        MOVL      *+XAR6[AR0],ACC       ; [CPU_ALU] |138| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 139,column 5,is_stmt,isa 0
        MOVB      ACC,#36               ; [CPU_ALU] |139| 
        ADDL      ACC,*+XAR4[6]         ; [CPU_ALU] |139| 
        MOVL      XAR5,ACC              ; [CPU_ALU] |139| 
        MOVB      XAR0,#60              ; [CPU_ALU] |139| 
        MOVL      ACC,*+XAR5[0]         ; [CPU_ALU] |139| 
        MOVL      *+XAR6[AR0],ACC       ; [CPU_ALU] |139| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 140,column 5,is_stmt,isa 0
        MOVB      ACC,#42               ; [CPU_ALU] |140| 
        ADDL      ACC,*+XAR4[6]         ; [CPU_ALU] |140| 
        MOVL      XAR5,ACC              ; [CPU_ALU] |140| 
        MOVB      XAR0,#72              ; [CPU_ALU] |140| 
        MOVL      ACC,*+XAR5[0]         ; [CPU_ALU] |140| 
        MOVL      *+XAR6[AR0],ACC       ; [CPU_ALU] |140| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 141,column 5,is_stmt,isa 0
        MOVB      ACC,#48               ; [CPU_ALU] |141| 
        ADDL      ACC,*+XAR4[6]         ; [CPU_ALU] |141| 
        MOVL      XAR5,ACC              ; [CPU_ALU] |141| 
        MOVB      XAR0,#84              ; [CPU_ALU] |141| 
        MOVL      ACC,*+XAR5[0]         ; [CPU_ALU] |141| 
        MOVL      *+XAR6[AR0],ACC       ; [CPU_ALU] |141| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 142,column 5,is_stmt,isa 0
        MOVB      ACC,#50               ; [CPU_ALU] |142| 
        ADDL      ACC,*+XAR4[6]         ; [CPU_ALU] |142| 
        MOVL      XAR5,ACC              ; [CPU_ALU] |142| 
        MOVB      XAR0,#88              ; [CPU_ALU] |142| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 143,column 5,is_stmt,isa 0
        MOVB      XAR1,#96              ; [CPU_ALU] |143| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 142,column 5,is_stmt,isa 0
        MOVL      ACC,*+XAR5[0]         ; [CPU_ALU] |142| 
        MOVL      *+XAR6[AR0],ACC       ; [CPU_ALU] |142| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 143,column 5,is_stmt,isa 0
        MOVB      ACC,#54               ; [CPU_ALU] |143| 
        ADDL      ACC,*+XAR4[6]         ; [CPU_ALU] |143| 
        MOVL      XAR5,ACC              ; [CPU_ALU] |143| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 148,column 5,is_stmt,isa 0
        MOVB      XAR0,#12              ; [CPU_ALU] |148| 
        MOV       T,#17                 ; [CPU_ALU] |148| 
        CLRC      SXM                   ; [CPU_ALU] 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 143,column 5,is_stmt,isa 0
        MOVL      ACC,*+XAR5[0]         ; [CPU_ALU] |143| 
        MOVL      *+XAR6[AR1],ACC       ; [CPU_ALU] |143| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 149,column 5,is_stmt,isa 0
        MOVB      XAR1,#104             ; [CPU_ALU] |149| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 148,column 5,is_stmt,isa 0
        MOVL      ACC,*+XAR4[AR0]       ; [CPU_ALU] |148| 
        MOVB      XAR0,#16              ; [CPU_ALU] |148| 
        LSRL      ACC,T                 ; [CPU_ALU] |148| 
        AND       AL,#53247             ; [CPU_ALU] |148| 
        MOVL      P,ACC                 ; [CPU_ALU] |148| 
        MOVL      ACC,*+XAR4[AR0]       ; [CPU_ALU] |148| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 149,column 5,is_stmt,isa 0
        MOVB      XAR0,#12              ; [CPU_ALU] |149| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 148,column 5,is_stmt,isa 0
        SFR       ACC,1                 ; [CPU_ALU] |148| 
        ANDB      AL,#0                 ; [CPU_ALU] |148| 
        AND       AH,#53247             ; [CPU_ALU] |148| 
        OR        AL,PL                 ; [CPU_ALU] |148| 
        OR        AH,PH                 ; [CPU_ALU] |148| 
        MOVL      *+XAR6[4],ACC         ; [CPU_ALU] |148| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 149,column 5,is_stmt,isa 0
        MOVL      ACC,*+XAR4[AR0]       ; [CPU_ALU] |149| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 150,column 5,is_stmt,isa 0
        MOVB      XAR0,#16              ; [CPU_ALU] |150| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 149,column 5,is_stmt,isa 0
        SFR       ACC,1                 ; [CPU_ALU] |149| 
        ANDB      AH,#0                 ; [CPU_ALU] |149| 
        MOVL      *+XAR6[AR1],ACC       ; [CPU_ALU] |149| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 150,column 5,is_stmt,isa 0
        MOVB      XAR1,#108             ; [CPU_ALU] |150| 
        MOVL      ACC,*+XAR4[AR0]       ; [CPU_ALU] |150| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 151,column 5,is_stmt,isa 0
        MOVB      XAR0,#14              ; [CPU_ALU] |151| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 150,column 5,is_stmt,isa 0
        SFR       ACC,1                 ; [CPU_ALU] |150| 
        ANDB      AH,#0                 ; [CPU_ALU] |150| 
        MOVL      *+XAR6[AR1],ACC       ; [CPU_ALU] |150| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 151,column 5,is_stmt,isa 0
        MOVL      ACC,*+XAR4[AR0]       ; [CPU_ALU] |151| 
        B         ||$C$L6||,EQ          ; [CPU_ALU] |151| 
        ; branchcc occurs ; [] |151| 
;*** 152	-----------------------    mmrs[56] = (unsigned long)C$1>>1&0xffffuL;
;***	-----------------------g3:
;***  	-----------------------    return;
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 152,column 9,is_stmt,isa 0
        SFR       ACC,1                 ; [CPU_ALU] |152| 
        MOVB      XAR0,#112             ; [CPU_FPU] |152| 
        ANDB      AH,#0                 ; [CPU_ALU] |152| 
        MOVL      *+XAR6[AR0],ACC       ; [CPU_ALU] |152| 
||$C$L6||:    
        MOVL      XAR1,*--SP            ; [CPU_ALU] 
	.dwcfi	cfa_offset, -2
	.dwcfi	restore_reg, 7
$C$DW$32	.dwtag  DW_TAG_TI_branch
	.dwattr $C$DW$32, DW_AT_low_pc(0x00)
	.dwattr $C$DW$32, DW_AT_TI_return

        LRETR     ; [CPU_ALU] 
        ; return occurs ; [] 
	.dwattr $C$DW$27, DW_AT_TI_end_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c")
	.dwattr $C$DW$27, DW_AT_TI_end_line(0x99)
	.dwattr $C$DW$27, DW_AT_TI_end_column(0x01)
	.dwendentry
	.dwendtag $C$DW$27

	.sect	".dab_npu_ramfunc:TINIE_setup"
	.clink
	.global	||TINIE_setup||

$C$DW$33	.dwtag  DW_TAG_subprogram
	.dwattr $C$DW$33, DW_AT_name("TINIE_setup")
	.dwattr $C$DW$33, DW_AT_low_pc(||TINIE_setup||)
	.dwattr $C$DW$33, DW_AT_high_pc(0x00)
	.dwattr $C$DW$33, DW_AT_linkage_name("TINIE_setup")
	.dwattr $C$DW$33, DW_AT_external
	.dwattr $C$DW$33, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c")
	.dwattr $C$DW$33, DW_AT_decl_line(0x9f)
	.dwattr $C$DW$33, DW_AT_decl_column(0x06)
	.dwattr $C$DW$33, DW_AT_TI_max_frame_size(-4)
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 160,column 1,is_stmt,address ||TINIE_setup||,isa 0

	.dwfde $C$DW$CIE, ||TINIE_setup||
$C$DW$34	.dwtag  DW_TAG_formal_parameter
	.dwattr $C$DW$34, DW_AT_name("layer")
	.dwattr $C$DW$34, DW_AT_type(*$C$DW$T$33)
	.dwattr $C$DW$34, DW_AT_location[DW_OP_reg12]


;***************************************************************
;* FNAME: TINIE_setup                   FR SIZE:   2           *
;*                                                             *
;* FUNCTION ENVIRONMENT                                        *
;*                                                             *
;* FUNCTION PROPERTIES                                         *
;*                            0 Parameter,  0 Auto,  2 SOE     *
;***************************************************************

||TINIE_setup||:
;* AL    assigned to $O$C1
$C$DW$35	.dwtag  DW_TAG_variable
	.dwattr $C$DW$35, DW_AT_name("$O$C1")
	.dwattr $C$DW$35, DW_AT_type(*$C$DW$T$13)
	.dwattr $C$DW$35, DW_AT_location[DW_OP_reg0]

;* AR5   assigned to $O$v3
$C$DW$36	.dwtag  DW_TAG_variable
	.dwattr $C$DW$36, DW_AT_name("$O$v3")
	.dwattr $C$DW$36, DW_AT_type(*$C$DW$T$22)
	.dwattr $C$DW$36, DW_AT_location[DW_OP_reg14]

;* AR6   assigned to $O$v2
$C$DW$37	.dwtag  DW_TAG_variable
	.dwattr $C$DW$37, DW_AT_name("$O$v2")
	.dwattr $C$DW$37, DW_AT_type(*$C$DW$T$20)
	.dwattr $C$DW$37, DW_AT_location[DW_OP_reg16]

;* AR1   assigned to layer
$C$DW$38	.dwtag  DW_TAG_variable
	.dwattr $C$DW$38, DW_AT_name("layer")
	.dwattr $C$DW$38, DW_AT_type(*$C$DW$T$34)
	.dwattr $C$DW$38, DW_AT_location[DW_OP_reg6]

;* AR4   assigned to params
$C$DW$39	.dwtag  DW_TAG_variable
	.dwattr $C$DW$39, DW_AT_name("params")
	.dwattr $C$DW$39, DW_AT_type(*$C$DW$T$49)
	.dwattr $C$DW$39, DW_AT_location[DW_OP_reg12]

;* AR4   assigned to ins
$C$DW$40	.dwtag  DW_TAG_variable
	.dwattr $C$DW$40, DW_AT_name("ins")
	.dwattr $C$DW$40, DW_AT_type(*$C$DW$T$49)
	.dwattr $C$DW$40, DW_AT_location[DW_OP_reg12]

	.dwcfi	cfa_offset, -2
	.dwcfi	save_reg_to_mem, 26, 0
;*** 167	-----------------------    if ( (C$1 = (*layer).num_params) == 0uL ) goto g3;
        MOVL      *SP++,XAR1            ; [CPU_ALU] 
	.dwcfi	save_reg_to_mem, 7, 2
	.dwcfi	cfa_offset, -4
        MOVL      XAR1,XAR4             ; [CPU_ALU] |160| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 167,column 5,is_stmt,isa 0
        MOVL      ACC,*+XAR1[2]         ; [CPU_ALU] |167| 
        B         ||$C$L7||,EQ          ; [CPU_ALU] |167| 
        ; branchcc occurs ; [] |167| 
;*** 169	-----------------------    TINIE_mem_write(params = (volatile unsigned long *)0x55800uL, C$1, (*layer).params);
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 169,column 9,is_stmt,isa 0
        MOVB      XAR0,#8               ; [CPU_ALU] |169| 
        MOVL      XAR4,#350208          ; [CPU_ARAU] |169| 
        MOVL      XAR5,*+XAR1[AR0]      ; [CPU_ALU] |169| 
$C$DW$41	.dwtag  DW_TAG_TI_branch
	.dwattr $C$DW$41, DW_AT_low_pc(0x00)
	.dwattr $C$DW$41, DW_AT_name("TINIE_mem_write")
	.dwattr $C$DW$41, DW_AT_TI_call

        LCR       #||TINIE_mem_write||  ; [CPU_ALU] |169| 
        ; call occurs [#||TINIE_mem_write||] ; [] |169| 
||$C$L7||:    
;***	-----------------------g3:
;*** 182	-----------------------    if ( (v$2 = (*layer).num_ins) == 0uL ) goto g7;
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 182,column 5,is_stmt,isa 0
        MOVL      ACC,*+XAR1[4]         ; [CPU_ALU] |182| 
        MOVL      XAR6,ACC              ; [CPU_ALU] |182| 
        B         ||$C$L9||,EQ          ; [CPU_ALU] |182| 
        ; branchcc occurs ; [] |182| 
;*** 185	-----------------------    v$3 = (*layer).ins;
;*** 181	-----------------------    ins = (volatile unsigned long *)0x55000uL;
;*** 185	-----------------------    if ( v$3 != dab_npu_loaded_ins ) goto g6;
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 185,column 9,is_stmt,isa 0
        MOVB      XAR0,#10              ; [CPU_ALU] |185| 
        MOVL      XAR5,*+XAR1[AR0]      ; [CPU_ALU] |185| 
        MOVW      DP,#||dab_npu_loaded_ins|| ; [CPU_ARAU] 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 181,column 28,is_stmt,isa 0
        MOVL      XAR4,#348160          ; [CPU_ARAU] |181| 
        MOVL      ACC,XAR5              ; [CPU_ALU] |181| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 185,column 9,is_stmt,isa 0
        CMPL      ACC,@||dab_npu_loaded_ins|| ; [CPU_ALU] |185| 
        B         ||$C$L8||,NEQ         ; [CPU_ALU] |185| 
        ; branchcc occurs ; [] |185| 
;*** 185	-----------------------    if ( v$2 == dab_npu_loaded_ins_count ) goto g7;
        MOVL      ACC,XAR6              ; [CPU_ALU] 
        CMPL      ACC,@||dab_npu_loaded_ins_count|| ; [CPU_ALU] |185| 
        B         ||$C$L9||,EQ          ; [CPU_ALU] |185| 
        ; branchcc occurs ; [] |185| 
||$C$L8||:    
;***	-----------------------g6:
;*** 187	-----------------------    TINIE_mem_write(ins, v$2, v$3);
;*** 188	-----------------------    dab_npu_loaded_ins = (*layer).ins;
;*** 189	-----------------------    dab_npu_loaded_ins_count = (*layer).num_ins;
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 187,column 13,is_stmt,isa 0
        MOVL      ACC,XAR6              ; [CPU_ALU] |187| 
$C$DW$42	.dwtag  DW_TAG_TI_branch
	.dwattr $C$DW$42, DW_AT_low_pc(0x00)
	.dwattr $C$DW$42, DW_AT_name("TINIE_mem_write")
	.dwattr $C$DW$42, DW_AT_TI_call

        LCR       #||TINIE_mem_write||  ; [CPU_ALU] |187| 
        ; call occurs [#||TINIE_mem_write||] ; [] |187| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 188,column 13,is_stmt,isa 0
        MOVB      XAR0,#10              ; [CPU_ALU] |188| 
        MOVL      XAR6,*+XAR1[AR0]      ; [CPU_ALU] |188| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 189,column 13,is_stmt,isa 0
        MOVL      ACC,*+XAR1[4]         ; [CPU_ALU] |189| 
        MOVL      @||dab_npu_loaded_ins_count||,ACC ; [CPU_ALU] |189| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 188,column 13,is_stmt,isa 0
        MOVL      @||dab_npu_loaded_ins||,XAR6 ; [CPU_ALU] |188| 
||$C$L9||:    
;***	-----------------------g7:
;*** 202	-----------------------    write_configMMR(layer);
;***  	-----------------------    return;
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 202,column 5,is_stmt,isa 0
        MOVL      XAR4,XAR1             ; [CPU_ALU] |202| 
$C$DW$43	.dwtag  DW_TAG_TI_branch
	.dwattr $C$DW$43, DW_AT_low_pc(0x00)
	.dwattr $C$DW$43, DW_AT_name("write_configMMR")
	.dwattr $C$DW$43, DW_AT_TI_call

        LCR       #||write_configMMR||  ; [CPU_ALU] |202| 
        ; call occurs [#||write_configMMR||] ; [] |202| 
        MOVL      XAR1,*--SP            ; [CPU_ALU] 
	.dwcfi	cfa_offset, -2
	.dwcfi	restore_reg, 7
$C$DW$44	.dwtag  DW_TAG_TI_branch
	.dwattr $C$DW$44, DW_AT_low_pc(0x00)
	.dwattr $C$DW$44, DW_AT_TI_return

        LRETR     ; [CPU_ALU] 
        ; return occurs ; [] 
	.dwattr $C$DW$33, DW_AT_TI_end_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c")
	.dwattr $C$DW$33, DW_AT_TI_end_line(0xcf)
	.dwattr $C$DW$33, DW_AT_TI_end_column(0x01)
	.dwendentry
	.dwendtag $C$DW$33

	.sect	".text:TINIE_registerInterrupt"
	.clink
	.global	||TINIE_registerInterrupt||

$C$DW$45	.dwtag  DW_TAG_subprogram
	.dwattr $C$DW$45, DW_AT_name("TINIE_registerInterrupt")
	.dwattr $C$DW$45, DW_AT_low_pc(||TINIE_registerInterrupt||)
	.dwattr $C$DW$45, DW_AT_high_pc(0x00)
	.dwattr $C$DW$45, DW_AT_linkage_name("TINIE_registerInterrupt")
	.dwattr $C$DW$45, DW_AT_external
	.dwattr $C$DW$45, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c")
	.dwattr $C$DW$45, DW_AT_decl_line(0xde)
	.dwattr $C$DW$45, DW_AT_decl_column(0x06)
	.dwattr $C$DW$45, DW_AT_TI_max_frame_size(-4)
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 223,column 1,is_stmt,address ||TINIE_registerInterrupt||,isa 0

	.dwfde $C$DW$CIE, ||TINIE_registerInterrupt||
$C$DW$46	.dwtag  DW_TAG_formal_parameter
	.dwattr $C$DW$46, DW_AT_name("handler")
	.dwattr $C$DW$46, DW_AT_type(*$C$DW$T$38)
	.dwattr $C$DW$46, DW_AT_location[DW_OP_reg12]


;***************************************************************
;* FNAME: TINIE_registerInterrupt       FR SIZE:   2           *
;*                                                             *
;* FUNCTION ENVIRONMENT                                        *
;*                                                             *
;* FUNCTION PROPERTIES                                         *
;*                            0 Parameter,  0 Auto,  2 SOE     *
;***************************************************************

||TINIE_registerInterrupt||:
;* AR1   assigned to handler
$C$DW$47	.dwtag  DW_TAG_variable
	.dwattr $C$DW$47, DW_AT_name("handler")
	.dwattr $C$DW$47, DW_AT_type(*$C$DW$T$39)
	.dwattr $C$DW$47, DW_AT_location[DW_OP_reg6]

	.dwcfi	cfa_offset, -2
	.dwcfi	save_reg_to_mem, 26, 0
;*** 218	-----------------------    __disable_interrupts();  // [1]
;*** 225	-----------------------    Interrupt_disable(13043984uL);
;*** 258	-----------------------    __eallow();  // [2]
;*** 259	-----------------------    *(volatile unsigned long *)0xe8euL = (unsigned long)handler;  // [2]
;*** 260	-----------------------    __edis();  // [2]
;*** 227	-----------------------    Interrupt_enable(13043984uL);
;*** 198	-----------------------    __enable_interrupts();  // [0]
;***  	-----------------------    return;
        MOVL      *SP++,XAR1            ; [CPU_ALU] 
	.dwcfi	save_reg_to_mem, 7, 2
	.dwcfi	cfa_offset, -4
        MOVL      XAR1,XAR4             ; [CPU_ALU] |223| 
	.dwpsn	file "E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\interrupt.h",line 218,column 5,is_stmt,isa 0
        PUSH      ST1                   ; [CPU_ALU] |218| 
        SETC      INTM, DBGM            ; [CPU_ALU] |218| 
        MOV       AL,*--SP              ; [CPU_ALU] |218| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 225,column 5,is_stmt,isa 0
        MOV       AH,#199               ; [CPU_ALU] |225| 
        MOV       AL,#2320              ; [CPU_ALU] |225| 
$C$DW$48	.dwtag  DW_TAG_TI_branch
	.dwattr $C$DW$48, DW_AT_low_pc(0x00)
	.dwattr $C$DW$48, DW_AT_name("Interrupt_disable")
	.dwattr $C$DW$48, DW_AT_TI_call

        LCR       #||Interrupt_disable|| ; [CPU_ALU] |225| 
        ; call occurs [#||Interrupt_disable||] ; [] |225| 
	.dwpsn	file "E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\interrupt.h",line 258,column 5,is_stmt,isa 0
        EALLOW    ; [CPU_ALU] |258| 
	.dwpsn	file "E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\interrupt.h",line 259,column 5,is_stmt,isa 0
        MOV32     *(0:0x0e8e),XAR1      ; [CPU_FPU] |259| 
	.dwpsn	file "E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\interrupt.h",line 260,column 5,is_stmt,isa 0
        EDIS      ; [CPU_ALU] |260| 
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 227,column 5,is_stmt,isa 0
        MOV       AL,#2320              ; [CPU_ALU] |227| 
        MOV       AH,#199               ; [CPU_ALU] |227| 
$C$DW$49	.dwtag  DW_TAG_TI_branch
	.dwattr $C$DW$49, DW_AT_low_pc(0x00)
	.dwattr $C$DW$49, DW_AT_name("Interrupt_enable")
	.dwattr $C$DW$49, DW_AT_TI_call

        LCR       #||Interrupt_enable|| ; [CPU_ALU] |227| 
        ; call occurs [#||Interrupt_enable||] ; [] |227| 
	.dwpsn	file "E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\interrupt.h",line 198,column 5,is_stmt,isa 0
        PUSH      ST1                   ; [CPU_ALU] |198| 
        CLRC      INTM, DBGM            ; [CPU_ALU] |198| 
        MOV       AL,*--SP              ; [CPU_ALU] |198| 
        MOVL      XAR1,*--SP            ; [CPU_ALU] 
	.dwcfi	cfa_offset, -2
	.dwcfi	restore_reg, 7
$C$DW$50	.dwtag  DW_TAG_TI_branch
	.dwattr $C$DW$50, DW_AT_low_pc(0x00)
	.dwattr $C$DW$50, DW_AT_TI_return

        LRETR     ; [CPU_ALU] 
        ; return occurs ; [] 
	.dwattr $C$DW$45, DW_AT_TI_end_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c")
	.dwattr $C$DW$45, DW_AT_TI_end_line(0xe5)
	.dwattr $C$DW$45, DW_AT_TI_end_column(0x01)
	.dwendentry
	.dwendtag $C$DW$45

	.sect	".dab_npu_ramfunc:TINIE_clearInterruptACK"
	.clink
	.global	||TINIE_clearInterruptACK||

$C$DW$51	.dwtag  DW_TAG_subprogram
	.dwattr $C$DW$51, DW_AT_name("TINIE_clearInterruptACK")
	.dwattr $C$DW$51, DW_AT_low_pc(||TINIE_clearInterruptACK||)
	.dwattr $C$DW$51, DW_AT_high_pc(0x00)
	.dwattr $C$DW$51, DW_AT_linkage_name("TINIE_clearInterruptACK")
	.dwattr $C$DW$51, DW_AT_external
	.dwattr $C$DW$51, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c")
	.dwattr $C$DW$51, DW_AT_decl_line(0xe8)
	.dwattr $C$DW$51, DW_AT_decl_column(0x06)
	.dwattr $C$DW$51, DW_AT_TI_max_frame_size(-2)
	.dwpsn	file "D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c",line 233,column 1,is_stmt,address ||TINIE_clearInterruptACK||,isa 0

	.dwfde $C$DW$CIE, ||TINIE_clearInterruptACK||

;***************************************************************
;* FNAME: TINIE_clearInterruptACK       FR SIZE:   0           *
;*                                                             *
;* FUNCTION ENVIRONMENT                                        *
;*                                                             *
;* FUNCTION PROPERTIES                                         *
;*                            0 Parameter,  0 Auto,  0 SOE     *
;***************************************************************

||TINIE_clearInterruptACK||:
	.dwcfi	cfa_offset, -2
	.dwcfi	save_reg_to_mem, 26, 0
;*** 379	-----------------------    *(volatile unsigned *)0xce1uL = 256u;  // [3]
;***  	-----------------------    return;
	.dwpsn	file "E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\interrupt.h",line 379,column 5,is_stmt,isa 0
        MOV       AL,#256               ; [CPU_ALU] |379| 
        MOV       *(0:0x0ce1),AL        ; [CPU_ALU] |379| 
$C$DW$52	.dwtag  DW_TAG_TI_branch
	.dwattr $C$DW$52, DW_AT_low_pc(0x00)
	.dwattr $C$DW$52, DW_AT_TI_return

        LRETR     ; [CPU_ALU] 
        ; return occurs ; [] 
	.dwattr $C$DW$51, DW_AT_TI_end_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\dab_control_f28p550\model\experiments\fc\stage_c_20261031\work\C4\dab_control_f28p550\model\generated\fc_int8\dab_tinie_c28.c")
	.dwattr $C$DW$51, DW_AT_TI_end_line(0xeb)
	.dwattr $C$DW$51, DW_AT_TI_end_column(0x01)
	.dwendentry
	.dwendtag $C$DW$51

;* Inlined function references:
;* [0] Interrupt_enableGlobal
;* [1] Interrupt_disableGlobal
;* [2] Interrupt_register
;* [3] Interrupt_clearACKGroup
;* [4] SysCtl_enablePeripheral
;* [5] SysCtl_setNPUClockDivider
;**************************************************************
;* UNDEFINED EXTERNAL REFERENCES                              *
;**************************************************************
	.global	||Interrupt_disable||
	.global	||Interrupt_enable||

;***************************************************************
;* BUILD ATTRIBUTES                                            *
;***************************************************************
	.battr "c28xabi", Tag_File, 1, Tag_float_args(0)
	.battr "c28xabi", Tag_File, 1, Tag_double_args(0)
	.dwattr $C$DW$CU, DW_AT_language(DW_LANG_C)

;***************************************************************
;* DWARF CIE ENTRIES                                           *
;***************************************************************

$C$DW$CIE	.dwcie 26
	.dwcfi	cfa_register, 20
	.dwcfi	cfa_offset, 0
	.dwcfi	same_value, 28
	.dwcfi	same_value, 6
	.dwcfi	same_value, 7
	.dwcfi	same_value, 8
	.dwcfi	same_value, 9
	.dwcfi	same_value, 10
	.dwcfi	same_value, 11
	.dwcfi	same_value, 59
	.dwcfi	same_value, 63
	.dwcfi	same_value, 67
	.dwcfi	same_value, 71
	.dwendentry
	.dwendtag $C$DW$CU


;***************************************************************
;* TYPE INFORMATION                                            *
;***************************************************************

$C$DW$TU$28	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$28

$C$DW$T$28	.dwtag  DW_TAG_enumeration_type
	.dwattr $C$DW$T$28, DW_AT_byte_size(0x01)
$C$DW$53	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$53, DW_AT_name("SYSCTL_PERIPH_CLK_CLA1")
	.dwattr $C$DW$53, DW_AT_const_value(0x00)
	.dwattr $C$DW$53, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$53, DW_AT_decl_line(0x168)
	.dwattr $C$DW$53, DW_AT_decl_column(0x05)

$C$DW$54	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$54, DW_AT_name("SYSCTL_PERIPH_CLK_DMA")
	.dwattr $C$DW$54, DW_AT_const_value(0x200)
	.dwattr $C$DW$54, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$54, DW_AT_decl_line(0x169)
	.dwattr $C$DW$54, DW_AT_decl_column(0x05)

$C$DW$55	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$55, DW_AT_name("SYSCTL_PERIPH_CLK_TIMER0")
	.dwattr $C$DW$55, DW_AT_const_value(0x300)
	.dwattr $C$DW$55, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$55, DW_AT_decl_line(0x16a)
	.dwattr $C$DW$55, DW_AT_decl_column(0x05)

$C$DW$56	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$56, DW_AT_name("SYSCTL_PERIPH_CLK_TIMER1")
	.dwattr $C$DW$56, DW_AT_const_value(0x400)
	.dwattr $C$DW$56, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$56, DW_AT_decl_line(0x16b)
	.dwattr $C$DW$56, DW_AT_decl_column(0x05)

$C$DW$57	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$57, DW_AT_name("SYSCTL_PERIPH_CLK_TIMER2")
	.dwattr $C$DW$57, DW_AT_const_value(0x500)
	.dwattr $C$DW$57, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$57, DW_AT_decl_line(0x16c)
	.dwattr $C$DW$57, DW_AT_decl_column(0x05)

$C$DW$58	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$58, DW_AT_name("SYSCTL_PERIPH_CLK_HRCAL")
	.dwattr $C$DW$58, DW_AT_const_value(0x1000)
	.dwattr $C$DW$58, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$58, DW_AT_decl_line(0x16d)
	.dwattr $C$DW$58, DW_AT_decl_column(0x05)

$C$DW$59	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$59, DW_AT_name("SYSCTL_PERIPH_CLK_TBCLKSYNC")
	.dwattr $C$DW$59, DW_AT_const_value(0x1200)
	.dwattr $C$DW$59, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$59, DW_AT_decl_line(0x16e)
	.dwattr $C$DW$59, DW_AT_decl_column(0x05)

$C$DW$60	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$60, DW_AT_name("SYSCTL_PERIPH_CLK_ERAD")
	.dwattr $C$DW$60, DW_AT_const_value(0x1800)
	.dwattr $C$DW$60, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$60, DW_AT_decl_line(0x16f)
	.dwattr $C$DW$60, DW_AT_decl_column(0x05)

$C$DW$61	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$61, DW_AT_name("SYSCTL_PERIPH_CLK_EPWM1")
	.dwattr $C$DW$61, DW_AT_const_value(0x02)
	.dwattr $C$DW$61, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$61, DW_AT_decl_line(0x170)
	.dwattr $C$DW$61, DW_AT_decl_column(0x05)

$C$DW$62	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$62, DW_AT_name("SYSCTL_PERIPH_CLK_EPWM2")
	.dwattr $C$DW$62, DW_AT_const_value(0x102)
	.dwattr $C$DW$62, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$62, DW_AT_decl_line(0x171)
	.dwattr $C$DW$62, DW_AT_decl_column(0x05)

$C$DW$63	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$63, DW_AT_name("SYSCTL_PERIPH_CLK_EPWM3")
	.dwattr $C$DW$63, DW_AT_const_value(0x202)
	.dwattr $C$DW$63, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$63, DW_AT_decl_line(0x172)
	.dwattr $C$DW$63, DW_AT_decl_column(0x05)

$C$DW$64	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$64, DW_AT_name("SYSCTL_PERIPH_CLK_EPWM4")
	.dwattr $C$DW$64, DW_AT_const_value(0x302)
	.dwattr $C$DW$64, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$64, DW_AT_decl_line(0x173)
	.dwattr $C$DW$64, DW_AT_decl_column(0x05)

$C$DW$65	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$65, DW_AT_name("SYSCTL_PERIPH_CLK_EPWM5")
	.dwattr $C$DW$65, DW_AT_const_value(0x402)
	.dwattr $C$DW$65, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$65, DW_AT_decl_line(0x174)
	.dwattr $C$DW$65, DW_AT_decl_column(0x05)

$C$DW$66	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$66, DW_AT_name("SYSCTL_PERIPH_CLK_EPWM6")
	.dwattr $C$DW$66, DW_AT_const_value(0x502)
	.dwattr $C$DW$66, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$66, DW_AT_decl_line(0x175)
	.dwattr $C$DW$66, DW_AT_decl_column(0x05)

$C$DW$67	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$67, DW_AT_name("SYSCTL_PERIPH_CLK_EPWM7")
	.dwattr $C$DW$67, DW_AT_const_value(0x602)
	.dwattr $C$DW$67, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$67, DW_AT_decl_line(0x176)
	.dwattr $C$DW$67, DW_AT_decl_column(0x05)

$C$DW$68	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$68, DW_AT_name("SYSCTL_PERIPH_CLK_EPWM8")
	.dwattr $C$DW$68, DW_AT_const_value(0x702)
	.dwattr $C$DW$68, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$68, DW_AT_decl_line(0x177)
	.dwattr $C$DW$68, DW_AT_decl_column(0x05)

$C$DW$69	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$69, DW_AT_name("SYSCTL_PERIPH_CLK_EPWM9")
	.dwattr $C$DW$69, DW_AT_const_value(0x802)
	.dwattr $C$DW$69, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$69, DW_AT_decl_line(0x178)
	.dwattr $C$DW$69, DW_AT_decl_column(0x05)

$C$DW$70	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$70, DW_AT_name("SYSCTL_PERIPH_CLK_EPWM10")
	.dwattr $C$DW$70, DW_AT_const_value(0x902)
	.dwattr $C$DW$70, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$70, DW_AT_decl_line(0x179)
	.dwattr $C$DW$70, DW_AT_decl_column(0x05)

$C$DW$71	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$71, DW_AT_name("SYSCTL_PERIPH_CLK_EPWM11")
	.dwattr $C$DW$71, DW_AT_const_value(0xa02)
	.dwattr $C$DW$71, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$71, DW_AT_decl_line(0x17a)
	.dwattr $C$DW$71, DW_AT_decl_column(0x05)

$C$DW$72	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$72, DW_AT_name("SYSCTL_PERIPH_CLK_EPWM12")
	.dwattr $C$DW$72, DW_AT_const_value(0xb02)
	.dwattr $C$DW$72, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$72, DW_AT_decl_line(0x17b)
	.dwattr $C$DW$72, DW_AT_decl_column(0x05)

$C$DW$73	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$73, DW_AT_name("SYSCTL_PERIPH_CLK_ECAP1")
	.dwattr $C$DW$73, DW_AT_const_value(0x03)
	.dwattr $C$DW$73, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$73, DW_AT_decl_line(0x17c)
	.dwattr $C$DW$73, DW_AT_decl_column(0x05)

$C$DW$74	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$74, DW_AT_name("SYSCTL_PERIPH_CLK_ECAP2")
	.dwattr $C$DW$74, DW_AT_const_value(0x103)
	.dwattr $C$DW$74, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$74, DW_AT_decl_line(0x17d)
	.dwattr $C$DW$74, DW_AT_decl_column(0x05)

$C$DW$75	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$75, DW_AT_name("SYSCTL_PERIPH_CLK_EQEP1")
	.dwattr $C$DW$75, DW_AT_const_value(0x04)
	.dwattr $C$DW$75, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$75, DW_AT_decl_line(0x17e)
	.dwattr $C$DW$75, DW_AT_decl_column(0x05)

$C$DW$76	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$76, DW_AT_name("SYSCTL_PERIPH_CLK_EQEP2")
	.dwattr $C$DW$76, DW_AT_const_value(0x104)
	.dwattr $C$DW$76, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$76, DW_AT_decl_line(0x17f)
	.dwattr $C$DW$76, DW_AT_decl_column(0x05)

$C$DW$77	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$77, DW_AT_name("SYSCTL_PERIPH_CLK_EQEP3")
	.dwattr $C$DW$77, DW_AT_const_value(0x204)
	.dwattr $C$DW$77, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$77, DW_AT_decl_line(0x180)
	.dwattr $C$DW$77, DW_AT_decl_column(0x05)

$C$DW$78	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$78, DW_AT_name("SYSCTL_PERIPH_CLK_SCIA")
	.dwattr $C$DW$78, DW_AT_const_value(0x07)
	.dwattr $C$DW$78, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$78, DW_AT_decl_line(0x181)
	.dwattr $C$DW$78, DW_AT_decl_column(0x05)

$C$DW$79	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$79, DW_AT_name("SYSCTL_PERIPH_CLK_SCIB")
	.dwattr $C$DW$79, DW_AT_const_value(0x107)
	.dwattr $C$DW$79, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$79, DW_AT_decl_line(0x182)
	.dwattr $C$DW$79, DW_AT_decl_column(0x05)

$C$DW$80	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$80, DW_AT_name("SYSCTL_PERIPH_CLK_SCIC")
	.dwattr $C$DW$80, DW_AT_const_value(0x207)
	.dwattr $C$DW$80, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$80, DW_AT_decl_line(0x183)
	.dwattr $C$DW$80, DW_AT_decl_column(0x05)

$C$DW$81	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$81, DW_AT_name("SYSCTL_PERIPH_CLK_SPIA")
	.dwattr $C$DW$81, DW_AT_const_value(0x08)
	.dwattr $C$DW$81, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$81, DW_AT_decl_line(0x184)
	.dwattr $C$DW$81, DW_AT_decl_column(0x05)

$C$DW$82	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$82, DW_AT_name("SYSCTL_PERIPH_CLK_SPIB")
	.dwattr $C$DW$82, DW_AT_const_value(0x108)
	.dwattr $C$DW$82, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$82, DW_AT_decl_line(0x185)
	.dwattr $C$DW$82, DW_AT_decl_column(0x05)

$C$DW$83	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$83, DW_AT_name("SYSCTL_PERIPH_CLK_I2CA")
	.dwattr $C$DW$83, DW_AT_const_value(0x09)
	.dwattr $C$DW$83, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$83, DW_AT_decl_line(0x186)
	.dwattr $C$DW$83, DW_AT_decl_column(0x05)

$C$DW$84	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$84, DW_AT_name("SYSCTL_PERIPH_CLK_I2CB")
	.dwattr $C$DW$84, DW_AT_const_value(0x109)
	.dwattr $C$DW$84, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$84, DW_AT_decl_line(0x187)
	.dwattr $C$DW$84, DW_AT_decl_column(0x05)

$C$DW$85	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$85, DW_AT_name("SYSCTL_PERIPH_CLK_MCANA")
	.dwattr $C$DW$85, DW_AT_const_value(0x40a)
	.dwattr $C$DW$85, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$85, DW_AT_decl_line(0x188)
	.dwattr $C$DW$85, DW_AT_decl_column(0x05)

$C$DW$86	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$86, DW_AT_name("SYSCTL_PERIPH_CLK_MCANB")
	.dwattr $C$DW$86, DW_AT_const_value(0x50a)
	.dwattr $C$DW$86, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$86, DW_AT_decl_line(0x189)
	.dwattr $C$DW$86, DW_AT_decl_column(0x05)

$C$DW$87	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$87, DW_AT_name("SYSCTL_PERIPH_CLK_USBA")
	.dwattr $C$DW$87, DW_AT_const_value(0x100b)
	.dwattr $C$DW$87, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$87, DW_AT_decl_line(0x18a)
	.dwattr $C$DW$87, DW_AT_decl_column(0x05)

$C$DW$88	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$88, DW_AT_name("SYSCTL_PERIPH_CLK_NPU")
	.dwattr $C$DW$88, DW_AT_const_value(0x0c)
	.dwattr $C$DW$88, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$88, DW_AT_decl_line(0x18b)
	.dwattr $C$DW$88, DW_AT_decl_column(0x05)

$C$DW$89	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$89, DW_AT_name("SYSCTL_PERIPH_CLK_ADCA")
	.dwattr $C$DW$89, DW_AT_const_value(0x0d)
	.dwattr $C$DW$89, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$89, DW_AT_decl_line(0x18c)
	.dwattr $C$DW$89, DW_AT_decl_column(0x05)

$C$DW$90	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$90, DW_AT_name("SYSCTL_PERIPH_CLK_ADCB")
	.dwattr $C$DW$90, DW_AT_const_value(0x10d)
	.dwattr $C$DW$90, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$90, DW_AT_decl_line(0x18d)
	.dwattr $C$DW$90, DW_AT_decl_column(0x05)

$C$DW$91	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$91, DW_AT_name("SYSCTL_PERIPH_CLK_ADCC")
	.dwattr $C$DW$91, DW_AT_const_value(0x20d)
	.dwattr $C$DW$91, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$91, DW_AT_decl_line(0x18e)
	.dwattr $C$DW$91, DW_AT_decl_column(0x05)

$C$DW$92	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$92, DW_AT_name("SYSCTL_PERIPH_CLK_ADCD")
	.dwattr $C$DW$92, DW_AT_const_value(0x30d)
	.dwattr $C$DW$92, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$92, DW_AT_decl_line(0x18f)
	.dwattr $C$DW$92, DW_AT_decl_column(0x05)

$C$DW$93	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$93, DW_AT_name("SYSCTL_PERIPH_CLK_ADCE")
	.dwattr $C$DW$93, DW_AT_const_value(0x40d)
	.dwattr $C$DW$93, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$93, DW_AT_decl_line(0x190)
	.dwattr $C$DW$93, DW_AT_decl_column(0x05)

$C$DW$94	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$94, DW_AT_name("SYSCTL_PERIPH_CLK_CMPSS1")
	.dwattr $C$DW$94, DW_AT_const_value(0x0e)
	.dwattr $C$DW$94, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$94, DW_AT_decl_line(0x191)
	.dwattr $C$DW$94, DW_AT_decl_column(0x05)

$C$DW$95	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$95, DW_AT_name("SYSCTL_PERIPH_CLK_CMPSS2")
	.dwattr $C$DW$95, DW_AT_const_value(0x10e)
	.dwattr $C$DW$95, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$95, DW_AT_decl_line(0x192)
	.dwattr $C$DW$95, DW_AT_decl_column(0x05)

$C$DW$96	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$96, DW_AT_name("SYSCTL_PERIPH_CLK_CMPSS3")
	.dwattr $C$DW$96, DW_AT_const_value(0x20e)
	.dwattr $C$DW$96, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$96, DW_AT_decl_line(0x193)
	.dwattr $C$DW$96, DW_AT_decl_column(0x05)

$C$DW$97	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$97, DW_AT_name("SYSCTL_PERIPH_CLK_CMPSS4")
	.dwattr $C$DW$97, DW_AT_const_value(0x30e)
	.dwattr $C$DW$97, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$97, DW_AT_decl_line(0x194)
	.dwattr $C$DW$97, DW_AT_decl_column(0x05)

$C$DW$98	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$98, DW_AT_name("SYSCTL_PERIPH_CLK_PGA1")
	.dwattr $C$DW$98, DW_AT_const_value(0x0f)
	.dwattr $C$DW$98, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$98, DW_AT_decl_line(0x195)
	.dwattr $C$DW$98, DW_AT_decl_column(0x05)

$C$DW$99	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$99, DW_AT_name("SYSCTL_PERIPH_CLK_PGA2")
	.dwattr $C$DW$99, DW_AT_const_value(0x10f)
	.dwattr $C$DW$99, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$99, DW_AT_decl_line(0x196)
	.dwattr $C$DW$99, DW_AT_decl_column(0x05)

$C$DW$100	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$100, DW_AT_name("SYSCTL_PERIPH_CLK_PGA3")
	.dwattr $C$DW$100, DW_AT_const_value(0x20f)
	.dwattr $C$DW$100, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$100, DW_AT_decl_line(0x197)
	.dwattr $C$DW$100, DW_AT_decl_column(0x05)

$C$DW$101	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$101, DW_AT_name("SYSCTL_PERIPH_CLK_DACA")
	.dwattr $C$DW$101, DW_AT_const_value(0x1010)
	.dwattr $C$DW$101, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$101, DW_AT_decl_line(0x198)
	.dwattr $C$DW$101, DW_AT_decl_column(0x05)

$C$DW$102	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$102, DW_AT_name("SYSCTL_PERIPH_CLK_CLB1")
	.dwattr $C$DW$102, DW_AT_const_value(0x11)
	.dwattr $C$DW$102, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$102, DW_AT_decl_line(0x199)
	.dwattr $C$DW$102, DW_AT_decl_column(0x05)

$C$DW$103	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$103, DW_AT_name("SYSCTL_PERIPH_CLK_CLB2")
	.dwattr $C$DW$103, DW_AT_const_value(0x111)
	.dwattr $C$DW$103, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$103, DW_AT_decl_line(0x19a)
	.dwattr $C$DW$103, DW_AT_decl_column(0x05)

$C$DW$104	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$104, DW_AT_name("SYSCTL_PERIPH_CLK_FSITXA")
	.dwattr $C$DW$104, DW_AT_const_value(0x12)
	.dwattr $C$DW$104, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$104, DW_AT_decl_line(0x19b)
	.dwattr $C$DW$104, DW_AT_decl_column(0x05)

$C$DW$105	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$105, DW_AT_name("SYSCTL_PERIPH_CLK_FSIRXA")
	.dwattr $C$DW$105, DW_AT_const_value(0x112)
	.dwattr $C$DW$105, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$105, DW_AT_decl_line(0x19c)
	.dwattr $C$DW$105, DW_AT_decl_column(0x05)

$C$DW$106	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$106, DW_AT_name("SYSCTL_PERIPH_CLK_LINA")
	.dwattr $C$DW$106, DW_AT_const_value(0x13)
	.dwattr $C$DW$106, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$106, DW_AT_decl_line(0x19d)
	.dwattr $C$DW$106, DW_AT_decl_column(0x05)

$C$DW$107	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$107, DW_AT_name("SYSCTL_PERIPH_CLK_PMBUSA")
	.dwattr $C$DW$107, DW_AT_const_value(0x14)
	.dwattr $C$DW$107, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$107, DW_AT_decl_line(0x19e)
	.dwattr $C$DW$107, DW_AT_decl_column(0x05)

$C$DW$108	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$108, DW_AT_name("SYSCTL_PERIPH_CLK_DCC0")
	.dwattr $C$DW$108, DW_AT_const_value(0x15)
	.dwattr $C$DW$108, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$108, DW_AT_decl_line(0x19f)
	.dwattr $C$DW$108, DW_AT_decl_column(0x05)

$C$DW$109	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$109, DW_AT_name("SYSCTL_PERIPH_CLK_DCC1")
	.dwattr $C$DW$109, DW_AT_const_value(0x115)
	.dwattr $C$DW$109, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$109, DW_AT_decl_line(0x1a0)
	.dwattr $C$DW$109, DW_AT_decl_column(0x05)

$C$DW$110	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$110, DW_AT_name("SYSCTL_PERIPH_CLK_AESA")
	.dwattr $C$DW$110, DW_AT_const_value(0x1a)
	.dwattr $C$DW$110, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$110, DW_AT_decl_line(0x1a1)
	.dwattr $C$DW$110, DW_AT_decl_column(0x05)

$C$DW$111	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$111, DW_AT_name("SYSCTL_PERIPH_CLK_EPG1")
	.dwattr $C$DW$111, DW_AT_const_value(0x1b)
	.dwattr $C$DW$111, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$111, DW_AT_decl_line(0x1a2)
	.dwattr $C$DW$111, DW_AT_decl_column(0x05)

	.dwattr $C$DW$T$28, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$T$28, DW_AT_decl_line(0x167)
	.dwattr $C$DW$T$28, DW_AT_decl_column(0x01)
	.dwendtag $C$DW$T$28

	.dwendtag $C$DW$TU$28


$C$DW$TU$29	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$29
$C$DW$T$29	.dwtag  DW_TAG_typedef
	.dwattr $C$DW$T$29, DW_AT_name("SysCtl_PeripheralPCLOCKCR")
	.dwattr $C$DW$T$29, DW_AT_type(*$C$DW$T$28)
	.dwattr $C$DW$T$29, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$T$29, DW_AT_decl_line(0x1a3)
	.dwattr $C$DW$T$29, DW_AT_decl_column(0x03)

	.dwendtag $C$DW$TU$29


$C$DW$TU$30	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$30

$C$DW$T$30	.dwtag  DW_TAG_enumeration_type
	.dwattr $C$DW$T$30, DW_AT_byte_size(0x01)
$C$DW$112	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$112, DW_AT_name("SYSCTL_NPUCLK_DIV_1")
	.dwattr $C$DW$112, DW_AT_const_value(0x00)
	.dwattr $C$DW$112, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$112, DW_AT_decl_line(0x25c)
	.dwattr $C$DW$112, DW_AT_decl_column(0x05)

$C$DW$113	.dwtag  DW_TAG_enumerator
	.dwattr $C$DW$113, DW_AT_name("SYSCTL_NPUCLK_DIV_2")
	.dwattr $C$DW$113, DW_AT_const_value(0x01)
	.dwattr $C$DW$113, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$113, DW_AT_decl_line(0x25d)
	.dwattr $C$DW$113, DW_AT_decl_column(0x05)

	.dwattr $C$DW$T$30, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$T$30, DW_AT_decl_line(0x25b)
	.dwattr $C$DW$T$30, DW_AT_decl_column(0x01)
	.dwendtag $C$DW$T$30

	.dwendtag $C$DW$TU$30


$C$DW$TU$31	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$31
$C$DW$T$31	.dwtag  DW_TAG_typedef
	.dwattr $C$DW$T$31, DW_AT_name("SysCtl_NPUCLKDivider")
	.dwattr $C$DW$T$31, DW_AT_type(*$C$DW$T$30)
	.dwattr $C$DW$T$31, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\sysctl.h")
	.dwattr $C$DW$T$31, DW_AT_decl_line(0x25e)
	.dwattr $C$DW$T$31, DW_AT_decl_column(0x03)

	.dwendtag $C$DW$TU$31


$C$DW$TU$27	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$27

$C$DW$T$27	.dwtag  DW_TAG_structure_type
	.dwattr $C$DW$T$27, DW_AT_byte_size(0x12)
$C$DW$114	.dwtag  DW_TAG_member
	.dwattr $C$DW$114, DW_AT_type(*$C$DW$T$20)
	.dwattr $C$DW$114, DW_AT_name("num_mmrs")
	.dwattr $C$DW$114, DW_AT_accessibility(DW_ACCESS_public)
	.dwattr $C$DW$114, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\review_20261003\npu_integration_20261009\nnc211_env\Lib\site-packages\tvm\3rdparty\tinie-api\hard/inc/tinie.h")
	.dwattr $C$DW$114, DW_AT_decl_line(0x7b)
	.dwattr $C$DW$114, DW_AT_decl_column(0x0f)

$C$DW$115	.dwtag  DW_TAG_member
	.dwattr $C$DW$115, DW_AT_type(*$C$DW$T$20)
	.dwattr $C$DW$115, DW_AT_name("num_params")
	.dwattr $C$DW$115, DW_AT_data_member_location[DW_OP_plus_uconst 0x2]
	.dwattr $C$DW$115, DW_AT_accessibility(DW_ACCESS_public)
	.dwattr $C$DW$115, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\review_20261003\npu_integration_20261009\nnc211_env\Lib\site-packages\tvm\3rdparty\tinie-api\hard/inc/tinie.h")
	.dwattr $C$DW$115, DW_AT_decl_line(0x7c)
	.dwattr $C$DW$115, DW_AT_decl_column(0x0f)

$C$DW$116	.dwtag  DW_TAG_member
	.dwattr $C$DW$116, DW_AT_type(*$C$DW$T$20)
	.dwattr $C$DW$116, DW_AT_name("num_ins")
	.dwattr $C$DW$116, DW_AT_data_member_location[DW_OP_plus_uconst 0x4]
	.dwattr $C$DW$116, DW_AT_accessibility(DW_ACCESS_public)
	.dwattr $C$DW$116, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\review_20261003\npu_integration_20261009\nnc211_env\Lib\site-packages\tvm\3rdparty\tinie-api\hard/inc/tinie.h")
	.dwattr $C$DW$116, DW_AT_decl_line(0x7d)
	.dwattr $C$DW$116, DW_AT_decl_column(0x0f)

$C$DW$117	.dwtag  DW_TAG_member
	.dwattr $C$DW$117, DW_AT_type(*$C$DW$T$22)
	.dwattr $C$DW$117, DW_AT_name("mmrs")
	.dwattr $C$DW$117, DW_AT_data_member_location[DW_OP_plus_uconst 0x6]
	.dwattr $C$DW$117, DW_AT_accessibility(DW_ACCESS_public)
	.dwattr $C$DW$117, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\review_20261003\npu_integration_20261009\nnc211_env\Lib\site-packages\tvm\3rdparty\tinie-api\hard/inc/tinie.h")
	.dwattr $C$DW$117, DW_AT_decl_line(0x7e)
	.dwattr $C$DW$117, DW_AT_decl_column(0x15)

$C$DW$118	.dwtag  DW_TAG_member
	.dwattr $C$DW$118, DW_AT_type(*$C$DW$T$22)
	.dwattr $C$DW$118, DW_AT_name("params")
	.dwattr $C$DW$118, DW_AT_data_member_location[DW_OP_plus_uconst 0x8]
	.dwattr $C$DW$118, DW_AT_accessibility(DW_ACCESS_public)
	.dwattr $C$DW$118, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\review_20261003\npu_integration_20261009\nnc211_env\Lib\site-packages\tvm\3rdparty\tinie-api\hard/inc/tinie.h")
	.dwattr $C$DW$118, DW_AT_decl_line(0x7f)
	.dwattr $C$DW$118, DW_AT_decl_column(0x15)

$C$DW$119	.dwtag  DW_TAG_member
	.dwattr $C$DW$119, DW_AT_type(*$C$DW$T$22)
	.dwattr $C$DW$119, DW_AT_name("ins")
	.dwattr $C$DW$119, DW_AT_data_member_location[DW_OP_plus_uconst 0xa]
	.dwattr $C$DW$119, DW_AT_accessibility(DW_ACCESS_public)
	.dwattr $C$DW$119, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\review_20261003\npu_integration_20261009\nnc211_env\Lib\site-packages\tvm\3rdparty\tinie-api\hard/inc/tinie.h")
	.dwattr $C$DW$119, DW_AT_decl_line(0x80)
	.dwattr $C$DW$119, DW_AT_decl_column(0x15)

$C$DW$120	.dwtag  DW_TAG_member
	.dwattr $C$DW$120, DW_AT_type(*$C$DW$T$26)
	.dwattr $C$DW$120, DW_AT_name("in_fmap")
	.dwattr $C$DW$120, DW_AT_data_member_location[DW_OP_plus_uconst 0xc]
	.dwattr $C$DW$120, DW_AT_accessibility(DW_ACCESS_public)
	.dwattr $C$DW$120, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\review_20261003\npu_integration_20261009\nnc211_env\Lib\site-packages\tvm\3rdparty\tinie-api\hard/inc/tinie.h")
	.dwattr $C$DW$120, DW_AT_decl_line(0x81)
	.dwattr $C$DW$120, DW_AT_decl_column(0x0f)

$C$DW$121	.dwtag  DW_TAG_member
	.dwattr $C$DW$121, DW_AT_type(*$C$DW$T$26)
	.dwattr $C$DW$121, DW_AT_name("residual_fmap")
	.dwattr $C$DW$121, DW_AT_data_member_location[DW_OP_plus_uconst 0xe]
	.dwattr $C$DW$121, DW_AT_accessibility(DW_ACCESS_public)
	.dwattr $C$DW$121, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\review_20261003\npu_integration_20261009\nnc211_env\Lib\site-packages\tvm\3rdparty\tinie-api\hard/inc/tinie.h")
	.dwattr $C$DW$121, DW_AT_decl_line(0x82)
	.dwattr $C$DW$121, DW_AT_decl_column(0x0f)

$C$DW$122	.dwtag  DW_TAG_member
	.dwattr $C$DW$122, DW_AT_type(*$C$DW$T$26)
	.dwattr $C$DW$122, DW_AT_name("out_fmap")
	.dwattr $C$DW$122, DW_AT_data_member_location[DW_OP_plus_uconst 0x10]
	.dwattr $C$DW$122, DW_AT_accessibility(DW_ACCESS_public)
	.dwattr $C$DW$122, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\review_20261003\npu_integration_20261009\nnc211_env\Lib\site-packages\tvm\3rdparty\tinie-api\hard/inc/tinie.h")
	.dwattr $C$DW$122, DW_AT_decl_line(0x83)
	.dwattr $C$DW$122, DW_AT_decl_column(0x0f)

	.dwattr $C$DW$T$27, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\review_20261003\npu_integration_20261009\nnc211_env\Lib\site-packages\tvm\3rdparty\tinie-api\hard/inc/tinie.h")
	.dwattr $C$DW$T$27, DW_AT_decl_line(0x7a)
	.dwattr $C$DW$T$27, DW_AT_decl_column(0x01)
	.dwendtag $C$DW$T$27

	.dwendtag $C$DW$TU$27


$C$DW$TU$32	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$32
$C$DW$T$32	.dwtag  DW_TAG_typedef
	.dwattr $C$DW$T$32, DW_AT_name("TINIE_layer_t")
	.dwattr $C$DW$T$32, DW_AT_type(*$C$DW$T$27)
	.dwattr $C$DW$T$32, DW_AT_decl_file("D:\Project_File\Design_Optimization\F28P550Project\ccs_projects\review_20261003\npu_integration_20261009\nnc211_env\Lib\site-packages\tvm\3rdparty\tinie-api\hard/inc/tinie.h")
	.dwattr $C$DW$T$32, DW_AT_decl_line(0x84)
	.dwattr $C$DW$T$32, DW_AT_decl_column(0x03)

	.dwendtag $C$DW$TU$32


$C$DW$TU$33	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$33
$C$DW$T$33	.dwtag  DW_TAG_pointer_type
	.dwattr $C$DW$T$33, DW_AT_type(*$C$DW$T$32)
	.dwattr $C$DW$T$33, DW_AT_address_class(0x20)

	.dwendtag $C$DW$TU$33


$C$DW$TU$34	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$34
$C$DW$123	.dwtag  DW_TAG_TI_far_type
	.dwattr $C$DW$123, DW_AT_type(*$C$DW$T$33)

$C$DW$T$34	.dwtag  DW_TAG_const_type
	.dwattr $C$DW$T$34, DW_AT_type(*$C$DW$123)

	.dwendtag $C$DW$TU$34


$C$DW$TU$2	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$2
$C$DW$T$2	.dwtag  DW_TAG_unspecified_type
	.dwattr $C$DW$T$2, DW_AT_name("void")

	.dwendtag $C$DW$TU$2


$C$DW$TU$37	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$37

$C$DW$T$37	.dwtag  DW_TAG_subroutine_type
	.dwendtag $C$DW$T$37

	.dwendtag $C$DW$TU$37


$C$DW$TU$38	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$38
$C$DW$T$38	.dwtag  DW_TAG_pointer_type
	.dwattr $C$DW$T$38, DW_AT_type(*$C$DW$T$37)
	.dwattr $C$DW$T$38, DW_AT_address_class(0x20)

	.dwendtag $C$DW$TU$38


$C$DW$TU$39	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$39
$C$DW$124	.dwtag  DW_TAG_TI_far_type
	.dwattr $C$DW$124, DW_AT_type(*$C$DW$T$38)

$C$DW$T$39	.dwtag  DW_TAG_const_type
	.dwattr $C$DW$T$39, DW_AT_type(*$C$DW$124)

	.dwendtag $C$DW$TU$39


$C$DW$TU$4	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$4
$C$DW$T$4	.dwtag  DW_TAG_base_type
	.dwattr $C$DW$T$4, DW_AT_encoding(DW_ATE_boolean)
	.dwattr $C$DW$T$4, DW_AT_name("bool")
	.dwattr $C$DW$T$4, DW_AT_byte_size(0x01)

	.dwendtag $C$DW$TU$4


$C$DW$TU$5	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$5
$C$DW$T$5	.dwtag  DW_TAG_base_type
	.dwattr $C$DW$T$5, DW_AT_encoding(DW_ATE_signed_char)
	.dwattr $C$DW$T$5, DW_AT_name("signed char")
	.dwattr $C$DW$T$5, DW_AT_byte_size(0x01)

	.dwendtag $C$DW$TU$5


$C$DW$TU$6	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$6
$C$DW$T$6	.dwtag  DW_TAG_base_type
	.dwattr $C$DW$T$6, DW_AT_encoding(DW_ATE_unsigned_char)
	.dwattr $C$DW$T$6, DW_AT_name("unsigned char")
	.dwattr $C$DW$T$6, DW_AT_byte_size(0x01)

	.dwendtag $C$DW$TU$6


$C$DW$TU$7	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$7
$C$DW$T$7	.dwtag  DW_TAG_base_type
	.dwattr $C$DW$T$7, DW_AT_encoding(DW_ATE_signed_char)
	.dwattr $C$DW$T$7, DW_AT_name("wchar_t")
	.dwattr $C$DW$T$7, DW_AT_byte_size(0x02)

	.dwendtag $C$DW$TU$7


$C$DW$TU$8	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$8
$C$DW$T$8	.dwtag  DW_TAG_base_type
	.dwattr $C$DW$T$8, DW_AT_encoding(DW_ATE_signed)
	.dwattr $C$DW$T$8, DW_AT_name("short")
	.dwattr $C$DW$T$8, DW_AT_byte_size(0x01)

	.dwendtag $C$DW$TU$8


$C$DW$TU$9	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$9
$C$DW$T$9	.dwtag  DW_TAG_base_type
	.dwattr $C$DW$T$9, DW_AT_encoding(DW_ATE_unsigned)
	.dwattr $C$DW$T$9, DW_AT_name("unsigned short")
	.dwattr $C$DW$T$9, DW_AT_byte_size(0x01)

	.dwendtag $C$DW$TU$9


$C$DW$TU$10	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$10
$C$DW$T$10	.dwtag  DW_TAG_base_type
	.dwattr $C$DW$T$10, DW_AT_encoding(DW_ATE_signed)
	.dwattr $C$DW$T$10, DW_AT_name("int")
	.dwattr $C$DW$T$10, DW_AT_byte_size(0x01)

	.dwendtag $C$DW$TU$10


$C$DW$TU$56	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$56
$C$DW$T$56	.dwtag  DW_TAG_pointer_type
	.dwattr $C$DW$T$56, DW_AT_type(*$C$DW$T$10)
	.dwattr $C$DW$T$56, DW_AT_address_class(0x20)

	.dwendtag $C$DW$TU$56


$C$DW$TU$23	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$23
$C$DW$T$23	.dwtag  DW_TAG_typedef
	.dwattr $C$DW$T$23, DW_AT_name("__int16_t")
	.dwattr $C$DW$T$23, DW_AT_type(*$C$DW$T$10)
	.dwattr $C$DW$T$23, DW_AT_decl_file("E:\Software_Download\ti\ccs2020\ccs\tools\compiler\ti-cgt-c2000_22.6.2.LTS\include\machine/_types.h")
	.dwattr $C$DW$T$23, DW_AT_decl_line(0x40)
	.dwattr $C$DW$T$23, DW_AT_decl_column(0x1d)

	.dwendtag $C$DW$TU$23


$C$DW$TU$24	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$24
$C$DW$T$24	.dwtag  DW_TAG_typedef
	.dwattr $C$DW$T$24, DW_AT_name("int16_t")
	.dwattr $C$DW$T$24, DW_AT_type(*$C$DW$T$23)
	.dwattr $C$DW$T$24, DW_AT_decl_file("E:\Software_Download\ti\ccs2020\ccs\tools\compiler\ti-cgt-c2000_22.6.2.LTS\include\sys/_stdint.h")
	.dwattr $C$DW$T$24, DW_AT_decl_line(0x2b)
	.dwattr $C$DW$T$24, DW_AT_decl_column(0x14)

	.dwendtag $C$DW$TU$24


$C$DW$TU$25	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$25
$C$DW$T$25	.dwtag  DW_TAG_typedef
	.dwattr $C$DW$T$25, DW_AT_name("int8_t")
	.dwattr $C$DW$T$25, DW_AT_type(*$C$DW$T$24)
	.dwattr $C$DW$T$25, DW_AT_decl_file("E:\Software_Download\ti\c2000\C2000Ware_DigitalPower_SDK_5_05_01_00\c2000ware\driverlib\f28p55x\driverlib\inc/hw_types.h")
	.dwattr $C$DW$T$25, DW_AT_decl_line(0x6e)
	.dwattr $C$DW$T$25, DW_AT_decl_column(0x11)

	.dwendtag $C$DW$TU$25


$C$DW$TU$26	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$26
$C$DW$T$26	.dwtag  DW_TAG_pointer_type
	.dwattr $C$DW$T$26, DW_AT_type(*$C$DW$T$25)
	.dwattr $C$DW$T$26, DW_AT_address_class(0x20)

	.dwendtag $C$DW$TU$26


$C$DW$TU$11	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$11
$C$DW$T$11	.dwtag  DW_TAG_base_type
	.dwattr $C$DW$T$11, DW_AT_encoding(DW_ATE_unsigned)
	.dwattr $C$DW$T$11, DW_AT_name("unsigned int")
	.dwattr $C$DW$T$11, DW_AT_byte_size(0x01)

	.dwendtag $C$DW$TU$11


$C$DW$TU$41	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$41
$C$DW$T$41	.dwtag  DW_TAG_typedef
	.dwattr $C$DW$T$41, DW_AT_name("__uint16_t")
	.dwattr $C$DW$T$41, DW_AT_type(*$C$DW$T$11)
	.dwattr $C$DW$T$41, DW_AT_decl_file("E:\Software_Download\ti\ccs2020\ccs\tools\compiler\ti-cgt-c2000_22.6.2.LTS\include\machine/_types.h")
	.dwattr $C$DW$T$41, DW_AT_decl_line(0x41)
	.dwattr $C$DW$T$41, DW_AT_decl_column(0x1c)

	.dwendtag $C$DW$TU$41


$C$DW$TU$42	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$42
$C$DW$T$42	.dwtag  DW_TAG_typedef
	.dwattr $C$DW$T$42, DW_AT_name("uint16_t")
	.dwattr $C$DW$T$42, DW_AT_type(*$C$DW$T$41)
	.dwattr $C$DW$T$42, DW_AT_decl_file("E:\Software_Download\ti\ccs2020\ccs\tools\compiler\ti-cgt-c2000_22.6.2.LTS\include\sys/_stdint.h")
	.dwattr $C$DW$T$42, DW_AT_decl_line(0x41)
	.dwattr $C$DW$T$42, DW_AT_decl_column(0x15)

	.dwendtag $C$DW$TU$42


$C$DW$TU$12	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$12
$C$DW$T$12	.dwtag  DW_TAG_base_type
	.dwattr $C$DW$T$12, DW_AT_encoding(DW_ATE_signed)
	.dwattr $C$DW$T$12, DW_AT_name("long")
	.dwattr $C$DW$T$12, DW_AT_byte_size(0x02)

	.dwendtag $C$DW$TU$12


$C$DW$TU$13	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$13
$C$DW$T$13	.dwtag  DW_TAG_base_type
	.dwattr $C$DW$T$13, DW_AT_encoding(DW_ATE_unsigned)
	.dwattr $C$DW$T$13, DW_AT_name("unsigned long")
	.dwattr $C$DW$T$13, DW_AT_byte_size(0x02)

	.dwendtag $C$DW$TU$13


$C$DW$TU$19	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$19
$C$DW$T$19	.dwtag  DW_TAG_typedef
	.dwattr $C$DW$T$19, DW_AT_name("__uint32_t")
	.dwattr $C$DW$T$19, DW_AT_type(*$C$DW$T$13)
	.dwattr $C$DW$T$19, DW_AT_decl_file("E:\Software_Download\ti\ccs2020\ccs\tools\compiler\ti-cgt-c2000_22.6.2.LTS\include\machine/_types.h")
	.dwattr $C$DW$T$19, DW_AT_decl_line(0x43)
	.dwattr $C$DW$T$19, DW_AT_decl_column(0x1c)

	.dwendtag $C$DW$TU$19


$C$DW$TU$20	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$20
$C$DW$T$20	.dwtag  DW_TAG_typedef
	.dwattr $C$DW$T$20, DW_AT_name("uint32_t")
	.dwattr $C$DW$T$20, DW_AT_type(*$C$DW$T$19)
	.dwattr $C$DW$T$20, DW_AT_decl_file("E:\Software_Download\ti\ccs2020\ccs\tools\compiler\ti-cgt-c2000_22.6.2.LTS\include\sys/_stdint.h")
	.dwattr $C$DW$T$20, DW_AT_decl_line(0x46)
	.dwattr $C$DW$T$20, DW_AT_decl_column(0x15)

	.dwendtag $C$DW$TU$20


$C$DW$TU$21	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$21
$C$DW$125	.dwtag  DW_TAG_TI_far_type
	.dwattr $C$DW$125, DW_AT_type(*$C$DW$T$20)

$C$DW$T$21	.dwtag  DW_TAG_const_type
	.dwattr $C$DW$T$21, DW_AT_type(*$C$DW$125)

	.dwendtag $C$DW$TU$21


$C$DW$TU$22	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$22
$C$DW$T$22	.dwtag  DW_TAG_pointer_type
	.dwattr $C$DW$T$22, DW_AT_type(*$C$DW$T$21)
	.dwattr $C$DW$T$22, DW_AT_address_class(0x20)

	.dwendtag $C$DW$TU$22


$C$DW$TU$48	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$48
$C$DW$126	.dwtag  DW_TAG_TI_far_type
	.dwattr $C$DW$126, DW_AT_type(*$C$DW$T$20)

$C$DW$T$48	.dwtag  DW_TAG_volatile_type
	.dwattr $C$DW$T$48, DW_AT_type(*$C$DW$126)

	.dwendtag $C$DW$TU$48


$C$DW$TU$49	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$49
$C$DW$T$49	.dwtag  DW_TAG_pointer_type
	.dwattr $C$DW$T$49, DW_AT_type(*$C$DW$T$48)
	.dwattr $C$DW$T$49, DW_AT_address_class(0x20)

	.dwendtag $C$DW$TU$49


$C$DW$TU$14	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$14
$C$DW$T$14	.dwtag  DW_TAG_base_type
	.dwattr $C$DW$T$14, DW_AT_encoding(DW_ATE_signed)
	.dwattr $C$DW$T$14, DW_AT_name("long long")
	.dwattr $C$DW$T$14, DW_AT_byte_size(0x04)

	.dwendtag $C$DW$TU$14


$C$DW$TU$15	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$15
$C$DW$T$15	.dwtag  DW_TAG_base_type
	.dwattr $C$DW$T$15, DW_AT_encoding(DW_ATE_unsigned)
	.dwattr $C$DW$T$15, DW_AT_name("unsigned long long")
	.dwattr $C$DW$T$15, DW_AT_byte_size(0x04)

	.dwendtag $C$DW$TU$15


$C$DW$TU$16	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$16
$C$DW$T$16	.dwtag  DW_TAG_base_type
	.dwattr $C$DW$T$16, DW_AT_encoding(DW_ATE_float)
	.dwattr $C$DW$T$16, DW_AT_name("float")
	.dwattr $C$DW$T$16, DW_AT_byte_size(0x02)

	.dwendtag $C$DW$TU$16


$C$DW$TU$17	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$17
$C$DW$T$17	.dwtag  DW_TAG_base_type
	.dwattr $C$DW$T$17, DW_AT_encoding(DW_ATE_float)
	.dwattr $C$DW$T$17, DW_AT_name("double")
	.dwattr $C$DW$T$17, DW_AT_byte_size(0x04)

	.dwendtag $C$DW$TU$17


$C$DW$TU$18	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$18
$C$DW$T$18	.dwtag  DW_TAG_base_type
	.dwattr $C$DW$T$18, DW_AT_encoding(DW_ATE_float)
	.dwattr $C$DW$T$18, DW_AT_name("long double")
	.dwattr $C$DW$T$18, DW_AT_byte_size(0x04)

	.dwendtag $C$DW$TU$18


$C$DW$TU$65	.dwtag  DW_TAG_type_unit
	.dwmtype  $C$DW$T$65
$C$DW$T$65	.dwtag  DW_TAG_base_type
	.dwattr $C$DW$T$65, DW_AT_encoding(DW_ATE_unsigned_char)
	.dwattr $C$DW$T$65, DW_AT_name("unsigned char")
	.dwattr $C$DW$T$65, DW_AT_byte_size(0x01)

	.dwendtag $C$DW$TU$65

