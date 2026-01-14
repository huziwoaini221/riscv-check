/* Test file with misaligned pointer cast */

#include <stdlib.h>

void test_bad_cast_1() {
    char *buffer = malloc(10);
    buffer++;  /* Misaligned */
    int *i = (int*)buffer;  /* ERROR: ALIGN_PTR_CAST */
    *i = 42;
    free(buffer);
}

void test_bad_cast_2() {
    char *p = (char*)malloc(20);
    p += 3;  /* Odd address */
    long *l = (long*)p;  /* ERROR: ALIGN_PTR_CAST */
    *l = 123;
    free(p);
}
