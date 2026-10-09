#include "driverlib.h"
#include "device.h"
#include "dab_types.h"
#include "dab_pwm.h"
#include "dab_adc.h"
#include "dab_nn.h"
#include "dab_control.h"
#include "dab_protect.h"
#include "dab_telemetry.h"

volatile bool g_clearFaultRequested = false; // CCS 人工清故障请求；主循环读取后即清零，不是串口接收命令。
volatile bool g_lastClearFaultAccepted = false; // 记录最近一次清除是否获准；失败时应先查看故障原因和恢复条件。
volatile uint32_t g_backgroundHeartbeat = 0U; // 主循环进度计数，配合控制中断进度判断是否有任务停滞。
#pragma RETAIN(g_debugBuildId)
volatile const uint32_t g_debugBuildId = 0x20261009UL; // 自动实板调试读取此标记，核对新编译程序确已加载；不参与控制。
static uint32_t s_watchdogControlHeartbeat;

static void initWatchdog(void)
{
    s_watchdogControlHeartbeat = g_controlHeartbeat;
#if DAB_ENABLE_WATCHDOG
    // INTOSC1 / 512 / 64, 256 counts: nominal 0.839 s at 10 MHz.
    SysCtl_setWatchdogPredivider(SYSCTL_WD_PREDIV_512);
    SysCtl_setWatchdogPrescaler(SYSCTL_WD_PRESCALE_64);
    SysCtl_setWatchdogMode(SYSCTL_WD_MODE_RESET); // 超期触发 MCU 复位；名义约 0.839 s，不代替快速过流关断。
    SysCtl_serviceWatchdog();
    SysCtl_enableWatchdog();
#endif
}

static void serviceWatchdog(void)
{
    uint32_t heartbeat;
    bool masked = Interrupt_disableGlobal();
    heartbeat = g_controlHeartbeat; // 短暂关中断读取完整计数；退出时恢复进入前的中断屏蔽状态。
    if (!masked) Interrupt_enableGlobal();
#if DAB_ENABLE_WATCHDOG
    if (heartbeat != s_watchdogControlHeartbeat)
    { s_watchdogControlHeartbeat = heartbeat; SysCtl_serviceWatchdog(); } // 只有主循环运行且看到新的控制中断进度才喂狗，任一处卡住都无法持续喂狗。
#endif
    g_backgroundHeartbeat++;
}

static void updateFaultLED(Dab_State_e state)
{
    GPIO_writePin(DEVICE_GPIO_PIN_LED2,
                  state == DAB_STATE_FAULT ? DEVICE_LED_ON : DEVICE_LED_OFF); // LED5 仅在故障状态点亮。
}

static void initBoardLEDs(void)
{
    GPIO_setAnalogMode(DEVICE_GPIO_PIN_LED1, GPIO_ANALOG_DISABLED);
    GPIO_setAnalogMode(DEVICE_GPIO_PIN_LED2, GPIO_ANALOG_DISABLED); // LED20/21 也是模拟复用脚，明确接通数字驱动。
    GPIO_setPinConfig(DEVICE_GPIO_CFG_LED1);
    GPIO_setPinConfig(DEVICE_GPIO_CFG_LED2);
    GPIO_writePin(DEVICE_GPIO_PIN_LED1, DEVICE_LED_OFF);
    GPIO_writePin(DEVICE_GPIO_PIN_LED2, DEVICE_LED_OFF); // 先写熄灭电平，再设输出方向，避免初始化时短暂误亮。
    GPIO_setPadConfig(DEVICE_GPIO_PIN_LED1, GPIO_PIN_TYPE_STD);
    GPIO_setPadConfig(DEVICE_GPIO_PIN_LED2, GPIO_PIN_TYPE_STD);
    GPIO_setDirectionMode(DEVICE_GPIO_PIN_LED1, GPIO_DIR_MODE_OUT);
    GPIO_setDirectionMode(DEVICE_GPIO_PIN_LED2, GPIO_DIR_MODE_OUT);
}

static void initControlInterrupts(void)
{
    Interrupt_register(DAB_PWM_COMMIT_INTERRUPT, &dab_pwm_commit_ISR);
    Interrupt_register(DAB_CONTROL_INTERRUPT, &dab_control_ISR);
    Interrupt_enable(DAB_PWM_COMMIT_INTERRUPT);
    Interrupt_enable(DAB_CONTROL_INTERRUPT); // 两个中断均属于 PIE Group3，当前不嵌套。
}

void main(void)
{
    uint32_t lastTelemetry, now;
    bool masked, start, stop, clear;
    float vin, duty, error, voltage;
    Dab_State_e state;
#if DAB_AUTO_START
    bool autoPending = true;
    float nnOut[DAB_NN_OUTPUT_DIM];
#endif
    Device_init(); // 配置系统时钟、Flash/RAM 运行准备和外设时钟；开发板板载 20 MHz 晶振经 PLL 得到 150 MHz。
    // Device_init enables TBCLKSYNC. Stop it before any ePWM setup.
    SysCtl_disablePeripheral(SYSCTL_PERIPH_CLK_TBCLKSYNC); // 冻结 ePWM 计数，防止配置尚未完成时发生采样、同步或输出事件。
    Device_initGPIO();
    Interrupt_initModule();
    Interrupt_initVectorTable();
    // device.h selects LEDs/SCI for its configured board. Peripheral pinmux
    // is owned by this application; generated Board_init is intentionally unused.
    initBoardLEDs(); // LAUNCHXL-F28P55X：LED4/GPIO20 为心跳，LED5/GPIO21 为故障。
    DAB_Protect_init(); // 先建立外部低有效故障输入及 XBAR 路径。
    DAB_ADC_init(); // 初始化 ADCA/ADCB 通道、完成状态、滤波和参考稳定等待。
    DAB_NN_init(); // 初始化 NN 缓存及共享 Timer2；默认 FPU，只有真实模型接入后才启用 NPU。
    DAB_Control_init(); // 状态置待机，准备 PI 与软启动初始参数；此时不允许功率输出。
    DAB_PWM_init(); // 配置四桥 PWM 和 EPWM1 节拍；引脚切换前保持软件 OST 关断。
    DAB_Telemetry_init(115200U); // 配置 SCIA 的 8N1 遥测；发送三通道 VOFA+，没有远程启停协议。
    initControlInterrupts(); // EPWM7 提交功率参数，EPWM1 负责固定 10 kHz 采样和控制。
    lastTelemetry = CPUTimer_getTimerCount(CPUTIMER2_BASE);
    initWatchdog();
    SysCtl_enablePeripheral(SYSCTL_PERIPH_CLK_TBCLKSYNC); // 所有配置完成后才让 ePWM 共同开始计数。
    EINT;
    ERTM;
    // 外设初始化结束；下面是后台工作，不直接生成开关波形。
    // 引脚配置由应用管理，未调用生成的 Board_init，不能只改 SysConfig 就期待生效。

    while (1)
    {
        masked = Interrupt_disableGlobal();
        vin = g_sensing.vin_ave;
        stop = g_stopRequested;
        start = g_startRequested;
        clear = g_clearFaultRequested;
        g_stopRequested = g_startRequested = g_clearFaultRequested = false; // 每个请求只处理一次，拒绝的启动也不会延迟到将来自动执行。
        if (stop) DAB_Control_stop(); // 同一轮多个请求同时到达时，停止优先。
        if (!masked) Interrupt_enableGlobal();
        if (clear && !stop) g_lastClearFaultAccepted = DAB_Protect_clearFault();
        if (!DAB_NN_benchmarkService(g_dabState == DAB_STATE_STANDBY && !DAB_PWM_isEnabled()))
            DAB_NN_service(vin); // 普通服务保留输入缓存；重复测试仅在待机且输出关闭时接管，仍允许中断。
        DAB_Telemetry_service(); // 只填入有限数量的 FIFO 字节，串口满时立即返回。
        serviceWatchdog();
        if (start && !stop && !clear) DAB_Control_start(); // 启动必须另行满足板确认、待机、采样、NN 和保护条件。
#if DAB_AUTO_START
        if (stop || clear || g_nnBenchmarkState != DAB_NN_BENCH_IDLE) autoPending = false;
        if (autoPending && DAB_ADC_isReady() && DAB_NN_getOutput(nnOut))
        { DAB_Control_start(); autoPending = false; }
#endif
        now = CPUTimer_getTimerCount(CPUTIMER2_BASE);
        if ((uint32_t)(lastTelemetry - now) >= DEVICE_SYSCLK_FREQ / 10UL) // Timer2 向下计数，用无符号差值处理回绕；达到 100 ms 才采一帧显示数据。
        {
            lastTelemetry = now;
            // Snapshot only; do not block SCI or NPU interrupts during transmit.
            masked = Interrupt_disableGlobal();
            duty = g_pwmParams.F_duty;
            error = g_piCtrl.err;
            voltage = g_sensing.vout_n_ave;
            state = g_dabState;
            if (!masked) Interrupt_enableGlobal();
            DAB_Telemetry_sendVOFA(duty, error, voltage); // 三通道依次为 PI 修正、误差、平均输出电压；只入队，不等待线路传完。
            GPIO_togglePin(DEVICE_GPIO_PIN_LED1);
            updateFaultLED(state); // 板载指示灯低有效；待机和正常运行时故障灯熄灭。
        }
    }
}
