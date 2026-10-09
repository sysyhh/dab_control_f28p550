MEMORY
{
   BEGIN            : origin = 0x080000, length = 0x000002  // Update the codestart location as needed

   BOOT_RSVD        : origin = 0x000002, length = 0x000126     /* Part of M0, BOOT rom will use this for stack */
   RAMM0            : origin = 0x000128, length = 0x0002D8
   RAMM1            : origin = 0x000400, length = 0x0003F8 // Reserve final 8 words (prefetch erratum)

   RAMLS01          : origin = 0x008000, length = 0x001000 // Contiguous LS0 + LS1 ramfunc run area
   RAMLS2           : origin = 0x009000, length = 0x000800
   RAMLS3           : origin = 0x009800, length = 0x000800
   RAMLS4           : origin = 0x00A000, length = 0x000800
   RAMLS5           : origin = 0x00A800, length = 0x000800
   RAMLS6           : origin = 0x00B000, length = 0x000800
   RAMLS7           : origin = 0x00B800, length = 0x000800
   RAMLS8           : origin = 0x014000, length = 0x002000  // When configured as CLA program use the address 0x4000
   RAMLS9           : origin = 0x016000, length = 0x002000  // When configured as CLA program use the address 0x6000

   // RAMLS8_CLA    : origin = 0x004000, length = 0x002000  // Use only if configured as CLA program memory
   // RAMLS9_CLA    : origin = 0x006000, length = 0x002000  // Use only if configured as CLA program memory

   RAMGS0           : origin = 0x00C000, length = 0x002000
   RAMGS1           : origin = 0x00E000, length = 0x002000

   /* Flash Banks (128 sectors each) */
   FLASH_BANK0     : origin = 0x080002, length = 0x1FFFE
   FLASH_BANK1     : origin = 0x0A0000, length = 0x20000


   CLATOCPURAM      : origin = 0x001480,   length = 0x000080
   CPUTOCLARAM      : origin = 0x001500,   length = 0x000080
   CLATODMARAM      : origin = 0x001680,   length = 0x000080
   DMATOCLARAM      : origin = 0x001700,   length = 0x000080

   RESET            : origin = 0x3FFFC0, length = 0x000002
}


SECTIONS
{
   codestart        : > BEGIN
   .text            : >> FLASH_BANK0 | FLASH_BANK1, ALIGN(8)
   .cinit           : > FLASH_BANK0, ALIGN(8)
   .switch          : > FLASH_BANK0, ALIGN(8)
   .reset           : > RESET, TYPE = DSECT /* not used, */

   .stack           : > RAMM1
#if defined(__TI_EABI__)
   .bss             : > RAMLS5
   .bss:output      : > RAMLS3
   .init_array      : > FLASH_BANK0, ALIGN(8)
   .const           : > FLASH_BANK0, ALIGN(8)
   .data            : > RAMLS5  | RAMLS6
   .sysmem          : > RAMLS4
#else
   .pinit           : > FLASH_BANK0, ALIGN(8)
   .ebss            : >> RAMLS5 | RAMLS6
   .econst          : > FLASH_BANK0, ALIGN(8)
   .esysmem         : > RAMLS5
#endif

   ramgs0 : > RAMGS0
   ramgs1 : > RAMGS1
   .rodata.tvm : > FLASH_BANK1, ALIGN(8)
   .bss.noinit.tvm : > RAMGS1, ALIGN(8), TYPE = NOINIT
   // 权重、指令和配置常量在 LS3 读取；Flash 镜像在初始化时完整复制。
   .dab_npu_const : {} LOAD = FLASH_BANK1,
                      RUN = RAMLS3,
                      LOAD_START(DabNpuConstLoadStart),
                      LOAD_SIZE(DabNpuConstLoadSize),
                      RUN_START(DabNpuConstRunStart),
                      ALIGN(8)
   // NPU 热点代码使用独立 LS2；Flash 保存镜像，DAB_NN_init 在启用 NPU 前复制。
   .dab_npu_ramfunc : {} LOAD = FLASH_BANK0,
                        RUN = RAMLS2,
                        LOAD_START(DabNpuLoadStart),
                        LOAD_SIZE(DabNpuLoadSize),
                        RUN_START(DabNpuRunStart),
                        ALIGN(8)

   #if defined(__TI_EABI__)
       .TI.ramfunc : {} LOAD = FLASH_BANK0,
                        RUN = RAMLS01,
                        LOAD_START(RamfuncsLoadStart),
                        LOAD_SIZE(RamfuncsLoadSize),
                        LOAD_END(RamfuncsLoadEnd),
                        RUN_START(RamfuncsRunStart),
                        RUN_SIZE(RamfuncsRunSize),
                        RUN_END(RamfuncsRunEnd),
                        ALIGN(8)
   #else
       .TI.ramfunc : {} LOAD = FLASH_BANK0,
                        RUN = RAMLS01,
                        LOAD_START(_RamfuncsLoadStart),
                        LOAD_SIZE(_RamfuncsLoadSize),
                        LOAD_END(_RamfuncsLoadEnd),
                        RUN_START(_RamfuncsRunStart),
                        RUN_SIZE(_RamfuncsRunSize),
                        RUN_END(_RamfuncsRunEnd),
                        ALIGN(8)
   #endif

}

-l "E:/Software_Download/ti/c2000/C2000Ware_DigitalPower_SDK_5_05_01_00/c2000ware/driverlib/f28p55x/driverlib/ccs/Release/driverlib.lib"

/*
//===========================================================================
// End of file.
//===========================================================================
*/
