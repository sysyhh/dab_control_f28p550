#ifndef HOST_ASSERT_H
#define HOST_ASSERT_H
#include <stdio.h>
#include <stdlib.h>
#define assert(expr) do { if (!(expr)) { fprintf(stderr, "FAIL %s:%d: %s\n",__FILE__,__LINE__,#expr); exit(1); } } while (0)
#endif
