#include "driverlib.h"
#include "dab_adc.h"
#include "dab_control.h"
#include "dab_pwm.h"
#include "dab_protect.h"
#include "dab_nn.h"
#include "dab_math.h"
#include "dab_telemetry.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>

static void frame(void)
{
    mockTimer-=15000U;
    Mock_adcFrame(160U,320U,2221U,2221U);
    assert(DAB_ADC_read());
}
static void ready(void)
{
    unsigned int i;
    Mock_reset();DAB_Protect_init();DAB_ADC_init();DAB_NN_init();DAB_Control_init();DAB_PWM_init();
    DAB_NN_service(90.0f);
    for(i=0;i<50;i++) frame();
    g_controlLastTick=mockTimer;
    assert(DAB_ADC_isReady());
}
static void enable(void)
{
    assert(DAB_Control_start());DAB_Control_step();
    mockCounter[0]=2500U;mockDirection[0]=EPWM_TIME_BASE_STATUS_COUNT_DOWN;
    dab_pwm_commit_ISR();assert(!DAB_PWM_isEnabled());
    Mock_sync();dab_pwm_commit_ISR();assert(DAB_PWM_isEnabled());
}
static void testADC(void)
{
    unsigned int i;uint32_t cleared;
    ready();assert(!DAB_ADC_read());assert(!DAB_ADC_isReady());
    for(i=0;i<49;i++){frame();assert(!DAB_ADC_isReady());}
    frame();assert(DAB_ADC_isReady());
    mockTimer-=22501U;assert(!DAB_ADC_isReady());
    frame();assert(g_adcRecoveryFrameCount==1U && !DAB_ADC_isReady());
    cleared=mockADCClearCount[0];Mock_adcFrame(160,320,2221,2221);mockClearRace=true;
    assert(!DAB_ADC_read());assert(mockADCClearCount[0]==cleared+2U);
    assert(!mockADCReady[0] && !mockADCOverflow[0]);
    Mock_reset();mockRevision=0U;DAB_ADC_init();assert(mockADCConverterMask==31U);
    Mock_reset();mockRevision=1U;DAB_ADC_init();assert(mockADCConverterMask==3U);
    puts("PASS ADC: 50 consecutive recovery frames, age and gap, clear race, revision-0 converter power");
}
static void testLongFilter(void)
{
    uint16_t ring[50]={0};uint32_t sum=0U,seed=1U;unsigned int i,index=0;
    Mock_reset();DAB_ADC_init();
    for(i=0;i<50000;i++) {
        uint16_t raw;float expected;
        seed=seed*1664525U+1013904223U;raw=(uint16_t)((seed>>16)&4095U);
        sum-=ring[index];ring[index]=raw;sum+=raw;index=(index+1U)%50U;
        Mock_adcFrame(raw,raw,2221,2221);assert(DAB_ADC_read());
        expected=BUCK_VOUT_N_SCALE*(float)sum/(float)(i<50?i+1:50)+BUCK_VOUT_N_BIAS;
        assert(fabsf(g_sensing.vout_n_ave-expected)<0.0001f);
    }
    puts("PASS ADC: 50000 rolling samples match independently summed raw window");
}
static void testPWM(void)
{
    unsigned int i;uint32_t applied;
    ready();enable();applied=g_pwmAppliedSequence;
    DAB_Control_step();mockCounter[0]=2500;mockDirection[0]=EPWM_TIME_BASE_STATUS_COUNT_DOWN;
    dab_pwm_commit_ISR();assert(g_pwmAppliedSequence==applied);
    assert(DAB_PWM_checkDeadline() && g_pwmAppliedSequence==applied);
    Mock_sync();assert(DAB_PWM_checkDeadline() && g_pwmAppliedSequence!=applied);
    applied=g_pwmAppliedSequence;
    for(i=0;i<1100;i++) DAB_Control_step();
    assert(g_dabState==DAB_STATE_SOFT_START);assert(g_pwmAppliedSequence==applied);
    // Keep sampling/control alive while deliberately refusing every commit.
    ready();enable();
    for(i=0;i<5 && g_dabState!=DAB_STATE_FAULT;i++) {
        mockTimer-=15000U;Mock_adcFrame(160,320,2221,2221);dab_control_ISR();
        mockCounter[0]=DAB_PWM_COMMIT_GUARD_COUNTS;
        mockDirection[0]=EPWM_TIME_BASE_STATUS_COUNT_DOWN;dab_pwm_commit_ISR();
    }
    assert(!DAB_PWM_isEnabled());assert(g_pwmUpdateTimeoutCount==1U);
    assert(g_firstFault.reason==DAB_FAULT_PWM_TIMEOUT);
    // Missing first zero/load marker must never release outputs.
    ready();assert(DAB_Control_start());DAB_Control_step();
    mockCounter[0]=2500;mockDirection[0]=EPWM_TIME_BASE_STATUS_COUNT_DOWN;dab_pwm_commit_ISR();
    for(i=0;i<5 && g_dabState!=DAB_STATE_FAULT;i++) {
        mockTimer-=15000U;Mock_adcFrame(160,320,2221,2221);dab_control_ISR();
    }
    assert(!DAB_PWM_isEnabled() && g_firstFault.reason==DAB_FAULT_PWM_TIMEOUT);
    DAB_Control_faultReason(DAB_FAULT_NN);assert(g_firstFault.reason==DAB_FAULT_PWM_TIMEOUT);
    ready();enable();mockTimer-=22501U;
    mockCounter[0]=2500;mockDirection[0]=EPWM_TIME_BASE_STATUS_COUNT_DOWN;dab_pwm_commit_ISR();
    assert(!DAB_PWM_isEnabled());assert(g_firstFault.reason==DAB_FAULT_ADC);
    // Timer subtraction must survive wrap.
    ready();mockTimer=10U;
    for(i=0;i<50;i++){Mock_adcFrame(160,320,2221,2221);assert(DAB_ADC_read());}
    g_controlLastTick=mockTimer;enable();DAB_Control_step();
    mockTimer=(uint32_t)(10U-45001U);
    g_controlLastTick=mockTimer;
    assert(!DAB_PWM_checkDeadline());assert(!DAB_PWM_isEnabled());
    assert(g_firstFault.reason==DAB_FAULT_PWM_TIMEOUT);
    puts("PASS PWM: startup needs applied progress; bounded deferral, stopped control and wrap shut down; first fault retained");
}
static void testRecovery(void)
{
    unsigned int i;
    ready();enable();Mock_faultPulse();DAB_Control_step();
    assert(!DAB_Protect_clearFault());
    for(i=0;i<101;i++){frame();DAB_Protect_checkFault();}
    Mock_faultPulse();DAB_Protect_checkFault();assert(!DAB_Protect_clearFault());
    for(i=0;i<49;i++){frame();DAB_Protect_checkFault();}
    assert(!DAB_Protect_clearFault());
    for(i=0;i<2;i++){frame();DAB_Protect_checkFault();}
    assert(DAB_Protect_clearFault());assert(g_dabState==DAB_STATE_STANDBY);
    assert(g_firstFault.reason==DAB_FAULT_NONE && !DAB_PWM_isEnabled());
    puts("PASS recovery: manual clear requires stable qualification and does not restart");
}
static void testNNAndSCI(void)
{
    float bad[4]={1000000.0f,.25f,.001f,1.0f};unsigned int i;
    assert(!DAB_nnOutputValid(bad));bad[0]=.45f;bad[2]=-.0019f;assert(DAB_nnOutputValid(bad));
    bad[2]=-.1f;assert(!DAB_nnOutputValid(bad));
    Mock_reset();DAB_Telemetry_init(115200U);assert(mockAnalogMode[28]==GPIO_ANALOG_DISABLED);mockFIFOUsed=16U;
    for(i=0;i<4;i++)assert(DAB_Telemetry_sendVOFA(1,2,3));
    assert(!DAB_Telemetry_sendVOFA(1,2,3));assert(g_telemetryDroppedFrames==1U);
    DAB_Telemetry_service();assert(mockSCIcount==0U);
    mockFIFOUsed=14U;DAB_Telemetry_service();assert(mockSCIcount==2U && mockFIFOUsed==16U);
    mockFIFOUsed=0U;DAB_Telemetry_service();assert(mockSCIcount==18U); // bounded to 16 per call
    mockTimer-=3000001U;DAB_Telemetry_service();assert(g_telemetryTimeoutCount==1U);
    assert(g_telemetryDroppedFrames==4U); // one rejected + remaining three queued
    assert(DAB_Telemetry_sendVOFA(1,2,3));DAB_Telemetry_service();assert(mockSCIcount==34U);
    puts("PASS NN/SCI: impossible phase rejected; baseline tolerance; finite queue, full FIFO, partial frame, timeout and recovery");
}
int main(void)
{
    ready();
    assert(mockConfiguredCount==8U && mockUnsafeMuxCount==0U);
    assert(mockConfiguredPins[4]==GPIO_37_EPWM5_A && mockConfiguredPins[5]==GPIO_35_EPWM5_B);
    assert(mockConfiguredPins[6]==GPIO_62_EPWM10_A && mockConfiguredPins[7]==GPIO_63_EPWM10_B);
    assert(mockPWM[EPWM5_BASE].oneShot && mockPWM[EPWM5_BASE].link==EPWM_LINK_WITH_EPWM_7);
    assert(mockSyncSource[EPWM5_BASE]==EPWM_SYNC_IN_PULSE_SRC_SYNCOUT_EPWM7);
    assert(mockPWM[EPWM3_BASE].period==0U && !mockPWM[EPWM3_BASE].oneShot);
    assert(mockPWM[EPWM3_BASE].tripped);
    assert(mockGPIODirection[4]==GPIO_DIR_MODE_IN && mockGPIODirection[5]==GPIO_DIR_MODE_IN);
    assert(mockGPIODirection[0]==GPIO_DIR_MODE_IN && mockGPIODirection[1]==GPIO_DIR_MODE_IN);
    assert(mockPWMResetCount==5U);
    assert(mockXbarGPIO==60U);
    assert(mockADCChannel[0][0]==4 && mockADCChannel[0][1]==5);
    assert(mockADCChannel[1][0]==0 && mockADCChannel[1][1]==1);
    assert(mockADCWindow[0][0]==15U && mockADCWindow[0][1]==15U);
    assert(mockAnalogMode[12]==GPIO_ANALOG_DISABLED && mockAnalogMode[13]==GPIO_ANALOG_DISABLED);
    assert(mockAnalogMode[230]==GPIO_ANALOG_ENABLED && mockAnalogMode[253]==GPIO_ANALOG_ENABLED);
    assert(mockAnalogMode[225]==GPIO_ANALOG_ENABLED && mockAnalogMode[249]==GPIO_ANALOG_ENABLED);
    puts("PASS clustered pinout: Site2 J8 PWM7/4/5/10, J7 A4/A5/B0/B1, TZ GPIO60, GPIO61 timing, analog/digital selection");
    testADC();testLongFilter();testPWM();testRecovery();testNNAndSCI();
    puts("PASS follow-up software regressions; hardware registers are simulated");return 0;
}
