#include "driverlib.h"
#include "dab_adc.h"
#include "dab_control.h"
#include "dab_pwm.h"
#include "dab_protect.h"
#include "dab_nn.h"
#include "dab_telemetry.h"
#include "dab_math.h"
#include "nn_expected.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
static float nonfinite(uint32_t bits) { union {float f;uint32_t u;}v;v.u=bits;return v.f; }
static void checkOff(void) { unsigned int i;assert(!DAB_PWM_isEnabled());for(i=0;i<4;i++)assert(mockPWM[i].tripped); }
static void ready(void)
{
    unsigned int i;
    Mock_reset();DAB_Protect_init();DAB_ADC_init();DAB_NN_init();DAB_Control_init();DAB_PWM_init();
    DAB_NN_service(90.0f);
    for(i=0;i<50;i++) { Mock_adcFrame(160,320,2221,2221);assert(DAB_ADC_read()); }
    assert(DAB_ADC_isReady());assert(!DAB_Protect_checkFault());
}
static void testMath(void)
{
    float integral=0.0f, before, out;unsigned int i;
    assert(!DAB_isFinite(nonfinite(0x7FC00000U)));assert(!DAB_isFinite(nonfinite(0x7F800000U)));
    assert(!DAB_isFinite(nonfinite(0xFF800000U)));assert(DAB_isFinite(-1.0f));
    for(i=0;i<1000;i++) out=DAB_piStep(40.0f,0.00005f,0.0001f,&integral,0.15f);
    assert(out<=0.15f && integral<=0.15f);
    before=out;out=DAB_piStep(-40.0f,0.00005f,0.0001f,&integral,0.15f);
    assert(out<before && out<0.15f); // no 21 ms saturation hold
    for(i=0;i<1000;i++) out=DAB_piStep(-40.0f,0.00005f,0.0001f,&integral,0.15f);
    assert(out==0.0f);out=DAB_piStep(40.0f,0.00005f,0.0001f,&integral,0.15f);assert(out>0.0f);
}
static void testTelemetry(void)
{
    const uint16_t expected[16]={0,0,0x80,0x3F,0,0,0,0x40,0,0,0x40,0x40,0,0,0x80,0x7F};
    unsigned int i;Mock_reset();DAB_Telemetry_init(115200U);assert(DAB_Telemetry_sendVOFA(1,2,3));
    DAB_Telemetry_service();
    assert(mockSCIcount==16U);for(i=0;i<16;i++)assert(mockSCI[i]==expected[i]);
    printf("VOFA: 16 expected octets passed\n");
}
static void testADC(void)
{
    float before;unsigned int i;uint32_t frame;
    Mock_reset();DAB_ADC_init();
    assert(mockDelayUS>=5000U);assert(!DAB_ADC_isReady());
    for(i=0;i<2;i++) { assert(mockEOC[i]==ADC_SOC_NUMBER1);assert(mockADCTrigger[i][0]==ADC_TRIGGER_EPWM1_SOCA);assert(mockADCTrigger[i][1]==ADC_TRIGGER_EPWM1_SOCA); }
    Mock_adcFrame(160,320,2221,2221);assert(DAB_ADC_read());
    assert(fabsf(g_sensing.vout_n_ave-g_sensing.vout_n)<1e-5f);assert(fabsf(g_sensing.il)<0.01f);
    before=g_sensing.vout_n_ave;frame=g_adcFrameCount;
    mockADCReady[0]=true;mockADCReady[1]=false;assert(!DAB_ADC_read());
    assert(g_adcFrameCount==frame && g_sensing.vout_n_ave==before);
    Mock_adcFrame(200,400,2221,2221);mockADCOverflow[1]=true;assert(!DAB_ADC_read());
    assert(!mockADCOverflow[1]);
    Mock_adcFrame(200,400,2221,2221);mockCounter[4]=1;assert(!DAB_ADC_read());
    Mock_adcFrame(200,400,2221,2221);mockReadCost=1;assert(!DAB_ADC_read());mockReadCost=0;
    for(i=0;i<50;i++) { Mock_adcFrame(160,320,2221,2221);assert(DAB_ADC_read()); }
    assert(DAB_ADC_isReady());
    assert(!DAB_ADC_read());assert(!DAB_ADC_isReady()); // readiness expires on bad frame
    assert(g_adcInvalidFrameCount==5U);
    printf("ADC: frame completeness, overflow, late read, filter priming passed\n");
}
static void qualifyRecovery(void)
{
    unsigned int i;
    for(i=0;i<101;i++) {
        mockTimer-=15000U;Mock_adcFrame(160,320,2221,2221);assert(DAB_ADC_read());
        DAB_Protect_checkFault();
    }
}
static void testNN(void)
{
    float out[4],maxError=0.0f;unsigned int i,j;
    Mock_reset();DAB_NN_init();assert(!DAB_NN_getOutput(out));
    assert(mockTimerClock==CPUTIMER_CLOCK_SOURCE_SYS);
    for(i=0;i<121;i++) {
        DAB_NN_service((float)(20+i));assert(DAB_NN_getOutput(out));assert(!DAB_NN_hasFault());
        for(j=0;j<4;j++) { float e=fabsf(out[j]-nnExpected[i][j]);if(e>maxError)maxError=e;assert(e<1e-5f); }
    }
    assert(g_nnInferenceCount==121U);DAB_NN_service(140.01f);assert(g_nnInferenceCount==121U);
    // Snapshot helpers preserve an existing interrupt mask.
    mockMasked=true;assert(DAB_NN_getOutput(out));assert(mockMasked);mockMasked=false;
    DAB_NN_service(nonfinite(0x7FC00000U));assert(DAB_NN_hasFault());assert(!DAB_NN_getOutput(out));
    printf("NN: 121 original-expression vectors, max error %.9g; cache and invalid input passed\n",(double)maxError);
}
static void testControlAndPWM(void)
{
    unsigned int i;uint32_t arm;
    Dab_PwmParams_t params;
    ready();checkOff();assert(mockMuxCount==8 && mockUnsafeMuxCount==0);
    assert(mockXbarGPIO==60U);
    for(i=0;i<4;i++) {assert(mockPWM[i].loadPrescale==1U);assert(mockPWM[i].tripSignals & EPWM_TZ_SIGNAL_OSHT1);}
    assert(mockPWM[0].loadTrigger==EPWM_GL_LOAD_PULSE_CNTR_ZERO);
    for(i=1;i<4;i++)assert(mockPWM[i].loadTrigger==EPWM_GL_LOAD_PULSE_SYNC);
    DAB_Control_setRef(-5.0f);assert(g_piCtrl.ref==0.0f);
    DAB_Control_setRef(65.0f);assert(g_piCtrl.ref==60.0f);
    DAB_Control_setRef(nonfinite(0x7FC00000U));assert(g_piCtrl.ref==60.0f);
    DAB_Control_setRef(40.0f);
#if !DAB_BOARD_CONFIG_CONFIRMED
    assert(!DAB_Control_start());checkOff();
    printf("Control: unconfirmed-board output gate passed\n");return;
#else
    assert(DAB_Control_start());checkOff();DAB_Control_step();
    assert(g_pwmParams.D0==0.0f && g_pwmParams.D1==1.0f && g_pwmParams.D2==1.0f);
    mockCounter[0]=2500;mockDirection[0]=EPWM_TIME_BASE_STATUS_COUNT_DOWN;
    dab_pwm_commit_ISR();assert(mockArmCount==1);checkOff();
    Mock_sync();dab_pwm_commit_ISR();assert(DAB_PWM_isEnabled());
    for(i=0;i<4;i++)assert(!mockPWM[i].tripped);
    for(i=0;i<1001;i++) {
        DAB_Control_step();mockCounter[0]=2500U;mockDirection[0]=EPWM_TIME_BASE_STATUS_COUNT_DOWN;
        dab_pwm_commit_ISR();Mock_sync();mockCounter[0]=2500U;mockDirection[0]=EPWM_TIME_BASE_STATUS_COUNT_DOWN;
        dab_pwm_commit_ISR();
    }
    assert(g_dabState==DAB_STATE_RUN && g_pwmParams.D0>0.2f);
    assert(g_pwmParams.D1>=0.001f && g_pwmParams.D1<=0.999f);
    assert(g_pwmParams.D2>=0.001f && g_pwmParams.D2<=0.999f);
#if DAB_CONTROL_MODE == DAB_MODE_NN_OPEN_LOOP
    assert(g_pwmParams.F_duty==0.0f);
#else
    assert(g_pwmParams.F_duty>0.0f && g_pwmParams.F_duty<=0.15f);
#endif
    // A late entry keeps the old loaded packet and does not arm partial data.
    DAB_Control_step();arm=mockArmCount;mockDirection[0]=EPWM_TIME_BASE_STATUS_COUNT_DOWN;mockCounter[0]=1U;
    dab_pwm_commit_ISR();assert(mockArmCount==arm && g_pwmLateCommitCount==1U);
    mockCounter[0]=2500U;dab_pwm_commit_ISR();assert(mockArmCount==arm+1U);
    assert(mockUnprotectedPhaseWrites==0U);
    params=g_pwmParams;params.D0=-0.1f;assert(!DAB_PWM_updateModulation(&params));
    params=g_pwmParams;params.D1=nonfinite(0x7FC00000U);assert(!DAB_PWM_updateModulation(&params));
    // A short external pulse remains visible after the physical pin returns high.
    Mock_faultPulse();assert(DAB_PWM_hardwareFault());DAB_Control_step();checkOff();
    assert(g_dabState==DAB_STATE_FAULT && g_protectFlags.bit.H_OCP_Flag);
    DAB_Control_stop();assert(g_dabState==DAB_STATE_FAULT);
    assert(!DAB_Control_start());qualifyRecovery();assert(DAB_Protect_clearFault());checkOff();
    assert(g_dabState==DAB_STATE_STANDBY);
    // A stop before the first zero cancels a pending release.
    assert(DAB_Control_start());DAB_Control_step();mockCounter[0]=2500;mockDirection[0]=0;
    dab_pwm_commit_ISR();DAB_Control_stop();Mock_sync();dab_pwm_commit_ISR();checkOff();
    // A write overrunning the commit window must hold outputs low.
    assert(DAB_Control_start());DAB_Control_step();arm=mockArmCount;
    mockCounter[0]=2500;mockDirection[0]=0;mockWriteCost=200;
    dab_pwm_commit_ISR();mockWriteCost=0;checkOff();
    assert(g_dabState==DAB_STATE_FAULT && mockArmCount==arm);
    qualifyRecovery();assert(DAB_Protect_clearFault());
    // The first packet also cannot release on an invalid latest ADC frame.
    assert(DAB_Control_start());DAB_Control_step();mockCounter[0]=2500;mockDirection[0]=0;
    dab_pwm_commit_ISR();Mock_sync();assert(!DAB_ADC_read());dab_pwm_commit_ISR();checkOff();
    assert(g_dabState==DAB_STATE_FAULT);
    ready();assert(DAB_Control_start());g_sensing.il=-26.0f;DAB_Control_step();checkOff();
    assert(g_protectFlags.bit.L_OCP_Flag && !DAB_Protect_clearFault());
    ready();assert(DAB_Control_start());Mock_adcFrame(160,320,2221,2221);
    mockADCReady[1]=false;dab_control_ISR();checkOff();assert(g_dabState==DAB_STATE_FAULT);
    printf("Control/PWM: first-load release, modes, ramp, trip latch, stop cancellation, late commit, bad ADC passed\n");
#endif
}
int main(void)
{
    testMath();testTelemetry();testADC();testNN();testControlAndPWM();
    printf("PASS board=%d mode=%u\n",DAB_BOARD_CONFIG_CONFIRMED,(unsigned int)DAB_CONTROL_MODE);return 0;
}
