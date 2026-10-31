#include <stdint.h>
#include <assert.h>
#include <stdio.h>
static void copy(volatile uint32_t *dst,uint32_t num,const uint32_t *src){

  int count_by_4 = num >> 2;
  int count_by_1 = num & 0x3;
  if (count_by_4 > 0)
  {
    while (count_by_4--)
    {
      * dst    = *src++;
      *(dst+2) = *src++;
      *(dst+4) = *src++;
      *(dst+6) = *src++;
        dst   += 8;       /* C28 16-bit addressable, access NPU memory accordingly */
    }
  }
  if (count_by_1 > 0)
  {
    while (count_by_1--)
    {
      *dst++ = *src++;
       dst++;             /* C28 16-bit addressable, access NPU memory accordingly */
    }
  }
}
int main(void){
 uint32_t s[512],d[1032];
 for(unsigned n=0;n<=512;++n){
  for(unsigned i=0;i<512;++i)s[i]=i*1234567u+n;
  for(unsigned i=0;i<1032;++i)d[i]=0xa5a5a5a5;
  copy(d+4,n,s);
  for(unsigned i=0;i<1032;++i){
   if(i>=4 && i<4+2*n && !(i&1))assert(d[i]==s[(i-4)/2]);
   else assert(d[i]==0xa5a5a5a5);
  }
 }
 puts("PASS: original copier n=0..512, all data, stride holes and guards");return 0;
}
