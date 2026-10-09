#include "driverlib.h"
#include <string.h>
#include <assert.h>
MockPWM mockPWM[8];
bool mockADCReady[2], mockADCOverflow[2], mockMasked;
uint16_t mockADCResult[2][2], mockDirection[8], mockCounter[8], mockSCI[128];
uint32_t mockTimer, mockDelayUS, mockArmCount, mockWriteCost, mockSCIcount;
uint32_t mockMuxCount, mockUnsafeMuxCount, mockUnprotectedPhaseWrites;
uint32_t mockADCTrigger[2][2], mockEOC[2], mockXbarGPIO, mockReadCost;
uint32_t mockTimerClock;
uint32_t mockMarkerClearCost;
uint32_t mockTimerReadCost;
uint32_t mockRevision = 1U;
uint16_t mockFIFOUsed;
bool mockZeroEvent, mockClearRace;
uint32_t mockADCClearCount[2];
uint32_t mockADCConverterMask;
uint32_t mockWatchdogFeeds;
bool mockWatchdogEnabled;
static bool armed[4];
static void burn(uint32_t cost)
{
    if (cost >= mockCounter[0]) { mockDirection[0] = EPWM_TIME_BASE_STATUS_COUNT_UP; mockCounter[0] = 0U; }
    else mockCounter[0] -= (uint16_t)cost;
}
uint32_t mockGPIOLevel[64];
void GPIO_writePin(uint32_t pin, uint32_t value) { assert(pin<64U);mockGPIOLevel[pin]=value; }

uint32_t mockAnalogMode[254], mockSyncSource[8], mockConfiguredPins[8], mockADCWindow[2][2];
int mockADCChannel[2][2];
uint32_t mockGPIODirection[64];
unsigned int mockConfiguredCount;
void GPIO_setDirectionMode(uint32_t pin, uint32_t mode) { assert(pin<64U);mockGPIODirection[pin]=mode; }
void GPIO_setAnalogMode(uint32_t pin, uint32_t mode) { assert(pin<254U);mockAnalogMode[pin]=mode; }
void EPWM_setSyncInPulseSource(uint32_t base, uint32_t source) { assert(base<8U);mockSyncSource[base]=source; }
unsigned int mockPWMResetCount;
void (*mockInterruptHandlers[3])(void);
bool mockInterruptEnabled[3];
void Interrupt_register(uint32_t n, void (*h)(void)) { assert(n<3U);mockInterruptHandlers[n]=h; }
void Interrupt_enable(uint32_t n) { assert(n<3U);mockInterruptEnabled[n]=true; }
void SysCtl_resetPeripheral(uint32_t p)
{
    uint32_t b;
    if(p==SYSCTL_PERIPH_RES_EPWM7)b=EPWM7_BASE;
    else if(p==SYSCTL_PERIPH_RES_EPWM4)b=EPWM4_BASE;
    else if(p==SYSCTL_PERIPH_RES_EPWM5)b=EPWM5_BASE;
    else if(p==SYSCTL_PERIPH_RES_EPWM10)b=EPWM10_BASE;
    else { assert(p==SYSCTL_PERIPH_RES_EPWM1);b=EPWM1_BASE; }
    memset(&mockPWM[b],0,sizeof(mockPWM[b]));mockCounter[b]=0U;mockDirection[b]=0U;
    if(b<4U)armed[b]=false;
    mockPWMResetCount++;
}
void Mock_reset(void)
{
    memset(mockPWM,0,sizeof(mockPWM)); memset(armed,0,sizeof(armed));
    memset(mockADCReady,0,sizeof(mockADCReady)); memset(mockADCOverflow,0,sizeof(mockADCOverflow));
    memset(mockADCTrigger,0,sizeof(mockADCTrigger));
    mockTimer=0xFFFFFFFFU; mockDelayUS=mockArmCount=mockWriteCost=mockSCIcount=0U;
    mockTimerClock=0xFFFFFFFFU;
    mockMarkerClearCost=0U;
    mockTimerReadCost=0U;
    mockMuxCount=mockUnsafeMuxCount=mockUnprotectedPhaseWrites=mockReadCost=0U;
    mockXbarGPIO=0xFFFFFFFFU; mockMasked=false;
    mockRevision=1U;mockFIFOUsed=0U;mockZeroEvent=mockClearRace=false;
    mockADCClearCount[0]=mockADCClearCount[1]=0U;
    mockADCConverterMask=0U;
    memset(mockGPIOLevel,0xFF,sizeof(mockGPIOLevel));
    memset(mockAnalogMode,0xFF,sizeof(mockAnalogMode));memset(mockADCChannel,0xFF,sizeof(mockADCChannel));
    memset(mockSyncSource,0,sizeof(mockSyncSource));mockConfiguredCount=0U;
    memset(mockGPIODirection,0xFF,sizeof(mockGPIODirection));
    mockPWMResetCount=0U;memset(mockInterruptHandlers,0,sizeof(mockInterruptHandlers));memset(mockInterruptEnabled,0,sizeof(mockInterruptEnabled));
    mockWatchdogFeeds=0U;mockWatchdogEnabled=false;
    memset(mockDirection,0,sizeof(mockDirection));
    mockCounter[0]=2500U; mockCounter[4]=7500U;
}
void Mock_adcFrame(uint16_t vp,uint16_t vn,uint16_t io,uint16_t il)
{
    mockADCReady[0]=mockADCReady[1]=true;
    mockADCResult[0][0]=vp;mockADCResult[0][1]=vn;mockADCResult[1][0]=io;mockADCResult[1][1]=il;
    mockDirection[4]=EPWM_TIME_BASE_STATUS_COUNT_DOWN;mockCounter[4]=7500U;
}
void Mock_sync(void)
{
    uint16_t i;
    for(i=0;i<4;i++) if(armed[i]) {
        mockPWM[i].period=mockPWM[i].shadowPeriod;
        mockPWM[i].cmpA=mockPWM[i].shadowA;mockPWM[i].cmpB=mockPWM[i].shadowB;armed[i]=false;
    }
    mockDirection[0]=EPWM_TIME_BASE_STATUS_COUNT_UP;mockCounter[0]=0U;
    mockZeroEvent=true;
}
void Mock_faultPulse(void)
{
    uint16_t i;
    for(i=0;i<4;i++) if(mockPWM[i].tripSignals & EPWM_TZ_SIGNAL_OSHT1) {
        mockPWM[i].ostSource |= EPWM_TZ_OST_FLAG_OST1; mockPWM[i].tripped=true;
    }
}
void Mock_delay(uint32_t us) { mockDelayUS+=us; }
bool Interrupt_disableGlobal(void) { bool old=mockMasked;mockMasked=true;return old; }
bool Interrupt_enableGlobal(void) { mockMasked=false;return false; }
void GPIO_setPinConfig(uint32_t pin)
{
    const uint32_t configs[8]={GPIO_12_EPWM7_A,GPIO_13_EPWM7_B,GPIO_6_EPWM4_A,GPIO_7_EPWM4_B,
        GPIO_37_EPWM5_A,GPIO_35_EPWM5_B,GPIO_62_EPWM10_A,GPIO_63_EPWM10_B};
    unsigned int i,j;
    for(i=0;i<8;i++) if(pin==configs[i]) {
        mockMuxCount++;
        assert(mockConfiguredCount<8U);mockConfiguredPins[mockConfiguredCount++]=pin;
        for(j=0;j<4;j++) if(!mockPWM[j].tripped) mockUnsafeMuxCount++;
    }
}
uint32_t GPIO_readPin(uint32_t pin) { (void)pin;return 1U; } // pulse has returned high
void XBAR_setInputPin(uint32_t base,uint32_t input,uint32_t gpio) { (void)base;assert(input==XBAR_INPUT1);mockXbarGPIO=gpio; }
void ADC_setupSOC(uint32_t base,uint32_t soc,uint32_t trigger,int channel,uint32_t window)
{ assert(window>=10U);mockADCChannel[base][soc]=channel;mockADCWindow[base][soc]=window;mockADCTrigger[base][soc]=trigger; }
void ADC_setInterruptSource(uint32_t base,uint32_t interrupt,uint32_t soc)
{ (void)interrupt;mockEOC[base]=soc; }
bool ADC_getInterruptStatus(uint32_t base,uint32_t interrupt) { (void)interrupt;return mockADCReady[base]; }
bool ADC_getInterruptOverflowStatus(uint32_t base,uint32_t interrupt) { (void)interrupt;return mockADCOverflow[base]; }
void ADC_clearInterruptStatus(uint32_t base,uint32_t interrupt)
{
    (void)interrupt;mockADCClearCount[base]++;mockADCReady[base]=false;
    if (mockClearRace && base==ADCA_BASE)
    {mockADCReady[base]=true;mockADCOverflow[base]=true;mockClearRace=false;}
}
void ADC_clearInterruptOverflowStatus(uint32_t base,uint32_t interrupt) { (void)interrupt;mockADCOverflow[base]=false; }
uint16_t ADC_readResult(uint32_t base,uint32_t soc)
{
    if(mockReadCost) { mockCounter[4]=0U;mockDirection[4]=EPWM_TIME_BASE_STATUS_COUNT_UP; }
    return mockADCResult[base][soc];
}
void EPWM_setPeriodLoadMode(uint32_t base,uint32_t mode) { mockPWM[base].shadowPeriodMode=(mode==EPWM_PERIOD_SHADOW_LOAD); }
void EPWM_setTimeBasePeriod(uint32_t base,uint32_t period)
{
    if(mockPWM[base].shadowPeriodMode) mockPWM[base].shadowPeriod=(uint16_t)period;
    else mockPWM[base].period=(uint16_t)period;
    if(mockWriteCost) burn(mockWriteCost);
}
void EPWM_setTimeBaseCounter(uint32_t base,uint32_t value) { mockCounter[base]=(uint16_t)value; }
uint16_t EPWM_getTimeBaseCounterValue(uint32_t base) { return mockCounter[base]; }
uint16_t EPWM_getTimeBaseCounterDirection(uint32_t base) { return mockDirection[base]; }
void EPWM_disableCounterCompareShadowLoadMode(uint32_t base,uint32_t cmp)
{ if(cmp==EPWM_COUNTER_COMPARE_A)mockPWM[base].shadowAEnabled=false;else mockPWM[base].shadowBEnabled=false; }
void EPWM_setCounterCompareShadowLoadMode(uint32_t base,uint32_t cmp,uint32_t mode)
{ (void)mode;if(cmp==EPWM_COUNTER_COMPARE_A)mockPWM[base].shadowAEnabled=true;else mockPWM[base].shadowBEnabled=true; }
void EPWM_setCounterCompareValue(uint32_t base,uint32_t cmp,uint32_t value)
{
    MockPWM *p=&mockPWM[base];
    if(cmp==EPWM_COUNTER_COMPARE_A) { if(p->shadowAEnabled)p->shadowA=(uint16_t)value;else p->cmpA=(uint16_t)value; }
    else { if(p->shadowBEnabled)p->shadowB=(uint16_t)value;else p->cmpB=(uint16_t)value; }
    if(mockWriteCost) burn(mockWriteCost);
}
void EPWM_forceTripZoneEvent(uint32_t base,uint32_t event) { (void)event;mockPWM[base].tripped=true; }
void EPWM_clearTripZoneFlag(uint32_t base,uint32_t flags)
{ (void)flags;mockPWM[base].tripped=mockPWM[base].ostSource!=0U; }
uint16_t EPWM_getOneShotTripZoneFlagStatus(uint32_t base) { return mockPWM[base].ostSource; }
void EPWM_clearOneShotTripZoneFlag(uint32_t base,uint16_t flags) { mockPWM[base].ostSource &= (uint16_t)~flags; }
void EPWM_enableTripZoneSignals(uint32_t base,uint16_t signals) { mockPWM[base].tripSignals|=signals; }
void EPWM_enablePhaseShiftLoad(uint32_t base) { mockPWM[base].phaseEnabled=true;if(mockWriteCost)burn(mockWriteCost); }
void EPWM_disablePhaseShiftLoad(uint32_t base) { mockPWM[base].phaseEnabled=false;if(mockWriteCost)burn(mockWriteCost); }
void EPWM_setPhaseShift(uint32_t base,uint32_t phase)
{
    if(mockPWM[base].phaseEnabled) mockUnprotectedPhaseWrites++;
    mockPWM[base].phase=(uint16_t)phase;if(mockWriteCost)burn(mockWriteCost);
}
void EPWM_setGlobalLoadEventPrescale(uint32_t base,uint32_t prescale) { mockPWM[base].loadPrescale=(uint16_t)prescale; }
void EPWM_setGlobalLoadTrigger(uint32_t base,uint32_t trigger) { mockPWM[base].loadTrigger=(uint16_t)trigger; }
void EPWM_enableGlobalLoadOneShotMode(uint32_t base) { mockPWM[base].oneShot=true; }
void EPWM_setupEPWMLinks(uint32_t base,uint32_t link,uint32_t component)
{ assert(component==EPWM_LINK_GLDCTL2);mockPWM[base].link=link; }
void EPWM_setGlobalLoadOneShotLatch(uint32_t base)
{
    unsigned int i; assert(base==EPWM7_BASE);
    for(i=0;i<4;i++) { assert(mockPWM[i].oneShot);assert(mockPWM[i].loadPrescale==1U);armed[i]=true; }
    mockArmCount++;
}
void EPWM_setInterruptSource(uint32_t base,uint16_t source) { mockPWM[base].interruptSource=source; }
void SCI_writeCharBlockingFIFO(uint32_t base,uint16_t value) { (void)base;assert(mockSCIcount<128);mockSCI[mockSCIcount++]=value; }
uint32_t CPUTimer_getTimerCount(uint32_t base) { uint32_t value=mockTimer;(void)base;mockTimer-=mockTimerReadCost;return value; }
void CPUTimer_setPeriod(uint32_t base,uint32_t period) { (void)base;mockTimer=period; }
void CPUTimer_selectClockSource(uint32_t base,uint32_t source,uint32_t prescale)
{ (void)base;assert(prescale==CPUTIMER_CLOCK_PRESCALER_1);mockTimerClock=source; }
uint32_t SysCtl_getDeviceRevision(void) {return mockRevision;}
bool EPWM_getADCTriggerFlagStatus(uint32_t base,uint32_t soc)
{assert(base==EPWM7_BASE && soc==EPWM_SOC_B);return mockZeroEvent;}
void EPWM_clearADCTriggerFlag(uint32_t base,uint32_t soc)
{assert(base==EPWM7_BASE && soc==EPWM_SOC_B);mockZeroEvent=false;if(mockMarkerClearCost)burn(mockMarkerClearCost);}
uint16_t SCI_getTxFIFOStatus(uint32_t base)
{(void)base;return mockFIFOUsed==16U?SCI_FIFO_TX16:mockFIFOUsed;}
void SCI_writeCharNonBlocking(uint32_t base,uint16_t data)
{assert(mockFIFOUsed<16U);mockFIFOUsed++;SCI_writeCharBlockingFIFO(base,data);}
void SCI_resetTxFIFO(uint32_t base) {(void)base;mockFIFOUsed=0U;}
void ADC_enableConverter(uint32_t base) {mockADCConverterMask |= 1U<<base;}
void SysCtl_enableWatchdog(void) {mockWatchdogEnabled=true;}
void SysCtl_serviceWatchdog(void) {mockWatchdogFeeds++;}
