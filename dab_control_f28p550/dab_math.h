#ifndef DAB_MATH_H_
#define DAB_MATH_H_
#include <float.h>
#include "dab_board_config.h"

static inline int DAB_isFinite(float x)
{
    return (x == x) && (x <= FLT_MAX) && (x >= -FLT_MAX); // NaN 不等于自身；上下界比较排除正负无穷，保护后续除法和整数转换。
}

static inline float DAB_clamp(float x, float low, float high)
{
    return x < low ? low : (x > high ? high : x);
}

// Stop integration at the output boundary, retaining recovery-direction updates.
static inline float DAB_piStep(float error, float kp, float ki,
                               float *integral, float outputLimit)
{
    float next = *integral + ki * error; // 离散积分每次增加 ki×误差；ki 已含调用节拍意义，改变频率须重新设计。
    float unconstrained = kp * error + next;
    if (unconstrained > outputLimit && error > 0.0f)
        next = outputLimit - kp * error; // 上限饱和且误差继续推高时回退积分，使输出留在允许边界。
    else if (unconstrained < -outputLimit && error < 0.0f)
        next = -outputLimit - kp * error; // 下限饱和且误差继续推低时回退积分；恢复方向的积分仍保留。
    *integral = DAB_clamp(next, -outputLimit, outputLimit);
    return DAB_clamp(kp * error + *integral, -outputLimit, outputLimit);
}

static inline int DAB_nnOutputValid(const float *values)
{
    unsigned int i;
    for (i = 0U; i < 4U; i++)
    {
        if (!DAB_isFinite(values[i])) return 0;
    }
    if (values[3] < 0.5f || values[3] > 2.0f) return 0; // 第 4 项 T 限 0.5～2，对应当前开关周期允许范围。
    for (i = 0U; i < 3U; i++)
        if (values[i] < -DAB_NN_PHASE_TOLERANCE * values[3] ||
            values[i] > (1.0f + DAB_NN_PHASE_TOLERANCE) * values[3]) return 0;
            // 前三项允许相对 T 的 0.5% 数值容差，保留旧 FLOAT 网络的小负 D2。
            // 此检查只是数值合理性检查，不证明训练域、最小脉宽或功率电路安全。
    return 1;
}
#endif
