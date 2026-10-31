/* FC stage A: C28 packed integer input, eight 16-bit storage units.
 * Constants are initialized once by the application; only the Vin code changes.
 * Every float operation is the original firmware expression, in the same order. */
#ifndef FC_STAGE_A_INPUT_H
#define FC_STAGE_A_INPUT_H
#include <stdint.h>
#include <math.h>
static inline void DAB_FC_preparePackedInput(float vin_volts, uint16_t *packed)
{
    float normalized = vin_volts / 140.0f;
    float v_ = floorf(((normalized * 6.400000e+01f) + 5.000000e-01f));
    float v__1 = (v_) < (1.270000e+02f) ? (v_) : (1.270000e+02f);
    int16_t q = (int16_t)((v__1) > (-1.280000e+02f) ? (v__1) : (-1.280000e+02f));
    packed[0] = 0x00e0U | ((uint16_t)(q & 0x00ff) << 8);
}
#endif
