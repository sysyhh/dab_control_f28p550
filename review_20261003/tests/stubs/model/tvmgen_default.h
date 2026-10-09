#ifndef TEST_TVMGEN_DEFAULT_H
#define TEST_TVMGEN_DEFAULT_H
#include <stdint.h>
struct tvmgen_default_inputs { void *input; };
struct tvmgen_default_outputs { void *output; };
extern volatile int32_t tvmgen_default_finished;
int32_t tvmgen_default_run(struct tvmgen_default_inputs *, struct tvmgen_default_outputs *);
void TI_NPU_init(void);
#endif
