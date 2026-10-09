#include "driverlib.h"
#include "dab_nn.h"
#include "tvmgen_default.h"
#include <assert.h>
#include <stdio.h>
volatile int32_t tvmgen_default_finished;
static float *outBuffer,*inputBuffer;
static struct tvmgen_default_inputs *inputDescriptor;
static struct tvmgen_default_outputs *outputDescriptor;
static uint32_t submitted;
static int32_t runStatus;
void TI_NPU_init(void) { tvmgen_default_finished=0;submitted=0;runStatus=0; }
int32_t tvmgen_default_run(struct tvmgen_default_inputs *in,struct tvmgen_default_outputs *out)
{ inputDescriptor=in;outputDescriptor=out;inputBuffer=(float *)in->input;outBuffer=(float *)out->output;submitted++;return runStatus; }
static void complete(float t)
{ assert(outputDescriptor->output==outBuffer);assert(inputDescriptor->input==inputBuffer);
  outBuffer[0]=.45f;outBuffer[1]=.25f;outBuffer[2]=.001f;outBuffer[3]=t;tvmgen_default_finished=1; }
int main(void)
{
    float out[4];
    Mock_reset();DAB_NN_init();assert(!DAB_NN_getOutput(out));
    DAB_NN_service(90.0f);assert(submitted==1U);assert(!DAB_NN_getOutput(out));
    DAB_NN_service(100.0f);assert(submitted==1U);assert(inputBuffer[1]==90.0f/140.0f);
    complete(1.0f);DAB_NN_service(100.0f);assert(DAB_NN_getOutput(out));assert(out[3]==1.0f);
    DAB_NN_service(100.0f);assert(submitted==2U);assert(inputBuffer[1]==100.0f/140.0f);
    mockTimer-=150001U;DAB_NN_service(100.0f);assert(DAB_NN_hasFault());assert(g_nnTimeoutCount==1);
    assert(!DAB_NN_getOutput(out));DAB_NN_service(110.0f);assert(submitted==2U);
    // Separate fresh test instances: production timeout requires a device reset.
    Mock_reset();DAB_NN_init();runStatus=-1;DAB_NN_service(90.0f);assert(DAB_NN_hasFault());
    Mock_reset();DAB_NN_init();DAB_NN_service(90.0f);complete(0.0f);DAB_NN_service(90.0f);assert(DAB_NN_hasFault());
    Mock_reset();DAB_NN_init();mockTimer=50U;DAB_NN_service(90.0f);
    mockTimer=(uint32_t)(50U-150001U);DAB_NN_service(90.0f);assert(g_nnTimeoutCount==1U);
    // Timeout is enforced even if completion arrived before foreground resumed.
    Mock_reset();DAB_NN_init();DAB_NN_service(90.0f);mockTimer-=150001U;
    complete(1.0f);DAB_NN_service(90.0f);assert(DAB_NN_hasFault());assert(!DAB_NN_getOutput(out));
    // The control-side check also works while foreground service is stalled.
    Mock_reset();DAB_NN_init();DAB_NN_service(90.0f);mockTimer-=150001U;
    assert(!DAB_NN_checkDeadline());assert(g_nnTimeoutCount==1U);
    printf("PASS NPU API fixture: one in-flight buffer, return status, completion, timeout including timer wrap, no retry\n");
    return 0;
}
