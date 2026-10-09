// Include the actual foreground functions; do not execute the infinite MCU main.
#define main dab_embedded_main
#include "../../dab_control_f28p550/dab_main.c"
#undef main
#include <assert.h>
#include <stdio.h>
int main(void)
{
    Mock_reset();initBoardLEDs();
    assert(mockGPIOLevel[20]==1U && mockGPIOLevel[21]==1U);
    assert(mockAnalogMode[20]==GPIO_ANALOG_DISABLED && mockAnalogMode[21]==GPIO_ANALOG_DISABLED);
    updateFaultLED(DAB_STATE_FAULT);assert(mockGPIOLevel[21]==0U);
    updateFaultLED(DAB_STATE_STANDBY);assert(mockGPIOLevel[21]==1U);
    updateFaultLED(DAB_STATE_RUN);assert(mockGPIOLevel[21]==1U);
    assert(mockGPIOLevel[20]==1U); // 故障状态改变不能改变心跳灯。
    puts("PASS LaunchPad LEDs: initialization off, GPIO21 fault on and recovery off");
    Mock_reset();initControlInterrupts();
    assert(mockInterruptHandlers[INT_EPWM7]==dab_pwm_commit_ISR);
    assert(mockInterruptHandlers[INT_EPWM1]==dab_control_ISR);
    assert(mockInterruptEnabled[INT_EPWM7] && mockInterruptEnabled[INT_EPWM1]);
    assert(!mockInterruptEnabled[INT_EPWM5]);
    puts("PASS actual main interrupt registration: PWM7 commit and independent PWM1 control");
    Mock_reset();g_controlHeartbeat=0U;initWatchdog();
    assert(mockWatchdogEnabled && mockWatchdogFeeds==1U);
    serviceWatchdog();assert(mockWatchdogFeeds==1U);
    g_controlHeartbeat++;serviceWatchdog();assert(mockWatchdogFeeds==2U);
    serviceWatchdog();assert(mockWatchdogFeeds==2U);
    g_controlHeartbeat++;serviceWatchdog();assert(mockWatchdogFeeds==3U);
    mockMasked=true;serviceWatchdog();assert(mockMasked);mockMasked=false;
    puts("PASS watchdog: actual foreground services only on new control heartbeat, preserves interrupt mask");
    return 0;
}
