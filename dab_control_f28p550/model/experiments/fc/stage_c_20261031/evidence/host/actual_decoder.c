
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
typedef uint16_t C28_u8;
typedef struct {uint32_t num_mmrs,num_params,num_ins;const uint32_t*mmrs,*params,*ins;void*in_fmap,*residual_fmap,*out_fmap;} TINIE_layer_t;
static volatile uint32_t hw[66];static unsigned writes,mask[33];
#define TINIE_BASE_ADDR ((uintptr_t)hw)
#define TINIE_MMR_OFS 0
#define TINIE_TOTAL_MMRS 33
#define TINIE_CTL2_INDEX 3
#define TINIE_CTL0_INDEX 5
#define TINIE_CTL1_INDEX 4
#define TINIE_MMR0_INDEX 29
#define TINIE_MMR1_INDEX 30
#define TINIE_MMR2_INDEX 31
#define TINIE_MMR3_INDEX 32
#define __byte(p,i) (((const uint8_t*)(const void*)(p))[i])
#define __norm32(v,p) (*(p)=__builtin_clz((unsigned)(v))-1)
static void writeMmr(unsigned offset,uint32_t value){assert(offset%2==0&&offset<66);hw[offset]=value;writes++;mask[offset/2]++;}
static void TINIE_mem_write(volatile uint32_t*dst,uint32_t n,const uint32_t*src){for(unsigned i=0;i<n;++i){writeMmr((unsigned)(dst-hw),*src++);dst+=2;}}
static C28_u8 find_and_clear_lsb_in_31b(uint32_t *val) {

    uint32_t v = *val;
    // clear the non-zero lsb bit for next iteration
    uint32_t v_lsb = v & (v - 1);
    *val = v_lsb;

    // (v - v_lsb) zeros out all bit except the non-zero lsb
    // __norm32() nomalize an integer to 0x40000000, return number of left shift bits
    int shift;
    __norm32((v - v_lsb), &shift);
    return (30 - shift);

}
static void write_configMMR(TINIE_layer_t*layer){

    volatile uint32_t *mmrs = (uint32_t *) (TINIE_BASE_ADDR + TINIE_MMR_OFS);

    // Part 1: Set MMRs except CTL5/4/3/1, MMR0/1  (CTL4/3 not used for now)
    if (layer->num_mmrs == TINIE_TOTAL_MMRS)
    {
        // uncompressed, all entries available
        writeMmr(TINIE_CTL2_INDEX * 2,layer->mmrs[TINIE_CTL2_INDEX]);
        TINIE_mem_write(mmrs + TINIE_CTL0_INDEX * 2, TINIE_MMR0_INDEX - TINIE_CTL0_INDEX,
                        layer->mmrs + TINIE_CTL0_INDEX);
        if (layer->residual_fmap == NULL)
            writeMmr(TINIE_MMR2_INDEX * 2,layer->mmrs[TINIE_MMR2_INDEX]);
        writeMmr(TINIE_MMR3_INDEX * 2,layer->mmrs[TINIE_MMR3_INDEX]);
    }
    else if (layer->num_mmrs > 2)
    {
        // compressed, 2 32-bit bitvecs indicate which entries from CTL4 to MMR3 are set
        // always skip CTL5 in compressed mmrs[] data, so we start from element 1
        uint32_t bitvec_for_32b_val = layer->mmrs[0];
        uint32_t bitvec_for_8b_val  = layer->mmrs[1];
        const uint32_t *p_val = (const uint32_t *) &layer->mmrs[2];
        int32_t  bitvec_31bits;
        C28_u8  pos;

        if (bitvec_for_32b_val != 0)
        {
            bitvec_31bits = bitvec_for_32b_val & 0x7FFFFFFFUL;
            while (bitvec_31bits)
            {
                pos = find_and_clear_lsb_in_31b(&bitvec_31bits);
                writeMmr((1 + pos) * 2,*p_val++);
            }
            if (bitvec_for_32b_val & 0x80000000UL)
            {
                writeMmr((1 + 31) * 2,*p_val++);
            }
        }
        if (bitvec_for_8b_val != 0)
        {
            // 8b values are packed in 32b uint32_ts in little-endian (Cortex-M and C28)
            const C28_u8 *p_8bval = (const C28_u8 *) p_val;
            int count = 0;

            bitvec_31bits = bitvec_for_8b_val & 0x7FFFFFFFUL;
            while (bitvec_31bits)
            {
                pos = find_and_clear_lsb_in_31b(&bitvec_31bits);
                writeMmr((1 + pos) * 2,__byte(p_8bval, count++));
            }
            if (bitvec_for_8b_val & 0x80000000UL)
            {
                writeMmr((1 + 31) * 2,__byte(p_8bval, count++));
            }
        }
    }

    // Part 2: patch CTL1 and a few ARs to point them to correct ifmap/ofmap address values
    //         MMR0 for ifmap, MMR1 for ofmap, MMR2 for residual fmap
    uint32_t ctl1_val =  (((uint32_t)layer->in_fmap  >> 17) & 0xcfff) |
                        ((((uint32_t)layer->out_fmap >> 17) & 0xcfff) << 16);
    writeMmr(TINIE_CTL1_INDEX * 2,ctl1_val);
    writeMmr(TINIE_MMR0_INDEX * 2,((((uint32_t) layer->in_fmap)  >> 1) & 0xffff));
    writeMmr(TINIE_MMR1_INDEX * 2,((((uint32_t) layer->out_fmap) >> 1) & 0xffff));
    if (layer->residual_fmap != NULL)
        writeMmr(TINIE_MMR2_INDEX * 2,((((uint32_t) layer->residual_fmap) >> 1) & 0xffff));

}
static const uint32_t full[4][33]={{0u,0u,0u,16711680u,0u,73416729u,0u,0u,7u,0u,0u,0u,16u,0u,0u,0u,0u,0u,0u,0u,0u,0u,0u,0u,0u,64u,0u,96u,0u,0u,0u,0u,0u},{0u,0u,0u,16711680u,0u,73416721u,0u,0u,3u,2u,0u,0u,16u,0u,0u,0u,0u,0u,0u,0u,0u,0u,0u,0u,0u,64u,0u,80u,0u,0u,0u,0u,0u},{0u,0u,0u,16711680u,0u,73416721u,0u,0u,3u,0u,0u,0u,16u,0u,0u,0u,0u,0u,0u,0u,0u,0u,0u,0u,0u,32u,0u,48u,0u,0u,0u,0u,0u},{0u,0u,0u,8323456u,0u,73416849u,0u,0u,0u,0u,0u,0u,16u,0u,0u,0u,0u,0u,0u,0u,0u,0u,0u,0u,0u,8u,0u,12u,0u,0u,0u,0u,0u}};
static const uint32_t packed[4][6]={{20u,93456768u,16711680u,73416729u,1048583u,1614807040u},{20u,93456768u,16711680u,73416721u,1049091u,1346371584u},{20u,93456768u,16711680u,73416721u,1048579u,807403520u},{20u,93456768u,8323456u,73416849u,1048576u,201850880u}};

int main(void){
 const unsigned live[]={3,5,8,9,12,18,21,24,25,27,4,29,30};
 for(unsigned trial=0;trial<1000;++trial){
  for(unsigned r=0;r<66;++r)hw[r]=0xdead0000u+trial*17+r;
  for(unsigned layer=0;layer<4;++layer){
   uint32_t before[66],expected[66];memcpy(before,(const void*)hw,sizeof before);
   TINIE_layer_t l={0};l.in_fmap=(void*)(uintptr_t)(layer==0?0xe060:layer==2?0xe000:0xe020);
   l.out_fmap=(void*)(uintptr_t)(layer==0?0xe020:layer==1?0xe000:layer==2?0xe020:0xe010);
   l.num_mmrs=33;l.mmrs=full[layer];writes=0;memset(mask,0,sizeof mask);write_configMMR(&l);assert(writes==30);
   memcpy(expected,(const void*)hw,sizeof expected);memcpy((void*)hw,before,sizeof before);
   l.num_mmrs=6;l.mmrs=packed[layer];writes=0;memset(mask,0,sizeof mask);write_configMMR(&l);assert(writes==13);
   for(unsigned k=0;k<sizeof(live)/sizeof(live[0]);++k)assert(hw[2*live[k]]==expected[2*live[k]]);
   for(unsigned r=0;r<33;++r)if(!mask[r])assert(hw[2*r]==before[2*r]);
   // Adversarial execution state between FC layers. All required initial values
   // must be re-established, even if prior hardware mutated an address register.
   for(unsigned r=0;r<33;++r)if(r==12||r==21||r==25||r==27||r==15||r==22)hw[2*r]^=0xa5a50000u+trial+layer;
  }
 }
 uint32_t test[3]={0x80000000u,0,0x12345678};TINIE_layer_t l={0};l.num_mmrs=3;l.mmrs=test;
 write_configMMR(&l);assert(hw[64]==0x12345678);
 test[0]=0;test[1]=0x80000000u;test[2]=0x000000fe;write_configMMR(&l);assert(hw[64]==254);
 puts("PASS: actual decoder, 1000 dirty four-layer chains, all live registers, unchanged omissions, high-mask boundary");return 0;
}
